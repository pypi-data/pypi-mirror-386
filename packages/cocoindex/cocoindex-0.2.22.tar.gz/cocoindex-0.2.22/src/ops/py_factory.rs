use crate::prelude::*;

use pyo3::{
    Bound, IntoPyObjectExt, Py, PyAny, Python, pyclass, pymethods,
    types::{IntoPyDict, PyAnyMethods, PyList, PyString, PyTuple, PyTupleMethods},
};
use pythonize::{depythonize, pythonize};

use crate::{
    base::{schema, value},
    builder::plan,
    ops::sdk::SetupStateCompatibility,
    py::{self, ToResultWithPyTrace},
};
use anyhow::{Result, anyhow};

#[pyclass(name = "OpArgSchema")]
pub struct PyOpArgSchema {
    value_type: crate::py::Pythonized<schema::EnrichedValueType>,
    analyzed_value: crate::py::Pythonized<plan::AnalyzedValueMapping>,
}

#[pymethods]
impl PyOpArgSchema {
    #[getter]
    fn value_type(&self) -> &crate::py::Pythonized<schema::EnrichedValueType> {
        &self.value_type
    }

    #[getter]
    fn analyzed_value(&self) -> &crate::py::Pythonized<plan::AnalyzedValueMapping> {
        &self.analyzed_value
    }
}

struct PyFunctionExecutor {
    py_function_executor: Py<PyAny>,
    py_exec_ctx: Arc<crate::py::PythonExecutionContext>,

    num_positional_args: usize,
    kw_args_names: Vec<Py<PyString>>,
    result_type: schema::EnrichedValueType,

    enable_cache: bool,
    behavior_version: Option<u32>,
}

impl PyFunctionExecutor {
    fn call_py_fn<'py>(
        &self,
        py: Python<'py>,
        input: Vec<value::Value>,
    ) -> Result<pyo3::Bound<'py, pyo3::PyAny>> {
        let mut args = Vec::with_capacity(self.num_positional_args);
        for v in input[0..self.num_positional_args].iter() {
            args.push(py::value_to_py_object(py, v)?);
        }

        let kwargs = if self.kw_args_names.is_empty() {
            None
        } else {
            let mut kwargs = Vec::with_capacity(self.kw_args_names.len());
            for (name, v) in self
                .kw_args_names
                .iter()
                .zip(input[self.num_positional_args..].iter())
            {
                kwargs.push((name.bind(py), py::value_to_py_object(py, v)?));
            }
            Some(kwargs)
        };

        let result = self
            .py_function_executor
            .call(
                py,
                PyTuple::new(py, args.into_iter())?,
                kwargs
                    .map(|kwargs| -> Result<_> { Ok(kwargs.into_py_dict(py)?) })
                    .transpose()?
                    .as_ref(),
            )
            .to_result_with_py_trace(py)?;
        Ok(result.into_bound(py))
    }
}

#[async_trait]
impl interface::SimpleFunctionExecutor for Arc<PyFunctionExecutor> {
    async fn evaluate(&self, input: Vec<value::Value>) -> Result<value::Value> {
        let self = self.clone();
        let result_fut = Python::with_gil(|py| -> Result<_> {
            let result_coro = self.call_py_fn(py, input)?;
            let task_locals =
                pyo3_async_runtimes::TaskLocals::new(self.py_exec_ctx.event_loop.bind(py).clone());
            Ok(pyo3_async_runtimes::into_future_with_locals(
                &task_locals,
                result_coro,
            )?)
        })?;
        let result = result_fut.await;
        Python::with_gil(|py| -> Result<_> {
            let result = result.to_result_with_py_trace(py)?;
            Ok(py::value_from_py_object(
                &self.result_type.typ,
                &result.into_bound(py),
            )?)
        })
    }

    fn enable_cache(&self) -> bool {
        self.enable_cache
    }

    fn behavior_version(&self) -> Option<u32> {
        self.behavior_version
    }
}

pub(crate) struct PyFunctionFactory {
    pub py_function_factory: Py<PyAny>,
}

#[async_trait]
impl interface::SimpleFunctionFactory for PyFunctionFactory {
    async fn build(
        self: Arc<Self>,
        spec: serde_json::Value,
        input_schema: Vec<schema::OpArgSchema>,
        context: Arc<interface::FlowInstanceContext>,
    ) -> Result<(
        schema::EnrichedValueType,
        BoxFuture<'static, Result<Box<dyn interface::SimpleFunctionExecutor>>>,
    )> {
        let (result_type, executor, kw_args_names, num_positional_args) =
            Python::with_gil(|py| -> anyhow::Result<_> {
                let mut args = vec![pythonize(py, &spec)?];
                let mut kwargs = vec![];
                let mut num_positional_args = 0;
                for arg in input_schema.into_iter() {
                    let py_arg_schema = PyOpArgSchema {
                        value_type: crate::py::Pythonized(arg.value_type.clone()),
                        analyzed_value: crate::py::Pythonized(arg.analyzed_value.clone()),
                    };
                    match arg.name.0 {
                        Some(name) => {
                            kwargs.push((name.clone(), py_arg_schema));
                        }
                        None => {
                            args.push(py_arg_schema.into_bound_py_any(py)?);
                            num_positional_args += 1;
                        }
                    }
                }

                let kw_args_names = kwargs
                    .iter()
                    .map(|(name, _)| PyString::new(py, name).unbind())
                    .collect::<Vec<_>>();
                let result = self
                    .py_function_factory
                    .call(
                        py,
                        PyTuple::new(py, args.into_iter())?,
                        Some(&kwargs.into_py_dict(py)?),
                    )
                    .to_result_with_py_trace(py)?;
                let (result_type, executor) = result
                    .extract::<(crate::py::Pythonized<schema::EnrichedValueType>, Py<PyAny>)>(py)?;
                Ok((
                    result_type.into_inner(),
                    executor,
                    kw_args_names,
                    num_positional_args,
                ))
            })?;

        let executor_fut = {
            let result_type = result_type.clone();
            async move {
                let py_exec_ctx = context
                    .py_exec_ctx
                    .as_ref()
                    .ok_or_else(|| anyhow!("Python execution context is missing"))?
                    .clone();
                let (prepare_fut, enable_cache, behavior_version) =
                    Python::with_gil(|py| -> anyhow::Result<_> {
                        let prepare_coro = executor
                            .call_method(py, "prepare", (), None)
                            .to_result_with_py_trace(py)?;
                        let prepare_fut = pyo3_async_runtimes::into_future_with_locals(
                            &pyo3_async_runtimes::TaskLocals::new(
                                py_exec_ctx.event_loop.bind(py).clone(),
                            ),
                            prepare_coro.into_bound(py),
                        )?;
                        let enable_cache = executor
                            .call_method(py, "enable_cache", (), None)
                            .to_result_with_py_trace(py)?
                            .extract::<bool>(py)?;
                        let behavior_version = executor
                            .call_method(py, "behavior_version", (), None)
                            .to_result_with_py_trace(py)?
                            .extract::<Option<u32>>(py)?;
                        Ok((prepare_fut, enable_cache, behavior_version))
                    })?;
                prepare_fut.await?;
                Ok(Box::new(Arc::new(PyFunctionExecutor {
                    py_function_executor: executor,
                    py_exec_ctx,
                    num_positional_args,
                    kw_args_names,
                    result_type,
                    enable_cache,
                    behavior_version,
                }))
                    as Box<dyn interface::SimpleFunctionExecutor>)
            }
        };

        Ok((result_type, executor_fut.boxed()))
    }
}

////////////////////////////////////////////////////////
// Custom source connector
////////////////////////////////////////////////////////

pub(crate) struct PySourceConnectorFactory {
    pub py_source_connector: Py<PyAny>,
}

struct PySourceExecutor {
    py_source_executor: Py<PyAny>,
    py_exec_ctx: Arc<crate::py::PythonExecutionContext>,
    provides_ordinal: bool,
    key_fields: Box<[schema::FieldSchema]>,
    value_fields: Box<[schema::FieldSchema]>,
}

#[async_trait]
impl interface::SourceExecutor for PySourceExecutor {
    async fn list(
        &self,
        options: &interface::SourceExecutorReadOptions,
    ) -> Result<BoxStream<'async_trait, Result<Vec<interface::PartialSourceRow>>>> {
        let py_exec_ctx = self.py_exec_ctx.clone();
        let py_source_executor = Python::with_gil(|py| self.py_source_executor.clone_ref(py));

        // Get the Python async iterator
        let py_async_iter = Python::with_gil(|py| {
            py_source_executor
                .call_method(py, "list_async", (pythonize(py, options)?,), None)
                .to_result_with_py_trace(py)
        })?;

        // Create a stream that pulls from the Python async iterator one item at a time
        let stream = try_stream! {
            // We need to iterate over the Python async iterator
            loop {
                if let Some(source_row) = self.next_partial_source_row(&py_async_iter, &py_exec_ctx).await? {
                    // Yield a Vec containing just this single row
                    yield vec![source_row];
                } else {
                    break;
                }
            }
        };

        Ok(stream.boxed())
    }

    async fn get_value(
        &self,
        key: &value::KeyValue,
        _key_aux_info: &serde_json::Value,
        options: &interface::SourceExecutorReadOptions,
    ) -> Result<interface::PartialSourceRowData> {
        let py_exec_ctx = self.py_exec_ctx.clone();
        let py_source_executor = Python::with_gil(|py| self.py_source_executor.clone_ref(py));
        let key_clone = key.clone();

        let py_result = Python::with_gil(|py| -> Result<_> {
            let result_coro = py_source_executor
                .call_method(
                    py,
                    "get_value_async",
                    (
                        py::key_to_py_object(py, &key_clone)?,
                        pythonize(py, options)?,
                    ),
                    None,
                )
                .to_result_with_py_trace(py)?;
            let task_locals =
                pyo3_async_runtimes::TaskLocals::new(py_exec_ctx.event_loop.bind(py).clone());
            Ok(pyo3_async_runtimes::into_future_with_locals(
                &task_locals,
                result_coro.into_bound(py),
            )?)
        })?
        .await;

        Python::with_gil(|py| -> Result<_> {
            let result = py_result.to_result_with_py_trace(py)?;
            let result_bound = result.into_bound(py);
            let data = self.parse_partial_source_row_data(py, &result_bound)?;
            Ok(data)
        })
    }

    async fn change_stream(
        &self,
    ) -> Result<Option<BoxStream<'async_trait, Result<interface::SourceChangeMessage>>>> {
        Ok(None)
    }

    fn provides_ordinal(&self) -> bool {
        self.provides_ordinal
    }
}

impl PySourceExecutor {
    async fn next_partial_source_row(
        &self,
        py_async_iter: &Py<PyAny>,
        py_exec_ctx: &Arc<crate::py::PythonExecutionContext>,
    ) -> Result<Option<interface::PartialSourceRow>> {
        // Call the Python method to get the next item, avoiding storing Python objects across await points
        let next_item_coro = Python::with_gil(|py| -> Result<_> {
            let coro = py_async_iter
                .call_method0(py, "__anext__")
                .to_result_with_py_trace(py)?;
            let task_locals =
                pyo3_async_runtimes::TaskLocals::new(py_exec_ctx.event_loop.bind(py).clone());
            Ok(pyo3_async_runtimes::into_future_with_locals(
                &task_locals,
                coro.into_bound(py),
            )?)
        })?;

        // Await the future to get the next item
        let py_item_result = next_item_coro.await;

        // Handle StopAsyncIteration and convert to Rust data immediately to avoid Send issues
        Python::with_gil(|py| -> Result<Option<interface::PartialSourceRow>> {
            match py_item_result {
                Ok(item) => {
                    let bound_item = item.into_bound(py);
                    let source_row =
                        self.convert_py_tuple_to_partial_source_row(py, &bound_item)?;
                    Ok(Some(source_row))
                }
                Err(py_err) => {
                    if py_err.is_instance_of::<pyo3::exceptions::PyStopAsyncIteration>(py) {
                        Ok(None)
                    } else {
                        Err(py_err).to_result_with_py_trace(py)
                    }
                }
            }
        })
    }

    fn convert_py_tuple_to_partial_source_row(
        &self,
        py: Python,
        bound_item: &Bound<PyAny>,
    ) -> Result<interface::PartialSourceRow> {
        // Each item should be a tuple of (key, data)
        let tuple = bound_item
            .downcast::<PyTuple>()
            .map_err(|e| anyhow!("Failed to downcast to PyTuple: {}", e))?;
        if tuple.len() != 2 {
            api_bail!("Expected tuple of length 2 from Python source iterator");
        }

        let key_py = tuple.get_item(0)?;
        let data_py = tuple.get_item(1)?;

        // key_aux_info is always Null now
        let key_aux_info = serde_json::Value::Null;

        // Parse data
        let data = self.parse_partial_source_row_data(py, &data_py)?;

        // Convert key using py::field_values_from_py_seq
        let key_field_values = py::field_values_from_py_seq(&self.key_fields, &key_py)?;
        let key_parts: Result<Vec<_>, _> = key_field_values
            .fields
            .into_iter()
            .map(|field| field.into_key())
            .collect();
        let key_value = value::KeyValue(key_parts?.into_boxed_slice());

        Ok(interface::PartialSourceRow {
            key: key_value,
            key_aux_info,
            data,
        })
    }

    fn parse_partial_source_row_data(
        &self,
        _py: Python,
        data_py: &Bound<PyAny>,
    ) -> Result<interface::PartialSourceRowData> {
        // Extract fields from the Python dict
        let ordinal = if let Ok(ordinal_py) = data_py.get_item("ordinal")
            && !ordinal_py.is_none()
        {
            if ordinal_py.is_instance_of::<PyString>()
                && ordinal_py.extract::<&str>()? == "NO_ORDINAL"
            {
                Some(interface::Ordinal::unavailable())
            } else if let Ok(ordinal) = ordinal_py.extract::<i64>() {
                Some(interface::Ordinal(Some(ordinal)))
            } else {
                api_bail!("Invalid ordinal: {}", ordinal_py);
            }
        } else {
            None
        };

        // Handle content_version_fp - can be bytes or null
        let content_version_fp = if let Ok(fp_py) = data_py.get_item("content_version_fp")
            && !fp_py.is_none()
        {
            if let Ok(bytes_vec) = fp_py.extract::<Vec<u8>>() {
                Some(bytes_vec)
            } else {
                api_bail!("Invalid content_version_fp: {}", fp_py);
            }
        } else {
            None
        };

        // Handle value - can be NON_EXISTENCE string, encoded value, or null
        let value = if let Ok(value_py) = data_py.get_item("value")
            && !value_py.is_none()
        {
            if value_py.is_instance_of::<PyString>()
                && value_py.extract::<&str>()? == "NON_EXISTENCE"
            {
                Some(interface::SourceValue::NonExistence)
            } else if let Ok(field_values) =
                py::field_values_from_py_seq(&self.value_fields, &value_py)
            {
                Some(interface::SourceValue::Existence(field_values))
            } else {
                api_bail!("Invalid value: {}", value_py);
            }
        } else {
            None
        };

        Ok(interface::PartialSourceRowData {
            ordinal,
            content_version_fp,
            value,
        })
    }
}

#[async_trait]
impl interface::SourceFactory for PySourceConnectorFactory {
    async fn build(
        self: Arc<Self>,
        _source_name: &str,
        spec: serde_json::Value,
        context: Arc<interface::FlowInstanceContext>,
    ) -> Result<(
        schema::EnrichedValueType,
        BoxFuture<'static, Result<Box<dyn interface::SourceExecutor>>>,
    )> {
        let py_exec_ctx = context
            .py_exec_ctx
            .as_ref()
            .ok_or_else(|| anyhow!("Python execution context is missing"))?
            .clone();

        // First get the table type (this doesn't require executor)
        let table_type = Python::with_gil(|py| -> Result<_> {
            let value_type_result = self
                .py_source_connector
                .call_method(py, "get_table_type", (), None)
                .to_result_with_py_trace(py)?;
            let table_type: schema::EnrichedValueType =
                depythonize(&value_type_result.into_bound(py))?;
            Ok(table_type)
        })?;

        // Extract key and value field schemas from the table type - must be a KTable
        let (key_fields, value_fields) = match &table_type.typ {
            schema::ValueType::Table(table) => {
                // Must be a KTable for sources
                let num_key_parts = match &table.kind {
                    schema::TableKind::KTable(info) => info.num_key_parts,
                    _ => api_bail!("Source must return a KTable type, got {:?}", table.kind),
                };

                let key_fields = table.row.fields[..num_key_parts]
                    .to_vec()
                    .into_boxed_slice();
                let value_fields = table.row.fields[num_key_parts..]
                    .to_vec()
                    .into_boxed_slice();

                (key_fields, value_fields)
            }
            _ => api_bail!(
                "Expected KTable type from get_value_type(), got {:?}",
                table_type.typ
            ),
        };

        let executor_fut = async move {
            // Create the executor using the async create_executor method
            let create_future = Python::with_gil(|py| -> Result<_> {
                let create_coro = self
                    .py_source_connector
                    .call_method(py, "create_executor", (pythonize(py, &spec)?,), None)
                    .to_result_with_py_trace(py)?;
                let task_locals =
                    pyo3_async_runtimes::TaskLocals::new(py_exec_ctx.event_loop.bind(py).clone());
                let create_future = pyo3_async_runtimes::into_future_with_locals(
                    &task_locals,
                    create_coro.into_bound(py),
                )?;
                Ok(create_future)
            })?;

            let py_executor_context_result = create_future.await;

            let (py_source_executor_context, provides_ordinal) =
                Python::with_gil(|py| -> Result<_> {
                    let executor_context =
                        py_executor_context_result.to_result_with_py_trace(py)?;

                    // Get provides_ordinal from the executor context
                    let provides_ordinal = executor_context
                        .call_method(py, "provides_ordinal", (), None)
                        .to_result_with_py_trace(py)?
                        .extract::<bool>(py)?;

                    Ok((executor_context, provides_ordinal))
                })?;

            Ok(Box::new(PySourceExecutor {
                py_source_executor: py_source_executor_context,
                py_exec_ctx,
                provides_ordinal,
                key_fields,
                value_fields,
            }) as Box<dyn interface::SourceExecutor>)
        };

        Ok((table_type, executor_fut.boxed()))
    }
}

////////////////////////////////////////////////////////
// Custom target connector
////////////////////////////////////////////////////////

pub(crate) struct PyExportTargetFactory {
    pub py_target_connector: Py<PyAny>,
}

struct PyTargetExecutorContext {
    py_export_ctx: Py<PyAny>,
    py_exec_ctx: Arc<crate::py::PythonExecutionContext>,
}

#[derive(Debug)]
struct PyTargetResourceSetupChange {
    stale_existing_states: IndexSet<Option<serde_json::Value>>,
    desired_state: Option<serde_json::Value>,
}

impl setup::ResourceSetupChange for PyTargetResourceSetupChange {
    fn describe_changes(&self) -> Vec<setup::ChangeDescription> {
        vec![]
    }

    fn change_type(&self) -> setup::SetupChangeType {
        if self.stale_existing_states.is_empty() {
            setup::SetupChangeType::NoChange
        } else if self.desired_state.is_some() {
            if self
                .stale_existing_states
                .iter()
                .any(|state| state.is_none())
            {
                setup::SetupChangeType::Create
            } else {
                setup::SetupChangeType::Update
            }
        } else {
            setup::SetupChangeType::Delete
        }
    }
}

#[async_trait]
impl interface::TargetFactory for PyExportTargetFactory {
    async fn build(
        self: Arc<Self>,
        data_collections: Vec<interface::ExportDataCollectionSpec>,
        declarations: Vec<serde_json::Value>,
        context: Arc<interface::FlowInstanceContext>,
    ) -> Result<(
        Vec<interface::ExportDataCollectionBuildOutput>,
        Vec<(serde_json::Value, serde_json::Value)>,
    )> {
        if declarations.len() != 0 {
            api_error!("Custom target connector doesn't support declarations yet");
        }

        let mut build_outputs = Vec::with_capacity(data_collections.len());
        let py_exec_ctx = context
            .py_exec_ctx
            .as_ref()
            .ok_or_else(|| anyhow!("Python execution context is missing"))?
            .clone();
        for data_collection in data_collections.into_iter() {
            let (py_export_ctx, persistent_key, setup_state) = Python::with_gil(|py| {
                // Deserialize the spec to Python object.
                let py_export_ctx = self
                    .py_target_connector
                    .call_method(
                        py,
                        "create_export_context",
                        (
                            &data_collection.name,
                            pythonize(py, &data_collection.spec)?,
                            pythonize(py, &data_collection.key_fields_schema)?,
                            pythonize(py, &data_collection.value_fields_schema)?,
                            pythonize(py, &data_collection.index_options)?,
                        ),
                        None,
                    )
                    .to_result_with_py_trace(py)?;

                // Call the `get_persistent_key` method to get the persistent key.
                let persistent_key = self
                    .py_target_connector
                    .call_method(py, "get_persistent_key", (&py_export_ctx,), None)
                    .to_result_with_py_trace(py)?;
                let persistent_key: serde_json::Value =
                    depythonize(&persistent_key.into_bound(py))?;

                let setup_state = self
                    .py_target_connector
                    .call_method(py, "get_setup_state", (&py_export_ctx,), None)
                    .to_result_with_py_trace(py)?;
                let setup_state: serde_json::Value = depythonize(&setup_state.into_bound(py))?;

                anyhow::Ok((py_export_ctx, persistent_key, setup_state))
            })?;

            let factory = self.clone();
            let py_exec_ctx = py_exec_ctx.clone();
            let build_output = interface::ExportDataCollectionBuildOutput {
                export_context: Box::pin(async move {
                    Python::with_gil(|py| {
                        let prepare_coro = factory
                            .py_target_connector
                            .call_method(py, "prepare_async", (&py_export_ctx,), None)
                            .to_result_with_py_trace(py)?;
                        let task_locals = pyo3_async_runtimes::TaskLocals::new(
                            py_exec_ctx.event_loop.bind(py).clone(),
                        );
                        anyhow::Ok(pyo3_async_runtimes::into_future_with_locals(
                            &task_locals,
                            prepare_coro.into_bound(py),
                        )?)
                    })?
                    .await?;
                    anyhow::Ok(Arc::new(PyTargetExecutorContext {
                        py_export_ctx,
                        py_exec_ctx,
                    }) as Arc<dyn Any + Send + Sync>)
                }),
                setup_key: persistent_key,
                desired_setup_state: setup_state,
            };
            build_outputs.push(build_output);
        }
        Ok((build_outputs, vec![]))
    }

    async fn diff_setup_states(
        &self,
        _key: &serde_json::Value,
        desired_state: Option<serde_json::Value>,
        existing_states: setup::CombinedState<serde_json::Value>,
        _context: Arc<interface::FlowInstanceContext>,
    ) -> Result<Box<dyn setup::ResourceSetupChange>> {
        // Collect all possible existing states that are not the desired state.
        let mut stale_existing_states = IndexSet::new();
        if !existing_states.always_exists() && desired_state.is_some() {
            stale_existing_states.insert(None);
        }
        for possible_state in existing_states.possible_versions() {
            if Some(possible_state) != desired_state.as_ref() {
                stale_existing_states.insert(Some(possible_state.clone()));
            }
        }

        Ok(Box::new(PyTargetResourceSetupChange {
            stale_existing_states,
            desired_state,
        }))
    }

    fn normalize_setup_key(&self, key: &serde_json::Value) -> Result<serde_json::Value> {
        Ok(key.clone())
    }

    fn check_state_compatibility(
        &self,
        desired_state: &serde_json::Value,
        existing_state: &serde_json::Value,
    ) -> Result<SetupStateCompatibility> {
        let compatibility = Python::with_gil(|py| -> Result<_> {
            let result = self
                .py_target_connector
                .call_method(
                    py,
                    "check_state_compatibility",
                    (
                        pythonize(py, desired_state)?,
                        pythonize(py, existing_state)?,
                    ),
                    None,
                )
                .to_result_with_py_trace(py)?;
            let compatibility: SetupStateCompatibility = depythonize(&result.into_bound(py))?;
            Ok(compatibility)
        })?;
        Ok(compatibility)
    }

    fn describe_resource(&self, key: &serde_json::Value) -> Result<String> {
        Python::with_gil(|py| -> Result<String> {
            let result = self
                .py_target_connector
                .call_method(py, "describe_resource", (pythonize(py, key)?,), None)
                .to_result_with_py_trace(py)?;
            let description = result.extract::<String>(py)?;
            Ok(description)
        })
    }

    fn extract_additional_key(
        &self,
        _key: &value::KeyValue,
        _value: &value::FieldValues,
        _export_context: &(dyn Any + Send + Sync),
    ) -> Result<serde_json::Value> {
        Ok(serde_json::Value::Null)
    }

    async fn apply_setup_changes(
        &self,
        setup_change: Vec<interface::ResourceSetupChangeItem<'async_trait>>,
        context: Arc<interface::FlowInstanceContext>,
    ) -> Result<()> {
        // Filter the setup changes that are not NoChange, and flatten to
        //   `list[tuple[key, list[stale_existing_states | None], desired_state | None]]` for Python.
        let mut setup_changes = Vec::new();
        for item in setup_change.into_iter() {
            let decoded_setup_change = (item.setup_change as &dyn Any)
                .downcast_ref::<PyTargetResourceSetupChange>()
                .ok_or_else(invariance_violation)?;
            if <dyn setup::ResourceSetupChange>::change_type(decoded_setup_change)
                != setup::SetupChangeType::NoChange
            {
                setup_changes.push((
                    item.key,
                    &decoded_setup_change.stale_existing_states,
                    &decoded_setup_change.desired_state,
                ));
            }
        }

        if setup_changes.is_empty() {
            return Ok(());
        }

        // Call the `apply_setup_changes_async()` method.
        let py_exec_ctx = context
            .py_exec_ctx
            .as_ref()
            .ok_or_else(|| anyhow!("Python execution context is missing"))?
            .clone();
        let py_result = Python::with_gil(move |py| -> Result<_> {
            let result_coro = self
                .py_target_connector
                .call_method(
                    py,
                    "apply_setup_changes_async",
                    (pythonize(py, &setup_changes)?,),
                    None,
                )
                .to_result_with_py_trace(py)?;
            let task_locals =
                pyo3_async_runtimes::TaskLocals::new(py_exec_ctx.event_loop.bind(py).clone());
            Ok(pyo3_async_runtimes::into_future_with_locals(
                &task_locals,
                result_coro.into_bound(py),
            )?)
        })?
        .await;
        Python::with_gil(move |py| py_result.to_result_with_py_trace(py))?;

        Ok(())
    }

    async fn apply_mutation(
        &self,
        mutations: Vec<
            interface::ExportTargetMutationWithContext<'async_trait, dyn Any + Send + Sync>,
        >,
    ) -> Result<()> {
        if mutations.is_empty() {
            return Ok(());
        }

        let py_result = Python::with_gil(|py| -> Result<_> {
            // Create a `list[tuple[export_ctx, list[tuple[key, value | None]]]]` for Python, and collect `py_exec_ctx`.
            let mut py_args = Vec::with_capacity(mutations.len());
            let mut py_exec_ctx: Option<&Arc<crate::py::PythonExecutionContext>> = None;
            for mutation in mutations.into_iter() {
                // Downcast export_context to PyTargetExecutorContext.
                let export_context = (mutation.export_context as &dyn Any)
                    .downcast_ref::<PyTargetExecutorContext>()
                    .ok_or_else(invariance_violation)?;

                let mut flattened_mutations = Vec::with_capacity(
                    mutation.mutation.upserts.len() + mutation.mutation.deletes.len(),
                );
                for upsert in mutation.mutation.upserts.into_iter() {
                    flattened_mutations.push((
                        py::key_to_py_object(py, &upsert.key)?,
                        py::field_values_to_py_object(py, upsert.value.fields.iter())?,
                    ));
                }
                for delete in mutation.mutation.deletes.into_iter() {
                    flattened_mutations.push((
                        py::key_to_py_object(py, &delete.key)?,
                        py.None().into_bound(py),
                    ));
                }
                py_args.push((
                    &export_context.py_export_ctx,
                    PyList::new(py, flattened_mutations)?.into_any(),
                ));
                py_exec_ctx = py_exec_ctx.or(Some(&export_context.py_exec_ctx));
            }
            let py_exec_ctx = py_exec_ctx.ok_or_else(invariance_violation)?;

            let result_coro = self
                .py_target_connector
                .call_method(py, "mutate_async", (py_args,), None)
                .to_result_with_py_trace(py)?;
            let task_locals =
                pyo3_async_runtimes::TaskLocals::new(py_exec_ctx.event_loop.bind(py).clone());
            Ok(pyo3_async_runtimes::into_future_with_locals(
                &task_locals,
                result_coro.into_bound(py),
            )?)
        })?
        .await;

        Python::with_gil(move |py| py_result.to_result_with_py_trace(py))?;
        Ok(())
    }
}

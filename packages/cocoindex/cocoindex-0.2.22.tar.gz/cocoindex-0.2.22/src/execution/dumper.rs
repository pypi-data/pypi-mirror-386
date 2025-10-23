use crate::prelude::*;

use futures::{StreamExt, future::try_join_all};
use itertools::Itertools;
use serde::ser::SerializeSeq;
use sqlx::PgPool;
use std::path::{Path, PathBuf};
use yaml_rust2::YamlEmitter;

use super::evaluator::SourceRowEvaluationContext;
use super::memoization::EvaluationMemoryOptions;
use super::row_indexer;
use crate::base::{schema, value};
use crate::builder::plan::{AnalyzedImportOp, ExecutionPlan};
use crate::ops::interface::SourceExecutorReadOptions;
use crate::utils::yaml_ser::YamlSerializer;

#[derive(Debug, Clone, Deserialize)]
pub struct EvaluateAndDumpOptions {
    pub output_dir: String,
    pub use_cache: bool,
}

const FILENAME_PREFIX_MAX_LENGTH: usize = 128;

struct TargetExportData<'a> {
    schema: &'a Vec<schema::FieldSchema>,
    // The purpose is to make rows sorted by primary key.
    data: BTreeMap<value::KeyValue, &'a value::FieldValues>,
}

impl Serialize for TargetExportData<'_> {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        let mut seq = serializer.serialize_seq(Some(self.data.len()))?;
        for (_, values) in self.data.iter() {
            seq.serialize_element(&value::TypedFieldsValue {
                schema: self.schema,
                values_iter: values.fields.iter(),
            })?;
        }
        seq.end()
    }
}

#[derive(Serialize)]
struct SourceOutputData<'a> {
    key: value::TypedFieldsValue<'a, std::slice::Iter<'a, value::Value>>,

    #[serde(skip_serializing_if = "Option::is_none")]
    exports: Option<IndexMap<&'a str, TargetExportData<'a>>>,

    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}

struct Dumper<'a> {
    plan: &'a ExecutionPlan,
    setup_execution_ctx: &'a exec_ctx::FlowSetupExecutionContext,
    schema: &'a schema::FlowSchema,
    pool: &'a PgPool,
    options: EvaluateAndDumpOptions,
}

impl<'a> Dumper<'a> {
    async fn evaluate_source_entry<'b>(
        &'a self,
        import_op_idx: usize,
        import_op: &'a AnalyzedImportOp,
        key: &value::KeyValue,
        key_aux_info: &serde_json::Value,
        collected_values_buffer: &'b mut Vec<Vec<value::FieldValues>>,
    ) -> Result<Option<IndexMap<&'b str, TargetExportData<'b>>>>
    where
        'a: 'b,
    {
        let data_builder = row_indexer::evaluate_source_entry_with_memory(
            &SourceRowEvaluationContext {
                plan: self.plan,
                import_op,
                schema: self.schema,
                key,
                import_op_idx,
            },
            key_aux_info,
            self.setup_execution_ctx,
            EvaluationMemoryOptions {
                enable_cache: self.options.use_cache,
                evaluation_only: true,
            },
            self.pool,
        )
        .await?;

        let data_builder = if let Some(data_builder) = data_builder {
            data_builder
        } else {
            return Ok(None);
        };

        *collected_values_buffer = data_builder.collected_values;
        let exports = self
            .plan
            .export_ops
            .iter()
            .map(|export_op| -> Result<_> {
                let collector_idx = export_op.input.collector_idx as usize;
                let entry = (
                    export_op.name.as_str(),
                    TargetExportData {
                        schema: &self.schema.root_op_scope.collectors[collector_idx]
                            .spec
                            .fields,
                        data: collected_values_buffer[collector_idx]
                            .iter()
                            .map(|v| -> Result<_> {
                                let key = row_indexer::extract_primary_key_for_export(
                                    &export_op.primary_key_def,
                                    v,
                                )?;
                                Ok((key, v))
                            })
                            .collect::<Result<_>>()?,
                    },
                );
                Ok(entry)
            })
            .collect::<Result<_>>()?;
        Ok(Some(exports))
    }

    async fn evaluate_and_dump_source_entry(
        &self,
        import_op_idx: usize,
        import_op: &AnalyzedImportOp,
        key: value::KeyValue,
        key_aux_info: serde_json::Value,
        file_path: PathBuf,
    ) -> Result<()> {
        let _permit = import_op
            .concurrency_controller
            .acquire(concur_control::BYTES_UNKNOWN_YET)
            .await?;
        let mut collected_values_buffer = Vec::new();
        let (exports, error) = match self
            .evaluate_source_entry(
                import_op_idx,
                import_op,
                &key,
                &key_aux_info,
                &mut collected_values_buffer,
            )
            .await
        {
            Ok(exports) => (exports, None),
            Err(e) => (None, Some(format!("{e:?}"))),
        };
        let key_values: Vec<value::Value> = key.into_iter().map(|v| v.into()).collect::<Vec<_>>();
        let file_data = SourceOutputData {
            key: value::TypedFieldsValue {
                schema: &import_op.primary_key_schema,
                values_iter: key_values.iter(),
            },
            exports,
            error,
        };

        let yaml_output = {
            let mut yaml_output = String::new();
            let yaml_data = YamlSerializer::serialize(&file_data)?;
            let mut yaml_emitter = YamlEmitter::new(&mut yaml_output);
            yaml_emitter.multiline_strings(true);
            yaml_emitter.compact(true);
            yaml_emitter.dump(&yaml_data)?;
            yaml_output
        };
        tokio::fs::write(file_path, yaml_output).await?;

        Ok(())
    }

    async fn evaluate_and_dump_for_source(
        &self,
        import_op_idx: usize,
        import_op: &AnalyzedImportOp,
    ) -> Result<()> {
        let mut keys_by_filename_prefix: IndexMap<
            String,
            Vec<(value::KeyValue, serde_json::Value)>,
        > = IndexMap::new();

        let mut rows_stream = import_op
            .executor
            .list(&SourceExecutorReadOptions {
                include_ordinal: false,
                include_content_version_fp: false,
                include_value: false,
            })
            .await?;
        while let Some(rows) = rows_stream.next().await {
            for row in rows?.into_iter() {
                let mut s = row
                    .key
                    .encode_to_strs()
                    .into_iter()
                    .map(|s| urlencoding::encode(&s).into_owned())
                    .join(":");
                s.truncate(
                    (0..(FILENAME_PREFIX_MAX_LENGTH - import_op.name.as_str().len()))
                        .rev()
                        .find(|i| s.is_char_boundary(*i))
                        .unwrap_or(0),
                );
                keys_by_filename_prefix
                    .entry(s)
                    .or_default()
                    .push((row.key, row.key_aux_info));
            }
        }
        let output_dir = Path::new(&self.options.output_dir);
        let evaluate_futs =
            keys_by_filename_prefix
                .into_iter()
                .flat_map(|(filename_prefix, keys)| {
                    let num_keys = keys.len();
                    keys.into_iter()
                        .enumerate()
                        .map(move |(i, (key, key_aux_info))| {
                            let extra_id = if num_keys > 1 {
                                Cow::Owned(format!(".{i}"))
                            } else {
                                Cow::Borrowed("")
                            };
                            let file_name =
                                format!("{}@{}{}.yaml", import_op.name, filename_prefix, extra_id);
                            let file_path = output_dir.join(Path::new(&file_name));
                            self.evaluate_and_dump_source_entry(
                                import_op_idx,
                                import_op,
                                key,
                                key_aux_info,
                                file_path,
                            )
                        })
                });
        try_join_all(evaluate_futs).await?;
        Ok(())
    }

    async fn evaluate_and_dump(&self) -> Result<()> {
        try_join_all(
            self.plan
                .import_ops
                .iter()
                .enumerate()
                .map(|(idx, import_op)| self.evaluate_and_dump_for_source(idx, import_op)),
        )
        .await?;
        Ok(())
    }
}

pub async fn evaluate_and_dump(
    plan: &ExecutionPlan,
    setup_execution_ctx: &exec_ctx::FlowSetupExecutionContext,
    schema: &schema::FlowSchema,
    options: EvaluateAndDumpOptions,
    pool: &PgPool,
) -> Result<()> {
    let output_dir = Path::new(&options.output_dir);
    if output_dir.exists() {
        if !output_dir.is_dir() {
            return Err(anyhow::anyhow!("The path exists and is not a directory"));
        }
    } else {
        tokio::fs::create_dir(output_dir).await?;
    }

    let dumper = Dumper {
        plan,
        setup_execution_ctx,
        schema,
        pool,
        options,
    };
    dumper.evaluate_and_dump().await
}

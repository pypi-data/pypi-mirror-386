from dataclasses import dataclass
from enum import Enum


class LlmApiType(Enum):
    """The type of LLM API to use."""

    OPENAI = "OpenAi"
    OLLAMA = "Ollama"
    GEMINI = "Gemini"
    VERTEX_AI = "VertexAi"
    ANTHROPIC = "Anthropic"
    LITE_LLM = "LiteLlm"
    OPEN_ROUTER = "OpenRouter"
    VOYAGE = "Voyage"
    VLLM = "Vllm"
    BEDROCK = "Bedrock"


@dataclass
class VertexAiConfig:
    """A specification for a Vertex AI LLM."""

    kind = "VertexAi"

    project: str
    region: str | None = None


@dataclass
class OpenAiConfig:
    """A specification for a OpenAI LLM."""

    kind = "OpenAi"

    org_id: str | None = None
    project_id: str | None = None


@dataclass
class LlmSpec:
    """A specification for a LLM."""

    api_type: LlmApiType
    model: str
    address: str | None = None
    api_config: VertexAiConfig | OpenAiConfig | None = None

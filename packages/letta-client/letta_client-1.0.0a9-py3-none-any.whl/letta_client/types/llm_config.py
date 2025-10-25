# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .provider_category import ProviderCategory

__all__ = ["LlmConfig"]


class LlmConfig(BaseModel):
    context_window: int
    """The context window size for the model."""

    model: str
    """LLM model name."""

    api_model_endpoint_type: Literal[
        "openai",
        "anthropic",
        "google_ai",
        "google_vertex",
        "azure",
        "groq",
        "ollama",
        "webui",
        "webui-legacy",
        "lmstudio",
        "lmstudio-legacy",
        "lmstudio-chatcompletions",
        "llamacpp",
        "koboldcpp",
        "vllm",
        "hugging-face",
        "mistral",
        "together",
        "bedrock",
        "deepseek",
        "xai",
    ] = FieldInfo(alias="model_endpoint_type")
    """The endpoint type for the model."""

    compatibility_type: Optional[Literal["gguf", "mlx"]] = None
    """The framework compatibility type for the model."""

    display_name: Optional[str] = None
    """A human-friendly display name for the model."""

    enable_reasoner: Optional[bool] = None
    """
    Whether or not the model should use extended thinking if it is a 'reasoning'
    style model
    """

    frequency_penalty: Optional[float] = None
    """
    Positive values penalize new tokens based on their existing frequency in the
    text so far, decreasing the model's likelihood to repeat the same line verbatim.
    From OpenAI: Number between -2.0 and 2.0.
    """

    handle: Optional[str] = None
    """The handle for this config, in the format provider/model-name."""

    max_reasoning_tokens: Optional[int] = None
    """Configurable thinking budget for extended thinking.

    Used for enable_reasoner and also for Google Vertex models like Gemini 2.5
    Flash. Minimum value is 1024 when used with enable_reasoner.
    """

    max_tokens: Optional[int] = None
    """The maximum number of tokens to generate.

    If not set, the model will use its default value.
    """

    api_model_endpoint: Optional[str] = FieldInfo(alias="model_endpoint", default=None)
    """The endpoint for the model."""

    api_model_wrapper: Optional[str] = FieldInfo(alias="model_wrapper", default=None)
    """The wrapper for the model."""

    parallel_tool_calls: Optional[bool] = None
    """If set to True, enables parallel tool calling. Defaults to False."""

    provider_category: Optional[ProviderCategory] = None
    """The provider category for the model."""

    provider_name: Optional[str] = None
    """The provider name for the model."""

    put_inner_thoughts_in_kwargs: Optional[bool] = None
    """Puts 'inner_thoughts' as a kwarg in the function call if this is set to True.

    This helps with function calling performance and also the generation of inner
    thoughts.
    """

    reasoning_effort: Optional[Literal["minimal", "low", "medium", "high"]] = None
    """The reasoning effort to use when generating text reasoning models"""

    temperature: Optional[float] = None
    """The temperature to use when generating text with the model.

    A higher temperature will result in more random text.
    """

    tier: Optional[str] = None
    """The cost tier for the model (cloud only)."""

    verbosity: Optional[Literal["low", "medium", "high"]] = None
    """Soft control for how verbose model output should be, used for GPT-5 models."""

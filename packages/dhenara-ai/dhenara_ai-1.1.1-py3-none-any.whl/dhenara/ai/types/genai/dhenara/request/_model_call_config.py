import logging
from typing import Literal

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, model_validator

from dhenara.ai.types.genai.ai_model import AIModel
from dhenara.ai.types.genai.dhenara.request import (
    ArtifactConfig,
    StructuredOutputConfig,
    ToolChoice,
    ToolDefinition,
)
from dhenara.ai.types.shared.base import BaseModel

logger = logging.getLogger(__name__)


# TODO_FUTURE:
# Create seperate class for the parameter required conversion,
# class AIModelCallData(BaseModel):
#    tools: list[ToolDefinition] | None = None
#    tool_choice: ToolChoice | None = None
#    structured_output: StructuredOutputConfig | None = None


class AIModelCallConfig(BaseModel):
    """Configuration for AI model calls"""

    streaming: bool = False
    max_output_tokens: int | None = None
    reasoning: bool = False
    max_reasoning_tokens: int | None = Field(
        default=None,
        help="Maximum reasoning tokens when reasoning is enabled. Ignored for OpenAI APIs",
    )
    reasoning_effort: Literal["minimal", "low", "medium", "high"] | None = Field(
        default=None,
        help="OpenAI version to control thinking/reasoning tokens when reasoning is enabled. "
        "Ignored for other providers",
    )
    options: dict = {}

    tools: list[ToolDefinition] | None = None
    tool_choice: ToolChoice | None = None

    structured_output: type[PydanticBaseModel] | StructuredOutputConfig | None = None

    metadata: dict = {}
    timeout: float | None = None
    retries: int = 3
    retry_delay: float = 1.0
    max_retry_delay: float = 10.0
    test_mode: bool = False
    api_version_override: str | None = None

    artifact_config: ArtifactConfig | None = None

    @model_validator(mode="after")
    def validate_structured_output(self) -> "AIModelCallConfig":
        if isinstance(self.structured_output, type):
            try:
                if issubclass(self.structured_output, PydanticBaseModel):
                    self.structured_output = StructuredOutputConfig.from_model(
                        model_class=self.structured_output,
                    )
            except TypeError:
                # If PydanticBaseModel isn't a proper class in this environment, skip conversion
                pass
        return self

    def get_user(self):
        user = self.metadata.get("user", None)
        if not user:
            user = self.metadata.get("user_id", None)

        return user

    def get_max_output_tokens(self, model: AIModel) -> tuple[int, int | None]:
        """Returns max_output_tokens and max_reasoning_tokens based on the model settings and call-config"""

        if not model:
            raise ValueError("Model should be passed when max_token is not set in the call-config")

        _settings = model.get_settings()

        # Determine which max output tokens to use based on reasoning mode
        if not self.reasoning:
            _settings_max_output_tokens = _settings.max_output_tokens
            _reasoning_capable = False
        elif not _settings.supports_reasoning:  # Don't flag an error
            _settings_max_output_tokens = _settings.max_output_tokens
            _reasoning_capable = False
        else:
            _settings_max_output_tokens = _settings.max_output_tokens_reasoning_mode
            _reasoning_capable = True

        if not _settings_max_output_tokens:
            token_type = "max_output_tokens_reasoning_mode" if _reasoning_capable else "max_output_tokens"
            raise ValueError(f"Invalid call-config. {token_type} is not set in model {model.model_name}.")

        # Set max output tokens
        max_output_tokens = min(
            self.max_output_tokens if self.max_output_tokens is not None else _settings_max_output_tokens,
            _settings_max_output_tokens,
        )

        # Set max reasoning tokens
        if not _reasoning_capable or not self.reasoning or _settings.max_reasoning_tokens is None:
            max_reasoning_tokens = None
        else:
            max_reasoning_tokens = min(
                self.max_reasoning_tokens if self.max_reasoning_tokens is not None else _settings.max_reasoning_tokens,
                _settings.max_reasoning_tokens,
            )

        return (max_output_tokens, max_reasoning_tokens)

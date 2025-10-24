from collections.abc import Mapping
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from shai_plugin.entities.model import BaseModelConfig, ModelType, ModelUsage, PriceInfo
from shai_plugin.entities.model.message import (
    AssistantPromptMessage,
    PromptMessage,
)


class LLMMode(Enum):
    """
    Enum class for large language model mode.
    """

    COMPLETION = "completion"
    CHAT = "chat"

    @classmethod
    def value_of(cls, value: str) -> "LLMMode":
        """
        Get value of given mode.

        :param value: mode value
        :return: mode
        """
        for mode in cls:
            if mode.value == value:
                return mode
        raise ValueError(f"invalid mode value {value}")


class LLMUsage(ModelUsage):
    """
    Model class for llm usage.
    """

    prompt_tokens: int
    prompt_unit_price: Decimal
    prompt_price_unit: Decimal
    prompt_price: Decimal
    completion_tokens: int
    completion_unit_price: Decimal
    completion_price_unit: Decimal
    completion_price: Decimal
    total_tokens: int
    total_price: Decimal
    currency: str
    latency: float

    @classmethod
    def empty_usage(cls):
        return cls(
            prompt_tokens=0,
            prompt_unit_price=Decimal("0.0"),
            prompt_price_unit=Decimal("0.0"),
            prompt_price=Decimal("0.0"),
            completion_tokens=0,
            completion_unit_price=Decimal("0.0"),
            completion_price_unit=Decimal("0.0"),
            completion_price=Decimal("0.0"),
            total_tokens=0,
            total_price=Decimal("0.0"),
            currency="USD",
            latency=0.0,
        )


class LLMResultChunkDelta(BaseModel):
    """
    Model class for llm result chunk delta.
    """

    index: int
    message: AssistantPromptMessage
    usage: LLMUsage | None = None
    finish_reason: str | None = None


class LLMResultChunk(BaseModel):
    """
    Model class for llm result chunk.
    """

    model: str
    prompt_messages: list[PromptMessage] = Field(default_factory=list)
    system_fingerprint: str | None = None
    delta: LLMResultChunkDelta

    @field_validator("prompt_messages", mode="before")
    @classmethod
    def transform_prompt_messages(cls, value):
        """
        ISSUE:
        - https://github.com/langgenius/shai/issues/17799
        - https://github.com/langgenius/shai-official-plugins/issues/648

        The `prompt_messages` field is deprecated, but to keep backward compatibility
        we need to always set it to an empty list.

        NOTE: just do not use it anymore, it will be removed in the future.
        """
        return []


class LLMStructuredOutput(BaseModel):
    """
    Model class for llm structured output.
    """

    structured_output: Mapping | None = None


class LLMResultChunkWithStructuredOutput(LLMResultChunk, LLMStructuredOutput):
    """
    Model class for llm result chunk with structured output.
    """

    pass


class LLMResult(BaseModel):
    """
    Model class for llm result.
    """

    model: str
    prompt_messages: list[PromptMessage] = Field(default_factory=list)
    message: AssistantPromptMessage
    usage: LLMUsage
    system_fingerprint: str | None = None

    @field_validator("prompt_messages", mode="before")
    @classmethod
    def transform_prompt_messages(cls, value):
        """
        ISSUE:
        - https://github.com/langgenius/shai/issues/17799
        - https://github.com/langgenius/shai-official-plugins/issues/648

        The `prompt_messages` field is deprecated, but to keep backward compatibility
        we need to always set it to an empty list.

        NOTE: just do not use it anymore, it will be removed in the future.
        """
        return []

    def to_llm_result_chunk(self) -> "LLMResultChunk":
        return LLMResultChunk(
            model=self.model,
            system_fingerprint=self.system_fingerprint,
            delta=LLMResultChunkDelta(
                index=0,
                message=self.message,
                usage=self.usage,
                finish_reason=None,
            ),
        )


class LLMResultWithStructuredOutput(LLMResult, LLMStructuredOutput):
    """
    Model class for llm result with structured output.
    """

    def to_llm_result_chunk_with_structured_output(self) -> "LLMResultChunkWithStructuredOutput":
        return LLMResultChunkWithStructuredOutput(
            model=self.model,
            system_fingerprint=self.system_fingerprint,
            delta=LLMResultChunkDelta(
                index=0,
                message=self.message,
                usage=self.usage,
                finish_reason=None,
            ),
            structured_output=self.structured_output,
        )


class SummaryResult(BaseModel):
    """
    Model class for summary result.
    """

    summary: str


class NumTokensResult(PriceInfo):
    """
    Model class for number of tokens result.
    """

    tokens: int


class LLMModelConfig(BaseModelConfig):
    """
    Model class for llm model config.
    """

    model_type: ModelType = ModelType.LLM
    mode: str
    completion_params: dict = Field(default_factory=dict)

    model_config = ConfigDict(protected_namespaces=())

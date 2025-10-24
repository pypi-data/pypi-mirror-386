from collections.abc import Mapping
from enum import Enum
from typing import Any, Union

from pydantic import BaseModel, Field, field_validator

from shai_plugin.core.documentation.schema_doc import docs
from shai_plugin.core.utils.yaml_loader import load_yaml_file
from shai_plugin.entities import I18nObject
from shai_plugin.entities.invoke_message import InvokeMessage
from shai_plugin.entities.tool import (
    CommonParameterType,
    ParameterAutoGenerate,
    ParameterTemplate,
    ToolIdentity,
    ToolParameterOption,
    ToolProviderIdentity,
)


@docs(
    description="The identity of the agent strategy provider",
)
class AgentStrategyProviderIdentity(ToolProviderIdentity):
    pass


class AgentRuntime(BaseModel):
    user_id: str | None


@docs(
    description="The feature of the agent strategy",
)
class AgentStrategyFeature(str, Enum):
    HISTORY_MESSAGES = "history-messages"


@docs(
    description="The identity of the agent strategy",
)
class AgentStrategyIdentity(ToolIdentity):
    pass


@docs(
    description="The parameter of the agent strategy",
)
class AgentStrategyParameter(BaseModel):
    class ToolParameterType(str, Enum):
        STRING = CommonParameterType.STRING.value
        NUMBER = CommonParameterType.NUMBER.value
        BOOLEAN = CommonParameterType.BOOLEAN.value
        SELECT = CommonParameterType.SELECT.value
        SECRET_INPUT = CommonParameterType.SECRET_INPUT.value
        FILE = CommonParameterType.FILE.value
        FILES = CommonParameterType.FILES.value
        MODEL_SELECTOR = CommonParameterType.MODEL_SELECTOR.value
        APP_SELECTOR = CommonParameterType.APP_SELECTOR.value
        TOOLS_SELECTOR = CommonParameterType.TOOLS_SELECTOR.value
        # TOOL_SELECTOR = CommonParameterType.TOOL_SELECTOR.value
        ANY = CommonParameterType.ANY.value
        # MCP object and array type parameters
        OBJECT = CommonParameterType.OBJECT.value
        ARRAY = CommonParameterType.ARRAY.value

    name: str = Field(..., description="The name of the parameter")
    label: I18nObject = Field(..., description="The label presented to the user")
    help: I18nObject | None = None
    type: ToolParameterType = Field(..., description="The type of the parameter")
    auto_generate: ParameterAutoGenerate | None = Field(default=None, description="The auto generate of the parameter")
    template: ParameterTemplate | None = Field(default=None, description="The template of the parameter")
    scope: str | None = None
    required: bool | None = False
    default: Union[int, float, str] | None = None
    min: Union[float, int] | None = None
    max: Union[float, int] | None = None
    precision: int | None = None
    options: list[ToolParameterOption] | None = None


@docs(
    name="Python",
    description="The extra of the agent strategy",
)
class Python(BaseModel):
    source: str


@docs(
    name="AgentStrategyExtra",
    description="The extra of the agent strategy",
)
class AgentStrategyConfigurationExtra(BaseModel):
    python: Python


@docs(
    name="AgentStrategy",
    description="The Manifest of the agent strategy",
)
class AgentStrategyConfiguration(BaseModel):
    identity: AgentStrategyIdentity
    parameters: list[AgentStrategyParameter] = Field(default=[], description="The parameters of the agent")
    description: I18nObject
    extra: AgentStrategyConfigurationExtra
    has_runtime_parameters: bool = Field(default=False, description="Whether the tool has runtime parameters")
    output_schema: Mapping[str, Any] | None = None
    features: list[AgentStrategyFeature] = Field(default=[], description="The features of the agent")


@docs(
    name="AgentStrategyProviderExtra",
    description="The extra of the agent provider",
)
class AgentProviderConfigurationExtra(BaseModel):
    @docs(
        name="Python",
        description="The extra of the agent provider",
    )
    class Python(BaseModel):
        source: str

    python: Python


@docs(
    name="AgentStrategyProvider",
    description="The Manifest of the agent strategy provider",
    outside_reference_fields={"strategies": AgentStrategyConfiguration},
)
class AgentStrategyProviderConfiguration(BaseModel):
    identity: AgentStrategyProviderIdentity
    strategies: list[AgentStrategyConfiguration] = Field(default=[], description="The strategies of the agent provider")

    @field_validator("strategies", mode="before")
    @classmethod
    def validate_strategies(cls, value) -> list[AgentStrategyConfiguration]:
        if not isinstance(value, list):
            raise ValueError("strategies should be a list")

        strategies: list[AgentStrategyConfiguration] = []

        for strategy in value:
            # read from yaml
            if not isinstance(strategy, str):
                raise ValueError("strategy path should be a string")
            try:
                file = load_yaml_file(strategy)
                strategies.append(
                    AgentStrategyConfiguration(
                        **{
                            "identity": AgentStrategyIdentity(**file["identity"]),
                            "parameters": [
                                AgentStrategyParameter(**param) for param in file.get("parameters", []) or []
                            ],
                            "description": I18nObject(**file["description"]),
                            "extra": AgentStrategyConfigurationExtra(**file.get("extra", {})),
                            "features": file.get("features", []),
                        }
                    )
                )
            except Exception as e:
                raise ValueError(f"Error loading agent strategy configuration: {e!s}") from e

        return strategies


class AgentInvokeMessage(InvokeMessage):
    pass

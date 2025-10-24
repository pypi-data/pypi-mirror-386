from collections.abc import Mapping
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from shai_plugin.entities.datasource import (
    GetOnlineDocumentPageContentRequest,
    OnlineDriveBrowseFilesRequest,
    OnlineDriveDownloadFileRequest,
)
from shai_plugin.entities.model import ModelType
from shai_plugin.entities.model.message import (
    AssistantPromptMessage,
    PromptMessage,
    PromptMessageRole,
    PromptMessageTool,
    SystemPromptMessage,
    ToolPromptMessage,
    UserPromptMessage,
)
from shai_plugin.entities.provider_config import CredentialType


class PluginInvokeType(StrEnum):
    Tool = "tool"
    Model = "model"
    Endpoint = "endpoint"
    Agent = "agent_strategy"
    OAuth = "oauth"
    Datasource = "datasource"
    DynamicParameter = "dynamic_parameter"


class AgentActions(StrEnum):
    InvokeAgentStrategy = "invoke_agent_strategy"


class ToolActions(StrEnum):
    ValidateCredentials = "validate_tool_credentials"
    InvokeTool = "invoke_tool"
    GetToolRuntimeParameters = "get_tool_runtime_parameters"


class ModelActions(StrEnum):
    ValidateProviderCredentials = "validate_provider_credentials"
    ValidateModelCredentials = "validate_model_credentials"
    InvokeLLM = "invoke_llm"
    GetLLMNumTokens = "get_llm_num_tokens"
    InvokeTextEmbedding = "invoke_text_embedding"
    GetTextEmbeddingNumTokens = "get_text_embedding_num_tokens"
    InvokeRerank = "invoke_rerank"
    InvokeTTS = "invoke_tts"
    GetTTSVoices = "get_tts_model_voices"
    InvokeSpeech2Text = "invoke_speech2text"
    InvokeModeration = "invoke_moderation"
    GetAIModelSchemas = "get_ai_model_schemas"


class EndpointActions(StrEnum):
    InvokeEndpoint = "invoke_endpoint"


class OAuthActions(StrEnum):
    GetAuthorizationUrl = "get_authorization_url"
    GetCredentials = "get_credentials"
    RefreshCredentials = "refresh_credentials"


class DatasourceActions(StrEnum):
    ValidateCredentials = "validate_datasource_credentials"
    InvokeWebsiteDatasourceGetCrawl = "invoke_website_datasource_get_crawl"
    InvokeOnlineDocumentDatasourceGetPages = "invoke_online_document_datasource_get_pages"
    InvokeOnlineDocumentDatasourceGetPageContent = "invoke_online_document_datasource_get_page_content"
    InvokeOnlineDriveBrowseFiles = "invoke_online_drive_browse_files"
    InvokeOnlineDriveDownloadFile = "invoke_online_drive_download_file"


class DynamicParameterActions(StrEnum):
    FetchParameterOptions = "fetch_parameter_options"


# merge all the access actions
PluginAccessAction = AgentActions | ToolActions | ModelActions | EndpointActions | DynamicParameterActions


class PluginAccessRequest(BaseModel):
    type: PluginInvokeType
    user_id: str


class ToolInvokeRequest(PluginAccessRequest):
    type: PluginInvokeType = PluginInvokeType.Tool
    action: ToolActions = ToolActions.InvokeTool
    provider: str
    tool: str
    credentials: dict
    credential_type: CredentialType = CredentialType.API_KEY
    tool_parameters: dict[str, Any]


class AgentInvokeRequest(PluginAccessRequest):
    type: PluginInvokeType = PluginInvokeType.Agent
    action: AgentActions = AgentActions.InvokeAgentStrategy
    agent_strategy_provider: str
    agent_strategy: str
    agent_strategy_params: dict[str, Any]


class ToolValidateCredentialsRequest(PluginAccessRequest):
    type: PluginInvokeType = PluginInvokeType.Tool
    action: ToolActions = ToolActions.ValidateCredentials
    provider: str
    credentials: dict


class ToolGetRuntimeParametersRequest(PluginAccessRequest):
    type: PluginInvokeType = PluginInvokeType.Tool
    action: ToolActions = ToolActions.GetToolRuntimeParameters
    provider: str
    tool: str
    credentials: dict


class PluginAccessModelRequest(BaseModel):
    type: PluginInvokeType = PluginInvokeType.Model
    user_id: str
    provider: str
    model_type: ModelType
    model: str
    credentials: dict

    model_config = ConfigDict(protected_namespaces=())


class PromptMessageMixin(BaseModel):
    prompt_messages: list[PromptMessage]

    @field_validator("prompt_messages", mode="before")
    @classmethod
    def convert_prompt_messages(cls, v):
        if not isinstance(v, list):
            raise ValueError("prompt_messages must be a list")

        for i in range(len(v)):
            if isinstance(v[i], PromptMessage):
                continue

            if v[i]["role"] == PromptMessageRole.USER.value:
                v[i] = UserPromptMessage(**v[i])
            elif v[i]["role"] == PromptMessageRole.ASSISTANT.value:
                v[i] = AssistantPromptMessage(**v[i])
            elif v[i]["role"] == PromptMessageRole.SYSTEM.value:
                v[i] = SystemPromptMessage(**v[i])
            elif v[i]["role"] == PromptMessageRole.TOOL.value:
                v[i] = ToolPromptMessage(**v[i])
            else:
                v[i] = PromptMessage(**v[i])

        return v


class ModelInvokeLLMRequest(PluginAccessModelRequest, PromptMessageMixin):
    action: ModelActions = ModelActions.InvokeLLM

    model_parameters: dict[str, Any]
    stop: list[str] | None
    tools: list[PromptMessageTool] | None
    stream: bool = True

    model_config = ConfigDict(protected_namespaces=())


class ModelGetLLMNumTokens(PluginAccessModelRequest, PromptMessageMixin):
    action: ModelActions = ModelActions.GetLLMNumTokens

    tools: list[PromptMessageTool] | None


class ModelInvokeTextEmbeddingRequest(PluginAccessModelRequest):
    action: ModelActions = ModelActions.InvokeTextEmbedding

    texts: list[str]


class ModelGetTextEmbeddingNumTokens(PluginAccessModelRequest):
    action: ModelActions = ModelActions.GetTextEmbeddingNumTokens

    texts: list[str]


class ModelInvokeRerankRequest(PluginAccessModelRequest):
    action: ModelActions = ModelActions.InvokeRerank

    query: str
    docs: list[str]
    score_threshold: float | None
    top_n: int | None


class ModelInvokeTTSRequest(PluginAccessModelRequest):
    action: ModelActions = ModelActions.InvokeTTS

    content_text: str
    voice: str
    tenant_id: str


class ModelGetTTSVoices(PluginAccessModelRequest):
    action: ModelActions = ModelActions.GetTTSVoices

    language: str | None


class ModelInvokeSpeech2TextRequest(PluginAccessModelRequest):
    action: ModelActions = ModelActions.InvokeSpeech2Text

    file: str


class ModelInvokeModerationRequest(PluginAccessModelRequest):
    action: ModelActions = ModelActions.InvokeModeration

    text: str


class ModelValidateProviderCredentialsRequest(BaseModel):
    type: PluginInvokeType = PluginInvokeType.Model
    user_id: str
    provider: str
    credentials: dict

    action: ModelActions = ModelActions.ValidateProviderCredentials

    model_config = ConfigDict(protected_namespaces=())


class ModelValidateModelCredentialsRequest(BaseModel):
    type: PluginInvokeType = PluginInvokeType.Model
    user_id: str
    provider: str
    model_type: ModelType
    model: str
    credentials: dict

    action: ModelActions = ModelActions.ValidateModelCredentials

    model_config = ConfigDict(protected_namespaces=())


class ModelGetAIModelSchemas(PluginAccessModelRequest):
    action: ModelActions = ModelActions.GetAIModelSchemas


class EndpointInvokeRequest(BaseModel):
    type: PluginInvokeType = PluginInvokeType.Endpoint
    action: EndpointActions = EndpointActions.InvokeEndpoint
    settings: dict
    raw_http_request: str


class OAuthGetAuthorizationUrlRequest(PluginAccessRequest):
    type: PluginInvokeType = PluginInvokeType.OAuth
    action: OAuthActions = OAuthActions.GetAuthorizationUrl
    provider: str
    redirect_uri: str
    system_credentials: Mapping[str, Any]


class OAuthGetCredentialsRequest(PluginAccessRequest):
    type: PluginInvokeType = PluginInvokeType.OAuth
    action: OAuthActions = OAuthActions.GetCredentials
    provider: str
    redirect_uri: str
    system_credentials: Mapping[str, Any]
    raw_http_request: str


class OAuthRefreshCredentialsRequest(PluginAccessRequest):
    type: PluginInvokeType = PluginInvokeType.OAuth
    action: OAuthActions = OAuthActions.RefreshCredentials
    provider: str
    redirect_uri: str
    system_credentials: Mapping[str, Any]
    credentials: Mapping[str, Any]


class DynamicParameterFetchParameterOptionsRequest(BaseModel):
    type: PluginInvokeType = PluginInvokeType.DynamicParameter
    action: DynamicParameterActions = DynamicParameterActions.FetchParameterOptions
    credentials: dict
    provider: str
    provider_action: str
    user_id: str
    parameter: str

    model_config = ConfigDict(protected_namespaces=())


class DatasourceValidateCredentialsRequest(PluginAccessRequest):
    type: PluginInvokeType = PluginInvokeType.Datasource
    action: DatasourceActions = DatasourceActions.ValidateCredentials
    provider: str
    credentials: Mapping[str, Any]


class DatasourceCrawlWebsiteRequest(PluginAccessRequest):
    type: PluginInvokeType = PluginInvokeType.Datasource
    action: DatasourceActions = DatasourceActions.InvokeWebsiteDatasourceGetCrawl
    provider: str
    datasource: str
    credentials: Mapping[str, Any]
    datasource_parameters: Mapping[str, Any]


class DatasourceGetPagesRequest(PluginAccessRequest):
    type: PluginInvokeType = PluginInvokeType.Datasource
    action: DatasourceActions = DatasourceActions.InvokeOnlineDocumentDatasourceGetPages
    provider: str
    datasource: str
    credentials: Mapping[str, Any]
    datasource_parameters: Mapping[str, Any]


class DatasourceGetPageContentRequest(PluginAccessRequest):
    type: PluginInvokeType = PluginInvokeType.Datasource
    action: DatasourceActions = DatasourceActions.InvokeOnlineDocumentDatasourceGetPageContent
    provider: str
    datasource: str
    credentials: Mapping[str, Any]
    page: GetOnlineDocumentPageContentRequest


class DatasourceOnlineDriveBrowseFilesRequest(PluginAccessRequest):
    type: PluginInvokeType = PluginInvokeType.Datasource
    action: DatasourceActions = DatasourceActions.InvokeOnlineDriveBrowseFiles
    provider: str
    datasource: str
    credentials: Mapping[str, Any]
    request: OnlineDriveBrowseFilesRequest


class DatasourceOnlineDriveDownloadFileRequest(PluginAccessRequest):
    type: PluginInvokeType = PluginInvokeType.Datasource
    action: DatasourceActions = DatasourceActions.InvokeOnlineDriveDownloadFile
    provider: str
    datasource: str
    credentials: Mapping[str, Any]
    request: OnlineDriveDownloadFileRequest

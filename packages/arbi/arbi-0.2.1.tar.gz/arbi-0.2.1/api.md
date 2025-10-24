# API

Types:

```python
from arbi.types import Chunk, ChunkMetadata
```

Methods:

- <code title="get /api">client.api.<a href="./src/arbi/resources/api/api.py">index</a>() -> object</code>

## User

Types:

```python
from arbi.types.api import (
    Token,
    UserResponse,
    UserListWorkspacesResponse,
    UserLogoutResponse,
    UserVerifyEmailResponse,
)
```

Methods:

- <code title="get /api/user/workspaces">client.api.user.<a href="./src/arbi/resources/api/user/user.py">list_workspaces</a>() -> <a href="./src/arbi/types/api/user_list_workspaces_response.py">UserListWorkspacesResponse</a></code>
- <code title="post /api/user/login">client.api.user.<a href="./src/arbi/resources/api/user/user.py">login</a>(\*\*<a href="src/arbi/types/api/user_login_params.py">params</a>) -> <a href="./src/arbi/types/api/token.py">Token</a></code>
- <code title="post /api/user/logout">client.api.user.<a href="./src/arbi/resources/api/user/user.py">logout</a>() -> <a href="./src/arbi/types/api/user_logout_response.py">UserLogoutResponse</a></code>
- <code title="post /api/user/token_refresh">client.api.user.<a href="./src/arbi/resources/api/user/user.py">refresh_token</a>() -> <a href="./src/arbi/types/api/token.py">Token</a></code>
- <code title="post /api/user/register">client.api.user.<a href="./src/arbi/resources/api/user/user.py">register</a>(\*\*<a href="src/arbi/types/api/user_register_params.py">params</a>) -> <a href="./src/arbi/types/api/user_response.py">UserResponse</a></code>
- <code title="get /api/user/me">client.api.user.<a href="./src/arbi/resources/api/user/user.py">retrieve_me</a>() -> <a href="./src/arbi/types/api/user_response.py">UserResponse</a></code>
- <code title="post /api/user/verify-email">client.api.user.<a href="./src/arbi/resources/api/user/user.py">verify_email</a>(\*\*<a href="src/arbi/types/api/user_verify_email_params.py">params</a>) -> <a href="./src/arbi/types/api/user_verify_email_response.py">UserVerifyEmailResponse</a></code>

### Settings

Types:

```python
from arbi.types.api.user import SettingRetrieveResponse
```

Methods:

- <code title="get /api/user/settings">client.api.user.settings.<a href="./src/arbi/resources/api/user/settings.py">retrieve</a>() -> <a href="./src/arbi/types/api/user/setting_retrieve_response.py">SettingRetrieveResponse</a></code>
- <code title="patch /api/user/settings">client.api.user.settings.<a href="./src/arbi/resources/api/user/settings.py">update</a>(\*\*<a href="src/arbi/types/api/user/setting_update_params.py">params</a>) -> None</code>

## SSO

Types:

```python
from arbi.types.api import SSOInviteResponse, SSOLoginResponse, SSORotatePasscodeResponse
```

Methods:

- <code title="post /api/sso/invite">client.api.sso.<a href="./src/arbi/resources/api/sso.py">invite</a>(\*\*<a href="src/arbi/types/api/sso_invite_params.py">params</a>) -> <a href="./src/arbi/types/api/sso_invite_response.py">SSOInviteResponse</a></code>
- <code title="post /api/sso/login">client.api.sso.<a href="./src/arbi/resources/api/sso.py">login</a>(\*\*<a href="src/arbi/types/api/sso_login_params.py">params</a>) -> <a href="./src/arbi/types/api/sso_login_response.py">SSOLoginResponse</a></code>
- <code title="post /api/sso/rotate_passcode">client.api.sso.<a href="./src/arbi/resources/api/sso.py">rotate_passcode</a>() -> <a href="./src/arbi/types/api/sso_rotate_passcode_response.py">SSORotatePasscodeResponse</a></code>

## Workspace

Types:

```python
from arbi.types.api import (
    WorkspaceResponse,
    WorkspaceDeleteResponse,
    WorkspaceGetConversationsResponse,
    WorkspaceGetDoctagsResponse,
    WorkspaceGetDocumentsResponse,
    WorkspaceGetStatsResponse,
    WorkspaceGetTagsResponse,
    WorkspaceGetUsersResponse,
    WorkspaceRemoveUserResponse,
    WorkspaceShareResponse,
)
```

Methods:

- <code title="patch /api/workspace/{workspace_ext_id}">client.api.workspace.<a href="./src/arbi/resources/api/workspace.py">update</a>(workspace_ext_id, \*\*<a href="src/arbi/types/api/workspace_update_params.py">params</a>) -> <a href="./src/arbi/types/api/workspace_response.py">WorkspaceResponse</a></code>
- <code title="delete /api/workspace/{workspace_ext_id}">client.api.workspace.<a href="./src/arbi/resources/api/workspace.py">delete</a>(workspace_ext_id) -> <a href="./src/arbi/types/api/workspace_delete_response.py">WorkspaceDeleteResponse</a></code>
- <code title="post /api/workspace/create_protected">client.api.workspace.<a href="./src/arbi/resources/api/workspace.py">create_protected</a>(\*\*<a href="src/arbi/types/api/workspace_create_protected_params.py">params</a>) -> <a href="./src/arbi/types/api/workspace_response.py">WorkspaceResponse</a></code>
- <code title="get /api/workspace/{workspace_ext_id}/conversations">client.api.workspace.<a href="./src/arbi/resources/api/workspace.py">get_conversations</a>(workspace_ext_id) -> <a href="./src/arbi/types/api/workspace_get_conversations_response.py">WorkspaceGetConversationsResponse</a></code>
- <code title="get /api/workspace/{workspace_ext_id}/doctags">client.api.workspace.<a href="./src/arbi/resources/api/workspace.py">get_doctags</a>(workspace_ext_id) -> <a href="./src/arbi/types/api/workspace_get_doctags_response.py">WorkspaceGetDoctagsResponse</a></code>
- <code title="get /api/workspace/{workspace_ext_id}/documents">client.api.workspace.<a href="./src/arbi/resources/api/workspace.py">get_documents</a>(workspace_ext_id) -> <a href="./src/arbi/types/api/workspace_get_documents_response.py">WorkspaceGetDocumentsResponse</a></code>
- <code title="get /api/workspace/{workspace_ext_id}/stats">client.api.workspace.<a href="./src/arbi/resources/api/workspace.py">get_stats</a>(workspace_ext_id) -> <a href="./src/arbi/types/api/workspace_get_stats_response.py">WorkspaceGetStatsResponse</a></code>
- <code title="get /api/workspace/{workspace_ext_id}/tags">client.api.workspace.<a href="./src/arbi/resources/api/workspace.py">get_tags</a>(workspace_ext_id) -> <a href="./src/arbi/types/api/workspace_get_tags_response.py">WorkspaceGetTagsResponse</a></code>
- <code title="get /api/workspace/{workspace_ext_id}/users">client.api.workspace.<a href="./src/arbi/resources/api/workspace.py">get_users</a>(workspace_ext_id) -> <a href="./src/arbi/types/api/workspace_get_users_response.py">WorkspaceGetUsersResponse</a></code>
- <code title="delete /api/workspace/{workspace_ext_id}/user">client.api.workspace.<a href="./src/arbi/resources/api/workspace.py">remove_user</a>(workspace_ext_id, \*\*<a href="src/arbi/types/api/workspace_remove_user_params.py">params</a>) -> <a href="./src/arbi/types/api/workspace_remove_user_response.py">WorkspaceRemoveUserResponse</a></code>
- <code title="post /api/workspace/{workspace_ext_id}/share">client.api.workspace.<a href="./src/arbi/resources/api/workspace.py">share</a>(workspace_ext_id, \*\*<a href="src/arbi/types/api/workspace_share_params.py">params</a>) -> <a href="./src/arbi/types/api/workspace_share_response.py">WorkspaceShareResponse</a></code>

## Document

Types:

```python
from arbi.types.api import (
    DocResponse,
    DocumentUpdateResponse,
    DocumentDeleteResponse,
    DocumentGetParsedResponse,
    DocumentGetTagsResponse,
)
```

Methods:

- <code title="patch /api/document/{document_ext_id}">client.api.document.<a href="./src/arbi/resources/api/document/document.py">update</a>(document_ext_id, \*\*<a href="src/arbi/types/api/document_update_params.py">params</a>) -> <a href="./src/arbi/types/api/document_update_response.py">DocumentUpdateResponse</a></code>
- <code title="delete /api/document/{document_ext_id}">client.api.document.<a href="./src/arbi/resources/api/document/document.py">delete</a>(document_ext_id) -> <a href="./src/arbi/types/api/document_delete_response.py">DocumentDeleteResponse</a></code>
- <code title="get /api/document/{document_ext_id}/download">client.api.document.<a href="./src/arbi/resources/api/document/document.py">download</a>(document_ext_id) -> object</code>
- <code title="get /api/document/{document_ext_id}">client.api.document.<a href="./src/arbi/resources/api/document/document.py">get</a>(document_ext_id) -> <a href="./src/arbi/types/api/doc_response.py">DocResponse</a></code>
- <code title="get /api/document/{document_ext_id}/parsed-{stage}">client.api.document.<a href="./src/arbi/resources/api/document/document.py">get_parsed</a>(stage, \*, document_ext_id) -> <a href="./src/arbi/types/api/document_get_parsed_response.py">DocumentGetParsedResponse</a></code>
- <code title="get /api/document/{doc_ext_id}/tags">client.api.document.<a href="./src/arbi/resources/api/document/document.py">get_tags</a>(doc_ext_id) -> <a href="./src/arbi/types/api/document_get_tags_response.py">DocumentGetTagsResponse</a></code>
- <code title="post /api/document/upload">client.api.document.<a href="./src/arbi/resources/api/document/document.py">upload</a>(\*\*<a href="src/arbi/types/api/document_upload_params.py">params</a>) -> object</code>
- <code title="post /api/document/upload-url">client.api.document.<a href="./src/arbi/resources/api/document/document.py">upload_from_url</a>(\*\*<a href="src/arbi/types/api/document_upload_from_url_params.py">params</a>) -> object</code>
- <code title="get /api/document/{document_ext_id}/view">client.api.document.<a href="./src/arbi/resources/api/document/document.py">view</a>(document_ext_id, \*\*<a href="src/arbi/types/api/document_view_params.py">params</a>) -> object</code>

### Annotation

Types:

```python
from arbi.types.api.document import DocTagResponse, AnnotationDeleteResponse
```

Methods:

- <code title="post /api/document/{doc_ext_id}/annotation">client.api.document.annotation.<a href="./src/arbi/resources/api/document/annotation.py">create</a>(doc_ext_id, \*\*<a href="src/arbi/types/api/document/annotation_create_params.py">params</a>) -> <a href="./src/arbi/types/api/document/doc_tag_response.py">DocTagResponse</a></code>
- <code title="patch /api/document/{doc_ext_id}/annotation/{doctag_ext_id}">client.api.document.annotation.<a href="./src/arbi/resources/api/document/annotation.py">update</a>(doctag_ext_id, \*, doc_ext_id, \*\*<a href="src/arbi/types/api/document/annotation_update_params.py">params</a>) -> <a href="./src/arbi/types/api/document/doc_tag_response.py">DocTagResponse</a></code>
- <code title="delete /api/document/{doc_ext_id}/annotation/{doctag_ext_id}">client.api.document.annotation.<a href="./src/arbi/resources/api/document/annotation.py">delete</a>(doctag_ext_id, \*, doc_ext_id) -> <a href="./src/arbi/types/api/document/annotation_delete_response.py">AnnotationDeleteResponse</a></code>

## Conversation

Types:

```python
from arbi.types.api import (
    ConversationDeleteResponse,
    ConversationDeleteMessageResponse,
    ConversationRetrieveThreadsResponse,
    ConversationShareResponse,
    ConversationUpdateTitleResponse,
)
```

Methods:

- <code title="delete /api/conversation/{conversation_ext_id}">client.api.conversation.<a href="./src/arbi/resources/api/conversation/conversation.py">delete</a>(conversation_ext_id) -> <a href="./src/arbi/types/api/conversation_delete_response.py">ConversationDeleteResponse</a></code>
- <code title="delete /api/conversation/message/{message_ext_id}">client.api.conversation.<a href="./src/arbi/resources/api/conversation/conversation.py">delete_message</a>(message_ext_id) -> <a href="./src/arbi/types/api/conversation_delete_message_response.py">ConversationDeleteMessageResponse</a></code>
- <code title="get /api/conversation/{conversation_ext_id}/threads">client.api.conversation.<a href="./src/arbi/resources/api/conversation/conversation.py">retrieve_threads</a>(conversation_ext_id) -> <a href="./src/arbi/types/api/conversation_retrieve_threads_response.py">ConversationRetrieveThreadsResponse</a></code>
- <code title="post /api/conversation/{conversation_ext_id}/share">client.api.conversation.<a href="./src/arbi/resources/api/conversation/conversation.py">share</a>(conversation_ext_id) -> <a href="./src/arbi/types/api/conversation_share_response.py">ConversationShareResponse</a></code>
- <code title="patch /api/conversation/{conversation_ext_id}/title">client.api.conversation.<a href="./src/arbi/resources/api/conversation/conversation.py">update_title</a>(conversation_ext_id, \*\*<a href="src/arbi/types/api/conversation_update_title_params.py">params</a>) -> <a href="./src/arbi/types/api/conversation_update_title_response.py">ConversationUpdateTitleResponse</a></code>

### User

Types:

```python
from arbi.types.api.conversation import UserAddResponse, UserRemoveResponse
```

Methods:

- <code title="post /api/conversation/{conversation_ext_id}/user">client.api.conversation.user.<a href="./src/arbi/resources/api/conversation/user.py">add</a>(conversation_ext_id, \*\*<a href="src/arbi/types/api/conversation/user_add_params.py">params</a>) -> <a href="./src/arbi/types/api/conversation/user_add_response.py">UserAddResponse</a></code>
- <code title="delete /api/conversation/{conversation_ext_id}/user">client.api.conversation.user.<a href="./src/arbi/resources/api/conversation/user.py">remove</a>(conversation_ext_id, \*\*<a href="src/arbi/types/api/conversation/user_remove_params.py">params</a>) -> <a href="./src/arbi/types/api/conversation/user_remove_response.py">UserRemoveResponse</a></code>

## Assistant

Types:

```python
from arbi.types.api import MessageInput
```

Methods:

- <code title="post /api/assistant/retrieve">client.api.assistant.<a href="./src/arbi/resources/api/assistant.py">retrieve</a>(\*\*<a href="src/arbi/types/api/assistant_retrieve_params.py">params</a>) -> object</code>
- <code title="post /api/assistant/query">client.api.assistant.<a href="./src/arbi/resources/api/assistant.py">query</a>(\*\*<a href="src/arbi/types/api/assistant_query_params.py">params</a>) -> object</code>

## Health

Types:

```python
from arbi.types.api import (
    HealthCheckAppResponse,
    HealthCheckModelsResponse,
    HealthCheckServicesResponse,
    HealthGetModelsResponse,
    HealthRetrieveStatusResponse,
    HealthRetrieveVersionResponse,
)
```

Methods:

- <code title="get /api/health/app">client.api.health.<a href="./src/arbi/resources/api/health.py">check_app</a>() -> <a href="./src/arbi/types/api/health_check_app_response.py">HealthCheckAppResponse</a></code>
- <code title="get /api/health/remote-models">client.api.health.<a href="./src/arbi/resources/api/health.py">check_models</a>() -> <a href="./src/arbi/types/api/health_check_models_response.py">HealthCheckModelsResponse</a></code>
- <code title="get /api/health/services">client.api.health.<a href="./src/arbi/resources/api/health.py">check_services</a>() -> <a href="./src/arbi/types/api/health_check_services_response.py">HealthCheckServicesResponse</a></code>
- <code title="get /api/health/models">client.api.health.<a href="./src/arbi/resources/api/health.py">get_models</a>() -> <a href="./src/arbi/types/api/health_get_models_response.py">HealthGetModelsResponse</a></code>
- <code title="get /api/health/">client.api.health.<a href="./src/arbi/resources/api/health.py">retrieve_status</a>() -> <a href="./src/arbi/types/api/health_retrieve_status_response.py">HealthRetrieveStatusResponse</a></code>
- <code title="get /api/health/version">client.api.health.<a href="./src/arbi/resources/api/health.py">retrieve_version</a>() -> <a href="./src/arbi/types/api/health_retrieve_version_response.py">HealthRetrieveVersionResponse</a></code>

## Tag

Types:

```python
from arbi.types.api import (
    TagOperation,
    TagCreateResponse,
    TagUpdateResponse,
    TagDeleteResponse,
    TagApplyToDocsResponse,
    TagGetDocsResponse,
    TagRemoveFromDocsResponse,
)
```

Methods:

- <code title="post /api/tag/create">client.api.tag.<a href="./src/arbi/resources/api/tag.py">create</a>(\*\*<a href="src/arbi/types/api/tag_create_params.py">params</a>) -> <a href="./src/arbi/types/api/tag_create_response.py">TagCreateResponse</a></code>
- <code title="patch /api/tag/{tag_ext_id}">client.api.tag.<a href="./src/arbi/resources/api/tag.py">update</a>(tag_ext_id, \*\*<a href="src/arbi/types/api/tag_update_params.py">params</a>) -> <a href="./src/arbi/types/api/tag_update_response.py">TagUpdateResponse</a></code>
- <code title="delete /api/tag/{tag_ext_id}/delete">client.api.tag.<a href="./src/arbi/resources/api/tag.py">delete</a>(tag_ext_id) -> <a href="./src/arbi/types/api/tag_delete_response.py">TagDeleteResponse</a></code>
- <code title="post /api/tag/{tag_ext_id}/apply">client.api.tag.<a href="./src/arbi/resources/api/tag.py">apply_to_docs</a>(tag_ext_id, \*\*<a href="src/arbi/types/api/tag_apply_to_docs_params.py">params</a>) -> <a href="./src/arbi/types/api/tag_apply_to_docs_response.py">TagApplyToDocsResponse</a></code>
- <code title="get /api/tag/{tag_ext_id}/docs">client.api.tag.<a href="./src/arbi/resources/api/tag.py">get_docs</a>(tag_ext_id) -> <a href="./src/arbi/types/api/tag_get_docs_response.py">TagGetDocsResponse</a></code>
- <code title="delete /api/tag/{tag_ext_id}/remove">client.api.tag.<a href="./src/arbi/resources/api/tag.py">remove_from_docs</a>(tag_ext_id, \*\*<a href="src/arbi/types/api/tag_remove_from_docs_params.py">params</a>) -> <a href="./src/arbi/types/api/tag_remove_from_docs_response.py">TagRemoveFromDocsResponse</a></code>

## Configs

Types:

```python
from arbi.types.api import (
    ChunkerConfig,
    DocumentDateExtractorLlmConfig,
    EmbedderConfig,
    ModelCitationConfig,
    ParserConfig,
    QueryLlmConfig,
    RerankerConfig,
    RetrieverConfig,
    TitleLlmConfig,
    ConfigCreateResponse,
    ConfigRetrieveResponse,
    ConfigDeleteResponse,
    ConfigGetVersionsResponse,
)
```

Methods:

- <code title="post /api/configs/">client.api.configs.<a href="./src/arbi/resources/api/configs.py">create</a>(\*\*<a href="src/arbi/types/api/config_create_params.py">params</a>) -> <a href="./src/arbi/types/api/config_create_response.py">ConfigCreateResponse</a></code>
- <code title="get /api/configs/{config_ext_id}">client.api.configs.<a href="./src/arbi/resources/api/configs.py">retrieve</a>(config_ext_id) -> <a href="./src/arbi/types/api/config_retrieve_response.py">ConfigRetrieveResponse</a></code>
- <code title="delete /api/configs/{config_ext_id}">client.api.configs.<a href="./src/arbi/resources/api/configs.py">delete</a>(config_ext_id) -> <a href="./src/arbi/types/api/config_delete_response.py">ConfigDeleteResponse</a></code>
- <code title="get /api/configs/schema">client.api.configs.<a href="./src/arbi/resources/api/configs.py">get_schema</a>() -> object</code>
- <code title="get /api/configs/versions">client.api.configs.<a href="./src/arbi/resources/api/configs.py">get_versions</a>() -> <a href="./src/arbi/types/api/config_get_versions_response.py">ConfigGetVersionsResponse</a></code>

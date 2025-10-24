# Workspace

Types:

```python
from autofix_bot.types import WorkspaceRetrieveResponse
```

Methods:

- <code title="get /workspace">client.workspace.<a href="./src/autofix_bot/resources/workspace.py">retrieve</a>() -> <a href="./src/autofix_bot/types/workspace_retrieve_response.py">WorkspaceRetrieveResponse</a></code>

# Repositories

Types:

```python
from autofix_bot.types import PaginatedList, Repository, RepositoryListResponse
```

Methods:

- <code title="post /repositories">client.repositories.<a href="./src/autofix_bot/resources/repositories/repositories.py">create</a>(\*\*<a href="src/autofix_bot/types/repository_create_params.py">params</a>) -> <a href="./src/autofix_bot/types/repository.py">Repository</a></code>
- <code title="get /repositories/{id}">client.repositories.<a href="./src/autofix_bot/resources/repositories/repositories.py">retrieve</a>(id) -> <a href="./src/autofix_bot/types/repository.py">Repository</a></code>
- <code title="patch /repositories/{id}">client.repositories.<a href="./src/autofix_bot/resources/repositories/repositories.py">update</a>(id, \*\*<a href="src/autofix_bot/types/repository_update_params.py">params</a>) -> <a href="./src/autofix_bot/types/repository.py">Repository</a></code>
- <code title="get /repositories">client.repositories.<a href="./src/autofix_bot/resources/repositories/repositories.py">list</a>(\*\*<a href="src/autofix_bot/types/repository_list_params.py">params</a>) -> <a href="./src/autofix_bot/types/repository_list_response.py">RepositoryListResponse</a></code>
- <code title="delete /repositories/{id}">client.repositories.<a href="./src/autofix_bot/resources/repositories/repositories.py">delete</a>(id) -> None</code>

## Syncs

Types:

```python
from autofix_bot.types.repositories import Sync, SyncListResponse
```

Methods:

- <code title="post /repositories/{id}/syncs">client.repositories.syncs.<a href="./src/autofix_bot/resources/repositories/syncs.py">create</a>(id, \*\*<a href="src/autofix_bot/types/repositories/sync_create_params.py">params</a>) -> <a href="./src/autofix_bot/types/repositories/sync.py">Sync</a></code>
- <code title="get /repositories/{id}/syncs/{sync_id}">client.repositories.syncs.<a href="./src/autofix_bot/resources/repositories/syncs.py">retrieve</a>(sync_id, \*, id) -> <a href="./src/autofix_bot/types/repositories/sync.py">Sync</a></code>
- <code title="get /repositories/{id}/syncs">client.repositories.syncs.<a href="./src/autofix_bot/resources/repositories/syncs.py">list</a>(id, \*\*<a href="src/autofix_bot/types/repositories/sync_list_params.py">params</a>) -> <a href="./src/autofix_bot/types/repositories/sync_list_response.py">SyncListResponse</a></code>

# Analysis

Types:

```python
from autofix_bot.types import (
    Analysis,
    Fix,
    Issue,
    Language,
    AnalysisListResponse,
    AnalysisListFixesResponse,
    AnalysisListIssuesResponse,
)
```

Methods:

- <code title="post /analysis">client.analysis.<a href="./src/autofix_bot/resources/analysis.py">create</a>(\*\*<a href="src/autofix_bot/types/analysis_create_params.py">params</a>) -> <a href="./src/autofix_bot/types/analysis.py">Analysis</a></code>
- <code title="get /analysis/{id}">client.analysis.<a href="./src/autofix_bot/resources/analysis.py">retrieve</a>(id) -> <a href="./src/autofix_bot/types/analysis.py">Analysis</a></code>
- <code title="get /analysis">client.analysis.<a href="./src/autofix_bot/resources/analysis.py">list</a>(\*\*<a href="src/autofix_bot/types/analysis_list_params.py">params</a>) -> <a href="./src/autofix_bot/types/analysis_list_response.py">AnalysisListResponse</a></code>
- <code title="delete /analysis/{id}">client.analysis.<a href="./src/autofix_bot/resources/analysis.py">cancel</a>(id) -> <a href="./src/autofix_bot/types/analysis.py">Analysis</a></code>
- <code title="get /analysis/{id}/fixes">client.analysis.<a href="./src/autofix_bot/resources/analysis.py">list_fixes</a>(id, \*\*<a href="src/autofix_bot/types/analysis_list_fixes_params.py">params</a>) -> <a href="./src/autofix_bot/types/analysis_list_fixes_response.py">AnalysisListFixesResponse</a></code>
- <code title="get /analysis/{id}/issues">client.analysis.<a href="./src/autofix_bot/resources/analysis.py">list_issues</a>(id, \*\*<a href="src/autofix_bot/types/analysis_list_issues_params.py">params</a>) -> <a href="./src/autofix_bot/types/analysis_list_issues_response.py">AnalysisListIssuesResponse</a></code>

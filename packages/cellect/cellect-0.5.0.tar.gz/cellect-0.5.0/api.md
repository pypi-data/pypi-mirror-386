# Cellect

Methods:

- <code title="get /">client.<a href="./src/cellect/_client.py">health_check</a>() -> object</code>

# API

## V1

Types:

```python
from cellect.types.api import V1ListProjectsResponse
```

Methods:

- <code title="get /api/v1/projects">client.api.v1.<a href="./src/cellect/resources/api/v1/v1.py">list_projects</a>(\*\*<a href="src/cellect/types/api/v1_list_projects_params.py">params</a>) -> <a href="./src/cellect/types/api/v1_list_projects_response.py">V1ListProjectsResponse</a></code>
- <code title="post /api/v1/upload">client.api.v1.<a href="./src/cellect/resources/api/v1/v1.py">upload_file</a>(\*\*<a href="src/cellect/types/api/v1_upload_file_params.py">params</a>) -> object</code>

### Project

Types:

```python
from cellect.types.api.v1 import ProjectResponse
```

Methods:

- <code title="post /api/v1/project">client.api.v1.project.<a href="./src/cellect/resources/api/v1/project.py">create</a>(\*\*<a href="src/cellect/types/api/v1/project_create_params.py">params</a>) -> <a href="./src/cellect/types/api/v1/project_response.py">ProjectResponse</a></code>
- <code title="get /api/v1/project/{project_id}">client.api.v1.project.<a href="./src/cellect/resources/api/v1/project.py">retrieve</a>(project_id) -> <a href="./src/cellect/types/api/v1/project_response.py">ProjectResponse</a></code>
- <code title="delete /api/v1/project/{project_id}">client.api.v1.project.<a href="./src/cellect/resources/api/v1/project.py">delete</a>(project_id) -> object</code>
- <code title="post /api/v1/project/{project_id}/apply">client.api.v1.project.<a href="./src/cellect/resources/api/v1/project.py">apply_transform</a>(project_id, \*\*<a href="src/cellect/types/api/v1/project_apply_transform_params.py">params</a>) -> object</code>
- <code title="get /api/v1/project/{project_id}/download">client.api.v1.project.<a href="./src/cellect/resources/api/v1/project.py">download</a>(project_id, \*\*<a href="src/cellect/types/api/v1/project_download_params.py">params</a>) -> object</code>
- <code title="get /api/v1/project/{project_id}/status">client.api.v1.project.<a href="./src/cellect/resources/api/v1/project.py">get_status</a>(project_id, \*\*<a href="src/cellect/types/api/v1/project_get_status_params.py">params</a>) -> object</code>

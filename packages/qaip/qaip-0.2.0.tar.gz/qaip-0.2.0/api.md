# Shared Types

```python
from qaip.types import Content, FileType, SourceType
```

# Qaip

Types:

```python
from qaip.types import CompletionResponse, ExtractResponse, SearchResponse
```

Methods:

- <code title="post /completions">client.<a href="./src/qaip/_client.py">completion</a>(\*\*<a href="src/qaip/types/client_completion_params.py">params</a>) -> <a href="./src/qaip/types/completion_response.py">CompletionResponse</a></code>
- <code title="get /contents/{id}">client.<a href="./src/qaip/_client.py">content</a>(id) -> <a href="./src/qaip/types/shared/content.py">Content</a></code>
- <code title="post /extract">client.<a href="./src/qaip/_client.py">extract</a>(\*\*<a href="src/qaip/types/client_extract_params.py">params</a>) -> <a href="./src/qaip/types/extract_response.py">ExtractResponse</a></code>
- <code title="post /search">client.<a href="./src/qaip/_client.py">search</a>(\*\*<a href="src/qaip/types/client_search_params.py">params</a>) -> <a href="./src/qaip/types/search_response.py">SearchResponse</a></code>

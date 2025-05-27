# Tool Providers

Tools such as scrapers and analyzers are exposed through provider functions. Each provider is decorated with `@injectable(use_cache=False)` and lives in `di/providers.py`.

## Example Provider

```python
from fastapi import Depends
from fastapi_injectable import injectable

@injectable(use_cache=False)
def get_web_scraper():
    from local_newsifier.tools.web_scraper import WebScraperTool
    return WebScraperTool()
```

## Using Tools in Services

```python
@injectable(use_cache=False)
class NewsService:
    def __init__(self, scraper: Annotated[WebScraperTool, Depends(get_web_scraper)]):
        self.scraper = scraper
```

## Testing

Override tool providers with mocks when testing:

```python
@pytest.fixture
def patch_web_scraper(monkeypatch):
    scraper = Mock()
    monkeypatch.setattr("local_newsifier.di.providers.get_web_scraper", lambda: scraper)
    return scraper
```

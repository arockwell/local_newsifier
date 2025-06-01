# Gameplan: Fix Missing Article Fields in Apify Integration

## Objective
Fix the issue where all articles from Apify are being skipped due to missing required fields (title, content).

## Priority: HIGH
This issue prevents any data collection from Apify, making the integration useless.

## Implementation Steps

### Phase 1: Diagnose the Issue (1 hour)

1. **Add comprehensive logging**
   ```python
   def _create_articles_from_dataset(self, items: List[Dict]) -> Dict[str, Any]:
       """Process dataset items with detailed logging."""
       if not items:
           logger.warning("No items in dataset")
           return {"articles_created": 0}

       # Log first item structure for debugging
       logger.info(f"First dataset item structure: {json.dumps(items[0], indent=2)}")
       logger.info(f"Available fields: {list(items[0].keys())}")

       for idx, item in enumerate(items, 1):
           logger.info(f"Processing item {idx}/{len(items)}")
           logger.debug(f"Item data: {json.dumps(item, default=str)}")

           # Log missing fields
           missing_fields = []
           if not item.get('title'):
               missing_fields.append('title')
           if not (item.get('content') or item.get('text')):
               missing_fields.append('content/text')

           if missing_fields:
               logger.warning(f"Missing fields: {missing_fields}. Item keys: {list(item.keys())}")
   ```

2. **Create diagnostic endpoint**
   ```python
   @router.get("/webhooks/apify/diagnostic/{dataset_id}")
   def diagnose_dataset(
       dataset_id: str,
       apify_service: ApifyService = Depends(get_apify_service)
   ):
       """Diagnostic endpoint to examine dataset structure."""
       items = apify_service.get_dataset_items(dataset_id, limit=1)
       if items:
           return {
               "item_structure": items[0],
               "available_fields": list(items[0].keys()),
               "field_types": {k: type(v).__name__ for k, v in items[0].items()}
           }
       return {"error": "No items found"}
   ```

### Phase 2: Implement Flexible Field Mapping (2 hours)

1. **Create field mapping configuration**
   ```python
   class ApifyFieldMapping:
       """Configuration for mapping Apify fields to article fields."""

       # Common field name variations
       FIELD_MAPPINGS = {
           'title': ['title', 'headline', 'name', 'articleTitle', 'pageTitle'],
           'content': ['content', 'text', 'body', 'articleBody', 'description', 'fullText'],
           'url': ['url', 'link', 'href', 'canonicalUrl'],
           'published_at': ['publishedAt', 'datePublished', 'pubDate', 'date', 'created'],
           'author': ['author', 'byline', 'creator', 'authorName']
       }

       @classmethod
       def extract_field(cls, item: Dict, field_name: str) -> Optional[str]:
           """Extract field value trying multiple possible names."""
           # Direct match first
           if value := item.get(field_name):
               return str(value)

           # Try mapped variations
           for variant in cls.FIELD_MAPPINGS.get(field_name, []):
               if value := item.get(variant):
                   return str(value)

           # Try nested paths (e.g., 'meta.title')
           for variant in cls.FIELD_MAPPINGS.get(field_name, []):
               if '.' in variant:
                   value = cls._extract_nested(item, variant)
                   if value:
                       return str(value)

           return None

       @staticmethod
       def _extract_nested(item: Dict, path: str) -> Optional[Any]:
           """Extract value from nested path like 'meta.title'."""
           keys = path.split('.')
           value = item
           for key in keys:
               if isinstance(value, dict):
                   value = value.get(key)
                   if value is None:
                       return None
               else:
                   return None
           return value
   ```

2. **Update article creation logic**
   ```python
   def _create_article_from_item(self, item: Dict) -> Optional[Article]:
       """Create article from dataset item with flexible mapping."""
       # Extract fields with fallbacks
       title = ApifyFieldMapping.extract_field(item, 'title')
       content = ApifyFieldMapping.extract_field(item, 'content')
       url = ApifyFieldMapping.extract_field(item, 'url')

       # Validate required fields
       if not all([title, content, url]):
           missing = []
           if not title: missing.append('title')
           if not content: missing.append('content')
           if not url: missing.append('url')
           logger.warning(f"Missing required fields: {missing} for URL: {url or 'unknown'}")
           return None

       # Extract optional fields
       published_at = ApifyFieldMapping.extract_field(item, 'published_at')
       if published_at:
           published_at = self._parse_date(published_at)

       # Create article
       return Article(
           title=title,
           content=content,
           url=url,
           source_url=url,
           published_at=published_at or datetime.utcnow()
       )
   ```

### Phase 3: Handle Different Actor Types (2 hours)

1. **Detect actor output type**
   ```python
   def _detect_actor_type(self, items: List[Dict]) -> str:
       """Detect the type of actor based on output structure."""
       if not items:
           return 'unknown'

       first_item = items[0]

       # Web scraper actor (generic pages)
       if 'pageFunctionResult' in first_item:
           return 'page_function'

       # Article scraper actor
       if all(field in first_item for field in ['title', 'text', 'url']):
           return 'article_scraper'

       # Legacy scraper
       if 'pageTitle' in first_item and 'pageContent' in first_item:
           return 'legacy_scraper'

       # URL list (needs secondary processing)
       if 'url' in first_item and len(first_item) <= 3:
           return 'url_list'

       return 'unknown'
   ```

2. **Add actor-specific processors**
   ```python
   def _process_by_actor_type(self, items: List[Dict], actor_type: str) -> List[Article]:
       """Process items based on detected actor type."""
       processors = {
           'page_function': self._process_page_function_results,
           'article_scraper': self._process_article_scraper_results,
           'legacy_scraper': self._process_legacy_scraper_results,
           'url_list': self._process_url_list
       }

       processor = processors.get(actor_type, self._process_generic)
       return processor(items)
   ```

### Phase 4: Add Configuration Management (2 hours)

1. **Create actor configuration model**
   ```python
   class ApifyActorConfig(SQLModel, table=True):
       """Configuration for Apify actor field mappings."""
       __tablename__ = "apify_actor_configs"

       id: Optional[int] = Field(default=None, primary_key=True)
       actor_id: str = Field(unique=True)
       actor_name: str
       field_mappings: Dict = Field(sa_column=Column(JSON))
       processor_type: str
       active: bool = True
       created_at: datetime = Field(default_factory=datetime.utcnow)
   ```

2. **Add configuration UI/CLI**
   ```python
   @router.post("/webhooks/apify/configure/{actor_id}")
   def configure_actor_mapping(
       actor_id: str,
       test_dataset_id: str,
       session: Session = Depends(get_session)
   ):
       """Auto-detect and configure field mappings for an actor."""
       # Fetch sample data
       # Analyze structure
       # Suggest mappings
       # Save configuration
   ```

### Phase 5: Testing and Validation (2 hours)

1. **Create test fixtures**
   ```python
   # Different actor output formats
   ACTOR_OUTPUT_SAMPLES = {
       'article_scraper': {
           'title': 'Test Article',
           'text': 'Article content...',
           'url': 'https://example.com/article'
       },
       'page_function': {
           'pageFunctionResult': {
               'headline': 'Test Article',
               'body': 'Article content...'
           },
           'url': 'https://example.com/article'
       },
       'legacy': {
           'pageTitle': 'Test Article',
           'pageContent': 'Article content...',
           'pageUrl': 'https://example.com/article'
       }
   }
   ```

2. **Test field extraction**
   ```python
   def test_field_mapping():
       for actor_type, sample in ACTOR_OUTPUT_SAMPLES.items():
           article = create_article_from_item(sample)
           assert article is not None
           assert article.title == 'Test Article'
           assert article.content == 'Article content...'
   ```

### Phase 6: Add Monitoring and Alerts (1 hour)

1. **Track extraction success rate**
   ```python
   def log_extraction_metrics(self, dataset_id: str, stats: Dict):
       """Log metrics for monitoring."""
       logger.info(f"Dataset {dataset_id} extraction stats: {stats}")

       # Alert if success rate is too low
       success_rate = stats['created'] / stats['total'] if stats['total'] > 0 else 0
       if success_rate < 0.5:
           logger.error(f"Low extraction success rate: {success_rate:.2%}")
   ```

2. **Add webhook metadata**
   ```python
   class WebhookProcessingResult(SQLModel, table=True):
       """Track webhook processing results."""
       __tablename__ = "webhook_processing_results"

       id: Optional[int] = Field(default=None, primary_key=True)
       run_id: str
       dataset_id: str
       total_items: int
       successful_extractions: int
       failed_extractions: int
       skip_reasons: Dict = Field(sa_column=Column(JSON))
       processed_at: datetime = Field(default_factory=datetime.utcnow)
   ```

## Deployment Strategy

1. **Phase 1**: Deploy logging changes to understand data structure
2. **Phase 2**: Deploy field mapping based on findings
3. **Phase 3**: Test with real webhooks
4. **Phase 4**: Deploy configuration management
5. **Phase 5**: Monitor and tune

## Success Criteria

1. Articles successfully extracted from Apify datasets
2. >80% extraction success rate
3. Clear logging of why articles are skipped
4. Configuration UI for new actors
5. Monitoring of extraction metrics

## Rollback Plan

1. Keep existing code path as fallback
2. Feature flag for new extraction logic
3. Ability to reprocess failed datasets
4. Manual override for field mappings

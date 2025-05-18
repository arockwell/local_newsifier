"""Service for processing incoming webhooks from external systems."""

import logging
import traceback
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from sqlalchemy.orm import Session
from sqlmodel import select

from local_newsifier.config.settings import settings
from local_newsifier.errors import handle_apify
from local_newsifier.models.apify import ApifyJob, ApifyDatasetItem
from local_newsifier.models.article import Article
from local_newsifier.models.webhook import (
    ApifyWebhookPayload, 
    ApifyDatasetTransformationConfig
)
from local_newsifier.services.apify_service import ApifyService
from local_newsifier.services.article_service import ArticleService


class WebhookService:
    """Base class for webhook processing services."""
    
    def __init__(self, session_factory: Callable[[], Session]):
        """Initialize the webhook service.
        
        Args:
            session_factory: Callable that returns a database session
        """
        self.session_factory = session_factory
        self.logger = logging.getLogger(__name__)


class ApifyWebhookHandler(WebhookService):
    """Service for handling Apify webhook notifications and processing datasets."""
    
    def __init__(
        self, 
        apify_service: ApifyService,
        article_service: ArticleService,
        session_factory: Callable[[], Session],
        transformation_config: Optional[ApifyDatasetTransformationConfig] = None,
    ):
        """Initialize the Apify webhook handler.
        
        Args:
            apify_service: Service for interacting with the Apify API
            article_service: Service for article operations
            session_factory: Callable that returns a database session
            transformation_config: Optional configuration for dataset transformation
        """
        super().__init__(session_factory)
        self.apify_service = apify_service
        self.article_service = article_service
        self.config = transformation_config or ApifyDatasetTransformationConfig()
    
    def validate_webhook(self, payload: ApifyWebhookPayload) -> bool:
        """Validate that the webhook payload is authentic.
        
        Args:
            payload: The webhook payload to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Skip validation in test mode
        if self.apify_service._test_mode:
            return True
            
        # If no secret is set, allow all (not recommended for production)
        if not settings.APIFY_WEBHOOK_SECRET:
            self.logger.warning("No APIFY_WEBHOOK_SECRET set, skipping validation")
            return True
            
        # Validate secret
        return payload.secret == settings.APIFY_WEBHOOK_SECRET
    
    def _handle_failed_run(self, payload: ApifyWebhookPayload) -> Tuple[bool, Optional[int], str]:
        """Handle a failed Apify run.
        
        Args:
            payload: The webhook payload
            
        Returns:
            Tuple[bool, Optional[int], str]: (success, job_id, message)
        """
        with self.session_factory() as session:
            # Check if we already have a job record for this run
            job_query = select(ApifyJob).where(ApifyJob.run_id == payload.actorRunId)
            existing_job = session.exec(job_query).first()
            
            if existing_job:
                # Update existing job
                existing_job.status = payload.status
                existing_job.error_message = payload.statusMessage or f"Run failed with status: {payload.status}"
                existing_job.finished_at = payload.finishedAt or datetime.now(timezone.utc)
                
                if payload.startedAt and existing_job.started_at:
                    # Calculate duration if we have both timestamps
                    duration = (payload.finishedAt or datetime.now(timezone.utc)) - payload.startedAt
                    existing_job.duration_seconds = int(duration.total_seconds())
                
                session.add(existing_job)
                session.commit()
                return True, existing_job.id, f"Updated failed job record for run {payload.actorRunId}"
            else:
                # Create new job record
                new_job = ApifyJob(
                    run_id=payload.actorRunId,
                    actor_id=payload.actorId,
                    status=payload.status,
                    started_at=payload.startedAt,
                    finished_at=payload.finishedAt or datetime.now(timezone.utc),
                    dataset_id=payload.defaultDatasetId,
                    error_message=payload.statusMessage or f"Run failed with status: {payload.status}",
                )
                
                # Calculate duration if possible
                if payload.startedAt and payload.finishedAt:
                    duration = payload.finishedAt - payload.startedAt
                    new_job.duration_seconds = int(duration.total_seconds())
                
                session.add(new_job)
                session.commit()
                return True, new_job.id, f"Created job record for failed run {payload.actorRunId}"
    
    @handle_apify
    def handle_webhook(self, payload: ApifyWebhookPayload) -> Tuple[bool, Optional[int], str]:
        """Process an Apify webhook notification.
        
        Args:
            payload: The webhook payload
            
        Returns:
            Tuple[bool, Optional[int], str]: (success, job_id, message)
        """
        # Check event type
        if payload.eventType != "ACTOR.RUN.SUCCEEDED":
            if "FAILED" in payload.eventType or "ABORTED" in payload.eventType:
                return self._handle_failed_run(payload)
            return False, None, f"Unsupported event type: {payload.eventType}"
        
        # Create or update ApifyJob record
        with self.session_factory() as session:
            # Check if we already have a job record for this run
            job_query = select(ApifyJob).where(ApifyJob.run_id == payload.actorRunId)
            existing_job = session.exec(job_query).first()
            
            if existing_job:
                # Update existing job
                existing_job.status = payload.status
                existing_job.finished_at = payload.finishedAt or datetime.now(timezone.utc)
                existing_job.dataset_id = payload.defaultDatasetId
                
                if payload.startedAt and payload.finishedAt:
                    # Calculate duration if we have both timestamps
                    duration = payload.finishedAt - payload.startedAt
                    existing_job.duration_seconds = int(duration.total_seconds())
                
                session.add(existing_job)
                session.commit()
                job_id = existing_job.id
            else:
                # Create new job record
                new_job = ApifyJob(
                    run_id=payload.actorRunId,
                    actor_id=payload.actorId,
                    status=payload.status,
                    started_at=payload.startedAt,
                    finished_at=payload.finishedAt or datetime.now(timezone.utc),
                    dataset_id=payload.defaultDatasetId,
                )
                
                # Calculate duration if possible
                if payload.startedAt and payload.finishedAt:
                    duration = payload.finishedAt - payload.startedAt
                    new_job.duration_seconds = int(duration.total_seconds())
                
                session.add(new_job)
                session.commit()
                session.refresh(new_job)
                job_id = new_job.id
        
        # Return without fetching dataset if this is just a notification
        return True, job_id, f"Successfully recorded job for run {payload.actorRunId} with dataset {payload.defaultDatasetId}"
        
    def _extract_field(self, data: Dict[str, Any], field_names: List[str]) -> Optional[Any]:
        """Extract a field from data using a list of possible field names.
        
        Args:
            data: The data to extract from
            field_names: List of possible field names to try
            
        Returns:
            Optional[Any]: The field value if found, None otherwise
        """
        for field in field_names:
            if field in data and data[field] is not None:
                return data[field]
        return None
    
    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL as a fallback source.
        
        Args:
            url: The URL to extract domain from
            
        Returns:
            Optional[str]: The domain if extraction successful, None otherwise
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            # Remove www. prefix if present
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return None
    
    def _safe_text(self, text: Any) -> str:
        """Safely convert any value to text.
        
        Args:
            text: The value to convert
            
        Returns:
            str: String representation of the value
        """
        if text is None:
            return ""
        return str(text)
            
    def _parse_date(self, date_str: Any) -> Optional[datetime]:
        """Try to parse a date string into a datetime object.
        
        Args:
            date_str: The date string to parse
            
        Returns:
            Optional[datetime]: Parsed datetime or None if parsing failed
        """
        if not date_str:
            return None
            
        if isinstance(date_str, datetime):
            return date_str
            
        # Convert to string if not already
        date_str = str(date_str)
        
        # Try various date formats
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO format with milliseconds
            "%Y-%m-%dT%H:%M:%SZ",      # ISO format without milliseconds
            "%Y-%m-%dT%H:%M:%S",       # ISO format without Z
            "%Y-%m-%d %H:%M:%S",       # SQL-like format
            "%Y-%m-%d",                # Just date
            "%m/%d/%Y %H:%M:%S",       # US format with time
            "%m/%d/%Y",                # US format date only
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                # Assume UTC if no timezone info
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
                
        # If all parsing attempts failed
        self.logger.warning(f"Could not parse date string: {date_str}")
        return None
    
    def transform_dataset_item(
        self, 
        item_data: Dict[str, Any]
    ) -> Tuple[bool, Optional[Article], Optional[str]]:
        """Transform an Apify dataset item into an article.
        
        Args:
            item_data: Raw data from Apify dataset
            
        Returns:
            Tuple[bool, Optional[Article], Optional[str]]: 
                (success, article if created, error message if failed)
        """
        try:
            # Extract required fields
            url = self._extract_field(item_data, [self.config.url_field])
            if not url:
                return False, None, "URL field missing or empty"
                
            title = self._extract_field(item_data, [self.config.title_field])
            if not title:
                return False, None, "Title field missing or empty"
                
            content = self._extract_field(item_data, self.config.content_field)
            if not content:
                if self.config.skip_empty_content:
                    return False, None, "Content field missing or empty, skipping"
                content = ""  # Use empty string as fallback
            
            # Skip if content is too short
            if len(self._safe_text(content)) < self.config.min_content_length:
                return False, None, f"Content too short ({len(self._safe_text(content))} chars)"
                
            # Extract optional fields with fallbacks
            source = self._extract_field(item_data, [self.config.source_field])
            if not source and self.config.extract_domain_as_source:
                source = self._extract_domain(url)
                
            published_at = self._extract_field(item_data, self.config.published_at_field)
            published_at = self._parse_date(published_at)
            
            # Create article model
            article = Article(
                url=url,
                title=self._safe_text(title),
                content=self._safe_text(content),
                source=self._safe_text(source) if source else None,
                published_at=published_at,
                # Always set created_at to current time
                created_at=datetime.now(timezone.utc),
            )
            
            return True, article, None
        except Exception as e:
            error_msg = f"Error transforming dataset item: {str(e)}\n{traceback.format_exc()}"
            self.logger.error(error_msg)
            return False, None, error_msg
    
    def process_dataset(self, dataset_id: str, job_id: int) -> Tuple[bool, int, int, Optional[str]]:
        """Process an Apify dataset and create articles from its items.
        
        Args:
            dataset_id: The Apify dataset ID to process
            job_id: The ApifyJob ID to update
            
        Returns:
            Tuple[bool, int, int, Optional[str]]: 
                (success, items_processed, articles_created, error_message)
        """
        try:
            # Fetch dataset items from Apify
            dataset_result = self.apify_service.get_dataset_items(dataset_id)
            
            if "error" in dataset_result:
                return False, 0, 0, f"Error fetching dataset: {dataset_result['error']}"
                
            items = dataset_result.get("items", [])
            if not items:
                return False, 0, 0, "No items found in dataset"
                
            # Track statistics
            items_processed = 0
            articles_created = 0
            errors = []
            
            # Process items and create articles
            for item in items:
                items_processed += 1
                
                # Store raw data first
                with self.session_factory() as session:
                    dataset_item = ApifyDatasetItem(
                        job_id=job_id,
                        apify_id=item.get("id", str(items_processed)),
                        raw_data=item,
                    )
                    session.add(dataset_item)
                    session.commit()
                    session.refresh(dataset_item)
                    dataset_item_id = dataset_item.id
                
                # Transform to article
                success, article, error = self.transform_dataset_item(item)
                
                if not success or not article:
                    # Update dataset item with error
                    with self.session_factory() as session:
                        dataset_item = session.get(ApifyDatasetItem, dataset_item_id)
                        if dataset_item:
                            dataset_item.error_message = error
                            session.add(dataset_item)
                            session.commit()
                    errors.append(error)
                    continue
                
                # Check if article already exists
                with self.session_factory() as session:
                    existing_article = self.article_service.get_by_url(article.url, session)
                    
                    if existing_article and not self.config.force_update_existing:
                        # Link dataset item to existing article without updating
                        dataset_item = session.get(ApifyDatasetItem, dataset_item_id)
                        if dataset_item:
                            dataset_item.transformed = True
                            dataset_item.article_id = existing_article.id
                            session.add(dataset_item)
                            session.commit()
                        continue
                    
                    # Create new article or update existing one
                    if existing_article and self.config.force_update_existing:
                        # Update fields on existing article
                        existing_article.title = article.title
                        existing_article.content = article.content
                        existing_article.source = article.source
                        if article.published_at:
                            existing_article.published_at = article.published_at
                        session.add(existing_article)
                        session.commit()
                        created_article_id = existing_article.id
                    else:
                        # Create new article
                        session.add(article)
                        session.commit()
                        session.refresh(article)
                        created_article_id = article.id
                        articles_created += 1
                    
                    # Update dataset item with article reference
                    dataset_item = session.get(ApifyDatasetItem, dataset_item_id)
                    if dataset_item:
                        dataset_item.transformed = True
                        dataset_item.article_id = created_article_id
                        session.add(dataset_item)
                        session.commit()
                    
                    # Process the article through the entity extraction pipeline
                    # This is done asynchronously to avoid blocking the webhook response
                    try:
                        self.article_service.process_article(created_article_id)
                    except Exception as e:
                        self.logger.error(f"Error processing article {created_article_id}: {str(e)}")
            
            # Update job with processing results
            with self.session_factory() as session:
                job = session.get(ApifyJob, job_id)
                if job:
                    job.processed = True
                    job.articles_created = articles_created
                    job.processed_at = datetime.now(timezone.utc)
                    job.item_count = items_processed
                    session.add(job)
                    session.commit()
            
            return True, items_processed, articles_created, None
        except Exception as e:
            error_msg = f"Error processing dataset: {str(e)}\n{traceback.format_exc()}"
            self.logger.error(error_msg)
            return False, 0, 0, error_msg
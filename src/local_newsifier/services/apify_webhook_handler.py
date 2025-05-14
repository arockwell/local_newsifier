"""Service for handling Apify webhook notifications and processing datasets."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from sqlmodel import Session

from local_newsifier.models.apify import ApifyJob, ApifyDatasetItem
from local_newsifier.models.article import Article
from local_newsifier.services.apify_service import ApifyService
from local_newsifier.services.article_service import ArticleService

logger = logging.getLogger(__name__)


class ApifyWebhookHandler:
    """Handler for Apify webhook notifications and dataset processing."""

    def __init__(
        self,
        apify_service: ApifyService,
        article_service: ArticleService,
        session_factory: callable
    ):
        """Initialize the Apify webhook handler.
        
        Args:
            apify_service: Service for Apify API operations
            article_service: Service for article operations
            session_factory: Factory function to create database sessions
        """
        self.apify_service = apify_service
        self.article_service = article_service
        self.session_factory = session_factory
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process an Apify webhook notification.
        
        Args:
            webhook_data: Webhook payload from Apify
            
        Returns:
            Dict containing processing results
        """
        event_type = webhook_data.get("eventType")
        dataset_id = webhook_data.get("datasetId") or webhook_data.get("defaultDatasetId")
        actor_id = webhook_data.get("actorId")
        actor_run_id = webhook_data.get("actorRunId")
        
        if event_type != "RUN.SUCCEEDED" or not dataset_id:
            return {
                "status": "skipped",
                "reason": f"Event type {event_type} or missing dataset ID"
            }
        
        logger.info(f"Processing Apify webhook for actor {actor_id}, run {actor_run_id}")
        
        # Process the dataset and create articles
        try:
            job_id = await self._create_or_update_job(actor_id, actor_run_id, dataset_id)
            processed_items = await self._process_dataset_items(dataset_id, job_id)
            
            return {
                "status": "success",
                "job_id": job_id,
                "dataset_id": dataset_id,
                "processed_count": len(processed_items),
                "articles_created": sum(1 for item in processed_items if item[1])
            }
        
        except Exception as e:
            logger.exception(f"Error processing webhook: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _create_or_update_job(
        self,
        actor_id: str,
        run_id: str,
        dataset_id: str
    ) -> int:
        """Create or update an ApifyJob record.
        
        Args:
            actor_id: ID of the Apify actor
            run_id: ID of the actor run
            dataset_id: ID of the dataset with results
            
        Returns:
            ID of the created or updated job
        """
        with self.session_factory() as session:
            # Check if job already exists
            from sqlmodel import select
            statement = select(ApifyJob).where(ApifyJob.run_id == run_id)
            existing_job = session.exec(statement).first()
            
            if existing_job:
                # Update existing job
                existing_job.status = "SUCCEEDED"
                existing_job.dataset_id = dataset_id
                existing_job.finished_at = datetime.now(timezone.utc)
                session.add(existing_job)
                session.commit()
                session.refresh(existing_job)
                return existing_job.id
            
            # Create new job
            job = ApifyJob(
                run_id=run_id,
                actor_id=actor_id,
                status="SUCCEEDED",
                dataset_id=dataset_id,
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc)
            )
            session.add(job)
            session.commit()
            session.refresh(job)
            return job.id
    
    async def _process_dataset_items(self, dataset_id: str, job_id: int) -> List[Tuple[int, Optional[int]]]:
        """Process items from the dataset and create articles.
        
        Args:
            dataset_id: ID of the Apify dataset
            job_id: ID of the ApifyJob record
            
        Returns:
            List of tuples (dataset_item_id, article_id) where article_id is None if transformation failed
        """
        processed_items = []
        
        # Get dataset items from Apify
        dataset_response = self.apify_service.get_dataset_items(dataset_id)
        items = dataset_response.get("items", [])
        
        logger.info(f"Processing {len(items)} items from dataset {dataset_id}")
        
        for item in items:
            try:
                with self.session_factory() as session:
                    # Create dataset item record
                    dataset_item = ApifyDatasetItem(
                        job_id=job_id,
                        apify_id=item.get("id", str(hash(str(item)))),
                        raw_data=item,
                        transformed=False
                    )
                    session.add(dataset_item)
                    session.commit()
                    session.refresh(dataset_item)
                    
                    # Transform to article
                    article_id = await self._transform_to_article(item, dataset_item.id, session)
                    
                    # Update dataset item with result
                    dataset_item.transformed = article_id is not None
                    dataset_item.article_id = article_id
                    if not article_id:
                        dataset_item.error_message = "Failed to transform to article"
                    
                    session.add(dataset_item)
                    session.commit()
                    
                    processed_items.append((dataset_item.id, article_id))
            
            except Exception as e:
                logger.exception(f"Error processing dataset item: {str(e)}")
                processed_items.append((0, None))
        
        # Update job with processing results
        await self._update_job_processing_status(job_id, processed_items)
        
        return processed_items
    
    async def _transform_to_article(
        self,
        item: Dict[str, Any],
        dataset_item_id: int,
        session: Session
    ) -> Optional[int]:
        """Transform a dataset item to an article.
        
        Args:
            item: Raw dataset item from Apify
            dataset_item_id: ID of the ApifyDatasetItem record
            session: Database session
            
        Returns:
            Article ID if transformation successful, None otherwise
        """
        try:
            # Extract required fields based on actor output format
            url = item.get("url")
            if not url:
                return None
            
            title = item.get("title")
            if not title:
                title = item.get("pageTitle", "Untitled Article")
            
            # Extract content - try different possible field names
            content = item.get("content")
            if not content:
                content = item.get("text")
            if not content:
                content = item.get("articleBody")
            if not content:
                content = item.get("description", "No content available")
            
            # Extract published date - try different possible formats
            published_at = None
            pub_date_str = item.get("publishedAt") or item.get("datePublished")
            if pub_date_str:
                try:
                    # Try different date formats
                    from dateutil import parser
                    published_at = parser.parse(pub_date_str)
                    if not published_at.tzinfo:
                        # If no timezone info, assume UTC
                        published_at = published_at.replace(tzinfo=timezone.utc)
                except Exception:
                    logger.warning(f"Failed to parse date: {pub_date_str}")
                    published_at = datetime.now(timezone.utc)
            else:
                published_at = datetime.now(timezone.utc)
            
            # Extract source from URL domain if not provided
            source = item.get("source")
            if not source:
                try:
                    domain = urlparse(url).netloc
                    source = domain.replace("www.", "")
                except Exception:
                    source = "unknown"
            
            # Create article
            article = Article(
                title=title,
                content=content,
                url=url,
                source=source,
                published_at=published_at,
                apify_dataset_item_id=dataset_item_id
            )
            
            session.add(article)
            session.commit()
            session.refresh(article)
            
            # Process article for entities, analysis, etc.
            self.article_service.process_article(article.id)
            
            return article.id
        
        except Exception as e:
            logger.exception(f"Error transforming dataset item {dataset_item_id}: {str(e)}")
            return None
    
    async def _update_job_processing_status(
        self,
        job_id: int,
        processed_items: List[Tuple[int, Optional[int]]]
    ) -> None:
        """Update the job record with processing results.
        
        Args:
            job_id: ID of the ApifyJob record
            processed_items: List of (dataset_item_id, article_id) tuples
        """
        with self.session_factory() as session:
            # Get job record
            from sqlmodel import select
            statement = select(ApifyJob).where(ApifyJob.id == job_id)
            job = session.exec(statement).first()
            
            if not job:
                logger.error(f"Job {job_id} not found for updating processing status")
                return
            
            # Update job status
            job.processed = True
            job.processed_at = datetime.now(timezone.utc)
            job.item_count = len(processed_items)
            job.articles_created = sum(1 for item in processed_items if item[1])
            
            session.add(job)
            session.commit()
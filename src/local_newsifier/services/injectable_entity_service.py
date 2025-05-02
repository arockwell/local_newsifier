"""Entity service using fastapi-injectable for dependency injection."""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Dict, List, Optional, Generator, TypeVar

from fastapi import Depends
from fastapi_injectable import injectable
from sqlmodel import Session

from local_newsifier.models.entity import Entity
from local_newsifier.models.entity_tracking import CanonicalEntity, EntityMentionContext, EntityProfile
from local_newsifier.models.state import (
    EntityTrackingState, 
    EntityBatchTrackingState, 
    EntityDashboardState, 
    EntityRelationshipState, 
    TrackingStatus
)
from local_newsifier.crud.entity import EntityCRUD
from local_newsifier.crud.canonical_entity import CanonicalEntityCRUD
from local_newsifier.crud.entity_mention_context import EntityMentionContextCRUD
from local_newsifier.crud.entity_profile import EntityProfileCRUD
from local_newsifier.crud.article import ArticleCRUD
from local_newsifier.tools.extraction.entity_extractor import EntityExtractor
from local_newsifier.tools.analysis.context_analyzer import ContextAnalyzer
from local_newsifier.tools.resolution.entity_resolver import EntityResolver
from local_newsifier.di.providers import (
    get_entity_crud,
    get_canonical_entity_crud,
    get_entity_mention_context_crud,
    get_entity_profile_crud,
    get_article_crud,
    get_entity_extractor,
    get_context_analyzer,
    get_entity_resolver,
    get_session,
)


@injectable
class InjectableEntityService:
    """Entity service for coordinating entity-related operations using fastapi-injectable."""
    
    def __init__(
        self,
        entity_crud: Annotated[EntityCRUD, Depends(get_entity_crud)],
        canonical_entity_crud: Annotated[CanonicalEntityCRUD, Depends(get_canonical_entity_crud)],
        entity_mention_context_crud: Annotated[EntityMentionContextCRUD, Depends(get_entity_mention_context_crud)],
        entity_profile_crud: Annotated[EntityProfileCRUD, Depends(get_entity_profile_crud)],
        article_crud: Annotated[ArticleCRUD, Depends(get_article_crud)],
        entity_extractor: Annotated[EntityExtractor, Depends(get_entity_extractor)],
        context_analyzer: Annotated[ContextAnalyzer, Depends(get_context_analyzer)],
        entity_resolver: Annotated[EntityResolver, Depends(get_entity_resolver)],
        session: Annotated[Session, Depends(get_session)],
    ):
        """Initialize with injected dependencies.
        
        Args:
            entity_crud: CRUD for entities
            canonical_entity_crud: CRUD for canonical entities
            entity_mention_context_crud: CRUD for entity mention contexts
            entity_profile_crud: CRUD for entity profiles
            article_crud: CRUD for articles
            entity_extractor: Tool for extracting entities from text
            context_analyzer: Tool for analyzing entity contexts
            entity_resolver: Tool for resolving entities to canonical forms
            session: Injected database session
        """
        self.entity_crud = entity_crud
        self.canonical_entity_crud = canonical_entity_crud
        self.entity_mention_context_crud = entity_mention_context_crud
        self.entity_profile_crud = entity_profile_crud
        self.article_crud = article_crud
        self.entity_extractor = entity_extractor
        self.context_analyzer = context_analyzer
        self.entity_resolver = entity_resolver
        self.session = session
    
    def process_article_entities(
        self, 
        article_id: int,
        content: str,
        title: str,
        published_at: datetime
    ) -> List[Dict[str, object]]:
        """Process an article to extract and track entities.
        
        Args:
            article_id: ID of the article
            content: Article content
            title: Article title
            published_at: Article publication date
            
        Returns:
            List of processed entities with metadata
        """
        # Extract entities using EntityExtractor
        entities = self.entity_extractor.extract_entities(content)
        
        processed_entities = []
        
        # Using the injected session directly instead of a session factory
        session = self.session
        
        # Get existing canonical entities for resolution
        existing_entities = [
            {
                "name": entity.name,
                "entity_type": entity.entity_type,
                "id": entity.id
            }
            for entity in self.canonical_entity_crud.get_all(session)
        ]
        
        for entity in entities:
            # Analyze context using ContextAnalyzer
            context_analysis = self.context_analyzer.analyze_context(entity["context"])
            
            # Resolve entity using EntityResolver
            resolved_entity = self.entity_resolver.resolve_entity(
                entity["text"], 
                entity["type"],
                existing_entities
            )
            
            # Handle canonical entity creation or retrieval
            if resolved_entity["is_new"]:
                canonical_entity_data = CanonicalEntity(
                    name=resolved_entity["name"],
                    entity_type=resolved_entity["entity_type"],
                    entity_metadata={}
                )
                canonical_entity = self.canonical_entity_crud.create(
                    session, 
                    obj_in=canonical_entity_data
                )
            else:
                canonical_entity = self.canonical_entity_crud.get_by_name(
                    session,
                    name=resolved_entity["name"], 
                    entity_type=resolved_entity["entity_type"]
                )
            
            # Store entity in database
            entity_data = Entity(
                article_id=article_id,
                text=entity["text"],
                entity_type=entity["type"],
                confidence=entity.get("confidence", 1.0)
            )
            db_entity = self.entity_crud.create(session, obj_in=entity_data)
            
            # Store entity mention context
            context_data = EntityMentionContext(
                entity_id=db_entity.id,
                article_id=article_id,
                context_text=entity["context"],
                context_type="sentence",
                sentiment_score=context_analysis["sentiment"]["score"]
            )
            self.entity_mention_context_crud.create(session, obj_in=context_data)
            
            # Add to results
            processed_entities.append({
                "original_text": entity["text"],
                "canonical_name": canonical_entity.name,
                "canonical_id": canonical_entity.id,
                "context": entity["context"],
                "sentiment_score": context_analysis["sentiment"]["score"],
                "framing_category": context_analysis["framing"]["category"]
            })
        
        return processed_entities
    
    @injectable
    def process_article_with_state(self, state: EntityTrackingState) -> EntityTrackingState:
        """Process an article using state-based approach.
        
        Args:
            state: EntityTrackingState containing article info
            
        Returns:
            Updated state with processed entities
        """
        try:
            # Update state status
            state.status = TrackingStatus.PROCESSING
            state.add_log("Processing article for entity tracking")
            
            # Process article entities
            processed_entities = self.process_article_entities(
                article_id=state.article_id,
                content=state.content,
                title=state.title,
                published_at=state.published_at
            )
            
            # Update state with results
            state.entities = processed_entities
            state.status = TrackingStatus.SUCCESS
            state.add_log(f"Successfully processed {len(processed_entities)} entities")
            
            # Update article status using the injected session
            self.article_crud.update_status(
                self.session, 
                article_id=state.article_id, 
                status="entity_tracked"
            )
            
        except Exception as e:
            state.set_error("entity_tracking", e)
            state.add_log(f"Error processing entities: {str(e)}")
            
        return state
    
    @injectable
    def process_articles_batch(self, state: EntityBatchTrackingState) -> EntityBatchTrackingState:
        """Process multiple articles for entity tracking.
        
        Args:
            state: EntityBatchTrackingState object
            
        Returns:
            Updated state with processed article results
        """
        try:
            # Update state status
            state.status = TrackingStatus.PROCESSING
            state.add_log(f"Starting batch processing with status filter: {state.status_filter}")
            
            # Using the injected session
            session = self.session
            
            # Get articles with the specified status
            articles = self.article_crud.get_by_status(session, status=state.status_filter)
            state.total_articles = len(articles)
            state.add_log(f"Found {state.total_articles} articles to process")
            
            # Process each article
            for article in articles:
                try:
                    # Create tracking state for this article
                    article_state = EntityTrackingState(
                        article_id=article.id,
                        content=article.content,
                        title=article.title,
                        published_at=article.published_at or datetime.now(timezone.utc)
                    )
                    
                    # Process article
                    processed_state = self.process_article_with_state(article_state)
                    
                    # Update batch state with this article's result
                    article_result = {
                        "article_id": article.id,
                        "title": article.title,
                        "url": article.url,
                        "entity_count": len(processed_state.entities),
                        "entities": processed_state.entities,
                        "status": processed_state.status.value
                    }
                    
                    state.add_processed_article(
                        article_result, 
                        success=(processed_state.status == TrackingStatus.SUCCESS)
                    )
                    
                    # Update article status
                    if processed_state.status == TrackingStatus.SUCCESS:
                        self.article_crud.update_status(
                            session, 
                            article_id=article.id, 
                            status="entity_tracked"
                        )
                    
                except Exception as e:
                    # Handle individual article failures without stopping the batch
                    error_msg = f"Error processing article {article.id}: {str(e)}"
                    state.add_log(error_msg)
                    state.error_count += 1
            
            # Update final state
            if state.error_count == 0:
                state.status = TrackingStatus.SUCCESS
                state.add_log("Batch processing completed successfully")
            elif state.error_count < state.total_articles:
                state.status = TrackingStatus.SUCCESS
                state.add_log(f"Batch processing completed with {state.error_count} errors")
            else:
                state.status = TrackingStatus.FAILED
                state.add_log("Batch processing failed for all articles")
                
        except Exception as e:
            state.set_error("batch_processing", e)
            state.add_log(f"Fatal error in batch processing: {str(e)}")
            
        return state
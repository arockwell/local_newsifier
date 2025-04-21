"""Entity service for coordinating entity-related operations."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

from local_newsifier.models.entity import Entity
from local_newsifier.models.entity_tracking import CanonicalEntity, EntityMentionContext, EntityProfile
from local_newsifier.models.state import EntityTrackingState, EntityBatchTrackingState, EntityDashboardState, EntityRelationshipState, TrackingStatus
from local_newsifier.database.engine import SessionManager

class EntityService:
    """Service for entity-related operations using the new refactored tools."""
    
    def __init__(
        self,
        entity_crud,
        canonical_entity_crud,
        entity_mention_context_crud,
        entity_profile_crud,
        article_crud,
        entity_extractor,
        context_analyzer,
        entity_resolver,
        session_factory=None
    ):
        """Initialize with dependencies.
        
        Args:
            entity_crud: CRUD for entities
            canonical_entity_crud: CRUD for canonical entities
            entity_mention_context_crud: CRUD for entity mention contexts
            entity_profile_crud: CRUD for entity profiles
            article_crud: CRUD for articles
            entity_extractor: Tool for extracting entities from text
            context_analyzer: Tool for analyzing entity contexts
            entity_resolver: Tool for resolving entities to canonical forms
            session_factory: Factory for database sessions
        """
        self.entity_crud = entity_crud
        self.canonical_entity_crud = canonical_entity_crud
        self.entity_mention_context_crud = entity_mention_context_crud
        self.entity_profile_crud = entity_profile_crud
        self.article_crud = article_crud
        self.entity_extractor = entity_extractor
        self.context_analyzer = context_analyzer
        self.entity_resolver = entity_resolver
        self.session_factory = session_factory or SessionManager
    
    def process_article_entities(
        self, 
        article_id: int,
        content: str,
        title: str,
        published_at: datetime
    ) -> List[Dict[str, Any]]:
        """Process an article to extract and track entities.
        
        Args:
            article_id: ID of the article
            content: Article content
            title: Article title
            published_at: Article publication date
            
        Returns:
            List of processed entities with metadata
        """
        # Extract entities using the new EntityExtractor
        entities = self.entity_extractor.extract_entities(content)
        
        processed_entities = []
        
        # Use the provided session_factory instead of creating a new SessionManager
        with self.session_factory() as session:
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
                # Analyze context using the new ContextAnalyzer
                context_analysis = self.context_analyzer.analyze_context(entity["context"])
                
                # Resolve entity using the new EntityResolver
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
            
            # Update article status if session is available
            with self.session_factory() as session:
                self.article_crud.update_status(
                    session, 
                    article_id=state.article_id, 
                    status="entity_tracked"
                )
                
        except Exception as e:
            state.set_error("entity_tracking", e)
            state.add_log(f"Error processing entities: {str(e)}")
            
        return state

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
            
            # Get articles with the specified status
            with self.session_factory() as session:
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
                        state.add_log(f"Error processing article {article.id}: {str(e)}")
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

    def generate_entity_dashboard(self, state: EntityDashboardState) -> EntityDashboardState:
        """Generate dashboard data for entities.
        
        Args:
            state: EntityDashboardState with dashboard parameters
            
        Returns:
            Updated state with dashboard data
        """
        try:
            # Update state status
            state.status = TrackingStatus.PROCESSING
            state.add_log(f"Generating entity dashboard for {state.entity_type} entities over past {state.days} days")
            
            # Calculate date range
            state.end_date = datetime.now(timezone.utc)
            state.start_date = state.end_date - timedelta(days=state.days)
            
            with self.session_factory() as session:
                # Get all canonical entities of the specified type
                entities = self.canonical_entity_crud.get_by_type(session, entity_type=state.entity_type)
                
                # Get mention counts and trends for each entity
                entity_data = []
                for entity in entities:
                    # Get mention count
                    mention_count = self.canonical_entity_crud.get_mentions_count(session, entity_id=entity.id)
                    timeline = self.canonical_entity_crud.get_entity_timeline(
                        session, entity_id=entity.id, start_date=state.start_date, end_date=state.end_date
                    )
                    sentiment_trend = self.entity_mention_context_crud.get_sentiment_trend(
                        session, entity_id=entity.id, start_date=state.start_date, end_date=state.end_date
                    )
                    
                    # Add to entity data
                    entity_data.append(
                        {
                            "id": entity.id,
                            "name": entity.name,
                            "type": entity.entity_type,
                            "mention_count": mention_count,
                            "first_seen": entity.first_seen,
                            "last_seen": entity.last_seen,
                            "timeline": timeline[:5],  # Include only 5 most recent mentions
                            "sentiment_trend": sentiment_trend,
                        }
                    )
                
                # Sort entities by mention count (descending)
                entity_data.sort(key=lambda x: x["mention_count"], reverse=True)
                
                # Prepare dashboard data
                dashboard = {
                    "date_range": {"start": state.start_date, "end": state.end_date, "days": state.days},
                    "entity_count": len(entity_data),
                    "total_mentions": sum(e["mention_count"] for e in entity_data),
                    "entities": entity_data[:20],  # Include only top 20 entities
                }
                
                # Update state with dashboard data
                state.dashboard_data = dashboard
                state.status = TrackingStatus.SUCCESS
                state.add_log(f"Successfully generated dashboard with {len(entity_data)} entities")
                
        except Exception as e:
            state.set_error("dashboard_generation", e)
            state.add_log(f"Error generating dashboard: {str(e)}")
            
        return state

    def find_entity_relationships(self, state: EntityRelationshipState) -> EntityRelationshipState:
        """Find relationships between entities based on co-occurrence.
        
        Args:
            state: EntityRelationshipState with relationship parameters
            
        Returns:
            Updated state with relationship data
        """
        try:
            # Update state status
            state.status = TrackingStatus.PROCESSING
            state.add_log(f"Finding relationships for entity {state.entity_id} over past {state.days} days")
            
            # Calculate date range
            state.end_date = datetime.now(timezone.utc)
            state.start_date = state.end_date - timedelta(days=state.days)
            
            with self.session_factory() as session:
                # Get entity name and articles
                entity = self.canonical_entity_crud.get(session, id=state.entity_id)
                
                if not entity:
                    raise ValueError(f"Entity with ID {state.entity_id} not found")
                
                # Log entity name
                state.add_log(f"Analyzing relationships for entity: {entity.name}")
                
                # Get articles mentioning this entity in the date range
                articles = self.canonical_entity_crud.get_articles_mentioning_entity(
                    session, entity_id=state.entity_id, start_date=state.start_date, end_date=state.end_date
                )
                
                state.add_log(f"Found {len(articles)} articles mentioning this entity")
                
                # Find co-occurring entities
                co_occurrences = {}
                for article in articles:
                    # Get all entities mentioned in this article
                    article_entities = self.entity_crud.get_by_article(session, article_id=article.id)
                    
                    # Get canonical entities for these mentions
                    for article_entity in article_entities:
                        # Skip if this is the same entity we're analyzing
                        if article_entity.text == entity.name:
                            continue
                        
                        # Get canonical entity
                        canonical_entity = self.canonical_entity_crud.get_by_name(
                            session, 
                            name=article_entity.text, 
                            entity_type=article_entity.entity_type
                        )
                        
                        # Skip if no canonical entity found
                        if not canonical_entity:
                            continue
                        
                        # Skip if this is still the same entity
                        if canonical_entity.id == state.entity_id:
                            continue
                        
                        # Count co-occurrence
                        if canonical_entity.id in co_occurrences:
                            co_occurrences[canonical_entity.id]["count"] += 1
                            co_occurrences[canonical_entity.id]["articles"].add(article.id)
                        else:
                            co_occurrences[canonical_entity.id] = {
                                "entity": canonical_entity,
                                "count": 1,
                                "articles": {article.id},
                            }
                
                # Convert to list and sort by co-occurrence count
                relationships = []
                for related_id, data in co_occurrences.items():
                    relationships.append(
                        {
                            "entity_id": related_id,
                            "entity_name": data["entity"].name,
                            "entity_type": data["entity"].entity_type,
                            "co_occurrence_count": data["count"],
                            "article_count": len(data["articles"]),
                        }
                    )
                
                relationships.sort(key=lambda x: x["co_occurrence_count"], reverse=True)
                
                # Prepare relationship data
                relationship_data = {
                    "entity_id": state.entity_id,
                    "entity_name": entity.name,
                    "date_range": {"start": state.start_date, "end": state.end_date, "days": state.days},
                    "relationships": relationships[:20],  # Include only top 20 relationships
                }
                
                # Update state with relationship data
                state.relationship_data = relationship_data
                state.status = TrackingStatus.SUCCESS
                state.add_log(f"Successfully identified {len(relationships)} relationships")
                
        except Exception as e:
            state.set_error("relationship_analysis", e)
            state.add_log(f"Error finding relationships: {str(e)}")
            
        return state

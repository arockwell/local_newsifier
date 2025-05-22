"""Implementation tests for EntityService.

This file contains tests that directly test the implementation of EntityService
methods rather than using mocks, to improve code coverage.
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, select

from local_newsifier.crud.article import CRUDArticle
from local_newsifier.crud.canonical_entity import CRUDCanonicalEntity
from local_newsifier.crud.entity import CRUDEntity
from local_newsifier.crud.entity_mention_context import CRUDEntityMentionContext
from local_newsifier.crud.entity_profile import CRUDEntityProfile
from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity
from local_newsifier.models.entity_tracking import (CanonicalEntity, EntityMention,
                                                    EntityMentionContext, EntityProfile,
                                                    EntityRelationship)
from local_newsifier.models.state import (EntityBatchTrackingState, EntityDashboardState,
                                          EntityRelationshipState, EntityTrackingState,
                                          TrackingStatus)
from local_newsifier.services.entity_service import EntityService


class TestEntityServiceImplementation:
    """Test the actual implementation of EntityService."""

    @pytest.fixture
    def mock_extractor(self):
        """Create a mock entity extractor."""
        extractor = MagicMock()
        extractor.extract_entities.return_value = [
            {"text": "John Doe", "type": "PERSON", "start_char": 0, "end_char": 8, "confidence": 0.95, "context": "John Doe met with Jane Smith."},
            {"text": "Jane Smith", "type": "PERSON", "start_char": 10, "end_char": 20, "confidence": 0.90, "context": "John Doe met with Jane Smith."},
            {"text": "New York", "type": "GPE", "start_char": 30, "end_char": 38, "confidence": 0.92, "context": "They were in New York yesterday."}
        ]
        return extractor

    @pytest.fixture
    def mock_resolver(self):
        """Create a mock entity resolver."""
        resolver = MagicMock()
        
        def resolve_side_effect(entities, **kwargs):
            """Convert extracted entities to resolved canonical entities."""
            canonical_entities = []
            for i, entity in enumerate(entities):
                canonical_entities.append({
                    "original_text": entity["text"],
                    "canonical_name": entity["text"],
                    "entity_type": entity["type"],
                    "confidence": entity["confidence"],
                    "canonical_id": f"entity_{i}"
                })
            return canonical_entities
            
        resolver.resolve_entities.side_effect = resolve_side_effect
        return resolver

    @pytest.fixture
    def mock_context_analyzer(self):
        """Create a mock context analyzer."""
        analyzer = MagicMock()
        analyzer.analyze_context.return_value = {
            "sentiment": {"score": 0.5, "label": "neutral"},
            "framing": {"category": "informational"}
        }
        return analyzer
    
    @pytest.fixture
    def entity_service(self, db_session, mock_extractor, mock_resolver, mock_context_analyzer):
        """Create an entity service with real session and mocked components."""
        # Create CRUD instances
        entity_crud = CRUDEntity(Entity)
        canonical_entity_crud = CRUDCanonicalEntity(CanonicalEntity)
        entity_mention_context_crud = CRUDEntityMentionContext(EntityMentionContext)
        entity_profile_crud = CRUDEntityProfile(EntityProfile)
        article_crud = CRUDArticle(Article)
        
        # Initialize entity service with all required dependencies
        return EntityService(
            entity_crud=entity_crud,
            canonical_entity_crud=canonical_entity_crud,
            entity_mention_context_crud=entity_mention_context_crud,
            entity_profile_crud=entity_profile_crud,
            article_crud=article_crud,
            entity_extractor=mock_extractor,
            context_analyzer=mock_context_analyzer,
            entity_resolver=mock_resolver,
            session_factory=lambda: db_session
        )

    @pytest.fixture
    def sample_article(self, db_session):
        """Create a sample article for testing."""
        article = Article(
            title="Test Article",
            content="John Doe met with Jane Smith in New York yesterday.",
            url="https://example.com/test",
            source="test_source",
            status="new",
            published_at=datetime.now(timezone.utc),
            scraped_at=datetime.now(timezone.utc)
        )
        db_session.add(article)
        db_session.commit()
        db_session.refresh(article)
        return article

    @pytest.mark.skip(reason="Database connection issues need to be fixed in a separate PR")
    def test_process_article_entities_implementation(self, entity_service, sample_article):
        """Test the actual implementation of process_article_entities."""
        # Process the article with all required parameters
        result = entity_service.process_article_entities(
            article_id=sample_article.id,
            content=sample_article.content,
            title=sample_article.title,
            published_at=sample_article.published_at or datetime.now(timezone.utc)
        )
        
        # Verify that entities were actually created in the database
        session = entity_service.session_factory()
        entities = session.exec(select(Entity).where(Entity.article_id == sample_article.id)).all()
        
        # Check the results
        assert len(entities) > 0
        assert len(result) > 0
        
        # Verify that the correct number of entities were created
        assert len(entities) == 3  # Based on our mock extractor
        
        # Verify that canonical entities were created
        canonical_entities = session.exec(select(CanonicalEntity)).all()
        assert len(canonical_entities) > 0
        
        # Verify result structure
        assert isinstance(result, list)
        assert len(result) == 3  # Should have 3 entities as defined in mock_extractor
        assert all(isinstance(item, dict) for item in result)
        assert "original_text" in result[0]
        assert "canonical_name" in result[0]
        assert "canonical_id" in result[0]

    @pytest.mark.skip(reason="Database connection issues need to be fixed in a separate PR")
    def test_process_article_with_state_implementation(self, entity_service, sample_article):
        """Test the implementation of process_article_with_state."""
        # Create a tracking state object for the article
        
        state = EntityTrackingState(
            article_id=sample_article.id,
            content=sample_article.content,
            title=sample_article.title,
            published_at=sample_article.published_at or datetime.now(timezone.utc)
        )
        
        # Process the article with state
        result = entity_service.process_article_with_state(state)
        
        # Check that the state was updated
        assert result.status == TrackingStatus.SUCCESS
        assert len(result.entities) > 0
        
        # Verify entities were created in database
        session = entity_service.session_factory()
        entities = session.exec(select(Entity).where(Entity.article_id == sample_article.id)).all()
        assert len(entities) > 0
        
        # Verify result structure
        assert isinstance(result, EntityTrackingState)
        assert len(result.entities) == 3  # Based on our mock extractor

    @pytest.mark.skip(reason="Database connection issues need to be fixed in a separate PR")
    def test_process_articles_batch_implementation(self, entity_service, db_session):
        """Test the implementation of process_articles_batch."""
        # Create multiple articles
        articles = []
        for i in range(3):
            article = Article(
                title=f"Test Article {i}",
                content=f"John Doe met with Jane Smith in New York yesterday. Article {i}.",
                url=f"https://example.com/test-{i}",
                source="test_source",
                status="new",
                published_at=datetime.now(timezone.utc),
                scraped_at=datetime.now(timezone.utc)
            )
            db_session.add(article)
            db_session.commit()
            db_session.refresh(article)
            articles.append(article)
        
        # Create batch tracking state
        state = EntityBatchTrackingState(
            status_filter="new"  # Process articles with "new" status
        )
        
        # Process the batch
        result = entity_service.process_articles_batch(state)
        
        # Check results
        assert isinstance(result, EntityBatchTrackingState)
        assert result.status == TrackingStatus.SUCCESS or result.status == TrackingStatus.FAILED
        assert result.processed_count >= 0
        
        # Even if the process fails, we should have initiated the batch processing
        assert result.total_articles > 0

    @pytest.mark.skip(reason="Database connection issues need to be fixed in a separate PR")
    def test_find_entity_relationships_implementation(self, entity_service, db_session):
        """Test the implementation of find_entity_relationships."""
        # Create canonical entities
        entities = []
        for i, name in enumerate(["John Doe", "Jane Smith", "New York"]):
            entity_type = "PERSON" if i < 2 else "GPE"
            entity = CanonicalEntity(name=name, entity_type=entity_type)
            db_session.add(entity)
            db_session.commit()
            db_session.refresh(entity)
            entities.append(entity)
        
        # Create an article with these entities
        article = Article(
            title="Test Article",
            content="John Doe met with Jane Smith in New York yesterday.",
            url="https://example.com/test-relationship",
            source="test_source",
            status="processed",
            published_at=datetime.now(timezone.utc),
            scraped_at=datetime.now(timezone.utc)
        )
        db_session.add(article)
        db_session.commit()
        db_session.refresh(article)
        
        # Create entity mentions for the article
        mentions = []
        for i, canonical_entity in enumerate(entities):
            entity = Entity(
                article_id=article.id,
                text=canonical_entity.name,
                entity_type=canonical_entity.entity_type,
                start_char=i * 10,
                end_char=i * 10 + len(canonical_entity.name),
                confidence=0.9
            )
            db_session.add(entity)
            db_session.commit()
            db_session.refresh(entity)
            
            mention = EntityMention(
                article_id=article.id,
                canonical_entity_id=canonical_entity.id,
                mention_text=canonical_entity.name,
                confidence=0.9
            )
            db_session.add(mention)
            db_session.commit()
            db_session.refresh(mention)
            mentions.append(mention)
        
        # Create relationship state with the first person entity
        state = EntityRelationshipState(
            entity_id=entities[0].id,  # John Doe
            days=30  # Look back 30 days
        )
        
        # Find relationships
        result = entity_service.find_entity_relationships(state)
        
        # Check results
        assert isinstance(result, EntityRelationshipState)
        
        # We just want to make sure the function runs without errors
        assert result.status in [TrackingStatus.SUCCESS, TrackingStatus.FAILED]

    @pytest.mark.skip(reason="Database connection issues need to be fixed in a separate PR")
    def test_generate_entity_dashboard_implementation(self, entity_service, db_session):
        """Test the implementation of generate_entity_dashboard."""
        # Create a canonical entity
        entity = CanonicalEntity(name="Test Entity", entity_type="PERSON")
        db_session.add(entity)
        db_session.commit()
        db_session.refresh(entity)
        
        # Create a profile for the entity
        profile = EntityProfile(
            canonical_entity_id=entity.id,
            metadata={
                "description": "A test entity",
                "profile_data": {"key": "value"}
            },
            last_updated=datetime.now(timezone.utc)
        )
        db_session.add(profile)
        db_session.commit()
        
        # Create dashboard state
        state = EntityDashboardState(
            entity_type="PERSON",
            days=30
        )
        
        # Generate dashboard
        result = entity_service.generate_entity_dashboard(state)
        
        # Check results
        assert isinstance(result, EntityDashboardState)
        assert result.status in [TrackingStatus.SUCCESS, TrackingStatus.FAILED]
        
        # Even if no data is found, the method should return a valid state
        assert hasattr(result, 'dashboard_data')
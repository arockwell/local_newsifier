"""Tests for the Article and Entity database models."""

import datetime
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from local_newsifier.models.database.base import BaseModel
from local_newsifier.models.database.article import Article
from local_newsifier.models.database.entity import Entity
from local_newsifier.models.state import AnalysisStatus


class TestArticleEntity(unittest.TestCase):
    """Test case for Article and Entity models."""
    
    def setUp(self):
        """Set up a test database."""
        self.engine = create_engine("sqlite:///:memory:")
        BaseModel.metadata.create_all(self.engine)
        self.session = Session(self.engine)
    
    def tearDown(self):
        """Tear down the test database."""
        self.session.close()
    
    def test_article_creation(self):
        """Test creating an Article instance."""
        article = Article(
            url="https://example.com/news/1",
            title="Test Article",
            source_domain="example.com",
            scraped_text="This is a test article.",
            status=AnalysisStatus.INITIALIZED
        )
        self.session.add(article)
        self.session.commit()
        
        assert article.id is not None
        assert article.url == "https://example.com/news/1"
        assert article.title == "Test Article"
        assert article.source_domain == "example.com"
        assert article.scraped_text == "This is a test article."
        assert article.status == AnalysisStatus.INITIALIZED
        assert isinstance(article.created_at, datetime.datetime)
        assert isinstance(article.updated_at, datetime.datetime)
        assert isinstance(article.scraped_at, datetime.datetime)

    def test_article_entity_relationship(self):
        """Test relationship between Article and Entity."""
        article = Article(
            url="https://example.com/news/1",
            title="Test Article",
            source_domain="example.com",
            scraped_text="This is a test article about Gainesville.",
            status=AnalysisStatus.SCRAPE_SUCCEEDED
        )
        
        entity = Entity(
            text="Gainesville",
            entity_type="GPE",
            sentence_context="This is a test article about Gainesville."
        )
        
        article.entities.append(entity)
        self.session.add(article)
        self.session.commit()
        
        # Refresh the session to ensure we're getting fresh data
        self.session.refresh(article)
        
        assert len(article.entities) == 1
        assert article.entities[0].text == "Gainesville"
        assert article.entities[0].entity_type == "GPE"
        assert article.entities[0].article_id == article.id
        assert article.entities[0].article == article

    def test_article_unique_url_constraint(self):
        """Test that article URL must be unique."""
        article1 = Article(
            url="https://example.com/news/1",
            title="Test Article 1",
            source_domain="example.com"
        )
        self.session.add(article1)
        self.session.commit()
        
        article2 = Article(
            url="https://example.com/news/1",  # Same URL as article1
            title="Test Article 2",
            source_domain="example.com"
        )
        self.session.add(article2)
        
        # This should raise an exception due to unique constraint
        with self.assertRaises(Exception):
            self.session.commit()

    def test_article_cascade_delete(self):
        """Test that deleting an article cascades to its entities."""
        article = Article(
            url="https://example.com/news/1",
            title="Test Article",
            source_domain="example.com"
        )
        
        entity = Entity(
            text="Gainesville",
            entity_type="GPE",
            sentence_context="This is a test article about Gainesville."
        )
        
        article.entities.append(entity)
        self.session.add(article)
        self.session.commit()
        
        # Get the entity ID for later check
        entity_id = entity.id
        
        # Delete the article
        self.session.delete(article)
        self.session.commit()
        
        # Check if entity is also deleted
        remaining_entity = self.session.query(Entity).filter_by(id=entity_id).first()
        assert remaining_entity is None
        
    def test_entity_creation(self):
        """Test creating an Entity instance."""
        article = Article(
            url="https://example.com/news/1",
            title="Test Article",
            source_domain="example.com",
            status=AnalysisStatus.SCRAPE_SUCCEEDED
        )
        self.session.add(article)
        self.session.commit()
        
        entity = Entity(
            article_id=article.id,
            text="Gainesville",
            entity_type="GPE",
            sentence_context="This is about Gainesville.",
            confidence=0.95
        )
        self.session.add(entity)
        self.session.commit()
        
        assert entity.id is not None
        assert entity.article_id == article.id
        assert entity.text == "Gainesville"
        assert entity.entity_type == "GPE"
        assert entity.sentence_context == "This is about Gainesville."
        assert entity.confidence == 0.95
        assert isinstance(entity.created_at, datetime.datetime)
        assert isinstance(entity.updated_at, datetime.datetime)

    def test_multiple_entities_for_article(self):
        """Test that an article can have multiple entities."""
        article = Article(
            url="https://example.com/news/1",
            title="Test Article",
            source_domain="example.com",
            status=AnalysisStatus.SCRAPE_SUCCEEDED
        )
        self.session.add(article)
        self.session.commit()
        
        entities = [
            Entity(text="Gainesville", entity_type="GPE"),
            Entity(text="University of Florida", entity_type="ORG"),
            Entity(text="John Smith", entity_type="PERSON")
        ]
        
        for entity in entities:
            article.entities.append(entity)
        
        self.session.commit()
        
        # Refresh the session
        self.session.refresh(article)
        
        assert len(article.entities) == 3
        
        # Check that all entities are properly associated
        entity_texts = [e.text for e in article.entities]
        assert "Gainesville" in entity_texts
        assert "University of Florida" in entity_texts
        assert "John Smith" in entity_texts

    def test_entity_default_values(self):
        """Test default values for Entity fields."""
        article = Article(
            url="https://example.com/news/1",
            title="Test Article",
            source_domain="example.com",
            status=AnalysisStatus.SCRAPE_SUCCEEDED
        )
        self.session.add(article)
        self.session.commit()
        
        entity = Entity(
            article_id=article.id,
            text="Gainesville",
            entity_type="GPE"
        )
        self.session.add(entity)
        self.session.commit()
        
        assert entity.confidence == 1.0  # Default confidence value
        assert entity.created_at is not None
        assert entity.updated_at is not None
        
    def test_full_article_entity_workflow(self):
        """Test a full workflow of creating an article with entities."""
        # Create an article
        article = Article(
            url="https://example.com/news/1",
            title="Local News: City Council Approves New Budget",
            source_domain="example.com",
            scraped_text=(
                "The Gainesville City Council approved a new budget yesterday. "
                "Mayor John Smith praised the decision, saying it would help fund "
                "critical infrastructure projects for the University of Florida community."
            ),
            status=AnalysisStatus.ANALYSIS_SUCCEEDED
        )
        
        # Create entities
        entities = [
            Entity(
                text="Gainesville City Council",
                entity_type="ORG",
                sentence_context="The Gainesville City Council approved a new budget yesterday.",
                confidence=0.92
            ),
            Entity(
                text="John Smith",
                entity_type="PERSON",
                sentence_context="Mayor John Smith praised the decision.",
                confidence=0.98
            ),
            Entity(
                text="University of Florida",
                entity_type="ORG",
                sentence_context="Critical infrastructure projects for the University of Florida community.",
                confidence=0.95
            ),
            Entity(
                text="Gainesville",
                entity_type="GPE",
                sentence_context="The Gainesville City Council approved a new budget yesterday.",
                confidence=0.97
            )
        ]
        
        # Add entities to article
        for entity in entities:
            article.entities.append(entity)
        
        # Save to database
        self.session.add(article)
        self.session.commit()
        
        # Retrieve article from database
        retrieved_article = self.session.query(Article).filter_by(url="https://example.com/news/1").first()
        
        # Verify article data
        assert retrieved_article is not None
        assert retrieved_article.title == "Local News: City Council Approves New Budget"
        assert retrieved_article.status == AnalysisStatus.ANALYSIS_SUCCEEDED
        
        # Verify entities
        assert len(retrieved_article.entities) == 4
        
        # Check for specific entities
        entity_texts = [e.text for e in retrieved_article.entities]
        assert "Gainesville City Council" in entity_texts
        assert "John Smith" in entity_texts
        assert "University of Florida" in entity_texts
        assert "Gainesville" in entity_texts
        
        # Verify entity types
        person_entities = [e for e in retrieved_article.entities if e.entity_type == "PERSON"]
        org_entities = [e for e in retrieved_article.entities if e.entity_type == "ORG"]
        gpe_entities = [e for e in retrieved_article.entities if e.entity_type == "GPE"]
        
        assert len(person_entities) == 1
        assert len(org_entities) == 2
        assert len(gpe_entities) == 1
        
        # Verify relationships
        for entity in retrieved_article.entities:
            assert entity.article == retrieved_article
            assert entity.article_id == retrieved_article.id
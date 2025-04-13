"""Tests for compatibility between SQLAlchemy models and Pydantic models."""

import unittest
from datetime import datetime, timezone

from local_newsifier.models.database.article import ArticleDB
from local_newsifier.models.database.entity import EntityDB
from local_newsifier.models.database.analysis_result import AnalysisResultDB

# Direct imports from the database.py file
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from src.local_newsifier.models.database import (
    ArticleBase, ArticleCreate, Article,
    EntityBase, EntityCreate, Entity,
    AnalysisResultBase, AnalysisResultCreate, AnalysisResult
)
from local_newsifier.models.state import AnalysisStatus


class TestPydanticCompatibility(unittest.TestCase):
    """Test case for compatibility between SQLAlchemy and Pydantic models."""
    
    def test_article_create_to_article_db(self):
        """Test creating ArticleDB from ArticleCreate."""
        # Create an ArticleCreate instance
        article_create = ArticleCreate(
            url="https://example.com/news/1",
            title="Test Article",
            source="example.com",
            content="This is a test article.",
            status=AnalysisStatus.INITIALIZED.value,
        )
        
        # Convert to dictionary
        article_data = article_create.model_dump()
        
        # Create ArticleDB
        article_db = ArticleDB(**article_data)
        
        # Verify
        self.assertEqual(article_db.url, "https://example.com/news/1")
        self.assertEqual(article_db.title, "Test Article")
        self.assertEqual(article_db.source, "example.com")
        self.assertEqual(article_db.content, "This is a test article.")
        self.assertEqual(article_db.status, AnalysisStatus.INITIALIZED.value)
    
    def test_entity_create_to_entity_db(self):
        """Test creating EntityDB from EntityCreate."""
        # Create an EntityCreate instance
        entity_create = EntityCreate(
            article_id=1,
            text="Test Entity",
            entity_type="CONCEPT",
            confidence=0.9,
        )
        
        # Convert to dictionary
        entity_data = entity_create.model_dump()
        
        # Create EntityDB
        entity_db = EntityDB(**entity_data)
        
        # Verify
        self.assertEqual(entity_db.article_id, 1)
        self.assertEqual(entity_db.text, "Test Entity")
        self.assertEqual(entity_db.entity_type, "CONCEPT")
        self.assertEqual(entity_db.confidence, 0.9)
    
    def test_analysis_result_create_to_analysis_result_db(self):
        """Test creating AnalysisResultDB from AnalysisResultCreate."""
        # Create an AnalysisResultCreate instance
        analysis_create = AnalysisResultCreate(
            article_id=1,
            analysis_type="sentiment",
            results={"score": 0.75, "label": "positive"},
        )
        
        # Convert to dictionary
        analysis_data = analysis_create.model_dump()
        
        # Create AnalysisResultDB
        analysis_db = AnalysisResultDB(**analysis_data)
        
        # Verify
        self.assertEqual(analysis_db.article_id, 1)
        self.assertEqual(analysis_db.analysis_type, "sentiment")
        self.assertEqual(analysis_db.results["score"], 0.75)
        self.assertEqual(analysis_db.results["label"], "positive")
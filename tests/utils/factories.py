"""Model factories for test data generation.

This module provides factories for creating test instances of models.
It uses factory_boy and Faker to generate realistic test data.
"""

import factory
from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker
from datetime import datetime, timezone
import random
import uuid

from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity
from local_newsifier.models.analysis_result import AnalysisResult
from local_newsifier.models.entity_tracking import (
    CanonicalEntity, EntityMention, EntityMentionContext,
    EntityProfile, EntityRelationship
)

fake = Faker()

class BaseFactory(SQLAlchemyModelFactory):
    """Base factory for all model factories."""
    
    class Meta:
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"

class ArticleFactory(BaseFactory):
    """Factory for Article models."""
    
    class Meta:
        model = Article
    
    title = factory.LazyFunction(lambda: fake.sentence(nb_words=6))
    content = factory.LazyFunction(lambda: "\n\n".join(fake.paragraphs(nb=3)))
    url = factory.LazyFunction(lambda: fake.url())
    source = factory.LazyFunction(lambda: fake.company())
    published_at = factory.LazyFunction(lambda: fake.date_time_this_month(tzinfo=timezone.utc))
    status = factory.LazyFunction(lambda: random.choice(["new", "processed", "analyzed"]))
    scraped_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))

class EntityFactory(BaseFactory):
    """Factory for Entity models."""
    
    class Meta:
        model = Entity
    
    article_id = factory.SelfAttribute('article.id')
    article = factory.SubFactory(ArticleFactory)
    text = factory.LazyFunction(lambda: fake.name())
    entity_type = factory.LazyFunction(lambda: random.choice(["PERSON", "ORG", "GPE", "LOC"]))
    confidence = factory.LazyFunction(lambda: round(random.uniform(0.7, 1.0), 2))
    sentence_context = factory.LazyFunction(lambda: fake.sentence())

class AnalysisResultFactory(BaseFactory):
    """Factory for AnalysisResult models."""
    
    class Meta:
        model = AnalysisResult
    
    article_id = factory.SelfAttribute('article.id')
    article = factory.SubFactory(ArticleFactory)
    analysis_type = factory.LazyFunction(lambda: random.choice(["NER", "SENTIMENT", "TOPIC"]))
    results = factory.LazyFunction(lambda: {"score": round(random.uniform(0, 1), 2), "entities": random.randint(1, 10)})

class CanonicalEntityFactory(BaseFactory):
    """Factory for CanonicalEntity models."""
    
    class Meta:
        model = CanonicalEntity
    
    name = factory.LazyFunction(lambda: fake.name())
    entity_type = factory.LazyFunction(lambda: random.choice(["PERSON", "ORG", "GPE", "LOC"]))
    description = factory.LazyFunction(lambda: fake.paragraph())
    entity_metadata = factory.LazyFunction(lambda: {"source": fake.company(), "id": str(uuid.uuid4())})

class EntityMentionContextFactory(BaseFactory):
    """Factory for EntityMentionContext models."""
    
    class Meta:
        model = EntityMentionContext
    
    entity_id = factory.SelfAttribute('entity.id')
    entity = factory.SubFactory(EntityFactory)
    article_id = factory.SelfAttribute('entity.article_id')
    context_text = factory.LazyFunction(lambda: fake.paragraph())
    context_type = factory.LazyFunction(lambda: random.choice(["sentence", "paragraph"]))
    sentiment_score = factory.LazyFunction(lambda: round(random.uniform(-1.0, 1.0), 2))

class EntityProfileFactory(BaseFactory):
    """Factory for EntityProfile models."""
    
    class Meta:
        model = EntityProfile
    
    canonical_entity_id = factory.SelfAttribute('canonical_entity.id')
    canonical_entity = factory.SubFactory(CanonicalEntityFactory)
    profile_type = factory.LazyFunction(lambda: random.choice(["summary", "biography", "analysis"]))
    content = factory.LazyFunction(lambda: fake.paragraphs(nb=2))
    profile_metadata = factory.LazyFunction(lambda: {"source": fake.company(), "created_at": datetime.now().isoformat()})

class EntityRelationshipFactory(BaseFactory):
    """Factory for EntityRelationship models."""
    
    class Meta:
        model = EntityRelationship
    
    source_entity_id = factory.SelfAttribute('source_entity.id')
    source_entity = factory.SubFactory(CanonicalEntityFactory)
    target_entity_id = factory.SelfAttribute('target_entity.id')
    target_entity = factory.SubFactory(CanonicalEntityFactory)
    relationship_type = factory.LazyFunction(lambda: random.choice(["WORKS_FOR", "LOCATED_IN", "RELATED_TO"]))
    confidence = factory.LazyFunction(lambda: round(random.uniform(0.7, 1.0), 2))
    evidence = factory.LazyFunction(lambda: fake.paragraph())

# Factory utility functions

def create_article_batch(session, count=3):
    """Create a batch of articles."""
    ArticleFactory._meta.sqlalchemy_session = session
    return ArticleFactory.create_batch(count)

def create_entity_batch(session, article=None, count=5):
    """Create a batch of entities, optionally for a specific article."""
    EntityFactory._meta.sqlalchemy_session = session
    
    if article:
        return EntityFactory.create_batch(count, article=article)
    else:
        return EntityFactory.create_batch(count)

def create_canonical_entity_batch(session, count=3):
    """Create a batch of canonical entities."""
    CanonicalEntityFactory._meta.sqlalchemy_session = session
    return CanonicalEntityFactory.create_batch(count)

def create_related_entities(session, count=2):
    """Create related canonical entities with relationships."""
    CanonicalEntityFactory._meta.sqlalchemy_session = session
    EntityRelationshipFactory._meta.sqlalchemy_session = session
    
    entities = CanonicalEntityFactory.create_batch(count)
    relationships = []
    
    for i in range(count-1):
        relationships.append(EntityRelationshipFactory.create(
            source_entity=entities[i],
            target_entity=entities[i+1]
        ))
    
    # Add a circular relationship for the last entity
    relationships.append(EntityRelationshipFactory.create(
        source_entity=entities[-1],
        target_entity=entities[0]
    ))
    
    return entities, relationships

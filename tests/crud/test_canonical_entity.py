"""Tests for the canonical entity CRUD module."""

from datetime import datetime, timedelta, timezone

# We need pytest for fixtures but don't explicitly use it
from sqlmodel import select

from local_newsifier.crud.canonical_entity import CRUDCanonicalEntity
from local_newsifier.crud.canonical_entity import (
    canonical_entity as canonical_entity_crud,
)
from local_newsifier.models.article import Article
from local_newsifier.models.entity_tracking import (
    CanonicalEntity,
    EntityMention,
)


class TestCanonicalEntityCRUD:
    """Tests for CanonicalEntityCRUD class."""

    def test_create(self, db_session, sample_canonical_entity_data):
        """Test creating a new canonical entity."""
        obj_in = sample_canonical_entity_data
        entity = canonical_entity_crud.create(db_session, obj_in=obj_in)

        assert entity is not None
        assert entity.id is not None
        assert entity.name == obj_in["name"]
        assert entity.entity_type == obj_in["entity_type"]
        assert entity.description == obj_in["description"]
        assert entity.entity_metadata == obj_in["entity_metadata"]
        assert entity.first_seen is not None
        assert entity.last_seen is not None

        # Verify it was saved to the database
        statement = select(CanonicalEntity).where(CanonicalEntity.id == entity.id)
        db_entity = db_session.exec(statement).first()
        assert db_entity is not None
        assert db_entity.name == obj_in["name"]

    def test_get(self, db_session, create_canonical_entity):
        """Test getting a canonical entity by ID."""
        entity = canonical_entity_crud.get(
            db_session, id=create_canonical_entity.id
        )

        assert entity is not None
        assert entity.id == create_canonical_entity.id
        assert entity.name == create_canonical_entity.name
        assert entity.entity_type == create_canonical_entity.entity_type

    def test_get_by_name(self, db_session, create_canonical_entity):
        """Test getting a canonical entity by name and type."""
        entity = canonical_entity_crud.get_by_name(
            db_session,
            name=create_canonical_entity.name,
            entity_type=create_canonical_entity.entity_type,
        )

        assert entity is not None
        assert entity.id == create_canonical_entity.id
        assert entity.name == create_canonical_entity.name
        assert entity.entity_type == create_canonical_entity.entity_type

    def test_get_by_name_not_found(self, db_session):
        """Test getting a non-existent canonical entity by name and type."""
        entity = canonical_entity_crud.get_by_name(
            db_session, name="Nonexistent Entity", entity_type="PERSON"
        )

        assert entity is None

    def test_get_by_type(self, db_session, create_canonical_entities):
        """Test getting canonical entities by type."""
        # Test getting entities of type "PERSON"
        entities = canonical_entity_crud.get_by_type(
            db_session, entity_type="PERSON"
        )

        assert len(entities) == 2
        for entity in entities:
            assert entity.entity_type == "PERSON"

        # Test getting entities of type "ORG"
        entities = canonical_entity_crud.get_by_type(
            db_session, entity_type="ORG"
        )

        assert len(entities) == 1
        assert entities[0].entity_type == "ORG"

        # Test getting entities of a non-existent type
        entities = canonical_entity_crud.get_by_type(
            db_session, entity_type="NONEXISTENT"
        )

        assert len(entities) == 0

    def test_get_all(self, db_session, create_canonical_entities):
        """Test getting all canonical entities."""
        # Test getting all entities without filtering
        entities = canonical_entity_crud.get_all(db_session)

        assert len(entities) == 3

        # Test getting all entities with filtering by type
        entities = canonical_entity_crud.get_all(
            db_session, entity_type="PERSON"
        )

        assert len(entities) == 2
        for entity in entities:
            assert entity.entity_type == "PERSON"

    def test_get_mentions_count(
        self, db_session, create_canonical_entity, create_entity
    ):
        """Test getting the count of mentions for an entity."""
        # Add an entity mention
        entity_mention = EntityMention(
            canonical_entity_id=create_canonical_entity.id,
            entity_id=create_entity.id,
            article_id=create_entity.article_id,
            confidence=0.9,
        )
        db_session.add(entity_mention)
        db_session.commit()

        # Test getting the mentions count
        count = canonical_entity_crud.get_mentions_count(
            db_session, entity_id=create_canonical_entity.id
        )

        assert count == 1

        # Add another entity mention
        entity_mention2 = EntityMention(
            canonical_entity_id=create_canonical_entity.id,
            entity_id=create_entity.id + 1,  # Using a different entity ID
            article_id=create_entity.article_id,
            confidence=0.85,
        )
        db_session.add(entity_mention2)
        db_session.commit()

        # Test getting the updated mentions count
        count = canonical_entity_crud.get_mentions_count(
            db_session, entity_id=create_canonical_entity.id
        )

        assert count == 2

    def test_get_entity_timeline(
        self, db_session, create_canonical_entity, create_article
    ):
        """Test getting the timeline of entity mentions."""
        # Create articles with different published dates
        articles = []
        base_date = datetime.now(timezone.utc)
        for i in range(5):
            article = Article(
                title=f"Test Article {i}",
                content=f"This is test article {i}.",
                url=f"https://example.com/test-article-{i}",
                source="test_source",
                published_at=base_date - timedelta(days=i),
                status="new",
                scraped_at=datetime.now(timezone.utc),
            )
            db_session.add(article)
            db_session.flush()
            articles.append(article)
        db_session.commit()

        # Create entity mentions for different articles
        for i, article in enumerate(articles):
            # Add entity mention for different articles
            entity_mention = EntityMention(
                canonical_entity_id=create_canonical_entity.id,
                entity_id=i + 100,  # Using different entity IDs
                article_id=article.id,
                confidence=0.9,
            )
            db_session.add(entity_mention)

        # Add multiple mentions for one of the articles
        additional_mention = EntityMention(
            canonical_entity_id=create_canonical_entity.id,
            entity_id=200,
            article_id=articles[0].id,
            confidence=0.85,
        )
        db_session.add(additional_mention)
        db_session.commit()

        # Test getting the entity timeline
        start_date = base_date - timedelta(days=10)
        end_date = base_date + timedelta(days=1)
        timeline = canonical_entity_crud.get_entity_timeline(
            db_session,
            entity_id=create_canonical_entity.id,
            start_date=start_date,
            end_date=end_date,
        )

        assert len(timeline) == 5
        # The first article should have 2 mentions
        assert any(
            entry["date"] == articles[0].published_at
            and entry["mention_count"] == 2
            for entry in timeline
        )
        # The other articles should have 1 mention each
        for i in range(1, 5):
            assert any(
                entry["date"] == articles[i].published_at
                and entry["mention_count"] == 1
                for entry in timeline
            )

    def test_get_articles_mentioning_entity(
        self, db_session, create_canonical_entity, create_article
    ):
        """Test getting articles mentioning an entity."""
        # Create additional articles
        articles = []
        base_date = datetime.now(timezone.utc)
        for i in range(5):
            article = Article(
                title=f"Test Article {i}",
                content=f"This is test article {i}.",
                url=f"https://example.com/test-article-{i}",
                source="test_source",
                published_at=base_date - timedelta(days=i),
                status="new",
                scraped_at=datetime.now(timezone.utc),
            )
            db_session.add(article)
            db_session.flush()
            articles.append(article)
        db_session.commit()

        # Create entity mentions for some of the articles
        for i in range(
            0, 3
        ):  # Only mention the entity in the first 3 articles
            entity_mention = EntityMention(
                canonical_entity_id=create_canonical_entity.id,
                entity_id=i + 100,
                article_id=articles[i].id,
                confidence=0.9,
            )
            db_session.add(entity_mention)
        db_session.commit()

        # Test getting articles mentioning the entity
        start_date = base_date - timedelta(days=10)
        end_date = base_date + timedelta(days=1)
        db_articles = canonical_entity_crud.get_articles_mentioning_entity(
            db_session,
            entity_id=create_canonical_entity.id,
            start_date=start_date,
            end_date=end_date,
        )

        assert len(db_articles) == 3
        article_ids = [article.id for article in db_articles]
        for i in range(0, 3):
            assert articles[i].id in article_ids

    def test_singleton_instance(self):
        """Test singleton instance behavior."""
        assert isinstance(canonical_entity_crud, CRUDCanonicalEntity)
        assert canonical_entity_crud.model == CanonicalEntity

"""Tests for database models with PostgreSQL."""

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from local_newsifier.models.database.base import Base
from local_newsifier.models.database.article import ArticleDB
from local_newsifier.models.database.entity import EntityDB
from local_newsifier.models.state import AnalysisStatus


@pytest.fixture(scope="session")
def postgres_url():
    """Generate a unique test database URL."""
    import uuid

    test_db_name = f"local_newsifier_test_{uuid.uuid4().hex[:8]}"
    return f"postgresql://postgres:postgres@localhost:5432/{test_db_name}"


@pytest.fixture(scope="session")
def engine(postgres_url):
    """Create a PostgreSQL engine for testing."""
    # Connect to default postgres database to create test db
    admin_url = postgres_url.rsplit("/", 1)[0] + "/postgres"
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    test_db_name = postgres_url.rsplit("/", 1)[1]

    # Create test database
    with admin_engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
        conn.execute(text(f"CREATE DATABASE {test_db_name}"))

    # Create engine for the test database
    engine = create_engine(postgres_url)
    Base.metadata.create_all(engine)

    yield engine

    # Clean up
    Base.metadata.drop_all(engine)
    engine.dispose()

    # Drop the test database
    with admin_engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
    admin_engine.dispose()


@pytest.fixture
def session(engine):
    """Create a session for testing."""
    with Session(engine) as session:
        yield session
        session.rollback()


def test_schema_generation(engine):
    """Test that the schema is properly generated."""
    inspector = inspect(engine)

    # Check that all tables are created
    tables = inspector.get_table_names()
    assert "articles" in tables
    assert "entities" in tables

    # Check article table columns
    article_columns = {
        col["name"] for col in inspector.get_columns("articles")
    }
    expected_article_columns = {
        "id",
        "url",
        "title",
        "source",
        "content",
        "scraped_at",
        "status",
        "created_at",
        "updated_at",
    }
    assert expected_article_columns.issubset(article_columns)

    # Check entity table columns
    entity_columns = {col["name"] for col in inspector.get_columns("entities")}
    expected_entity_columns = {
        "id",
        "article_id",
        "text",
        "entity_type",
        "sentence_context",
        "created_at",
        "updated_at",
    }
    assert expected_entity_columns.issubset(entity_columns)


def test_query_by_status(session):
    """Test querying articles by status."""
    # Create articles with different statuses
    articles = [
        ArticleDB(
            url=f"https://example.com/news/status/{i}",
            title=f"Status Test {i}",
            source="example.com",
            status=status.value,
        )
        for i, status in enumerate(
            [
                AnalysisStatus.INITIALIZED,
                AnalysisStatus.SCRAPE_SUCCEEDED,
                AnalysisStatus.ANALYSIS_SUCCEEDED,
                AnalysisStatus.INITIALIZED,  # Duplicate status
            ]
        )
    ]

    # Add to session and commit
    session.add_all(articles)
    session.commit()

    # Query by status
    initialized = (
        session.query(ArticleDB)
        .filter_by(status=AnalysisStatus.INITIALIZED.value)
        .all()
    )

    # Verify
    assert len(initialized) == 2


def test_full_article_entity_workflow(session):
    """Test a full workflow of creating an article with entities."""
    # Create a unique URL for this test
    import uuid

    unique_id = uuid.uuid4().hex[:8]

    # Create an article
    article = ArticleDB(
        url=f"https://example.com/news/workflow/{unique_id}",
        title="Local News: City Council Approves New Budget",
        source="Example News",
        content=(
            "The Gainesville City Council approved a new budget yesterday. "
            "Mayor John Smith praised the decision, saying it would help fund "
            "critical infrastructure projects for the University of Florida community."
        ),
        status=AnalysisStatus.ANALYSIS_SUCCEEDED.value,
    )

    # Create entities
    entities = [
        EntityDB(
            text="Gainesville City Council",
            entity_type="ORG",
            sentence_context=(
                "The Gainesville City Council approved a new budget yesterday."
            ),
        ),
        EntityDB(
            text="John Smith",
            entity_type="PERSON",
            sentence_context="Mayor John Smith praised the decision.",
        ),
        EntityDB(
            text="University of Florida",
            entity_type="ORG",
            sentence_context=(
                "Critical infrastructure projects for the University of Florida community."
            ),
        ),
        EntityDB(
            text="Gainesville",
            entity_type="GPE",
            sentence_context=(
                "The Gainesville City Council approved a new budget yesterday."
            ),
        ),
    ]

    # Add entities to article
    for entity in entities:
        article.entities.append(entity)

    # Save to database
    session.add(article)
    session.commit()

    # Retrieve article from database
    retrieved_article = (
        session.query(ArticleDB).filter_by(url=article.url).first()
    )

    # Verify article data
    assert retrieved_article is not None
    assert (
        retrieved_article.title == "Local News: City Council Approves New Budget"
    )
    assert retrieved_article.status == AnalysisStatus.ANALYSIS_SUCCEEDED.value

    # Verify entities
    assert len(retrieved_article.entities) == 4

    # Check for specific entities
    entity_texts = [e.text for e in retrieved_article.entities]
    assert "Gainesville City Council" in entity_texts
    assert "John Smith" in entity_texts
    assert "University of Florida" in entity_texts
    assert "Gainesville" in entity_texts

    # Verify entity types
    person_entities = [
        e for e in retrieved_article.entities 
        if e.entity_type == "PERSON"
    ]
    org_entities = [
        e for e in retrieved_article.entities 
        if e.entity_type == "ORG"
    ]
    gpe_entities = [
        e for e in retrieved_article.entities 
        if e.entity_type == "GPE"
    ]

    assert len(person_entities) == 1
    assert len(org_entities) == 2
    assert len(gpe_entities) == 1

    # Verify relationships
    for entity in retrieved_article.entities:
        assert entity.article == retrieved_article


@pytest.fixture(scope="module")
def sqlite_engine():
    """Set up a SQLite in-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(sqlite_engine):
    """Create a test database session."""
    TestSession = sessionmaker(bind=sqlite_engine)
    session = TestSession()
    yield session
    session.close()


def test_article_entity_integration(db_session):
    """Test the integration between Article and Entity models."""
    # Create an article
    article = ArticleDB(
        url="https://example.com/news/1",
        title="Test Article",
        source="Example News",
        content="This is a test article about Gainesville.",
        status=AnalysisStatus.INITIALIZED.value
    )
    db_session.add(article)
    db_session.commit()

    # Create entities
    entities = [
        EntityDB(
            text="Gainesville",
            entity_type="GPE",
            sentence_context=(
                "This is a test article about Gainesville."
            )
        ),
        EntityDB(
            text="University of Florida",
            entity_type="ORG",
            sentence_context=(
                "The University of Florida is located in Gainesville."
            )
        ),
        EntityDB(
            text="John Smith",
            entity_type="PERSON",
            sentence_context=(
                "John Smith is a professor at the University of Florida."
            )
        )
    ]

    for entity in entities:
        article.entities.append(entity)

    db_session.commit()

    # Verify relationships
    assert len(article.entities) == 3
    assert all(e.article_id == article.id for e in article.entities)
    assert all(e.article == article for e in article.entities)

    # Verify entity types
    entity_types = {e.entity_type for e in article.entities}
    assert "GPE" in entity_types
    assert "ORG" in entity_types
    assert "PERSON" in entity_types

    # Verify entity texts
    entity_texts = {e.text for e in article.entities}
    assert "Gainesville" in entity_texts
    assert "University of Florida" in entity_texts
    assert "John Smith" in entity_texts

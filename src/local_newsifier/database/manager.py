"""Database manager for handling database operations."""

from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.database import (AnalysisResult, AnalysisResultCreate,
                               AnalysisResultDB, Article, ArticleCreate,
                               ArticleDB, Entity, EntityCreate, EntityDB)


class DatabaseManager:
    """Manager class for database operations."""

    def __init__(self, session: Session):
        """Initialize the database manager.

        Args:
            session: SQLAlchemy session instance
        """
        self.session = session

    def create_article(self, article: ArticleCreate) -> Article:
        """Create a new article in the database.

        Args:
            article: Article data to create

        Returns:
            Created article
        """
        db_article = ArticleDB(**article.model_dump())
        self.session.add(db_article)
        self.session.commit()
        self.session.refresh(db_article)
        return Article.model_validate(db_article)

    def get_article(self, article_id: int) -> Optional[Article]:
        """Get an article by ID.

        Args:
            article_id: ID of the article to get

        Returns:
            Article if found, None otherwise
        """
        db_article = (
            self.session.query(ArticleDB).filter(ArticleDB.id == article_id).first()
        )
        return Article.model_validate(db_article) if db_article else None

    def get_article_by_url(self, url: str) -> Optional[Article]:
        """Get an article by URL.

        Args:
            url: URL of the article to get

        Returns:
            Article if found, None otherwise
        """
        db_article = self.session.query(ArticleDB).filter(ArticleDB.url == url).first()
        return Article.model_validate(db_article) if db_article else None

    def add_entity(self, entity: EntityCreate) -> Entity:
        """Add an entity to an article.

        Args:
            entity: Entity data to add

        Returns:
            Created entity
        """
        db_entity = EntityDB(**entity.model_dump())
        self.session.add(db_entity)
        self.session.commit()
        self.session.refresh(db_entity)
        return Entity.model_validate(db_entity)

    def add_analysis_result(self, result: AnalysisResultCreate) -> AnalysisResult:
        """Add an analysis result to an article.

        Args:
            result: Analysis result data to add

        Returns:
            Created analysis result
        """
        db_result = AnalysisResultDB(**result.model_dump())
        self.session.add(db_result)
        self.session.commit()
        self.session.refresh(db_result)
        return AnalysisResult.model_validate(db_result)

    def update_article_status(self, article_id: int, status: str) -> Optional[Article]:
        """Update an article's status.

        Args:
            article_id: ID of the article to update
            status: New status

        Returns:
            Updated article if found, None otherwise
        """
        db_article = (
            self.session.query(ArticleDB).filter(ArticleDB.id == article_id).first()
        )
        if db_article:
            db_article.status = status
            self.session.commit()
            self.session.refresh(db_article)
            return Article.model_validate(db_article)
        return None

    def get_articles_by_status(self, status: str) -> List[Article]:
        """Get all articles with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of articles with the specified status
        """
        db_articles = (
            self.session.query(ArticleDB).filter(ArticleDB.status == status).all()
        )
        return [Article.model_validate(article) for article in db_articles]

    def get_entities_by_article(self, article_id: int) -> List[Entity]:
        """Get all entities for an article.

        Args:
            article_id: ID of the article

        Returns:
            List of entities for the article
        """
        db_entities = (
            self.session.query(EntityDB).filter(EntityDB.article_id == article_id).all()
        )
        return [Entity.model_validate(entity) for entity in db_entities]

    def get_analysis_results_by_article(self, article_id: int) -> List[AnalysisResult]:
        """Get all analysis results for an article.

        Args:
            article_id: ID of the article

        Returns:
            List of analysis results for the article
        """
        db_results = (
            self.session.query(AnalysisResultDB)
            .filter(AnalysisResultDB.article_id == article_id)
            .all()
        )
        return [AnalysisResult.model_validate(result) for result in db_results]

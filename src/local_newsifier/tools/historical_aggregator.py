"""Tool for aggregating historical news article data for trend analysis."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Union

from sqlmodel import Session, select

from local_newsifier.config.database import get_database_settings
from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity
from local_newsifier.models.trend import TimeFrame, TopicFrequency
from local_newsifier.database.init import init_db


class HistoricalDataAggregator:
    """Tool for retrieving and organizing historical news data for analysis."""

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize the historical data aggregator.

        Args:
            session: Optional database session. If not provided,
                    a new one will be created.
        """
        if session is None:
            from sqlmodel import Session
            
            db_settings = get_database_settings()
            engine = init_db(str(db_settings.DATABASE_URL))
            self.session = Session(engine)
        else:
            self.session = session
            
        self._cache: Dict[str, any] = {}

    def get_articles_in_timeframe(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        source: Optional[str] = None,
    ) -> List[Article]:
        """
        Retrieve articles within the specified timeframe.

        Args:
            start_date: Start date for the query
            end_date: End date for the query (defaults to current time)
            source: Optional filter for news source

        Returns:
            List of article records
        """
        if end_date is None:
            end_date = datetime.now(timezone.utc)

        cache_key = f"articles_{start_date.isoformat()}_{end_date.isoformat()}_{source}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Query the database using SQLModel
        statement = select(Article).where(
            Article.published_at >= start_date,
            Article.published_at <= end_date
        )

        if source:
            statement = statement.where(Article.source == source)

        articles = self.session.exec(statement).all()
        self._cache[cache_key] = articles
        return articles

    def calculate_date_range(
        self, time_frame: TimeFrame, periods: int = 1
    ) -> Tuple[datetime, datetime]:
        """
        Calculate start and end dates based on time frame.

        Args:
            time_frame: The time frame unit (DAY, WEEK, MONTH, etc.)
            periods: Number of periods to look back

        Returns:
            Tuple of (start_date, end_date)
        """
        end_date = datetime.now(timezone.utc)

        if time_frame == TimeFrame.DAY:
            start_date = end_date - timedelta(days=periods)
        elif time_frame == TimeFrame.WEEK:
            start_date = end_date - timedelta(weeks=periods)
        elif time_frame == TimeFrame.MONTH:
            # Approximate a month as 30 days
            start_date = end_date - timedelta(days=30 * periods)
        elif time_frame == TimeFrame.QUARTER:
            # Approximate a quarter as 90 days
            start_date = end_date - timedelta(days=90 * periods)
        elif time_frame == TimeFrame.YEAR:
            # Approximate a year as 365 days
            start_date = end_date - timedelta(days=365 * periods)
        else:
            raise ValueError(f"Unsupported time frame: {time_frame}")

        return start_date, end_date

    def get_entity_frequencies(
        self,
        entity_types: List[str],
        start_date: datetime,
        end_date: Optional[datetime] = None,
        top_n: int = 20,
    ) -> Dict[str, TopicFrequency]:
        """
        Get frequency data for entities within a time period.

        Args:
            entity_types: List of entity types to include
            start_date: Start date for the analysis
            end_date: End date for the analysis (defaults to current time)
            top_n: Number of top entities to return

        Returns:
            Dictionary mapping entity text to frequency information
        """
        if end_date is None:
            end_date = datetime.now(timezone.utc)

        cache_key = f"entity_freq_{start_date.isoformat()}_{end_date.isoformat()}_{','.join(entity_types)}_{top_n}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Get all articles in the time period
        articles = self.get_articles_in_timeframe(start_date, end_date)
        article_ids = [article.id for article in articles]

        # No articles found
        if not article_ids:
            return {}

        # Build a date lookup for articles
        article_dates = {article.id: article.published_at for article in articles}

        # Query all entities for these articles
        frequencies: Dict[str, TopicFrequency] = {}
        statement = select(Entity).where(
            Entity.article_id.in_(article_ids),
            Entity.entity_type.in_(entity_types)
        )
        entities = self.session.exec(statement).all()

        # Process entities
        for entity in entities:
            entity_key = f"{entity.text}:{entity.entity_type}"

            if entity_key not in frequencies:
                frequencies[entity_key] = TopicFrequency(
                    topic=entity.text,
                    entity_type=entity.entity_type,
                    frequencies={},
                    total_mentions=0,
                )

            # Get the article date
            article_date = article_dates.get(entity.article_id)
            if article_date:
                frequencies[entity_key].add_occurrence(article_date)

        # Sort by total mentions and take top N
        sorted_frequencies = sorted(
            frequencies.values(), key=lambda x: x.total_mentions, reverse=True
        )
        result = {
            f"{item.topic}:{item.entity_type}": item
            for item in sorted_frequencies[:top_n]
        }

        # Cache the result
        self._cache[cache_key] = result
        return result

    def get_baseline_frequencies(
        self,
        entity_types: List[str],
        time_frame: TimeFrame,
        current_period: int = 1,
        baseline_periods: int = 3,
    ) -> Tuple[Dict[str, TopicFrequency], Dict[str, TopicFrequency]]:
        """
        Get current and baseline frequencies for comparison.

        Args:
            entity_types: List of entity types to include
            time_frame: The time frame to analyze
            current_period: Number of time frame units for current period
            baseline_periods: Number of time frame units for baseline

        Returns:
            Tuple of (current_frequencies, baseline_frequencies)
        """
        # Calculate the current period date range
        current_start, current_end = self.calculate_date_range(
            time_frame, current_period
        )

        # Calculate the baseline period date range
        baseline_start = current_start - timedelta(
            (current_end - current_start).days * baseline_periods
        )
        baseline_end = current_start - timedelta(
            seconds=1
        )  # End just before current period

        # Get frequencies for both periods
        current_frequencies = self.get_entity_frequencies(
            entity_types, current_start, current_end
        )

        baseline_frequencies = self.get_entity_frequencies(
            entity_types, baseline_start, baseline_end
        )

        return current_frequencies, baseline_frequencies

    def clear_cache(self) -> None:
        """Clear the internal cache to free memory."""
        self._cache.clear()
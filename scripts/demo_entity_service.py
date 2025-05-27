#!/usr/bin/env python
"""
Demo script for the refactored entity service architecture.

This script demonstrates how to use the new service layer to process articles
and track entities across them.
"""

import argparse
from datetime import datetime
from pathlib import Path

from local_newsifier.crud.analysis_result import analysis_result as analysis_result_crud
from local_newsifier.crud.article import article as article_crud
from local_newsifier.crud.canonical_entity import canonical_entity as canonical_entity_crud
from local_newsifier.crud.entity import entity as entity_crud
from local_newsifier.crud.entity_mention_context import \
    entity_mention_context as entity_mention_context_crud
from local_newsifier.crud.entity_profile import entity_profile as entity_profile_crud
from local_newsifier.database.engine import SessionManager
from local_newsifier.services.article_service import ArticleService
from local_newsifier.services.entity_service import EntityService
from local_newsifier.services.news_pipeline_service import NewsPipelineService
from local_newsifier.tools.analysis.context_analyzer import ContextAnalyzer
from local_newsifier.tools.extraction.entity_extractor import EntityExtractor
from local_newsifier.tools.file_writer import FileWriterTool
from local_newsifier.tools.resolution.entity_resolver import EntityResolver
from local_newsifier.tools.web_scraper import WebScraperTool


def setup_services():
    """Set up the service layer components."""
    # Create entity service
    entity_service = EntityService(
        entity_crud=entity_crud,
        canonical_entity_crud=canonical_entity_crud,
        entity_mention_context_crud=entity_mention_context_crud,
        entity_profile_crud=entity_profile_crud,
        entity_extractor=EntityExtractor(),
        context_analyzer=ContextAnalyzer(),
        entity_resolver=EntityResolver(),
        session_factory=None,  # We're using SessionManager directly in the service
    )

    # Create article service
    article_service = ArticleService(
        article_crud=article_crud,
        analysis_result_crud=analysis_result_crud,
        entity_service=entity_service,
        session_factory=None,  # We're using SessionManager directly in the service
    )

    # Create pipeline service
    pipeline_service = NewsPipelineService(
        article_service=article_service,
        web_scraper=WebScraperTool(),
        file_writer=FileWriterTool(output_dir="output"),
        session_factory=None,  # We're using SessionManager directly in the service
    )

    return entity_service, article_service, pipeline_service


def process_url(url, pipeline_service):
    """Process a URL using the pipeline service."""
    print(f"Processing URL: {url}")
    result = pipeline_service.process_url(url)

    if "status" in result and result["status"] == "error":
        print(f"Error: {result['message']}")
        return None

    print(f"Successfully processed article: {result['title']}")
    print(f"Found {len(result['entities'])} entities")

    # Print entity summary
    print("\nEntity Summary:")
    for entity in result["entities"]:
        print(f"- {entity['original_text']} (canonical: {entity['canonical_name']})")
        print(
            f"  Sentiment: {entity['sentiment_score']:.2f}, "
            f"Framing: {entity['framing_category']}"
        )

    return result


def process_content(content, title, url, article_service):
    """Process article content directly using the article service."""
    print(f"Processing article: {title}")
    result = article_service.process_article(
        url=url, content=content, title=title, published_at=datetime.now()
    )

    print(f"Successfully processed article: {result['title']}")
    print(f"Found {len(result['entities'])} entities")

    # Print entity summary
    print("\nEntity Summary:")
    for entity in result["entities"]:
        print(f"- {entity['original_text']} (canonical: {entity['canonical_name']})")
        print(
            f"  Sentiment: {entity['sentiment_score']:.2f}, "
            f"Framing: {entity['framing_category']}"
        )

    return result


def get_entity_dashboard(entity_service):
    """Get a dashboard of all tracked entities."""
    print("\nEntity Dashboard:")

    # Get entity count
    try:
        with SessionManager() as session:
            entities = canonical_entity_crud.get_all(session)
            entity_count = len(entities)
            print(f"Total entities tracked: {entity_count}")

            # Get entity IDs
            entity_ids = [entity.id for entity in entities]
    except Exception as e:
        print(f"Error retrieving entity count: {str(e)}")
        return

    # Process each entity by ID in a separate session
    for entity_id in entity_ids:
        try:
            with SessionManager() as session:
                # Get entity by ID
                entity = canonical_entity_crud.get(session, id=entity_id)
                if not entity:
                    continue

                # Get mention count
                mention_count = canonical_entity_crud.get_mentions_count(
                    session, entity_id=entity_id
                )

                print(f"\n- {entity.name} ({entity.entity_type})")
                print(f"  Mentions: {mention_count}")
                print(f"  First seen: {entity.first_seen}")
                print(f"  Last seen: {entity.last_seen}")

                # Try to get profile
                try:
                    profile = entity_profile_crud.get_by_entity(session, entity_id=entity_id)
                    if profile and profile.profile_metadata:
                        metadata = profile.profile_metadata
                        if "sentiment_scores" in metadata:
                            avg_sentiment = metadata["sentiment_scores"].get("average", 0)
                            print(f"  Average sentiment: {avg_sentiment:.2f}")
                        if (
                            "framing_categories" in metadata
                            and "history" in metadata["framing_categories"]
                        ):
                            categories = metadata["framing_categories"]["history"]
                            if categories:
                                most_common = max(set(categories), key=categories.count)
                                print(f"  Common framing: {most_common}")
                except Exception as e:
                    error_msg = str(e).split("[SQL:")[0]
                    print(f"  Note: Could not retrieve profile data: {error_msg}")
        except Exception as e:
            print(f"\n- Entity ID {entity_id}")
            print(f"  Error retrieving entity details: {str(e)}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Demo the entity service architecture")
    parser.add_argument("--url", help="URL to process")
    parser.add_argument("--file", help="File containing article content")
    parser.add_argument("--dashboard", action="store_true", help="Show entity dashboard")
    args = parser.parse_args()

    # Set up services
    entity_service, article_service, pipeline_service = setup_services()

    if args.url:
        # Process URL
        process_url(args.url, pipeline_service)

    if args.file:
        # Process file
        try:
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"Error: File not found: {args.file}")
                return

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Use filename as title if not provided
            title = file_path.stem.replace("_", " ").title()
            # Add timestamp to URL to make it unique
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            url = f"file://{file_path.absolute()}?t={timestamp}"

            process_content(content, title, url, article_service)

        except Exception as e:
            print(f"Error processing file: {str(e)}")

    if args.dashboard or (not args.url and not args.file):
        # Show entity dashboard
        get_entity_dashboard(entity_service)


if __name__ == "__main__":
    main()

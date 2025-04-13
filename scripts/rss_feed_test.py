"""
Script to test the RSS parser with a real feed.
"""

import logging
from pathlib import Path

from local_newsifier.tools.rss_parser import RSSParser

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main():
    # Create cache directory if it doesn't exist
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)

    # Initialize parser with cache file
    parser = RSSParser(cache_file=str(cache_dir / "rss_cache.json"))

    # Test with NPR News RSS feed
    feed_url = "https://feeds.npr.org/1001/rss.xml"

    print(f"\nTesting feed: {feed_url}")
    print("-" * 80)

    # Get all items first
    items = parser.parse_feed(feed_url)
    print(f"\nFound {len(items)} total items in feed")

    # Print first 5 items
    for i, item in enumerate(items[:5], 1):
        print(f"\nItem {i}:")
        print(f"Title: {item.title}")
        print(f"URL: {item.url}")
        print(f"Published: {item.published}")
        if item.description:
            print(f"Description: {item.description[:200]}...")

    # Get only new items
    new_items = parser.get_new_urls(feed_url)
    print(f"\nFound {len(new_items)} new items")

    # Try again to demonstrate caching
    new_items = parser.get_new_urls(feed_url)
    print(f"Found {len(new_items)} new items on second try (should be 0)")


if __name__ == "__main__":
    main()

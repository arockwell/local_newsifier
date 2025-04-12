"""
Test script for the new RSS parser implementation.
"""
import logging
from pathlib import Path
from local_newsifier.tools.rss_parser import RSSParser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    # Create cache directory if it doesn't exist
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)
    
    # Initialize parser with cache file
    parser = RSSParser(cache_file=str(cache_dir / "rss_cache.json"))
    
    # Test with public RSS feeds
    test_feeds = [
        "https://news.ycombinator.com/rss",  # Hacker News RSS
        "https://www.reddit.com/r/python/.rss",  # Python subreddit RSS
        "https://www.nasa.gov/feed/"  # NASA RSS
    ]
    
    for feed_url in test_feeds:
        print(f"\nTesting feed: {feed_url}")
        print("=" * 50)
        
        # Get new items from the feed
        items = parser.get_new_urls(feed_url)
        
        if not items:
            print("No new items found in feed")
            continue
            
        print(f"Found {len(items)} new items:")
        for item in items:
            print(f"\nTitle: {item.title}")
            print(f"URL: {item.url}")
            if item.published:
                print(f"Published: {item.published}")
            if item.description:
                print(f"Description: {item.description[:100]}...")
            print("-" * 30)

if __name__ == "__main__":
    main() 
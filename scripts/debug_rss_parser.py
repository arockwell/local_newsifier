#!/usr/bin/env python
"""
Debug script for testing RSS parser functionality.
Run with: python -m scripts.debug_rss_parser
"""

import logging
import json
import sys
from pprint import pprint

# Configure logging to show debug messages
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add parent directory to path so we can import local_newsifier modules
sys.path.insert(0, ".")

# Import RSS parser functionality
from local_newsifier.tools.rss_parser import parse_rss_feed
from local_newsifier.config.logging_config import configure_logging

# Enable detailed logging
configure_logging()
logger = logging.getLogger(__name__)

def test_rss_feed(feed_url):
    """
    Test parsing an RSS feed and display detailed results.
    
    Args:
        feed_url: URL of the RSS feed to test
    """
    logger.info(f"Testing RSS feed: {feed_url}")
    
    try:
        # Parse the feed
        result = parse_rss_feed(feed_url)
        
        # Display basic information
        print("=" * 80)
        print(f"Feed URL: {feed_url}")
        print(f"Feed Title: {result.get('title', 'Unknown')}")
        print(f"Entries Found: {len(result.get('entries', []))}")
        print("=" * 80)
        
        # Display entry information
        if result.get('entries'):
            print("\nEntries (first 5):")
            for i, entry in enumerate(result.get('entries')[:5]):
                print(f"\n--- Entry {i+1} ---")
                print(f"Title: {entry.get('title')}")
                print(f"Link: {entry.get('link')}")
                print(f"Published: {entry.get('published')}")
                print(f"Description: {entry.get('description')[:100]}..." if entry.get('description') else "None")
            
            # Save a sample of the first entry to file
            sample_entry = result.get('entries')[0]
            with open('debug_entry_sample.json', 'w') as f:
                json.dump(sample_entry, f, indent=2)
            print(f"\nSaved first entry sample to debug_entry_sample.json")
        else:
            print("\nNo entries found in the feed.")
            
        # Return the result for further analysis
        return result
    
    except Exception as e:
        logger.exception(f"Error testing RSS feed: {e}")
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    # Test CBS News feed
    cbs_feed = "https://www.cbsnews.com/us/rss/"
    test_rss_feed(cbs_feed)
    
    # Test a known working feed for comparison
    print("\n\nTesting NY Times feed for comparison:")
    nyt_feed = "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"
    test_rss_feed(nyt_feed)

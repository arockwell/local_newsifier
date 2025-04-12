"""
Script to test the RSS scraping flow with a real feed.
"""
import logging
from pathlib import Path
from local_newsifier.flows.rss_scraping_flow import RSSScrapingFlow
from local_newsifier.models.state import AnalysisStatus

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    # Create cache directory if it doesn't exist
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)
    
    # Initialize flow with cache directory
    flow = RSSScrapingFlow(cache_dir=str(cache_dir))
    
    # Test with NPR News RSS feed
    feed_url = "https://feeds.npr.org/1001/rss.xml"
    
    print(f"\nTesting flow with feed: {feed_url}")
    print("-" * 80)
    
    # Process the feed
    states = flow.process_feed(feed_url)
    
    # Print results
    print(f"\nProcessed {len(states)} articles")
    
    # Print summary of results
    success_count = sum(1 for s in states if s.status == AnalysisStatus.SCRAPE_SUCCEEDED)
    failed_count = sum(1 for s in states if s.status == AnalysisStatus.SCRAPE_FAILED_NETWORK)
    
    print(f"\nSummary:")
    print(f"Successfully scraped: {success_count}")
    print(f"Failed to scrape: {failed_count}")
    
    # Print details of first 3 articles
    print("\nFirst 3 articles:")
    for i, state in enumerate(states[:3], 1):
        print(f"\nArticle {i}:")
        print(f"URL: {state.target_url}")
        print(f"Status: {state.status}")
        if state.scraped_text:
            print(f"Content preview: {state.scraped_text[:200]}...")
        if state.error_details:
            print(f"Error: {state.error_details.message}")

if __name__ == "__main__":
    main() 
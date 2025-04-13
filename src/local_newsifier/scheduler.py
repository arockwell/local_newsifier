import schedule
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from .flows.news_pipeline import NewsPipelineFlow
from .models.state import AnalysisStatus

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scheduler.log")
    ]
)
logger = logging.getLogger(__name__)

class NewsScheduler:
    """Scheduler for running news analysis tasks."""
    
    def __init__(self, output_dir: str = "output"):
        """Initialize the scheduler."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.pipeline = NewsPipelineFlow(output_dir=str(self.output_dir))
        
        # Define news sources
        self.sources = [
            {
                "url": "https://www.gainesville.com/news/",
                "type": "web",
                "name": "Gainesville Sun"
            },
            {
                "url": "https://www.wuft.org/news/feed/",
                "type": "rss",
                "name": "WUFT News"
            }
        ]
    
    def fetch_news(self) -> None:
        """Fetch and analyze news from all sources."""
        logger.info("Starting news fetch cycle")
        
        for source in self.sources:
            try:
                logger.info(f"Processing {source['name']} ({source['url']})")
                state = self.pipeline.start_pipeline(url=source['url'])
                
                if state.status == AnalysisStatus.COMPLETED_SUCCESS:
                    logger.info(f"Successfully processed {source['name']}")
                else:
                    logger.error(f"Failed to process {source['name']}: {state.status}")
                    if state.error_details:
                        logger.error(f"Error: {state.error_details.message}")
            
            except Exception as e:
                logger.error(f"Error processing {source['name']}: {str(e)}")
        
        logger.info("Completed news fetch cycle")
    
    def run(self, interval_minutes: int = 60) -> None:
        """
        Run the scheduler.
        
        Args:
            interval_minutes: How often to run the fetch cycle (in minutes)
        """
        logger.info(f"Starting scheduler with {interval_minutes} minute interval")
        
        # Schedule the job
        schedule.every(interval_minutes).minutes.do(self.fetch_news)
        
        # Run immediately on startup
        self.fetch_news()
        
        # Keep the scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def main():
    """Main entry point."""
    scheduler = NewsScheduler()
    scheduler.run()

if __name__ == "__main__":
    main() 
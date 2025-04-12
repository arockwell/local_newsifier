"""Tests for the web scraper tool."""

import pytest
from bs4 import BeautifulSoup

from local_newsifier.tools.web_scraper import WebScraperTool


@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return """
    <html>
        <body>
            <article>
                <p>John Smith visited Gainesville, Florida yesterday.</p>
                <p>He met with representatives from the University of Florida.</p>
            </article>
        </body>
    </html>
    """


def test_web_scraper_extract_article(sample_html):
    """Test article text extraction."""
    scraper = WebScraperTool()
    text = scraper.extract_article_text(sample_html)
    
    assert "John Smith" in text
    assert "Gainesville, Florida" in text
    assert "University of Florida" in text 
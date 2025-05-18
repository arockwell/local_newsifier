"""Tests for the article preprocessing module."""

import pytest
from datetime import datetime
from bs4 import BeautifulSoup

from local_newsifier.tools.preprocessing.content_cleaner import ContentCleaner
from local_newsifier.tools.preprocessing.content_extractor import ContentExtractor
from local_newsifier.tools.preprocessing.metadata_enhancer import MetadataEnhancer
from local_newsifier.tools.preprocessing.article_preprocessor import ArticlePreprocessor


class TestContentCleaner:
    """Tests for the ContentCleaner class."""
    
    def test_handle_special_characters(self):
        """Test handling of special characters in content."""
        cleaner = ContentCleaner()
        
        # Test HTML entities
        content = "This &amp; that &lt;tag&gt; with &quot;quotes&quot;"
        result = cleaner._handle_special_characters(content)
        assert "&amp;" not in result
        assert "&lt;" not in result
        assert "&gt;" not in result
        assert "&quot;" not in result
        assert "This & that <tag> with \"quotes\"" == result
        
        # Test smart quotes
        content = "These \"smart quotes\" and 'apostrophes' should be normalized"
        result = cleaner._handle_special_characters(content)
        assert "These \"smart quotes\" and 'apostrophes' should be normalized" == result
        
        # Test dashes and other special characters
        content = "This–that and—other…things"
        result = cleaner._handle_special_characters(content)
        assert "This-that and-other...things" == result
    
    def test_normalize_whitespace(self):
        """Test normalization of whitespace in content."""
        cleaner = ContentCleaner()
        
        # Test multiple spaces
        content = "This    has    too    many    spaces"
        result = cleaner._normalize_whitespace(content)
        assert "This has too many spaces" == result
        
        # Test tabs and newlines - in the implementation, all whitespace is converted to spaces first
        content = "This\thas\ttabs\nand\nnewlines"
        result = cleaner._normalize_whitespace(content)
        assert "This has tabs and newlines" == result
        
        # Update test for paragraph identification
        paragraphs = ["First paragraph", "Second paragraph", "Third paragraph"]
        content = "First paragraph<p>Second paragraph</p><div>Third paragraph</div>"
        result = cleaner._normalize_whitespace(content)
        for p in paragraphs:
            assert p in result
    
    def test_remove_boilerplate(self):
        """Test removal of boilerplate text from content."""
        cleaner = ContentCleaner()
        
        # Create test content with longer paragraphs (to pass min length check)
        content = """
        This is the real article content with enough text to not be filtered out by length checks.
        
        Subscribe to our newsletter for more updates.
        
        More article content here with enough text to pass the minimum length threshold.
        
        Follow us on Twitter and Facebook for the latest updates and news.
        
        Final content paragraph with substantial length to ensure it passes filtering.
        """
        
        # Normalize the text first (as the implementation would)
        normalized_content = cleaner._normalize_whitespace(content)
        
        # Now test boilerplate removal
        result = cleaner._remove_boilerplate(normalized_content)
        
        # Verify boilerplate removal
        assert "Subscribe to our newsletter" not in result
        assert "Follow us on Twitter" not in result
        
        # Verify important content is kept
        assert "This is the real article content" in result
        assert "More article content here" in result 
        assert "Final content paragraph" in result
    
    def test_remove_duplicate_paragraphs(self):
        """Test removal of duplicate paragraphs from content."""
        cleaner = ContentCleaner()
        
        # Create test content with normalized paragraphs
        content = "First paragraph.\n\nSecond paragraph.\n\nFirst paragraph.\n\nThird paragraph."
        
        # The implementation expects normalized input
        result = cleaner._remove_duplicate_paragraphs(content)
        
        # Verify duplicates are removed
        paragraphs = result.split("\n\n")
        first_para_count = sum(1 for p in paragraphs if p.lower().startswith("first paragraph"))
        assert first_para_count == 1
        assert any("Second paragraph" in p for p in paragraphs)
        assert any("Third paragraph" in p for p in paragraphs)
        
        # Test case-insensitive duplicates
        content = "First paragraph.\n\nFIRST PARAGRAPH.\n\nSecond paragraph."
        
        result = cleaner._remove_duplicate_paragraphs(content)
        paragraphs = result.split("\n\n")
        
        # Should only keep the first instance
        assert any("First paragraph" in p for p in paragraphs)
        assert not any("FIRST PARAGRAPH" in p for p in paragraphs)
        assert any("Second paragraph" in p for p in paragraphs)
    
    def test_clean_content_full(self):
        """Test the full content cleaning process."""
        cleaner = ContentCleaner()
        
        # Create test content with longer paragraphs to pass length filtering
        content = """
        This is &amp; the main article content with enough length to not be filtered out.
        
        This   has   too   many   spaces but also has sufficient length to be preserved.
        
        Subscribe to our newsletter for more updates and articles like this one!
        
        "Smart quotes" need to be normalized and this paragraph is long enough to be kept.
        
        This is &amp; the main article content with enough length to not be filtered out.
        
        Follow us on Twitter for updates and the latest news from our team.
        """
        
        result = cleaner.clean_content(content)
        
        # Verify results (checking for substrings since the actual output may vary)
        
        # Should handle special characters
        assert "&amp;" not in result
        assert "This is & the main article content" in result
        
        # Should normalize whitespace 
        assert "too   many   spaces" not in result
        assert "too many spaces" in result
        
        # Should remove boilerplate
        assert "Subscribe to our newsletter" not in result
        assert "Follow us on Twitter" not in result
        
        # Should remove duplicates
        occurrences = result.count("This is & the main article content")
        assert occurrences == 1
        
        # Should normalize quotes
        assert "Smart quotes" in result


class TestContentExtractor:
    """Tests for the ContentExtractor class."""
    
    def test_extract_title(self):
        """Test extraction of article title from HTML."""
        extractor = ContentExtractor()
        
        html = """
        <html>
            <head>
                <title>Page Title</title>
                <meta property="og:title" content="OG Title" />
            </head>
            <body>
                <h1 class="article-title">Article Headline</h1>
                <article>
                    <p>Content</p>
                </article>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Should prefer h1 with article-title class
        title = extractor._extract_title(soup)
        assert title == "Article Headline"
        
        # Test fallback to meta tags when h1 not available
        html = """
        <html>
            <head>
                <title>Page Title</title>
                <meta property="og:title" content="OG Title" />
            </head>
            <body>
                <article>
                    <p>Content</p>
                </article>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, "html.parser")
        title = extractor._extract_title(soup)
        assert title == "OG Title"
    
    def test_find_content_container(self):
        """Test finding the main content container in HTML."""
        extractor = ContentExtractor()
        
        # Test finding article tag with content class
        html = """
        <html>
            <body>
                <header>Header</header>
                <article class="content">
                    <p>Article content here</p>
                </article>
                <aside>Sidebar</aside>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, "html.parser")
        container = extractor._find_content_container(soup)
        assert container is not None
        assert container.name == "article"
        assert "content" in container.get("class", [])
        
        # Test finding div with articleBody attribute
        html = """
        <html>
            <body>
                <header>Header</header>
                <div itemprop="articleBody">
                    <p>Article content here</p>
                </div>
                <aside>Sidebar</aside>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, "html.parser")
        container = extractor._find_content_container(soup)
        assert container is not None
        assert container.name == "div"
        assert container.get("itemprop") == "articleBody"
        
        # Test finding article with most paragraphs
        html = """
        <html>
            <body>
                <article>
                    <p>One paragraph</p>
                </article>
                <article>
                    <p>First paragraph</p>
                    <p>Second paragraph</p>
                    <p>Third paragraph</p>
                </article>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, "html.parser")
        container = extractor._find_content_container(soup)
        assert container is not None
        assert container.name == "article"
        assert len(container.find_all("p")) == 3
    
    def test_extract_content_full(self):
        """Test the full content extraction process."""
        extractor = ContentExtractor()
        
        html = """
        <html>
            <head>
                <title>Test Article</title>
            </head>
            <body>
                <header>
                    <h1 class="headline">Article Headline</h1>
                    <div class="metadata">Published on Jan 1, 2023</div>
                </header>
                <article class="content">
                    <p>First paragraph of content.</p>
                    <p>Second paragraph with <a href="https://example.com">a link</a>.</p>
                    <figure>
                        <img src="image.jpg" alt="Test image" />
                        <figcaption>Image caption</figcaption>
                    </figure>
                    <ul>
                        <li>List item 1</li>
                        <li>List item 2</li>
                    </ul>
                    <blockquote>
                        <p>This is a quote</p>
                        <cite>Quote attribution</cite>
                    </blockquote>
                    <div class="related-content">
                        <h3>Related Articles</h3>
                        <ul>
                            <li><a href="#">Related article 1</a></li>
                        </ul>
                    </div>
                </article>
                <footer>Footer content</footer>
            </body>
        </html>
        """
        
        result = extractor.extract_content(html)
        
        # Check basic extraction
        assert result["title"] == "Article Headline"
        assert "First paragraph of content" in result["text"]
        assert "Second paragraph" in result["text"]
        
        # Check image extraction
        assert "images" in result
        assert len(result["images"]) == 1
        assert result["images"][0]["src"] == "image.jpg"
        assert result["images"][0]["caption"] == "Image caption"
        
        # Check link extraction
        assert "links" in result
        assert len(result["links"]) >= 1
        assert any(link["url"] == "https://example.com" for link in result["links"])
        
        # Check list extraction
        assert "lists" in result
        assert len(result["lists"]) == 1
        assert result["lists"][0]["type"] == "unordered"
        assert "List item 1" in result["lists"][0]["items"]
        
        # Check quote extraction
        assert "quotes" in result
        assert len(result["quotes"]) == 1
        assert "This is a quote" in result["quotes"][0]["text"]
        assert "Quote attribution" in result["quotes"][0]["attribution"]
        
        # Check that related content is removed
        assert "Related Articles" not in result["text"]


class TestMetadataEnhancer:
    """Tests for the MetadataEnhancer class."""
    
    def test_extract_publication_date(self):
        """Test extraction of publication date from various sources."""
        enhancer = MetadataEnhancer()
        
        # Test extraction from HTML metadata
        html = """
        <html>
            <head>
                <meta property="article:published_time" content="2023-01-15T12:30:45Z" />
            </head>
            <body>
                <article>
                    <p>Content published on January 15, 2023</p>
                </article>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, "html.parser")
        date = enhancer._extract_publication_date(
            content="Content published on January 15, 2023",
            soup=soup,
            url=None,
            existing_date=None
        )
        
        assert date is not None
        assert date.year == 2023
        assert date.month == 1
        assert date.day == 15
        
        # Test extraction from content text
        content = "Published on January 15, 2023 - This is an article"
        date = enhancer._extract_publication_date(
            content=content,
            soup=None,
            url=None,
            existing_date=None
        )
        
        assert date is not None
        assert date.year == 2023
        assert date.month == 1
        assert date.day == 15
        
        # Test extraction from URL
        url = "https://example.com/2023/01/15/article-title.html"
        date = enhancer._extract_publication_date(
            content="",
            soup=None,
            url=url,
            existing_date=None
        )
        
        assert date is not None
        assert date.year == 2023
        assert date.month == 1
        assert date.day == 15
    
    def test_extract_categories(self):
        """Test extraction of content categories from various sources."""
        enhancer = MetadataEnhancer()
        
        # Test extraction from HTML metadata
        html = """
        <html>
            <head>
                <meta property="article:section" content="Politics" />
                <meta name="keywords" content="election, government, policy" />
            </head>
            <body>
                <article>
                    <p>Political content here</p>
                </article>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, "html.parser")
        categories = enhancer._extract_categories(
            content="Political content about elections and government.",
            soup=soup,
            url="https://example.com/politics/article.html"
        )
        
        assert "Politics" in categories
        assert "election" in categories or "government" in categories or "policy" in categories
        
        # Test extraction from URL
        categories = enhancer._extract_categories(
            content="Sports content about football.",
            soup=None,
            url="https://example.com/sports/football/article.html"
        )
        
        assert "sports" in categories
    
    def test_enhance_metadata_full(self):
        """Test the full metadata enhancement process."""
        enhancer = MetadataEnhancer()
        
        content = """
        Published on January 15, 2023
        
        This is an article about politics and elections in the United States.
        The government announced new policies yesterday in Washington DC.
        """
        
        html = """
        <html>
            <head>
                <title>Politics Article</title>
                <meta property="og:title" content="Election Results" />
                <meta property="article:published_time" content="2023-01-15T12:30:45Z" />
                <meta property="article:section" content="Politics" />
            </head>
            <body>
                <article>
                    <h1>Election Results Announced</h1>
                    <p>Published on January 15, 2023</p>
                    <p>This is an article about politics and elections in the United States.</p>
                    <p>The government announced new policies yesterday in Washington DC.</p>
                </article>
            </body>
        </html>
        """
        
        url = "https://example.com/politics/2023/01/15/election-results.html"
        
        result = enhancer.enhance_metadata(
            content=content,
            html_content=html,
            url=url,
            existing_metadata={"title": "Election Results"}
        )
        
        # Check that publication date was extracted
        assert "published_at" in result
        assert result["published_at"].year == 2023
        assert result["published_at"].month == 1
        assert result["published_at"].day == 15
        
        # Check that categories were extracted
        assert "categories" in result
        assert "politics" in result["categories"] or "Politics" in result["categories"]
        
        # Check that source was extracted from URL
        assert "source" in result
        assert result["source"] == "example.com"
        
        # Check that word count was added
        assert "word_count" in result
        assert result["word_count"] > 0


class TestArticlePreprocessor:
    """Tests for the ArticlePreprocessor service."""
    
    def test_preprocess(self):
        """Test the full article preprocessing process."""
        # Create mock component instances
        cleaner = ContentCleaner()
        extractor = ContentExtractor()
        enhancer = MetadataEnhancer()
        
        preprocessor = ArticlePreprocessor(
            content_cleaner=cleaner,
            content_extractor=extractor,
            metadata_enhancer=enhancer
        )
        
        html = """
        <html>
            <head>
                <title>Test Article</title>
                <meta property="article:published_time" content="2023-01-15T12:30:45Z" />
                <meta property="article:section" content="Technology" />
            </head>
            <body>
                <article class="content">
                    <h1>Article Headline</h1>
                    <div class="metadata">Published on January 15, 2023</div>
                    <p>First paragraph of content.</p>
                    <p>Second paragraph with a link.</p>
                    <p>Subscribe to our newsletter for more updates!</p>
                    <div class="related-content">Related articles</div>
                </article>
                <footer>Footer content</footer>
            </body>
        </html>
        """
        
        content = """
        First paragraph of content.
        
        Second paragraph with a link.
        
        Subscribe to our newsletter for more updates!
        """
        
        url = "https://example.com/technology/2023/01/15/article-headline.html"
        
        result = preprocessor.preprocess(
            content=content,
            html_content=html,
            url=url,
            metadata={"title": "Article Headline"}
        )
        
        # Check that content was cleaned
        assert "First paragraph of content" in result["content"]
        assert "Second paragraph with a link" in result["content"]
        assert "Subscribe to our newsletter" not in result["content"]
        
        # Check that metadata was enhanced
        assert "metadata" in result
        assert result["metadata"]["title"] == "Article Headline"
        assert "published_at" in result["metadata"]
        assert "categories" in result["metadata"]
        assert "Technology" in result["metadata"]["categories"] or "technology" in result["metadata"]["categories"]
        assert result["metadata"]["source"] == "example.com"
        
        # Check that structures were extracted
        assert "structures" in result
        assert "title" in result["structures"]
        assert "html" in result["structures"]
    
    def test_preprocess_article_data(self):
        """Test preprocessing of article data in dictionary format."""
        # Create the preprocessor with mock components
        preprocessor = ArticlePreprocessor()
        
        article_data = {
            "title": "Article Headline",
            "content": "Article content with some boilerplate. Subscribe to our newsletter!",
            "url": "https://example.com/article.html",
            "published_at": datetime(2023, 1, 15, 12, 30, 45)
        }
        
        html = """
        <html>
            <body>
                <article>
                    <h1>Article Headline</h1>
                    <p>Article content with some boilerplate.</p>
                    <p>Subscribe to our newsletter!</p>
                </article>
            </body>
        </html>
        """
        
        result = preprocessor.preprocess_article_data(
            article_data=article_data,
            html_content=html
        )
        
        # Check that content was cleaned
        assert "Article content with some boilerplate" in result["content"]
        assert "Subscribe to our newsletter" not in result["content"]
        
        # Check that original metadata was preserved
        assert result["title"] == "Article Headline"
        assert result["published_at"] == article_data["published_at"]
        assert result["url"] == "https://example.com/article.html"
        
        # Check that source was added
        assert "source" in result
        assert result["source"] == "example.com"
        
        # Check that structures were added
        assert "structures" in result
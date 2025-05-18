"""
Metadata enhancement utilities for article preprocessing.

This module provides functions to extract and enhance article metadata,
including publication date, categories, locations, and language.
"""

import re
import datetime
from typing import List, Dict, Any, Optional, Tuple, Set
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# Try to import spacy for NLP-based metadata enhancement
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False


class MetadataEnhancer:
    """Tool for enhancing article metadata."""
    
    def __init__(
        self,
        extract_date: bool = True,
        extract_categories: bool = True,
        extract_locations: bool = True,
        detect_language: bool = True,
        spacy_model: Optional[str] = "en_core_web_sm",
    ):
        """Initialize the metadata enhancer with configurable options.
        
        Args:
            extract_date: Whether to extract publication date
            extract_categories: Whether to extract content categories
            extract_locations: Whether to extract mentioned locations
            detect_language: Whether to detect content language
            spacy_model: Name of spaCy model to use (None for no NLP)
        """
        self.extract_date = extract_date
        self.extract_categories = extract_categories
        self.extract_locations = extract_locations
        self.detect_language = detect_language
        
        # Initialize NLP model if requested and available
        self.nlp = None
        if SPACY_AVAILABLE and spacy_model:
            try:
                self.nlp = spacy.load(spacy_model)
            except (OSError, IOError):
                pass
    
    def enhance_metadata(
        self, 
        content: str,
        html_content: Optional[str] = None,
        url: Optional[str] = None,
        existing_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Enhance article metadata using all configured operations.
        
        Args:
            content: Plain text article content
            html_content: Optional HTML content for better extraction
            url: Optional article URL for additional context
            existing_metadata: Optional existing metadata to enhance
            
        Returns:
            Dictionary with enhanced metadata
        """
        metadata = existing_metadata or {}
        
        # Create BeautifulSoup object if HTML content is provided
        soup = BeautifulSoup(html_content, "html.parser") if html_content else None
        
        # Apply each metadata enhancement if enabled
        if self.extract_date:
            publication_date = self._extract_publication_date(content, soup, url, metadata.get("published_at"))
            if publication_date:
                metadata["published_at"] = publication_date
        
        if self.extract_categories and content:
            categories = self._extract_categories(content, soup, url)
            if categories:
                metadata["categories"] = categories
        
        if self.extract_locations and content and self.nlp:
            locations = self._extract_locations(content)
            if locations:
                metadata["locations"] = locations
        
        if self.detect_language and content:
            language = self._detect_language(content)
            if language:
                metadata["language"] = language
        
        # Extract source domain from URL if not already in metadata
        if url and not metadata.get("source"):
            parsed_url = urlparse(url)
            if parsed_url.netloc:
                metadata["source"] = parsed_url.netloc
        
        # Extract word count if content is available
        if content:
            metadata["word_count"] = len(content.split())
        
        return metadata
    
    def _extract_publication_date(
        self, 
        content: str,
        soup: Optional[BeautifulSoup],
        url: Optional[str],
        existing_date: Optional[datetime.datetime]
    ) -> Optional[datetime.datetime]:
        """Extract publication date from article content or metadata.
        
        Args:
            content: Plain text article content
            soup: BeautifulSoup object of HTML content (or None)
            url: Article URL (or None)
            existing_date: Existing publication date (or None)
            
        Returns:
            Extracted publication date or None if not found
        """
        # Return existing date if provided
        if existing_date:
            return existing_date
        
        # Try to extract from HTML metadata if available
        if soup:
            # Check standard meta tags
            meta_dates = []
            
            for meta in soup.find_all("meta"):
                if meta.get("property") in ["article:published_time", "og:published_time", "publication_date"]:
                    date_str = meta.get("content")
                    if date_str:
                        try:
                            from dateutil.parser import parse
                            return parse(date_str)
                        except (ImportError, ValueError):
                            pass
                
                if meta.get("name") in ["pubdate", "date", "DC.date", "DC.Date.Issued"]:
                    date_str = meta.get("content")
                    if date_str:
                        try:
                            from dateutil.parser import parse
                            return parse(date_str)
                        except (ImportError, ValueError):
                            pass
            
            # Check for time tag with datetime attribute
            time_tags = soup.find_all("time")
            for time_tag in time_tags:
                date_str = time_tag.get("datetime")
                if date_str:
                    try:
                        from dateutil.parser import parse
                        return parse(date_str)
                    except (ImportError, ValueError):
                        pass
            
            # Check for structured data
            ld_json = soup.find("script", {"type": "application/ld+json"})
            if ld_json:
                try:
                    import json
                    data = json.loads(ld_json.string)
                    if isinstance(data, dict):
                        date_str = data.get("datePublished") or data.get("dateModified")
                        if date_str:
                            from dateutil.parser import parse
                            return parse(date_str)
                except (ImportError, ValueError, AttributeError, json.JSONDecodeError):
                    pass
        
        # Try to extract from text content
        date_patterns = [
            # Common date formats
            r"(?:Published|Posted|Updated)(?:\s+on)?\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})",
            r"(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})",
            r"(\d{1,2}/\d{1,2}/\d{2,4})",
            r"(\d{4}-\d{1,2}-\d{1,2})",
            r"(\d{1,2}-\d{1,2}-\d{4})",
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content)
            if match:
                date_str = match.group(1)
                try:
                    from dateutil.parser import parse
                    return parse(date_str)
                except (ImportError, ValueError):
                    continue
        
        # Try to extract from URL if available
        if url:
            # Look for date patterns in URL (e.g., /2023/05/25/)
            url_date_pattern = r"/(\d{4})/(\d{1,2})/(\d{1,2})/"
            match = re.search(url_date_pattern, url)
            if match:
                year, month, day = map(int, match.groups())
                try:
                    return datetime.datetime(year, month, day)
                except ValueError:
                    pass
        
        # Default to current date if all extraction attempts fail
        return datetime.datetime.now()
    
    def _extract_categories(
        self, 
        content: str,
        soup: Optional[BeautifulSoup],
        url: Optional[str]
    ) -> List[str]:
        """Extract content categories from article content or metadata.
        
        Args:
            content: Plain text article content
            soup: BeautifulSoup object of HTML content (or None)
            url: Article URL (or None)
            
        Returns:
            List of extracted categories
        """
        categories = set()
        
        # Try to extract from HTML metadata if available
        if soup:
            # Check article category tags
            for meta in soup.find_all("meta"):
                if meta.get("property") in ["article:section", "article:tag"]:
                    categories.add(meta.get("content", "").strip())
                
                if meta.get("name") in ["keywords", "news_keywords", "categories"]:
                    keywords = meta.get("content", "").split(",")
                    categories.update([k.strip() for k in keywords if k.strip()])
            
            # Check for category links/breadcrumbs
            for a in soup.find_all("a", class_=lambda x: x and any(
                term in x.lower() for term in ["category", "section", "channel", "topic"]
            )):
                categories.add(a.get_text().strip())
        
        # Try to extract from URL if available
        if url:
            # Look for category segments in URL
            url_parts = urlparse(url).path.split("/")
            common_categories = [
                "news", "politics", "business", "tech", "technology", "sports",
                "entertainment", "lifestyle", "health", "science", "opinion",
                "weather", "world", "us", "usa", "education", "travel"
            ]
            
            for part in url_parts:
                if part.lower() in common_categories:
                    categories.add(part.lower())
        
        # Use NLP-based topic extraction for more categories
        if content and self.nlp and len(categories) < 3:
            # Use text classification if available in the model
            if hasattr(self.nlp, "pipe_names") and "textcat" in self.nlp.pipe_names:
                doc = self.nlp(content[:1000])  # Analyze first 1000 chars for efficiency
                for cat, score in doc.cats.items():
                    if score > 0.6:  # Only include high-confidence categories
                        categories.add(cat)
            
            # Fallback: extract key noun phrases as topics
            if len(categories) < 2:
                common_topics = {
                    "pandemic": "health",
                    "covid": "health",
                    "virus": "health",
                    "vaccine": "health",
                    "election": "politics",
                    "president": "politics",
                    "congress": "politics",
                    "economy": "business",
                    "market": "business",
                    "stock": "business",
                    "climate": "environment",
                    "weather": "environment",
                    "phone": "technology",
                    "app": "technology",
                    "software": "technology",
                    "game": "entertainment",
                    "movie": "entertainment",
                    "music": "entertainment",
                    "sport": "sports",
                    "player": "sports",
                    "team": "sports",
                }
                
                for topic, category in common_topics.items():
                    if topic in content.lower() and category not in categories:
                        categories.add(category)
        
        return list(categories)
    
    def _extract_locations(self, content: str) -> List[Dict[str, str]]:
        """Extract locations mentioned in the article content.
        
        Args:
            content: Plain text article content
            
        Returns:
            List of dictionaries with location information:
            - name: location name
            - type: location type (city, country, etc.) if available
        """
        if not self.nlp:
            return []
        
        locations = []
        seen_locations = set()
        
        # Process with NLP to extract named entities
        doc = self.nlp(content[:5000])  # Limit to first 5000 chars for performance
        
        # Extract location entities
        for ent in doc.ents:
            if ent.label_ in ["GPE", "LOC", "FAC"]:
                location_name = ent.text.strip()
                
                # Skip very short locations (likely errors)
                if len(location_name) < 3:
                    continue
                
                # Skip duplicates
                if location_name.lower() in seen_locations:
                    continue
                
                seen_locations.add(location_name.lower())
                
                # Determine location type
                location_type = "location"
                if ent.label_ == "GPE":
                    location_type = "city" if len(location_name.split()) == 1 else "country"
                elif ent.label_ == "LOC":
                    location_type = "geographic"
                elif ent.label_ == "FAC":
                    location_type = "facility"
                
                locations.append({
                    "name": location_name,
                    "type": location_type
                })
        
        return locations
    
    def _detect_language(self, content: str) -> Optional[str]:
        """Detect the language of the article content.
        
        Args:
            content: Plain text article content
            
        Returns:
            ISO language code or None if detection fails
        """
        # Try using spaCy for language detection if available
        if self.nlp and hasattr(self.nlp, "lang"):
            return self.nlp.lang
        
        # Try using langdetect if available
        try:
            from langdetect import detect
            return detect(content)
        except ImportError:
            pass
        
        # Simple heuristic for English vs. non-English
        # Count common English words
        english_words = {"the", "and", "is", "in", "to", "of", "that", "for", "it", "with"}
        content_words = set(re.findall(r'\b\w+\b', content.lower()))
        
        if len(content_words.intersection(english_words)) >= 4:
            return "en"
        
        # Default to unknown
        return None
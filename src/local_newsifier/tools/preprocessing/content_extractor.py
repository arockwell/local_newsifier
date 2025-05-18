"""
Content extraction utilities for article preprocessing.

This module provides functions to extract the main content from HTML,
identify important structural elements, and format special content types.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup


class ContentExtractor:
    """Tool for extracting and structuring article content from HTML."""
    
    def __init__(
        self,
        extract_images: bool = True,
        extract_links: bool = True,
        preserve_formatting: bool = True,
        extract_lists: bool = True,
        extract_quotes: bool = True,
    ):
        """Initialize the content extractor with configurable options.
        
        Args:
            extract_images: Whether to extract image information
            extract_links: Whether to extract link information
            preserve_formatting: Whether to preserve formatting like bold, italic
            extract_lists: Whether to extract and format lists
            extract_quotes: Whether to extract and format quotes
        """
        self.extract_images = extract_images
        self.extract_links = extract_links
        self.preserve_formatting = preserve_formatting
        self.extract_lists = extract_lists
        self.extract_quotes = extract_quotes
    
    def extract_content(self, html_content: str) -> Dict[str, Any]:
        """Extract and structure content from HTML.
        
        Args:
            html_content: The HTML content to process
            
        Returns:
            Dictionary containing extracted content and metadata:
            - title: article title
            - text: main text content
            - html: structured HTML content
            - images: list of image information (if extract_images is True)
            - links: list of link information (if extract_links is True)
            - lists: list of extracted lists (if extract_lists is True)
            - quotes: list of extracted quotes (if extract_quotes is True)
        """
        if not html_content:
            return {"text": "", "html": "", "title": ""}
        
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Extract title
        title = self._extract_title(soup)
        
        # Find the main content container
        content_container = self._find_content_container(soup)
        
        # Clean up the content container
        if content_container:
            self._clean_content_container(content_container)
        
        # Extract structured content
        result = {
            "title": title,
            "text": self._extract_text(content_container) if content_container else "",
            "html": str(content_container) if content_container else "",
        }
        
        # Extract additional elements if configured
        if self.extract_images and content_container:
            result["images"] = self._extract_images(content_container)
            
        if self.extract_links and content_container:
            result["links"] = self._extract_links(content_container)
            
        if self.extract_lists and content_container:
            result["lists"] = self._extract_lists(content_container)
            
        if self.extract_quotes and content_container:
            result["quotes"] = self._extract_quotes(content_container)
            
        return result
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the article title from HTML.
        
        Args:
            soup: BeautifulSoup object of the HTML content
            
        Returns:
            Article title or empty string if not found
        """
        # Check various title candidates in order of preference
        candidates = [
            soup.find("h1", class_=lambda x: x and any(term in x.lower() for term in ["headline", "title", "article-title"])),
            soup.find("h1", itemprop="headline"),
            soup.find("h1", property="og:title"),
            soup.find("h1"),
            soup.find("meta", property="og:title"),
            soup.find("meta", attrs={"name": "twitter:title"}),
            soup.find("title")
        ]
        
        for candidate in candidates:
            if candidate:
                if candidate.name in ["meta", "title"]:
                    # For meta tags, use the content attribute
                    return candidate.get("content", "").strip()
                else:
                    # For heading tags, use the text content
                    return candidate.get_text().strip()
        
        return ""
    
    def _find_content_container(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Find the main content container in the HTML.
        
        This function uses multiple strategies to identify the main
        article content container.
        
        Args:
            soup: BeautifulSoup object of the HTML content
            
        Returns:
            BeautifulSoup object of the main content container or None if not found
        """
        # Strategy 1: Look for article tag with content-related class
        content = soup.find(
            "article", 
            class_=lambda x: x and any(term in x.lower() for term in ["content", "story", "article", "post"])
        )
        if content:
            return content
        
        # Strategy 2: Look for div with article-specific attributes
        content = soup.find(
            "div", 
            attrs={
                "itemprop": "articleBody"
            }
        ) or soup.find(
            "div", 
            attrs={
                "class": lambda x: x and any(term in x.lower() for term in ["article-body", "story-body", "content-body", "entry-content", "post-content"])
            }
        )
        if content:
            return content
        
        # Strategy 3: Look for the article tag with the most paragraphs
        articles = soup.find_all("article")
        if articles:
            return max(articles, key=lambda x: len(x.find_all("p")))
        
        # Strategy 4: Look for main tag
        main = soup.find("main")
        if main:
            return main
        
        # Strategy 5: Look for div with most paragraphs and reasonable structure
        divs = [
            div for div in soup.find_all("div") 
            if len(div.find_all("p")) > 3 and not div.find("div", recursive=False)
        ]
        
        if divs:
            return max(divs, key=lambda x: len(x.find_all("p")))
        
        return None
    
    def _clean_content_container(self, container: BeautifulSoup) -> None:
        """Clean up the content container by removing non-content elements.
        
        Args:
            container: BeautifulSoup object of the content container
        """
        # Remove navigation, sidebar, footer, etc.
        for element in container.find_all(["nav", "aside", "footer", "header"]):
            element.decompose()
        
        # Remove elements with non-content classes
        for element in container.find_all(class_=lambda x: x and any(
            term in x.lower() for term in [
                "comment", "share", "social", "related", "sidebar", "widget",
                "promo", "advertisement", "banner", "sponsor", "recommended", 
                "newsletter", "subscription", "toolbar", "menu", "nav", "footer"
            ]
        )):
            element.decompose()
        
        # Remove script and style tags
        for element in container.find_all(["script", "style", "iframe", "noscript"]):
            element.decompose()
    
    def _extract_text(self, container: BeautifulSoup) -> str:
        """Extract plain text from the content container.
        
        Args:
            container: BeautifulSoup object of the content container
            
        Returns:
            Plain text content
        """
        if not container:
            return ""
        
        # Get all text blocks that look like article content
        paragraphs = []
        
        for element in container.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li"]):
            text = element.get_text().strip()
            
            # Skip empty or very short blocks
            if len(text) < 5:
                continue
                
            # Skip blocks that look like navigation/metadata
            if any(term in text.lower() for term in [
                "share", "subscribe", "follow us", "related", "comment",
                "copyright", "all rights reserved", "published on"
            ]):
                continue
                
            # Format based on tag type
            if element.name.startswith("h") and len(text) > 0:
                # Add blank line before headings and make them stand out
                if paragraphs:  # Only add extra line if not the first element
                    paragraphs.append("")
                paragraphs.append(text)
                paragraphs.append("")  # Line after heading
            elif element.name == "li":
                # Format list items
                paragraphs.append(f"• {text}")
            else:
                paragraphs.append(text)
        
        return "\n".join(paragraphs)
    
    def _extract_images(self, container: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract image information from the content container.
        
        Args:
            container: BeautifulSoup object of the content container
            
        Returns:
            List of dictionaries containing image information:
            - src: image source URL
            - alt: alternative text
            - caption: image caption if available
        """
        images = []
        
        for img in container.find_all("img"):
            src = img.get("src", "")
            if not src:
                src = img.get("data-src", "")
            
            if src:
                # Try to find caption
                caption = ""
                
                # Look for caption in figcaption
                fig_parent = img.find_parent("figure")
                if fig_parent:
                    figcaption = fig_parent.find("figcaption")
                    if figcaption:
                        caption = figcaption.get_text().strip()
                
                # Look for caption in nearby elements
                if not caption:
                    next_sibling = img.next_sibling
                    if next_sibling and hasattr(next_sibling, "name") and next_sibling.name == "p":
                        if len(next_sibling.get_text()) < 150:  # Likely a caption if short
                            caption = next_sibling.get_text().strip()
                
                images.append({
                    "src": src,
                    "alt": img.get("alt", ""),
                    "caption": caption
                })
        
        return images
    
    def _extract_links(self, container: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract link information from the content container.
        
        Args:
            container: BeautifulSoup object of the content container
            
        Returns:
            List of dictionaries containing link information:
            - url: link URL
            - text: link text
            - title: link title if available
        """
        links = []
        
        for a in container.find_all("a"):
            url = a.get("href", "")
            if url and not url.startswith("#"):  # Skip anchor links
                links.append({
                    "url": url,
                    "text": a.get_text().strip(),
                    "title": a.get("title", "")
                })
        
        return links
    
    def _extract_lists(self, container: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract lists from the content container.
        
        Args:
            container: BeautifulSoup object of the content container
            
        Returns:
            List of dictionaries containing list information:
            - type: list type (ordered/unordered)
            - items: list items as text
        """
        extracted_lists = []
        
        for list_tag in container.find_all(["ul", "ol"]):
            list_type = "ordered" if list_tag.name == "ol" else "unordered"
            items = [li.get_text().strip() for li in list_tag.find_all("li")]
            
            # Skip empty lists
            if not items:
                continue
                
            extracted_lists.append({
                "type": list_type,
                "items": items
            })
        
        return extracted_lists
    
    def _extract_quotes(self, container: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract quotes from the content container.
        
        Args:
            container: BeautifulSoup object of the content container
            
        Returns:
            List of dictionaries containing quote information:
            - text: quote text
            - attribution: quote attribution if available
        """
        quotes = []
        
        # Look for blockquote tags
        for blockquote in container.find_all("blockquote"):
            text = blockquote.get_text().strip()
            
            # Skip empty quotes
            if not text:
                continue
                
            # Try to find attribution
            attribution = ""
            cite = blockquote.find("cite")
            if cite:
                attribution = cite.get_text().strip()
                # Remove the attribution from the quote text
                text = text.replace(attribution, "").strip()
            
            # Another approach: look for a specific format like "Text" - Attribution
            if not attribution:
                match = re.search(r'"([^"]+)"\s*[-—–]\s*(.+)$', text)
                if match:
                    text = match.group(1)
                    attribution = match.group(2)
            
            quotes.append({
                "text": text,
                "attribution": attribution
            })
        
        # Look for inline quotes (using quotes or specific formatting)
        p_tags = container.find_all("p")
        for p in p_tags:
            text = p.get_text().strip()
            
            # Check if the paragraph is a standalone quote
            if (text.startswith('"') and text.endswith('"')) or (text.startswith('"') and text.endswith('"')):
                # Extract attribution if it exists
                parts = text.split('" — ')
                if len(parts) > 1:
                    quote_text = parts[0].strip('"') + '"'
                    attribution = parts[1]
                else:
                    quote_text = text
                    attribution = ""
                
                quotes.append({
                    "text": quote_text.strip('"').strip('"'),
                    "attribution": attribution
                })
        
        return quotes
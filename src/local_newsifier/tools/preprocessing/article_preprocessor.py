"""
ArticlePreprocessor service for comprehensive article content preprocessing.

This service combines the ContentCleaner, ContentExtractor, and MetadataEnhancer
to provide a complete preprocessing pipeline for article content.
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from fastapi_injectable import injectable

from local_newsifier.tools.preprocessing.content_cleaner import ContentCleaner
from local_newsifier.tools.preprocessing.content_extractor import ContentExtractor
from local_newsifier.tools.preprocessing.metadata_enhancer import MetadataEnhancer


@injectable(use_cache=False)
class ArticlePreprocessor:
    """Service for preprocessing article content."""
    
    def __init__(
        self,
        content_cleaner: Optional[ContentCleaner] = None,
        content_extractor: Optional[ContentExtractor] = None,
        metadata_enhancer: Optional[MetadataEnhancer] = None,
    ):
        """Initialize the article preprocessor with component dependencies.
        
        Args:
            content_cleaner: Optional content cleaner instance
            content_extractor: Optional content extractor instance
            metadata_enhancer: Optional metadata enhancer instance
        """
        self.content_cleaner = content_cleaner or ContentCleaner()
        self.content_extractor = content_extractor or ContentExtractor()
        self.metadata_enhancer = metadata_enhancer or MetadataEnhancer()
    
    def preprocess(
        self,
        content: str,
        html_content: Optional[str] = None,
        url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        clean_content: bool = True,
        extract_structures: bool = True,
        enhance_metadata: bool = True
    ) -> Dict[str, Any]:
        """Preprocess article content with configurable processing options.
        
        Args:
            content: Plain text article content
            html_content: Optional HTML content for better extraction
            url: Optional article URL for context
            metadata: Optional existing metadata to enhance
            clean_content: Whether to clean the content
            extract_structures: Whether to extract content structures
            enhance_metadata: Whether to enhance metadata
            
        Returns:
            Dictionary with preprocessing results:
            - content: Cleaned text content
            - original_content: Original text content
            - metadata: Enhanced metadata
            - structures: Extracted structures (if extract_structures is True)
        """
        result = {
            "original_content": content,
            "content": content,
            "metadata": metadata or {}
        }
        
        # Extract content from HTML if available and content is not provided
        if html_content and not content.strip():
            extracted_content = self.content_extractor.extract_content(html_content)
            result["content"] = extracted_content.get("text", "")
            
            # Store extracted structures if requested
            if extract_structures:
                result["structures"] = {
                    "title": extracted_content.get("title", ""),
                    "html": extracted_content.get("html", ""),
                }
                
                # Add other extracted elements if available
                for key in ["images", "links", "lists", "quotes"]:
                    if key in extracted_content:
                        result["structures"][key] = extracted_content[key]
        
        # Clean content if requested
        if clean_content and result["content"]:
            result["content"] = self.content_cleaner.clean_content(result["content"])
        
        # Extract structures from content if requested and not already extracted
        if extract_structures and html_content and "structures" not in result:
            extracted_content = self.content_extractor.extract_content(html_content)
            result["structures"] = {
                "title": extracted_content.get("title", ""),
                "html": extracted_content.get("html", ""),
            }
            
            # Add other extracted elements if available
            for key in ["images", "links", "lists", "quotes"]:
                if key in extracted_content:
                    result["structures"][key] = extracted_content[key]
        
        # Enhance metadata if requested
        if enhance_metadata:
            enhanced_metadata = self.metadata_enhancer.enhance_metadata(
                content=result["content"],
                html_content=html_content,
                url=url,
                existing_metadata=result["metadata"]
            )
            result["metadata"] = enhanced_metadata
        
        return result
    
    def preprocess_article_data(
        self,
        article_data: Dict[str, Any],
        html_content: Optional[str] = None,
        clean_content: bool = True,
        extract_structures: bool = True,
        enhance_metadata: bool = True
    ) -> Dict[str, Any]:
        """Preprocess article data with configurable processing options.
        
        This method is a convenience wrapper for preprocess() that takes
        article data in a dictionary format.
        
        Args:
            article_data: Dictionary containing article data:
              - content: Article content
              - url: Article URL
              - title: Article title
              - published_at: Publication date
              - source: Article source
            html_content: Optional HTML content for better extraction
            clean_content: Whether to clean the content
            extract_structures: Whether to extract content structures
            enhance_metadata: Whether to enhance metadata
            
        Returns:
            Dictionary with preprocessing results
        """
        # Extract data from article_data dictionary
        content = article_data.get("content", "")
        url = article_data.get("url", "")
        
        # Build metadata from article_data
        metadata = {}
        for key in ["title", "published_at", "source"]:
            if key in article_data and article_data[key]:
                metadata[key] = article_data[key]
        
        # Preprocess with extracted data
        result = self.preprocess(
            content=content,
            html_content=html_content,
            url=url,
            metadata=metadata,
            clean_content=clean_content,
            extract_structures=extract_structures,
            enhance_metadata=enhance_metadata
        )
        
        # Update article_data with preprocessed results
        article_data["content"] = result["content"]
        
        # Update metadata fields in article_data
        for key, value in result["metadata"].items():
            if key not in article_data or not article_data[key]:
                article_data[key] = value
        
        # Add structures if extracted
        if "structures" in result:
            article_data["structures"] = result["structures"]
        
        return article_data
    
    def clean_html_content(
        self,
        html_content: str,
        extract_main_content: bool = True,
        remove_boilerplate: bool = True
    ) -> str:
        """Clean HTML content by extracting main content and removing boilerplate.
        
        Args:
            html_content: HTML content to clean
            extract_main_content: Whether to extract main content
            remove_boilerplate: Whether to remove boilerplate elements
            
        Returns:
            Cleaned HTML content
        """
        if not html_content:
            return ""
        
        # Extract main content if requested
        if extract_main_content:
            extracted = self.content_extractor.extract_content(html_content)
            return extracted.get("html", "")
        
        return html_content
    
    def extract_article_metadata(
        self,
        content: str,
        html_content: Optional[str] = None,
        url: Optional[str] = None,
        existing_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Extract metadata from article content.
        
        Args:
            content: Plain text article content
            html_content: Optional HTML content for better extraction
            url: Optional article URL for context
            existing_metadata: Optional existing metadata to enhance
            
        Returns:
            Dictionary with extracted metadata
        """
        return self.metadata_enhancer.enhance_metadata(
            content=content,
            html_content=html_content,
            url=url,
            existing_metadata=existing_metadata
        )
"""
Content cleaning utilities for article preprocessing.

This module provides functions to clean and normalize article content,
removing boilerplate text, normalizing whitespace, and handling special characters.
"""

import re
import html
import unicodedata
from typing import List, Set, Dict, Any, Optional


class ContentCleaner:
    """Tool for cleaning and normalizing article content."""
    
    def __init__(
        self,
        remove_boilerplate: bool = True,
        normalize_whitespace: bool = True,
        handle_special_chars: bool = True,
        remove_duplicates: bool = True,
    ):
        """Initialize the content cleaner with configurable options.
        
        Args:
            remove_boilerplate: Whether to remove common boilerplate text
            normalize_whitespace: Whether to normalize whitespace
            handle_special_chars: Whether to handle special characters
            remove_duplicates: Whether to remove duplicate paragraphs
        """
        self.remove_boilerplate = remove_boilerplate
        self.normalize_whitespace = normalize_whitespace
        self.handle_special_chars = handle_special_chars
        self.remove_duplicates = remove_duplicates
        
        # Common boilerplate patterns to remove
        self.boilerplate_patterns = [
            r"Subscribe to our newsletter",
            r"Sign up (for|to) our newsletter",
            r"Subscribe now",
            r"For more (news|information|stories)",
            r"Follow us on (Twitter|Facebook|Instagram)",
            r"Share this (article|story|post)",
            r"Related (articles|stories|content)",
            r"Recommended (for you|articles|reading)",
            r"Continue reading",
            r"Privacy Policy",
            r"Terms of (Use|Service)",
            r"All rights reserved",
            r"\d+ min read",
            r"Published \d+ (minutes|hours|days) ago",
            r"Updated on",
            r"Please enable JavaScript",
            r"Download our app",
            r"Click here to subscribe",
            r"Advertisement",
            r"Sponsored content",
            r"This article contains affiliate links",
        ]
        
        # Compile the patterns for efficiency
        self.boilerplate_regex = re.compile(
            "|".join(f"({pattern})" for pattern in self.boilerplate_patterns),
            re.IGNORECASE
        )
    
    def clean_content(self, content: str) -> str:
        """Clean article content by applying all configured cleaning operations.
        
        Args:
            content: The article content to clean
            
        Returns:
            Cleaned article content
        """
        if not content:
            return ""
        
        # Apply each cleaning operation if enabled
        if self.handle_special_chars:
            content = self._handle_special_characters(content)
            
        if self.remove_boilerplate:
            content = self._remove_boilerplate(content)
            
        if self.normalize_whitespace:
            content = self._normalize_whitespace(content)
            
        if self.remove_duplicates:
            content = self._remove_duplicate_paragraphs(content)
            
        return content.strip()
    
    def _handle_special_characters(self, content: str) -> str:
        """Handle special characters and encodings.
        
        This function:
        1. Decodes HTML entities
        2. Normalizes Unicode characters
        3. Converts smart quotes to regular quotes
        
        Args:
            content: The article content to process
            
        Returns:
            Content with special characters handled
        """
        # Decode HTML entities (e.g., &amp; to &)
        content = html.unescape(content)
        
        # Normalize Unicode characters
        content = unicodedata.normalize('NFKC', content)
        
        # Convert smart quotes to regular quotes
        smart_quotes_map = {
            '"': '"',  # Left double quote
            '"': '"',  # Right double quote
            ''': "'",  # Left single quote
            ''': "'",  # Right single quote
            '–': "-",  # En dash
            '—': "-",  # Em dash
            '…': "...",  # Ellipsis
            '\u2022': "*",  # Bullet
            '\u2023': ">",  # Triangle bullet
            '\u2043': "-",  # Hyphen bullet
        }
        
        for smart, regular in smart_quotes_map.items():
            content = content.replace(smart, regular)
            
        return content
    
    def _normalize_whitespace(self, content: str) -> str:
        """Normalize whitespace in the content.
        
        This function:
        1. Converts all whitespace to spaces
        2. Reduces multiple spaces to single spaces
        3. Ensures consistent newlines between paragraphs
        
        Args:
            content: The article content to process
            
        Returns:
            Content with normalized whitespace
        """
        # Convert all whitespace characters to spaces
        content = re.sub(r'\s', ' ', content)
        
        # Reduce multiple spaces to single spaces
        content = re.sub(r' +', ' ', content)
        
        # Identify paragraphs (we'll consider them separated by multiple spaces or specific html tags)
        paragraphs = re.split(r'(?:</?(?:p|div|h[1-6]|br|article|section)>|  +)', content)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # Join paragraphs with consistent newlines
        return "\n\n".join(paragraphs)
    
    def _remove_boilerplate(self, content: str) -> str:
        """Remove common boilerplate text from the content.
        
        Args:
            content: The article content to process
            
        Returns:
            Content with boilerplate text removed
        """
        # Split content into paragraphs
        paragraphs = content.split('\n\n')
        
        # Filter out paragraphs that match boilerplate patterns
        filtered_paragraphs = []
        for paragraph in paragraphs:
            # Skip empty paragraphs
            if not paragraph.strip():
                continue
                
            # Skip paragraphs matching boilerplate patterns
            if self.boilerplate_regex.search(paragraph):
                continue
                
            # Skip paragraphs that are too short and look like navigation/metadata
            if len(paragraph) < 30 and not re.search(r'[.!?]', paragraph):
                continue
                
            filtered_paragraphs.append(paragraph)
            
        return '\n\n'.join(filtered_paragraphs)
    
    def _remove_duplicate_paragraphs(self, content: str) -> str:
        """Remove duplicate paragraphs from the content.
        
        Args:
            content: The article content to process
            
        Returns:
            Content with duplicate paragraphs removed
        """
        # Split content into paragraphs
        paragraphs = content.split('\n\n')
        
        # Use a set to track unique paragraphs (order-preserving)
        unique_paragraphs = []
        seen_paragraphs = set()
        
        for paragraph in paragraphs:
            # Normalize for comparison (lowercase, remove extra whitespace)
            normalized = re.sub(r'\s+', ' ', paragraph.lower().strip())
            
            # Only keep if we haven't seen this paragraph before
            if normalized and normalized not in seen_paragraphs:
                seen_paragraphs.add(normalized)
                unique_paragraphs.append(paragraph)
                
        return '\n\n'.join(unique_paragraphs)
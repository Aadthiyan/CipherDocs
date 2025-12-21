"""
Text cleaning and preprocessing logic.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TextCleaner:
    """Utilities for cleaning and normalizing text"""
    
    @staticmethod
    def clean(text: str) -> str:
        """
        Apply text cleaning pipeline.
        
        1. Normalize whitespace
        2. Remove boilerplate (headers/footers approximation)
        3. Clean invisible characters
        """
        if not text:
            return ""
            
        text = TextCleaner._normalize_whitespace(text)
        text = TextCleaner._fix_utf8_artifacts(text)
        
        return text.strip()

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """Replace multiple spaces/newlines with single ones, preserving paragraph breaks"""
        # Replace non-breaking spaces
        text = text.replace('\xa0', ' ')
        
        # Replace 3+ newlines with 2 (paragraphs)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Replace multiple spaces with single space (within lines)
        # We process line by line to avoid merging lines incorrectly if not desired
        lines = []
        for line in text.split('\n'):
            clean_line = re.sub(r'[ \t]+', ' ', line).strip()
            lines.append(clean_line)
            
        return '\n'.join(lines)

    @staticmethod
    def _fix_utf8_artifacts(text: str) -> str:
        """Fix common encoding artifacts"""
        replacements = {
            '\u2018': "'", '\u2019': "'",  # Smart quotes
            '\u201c': '"', '\u201d': '"',  # Smart double quotes
            '\u2013': '-', '\u2014': '-',  # Dashes
            '\u2026': '...',               # Ellipsis
        }
        for char, repl in replacements.items():
            text = text.replace(char, repl)
        return text

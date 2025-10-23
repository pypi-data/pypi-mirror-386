"""
Citation Hallucination Stop Library

A Python library for filtering academic references to match only in-text citations,
eliminating hallucinated or non-cited references.

Usage:
    from citation_hallucination_stop import CitationHallucinationStop
    
    cleaner = CitationHallucinationStop()
    filtered_refs = cleaner.clean_references(text_content, all_references)
"""

from .cleaner import CitationHallucinationStop
from .utils import normalize_token, validate_apa_author

__version__ = "1.0.0"
__author__ = "Citation Hallucination Stop Team"
__email__ = "citation.hallucination.stop@example.com"

__all__ = [
    "CitationHallucinationStop",
    "normalize_token", 
    "validate_apa_author"
]

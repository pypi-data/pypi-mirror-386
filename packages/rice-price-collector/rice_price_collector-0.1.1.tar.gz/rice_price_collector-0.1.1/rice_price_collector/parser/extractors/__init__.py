"""
rice_price_collector.parser.extractors
Subpackage for section-specific PDF extractors (e.g., rice, fish, vegetables).
Each extractor knows how to read its section and convert it into a clean table.
"""

from .rice import extract_and_parse_rice

__all__ = [
    "extract_and_parse_rice",
]

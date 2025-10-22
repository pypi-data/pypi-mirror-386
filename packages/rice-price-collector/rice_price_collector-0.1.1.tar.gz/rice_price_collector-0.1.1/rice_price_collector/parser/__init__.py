
"""
rice_price_collector.parser

Parser subpackage for extracting and cleaning CBSL rice price data.
Exposes main user-facing functions for easy import.
"""


# Expose only the main user-facing API
from .parser import process_year_folders_dict, parse_price_section
from .columns import create_smart_column_names
from .utils import extract_section_between, fix_missing_columns

__all__ = [
    "process_year_folders_dict",
    "parse_price_section",
    "create_smart_column_names",
    "extract_section_between",
    "fix_missing_columns",
]

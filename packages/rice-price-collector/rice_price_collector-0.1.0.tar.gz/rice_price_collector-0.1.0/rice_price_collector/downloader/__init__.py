"""
rice_price_collector.downloader

Downloader subpackage for fetching CBSL rice price PDFs.
Exposes main user-facing functions for easy import.
"""

# Expose only the main user-facing API
from .pdf_downloader import main as download_all_pdfs, download_pdfs_to

__all__ = ["download_all_pdfs", "download_pdfs_to"]
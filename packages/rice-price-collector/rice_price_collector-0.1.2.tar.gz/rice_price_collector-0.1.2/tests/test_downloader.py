import tempfile
import shutil
import os
import asyncio
import pytest
from rice_price_collector import download_pdfs_to

@pytest.mark.asyncio
async def test_download_pdfs_to_creates_files():
    # Use a temporary directory for output
    with tempfile.TemporaryDirectory() as tmpdir:
        years = [2024]  # Use a single year for a quick test
        await download_pdfs_to(years, tmpdir)
        # Check that a subdirectory for the year exists and contains files
        year_dir = os.path.join(tmpdir, "2024")
        assert os.path.isdir(year_dir), f"Year directory {year_dir} not created"
        files = os.listdir(year_dir)
        assert any(f.endswith(".pdf") for f in files), "No PDF files downloaded"

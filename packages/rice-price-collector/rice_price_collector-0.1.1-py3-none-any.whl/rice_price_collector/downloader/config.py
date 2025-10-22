# Base URLs
BASE = "https://www.cbsl.gov.lk"
AJAX_URL = f"{BASE}/en/views/ajax"

# Folder to save PDFs (always in current working directory)
from pathlib import Path
OUTPUT_DIR = Path(__file__).resolve().parent / "data" / "raw"
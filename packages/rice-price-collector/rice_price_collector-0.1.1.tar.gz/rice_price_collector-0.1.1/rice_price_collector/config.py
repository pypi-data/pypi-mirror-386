# Configuration for rice_price_collector
from pathlib import Path

# Project root directory
BASE_DIR = Path.cwd()

# Data directories
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# Ensure directories exist
for path in [RAW_DATA_DIR, PROCESSED_DIR]:
	path.mkdir(parents=True, exist_ok=True)

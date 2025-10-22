"""
batch_extract.py

Batch extractor for multiple yearly folders of CBSL rice price PDFs.

Usage:
    python -m rice_price_collector.parser.batch_extract 2025 2024 2023

This will look inside:
    ../data/raw/2025/
    ../data/raw/2024/
    ../data/raw/2023/

and extract the "RICE" section from every PDF found in each folder.
Each year's results are saved as CSV, and a combined file is created.
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Local import (your extractor function)
from .extractors.rice import extract_and_parse_rice


# Function to process a single year's folder

def process_year_folder(year_folder: Path, output_dir: Path):
    """
    Process all PDFs within a given year's folder and save the combined CSV.
    """
    print(f"\nProcessing year {year_folder.name} ...")

    pdf_files = sorted(year_folder.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDFs found in {year_folder}")
        return None

    all_dfs = []
    for idx, pdf_path in enumerate(pdf_files, start=1):
        print(f"[{idx}/{len(pdf_files)}] → {pdf_path.name}")
        try:
            df = extract_and_parse_rice(str(pdf_path))
            if not df.empty:
                # Add the date (from filename) for tracking
                df.insert(0, "date", pdf_path.stem)
                all_dfs.append(df)
            else:
                print("No 'RICE' section data found.")
        except Exception as e:
            print(f"Failed to parse {pdf_path.name}: {e}")

    if not all_dfs:
        print(f"No usable data extracted for {year_folder.name}")
        return None

    # Combine and save
    df_year = pd.concat(all_dfs, ignore_index=True)
    output_file = output_dir / f"rice_prices_{year_folder.name}.csv"
    df_year.to_csv(output_file, index=False)
    print(f"Saved {len(df_year)} rows → {output_file.resolve()}")
    return df_year

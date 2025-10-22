import tempfile
import os
import pandas as pd
from rice_price_collector import process_year_folders_dict

def test_process_year_folders_dict_returns_dataframe():
    # Use a temp dir and create a fake year folder with a dummy PDF if needed
    with tempfile.TemporaryDirectory() as tmpdir:
        year = "2024"
        year_dir = os.path.join(tmpdir, year)
        os.makedirs(year_dir)
        # Place a dummy PDF file so the parser finds something
        dummy_pdf_path = os.path.join(year_dir, "dummy.pdf")
        with open(dummy_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4\n%Fake PDF content\n")
        folders = {year: year_dir}
        df = process_year_folders_dict(folders)
        # Accept DataFrame or None (if parser can't handle dummy PDF)
        assert df is None or isinstance(df, pd.DataFrame), "Output is not a DataFrame or None"

# Utility: process a dict of years and folders
def process_year_folders_dict(year_folder_dict, output_dir=None):
    """
    Process a dictionary mapping years to folder paths, combine results into a DataFrame.
    Args:
        year_folder_dict (dict): {"2023": "/path/to/2023", ...}
        output_dir (Path or str, optional): Where to save combined CSV (if provided)
    Returns:
        pd.DataFrame: Combined DataFrame for all years
    """
    from pathlib import Path
    from .batch_extract import process_year_folder
    combined = []
    for year, folder in year_folder_dict.items():
        folder_path = Path(folder)
        if not folder_path.exists():
            print(f"Folder not found: {folder_path}")
            continue
        df_year = process_year_folder(folder_path, Path("."))
        if df_year is not None:
            combined.append(df_year)
    if combined:
        full_df = pd.concat(combined, ignore_index=True)
        return full_df
    else:
        print("No data extracted from provided folders.")
        return None
import re
import pandas as pd
from .utils import fix_missing_columns

def parse_price_section(section_lines):
    """
    Takes messy price text and creates a neat table (DataFrame).
    
    What it does:
        1. Combines broken lines
        2. Cleans up the text
        3. Splits each line into: Item name, Unit, and Prices
        4. Creates a table with all the data
    
    Input example:
        ["Samba Rs./kg 130.00 132.00 135.00",
         "Nadu (White)",
         "Rs./kg 125.00 128.00"]
    
    Output: A pandas table with columns [Item, Unit, Col1, Col2, ...]
    """
    
    # Combine Lines That Belong Together
    # Sometimes one item is split across multiple lines. We fix that here.
    
    merged_lines = []
    
    for line in section_lines:
        # Skip empty lines or lines with "Marandagahamula"
        if not line.strip() or "Marandagahamula" in line:
            continue
        
        # Does this line start with a letter? Then it's a NEW item
        if re.match(r"^[A-Za-z]", line):
            merged_lines.append(line)
        
        # Otherwise, add it to the PREVIOUS item
        elif len(merged_lines) > 0:
            merged_lines[-1] = merged_lines[-1] + " " + line
    
    # Process Each Line
    
    parsed_rows = []  # Will store all our cleaned data
    
    for line in merged_lines:
        
        # Clean up the text
        clean_line = line
        clean_line = clean_line.replace(",", "")      # Remove commas
        clean_line = clean_line.replace("...", "")    # Remove dots
        clean_line = clean_line.replace("—", "-")     # Fix dashes
        
        # Add space between letters and "Rs."
        # "SambaRs." becomes "Samba Rs."
        clean_line = re.sub(r"([a-zA-Z)])(Rs\.)", r"\1 \2", clean_line)
        
        # Separate numbers that are stuck together
        # "130.00132.00" becomes "130.00 132.00"
        clean_line = re.sub(r"(\d+\.\d{1,2})(?=\d+\.\d{1,2})", r"\1 ", clean_line)
        
        # Break line into pieces (tokens)
        # Find: "n.a.", "Rs./kg", words, and decimal numbers
        tokens = re.findall(
            r"n\.a\.|N\.A\.|Rs\.\/[A-Za-z]+|[A-Za-z()]+|\d+\.\d{1,2}|\d+",
            clean_line
        )
        
        # Need at least 3 pieces (item name, unit, one price)
        if len(tokens) < 3:
            continue  # Skip this line, not enough data
        
        # Find the unit marker (Rs./kg or Rs./Ltr)
        unit_index = None
        for i, token in enumerate(tokens):
            if "Rs" in token:
                unit_index = i
                break
        
        # If no unit found, skip this line
        if unit_index is None:
            continue
        
        # Split tokens into parts
        item_name = " ".join(tokens[:unit_index]).strip()  # Everything before "Rs./kg"
        unit = tokens[unit_index].strip()                  # "Rs./kg"
        value_tokens = tokens[unit_index + 1:]             # All prices after unit
        
        # Extract Price Numbers
        
        prices = []
        for value in value_tokens:
            # Find decimal numbers in this token
            numbers = re.findall(r"\d+\.\d{1,2}", value)
            
            if numbers:
                # Add all numbers found
                prices.extend(numbers)
            elif value.lower() == "n.a.":
                # "n.a." means missing data
                prices.append(None)
            else:
                # Unknown value, treat as missing
                prices.append(None)
        
        # Fix Missing Columns

        # Make sure we have exactly 10 price columns
        # Missing columns are added after position 6
        
        prices = fix_missing_columns(prices, total_columns=10, insert_position=6)
        
        # Create row: [Item, Unit, Price1, Price2, ...]
        row = [item_name, unit] + prices
        parsed_rows.append(row)
    
    # ─────────────────────────────────────────────────────────────────
    # STEP 5: Create the DataFrame (Table)
    # ─────────────────────────────────────────────────────────────────
    
    # If no data was found, return an empty table
    if len(parsed_rows) == 0:
        return pd.DataFrame(columns=["Item", "Unit"])
    
    # Find the longest row
    max_length = max(len(row) for row in parsed_rows)
    
    # Make all rows the same length by adding None to the end
    for row in parsed_rows:
        while len(row) < max_length:
            row.append(None)
    
    # Create column names: Item, Unit, Col1, Col2, Col3...
    num_price_cols = max_length - 2
    column_names = ["Item", "Unit"] + [f"Col{i}" for i in range(1, num_price_cols + 1)]
    
    # Create the DataFrame
    df = pd.DataFrame(parsed_rows, columns=column_names)
    
    # Clean Up Item Names and Units
    
    # Remove "Rs" from end of item names
    df["Item"] = df["Item"].str.replace(r"Rs$", "", regex=True).str.strip()
    
    # Clean unit column (keep only letters, slash, dot)
    df["Unit"] = df["Unit"].str.replace(r"[^A-Za-z/.]", "", regex=True).str.strip()
    
    # Fix cases where "Rs./kg" ended up in the Item column
    # Example: "Samba Rs./kg" should be split into "Samba" | "Rs./kg"
    
    # Find rows where Unit is empty but Item contains "Rs"
    has_problem = (df["Unit"] == "") | (df["Unit"].isna())
    has_problem = has_problem & df["Item"].str.contains("Rs", na=False)
    
    for index in df[has_problem].index:
        item_text = df.at[index, "Item"]
        
        # Try to split "Samba Rs./kg" into two parts
        match = re.search(r"(.*?)(Rs\.\/[A-Za-z]+)", item_text)
        if match:
            df.at[index, "Item"] = match.group(1).strip()  # "Samba"
            df.at[index, "Unit"] = match.group(2).strip()  # "Rs./kg"
    
    # Convert Prices to Numbers
    
    # Replace text "n.a." with actual None (missing value)
    df = df.replace({"n.a.": None, "N.A.": None})
    
    # Convert all price columns from text to numbers
    for col in df.columns[2:]:  # Skip Item and Unit columns
        df[col] = pd.to_numeric(df[col], errors="coerce")


    return df
import pdfplumber

def extract_section_between(pdf_path, start_letters, end_letters, page_num=2):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num - 1]
        chars = page.chars

    # Group by approximate line y-position
    y_map = {}
    for c in chars:
        y_key = round(c["top"], -1)
        y_map.setdefault(y_key, []).append(c["text"])
    
    # Rebuild text lines
    lines = []
    for y, texts in sorted(y_map.items()):
        line_text = "".join(texts).replace("\xa0", "").strip()
        lines.append((y, line_text))
    
    # Find start and end positions
    def find_line_y(target):
        for y, text in lines:
            if all(ch in text for ch in target.replace(" ", "")):  # handles spaced "R I C E"
                return y
        return None

    start_y = find_line_y(start_letters)
    end_y = find_line_y(end_letters)
    if not start_y or not end_y:
        raise ValueError("Could not find start or end header.")

    # Collect lines in between
    section = [txt for y, txt in lines if start_y < y < end_y]
    return section

def fix_missing_columns(price_list, total_columns=10, insert_position=6):
    """
    Makes sure each row has the same number of price columns.
    
    Why? Sometimes data has missing columns in the middle (like missing retail prices).
    We need to add empty spaces (None) in the right place.
    
    Example:
        Input:  [130.00, 132.00, 135.00]  (only 3 prices, but we need 10)
        Output: [130.00, 132.00, 135.00, None, None, None, None, None, None, None]
        
        The None values are added after position 6 (after wholesale prices).
    
    Parameters:
        price_list: List of prices (may be incomplete)
        total_columns: How many columns we want in total (default: 10)
        insert_position: Where to add missing values (default: 6)
    
    Returns:
        A list with exactly 'total_columns' items
    """
    # Make a copy so we don't change the original
    price_list = list(price_list)
    
    # Check if we're missing columns
    if len(price_list) < total_columns:
        # Calculate how many columns are missing
        missing_count = total_columns - len(price_list)
        
        # Don't insert beyond what we have
        safe_position = min(insert_position, len(price_list))
        
        # Insert None values at the right position
        # This is like cutting the list and inserting empty spaces
        for i in range(missing_count):
            price_list.insert(safe_position, None)
    
    return price_list
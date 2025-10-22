def create_smart_column_names(section_lines):
    """
    Creates meaningful column names based on what locations are in the data.
    
    Why? The data has prices from different markets and different days.
    Instead of "Col1, Col2, Col3...", we want names like:
        "wholesale_pettah_yesterday", "wholesale_pettah_today", etc.
    
    How it works:
        1. Looks at the first 50 lines to see what locations are mentioned
        2. Checks if "Marandagahamula" market exists
        3. Creates column names for each location and day
    
    Typical structure:
        - Wholesale markets: Pettah, Dambulla (sometimes Marandagahamula)
        - Retail markets: Pettah, Dambulla, Narahenpita
        - Each location has: Yesterday's price + Today's price
    
    Parameters:
        section_lines: List of text lines from the document
    
    Returns:
        List of column names like:
            ["item", "unit", "wholesale_pettah_yesterday", 
             "wholesale_pettah_today", ...]
    """
    
    # Combine first 50 lines to search for location names
    # We only check the beginning because location names appear at the top
    first_50_lines = section_lines[:50]
    combined_text = " ".join(first_50_lines).lower()

    # Start with basic columns
    column_names = ["item", "unit"]

    # Define default locations
    # These are the markets where wholesale prices come from
    wholesale_locations = ["pettah", "marandagahamula"]
    
    # These are the markets where retail (customer) prices come from
    retail_locations = ["pettah", "dambulla", "narahenpita"]

    # Build wholesale column names
    # For each wholesale market, add yesterday and today columns
    for location in wholesale_locations:
        column_names.append(f"wholesale_{location}_yesterday")
        column_names.append(f"wholesale_{location}_today")
    
    
    # Build retail column names
    # For each retail market, add yesterday and today columns
    for location in retail_locations:
        column_names.append(f"retail_{location}_yesterday")
        column_names.append(f"retail_{location}_today")
    
    return column_names

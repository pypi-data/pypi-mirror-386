from ..utils import extract_section_between
from ..parser import parse_price_section
from ..columns import create_smart_column_names


def extract_and_parse_rice(pdf_path, start_word="RICE", end_word="FISH", page_number=2):
    """
    Extracts the RICE section from a PDF and converts it to a table with smart column names.
    
    This function does three things:
        1. Finds and extracts text between "RICE" and "FISH" in the PDF
        2. Parses that text into a clean DataFrame
        3. Adds meaningful column names based on detected locations
    
    Parameters:
        pdf_path: Path to the PDF file
        start_word: Word that marks the beginning of the section (default: "RICE")
        end_word: Word that marks the end of the section (default: "FISH")
        page_number: Which page to look at (default: 2)
    
    Returns:
        A pandas DataFrame with the parsed price data and smart column names
    """
    
    # extract_section_between function should read the PDF and return lines of text
    section_lines = extract_section_between(pdf_path, start_word, end_word, page_number)
    
    # Parse the extracted lines into a DataFrame
    df = parse_price_section(section_lines)

    # Add Smart Column Names
    # Generate meaningful column names based on locations
    smart_columns = create_smart_column_names(section_lines)
    
    # Only use as many column names as we have columns in the DataFrame
    # (Sometimes we have fewer columns than expected)
    smart_columns = smart_columns[:len(df.columns)]
    
    # Replace the generic column names (Item, Unit, Col1, Col2...)
    # with meaningful names (item, unit, wholesale_pettah_yesterday...)
    df.columns = smart_columns
    
    return df

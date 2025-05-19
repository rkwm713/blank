# excel_utils.py

def extract_string_value(value, default='N/A'):
    """
    Safely extract a string value from a potential dictionary.
    This handles Katapult's nested attribute structure.
    """
    if value is None:
        return default
        
    if isinstance(value, dict):
        # Try to extract a value from common paths in Katapult attributes
        for key in ['-Imported', 'assessment', 'button_added', 'tagtext']:
            if key in value:
                nested_value = value.get(key)
                if isinstance(nested_value, dict) and 'tagtext' in nested_value:
                    return nested_value['tagtext']
                elif nested_value:
                    return str(nested_value)
        # If no specific key found, just take the first value
        if value:
            return str(next(iter(value.values()), default))
    
    return str(value) if value is not None else default

def inches_to_feet_inches_str(inches):
    """
    Convert inches to feet-inches string format.
    This duplicates the function from utils.py for independence.
    """
    if inches is None:
        return 'N/A'
    try:
        inches = float(inches)
        feet = int(inches // 12)
        rem_inches = int(round(inches % 12))
        # Handle the case where inches rounds to 12
        if rem_inches == 12:
            feet += 1
            rem_inches = 0
        return f"{feet}'-{rem_inches}\""
    except Exception:
        return 'N/A'

def categorize_wire(wire_type):
    """Categorize wire as COMM, CPS, or OTHER based on description."""
    if not wire_type:
        return 'OTHER'
        
    wire_type_lower = wire_type.lower()
    
    # Check for comm-related keywords
    if any(comm_term in wire_type_lower for comm_term in 
          ['fiber', 'telco', 'comm', 'cable', 'telephone', 'catv', 'charter', 'att', 'spectrum']):
        return 'COMM'
    
    # Check for CPS-related keywords
    if any(cps_term in wire_type_lower for cps_term in 
          ['cps', 'electric', 'power', 'neutral', 'primary', 'secondary']):
        return 'CPS'
    
    # Default to OTHER
    return 'OTHER'

def get_excel_column_letter(column_index):
    """
    Convert a column index to Excel column letter (1=A, 2=B, etc.)
    """
    result = ""
    while column_index > 0:
        column_index, remainder = divmod(column_index - 1, 26)
        result = chr(65 + remainder) + result
    return result

def parse_feet_inches(height_str):
    """
    Parse a height string in feet-inches format (e.g. "35'-6\"") to inches.
    """
    if not height_str or height_str == 'N/A':
        return None
        
    import re
    match = re.search(r'(\d+)\'(?:-)?(\d+)"', height_str)
    if match:
        feet = int(match.group(1))
        inches = int(match.group(2))
        return (feet * 12) + inches
    
    # Try to parse as a direct number
    try:
        return float(height_str)
    except ValueError:
        return None 
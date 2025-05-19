# utils.py
import re
import math

def inches_to_feet_inches_str(inches):
    """Convert inches to feet-inches string format (e.g. 42 -> "3'-6\"")."""
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

def meters_to_feet_inches_str(meters):
    """Convert meters to feet-inches string format."""
    if meters is None:
        return 'N/A'
    try:
        inches = float(meters) * 39.3701
        return inches_to_feet_inches_str(inches)
    except Exception:
        return 'N/A'

def normalize_pole_id(pole_id):
    """Extract the numeric portion of a pole ID."""
    if not pole_id:
        return None
    match = re.search(r'(\d+)$', str(pole_id))
    return match.group(1) if match else None

def normalize_owner(owner):
    """Normalize owner name for consistent comparison."""
    if not owner:
        return None
    owner = owner.strip().upper().replace('&', 'AND')
    if owner in ['AT&T', 'ATT', 'AT AND T', 'ATANDT']:
        return 'AT&T'
    if owner in ['CPS ENERGY', 'CPS']:
        return 'CPS ENERGY'
    return owner

def get_pole_number_from_node_id(katapult, node_id, fallback_id=None):
    """
    Get the pole number from a node ID with enhanced fallback options.
    
    Args:
        katapult (dict): The full Katapult JSON data
        node_id (str): The node ID to look up
        fallback_id (str, optional): Fallback ID to use if no pole number is found
        
    Returns:
        str: The pole number or a descriptive fallback
    """
    if not node_id:
        return fallback_id or "Unknown"
    
    node = katapult.get('nodes', {}).get(node_id, {})
    attributes = node.get('attributes', {})
    
    # Ordered list of attribute names to check for pole number
    attribute_names = ['PoleNumber', 'pl_number', 'dloc_number', 'PL_number', 'DLOC_number', 'pole_tag', 'electric_pole_tag']
    
    # Try each attribute name
    for attr_name in attribute_names:
        attr = attributes.get(attr_name)
        if attr:
            if isinstance(attr, dict):
                # Try common paths within the attribute dict
                for key in ['-Imported', 'assessment', 'button_added', 'tagtext']:
                    if key in attr:
                        value = attr.get(key)
                        if isinstance(value, dict) and 'tagtext' in value:
                            return value['tagtext']
                        elif value:
                            return value
            elif isinstance(attr, str):
                return attr
    
    # If no pole number found, check if this is a reference/service pole
    node_type = attributes.get('node_type')
    if node_type:
        if isinstance(node_type, dict):
            node_type_value = next(iter(node_type.values()), None)
        else:
            node_type_value = node_type
            
        if node_type_value and str(node_type_value).lower() in ['reference', 'service', 'anchor']:
            # Try to get a descriptive name for the reference node
            for name_attr in ['name', 'label', 'scid', 'reference_name', 'description']:
                name_value = attributes.get(name_attr)
                if name_value:
                    if isinstance(name_value, dict):
                        first_value = next(iter(name_value.values()), None)
                        if first_value:
                            return f"Reference-{first_value}"
                    else:
                        return f"Reference-{name_value}"
            
            # If no specific name found, use node type
            return f"{node_type_value.capitalize()}-{node_id[:6]}"
    
    # Last resort: use short node ID as fallback
    return fallback_id or f"Node-{node_id[:6]}"

def extract_string_value(value, default='N/A'):
    """
    Safely extract a string value from a potential dictionary.
    This handles Katapult's nested attribute structure.
    
    Args:
        value: The value to extract from (string, dictionary, or None)
        default: Default value to return if extraction fails
    
    Returns:
        str: The extracted string value
    """
    if value is None:
        return default
        
    if isinstance(value, dict):
        # Try to extract from common Katapult patterns
        # Order of preference for keys
        preferred_keys = ['-Imported', 'assessment', 'button_added', 'tagtext', 'value', 'name', 'id']
        for key in preferred_keys:
            if key in value:
                val = value[key]
                # If the value itself is a dict, recurse or take its primary value
                if isinstance(val, dict):
                    # Attempt to get a more specific sub-value if common keys exist
                    for sub_key in ['tagtext', 'value', 'name', 'id']:
                        if sub_key in val:
                            return str(val[sub_key])
                    # Otherwise, take the first value of the nested dict
                    if val:
                        return str(next(iter(val.values())))
                elif val is not None: # Ensure value is not None before converting to string
                    return str(val)

        # If no preferred keys found, take the first non-empty value
        for val in value.values():
            if isinstance(val, dict):
                # Attempt to get a more specific sub-value
                for sub_key in ['tagtext', 'value', 'name', 'id']:
                    if sub_key in val:
                        return str(val[sub_key])
                if val: # If still a dict, take its first value
                    return str(next(iter(val.values())))
            elif val is not None: # Ensure value is not None
                 return str(val)
        
        # If all values were None or dicts that resolved to None
        return default

    # If not a dictionary or None, convert to string
    return str(value)

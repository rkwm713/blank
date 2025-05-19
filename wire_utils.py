# wire_utils.py
import re
from utils import extract_string_value # For robustly getting values

def parse_feet_inches_str_to_inches(height_str):
    """Converts a string like "X'-Y\"" or "X' Y\"" to inches."""
    if not isinstance(height_str, str):
        return None
    
    match = re.match(r"(\d+)'(?:-|\s*)?(\d+)\"?", height_str)
    if match:
        try:
            feet = int(match.group(1))
            inches_part = int(match.group(2))
            return (feet * 12) + inches_part
        except ValueError:
            return None
    # Try to parse if it's just a number (could be inches already)
    try:
        return float(height_str)
    except ValueError:
        return None

def process_wire_height(wire):
    """
    Extract height from wire data in inches.
    
    Args:
        wire (dict): Wire data from Katapult
        
    Returns:
        float: Height in inches or None if not available
    """
    if not wire or not isinstance(wire, dict):
        print(f"[DEBUG] Wire data is empty, None, or not a dict.")
        return None

    wire_id_val = wire.get('id') or wire.get('_id') # Get some identifier for logging
    wire_id_for_log = extract_string_value(wire_id_val, 'unknown_wire')
    
    height_keys_to_check = [
        '_measured_height', 'measured_height', 'height', 
        'attachmentHeight', 'z', 'z_coord', 'elevation', 
        'value', # Generic, often used in nested structures like SPIDA's attachmentHeight
        'measuredHeight_in' # From some Katapult exports for spans
    ]

    for key in height_keys_to_check:
        raw_height_val = None
        if key == 'z' or key == 'z_coord': # Often nested under 'position'
            position_data = wire.get('position')
            if isinstance(position_data, dict):
                raw_height_val = position_data.get(key)
        elif key == 'value' and 'attachmentHeight' in wire: # SPIDA pattern: "attachmentHeight": {"value": X, "unit": "m"}
             attachment_height_dict = wire.get('attachmentHeight')
             if isinstance(attachment_height_dict, dict):
                 raw_height_val = attachment_height_dict.get('value')
                 unit = extract_string_value(attachment_height_dict.get('unit'), 'inches').lower()
                 if raw_height_val is not None:
                    try:
                        height_float = float(raw_height_val)
                        if unit == 'm' or unit == 'meters':
                            print(f"[DEBUG] Converting SPIDA height {height_float}m from key '{key}' for wire {wire_id_for_log}")
                            return height_float * 39.3701
                        elif unit == 'ft' or unit == 'feet':
                            print(f"[DEBUG] Converting SPIDA height {height_float}ft from key '{key}' for wire {wire_id_for_log}")
                            return height_float * 12
                        # Assuming inches if unit is 'in', 'inches', or not specified and value is large
                        print(f"[DEBUG] Using SPIDA height {height_float} (assumed inches) from key '{key}' for wire {wire_id_for_log}")
                        return height_float
                    except (ValueError, TypeError) as e:
                        print(f"[DEBUG] Error parsing SPIDA height '{raw_height_val}' from key '{key}' for wire {wire_id_for_log}: {e}")
                        continue # Try next key
        else:
            raw_height_val = wire.get(key)

        if raw_height_val is not None:
            # Attempt to parse if it's a string like "X'-Y\""
            if isinstance(raw_height_val, str):
                parsed_inches = parse_feet_inches_str_to_inches(raw_height_val)
                if parsed_inches is not None:
                    print(f"[DEBUG] Parsed feet-inches string '{raw_height_val}' to {parsed_inches} inches from key '{key}' for wire {wire_id_for_log}")
                    return parsed_inches
            
            # Try direct float conversion
            try:
                height_float = float(raw_height_val)
                # Heuristic: if value is small (e.g. < 10 for meters, < 50 for feet) and not explicitly inches,
                # it might need conversion. This is tricky without explicit units.
                # The original code assumed < 100 was meters, which is too broad.
                # For now, if a unit isn't specified, we assume it's inches unless it's a very small number.
                # This part needs careful consideration based on typical data patterns.
                # If _measured_height is usually in inches, trust it.
                # If 'z' from 'position' is often meters, convert it.
                if key in ['z', 'z_coord', 'elevation'] and height_float < 15: # Likely meters if from a coordinate system
                    print(f"[DEBUG] Converting height {height_float} (assumed meters) from key '{key}' for wire {wire_id_for_log}")
                    return height_float * 39.3701
                # If key is 'height' and value is small, it might be feet.
                elif key == 'height' and 15 <= height_float < 50: # Potentially feet
                     # This is ambiguous. Could be a low attachment in inches or a height in feet.
                     # For now, assume inches if not clearly specified otherwise by key/context.
                     # To be safer, one might require explicit unit or more context.
                     print(f"[DEBUG] Using height {height_float} (ambiguous, assumed inches) from key '{key}' for wire {wire_id_for_log}")
                     return height_float
                
                print(f"[DEBUG] Using height {height_float} (assumed inches) from key '{key}' for wire {wire_id_for_log}")
                return height_float
            except (ValueError, TypeError) as e:
                print(f"[DEBUG] Error parsing height '{raw_height_val}' from key '{key}' for wire {wire_id_for_log}: {e}")
                # Continue to the next key if parsing fails
    
    trace_id_val = wire.get('_trace')
    trace_id_for_log = extract_string_value(trace_id_val, 'unknown_trace')
    print(f"[DEBUG] No valid height found after checking all keys for wire {wire_id_for_log} with trace {trace_id_for_log}")
    return None

# trace_utils.py
from utils import normalize_owner, extract_string_value

def get_trace_by_id(katapult, trace_id):
    """
    Enhanced robust trace lookup that handles different Katapult JSON trace structures.
    
    Args:
        katapult (dict): The full Katapult JSON data
        trace_id (str): The trace ID to look up
        
    Returns:
        dict: The trace data if found, or an empty dict if not found
    """
    if not trace_id:
        return {}
    
    # Log trace structure for debugging
    trace_struct = "unknown"
    
    # First check direct top-level access (original expectation)
    if trace_id in katapult.get('traces', {}):
        trace_struct = "direct"
        return katapult['traces'][trace_id]
        
    # Check if it's in trace_data (new structure)
    trace_data = katapult.get('traces', {}).get('trace_data', {})
    if isinstance(trace_data, dict) and trace_id in trace_data:
        trace_struct = "trace_data"
        return trace_data[trace_id]
        
    # Check if it's in trace_items (alternative structure)
    trace_items = katapult.get('traces', {}).get('trace_items', {})
    if isinstance(trace_items, dict) and trace_id in trace_items:
        trace_struct = "trace_items"
        return trace_items[trace_id]
    
    # Additional fallback: check if trace_id is nested one level deeper
    for key, value in katapult.get('traces', {}).items():
        if isinstance(value, dict) and trace_id in value:
            trace_struct = f"nested_under_{key}"
            return value[trace_id]
    
    print(f"[DEBUG] Could not find trace_id '{trace_id}' (structure: {trace_struct})")
    return {}

def extract_wire_metadata(wire, trace):
    """
    Extract important metadata from a wire and its trace.
    
    Args:
        wire (dict): Wire data object
        trace (dict): Trace data or None
        
    Returns:
        dict: Dictionary with owner, cable_type, and is_proposed flags
    """
    result = {
        'owner': 'Unknown', # Default to Unknown
        'cable_type': 'Unknown', # Default to Unknown
        'is_proposed': False
    }

    # Attempt to extract from trace first (more reliable source)
    if trace:
        # Owner: Try 'company', then 'owner', then 'client'
        owner_val = trace.get('company') or trace.get('owner') or trace.get('client')
        if owner_val:
            result['owner'] = extract_string_value(owner_val, 'Unknown')

        # Cable type: Try 'cable_type', then 'type', then 'description'
        cable_type_val = trace.get('cable_type') or trace.get('type') or trace.get('description')
        if cable_type_val:
            result['cable_type'] = extract_string_value(cable_type_val, 'Unknown')
            
        # Proposed status
        # Check common boolean flags or string indicators
        proposed_flag = trace.get('proposed') or trace.get('is_proposed') or trace.get('status')
        if isinstance(proposed_flag, bool):
            result['is_proposed'] = proposed_flag
        elif isinstance(proposed_flag, str) and proposed_flag.lower() in ['true', 'yes', 'proposed']:
            result['is_proposed'] = True
        elif isinstance(proposed_flag, (int, float)) and proposed_flag == 1:
             result['is_proposed'] = True


    # Fallback to wire data if trace didn't yield full results
    # Owner from wire
    if result['owner'] == 'Unknown':
        owner_wire_val = wire.get('_company') or wire.get('owner') or wire.get('client')
        if owner_wire_val:
            result['owner'] = extract_string_value(owner_wire_val, 'Unknown')

    # Cable type from wire
    if result['cable_type'] == 'Unknown':
        cable_type_wire_val = wire.get('_cable_type') or wire.get('type') or wire.get('description')
        if cable_type_wire_val:
            result['cable_type'] = extract_string_value(cable_type_wire_val, 'Unknown')

    # Proposed status from wire (if not already set from trace)
    if not result['is_proposed']:
        proposed_wire_flag = wire.get('_proposed') or wire.get('is_proposed') or wire.get('status')
        if isinstance(proposed_wire_flag, bool):
            result['is_proposed'] = proposed_wire_flag
        elif isinstance(proposed_wire_flag, str) and proposed_wire_flag.lower() in ['true', 'yes', 'proposed']:
            result['is_proposed'] = True
        elif isinstance(proposed_wire_flag, (int, float)) and proposed_wire_flag == 1:
            result['is_proposed'] = True
            
    # Normalize owner name
    result['owner'] = normalize_owner(result['owner']) if result['owner'] != 'Unknown' else 'Unknown'

    # If cable_type is still "Unknown" but owner is known, try to infer from owner
    if result['cable_type'] == 'Unknown' and result['owner'] != 'Unknown':
        if 'CPS ENERGY' in result['owner'].upper():
            # Could be neutral, primary, secondary. For now, keep as Unknown or add specific logic.
            pass # Or, e.g., result['cable_type'] = "CPS Unspecified"
        elif any(comm_owner in result['owner'].upper() for comm_owner in ['AT&T', 'SPECTRUM', 'CHARTER']):
            result['cable_type'] = "Communication" # Generic communication type

    # Final check for "unknown" and replace with a more descriptive placeholder if needed
    if result['owner'] == 'Unknown' and result['cable_type'] == 'Unknown':
        # This indicates a significant lack of data.
        # Consider logging this event for review.
        print(f"[DEBUG] Wire metadata extraction resulted in Unknown/Unknown for wire: {wire.get('id', 'N/A')}")
        pass


    return result

def classify_wire(trace_data):
    """
    Enhanced classification of a wire based on its trace data.
    
    Args:
        trace_data (dict): A single trace entry from katapult['traces']
        
    Returns:
        str: "CPS_ELECTRICAL", "COMMUNICATION", or "OTHER"
    """
    # Default to OTHER if we can't classify
    if not isinstance(trace_data, dict):
        return "OTHER"
        
    # 1. Primary classification: usageGroup if available
    usage_group = trace_data.get('usageGroup', '').upper()
    if usage_group == 'POWER':
        # Check if it's CPS Energy specifically
        company = trace_data.get('company', '').strip().upper()
        if 'CPS' in company:
            return "CPS_ELECTRICAL"
        return "OTHER"  # Non-CPS power
    elif usage_group == 'COMMUNICATION':
        return "COMMUNICATION"
        
    # 2. Fallback: company + cable_type
    company = trace_data.get('company', '').strip().upper()
    cable_type = trace_data.get('cable_type', '').strip().upper()
    
    # CPS Electrical
    if 'CPS' in company:
        if any(power_type in cable_type for power_type in 
              ['PRIMARY', 'NEUTRAL', 'SECONDARY', 'ELECTRIC', 'POWER', 'PHASE']):
            return "CPS_ELECTRICAL"
        # If no cable type but it's CPS, assume it's electrical as fallback
        elif not cable_type:
            return "CPS_ELECTRICAL"
    
    # Communication
    if any(comm_co in company for comm_co in 
          ['AT&T', 'ATT', 'SPECTRUM', 'CHARTER', 'COMCAST', 'FRONTIER', 'VERIZON', 'TELCO']):
        return "COMMUNICATION"
        
    if any(comm_type in cable_type for comm_type in 
          ['COM', 'FIBER', 'TELCO', 'CABLE', 'TELEPHONE', 'CATV']):
        return "COMMUNICATION"
        
    # Default fallback
    return "OTHER"

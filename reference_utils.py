# reference_utils.py
import re
from utils import inches_to_feet_inches_str, normalize_pole_id, normalize_owner, get_pole_number_from_node_id
from wire_utils import process_wire_height
from trace_utils import extract_wire_metadata, get_trace_by_id

def get_direction_between_nodes(node1, node2):
    """
    Calculate cardinal direction from node1 to node2 based on coordinates.
    
    Args:
        node1 (dict): Source node with latitude/longitude
        node2 (dict): Target node with latitude/longitude
        
    Returns:
        str: Cardinal direction ("North", "South", "East", "West", etc.)
    """
    if not node1 or not node2 or 'latitude' not in node1 or 'longitude' not in node1 or 'latitude' not in node2 or 'longitude' not in node2:
        return "Unknown Direction"
    
    # Calculate direction from coordinates
    lat_diff = node2.get('latitude', 0) - node1.get('latitude', 0)
    lon_diff = node2.get('longitude', 0) - node1.get('longitude', 0)
    
    # Simple 8-direction calculation
    if abs(lat_diff) > abs(lon_diff) * 2:
        direction = "North" if lat_diff > 0 else "South"
    elif abs(lon_diff) > abs(lat_diff) * 2:
        direction = "East" if lon_diff > 0 else "West"
    else:
        # Diagonal directions
        if lat_diff > 0 and lon_diff > 0:
            direction = "North East"
        elif lat_diff > 0 and lon_diff < 0:
            direction = "North West"
        elif lat_diff < 0 and lon_diff > 0:
            direction = "South East"
        else:  # lat_diff < 0 and lon_diff < 0
            direction = "South West"
    
    return direction

def get_attacher_from_wire(wire, trace, section_midspan_height_in=None):
    """
    Create an attacher dictionary from a wire and its trace data.
    
    Args:
        wire (dict): Wire data from connection section photo
        trace (dict): Trace data for the wire
        section_midspan_height_in (str, optional): Midspan height from section data
        
    Returns:
        dict: Attacher dictionary with standard fields
    """
    # Extract metadata
    wire_meta = extract_wire_metadata(wire, trace)
    owner = wire_meta['owner']
    cable_type = wire_meta['cable_type']
    is_proposed = wire_meta['is_proposed']
    
    # Create description
    att_desc = f"{owner} {cable_type}".strip()
    if not att_desc:
        att_desc = "Unknown Attachment"
    
    # Extract heights
    existing_height_inches = process_wire_height(wire)
    existing_height_str = inches_to_feet_inches_str(existing_height_inches) if existing_height_inches is not None else "N/A"
    
    # Determine proposed height based on wire status
    proposed_height_str = "N/A"
    if is_proposed:  # New install on this span
        existing_height_str = "N/A"  # New has no existing height on span
        proposed_height_str = inches_to_feet_inches_str(existing_height_inches) if existing_height_inches is not None else "N/A"
    
    # Determine midspan value
    midspan_val_str = "N/A"
    raw_midspan_val_inches = None
    
    # Check if wire is underground from various indicators
    goes_underground = False
    
    # 1. Check trace cable_type for underground indicators
    if trace:
        cable_type_str = trace.get('cable_type', '').lower() if trace.get('cable_type') else ''
        if ('underground' in cable_type_str or 
            cable_type_str == 'ug' or
            'riser' in cable_type_str or 
            'vertical' in cable_type_str):
            goes_underground = True
            print(f"[DEBUG] Wire {att_desc} marked as UG based on cable_type: {trace.get('cable_type', '')}")
    
    # 2. Check description for underground indicators 
    if not goes_underground and att_desc:
        desc_lower = att_desc.lower()
        if ('ug' in desc_lower or 
            'underground' in desc_lower or 
            'riser' in desc_lower or 
            'vertical' in desc_lower):
            goes_underground = True
            print(f"[DEBUG] Wire {att_desc} marked as UG based on description")
    
    # 3. Check wire attributes for underground flag
    if not goes_underground:
        if wire.get('_underground') or wire.get('underground'):
            goes_underground = True
            print(f"[DEBUG] Wire {att_desc} marked as UG based on _underground flag")
    
    # If it goes underground, always set midspan to UG regardless of other values
    if goes_underground:
        midspan_val_str = "UG"
    else:
        # Not underground, process normal midspan height
        # Try section-level midspan height first
        if section_midspan_height_in:
            try:
                raw_midspan_val_inches = float(section_midspan_height_in)
                midspan_val_str = inches_to_feet_inches_str(raw_midspan_val_inches)
            except (ValueError, TypeError):
                print(f"[DEBUG] Could not parse section midspanHeight_in: {section_midspan_height_in}")
        
        # Try wire's own midspan height if available
        wire_midspan_height = wire.get('_midspan_height')
        if not raw_midspan_val_inches and wire_midspan_height:
            try:
                wire_midspan_height_float = float(wire_midspan_height)
                midspan_val_str = inches_to_feet_inches_str(wire_midspan_height_float)
                raw_midspan_val_inches = wire_midspan_height_float
                print(f"[DEBUG] Using wire's own _midspan_height: {midspan_val_str}")
            except (ValueError, TypeError):
                print(f"[DEBUG] Could not parse wire _midspan_height: {wire_midspan_height}")
    
    # Create final attacher dictionary
    return {
        'description': att_desc,
        'existing_height': existing_height_str,
        'proposed_height': proposed_height_str,
        'midspan_proposed': midspan_val_str,
        'raw_existing_height_inches': existing_height_inches,
        'raw_proposed_height_inches': existing_height_inches if proposed_height_str != "N/A" else None,
        'is_proposed': is_proposed,
        'goes_underground': goes_underground
    }

def process_reference_span(katapult, current_node_id, other_node_id, conn_id, conn_data, is_backspan=False, previous_pole_id=None):
    """
    Process a reference span connection and generate a header and attachments.
    
    Args:
        katapult (dict): The full Katapult JSON data
        current_node_id (str): The node ID of the current pole
        other_node_id (str): The node ID of the other end of the span
        conn_id (str): The connection ID
        conn_data (dict): The connection data
        is_backspan (bool): Whether this is a backspan connection
        previous_pole_id (str, optional): The previous pole ID if this is a backspan
        
    Returns:
        tuple: (header_dict, attachments_list)
    """
    print(f"[DEBUG] Processing {'backspan' if is_backspan else 'reference'} connection {conn_id}")
    
    # Get pole tag for other node with enhanced fallback
    other_pole_tag_raw = get_pole_number_from_node_id(katapult, other_node_id, fallback_id=f"Node-{other_node_id[:6]}")
    other_node_data = katapult.get('nodes', {}).get(other_node_id, {})
    
    # Log the found tag
    print(f"[DEBUG] Found other pole tag: {other_pole_tag_raw} for node {other_node_id}")
    
    # Use the normalized previous pole ID for backspan if available
    if is_backspan and previous_pole_id:
        other_pole_tag_display = previous_pole_id
        print(f"[DEBUG] Using previous pole ID from sequence: {previous_pole_id} for backspan")
    else:
        # If not a backspan, ensure we have a readable tag for the other pole
        if other_pole_tag_raw:
            if isinstance(other_pole_tag_raw, str):
                # Check if the tag is a descriptive/fallback tag that should not be normalized by normalize_pole_id
                is_descriptive_or_fallback_tag = any(
                    other_pole_tag_raw.startswith(prefix) for prefix in 
                    ["Reference-", "Service-", "Anchor-", "Node-", "Unknown-"]
                )

                if is_descriptive_or_fallback_tag:
                    other_pole_tag_display = other_pole_tag_raw
                    print(f"[DEBUG] Using descriptive/fallback other pole tag as is: {other_pole_tag_display}")
                # Check if it's a standard pole ID format that might need PL prefixing
                elif other_pole_tag_raw.isdigit() or \
                     (other_pole_tag_raw.upper().startswith("PL") and other_pole_tag_raw[2:].isdigit()):
                    try:
                        normalized_numeric_part = normalize_pole_id(other_pole_tag_raw) # Extracts numeric part
                        if normalized_numeric_part:
                            other_pole_tag_display = f"PL{normalized_numeric_part}" # Ensure PL prefix
                        else: # normalize_pole_id returned None
                            other_pole_tag_display = other_pole_tag_raw # Fallback
                        print(f"[DEBUG] Normalized standard pole tag to: {other_pole_tag_display}")
                    except Exception as e:
                        print(f"[DEBUG] Error normalizing pole tag '{other_pole_tag_raw}': {e}")
                        other_pole_tag_display = other_pole_tag_raw
                else:
                    # For other string formats (e.g., "071.A", "PoleWithSuffixLetter123A") use as is.
                    other_pole_tag_display = other_pole_tag_raw
                    print(f"[DEBUG] Using other pole tag (non-standard for PL normalization) as is: {other_pole_tag_display}")
            else:
                # If other_pole_tag_raw is not a string (e.g. None, int), use its string representation
                other_pole_tag_display = str(other_pole_tag_raw)
                print(f"[DEBUG] Using non-string other pole tag as string: {other_pole_tag_display}")
        else:
            # Fallback if other_pole_tag_raw is None or empty
            other_pole_tag_display = f"Unknown-{other_node_id[:6]}"
            print(f"[DEBUG] Using fallback tag for other pole due to empty raw tag: {other_pole_tag_display}")

    # Ensure other_pole_tag_display is not None before creating the header
    if other_pole_tag_display is None:
        other_pole_tag_display = f"Error-{other_node_id[:6]}" # Should not happen with above logic
        print(f"[ERROR] other_pole_tag_display became None unexpectedly for node {other_node_id}. Raw: {other_pole_tag_raw}")

    print(f"[DEBUG] Final other pole tag for header: {other_pole_tag_display}")

    # Determine header text and style based on connection type
    header_text = ""
    header_style_hint = ""
    
    # Get direction
    direction = "Unknown Direction"
    connection_attributes = conn_data.get('attributes', {})
    
    # Try to extract direction from attributes
    for direction_path in ['direction_tag', 'direction', 'span_direction', 'ref_direction']:
        direction_attr = connection_attributes.get(direction_path)
        if direction_attr:
            print(f"[DEBUG] Found direction attribute: {direction_path} = {direction_attr}")
            
            # Handle if it's a dict with tagtext
            if isinstance(direction_attr, dict):
                for key in ['-Notes Added', 'button_added', 'assessment', '-Imported']:
                    if key in direction_attr:
                        direction_value = direction_attr[key]
                        if isinstance(direction_value, dict) and 'tagtext' in direction_value:
                            direction = direction_value['tagtext']
                            print(f"[DEBUG] Direction from {direction_path}.{key}.tagtext: {direction}")
                            break
                        elif isinstance(direction_value, str):
                            direction = direction_value
                            print(f"[DEBUG] Direction from {direction_path}.{key}: {direction}")
                            break
            # Handle if it's a direct string
            elif isinstance(direction_attr, str):
                direction = direction_attr
                print(f"[DEBUG] Direction directly from {direction_path}: {direction}")
            
            if direction != "Unknown Direction":
                break
    
    # If direction is still unknown, try to calculate it from coordinates
    if direction == "Unknown Direction" and not is_backspan:
        current_node = katapult.get('nodes', {}).get(current_node_id, {})
        calculated_direction = get_direction_between_nodes(current_node, other_node_data)
        if calculated_direction != "Unknown Direction":
            direction = calculated_direction
            print(f"[DEBUG] Calculated direction from coordinates: {direction}")
    
    # If backspan, override direction
    if is_backspan:
        direction = "Backspan"
        header_style_hint = "light-blue"  # Use light blue for backspans
    else:
        # For regular reference spans, determine color
        ref_color_hint = "orange"  # Default
        
        # Try multiple paths for color
        for color_path in ['color_tag', 'color', 'span_color', 'ref_color']:
            color_attr = connection_attributes.get(color_path)
            if color_attr:
                print(f"[DEBUG] Found color attribute: {color_path} = {color_attr}")
                
                # Extract color text using similar nested checking as with direction
                color_text = None
                if isinstance(color_attr, dict):
                    for key in ['-Notes Added', 'button_added', 'assessment', '-Imported']:
                        if key in color_attr:
                            color_value = color_attr[key]
                            if isinstance(color_value, dict) and 'tagtext' in color_value:
                                color_text = color_value['tagtext'].lower()
                                print(f"[DEBUG] Color from {color_path}.{key}.tagtext: {color_text}")
                                break
                            elif isinstance(color_value, str):
                                color_text = color_value.lower()
                                print(f"[DEBUG] Color from {color_path}.{key}: {color_text}")
                                break
                elif isinstance(color_attr, str):
                    color_text = color_attr.lower()
                    print(f"[DEBUG] Color directly from {color_path}: {color_text}")
                
                # Determine style hint based on color text
                if color_text:
                    if "orange" in color_text:
                        ref_color_hint = "orange"
                    elif "purple" in color_text:
                        ref_color_hint = "purple"
                    print(f"[DEBUG] Setting reference color to {ref_color_hint} based on '{color_text}'")
                    break
        
        header_style_hint = ref_color_hint
    
    # Sanitize direction for header
    if direction == "Unknown Direction":
        direction = "Reference"
        
    # Create consistent header text
    header_text = f"Ref ({direction}) to {other_pole_tag_display}"
    print(f"[DEBUG] Final header text: {header_text}")
    
    # Create header dictionary
    header = {
        'type': 'reference_header',
        'description': header_text,
        'style_hint': header_style_hint,
        'existing_height': '',
        'proposed_height': '',
        'midspan_proposed': ''
    }
    
    # Process attachments for this reference/backspan
    print(f"[DEBUG] Processing connection sections for {header_text} from connection {conn_id}")
    span_attachments = []
    
    # Extract attachments from connection sections
    for section_id, section in conn_data.get('sections', {}).items():
        print(f"[DEBUG] Processing section {section_id}")
        
        # Mid-span height for the section
        section_midspan_height_in_str = section.get('midspanHeight_in')
        print(f"[DEBUG] Section {section_id} midspanHeight_in: {section_midspan_height_in_str}")
        
        # Process photos in this section
        for photo_id, photo_assoc in section.get('photos', {}).items():
            print(f"[DEBUG] Processing photo {photo_id} in section {section_id}")
            
            # Get the full photo data
            main_photo_data = katapult.get('photos', {}).get(photo_id, {})
            photofirst_data = main_photo_data.get('photofirst_data', {})
            
            # Handle wire data as either list or dictionary
            wire_items_data = photofirst_data.get('wire', [])
            current_wire_items = []
            
            if isinstance(wire_items_data, dict):
                current_wire_items = list(wire_items_data.values())
            elif isinstance(wire_items_data, list):
                current_wire_items = wire_items_data
            
            print(f"[DEBUG] Found {len(current_wire_items)} wire items in photo {photo_id}")
            
            # Process each wire
            for wire in current_wire_items:
                if not isinstance(wire, dict):
                    continue
                    
                # Get trace ID and trace data
                trace_id = wire.get('_trace', '').strip()
                if not trace_id:
                    continue
                    
                trace = get_trace_by_id(katapult, trace_id)
                
                # Create attacher dictionary for this wire
                attacher = get_attacher_from_wire(wire, trace, section_midspan_height_in_str)
                span_attachments.append(attacher)
    
    # Sort attachments by height (descending)
    if span_attachments:
        sorted_span_attachments = sorted(
            span_attachments,
            key=lambda x: (x.get('raw_existing_height_inches') or 0) if x.get('existing_height', 'N/A') != 'N/A' else 
                          (x.get('raw_proposed_height_inches') or 0),
            reverse=True
        )
        
        # Per spec "list **all** attachments" for reference spans, so skipping deduplication here for now.
        # If over-listing becomes an issue, a more nuanced deduplication might be needed.
        # if len(sorted_span_attachments) > 1:
        #     # sorted_span_attachments = deduplicate_attachments(sorted_span_attachments) # Original deduplication
        #     print(f"[DEBUG] Reference span attachments (pre-dedup): {len(sorted_span_attachments)}")
        #     # print(f"[DEBUG] After deduplication, reference span has {len(sorted_span_attachments)} attachments")
        
        return header, sorted_span_attachments
    
    return header, []

# Keeping the function in case a more nuanced deduplication is needed later.
def deduplicate_attachments(attachments):
    """
    Deduplicate attachments based on owner, type, and height.
    
    Args:
        attachments (list): List of attachment dictionaries
        
    Returns:
        list: Deduplicated list of attachments
    """
    if not attachments:
        return []
        
    unique_attachments = {}
    
    for attachment in attachments:
        # Create a unique key based on owner, type and normalized height
        description = attachment.get('description', '')
        height = attachment.get('existing_height', 'N/A')
        
        # Extract owner and type from description
        parts = description.split(' ', 1)
        owner = parts[0] if parts else ''
        attachment_type = parts[1] if len(parts) > 1 else ''
        
        # Key combines owner, type, and height
        key = f"{owner}|{attachment_type}|{height}"
        
        if key not in unique_attachments:
            unique_attachments[key] = attachment
    
    return list(unique_attachments.values())

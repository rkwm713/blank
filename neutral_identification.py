"""
Module for neutral wire identification and height normalization.

This module provides functions to identify neutral wires across different data sources
(Katapult and SPIDAcalc) and normalize height values for consistent comparison.
"""

import re
import logging

def get_trace_by_id(katapult, trace_id):
    """
    Wrapper function for get_trace_by_id from make_ready_processor.py
    
    Args:
        katapult (dict): The full Katapult JSON data
        trace_id (str): The trace ID to look up
        
    Returns:
        dict: The trace data if found, or an empty dict if not found
    """
    # Import here to avoid circular imports
    from make_ready_processor import get_trace_by_id as processor_get_trace_by_id
    return processor_get_trace_by_id(katapult, trace_id)

# Configure logger
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('neutral_identification')

# Neutral wire identification patterns
NEUTRAL_PATTERNS = [
    r'neutral',
    r'cps\s+energy\s+neutral',
    r'cps\s+neutral',
    r'primary\s+neutral',
    r'secondary\s+neutral',
    r'power\s+neutral',
    r'electric.*neutral',
]

def normalize_height_to_inches(height_value, unit='inches'):
    """
    Normalize a height value to inches for consistent comparison.
    
    Args:
        height_value: The height value to normalize
        unit: The unit of the height value ('inches' or 'meters')
    
    Returns:
        float: The normalized height in inches, or None if conversion fails
    """
    if height_value is None:
        return None
        
    try:
        height_value = float(height_value)
        
        # Convert from meters to inches if needed
        if unit.lower() == 'meters':
            return height_value * 39.3701
        elif unit.lower() == 'inches':
            return height_value
        else:
            logger.warning(f"Unknown unit '{unit}', assuming inches")
            return height_value
    except (ValueError, TypeError) as e:
        logger.warning(f"Error converting height '{height_value}' to float: {str(e)}")
        return None

def is_neutral_wire(wire_description):
    """
    Determine if a wire description indicates it's a neutral wire.
    
    Args:
        wire_description: String description of the wire
        
    Returns:
        bool: True if it's a neutral wire, False otherwise
    """
    if not wire_description:
        return False
        
    normalized_desc = wire_description.lower().strip()
    
    # Check against known neutral wire patterns
    for pattern in NEUTRAL_PATTERNS:
        if re.search(pattern, normalized_desc):
            return True
            
    return False

def identify_neutrals_katapult(pole_data, katapult):
    """
    Identify neutral wires in Katapult data for a pole.
    
    Args:
        pole_data: Processed pole data dictionary
        katapult: Full Katapult JSON data
        
    Returns:
        list: List of dictionaries with neutral wire data
    """
    neutral_wires = []
    
    # Find the node data for this pole
    pole_number = pole_data.get('pole_number')
    node_id = None
    
    # First, try to find the node by pole number
    for node_id_candidate, node in katapult.get('nodes', {}).items():
        # Check various places where pole number might be stored
        attributes = node.get('attributes', {})
        for attr_key, attr_value in attributes.items():
            if isinstance(attr_value, dict):
                for sub_key, sub_value in attr_value.items():
                    if str(sub_value) == str(pole_number):
                        node_id = node_id_candidate
                        break
                if node_id:
                    break
            elif str(attr_value) == str(pole_number):
                node_id = node_id_candidate
                break
        if node_id:
            break
    
    if not node_id:
        logger.warning(f"Could not find node for pole {pole_number}")
        # Process photos directly from pole_data as fallback
        photos = pole_data.get('photos', {})
    else:
        # Get photos from the node
        node = katapult['nodes'][node_id]
        photos = node.get('photos', {})
        logger.info(f"Found node {node_id} for pole {pole_number} with {len(photos)} photos")
    
    # Process all photos and their wires
    for photo_id, photo in photos.items():
        try:
            # Ensure photo has data
            if not isinstance(photo, dict):
                continue
                
            # For nodes, actual photo data is in katapult['photos']
            if node_id:
                # If this is an association object, get the actual photo
                if 'association' in photo:
                    photofirst_data = katapult.get('photos', {}).get(photo_id, {}).get('photofirst_data', {})
                else:
                    photofirst_data = photo.get('photofirst_data', {})
            else:
                # Directly use photo data from pole_data (test data format)
                photofirst_data = photo.get('photofirst_data', {})
            
            # Get wire data - can be a dict or list
            wire_data = photofirst_data.get('wire', {})
            
            # Convert to a consistent format (list of wire objects)
            wires = []
            if isinstance(wire_data, list):
                wires = wire_data
            elif isinstance(wire_data, dict):
                wires = list(wire_data.values())
            
            # Process each wire
            for wire in wires:
                if not isinstance(wire, dict):
                    continue
                
                # Get trace ID and look up trace data
                trace_id = wire.get('_trace', '')
                if not trace_id:
                    continue
                    
                # Get height value
                measured_height = wire.get('_measured_height')
                if not measured_height:
                    continue
                
                # Use the trace ID to look up in traces.trace_data
                trace_data = None
                
                # First check if traces is a dict with trace_data
                if 'traces' in katapult and 'trace_data' in katapult['traces']:
                    trace_data = katapult['traces']['trace_data'].get(trace_id)
                
                # If not found, try looking directly in traces
                if not trace_data and 'traces' in katapult:
                    trace_data = katapult['traces'].get(trace_id)
                
                # If still not found, use our general trace lookup function
                if not trace_data:
                    trace_data = get_trace_by_id(katapult, trace_id)
                
                if not trace_data:
                    logger.warning(f"Could not find trace data for trace_id {trace_id}")
                    continue
                
                # Extract company and cable_type
                company = trace_data.get('company', '')
                cable_type = trace_data.get('cable_type', '')
                wire_description = f"{company} {cable_type}".strip()
                
                # Check if this is a neutral wire
                if 'neutral' in cable_type.lower() or is_neutral_wire(wire_description):
                    height_inches = normalize_height_to_inches(measured_height, 'inches')
                    
                    if height_inches is not None:
                        neutral_wire = {
                            'height': height_inches,
                            'description': wire_description,
                            'source': 'katapult',
                            'trace_data': trace_data,
                            'wire_data': wire,
                            'trace_id': trace_id
                        }
                        neutral_wires.append(neutral_wire)
                        logger.info(f"Found Katapult neutral wire: {wire_description} at height {height_inches} inches (trace ID: {trace_id})")
        except Exception as e:
            logger.error(f"Error processing photo {photo_id}: {str(e)}")
    
    return neutral_wires

def identify_neutrals_spidacalc(pole_data, spida_pole_data):
    """
    Identify neutral wires in SPIDAcalc data for a pole.
    
    Args:
        pole_data: Processed pole data dictionary
        spida_pole_data: SPIDAcalc data for this pole
        
    Returns:
        list: List of dictionaries with neutral wire data
    """
    neutral_wires = []
    
    if not spida_pole_data:
        return neutral_wires
        
    # Find measured and recommended designs
    measured_design = None
    recommended_design = None
    
    for design in spida_pole_data.get('designs', []):
        if not isinstance(design, dict):
            continue
            
        label = design.get('label', '').lower()
        if label == 'measured design':
            measured_design = design
        elif label == 'recommended design':
            recommended_design = design
    
    # Process wires from the measured design
    if measured_design:
        for wire in measured_design.get('structure', {}).get('wires', []):
            if not isinstance(wire, dict):
                continue
                
            # Check for neutral usage group
            usage_groups = wire.get('usageGroup', [])
            if isinstance(usage_groups, str):
                usage_groups = [usage_groups]
                
            is_neutral = False
            for group in usage_groups:
                if 'NEUTRAL' in group.upper():
                    is_neutral = True
                    break
                    
            # Also check owner and wire description
            owner = wire.get('owner', {}).get('id', '')
            wire_type = wire.get('clientItem', {}).get('type', '')
            wire_description = f"{owner} {wire_type}"
            
            if is_neutral or is_neutral_wire(wire_description):
                # Get attachment height and convert from meters to inches
                attachment_height = wire.get('attachmentHeight', {}).get('value')
                height_inches = normalize_height_to_inches(attachment_height, 'meters')
                
                if height_inches is not None:
                    neutral_wires.append({
                        'height': height_inches,
                        'description': wire_description,
                        'source': 'spidacalc',
                        'wire_data': wire,
                        'usage_groups': usage_groups
                    })
                    logger.info(f"Found SPIDAcalc neutral wire: {wire_description} at height {height_inches} inches")
    
    return neutral_wires

def get_highest_neutral(neutral_wires):
    """
    Get the highest neutral wire from a list of neutral wires.
    
    Args:
        neutral_wires: List of neutral wire dictionaries
        
    Returns:
        dict: The highest neutral wire, or None if no neutral wires
    """
    if not neutral_wires:
        return None
        
    return max(neutral_wires, key=lambda wire: wire['height'])

def identify_attachments_below_neutral(pole_data, highest_neutral, katapult, spida_pole_data=None):
    """
    Identify all attachments below the highest neutral wire.
    
    Args:
        pole_data: Processed pole data dictionary
        highest_neutral: Dictionary with the highest neutral wire data
        katapult: Full Katapult JSON data
        spida_pole_data: SPIDAcalc data for this pole (optional)
        
    Returns:
        list: List of attachments below the neutral wire
    """
    attachments_below_neutral = []
    
    # If no neutral wire found, log and return all attachments
    if not highest_neutral:
        logger.warning(f"No neutral wire found for pole {pole_data.get('pole_number')}. Including all attachments.")
        return pole_data.get('attachers', [])
        
    neutral_height = highest_neutral['height']
    logger.info(f"Using highest neutral at height {neutral_height} inches")
    
    # Find the node ID for this pole in Katapult
    pole_number = pole_data.get('pole_number')
    node_id = None
    node = None
    
    # First try to find the node by pole number
    for node_id_candidate, node_data in katapult.get('nodes', {}).items():
        # Check various places where pole number might be stored
        attributes = node_data.get('attributes', {})
        for attr_key, attr_value in attributes.items():
            if isinstance(attr_value, dict):
                for sub_key, sub_value in attr_value.items():
                    if str(sub_value) == str(pole_number):
                        node_id = node_id_candidate
                        node = node_data
                        break
                if node_id:
                    break
            elif str(attr_value) == str(pole_number):
                node_id = node_id_candidate
                node = node_data
                break
        if node_id:
            break
    
    # If we found the node, parse it directly to find all attachments
    attachments = []
    
    if node:
        logger.info(f"Found node {node_id} for pole {pole_number}")
        
        # Process photos to find all attachments 
        for photo_id, photo in node.get('photos', {}).items():
            try:
                # Check if this is an association object
                if 'association' in photo:
                    # Get the actual photo data from katapult photos
                    photo_data = katapult.get('photos', {}).get(photo_id, {})
                else:
                    photo_data = photo
                
                # Get photofirst data
                photofirst_data = photo_data.get('photofirst_data', {})
                if not photofirst_data:
                    continue
                
                # Get wire data - can be a dict or list
                wire_data = photofirst_data.get('wire', {})
                
                # Convert to a consistent format
                wires = []
                if isinstance(wire_data, list):
                    wires = wire_data
                elif isinstance(wire_data, dict):
                    wires = list(wire_data.values())
                
                # Process each wire
                for wire in wires:
                    if not isinstance(wire, dict):
                        continue
                    
                    # Get trace ID and measured height
                    trace_id = wire.get('_trace', '')
                    measured_height = wire.get('_measured_height')
                    
                    if not trace_id or not measured_height:
                        continue
                    
                    # Convert height to float for comparison
                    try:
                        height_inches = float(measured_height)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid height value: {measured_height}")
                        continue
                    
                    # Get trace data
                    trace_data = None
                    
                    # First check if traces is a dict with trace_data
                    if 'traces' in katapult and 'trace_data' in katapult['traces']:
                        trace_data = katapult['traces']['trace_data'].get(trace_id)
                    
                    # If not found, try looking directly in traces
                    if not trace_data and 'traces' in katapult:
                        trace_data = katapult['traces'].get(trace_id)
                    
                    # If still not found, use our general trace lookup function
                    if not trace_data:
                        trace_data = get_trace_by_id(katapult, trace_id)
                    
                    if not trace_data:
                        logger.warning(f"Could not find trace data for trace_id {trace_id}")
                        continue
                    
                    # Extract company and cable_type
                    company = trace_data.get('company', '')
                    cable_type = trace_data.get('cable_type', '')
                    wire_description = f"{company} {cable_type}".strip()
                    
                    # Create attachment record
                    attachment = {
                        'description': wire_description,
                        'existing_height': inches_to_feet_inches_str(height_inches),
                        'proposed_height': 'N/A',  # Will be filled in by Excel generation if available
                        'midspan_proposed': 'N/A',  # Will be filled in by Excel generation if available
                        'raw_existing_height_inches': height_inches,
                        'trace_id': trace_id
                    }
                    attachments.append(attachment)
            except Exception as e:
                logger.error(f"Error processing photo {photo_id}: {str(e)}")
        
        # If we found attachments in the Katapult data, use those instead of pole_data.attachers
        if attachments:
            logger.info(f"Found {len(attachments)} attachments in Katapult data for pole {pole_number}")
        else:
            logger.warning(f"No attachments found in Katapult data for pole {pole_number}, falling back to pole_data.attachers")
            attachments = pole_data.get('attachers', [])
    else:
        # If node not found, use attachers from pole_data (useful for testing)
        logger.warning(f"Could not find node for pole {pole_number}, using attachers from pole_data")
        attachments = pole_data.get('attachers', [])
    
    # Create a visualization of the pole with heights
    visualize_pole_attachments(pole_data, neutral_height)
    
    # Create a list for keeping track of processed attachments (avoid duplicates)
    processed_attachment_trace_ids = set()
    
    # Process all attachers and find those below the neutral
    for attachment in attachments:
        # Get height
        if 'raw_existing_height_inches' in attachment:
            # If we have already calculated raw height, use it
            attachment_height_inches = attachment['raw_existing_height_inches']
        else:
            # Otherwise, try to parse from the height string
            existing_height_str = attachment.get('existing_height')
            
            # Skip attachments with no height data
            if existing_height_str in (None, '', 'N/A'):
                logger.warning(f"Skipping attachment with missing height: {attachment.get('description')}")
                continue
                
            # Try to extract inches value from format like "34'-2\""
            feet_inches_match = re.search(r'(\d+)\'(?:-)?(\d+)"', str(existing_height_str))
            if feet_inches_match:
                feet = int(feet_inches_match.group(1))
                inches = int(feet_inches_match.group(2))
                attachment_height_inches = (feet * 12) + inches
            else:
                # Try direct conversion from number
                from make_ready_processor import process_wire_height
                attachment_height_inches = process_wire_height({'_measured_height': existing_height_str})
                
        if attachment_height_inches is None:
            logger.warning(f"Could not parse height for attachment: {attachment.get('description')}")
            continue
        
        # Check if we've already processed this attachment (by trace_id)
        trace_id = attachment.get('trace_id')
        if trace_id and trace_id in processed_attachment_trace_ids:
            logger.info(f"Skipping duplicate attachment with trace_id {trace_id}")
            continue
        
        # Add to processed set if trace_id exists
        if trace_id:
            processed_attachment_trace_ids.add(trace_id)
        
        # Check if this attachment is below the neutral wire
        if attachment_height_inches <= neutral_height:
            logger.info(f"Attachment below neutral: {attachment.get('description')} at {attachment_height_inches} inches (neutral at {neutral_height} inches)")
            attachments_below_neutral.append(attachment)
        else:
            logger.info(f"Attachment at or above neutral: {attachment.get('description')} at {attachment_height_inches} inches")
    
    return attachments_below_neutral

def inches_to_feet_inches_str(inches):
    """
    Convert inches to feet-inches string format.
    This duplicates the function from make_ready_processor.py for independence.
    
    Args:
        inches: The height in inches
        
    Returns:
        str: Height formatted as "feet'-inches\""
    """
    if inches is None:
        return 'N/A'
    try:
        inches = float(inches)
        feet = int(inches // 12)
        rem_inches = int(round(inches % 12))
        return f"{feet}'-{rem_inches}\""
    except Exception:
        return 'N/A'

def visualize_pole_attachments(pole_data, neutral_height=None):
    """
    Create a text-based visualization of pole attachments and neutral line.
    
    Args:
        pole_data: Processed pole data dictionary
        neutral_height: Height of the neutral line in inches (optional)
    """
    pole_number = pole_data.get('pole_number', 'Unknown')
    logger.info(f"\nPole Visualization for {pole_number}\n" + "="*50)
    
    # Get all attachments with heights
    attachments = []
    for attacher in pole_data.get('attachers', []):
        existing_height_str = attacher.get('existing_height')
        
        # Skip attachments with no height data
        if existing_height_str in (None, '', 'N/A'):
            continue
            
        # Try to extract inches value from format like "34'-2\""
        feet_inches_match = re.search(r'(\d+)\'(?:-)?(\d+)"', str(existing_height_str))
        if feet_inches_match:
            feet = int(feet_inches_match.group(1))
            inches = int(feet_inches_match.group(2))
            attachment_height_inches = (feet * 12) + inches
        else:
            # Try direct conversion from number
            from make_ready_processor import process_wire_height
            attachment_height_inches = process_wire_height({'_measured_height': existing_height_str})
            
        if attachment_height_inches is not None:
            attachments.append({
                'description': attacher.get('description', 'Unknown'),
                'height': attachment_height_inches,
                'height_str': existing_height_str
            })
    
    # Sort attachments by height (highest to lowest)
    attachments.sort(key=lambda a: a['height'], reverse=True)
    
    # Create the visualization
    max_desc_len = max([len(a['description']) for a in attachments] + [0]) + 5
    
    for attachment in attachments:
        line = f"{attachment['height']:6.1f} in ({attachment['height_str']:>8}) | "
        line += attachment['description'].ljust(max_desc_len)
        
        # Mark if this is at the neutral height
        if neutral_height and abs(attachment['height'] - neutral_height) < 0.1:
            line += " [NEUTRAL]"
            
        logger.info(line)
        
        # Draw neutral line if we're crossing it
        if neutral_height and attachment['height'] < neutral_height and attachments[0]['height'] > neutral_height:
            neutral_line = f"{neutral_height:6.1f} in | " + "-"*max_desc_len + " [NEUTRAL LINE]"
            logger.info(neutral_line)
    
    logger.info("="*50) 
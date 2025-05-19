# neutral_identification.py
"""
Module for neutral wire identification and height normalization.

This module provides functions to identify neutral wires across different data sources
(Katapult and SPIDAcalc) and normalize height values for consistent comparison.
"""

import re
import logging
from utils import inches_to_feet_inches_str
from wire_utils import process_wire_height
from trace_utils import get_trace_by_id, extract_wire_metadata

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
    r'power\s+line',        # Additional patterns
    r'primary',             # Primary wires are typically at neutral height or above
    r'supply\s+line',
    r'open\s+wire',
    r'transmission',
    r'distribution',
    r'high\s+voltage',
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
    Identify neutral wires from Katapult data.
    
    Args:
        pole_data (dict): Pole data dictionary containing photos and attachers
        katapult (dict): The full Katapult JSON data
        
    Returns:
        list: List of identified neutral wire dictionaries
    """
    neutral_wires = []
    
    # Process photos in pole data
    for photo_id, photo in pole_data.get('photos', {}).items():
        photofirst_data = photo.get('photofirst_data', {})
        
        # Process wire data (may be list or dictionary)
        wire_data = photofirst_data.get('wire', {})
        wire_items = []
        
        if isinstance(wire_data, list):
            wire_items = wire_data
        elif isinstance(wire_data, dict):
            wire_items = list(wire_data.values())
        
        for wire in wire_items:
            if not isinstance(wire, dict):
                continue
            
            # Get trace ID from wire
            trace_id = wire.get('_trace', '')
            if not trace_id:
                continue
            
            # Look up trace data
            trace = get_trace_by_id(katapult, trace_id)
            if not trace:
                continue
            
            # Extract metadata
            wire_meta = extract_wire_metadata(wire, trace)
            owner = wire_meta['owner']
            cable_type = wire_meta['cable_type']
            
            # Check if this is a neutral wire
            is_neutral = False
            
            # Check cable type for neutral indicators
            if isinstance(cable_type, str):
                cable_type_lower = cable_type.lower()
                if 'neutral' in cable_type_lower:
                    is_neutral = True
            
            # Check trace data for neutral indicators
            if not is_neutral and isinstance(trace, dict):
                trace_cable_type = trace.get('cable_type', '').lower()
                if 'neutral' in trace_cable_type:
                    is_neutral = True
                
                # Check usage group
                usage_group = trace.get('usageGroup', '').lower()
                if 'neutral' in usage_group:
                    is_neutral = True
            
            if is_neutral:
                # Process wire height
                height_inches = process_wire_height(wire)
                height_str = inches_to_feet_inches_str(height_inches)
                
                # Create neutral wire object
                neutral_wire = {
                    'description': f"{owner} Neutral",
                    'existing_height': height_str,
                    'raw_existing_height_inches': height_inches,
                    'photo_id': photo_id,
                    'wire_id': wire.get('id'),
                    'is_neutral': True
                }
                
                neutral_wires.append(neutral_wire)
    
    return neutral_wires

def identify_neutrals_spidacalc(pole_data, spida_pole_data):
    """
    Identify neutral wires from SPIDAcalc data.
    
    Args:
        pole_data (dict): Pole data dictionary
        spida_pole_data (dict): The SPIDAcalc data for this pole
        
    Returns:
        list: List of identified neutral wire dictionaries
    """
    neutral_wires = []
    
    # Check if SPIDAcalc data is available
    if not spida_pole_data or not isinstance(spida_pole_data, dict):
        return neutral_wires
    
    # Find measured design
    measured_design = None
    for design in spida_pole_data.get('designs', []):
        if design.get('label', '').lower() == 'measured design':
            measured_design = design
            break
    
    if not measured_design:
        return neutral_wires
    
    # Check wires in measured design for neutrals
    for wire in measured_design.get('structure', {}).get('wires', []):
        if not isinstance(wire, dict):
            continue
        
        # Check for neutral indicators
        is_neutral = False
        
        # Check wire description
        description = wire.get('clientItem', {}).get('description', '').lower()
        if 'neutral' in description:
            is_neutral = True
        
        # Check usageGroup
        usage_group = wire.get('usageGroup', '').lower()
        if 'neutral' in usage_group:
            is_neutral = True
        
        if is_neutral:
            # Get owner
            owner = wire.get('owner', {}).get('id', 'Unknown')
            
            # Get height
            height_meters = wire.get('attachmentHeight', {}).get('value')
            height_inches = height_meters * 39.3701 if height_meters is not None else None
            height_str = inches_to_feet_inches_str(height_inches)
            
            # Create neutral wire object
            neutral_wire = {
                'description': f"{owner} Neutral",
                'existing_height': height_str,
                'raw_existing_height_inches': height_inches,
                'wire_id': wire.get('id'),
                'is_neutral': True,
                'source': 'spidacalc'
            }
            
            neutral_wires.append(neutral_wire)
    
    return neutral_wires

def get_highest_neutral(neutral_wires):
    """
    Find the highest neutral wire from a list of neutral wires.
    
    Args:
        neutral_wires (list): List of neutral wire dictionaries
        
    Returns:
        dict: The highest neutral wire or None if no neutrals found
    """
    if not neutral_wires:
        return None
    
    highest_neutral = neutral_wires[0]
    highest_height = highest_neutral.get('raw_existing_height_inches', 0) or 0
    
    for neutral in neutral_wires[1:]:
        height = neutral.get('raw_existing_height_inches', 0) or 0
        if height > highest_height:
            highest_neutral = neutral
            highest_height = height
    
    return highest_neutral

def identify_attachments_below_neutral(pole_data, highest_neutral, katapult, spida_pole_data):
    """
    Identify attachments that are below the highest neutral wire.
    
    Args:
        pole_data (dict): Pole data dictionary
        highest_neutral (dict): The highest neutral wire
        katapult (dict): The full Katapult JSON data
        spida_pole_data (dict): The SPIDAcalc data for this pole
        
    Returns:
        list: List of attachments below the highest neutral
    """
    attachments_below_neutral = []
    
    # If no neutral found, return empty list
    if not highest_neutral:
        logger.warning(f"No neutral wire found for pole {pole_data.get('pole_number', 'Unknown')}")
        return attachments_below_neutral
    
    neutral_height = highest_neutral.get('raw_existing_height_inches', 0) or 0
    logger.info(f"Neutral wire found at height {inches_to_feet_inches_str(neutral_height)} for pole {pole_data.get('pole_number', 'Unknown')}")
    
    # Process attachers from pole data
    skipped_attachments = []
    for attacher in pole_data.get('attachers', []):
        # Skip if not a dictionary or has no height
        if not isinstance(attacher, dict):
            continue
        
        # Skip reference headers
        if attacher.get('type', '') in ['reference_header', 'backspan_header']:
            continue
        
        # Prefer existing height, else fallback to proposed height for new installs
        height_inches = attacher.get('raw_existing_height_inches')
        if height_inches is None:
            height_inches = attacher.get('raw_proposed_height_inches')
        if height_inches is None:
            continue
        
        description = attacher.get('description', 'Unknown')
        
        if height_inches < neutral_height:
            # This attachment is below the neutral
            logger.info(f"Including attachment below neutral: {description} at height {inches_to_feet_inches_str(height_inches)}")
            attachments_below_neutral.append(attacher)
        else:
            # Log attachments that are above or at the neutral height
            logger.info(f"Skipping attachment above/at neutral: {description} at height {inches_to_feet_inches_str(height_inches)}")
            skipped_attachments.append({
                'description': description,
                'height': inches_to_feet_inches_str(height_inches)
            })
    
    # Log skipped attachments
    if skipped_attachments:
        logger.info(f"Skipped {len(skipped_attachments)} attachments above/at neutral height for pole {pole_data.get('pole_number', 'Unknown')}")
        for skipped in skipped_attachments:
            logger.debug(f"  - {skipped['description']} at {skipped['height']}")
    
    # Add SPIDAcalc attachments below neutral if available
    if spida_pole_data:
        spida_attachments_below_neutral = identify_spida_attachments_below_neutral(
            spida_pole_data, neutral_height)
        
        # Merge with Katapult attachments
        for spida_attachment in spida_attachments_below_neutral:
            # Check if this attachment is already in the list by comparing description and height
            is_duplicate = False
            for att in attachments_below_neutral:
                if (att.get('description') == spida_attachment.get('description') and
                    abs((att.get('raw_existing_height_inches') or 0) - 
                        (spida_attachment.get('raw_existing_height_inches') or 0)) < 5):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                logger.info(f"Adding SPIDAcalc attachment below neutral: {spida_attachment.get('description')} at height {spida_attachment.get('existing_height')}")
                attachments_below_neutral.append(spida_attachment)
    
    # Sort attachments by height (descending)
    attachments_below_neutral.sort(
        key=lambda x: x.get('raw_existing_height_inches', 0) or 0,
        reverse=True
    )
    
    logger.info(f"Found {len(attachments_below_neutral)} attachments below neutral for pole {pole_data.get('pole_number', 'Unknown')}")
    
    return attachments_below_neutral

def identify_spida_attachments_below_neutral(spida_pole_data, neutral_height):
    """
    Identify attachments below neutral height in SPIDAcalc data.
    
    Args:
        spida_pole_data (dict): The SPIDAcalc data for this pole
        neutral_height (float): Height of the neutral wire in inches
        
    Returns:
        list: List of attachments below neutral
    """
    attachments = []
    
    # Find measured design
    measured_design = None
    for design in spida_pole_data.get('designs', []):
        if design.get('label', '').lower() == 'measured design':
            measured_design = design
            break
    
    if not measured_design:
        return attachments
    
    # Process wires
    for wire in measured_design.get('structure', {}).get('wires', []):
        if not isinstance(wire, dict):
            continue
        
        # Skip neutrals (already processed)
        description = wire.get('clientItem', {}).get('description', '').lower()
        usage_group = wire.get('usageGroup', '').lower()
        if 'neutral' in description or 'neutral' in usage_group:
            continue
        
        # Get height
        height_meters = wire.get('attachmentHeight', {}).get('value')
        if height_meters is None:
            continue
            
        height_inches = height_meters * 39.3701
        
        # Compare with neutral height
        if height_inches < neutral_height:
            owner = wire.get('owner', {}).get('id', 'Unknown')
            desc = wire.get('clientItem', {}).get('description', '')
            
            attachment = {
                'description': f"{owner} {desc}".strip(),
                'existing_height': inches_to_feet_inches_str(height_inches),
                'proposed_height': 'N/A',
                'midspan_proposed': 'N/A',
                'raw_existing_height_inches': height_inches,
                'source': 'spidacalc'
            }
            
            attachments.append(attachment)
    
    # Process equipment
    for equipment in measured_design.get('structure', {}).get('equipments', []):
        if not isinstance(equipment, dict):
            continue
        
        # Get height
        height_meters = equipment.get('attachmentHeight', {}).get('value')
        if height_meters is None:
            continue
            
        height_inches = height_meters * 39.3701
        
        # Compare with neutral height
        if height_inches < neutral_height:
            owner = equipment.get('owner', {}).get('id', 'Unknown')
            eq_type = equipment.get('clientItem', {}).get('type', '')
            
            attachment = {
                'description': f"{owner} {eq_type}".strip(),
                'existing_height': inches_to_feet_inches_str(height_inches),
                'proposed_height': 'N/A',
                'midspan_proposed': 'N/A',
                'raw_existing_height_inches': height_inches,
                'source': 'spidacalc'
            }
            
            attachments.append(attachment)
    
    return attachments

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
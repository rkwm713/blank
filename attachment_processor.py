# attachment_processor.py
import logging
from utils import meters_to_feet_inches_str, normalize_owner, inches_to_feet_inches_str
from trace_utils import get_trace_by_id, extract_wire_metadata
from wire_utils import process_wire_height

logger = logging.getLogger(__name__)

# Helper: normalize Charter/Spectrum and other descriptions
def normalize_charter(desc):
    """
    Normalize wire and equipment descriptions to match expected format.
    Handles Charter/Spectrum and other special cases.
    """
    desc = desc or ''
    desc_lower = desc.lower()
    
    # Handle Charter/Spectrum case
    if 'charter' in desc_lower or 'spectrum' in desc_lower:
        return 'Charter/Spectrum'
    
    # Handle Fiber Optic formatting
    if 'fiber' in desc_lower and 'optic' not in desc_lower:
        desc = desc.replace('Fiber', 'Fiber Optic').replace('fiber', 'Fiber Optic')
    
    # Handle AT&T Comm/Com variations
    if 'at&t' in desc_lower or 'att' in desc_lower:
        if 'telco' in desc_lower:
            return 'Telco Com'
        elif 'drop' in desc_lower:
            return 'Com Drop'
        elif 'fiber' in desc_lower:
            return 'Fiber Optic Com'
        elif 'com' in desc_lower:
            return 'Com'  # General case
    
    # Handle CPS Energy specific names
    if ('cps' in desc_lower or 'energy' in desc_lower) and 'fiber' in desc_lower:
        return 'Supply Fiber'
    
    # No special case matched, return as is
    return desc

def process_katapult_attachments(node, katapult):
    """
    Process attachments from Katapult node data.
    
    Args:
        node (dict): Node data from Katapult
        katapult (dict): Full Katapult data
        
    Returns:
        dict: Dictionary mapping attachment description to attachment data
    """
    attacher_map = {}
    
    # Process each photo in the node
    for photo_id, photo in node.get('photos', {}).items():
        # Skip invalid photos
        if not isinstance(photo, dict):
            logger.debug(f"Skipping non-dict photo in node photos: {photo}")
            continue
            
        # Check if photofirst_data exists and is a dictionary
        photofirst_data = photo.get('photofirst_data', {})
        if not isinstance(photofirst_data, dict):
            logger.debug(f"Skipping node photo with invalid photofirst_data: {photofirst_data}")
            continue
        
        # Process wire data
        wire_data = photofirst_data.get('wire', [])
        if not wire_data:
            logger.debug(f"No wire data found in photo {photo_id}")
            continue
            
        # Handle wire data as either list or dictionary
        wire_items = []
        if isinstance(wire_data, list):
            wire_items = wire_data
        elif isinstance(wire_data, dict):
            wire_items = wire_data.values()
        else:
            logger.debug(f"Unexpected wire data type: {type(wire_data)}")
            continue
            
        # Process each wire
        for wire in wire_items:
            if not isinstance(wire, dict):
                logger.debug(f"Skipping non-dict wire: {wire}")
                continue
                
            # Get trace ID and data
            trace_id = wire.get('_trace', '')
            if not trace_id:
                logger.debug(f"Wire missing _trace ID")
                continue
            
            trace = get_trace_by_id(katapult, trace_id.strip())
            
            # Extract metadata
            wire_meta = extract_wire_metadata(wire, trace)
            owner = wire_meta['owner']
            cable_type = wire_meta['cable_type']
            is_proposed = wire_meta['is_proposed']
            
            # Format the description using the standard function
            formatted_desc = format_attacher_description(owner, cable_type)
            
            # Process height data
            existing_height = wire.get('_measured_height')
            if not existing_height:
                logger.debug(f"Wire missing _measured_height")
                continue
                
            try:
                existing_height_float = float(existing_height)
                
                # Check if we already have this attachment with the exact same formatting
                current_height = 0
                if formatted_desc in attacher_map and isinstance(attacher_map[formatted_desc], dict):
                    current_height = attacher_map[formatted_desc].get('raw_existing_height_inches', 0)
                
                # Only add or update if this is a new attachment or has a greater height
                if formatted_desc not in attacher_map or existing_height_float > current_height:
                    proposed_height_val = 'N/A'
                    midspan_proposed_val = 'N/A'
                    
                    # If wire is explicitly marked as proposed, set its proposed height
                    if is_proposed:
                        proposed_height_val = inches_to_feet_inches_str(existing_height_float)
                        
                    attacher_map[formatted_desc] = {
                        'description': formatted_desc,
                        'existing_height': inches_to_feet_inches_str(existing_height),
                        'raw_existing_height_inches': existing_height_float,
                        'proposed_height': proposed_height_val,
                        'midspan_proposed': midspan_proposed_val, 
                        'is_proposed': is_proposed,
                    }
            except (ValueError, TypeError) as e:
                logger.debug(f"Error converting height '{existing_height}' to float: {str(e)}")
    
    return attacher_map

def process_spidacalc_attachments(spida_pole_data, norm_pole_number=None):
    """
    Process attachments from SPIDAcalc pole data, including measured and recommended designs, wires and equipment, with underground and Charter/Spectrum normalization.
    """
    if not spida_pole_data:
        return {}

    # Helper: detect underground
    def is_underground(desc, cable_type):
        d = (desc or '').lower()
        c = (cable_type or '').lower()
        return (
            'underground' in d or 'underground' in c or
            'ug' in d or 'ug' in c or
            'riser' in d or 'riser' in c or
            'vertical' in d or 'vertical' in c
        )

    # Find measured and recommended designs
    measured_design = None
    recommended_design = None
    for design in spida_pole_data.get('designs', []):
        if design.get('label', '').lower() == 'measured design':
            measured_design = design
        elif design.get('label', '').lower() == 'recommended design':
            recommended_design = design

    # If no designs found, return empty dict
    if not measured_design and not recommended_design:
        return {}

    # Build dict of all attachments (keyed by normalized owner/desc/type)
    attachments = {}

    # Helper for key
    def make_key(owner, desc, cable_type=None):
        owner_norm = normalize_owner(owner)
        desc_norm = normalize_charter(desc)
        if cable_type:
            return f"{owner_norm}||{desc_norm}||{cable_type.strip().lower()}"
        return f"{owner_norm}||{desc_norm}"

    # --- Process measured design (existing) ---
    measured_wires = {}
    if measured_design:
        for wire in measured_design.get('structure', {}).get('wires', []):
            owner = wire.get('owner', {}).get('id', '')
            desc = wire.get('clientItem', {}).get('description', '')
            cable_type = wire.get('clientItem', {}).get('type', '')
            usage_group = wire.get('usageGroup', '')
            id_str = wire.get('id', '')
            meters = wire.get('attachmentHeight', {}).get('value')
            midspan_meters = wire.get('midspanHeight', {}).get('value')

            key = make_key(owner, desc, cable_type)
            underground = is_underground(desc, cable_type)

            measured_wires[key] = {
                'description': format_attacher_description(owner, desc),
                'existing_height': meters_to_feet_inches_str(meters),
                'proposed_height': 'N/A',
                'midspan_proposed': 'UG' if underground else 'N/A',
                'raw_existing_height_inches': float(meters) * 39.3701 if meters is not None else 0,
                'raw_existing_midspan_inches': float(midspan_meters) * 39.3701 if midspan_meters is not None else 0,
                'existing_midspan_height': meters_to_feet_inches_str(midspan_meters) if midspan_meters is not None else 'N/A',
                'wire_id': id_str,
                'usage_group': usage_group,
                'is_underground': underground,
            }
            attachments[key] = measured_wires[key]

        # Equipment (e.g., risers, transformers)
        for eq in measured_design.get('structure', {}).get('equipments', []):
            owner = eq.get('owner', {}).get('id', '')
            desc = eq.get('clientItem', {}).get('description', '') or eq.get('clientItem', {}).get('type', '')
            cable_type = eq.get('clientItem', {}).get('type', '')
            id_str = eq.get('id', '')
            meters = eq.get('attachmentHeight', {}).get('value')
            underground = is_underground(desc, cable_type)
            key = make_key(owner, desc, cable_type)
            attachments[key] = {
                'description': format_attacher_description(owner, desc),
                'existing_height': meters_to_feet_inches_str(meters),
                'proposed_height': 'N/A',
                'midspan_proposed': 'UG' if underground else 'N/A',
                'raw_existing_height_inches': float(meters) * 39.3701 if meters is not None else 0,
                'wire_id': id_str,
                'is_underground': underground,
            }

    # --- Process recommended design (proposed) ---
    if recommended_design:
        for wire in recommended_design.get('structure', {}).get('wires', []):
            owner = wire.get('owner', {}).get('id', '')
            desc = wire.get('clientItem', {}).get('description', '')
            cable_type = wire.get('clientItem', {}).get('type', '')
            usage_group = wire.get('usageGroup', '')
            id_str = wire.get('id', '')
            meters = wire.get('attachmentHeight', {}).get('value')
            underground = is_underground(desc, cable_type)
            key = make_key(owner, desc, cable_type)

            # If this key exists in measured, it's a move or unchanged; else, it's new
            if key in attachments:
                # Existing attachment, check for move
                existing = attachments[key]
                existing_height = existing.get('existing_height', 'N/A')
                proposed_height = meters_to_feet_inches_str(meters)
                # If height changed, it's a move
                if existing_height != proposed_height:
                    existing['proposed_height'] = proposed_height
                # Underground status: if either is UG, mark as UG
                if underground or existing.get('is_underground'):
                    existing['midspan_proposed'] = 'UG'
            else:
                # New install
                attachments[key] = {
                    'description': format_attacher_description(owner, desc),
                    'existing_height': 'N/A',
                    'proposed_height': meters_to_feet_inches_str(meters),
                    'midspan_proposed': 'UG' if underground else 'N/A',
                    'raw_proposed_height_inches': float(meters) * 39.3701 if meters is not None else 0,
                    'wire_id': id_str,
                    'is_underground': underground,
                }

        for eq in recommended_design.get('structure', {}).get('equipments', []):
            owner = eq.get('owner', {}).get('id', '')
            desc = eq.get('clientItem', {}).get('description', '') or eq.get('clientItem', {}).get('type', '')
            cable_type = eq.get('clientItem', {}).get('type', '')
            id_str = eq.get('id', '')
            meters = eq.get('attachmentHeight', {}).get('value')
            underground = is_underground(desc, cable_type)
            key = make_key(owner, desc, cable_type)
            if key in attachments:
                existing = attachments[key]
                existing_height = existing.get('existing_height', 'N/A')
                proposed_height = meters_to_feet_inches_str(meters)
                if existing_height != proposed_height:
                    existing['proposed_height'] = proposed_height
                if underground or existing.get('is_underground'):
                    existing['midspan_proposed'] = 'UG'
            else:
                attachments[key] = {
                    'description': format_attacher_description(owner, desc),
                    'existing_height': 'N/A',
                    'proposed_height': meters_to_feet_inches_str(meters),
                    'midspan_proposed': 'UG' if underground else 'N/A',
                    'raw_proposed_height_inches': float(meters) * 39.3701 if meters is not None else 0,
                    'wire_id': id_str,
                    'is_underground': underground,
                }

    return attachments

def consolidate_attachments(spida_attachments, katapult_attachments):
    """
    Consolidate and deduplicate attachments from SPIDAcalc and Katapult.
    
    Args:
        spida_attachments (dict): SPIDAcalc attachments
        katapult_attachments (dict): Katapult attachments
        
    Returns:
        list: Consolidated list of attachment dictionaries
    """
    # Start with SPIDAcalc attachments if available
    if spida_attachments:
        # Remove duplicate entries (same description)
        unique_attachments = {}
        attachment_keys_by_description = {}
        
        # First, group by description
        for key, value in spida_attachments.items():
            if isinstance(value, dict) and 'description' in value:
                desc = value['description']
                if desc not in attachment_keys_by_description:
                    attachment_keys_by_description[desc] = []
                attachment_keys_by_description[desc].append(key)
        
        # Then select the best data for each description
        for desc, keys in attachment_keys_by_description.items():
            best_key = keys[0]  # Default to first key
            
            # Prefer keys where both existing and proposed heights exist
            for key in keys:
                value = spida_attachments[key]
                if (value.get('existing_height', 'N/A') != 'N/A' and 
                    value.get('proposed_height', 'N/A') != 'N/A'):
                    best_key = key
                    break
            
            unique_attachments[desc] = spida_attachments[best_key]
        
        consolidated = unique_attachments
    else:
        # No SPIDAcalc attachments, use Katapult only
        consolidated = katapult_attachments
    
    # -------------------------------------------------------------
    # 2025-05-22: Preserve per-wire mid-span value for MOVED
    # attachments.
    # If an attachment exists in both SPIDAcalc and Katapult datasets
    # and the SPIDA entry shows a *move* (existing & proposed heights
    # differ) but midspan_proposed is still 'N/A', copy the
    # midspan_proposed value from the corresponding Katapult record
    # (when it is a concrete number or 'UG').
    # -------------------------------------------------------------
    for desc, spida_att in consolidated.items():
        if desc in katapult_attachments:
            kat_att = katapult_attachments[desc]
            if not isinstance(spida_att, dict) or not isinstance(kat_att, dict):
                continue

            existing_h = spida_att.get('existing_height', 'N/A')
            proposed_h = spida_att.get('proposed_height', 'N/A')
            has_move = (
                existing_h not in (None, '', 'N/A') and
                proposed_h not in (None, '', 'N/A') and
                existing_h != proposed_h
            )

            # Only overwrite if attachment moved and SPIDA midspan is empty
            if has_move and spida_att.get('midspan_proposed', 'N/A') in (None, '', 'N/A'):
                kat_midspan = kat_att.get('midspan_proposed', 'N/A')
                if kat_midspan not in (None, '', 'N/A'):
                    spida_att['midspan_proposed'] = kat_midspan
                    # Also keep raw midspan inches if available for later logic
                    if 'raw_existing_midspan_inches' in kat_att:
                        spida_att['raw_existing_midspan_inches'] = kat_att['raw_existing_midspan_inches']
    
    # Convert to list form
    attacher_list = []
    for desc, attachment in consolidated.items():
        if isinstance(attachment, dict):
            attacher_list.append(attachment)
    
    # Sort by height (descending)
    sorted_attachers = sorted(
        attacher_list,
        key=lambda x: (x.get('raw_existing_height_inches') or 0),
        reverse=True
    )
    
    return sorted_attachers

def identify_owners_with_changes(attachers):
    """
    Identify owners with attachment height changes.
    
    Args:
        attachers (list): List of attachment dictionaries
        
    Returns:
        set: Set of owner names with height changes
    """
    owners_with_changes = set()
    
    for attacher in attachers:
        # Check if this attachment has both existing and proposed heights that differ
        if (attacher.get('existing_height', 'N/A') != 'N/A' and 
            attacher.get('proposed_height', 'N/A') != 'N/A' and
            attacher.get('existing_height') != attacher.get('proposed_height')):
            
            # Extract owner from description
            owner_parts = attacher.get('description', '').split(' ', 1)
            owner = owner_parts[0] if owner_parts else ''
            
            # Normalize owner name
            normalized_owner = normalize_owner(owner)
            
            # Add to set
            if normalized_owner:
                owners_with_changes.add(normalized_owner)
                logger.debug(f"Found attachment height change for owner: {normalized_owner}")
        
        # Also check the is_proposed flag
        if attacher.get('is_proposed', False):
            owner_parts = attacher.get('description', '').split(' ', 1)
            owner = owner_parts[0] if owner_parts else ''
            normalized_owner = normalize_owner(owner)
            
            if normalized_owner:
                owners_with_changes.add(normalized_owner)
                logger.debug(f"Found proposed attachment for owner: {normalized_owner}")
    
    return owners_with_changes

def apply_midspan_values(attachers_list, midspan_proposed):
    """Apply midspan values to attachments based on new 2025-05-22 rules."""
    for attacher in attachers_list:
        has_existing = attacher.get('existing_height', 'N/A') not in (None, '', 'N/A')
        has_proposed = attacher.get('proposed_height', 'N/A') not in (None, '', 'N/A')
        moved = has_existing and has_proposed and attacher.get('existing_height') != attacher.get('proposed_height')

        if moved:
            # Keep existing (copied-from-Katapult) midspan or fall back to span-level lowest.
            if attacher.get('midspan_proposed', 'N/A') in (None, '', 'N/A') and midspan_proposed != 'N/A':
                attacher['midspan_proposed'] = midspan_proposed
            continue

        if not has_existing and has_proposed:
            # New install – midspan must be blank (unless UG already present)
            if attacher.get('midspan_proposed', 'N/A') not in ('UG', 'ug'):
                attacher['midspan_proposed'] = 'N/A'
            continue

        # All other cases: leave midspan_proposed as is.

def format_attacher_description(owner, desc):
    """
    Format the complete attacher description by combining owner and description in the proper format.
    
    Args:
        owner (str): The owner of the attachment
        desc (str): The attachment description/type
        
    Returns:
        str: Formatted description string that matches expected output
    """
    # Normalize inputs and ensure they're strings
    owner = str(owner or '').strip()
    desc = str(desc or '').strip()
    owner_lower = owner.lower()
    desc_lower = desc.lower()
    
    # Special case: Neutral is always displayed simply as "Neutral"
    if 'neutral' in desc_lower:
        return "Neutral"
    
    # AT&T descriptions - check multiple variations of AT&T in owner
    if any(att_var in owner_lower for att_var in ['at&t', 'att', 'atandt', 'at and t']):
        if 'telco' in desc_lower:
            return "AT&T Telco Com"
        elif 'drop' in desc_lower:
            return "AT&T Com Drop"
        elif 'fiber' in desc_lower or 'optic' in desc_lower:
            return "AT&T Fiber Optic Com"
        else:
            # Generic AT&T attachment
            return f"AT&T {normalize_charter(desc)}"
    
    # Get normalized owner string for other cases
    normalized_owner = normalize_owner(owner)
    if normalized_owner == 'AT&T':  # Double-check after normalization
        return format_attacher_description('at&t', desc)  # Re-process with known format
    
    # CPS Energy descriptions
    if 'cps' in owner_lower or 'energy' in owner_lower:
        if 'fiber' in desc_lower:
            return "CPS Supply Fiber"
        # Other CPS-specific formats can be added here
    
    # Charter/Spectrum descriptions
    if 'charter' in owner_lower or 'spectrum' in owner_lower or 'charter' in desc_lower or 'spectrum' in desc_lower:
        if 'fiber' in desc_lower or 'optic' in desc_lower:
            return "Charter/Spectrum Fiber Optic"
        else:
            return f"Charter/Spectrum {normalize_charter(desc)}"
    
    # Default case: Combine normalized owner and description
    # Ensure AT&T is displayed correctly in all contexts
    if normalized_owner == 'AT&T':
        normalized_owner = 'AT&T'  # Explicit assignment to ensure correct formatting
            
    return f"{normalized_owner} {normalize_charter(desc)}".strip()
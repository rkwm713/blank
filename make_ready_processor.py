# make_ready_processor.py
import json
import logging

# Import utility modules
from trace_utils import get_trace_by_id, extract_wire_metadata
from utils import normalize_pole_id, inches_to_feet_inches_str, extract_string_value
from data_loader import load_katapult_data, load_spidacalc_data, build_spida_lookups, filter_target_poles
from pole_attribute_processor import extract_pole_attributes_katapult, extract_spida_pole_attributes, resolve_pole_attribute_conflicts, extract_notes
from attachment_processor import process_katapult_attachments, process_spidacalc_attachments, consolidate_attachments, identify_owners_with_changes
from connection_processor import process_pole_connections
from spida_utils import check_proposed_riser_spida, check_proposed_guy_spida, check_proposed_equipment_in_notes, get_construction_grade_spida, get_pole_sequence_from_spidacalc, filter_primary_operation_poles
from reference_utils import deduplicate_attachments
import neutral_identification as ni
import debug_logging
from wire_utils import parse_feet_inches_str_to_inches as feet_inches_str_to_inches

# Configure logging
logger = logging.getLogger(__name__)

def process_make_ready_report(katapult_path, spidacalc_path=None, target_poles=None, 
                             attachment_height_strategy='PREFER_KATAPULT', 
                             pole_attribute_strategy='PREFER_KATAPULT'):
    """
    Process Katapult and optional SPIDAcalc JSON files to generate a Make-Ready report.
    
    Args:
        katapult_path (str): Path to the Katapult JSON file
        spidacalc_path (str, optional): Path to the SPIDAcalc JSON file
        target_poles (list, optional): List of pole numbers to process. If provided, only these poles will be processed.
        attachment_height_strategy (str, optional): Strategy for resolving attachment height conflicts
        pole_attribute_strategy (str, optional): Strategy for resolving pole attribute conflicts
        
    Returns:
        list: List of processed pole data dictionaries, ordered according to their appearance in the SPIDAcalc file
    """
    # Set up logging
    logger = debug_logging.get_processing_logger()
    
    # Load data
    katapult = load_katapult_data(katapult_path)
    spida = load_spidacalc_data(spidacalc_path)
    
    # Build lookups
    spida_lookup, spida_wire_lookup, spida_pole_order = build_spida_lookups(spida)
    
    # Process target poles
    normalized_target_poles = filter_target_poles(target_poles)
    
    # Get pole sequence for backspan identification
    pole_sequence = get_pole_sequence_from_spidacalc(spida)
    
    # Build reconciliation map between SPIDAcalc and Katapult poles
    pole_map = {}
    
    # --- Build a map of normalized pole numbers to their SPIDAcalc order (sequence) ---
    sequence_map = {}
    if spida and spida_pole_order:
        for idx, pole_id in enumerate(spida_pole_order, start=1):
            sequence_map[pole_id] = idx

    # Process each pole
    poles = []
    for node_id, node in katapult.get('nodes', {}).items():
        try:
            # Check if this is a pole type
            if not is_pole_node(node):
                logger.debug(f"Skipping non-pole node {node_id}")
                continue
            
            # Get attributes
            attributes = node.get('attributes', {})
            if not isinstance(attributes, dict):
                logger.warning(f"Warning: attributes is not a dict for node {node_id}")
                attributes = {}
            
            # Extract pole attributes
            pole_attrs = extract_pole_attributes_katapult(node, attributes)
            pole_number = pole_attrs['pole_number']
            norm_pole_number = pole_attrs['norm_pole_number']
            
            # Skip if no pole number
            if not pole_number:
                logger.debug(f"Skipping node {node_id} - no pole number found")
                continue
            
            # Skip if not in target list
            if normalized_target_poles and norm_pole_number not in normalized_target_poles:
                logger.debug(f"Skipping pole {pole_number} - not in target list")
                continue
            
            # Initialize entry in pole map - all poles start as non-primary
            if norm_pole_number not in pole_map:
                pole_map[norm_pole_number] = {
                    "katapult_node_id": node_id,
                    "spida_obj": None,
                    "is_primary": False  # Default to False, will update for SPIDAcalc poles
                }
            
            # Get SPIDAcalc pole data if available
            spida_pole_data = None
            if spida and norm_pole_number in spida_lookup:
                spida_pole_data = spida_lookup[norm_pole_number]
                # Mark as having SPIDAcalc data in the pole map
                pole_map[norm_pole_number]["spida_obj"] = spida_pole_data
                
                # Extract SPIDAcalc pole attributes
                # spida_attrs is not directly needed here if we pass spida_pole_data and spida (full_spida_data)
                # spida_attrs = extract_spida_pole_attributes(spida_pole_data) 
                
                # Resolve conflicts between Katapult and SPIDAcalc attributes
                # Pass spida_pole_data for the specific pole and spida for the full SPIDA dataset
                pole_attrs = resolve_pole_attribute_conflicts(pole_attrs, spida_pole_data, spida, pole_attribute_strategy)
            
            # Process attachments
            katapult_attachments = process_katapult_attachments(node, katapult)
            spida_attachments = process_spidacalc_attachments(spida_pole_data, norm_pole_number) if spida_pole_data else {}
            
            # Consolidate attachments and identify owners with changes
            attachers_list = consolidate_attachments(spida_attachments, katapult_attachments)
            owners_with_attachment_changes = identify_owners_with_changes(attachers_list)
            
            # Process connections and midspan data
            pole_connections, midspan_data, reference_spans, backspan = process_pole_connections(
                node_id, pole_number, katapult, pole_sequence
            )
            
            # Extract lowest midspan heights for all spans from this pole
            midspan_heights = extract_lowest_midspan_heights(node_id, katapult)
            
            # Process neutral wires
            neutral_result = process_neutral_wires(node, katapult, spida_pole_data, attachers_list)
            attachments_below_neutral = neutral_result['attachments_below_neutral']
            
            # Count proposed risers and guys for columns F/G
            riser_count, guy_count = count_proposed_riser_guy(node, katapult, spida_pole_data)
            proposed_riser = f"YES ({riser_count})" if riser_count > 0 else "NO"
            proposed_guy = f"YES ({guy_count})" if guy_count > 0 else "NO"
            
            # Calculate midspan proposed value
            midspan_proposed = calculate_midspan_proposed(
                pole_connections, 
                owners_with_attachment_changes, 
                katapult, 
                attachers_list
            )
            
            # Apply midspan values to attachments (apply to both lists)
            apply_midspan_values(
                attachers_list, 
                midspan_proposed
            )
            apply_midspan_values(
                attachments_below_neutral,
                midspan_proposed
            )
            
            # Build final attachers list with reference spans
            final_attachers_list = build_final_attachers_list(
                attachments_below_neutral,  # Changed: Use filtered attachments below neutral
                reference_spans, 
                backspan
            )
            
            # Determine pole-level attachment action for Column B
            pole_action = determine_pole_action(final_attachers_list)
            
            # Determine pole status
            pole_status = determine_pole_status(attributes, pole_attrs)
            
            # Assign operation number based on SPIDAcalc order (if available)
            operation_number = sequence_map.get(norm_pole_number)
            
            # Build the complete pole data structure
            pole = {
                'pole_owner': pole_attrs['pole_owner'] or 'N/A',
                'pole_number': pole_number or 'N/A',
                'pole_structure': pole_attrs['pole_structure'] or 'N/A',
                'proposed_riser': proposed_riser,
                'proposed_guy': proposed_guy,
                'pla_percentage': pole_attrs['pla_percentage'],
                'construction_grade': pole_attrs['construction_grade'] or 'N/A',
                'existing_midspan_lowest_com': midspan_data['existing_midspan_lowest_com'],
                'existing_midspan_lowest_cps_electrical': midspan_data['existing_midspan_lowest_cps_electrical'],
                'midspan_proposed': midspan_proposed,
                'from_pole': midspan_data['from_pole'] or 'N/A',
                'to_pole': midspan_data['to_pole'] or 'N/A',
                'connections': pole_connections,
                'attachers': final_attachers_list,
                'attachments_below_neutral': attachments_below_neutral,
                'pole_action': pole_action,
                'latitude': node.get('latitude'),
                'longitude': node.get('longitude'),
                'status': pole_status,
                'operation_number': operation_number,
                'midspan_heights': midspan_heights,  # For Excel J/K
                'norm_pole_number': norm_pole_number,  # For filtering later
            }
            
            poles.append(pole)
            
        except Exception as e:
            logger.error(f"Error processing node {node_id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise  # Re-raise the exception after logging
    
    # Identify primary operation poles (those that should be in SPIDAcalc)
    primary_poles = filter_primary_operation_poles(pole_map)
    
    # Apply the is_primary flag to each pole in the results
    for pole in poles:
        norm_id = pole.get('norm_pole_number')
        if norm_id in primary_poles:
            pole['is_primary'] = True
        else:
            pole['is_primary'] = False
    
    # Sort poles according to SPIDAcalc order if available
    if spida and spida_pole_order:
        poles.sort(key=lambda pole: sequence_map.get(normalize_pole_id(pole.get('pole_number')), float('inf')))
    
    return poles

def is_pole_node(node):
    """Check if a node represents a pole."""
    # Check button type
    button = node.get('button', '')
    valid_pole_types = ['aerial', 'pole', 'aerial_path']
    
    if button in valid_pole_types:
        return True
    
    # Check node_type attribute
    node_type = node.get('attributes', {}).get('node_type', {})
    node_type_value = None
    
    if isinstance(node_type, dict):
        node_type_value = node_type.get('-Imported') or node_type.get('button_added')
    else:
        node_type_value = node_type
    
    if node_type_value == 'pole':
        return True
    
    return False

def process_neutral_wires(node, katapult, spida_pole_data, attachers_list):
    """Process neutral wires and identify attachments below neutral."""
    import logging
    logger = logging.getLogger('neutral_processing')
    
    # Get pole number for logging
    attributes = node.get('attributes', {})
    pole_number = None
    for attr in ['pole_number', 'PoleNumber', 'pl_number', 'pole_tag']:
        if attr in attributes:
            pole_number = attributes.get(attr)
            if pole_number:
                break
    
    if not pole_number:
        pole_number = node.get('id', 'Unknown')[:8]  # Use truncated node ID if no pole number
    
    logger.info(f"Processing neutral wires for pole {pole_number}")
    
    # Prepare data for neutral identification
    temp_pole_data = {
        'pole_number': pole_number,
        'photos': node.get('photos', {}),
        'attachers': attachers_list
    }
    
    # Identify neutral wires
    neutral_wires_katapult = ni.identify_neutrals_katapult(temp_pole_data, katapult)
    logger.info(f"Found {len(neutral_wires_katapult)} neutral wires from Katapult")
    
    neutral_wires_spida = []
    if spida_pole_data:
        neutral_wires_spida = ni.identify_neutrals_spidacalc(temp_pole_data, spida_pole_data)
        logger.info(f"Found {len(neutral_wires_spida)} neutral wires from SPIDAcalc")
    
    # Combine neutrals and find highest
    all_neutral_wires = neutral_wires_katapult + neutral_wires_spida
    highest_neutral = ni.get_highest_neutral(all_neutral_wires)
    
    if highest_neutral:
        from utils import inches_to_feet_inches_str
        neutral_height = highest_neutral.get('raw_existing_height_inches', 0)
        logger.info(f"Highest neutral wire found at {inches_to_feet_inches_str(neutral_height)} for pole {pole_number}")
        desc = highest_neutral.get('description', 'Unknown Neutral')
        logger.info(f"Neutral description: {desc}")
    else:
        logger.warning(f"No neutral wires found for pole {pole_number}")
    
    # Identify attachments below neutral
    attachments_below_neutral = ni.identify_attachments_below_neutral(
        temp_pole_data, highest_neutral, katapult, spida_pole_data
    )
    
    # Deduplicate
    if attachments_below_neutral:
        before_count = len(attachments_below_neutral)
        attachments_below_neutral = deduplicate_attachments(attachments_below_neutral)
        after_count = len(attachments_below_neutral)
        logger.info(f"Deduplicated attachments below neutral from {before_count} to {after_count}")
    
    # Include the highest neutral wire in the attachments_below_neutral list
    if highest_neutral:
        # Check if the neutral is already in the list
        neutral_in_list = False
        for attachment in attachments_below_neutral:
            if (attachment.get('description') == highest_neutral.get('description') and
                abs((attachment.get('raw_existing_height_inches') or 0) - 
                    (highest_neutral.get('raw_existing_height_inches') or 0)) < 5):
                neutral_in_list = True
                logger.info(f"Neutral already in attachments list: {highest_neutral.get('description')}")
                break
        
        # Add neutral if not already in the list
        if not neutral_in_list:
            logger.info(f"Adding highest neutral to attachments list: {highest_neutral.get('description')}")
            # Mark as neutral for UI distinction if needed
            highest_neutral_copy = highest_neutral.copy()
            highest_neutral_copy['is_neutral'] = True
            # Insert at the beginning (highest)
            attachments_below_neutral.insert(0, highest_neutral_copy)
    
    # Log the filtered attachments
    logger.info(f"Final attachment list for pole {pole_number} has {len(attachments_below_neutral)} items")
    for idx, att in enumerate(attachments_below_neutral):
        height_str = att.get('existing_height', 'N/A')
        desc = att.get('description', 'Unknown')
        logger.info(f"  {idx+1}. {desc} at {height_str}")
    
    return {
        'neutral_wires': all_neutral_wires,
        'highest_neutral': highest_neutral,
        'attachments_below_neutral': attachments_below_neutral
    }

def check_proposed_equipment(spida_pole_data, attributes):
    """Check for proposed equipment (risers and guys)."""
    proposed_riser = 'No'
    proposed_guy = 'No'
    
    # First check SPIDAcalc data
    if spida_pole_data:
        if check_proposed_riser_spida(spida_pole_data):
            proposed_riser = 'Yes'
        
        if check_proposed_guy_spida(spida_pole_data):
            proposed_guy = 'Yes'
    
    # Extract notes
    notes = extract_notes(attributes)
    
    # If not found in SPIDAcalc, check notes
    if proposed_riser == 'No':
        for note in [notes['kat_mr_notes'], notes['stress_mr_notes']]:
            if note and check_proposed_equipment_in_notes(note, 'riser'):
                proposed_riser = 'Yes'
                break
    
    if proposed_guy == 'No':
        for note in [notes['kat_mr_notes'], notes['stress_mr_notes']]:
            if note and check_proposed_equipment_in_notes(note, 'guy'):
                proposed_guy = 'Yes'
                break
    
    return {
        'proposed_riser': proposed_riser,
        'proposed_guy': proposed_guy
    }

def calculate_midspan_proposed(pole_connections, owners_with_changes, katapult, attachers_list):
    """Calculate the proposed midspan value."""
    from utils import inches_to_feet_inches_str
    
    # Check if there are any new installations
    has_new_installations = any(
        attacher.get('existing_height', 'N/A') == 'N/A' and attacher.get('proposed_height', 'N/A') != 'N/A'
        for attacher in attachers_list
    )
    
    # Only calculate if there are changes
    if not has_new_installations and not owners_with_changes:
        return 'N/A'
    
    # Collect midspan heights for owners with changes
    midspan_heights = []
    
    for conn in pole_connections:
        conn_id = conn.get('connection_id')
        if not conn_id:
            continue
        
        # Get connection data
        conn_data = katapult.get('connections', {}).get(conn_id, {})
        
        # Process sections
        for section in conn_data.get('sections', {}).values():
            if not isinstance(section, dict):
                continue
            
            # Process photos
            for photo_id, photo_assoc in section.get('photos', {}).items():
                # Get full photo data
                photo_data = katapult.get('photos', {}).get(photo_id, {})
                if not isinstance(photo_data, dict):
                    continue
                
                photofirst_data = photo_data.get('photofirst_data', {})
                if not isinstance(photofirst_data, dict):
                    continue
                
                # Get wire data
                wire_data = photofirst_data.get('wire', {})
                wire_items = []
                
                if isinstance(wire_data, list):
                    wire_items = wire_data
                elif isinstance(wire_data, dict):
                    wire_items = list(wire_data.values())
                else:
                    continue
                
                # Process each wire
                for wire in wire_items:
                    if not isinstance(wire, dict):
                        continue
                    
                    # Get trace
                    trace_id = wire.get('_trace', '')
                    if not trace_id:
                        continue
                    
                    trace = get_trace_by_id(katapult, trace_id.strip())
                    
                    # Get metadata
                    from trace_utils import extract_wire_metadata
                    wire_meta = extract_wire_metadata(wire, trace)
                    owner = wire_meta['owner']
                    is_proposed = wire_meta['is_proposed']
                    
                    # Check if owner has changes or wire is proposed
                    from utils import normalize_owner
                    normalized_owner = normalize_owner(owner)
                    include_wire = (
                        has_new_installations or 
                        normalized_owner in owners_with_changes or 
                        is_proposed
                    )
                    
                    if include_wire:
                        # Process height
                        from wire_utils import process_wire_height
                        height = process_wire_height(wire)
                        if height is not None:
                            midspan_heights.append((normalized_owner, height))
    
    # Find lowest height
    if midspan_heights:
        # Sort by height (ascending)
        midspan_heights.sort(key=lambda x: x[1])
        
        # Get the lowest height
        lowest_owner, lowest_height = midspan_heights[0]
        return inches_to_feet_inches_str(lowest_height)
    
    return 'N/A'

def apply_midspan_values(attachers_list, midspan_proposed):
    """Apply midspan values to attachments based on business rules."""
    for attacher in attachers_list:
        has_existing = attacher.get('existing_height', 'N/A') not in (None, '', 'N/A')
        has_proposed = attacher.get('proposed_height', 'N/A') not in (None, '', 'N/A')
        moved = has_existing and has_proposed and attacher.get('existing_height') != attacher.get('proposed_height')

        # --- New Rule (2025-05-22) ---
        # 1. Moved attachment → keep whatever midspan value we already
        #    captured (likely copied from Katapult).  If still 'N/A',
        #    attempt to use span-level lowest midspan for the pole.
        if moved:
            if attacher.get('midspan_proposed', 'N/A') in (None, '', 'N/A') and midspan_proposed != 'N/A':
                attacher['midspan_proposed'] = midspan_proposed
            continue  # Do not overwrite further

        # 2. New installations → force 'N/A' (unless UG already set)
        if not has_existing and has_proposed:
            if attacher.get('midspan_proposed', 'N/A') not in ('UG', 'ug'):
                attacher['midspan_proposed'] = 'N/A'
            continue

        # 3. Existing attachments with no move → leave as is.

def build_final_attachers_list(attachers_list, reference_spans, backspan):
    """Build the final ordered list of attachers including reference spans."""
    import logging
    logger = logging.getLogger('final_attachers')
    
    logger.info(f"Building final attachers list with {len(attachers_list)} attachments")
    
    # Get neutral height from the filtered list (first attachment should be the neutral)
    neutral_height = None
    for att in attachers_list:
        if att.get('is_neutral', False):
            neutral_height = att.get('raw_existing_height_inches')
            logger.info(f"Found neutral at height {neutral_height} inches")
            break
    
    # If no neutral found in the first few items, use height of the highest attachment as fallback
    if neutral_height is None and attachers_list:
        highest_att = max(attachers_list, 
                         key=lambda a: a.get('raw_existing_height_inches', 0) or 0, 
                         default=None)
        if highest_att:
            neutral_height = highest_att.get('raw_existing_height_inches', 0)
            logger.info(f"No explicit neutral found, using height of highest attachment: {neutral_height} inches")
    
    # Sort primary attachers by height (descending)
    primary_attachers = sorted(
        [att for att in attachers_list if not att.get('type', '').startswith('header_')],
        key=lambda att: (
            att.get('raw_existing_height_inches') or 
            att.get('raw_proposed_height_inches') or 
            -float('inf')
        ),
        reverse=True
    )
    
    # Log the primary attachers
    logger.info(f"Sorted {len(primary_attachers)} primary attachers")
    for idx, att in enumerate(primary_attachers):
        desc = att.get('description', 'Unknown')
        height = att.get('existing_height', 'Unknown')
        logger.info(f"  {idx+1}. {desc} at {height}")
    
    # Start with primary attachers
    final_list = list(primary_attachers)
    
    # Add backspan if exists
    if backspan:
        # Set the header type to properly identify it in the Excel output
        backspan_header = backspan['header'].copy()
        backspan_header['type'] = 'backspan_header'
        backspan_header['style_hint'] = 'light-blue'  # Ensure consistent styling
        
        # Add to the final list
        logger.info(f"Adding backspan header: {backspan_header.get('description')}")
        final_list.append(backspan_header)
        
        # Filter backspan attachments to match the same neutral height filtering
        if neutral_height:
            filtered_backspan_attachments = []
            for attachment in backspan['attachments']:
                height = attachment.get('raw_existing_height_inches')
                if height is not None and height < neutral_height:
                    filtered_backspan_attachments.append(attachment)
                elif attachment.get('is_neutral', False):
                    filtered_backspan_attachments.append(attachment)
            
            logger.info(f"Filtered backspan attachments from {len(backspan['attachments'])} to {len(filtered_backspan_attachments)}")
            final_list.extend(filtered_backspan_attachments)
        else:
            # If no neutral height reference, keep all attachments
            logger.info(f"Adding {len(backspan['attachments'])} backspan attachments (no filtering)")
            final_list.extend(backspan['attachments'])
    
    # Add reference spans
    for ref in reference_spans:
        # Set the header type and style based on direction
        ref_header = ref['header'].copy()
        ref_header['type'] = 'reference_header'
        
        # Set appropriate styling hint based on reference direction
        description = ref_header.get('description', '').lower()
        if 'south east' in description or 'southeast' in description:
            ref_header['style_hint'] = 'purple'  # Purple for South East refs
        else:
            ref_header['style_hint'] = 'orange'  # Default orange for other directions
        
        # Add to the final list
        logger.info(f"Adding reference header: {ref_header.get('description')}")
        final_list.append(ref_header)
        
        # Process midspan values for attachments in reference spans 
        ref_attachments = []
        
        # Filter reference span attachments based on neutral height
        if neutral_height:
            logger.info(f"Filtering reference attachments using neutral height {neutral_height}")
            for attachment in ref['attachments']:
                att_copy = attachment.copy()
                desc = att_copy.get('description', '').lower()
                height = att_copy.get('raw_existing_height_inches')
                
                # Include neutrals and attachments below neutral
                if (height is not None and height < neutral_height) or 'neutral' in desc.lower():
                    # For fiber optic attachments, make sure to show midspan values
                    if ('fiber' in desc or 'optic' in desc) and att_copy.get('midspan_proposed', 'N/A') == 'N/A':
                        # If no midspan value is set, try to use the existing height as a fallback
                        if att_copy.get('existing_height', 'N/A') != 'N/A':
                            # Use existing height as midspan for fibers that don't have a set value
                            att_copy['midspan_proposed'] = att_copy.get('existing_height')
                    
                    ref_attachments.append(att_copy)
                    logger.info(f"Including reference attachment: {att_copy.get('description')} at height {att_copy.get('existing_height')}")
                else:
                    logger.info(f"Skipping reference attachment above neutral: {att_copy.get('description')} at height {att_copy.get('existing_height')}")
        else:
            # If no neutral height, apply midspan logic to all attachments but don't filter by height
            logger.info("No neutral height available for filtering reference attachments")
            for attachment in ref['attachments']:
                att_copy = attachment.copy()
                desc = att_copy.get('description', '').lower()
                
                # For fiber optic attachments, make sure to show midspan values
                if ('fiber' in desc or 'optic' in desc) and att_copy.get('midspan_proposed', 'N/A') == 'N/A':
                    # If no midspan value is set, try to use the existing height as a fallback
                    if att_copy.get('existing_height', 'N/A') != 'N/A':
                        # Use existing height as midspan for fibers that don't have a set value
                        att_copy['midspan_proposed'] = att_copy.get('existing_height')
                
                ref_attachments.append(att_copy)
        
        logger.info(f"Adding {len(ref_attachments)} filtered reference span attachments")
        final_list.extend(ref_attachments)
    
    logger.info(f"Final attachers list has {len(final_list)} items")
    return final_list

def determine_pole_status(attributes, pole_attrs):
    """Determine pole status based on notes and attributes."""
    # Default status
    status = "No Change"
    
    # Extract notes
    notes = extract_notes(attributes)
    
    # Check for make-ready notes
    if notes['kat_mr_notes'] and isinstance(notes['kat_mr_notes'], str) and len(notes['kat_mr_notes'].strip()) > 0:
        status = "Make-Ready Required"
    
    # Check for PLA percentage below threshold
    try:
        passing_capacity = pole_attrs.get('passing_capacity')
        if passing_capacity and float(passing_capacity) < 85.0:
            status = "Issue Detected"
    except (ValueError, TypeError):
        pass
    
    return status

# ----------------------------------------------------------------------------------
#  NEW  – Column B logic: determine pole-level Attachment Action code
# ----------------------------------------------------------------------------------

def determine_pole_action(attachers):
    """Return Column-B action code for a pole.

    Rules (see excel-columns-explained/column_b_attachment_action.md):
    1. (I) Installing – at least one *new* attachment (is_proposed True **or** no existing height but has proposed height).
    2. (R) Removing   – no installs and at least one *removal* (existing height present, proposed height == 'N/A').
    3. (E) Existing   – otherwise (moves / unchanged).
    """

    if not attachers:
        return "(E)xisting"  # fallback when no attachments processed

    has_install = False
    has_removal = False

    for att in attachers:
        # Skip headers (reference / backspan rows)
        if att.get('type', '').startswith('header_'):
            continue

        existing_h = att.get('existing_height', 'N/A')
        proposed_h = att.get('proposed_height', 'N/A')
        is_proposed_flag = att.get('is_proposed', False)

        # New install → no existing height, has proposed or explicit flag
        if (existing_h in (None, '', 'N/A')) and (proposed_h not in (None, '', 'N/A') or is_proposed_flag):
            has_install = True
        # Removal → has existing height but no proposed height, and not flagged as proposed
        elif (existing_h not in (None, '', 'N/A')) and (proposed_h in (None, '', 'N/A')) and not is_proposed_flag:
            has_removal = True

    if has_install:
        return "(I)nstalling"
    if has_removal:
        return "(R)emoving"
    return "(E)xisting"

# Helper to count proposed risers and guys from both Katapult and SPIDAcalc
def count_proposed_riser_guy(node, katapult, spida_pole_data):
    riser_count = 0
    guy_count = 0
    pole_tag = "Unknown"
    
    # Get pole tag for better logging
    if node and 'attributes' in node:
        for attr in ['pole_tag', 'PoleNumber', 'pl_number', 'electric_pole_tag']:
            if attr in node['attributes']:
                attr_val = node['attributes'][attr]
                if isinstance(attr_val, dict) and '-Imported' in attr_val:
                    pole_tag = attr_val['-Imported'].get('tagtext', 'Unknown')
                    break
                elif isinstance(attr_val, str):
                    pole_tag = attr_val
                    break

    print(f"[DEBUG] Counting proposed risers and guys for pole {pole_tag}")
    
    # Katapult: look for attachments.riser and attachments.guying with proposed==True
    if node:
        attachments = node.get('attachments', {})
        
        # Check for risers
        risers = attachments.get('riser', [])
        for riser in risers:
            if riser.get('proposed'):
                riser_count += 1
                print(f"[DEBUG] Found proposed riser in Katapult for pole {pole_tag}")
        
        # Check for guys
        guys = attachments.get('guying', [])
        if guys:
            print(f"[DEBUG] Found {len(guys)} guying entries in Katapult for pole {pole_tag}")
            for guy in guys:
                # Check for proposed flag
                if guy.get('proposed'):
                    guy_count += 1
                    print(f"[DEBUG] Found proposed guy in Katapult with 'proposed' flag for pole {pole_tag}")
                # Alternative check for description containing "proposed"
                elif guy.get('desc', '').lower().find('proposed') >= 0:
                    guy_count += 1
                    print(f"[DEBUG] Found proposed guy in Katapult with 'proposed' in description for pole {pole_tag}")
                # Check for guy attributes
                guy_attrs = guy.get('attributes', {})
                if guy_attrs.get('proposed') or guy_attrs.get('is_proposed'):
                    guy_count += 1
                    print(f"[DEBUG] Found proposed guy in Katapult with attribute flags for pole {pole_tag}")
        
        # Also check wire attachments for guy wires that might be categorized differently
        wires = attachments.get('wires', [])
        for wire in wires:
            wire_desc = wire.get('desc', '').lower()
            if ('guy' in wire_desc or 'down guy' in wire_desc) and (wire.get('proposed') or 'proposed' in wire_desc):
                guy_count += 1
                print(f"[DEBUG] Found proposed guy wire in 'wires' array for pole {pole_tag}")

    # SPIDAcalc: look for recommended design equipments of type RISER or GUY
    if spida_pole_data:
        print(f"[DEBUG] Checking SPIDAcalc data for proposed guys for pole {pole_tag}")
        # Check in designs array
        for design in spida_pole_data.get('designs', []):
            design_label = design.get('label', '').lower()
            if 'recommended' in design_label:
                print(f"[DEBUG] Found recommended design in SPIDAcalc for pole {pole_tag}")
                # Check equipment for risers
                for eq in design.get('structure', {}).get('equipments', []):
                    eq_type = (eq.get('clientItem', {}) or {}).get('type', '').upper()
                    if eq_type == 'RISER':
                        riser_count += 1
                        print(f"[DEBUG] Found riser in SPIDAcalc recommended design for pole {pole_tag}")
                
                # Check guys array for guy wires
                guys = design.get('structure', {}).get('guys', [])
                if guys:
                    print(f"[DEBUG] Found {len(guys)} guys in SPIDAcalc recommended design for pole {pole_tag}")
                    for guy in guys:
                        guy_type = (guy.get('clientItem', {}) or {}).get('type', '').upper()
                        if guy_type and ('GUY' in guy_type or 'DOWN' in guy_type):
                            guy_count += 1
                            print(f"[DEBUG] Found guy in SPIDAcalc recommended design for pole {pole_tag}: type={guy_type}")
        
        # Also check for any notes in SPIDAcalc about proposed guys
        notes = spida_pole_data.get('analysis', {}).get('notes', '')
        if isinstance(notes, str) and ('add guy' in notes.lower() or 'proposed guy' in notes.lower()):
            print(f"[DEBUG] Found proposed guy in SPIDAcalc notes for pole {pole_tag}")
            guy_count += 1

    # Final count logging
    print(f"[DEBUG] Final counts for pole {pole_tag}: risers={riser_count}, guys={guy_count}")
    return riser_count, guy_count

def extract_lowest_midspan_heights(node_id, katapult):
    """
    For the given node (pole), extract the lowest midspan heights for each span (to each connected pole).
    Returns a dict: {to_pole_number: {'comm': value, 'cps': value, 'is_ug': bool}}
    """
    from utils import normalize_owner, inches_to_feet_inches_str
    results = {}
    node = katapult.get('nodes', {}).get(node_id, {})
    pole_number = None
    # Try to get normalized pole number
    attributes = node.get('attributes', {})
    for attr in ['PoleNumber', 'pl_number', 'dloc_number', 'PL_number', 'DLOC_number', 'pole_tag', 'electric_pole_tag']:
        val = attributes.get(attr)
        if val:
            pole_number = str(val) if isinstance(val, str) else str(next(iter(val.values())))
            break
    if not pole_number:
        return results

    # For each connection from this node
    for conn_id, conn in katapult.get('connections', {}).items():
        # Find if this node is one end
        from_id = conn.get('node_id_1')
        to_id = conn.get('node_id_2')
        if node_id not in (from_id, to_id):
            continue
        other_id = to_id if from_id == node_id else from_id
        # Get normalized pole number for the other end
        other_node = katapult.get('nodes', {}).get(other_id, {})
        other_pole_number = None
        other_attrs = other_node.get('attributes', {})
        for attr in ['PoleNumber', 'pl_number', 'dloc_number', 'PL_number', 'DLOC_number', 'pole_tag', 'electric_pole_tag']:
            val = other_attrs.get(attr)
            if val:
                other_pole_number = str(val) if isinstance(val, str) else str(next(iter(val.values())))
                break
        if not other_pole_number:
            continue

        # For each section in this connection
        lowest_comm = None
        lowest_cps = None
        is_ug = False
        for section in conn.get('sections', {}).values():
            # Check for underground path
            if conn.get('button', '').lower() == 'underground_path':
                is_ug = True
            # For each photo in section
            for photo_id in section.get('photos', {}):
                photo = katapult.get('photos', {}).get(photo_id, {})
                photofirst_data = photo.get('photofirst_data', {})
                wire_data = photofirst_data.get('wire', {})
                wire_items = []
                if isinstance(wire_data, list):
                    wire_items = wire_data
                elif isinstance(wire_data, dict):
                    wire_items = list(wire_data.values())
                for wire in wire_items:
                    if not isinstance(wire, dict):
                        continue
                    # Trace lookup for attribute fallback
                    trace = None
                    trace_id_local = wire.get('_trace') or ''
                    if trace_id_local:
                        from trace_utils import get_trace_by_id as _get_trace
                        trace = _get_trace(katapult, trace_id_local.strip())
                    # ---------------------------------------------------------
                    # Height selection (2025-05-22)
                    # Use *only* true mid-span values.  Accept the following
                    # fields in priority order and **ignore** pole-end
                    # _measured_height so we don't under- or over-state the
                    # clearance for this span.
                    # ---------------------------------------------------------
                    height = (
                        wire.get('_midspan_height') or  # preferred – per-wire
                        wire.get('midspanHeight_in') or  # alternative name
                        section.get('midspanHeight_in')   # section-level fallback
                    )
                    if height is None:
                        # Last-resort: some mid-span photos store the value in
                        # _measured_height even though the photo is taken at
                        # the span midpoint.  Use it only if every other field
                        # is missing.
                        height = wire.get('_measured_height')
                    if height is None:
                        continue  # still nothing we trust as mid-span
                    
                    try:
                        height = float(height)
                    except (TypeError, ValueError):
                        continue
                    # Get owner/type
                    owner = wire.get('owner') or wire.get('_company') or ''
                    owner = normalize_owner(owner)
                    wire_type = (wire.get('type') or '').lower()
                    usage_group = (wire.get('usageGroup') or '').lower()
                    # -----------------------------------------------------
                    # Fallback to TRACE attributes when the on-photo wire
                    # record is missing these fields (common for CPS
                    # neutrals in this data set).
                    # -----------------------------------------------------
                    if (not wire_type or wire_type == '') and trace:
                        wire_type = (trace.get('cable_type') or '').lower()
                    if (not usage_group or usage_group == '') and trace:
                        usage_group = (trace.get('usageGroup') or '').lower()
                    # Classify
                    if owner == 'CPS ENERGY':
                        # Count CPS-owned electrical wires.
                        is_electrical = (
                            any(t in wire_type for t in ['neutral', 'secondary', 'service', 'primary']) or
                            usage_group == 'power'
                        )
                        if is_electrical:
                            if lowest_cps is None or height < lowest_cps:
                                lowest_cps = height
                    else:
                        # Non-CPS owners – treat as communications
                        if lowest_comm is None or height < lowest_comm:
                            lowest_comm = height
        # Format
        if is_ug:
            results[other_pole_number] = {'comm': 'UG', 'cps': 'UG', 'is_ug': True}
        else:
            results[other_pole_number] = {
                'comm': inches_to_feet_inches_str(lowest_comm) if lowest_comm is not None else 'NA',
                'cps': inches_to_feet_inches_str(lowest_cps) if lowest_cps is not None else 'NA',
                'is_ug': False
            }
    return results

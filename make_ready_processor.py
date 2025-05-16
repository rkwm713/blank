import json
import math
import re

def inches_to_feet_inches_str(inches):
    if inches is None:
        return 'N/A'
    try:
        inches = float(inches)
        feet = int(inches // 12)
        rem_inches = int(round(inches % 12))
        return f"{feet} ft {rem_inches} in"
    except Exception:
        return 'N/A'

# Add helper function for processing wire height
def process_wire_height(wire):
    """
    Safely extract and convert a wire's measured height.
    Returns height in inches as float if valid, or None if invalid/missing.
    """
    # Get height value with default of None if key doesn't exist
    height_str = wire.get('_measured_height')
    
    # Convert to numerical value with validation
    try:
        # Skip processing if height is missing or empty
        if height_str is None or height_str == '':
            return None
            
        # Convert to float for numerical comparison
        height_inches = float(height_str)
        return height_inches
        
    except (ValueError, TypeError) as e:
        print(f"[DEBUG] Error converting height '{height_str}' to float: {str(e)}")
        return None  # Return None to indicate invalid height

def meters_to_feet_inches_str(meters):
    if meters is None:
        return 'N/A'
    try:
        inches = float(meters) * 39.3701
        return inches_to_feet_inches_str(inches)
    except Exception:
        return 'N/A'

def normalize_pole_id(pole_id):
    if not pole_id:
        return None
    match = re.search(r'(\d+)$', str(pole_id))
    return match.group(1) if match else None

def normalize_owner(owner):
    if not owner:
        return None
    owner = owner.strip().upper().replace('&', 'AND')
    if owner in ['AT&T', 'ATT', 'AT AND T']:
        return 'AT&T'
    if owner in ['CPS ENERGY', 'CPS']:
        return 'CPS ENERGY'
    return owner

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

def check_proposed_riser_spida(spida_pole_data):
    """
    Check if a pole has a proposed riser in SPIDAcalc data.
    A riser is considered proposed if it exists in the "Recommended Design" but not in the "Measured Design".
    
    Args:
        spida_pole_data (dict): The pole data from SPIDAcalc
        
    Returns:
        bool: True if a proposed riser is found, False otherwise
    """
    if not spida_pole_data or not isinstance(spida_pole_data, dict):
        return False
        
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
    
    if not recommended_design:
        return False  # No recommended design to check
    
    # Check for risers in recommended design
    recommended_risers = []
    for equipment in recommended_design.get('structure', {}).get('equipments', []):
        if not isinstance(equipment, dict):
            continue
            
        client_item = equipment.get('clientItem', {})
        if client_item.get('type', '').upper() == 'RISER':
            # Store key details about this riser
            riser_info = {
                'owner': equipment.get('owner', {}).get('id', ''),
                'size': client_item.get('size', ''),
                'direction': equipment.get('direction')
            }
            recommended_risers.append(riser_info)
    
    if not recommended_risers:
        return False  # No risers in recommended design
    
    # If no measured design, all recommended risers are proposed
    if not measured_design:
        return True
    
    # Check if any recommended risers don't exist in measured design
    measured_risers = []
    for equipment in measured_design.get('structure', {}).get('equipments', []):
        if not isinstance(equipment, dict):
            continue
            
        client_item = equipment.get('clientItem', {})
        if client_item.get('type', '').upper() == 'RISER':
            # Store key details about this riser
            riser_info = {
                'owner': equipment.get('owner', {}).get('id', ''),
                'size': client_item.get('size', ''),
                'direction': equipment.get('direction')
            }
            measured_risers.append(riser_info)
    
    # Check if any recommended riser is not in measured risers
    for rec_riser in recommended_risers:
        found_match = False
        for meas_riser in measured_risers:
            # Compare key attributes to determine if it's the same riser
            if (rec_riser['owner'] == meas_riser['owner'] and 
                rec_riser['size'] == meas_riser['size']):
                found_match = True
                break
        
        if not found_match:
            # Found a riser in recommended that's not in measured
            return True
    
    return False

def check_proposed_guy_spida(spida_pole_data):
    """
    Check if a pole has a proposed guy in SPIDAcalc data.
    A guy is considered proposed if it exists in the "Recommended Design" but not in the "Measured Design".
    
    Args:
        spida_pole_data (dict): The pole data from SPIDAcalc
        
    Returns:
        bool: True if a proposed guy is found, False otherwise
    """
    if not spida_pole_data or not isinstance(spida_pole_data, dict):
        return False
        
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
    
    if not recommended_design:
        return False  # No recommended design to check
    
    # Check for guys in recommended design
    recommended_guys = []
    for guy in recommended_design.get('structure', {}).get('guys', []):
        if not isinstance(guy, dict):
            continue
            
        # Store key details about this guy
        guy_info = {
            'owner': guy.get('owner', {}).get('id', ''),
            'size': guy.get('clientItem', {}).get('size', ''),
            'type': guy.get('clientItem', {}).get('type', '')
        }
        recommended_guys.append(guy_info)
    
    if not recommended_guys:
        return False  # No guys in recommended design
    
    # If no measured design, all recommended guys are proposed
    if not measured_design:
        return True
    
    # Check if any recommended guys don't exist in measured design
    measured_guys = []
    for guy in measured_design.get('structure', {}).get('guys', []):
        if not isinstance(guy, dict):
            continue
            
        # Store key details about this guy
        guy_info = {
            'owner': guy.get('owner', {}).get('id', ''),
            'size': guy.get('clientItem', {}).get('size', ''),
            'type': guy.get('clientItem', {}).get('type', '')
        }
        measured_guys.append(guy_info)
    
    # Check if any recommended guy is not in measured guys
    for rec_guy in recommended_guys:
        found_match = False
        for meas_guy in measured_guys:
            # Compare key attributes to determine if it's the same guy
            if (rec_guy['owner'] == meas_guy['owner'] and 
                rec_guy['size'] == meas_guy['size'] and
                rec_guy['type'] == meas_guy['type']):
                found_match = True
                break
        
        if not found_match:
            # Found a guy in recommended that's not in measured
            return True
    
    return False

def get_construction_grade_spida(spida_data):
    """
    Extract the construction grade from SPIDAcalc data.
    
    Args:
        spida_data (dict): The full SPIDAcalc data
        
    Returns:
        str: The construction grade if found, None otherwise
    """
    if not spida_data or not isinstance(spida_data, dict):
        return None
    
    # Check in clientData.analysisCases
    client_data = spida_data.get('clientData', {})
    if isinstance(client_data, dict):
        analysis_cases = client_data.get('analysisCases', [])
        if isinstance(analysis_cases, list):
            for case in analysis_cases:
                if isinstance(case, dict) and 'constructionGrade' in case:
                    return case.get('constructionGrade')
    
    return None

def check_proposed_equipment_in_notes(notes_text, equipment_type):
    """
    Check if notes text contains indications of proposed equipment.
    
    Args:
        notes_text (str): The notes text to check
        equipment_type (str): The type of equipment to look for ('riser' or 'guy')
        
    Returns:
        bool: True if proposed equipment is found, False otherwise
    """
    if not notes_text or not isinstance(notes_text, str):
        return False
    
    notes_lower = notes_text.lower()
    
    if equipment_type == 'riser':
        # Check for phrases indicating a proposed riser
        riser_patterns = [
            r'add\s+riser',
            r'install\s+riser',
            r'new\s+riser',
            r'proposed\s+riser'
        ]
        
        for pattern in riser_patterns:
            if re.search(pattern, notes_lower):
                return True
    
    elif equipment_type == 'guy':
        # Check for phrases indicating a proposed guy
        guy_patterns = [
            r'add\s+(down|overhead)?\s*guy',
            r'install\s+(down|overhead)?\s*guy',
            r'new\s+(down|overhead)?\s*guy',
            r'proposed\s+(down|overhead)?\s*guy'
        ]
        
        for pattern in guy_patterns:
            if re.search(pattern, notes_lower):
                return True
    
    return False

def process_make_ready_report(katapult_path, spidacalc_path=None, target_poles=None, 
                             attachment_height_strategy='PREFER_KATAPULT', 
                             pole_attribute_strategy='PREFER_KATAPULT'):
    """
    Process Katapult and optional SPIDAcalc JSON files to generate a Make-Ready report.
    
    Args:
        katapult_path (str): Path to the Katapult JSON file
        spidacalc_path (str, optional): Path to the SPIDAcalc JSON file
        target_poles (list, optional): List of pole numbers to process. If provided, only these poles will be processed.
        attachment_height_strategy (str, optional): Strategy for resolving attachment height conflicts:
            - PREFER_KATAPULT: Use Katapult values when conflicts occur (default)
            - PREFER_SPIDA: Use SPIDAcalc values when conflicts occur
            - HIGHLIGHT_DIFFERENCES: Mark conflicts for highlighting in the report
        pole_attribute_strategy (str, optional): Strategy for resolving pole attribute conflicts:
            - PREFER_KATAPULT: Use Katapult values when conflicts occur (default)
            - PREFER_SPIDA: Use SPIDAcalc values when conflicts occur
            - HIGHLIGHT_DIFFERENCES: Mark conflicts for highlighting in the report
        
    Returns:
        list: List of processed pole data dictionaries, ordered according to their appearance in the SPIDAcalc file
    """
    with open(katapult_path, 'r', encoding='utf-8') as f:
        katapult = json.load(f)
        
    # Process target poles list if provided
    normalized_target_poles = None
    if target_poles:
        # Normalize all target pole IDs for consistent matching
        normalized_target_poles = [normalize_pole_id(pole) for pole in target_poles if pole]
        print(f"[INFO] Filtering to {len(normalized_target_poles)} target poles: {normalized_target_poles}")
    
    # Debug: Print the structure of the first node
    if katapult.get('nodes'):
        first_node_id = next(iter(katapult['nodes']))
        first_node = katapult['nodes'][first_node_id]
        print(f"[DEBUG] First node structure: {json.dumps(first_node, indent=2)}")
        
    # Debug: Print the structure of the first connection
    if katapult.get('connections'):
        first_conn_id = next(iter(katapult['connections']))
        first_conn = katapult['connections'][first_conn_id]
        print(f"[DEBUG] First connection structure: {json.dumps(first_conn, indent=2)}")
    
    # Debug: Inspect the structure of traces collection
    if katapult.get('traces'):
        print(f"[DEBUG] Traces structure: Top-level keys in katapult['traces']: {list(katapult['traces'].keys())}")
        
        # Inspect trace_data structure if it exists
        if 'trace_data' in katapult['traces']:
            trace_data = katapult['traces']['trace_data']
            print(f"[DEBUG] trace_data is a {type(trace_data).__name__}")
            if isinstance(trace_data, dict) and trace_data:
                # Get a sample trace_id and its data
                sample_trace_id = next(iter(trace_data))
                print(f"[DEBUG] Sample trace_id in trace_data: '{sample_trace_id}'")
                print(f"[DEBUG] Sample trace structure: {json.dumps(trace_data[sample_trace_id], indent=2)}")
        
        # Inspect trace_items structure if it exists
        if 'trace_items' in katapult['traces']:
            trace_items = katapult['traces']['trace_items']
            print(f"[DEBUG] trace_items is a {type(trace_items).__name__}")
            if isinstance(trace_items, dict) and trace_items:
                # Get a sample trace_item_id and its data
                sample_item_id = next(iter(trace_items))
                print(f"[DEBUG] Sample item_id in trace_items: '{sample_item_id}'")
                print(f"[DEBUG] Sample trace_item structure: {json.dumps(trace_items[sample_item_id], indent=2)}")
    
    spida = None
    spida_wire_lookup = {}
    # Dictionary to track the order of poles in the SPIDAcalc file
    spida_pole_order = {}
    pole_order_index = 0
    
    if spidacalc_path:
        with open(spidacalc_path, 'r', encoding='utf-8') as f:
            spida = json.load(f)
        # Build a lookup for SPIDAcalc wires by (owner, sorted endpoints)
        for lead in spida.get('leads', []):
            for loc in lead.get('locations', []):
                loc_pole = normalize_pole_id(loc.get('label'))
                # Track the order of poles in the SPIDAcalc file
                if loc_pole and loc_pole not in spida_pole_order:
                    spida_pole_order[loc_pole] = pole_order_index
                    pole_order_index += 1
                
                for design in loc.get('designs', []):
                    for wire in design.get('structure', {}).get('wires', []):
                        owner = normalize_owner(wire.get('owner', {}).get('id', ''))
                        endpoints = [loc_pole]
                        # Try to get other endpoint from wireEndPoints if available
                        if 'wireEndPoints' in wire:
                            endpoints += [normalize_pole_id(e.get('label')) for e in wire['wireEndPoints'] if e.get('label')]
                        endpoints = sorted(set([e for e in endpoints if e]))
                        key = (owner, tuple(endpoints))
                        spida_wire_lookup[key] = wire

    # Build a lookup for SPIDAcalc locations by normalized pole label
    spida_lookup = {}
    if spida:
        for lead in spida.get('leads', []):
            for loc in lead.get('locations', []):
                label = loc.get('label')
                norm = normalize_pole_id(label)
                spida_lookup[norm] = loc

    poles = []
    for node_id, node in katapult.get('nodes', {}).items():
        try:
            # Debug: Print node structure
            print(f"[DEBUG] Processing node {node_id}")
            
            # Check if this node is a pole type before processing
            # Expanded list of valid pole types to include aerial_path and other path types
            button = node.get('button', '')
            valid_pole_types = ['aerial', 'pole', 'aerial_path']
            # Also check node_type attribute
            node_type = node.get('attributes', {}).get('node_type', {})
            node_type_value = None
            if isinstance(node_type, dict):
                node_type_value = node_type.get('-Imported') or node_type.get('button_added')
            else:
                node_type_value = node_type
                
            if button not in valid_pole_types and node_type_value != 'pole':
                print(f"[DEBUG] Skipping non-pole node type: {button} for node {node_id}")
                continue
                
            print(f"[DEBUG] Node structure: {json.dumps(node, indent=2)}")
            
            attributes = node.get('attributes', {})
            if not isinstance(attributes, dict):
                print(f"[DEBUG] Warning: attributes is not a dict for node {node_id}, it's a {type(attributes)}")
                attributes = {}
            
            # Safely get pole number with type checking
            pole_number = None
            pole_number_attr = attributes.get('PoleNumber') # Check capitalized "PoleNumber" first
            if isinstance(pole_number_attr, dict):
                pole_number = pole_number_attr.get('-Imported') or pole_number_attr.get('assessment')
            elif isinstance(pole_number_attr, str):
                pole_number = pole_number_attr

            if not pole_number: # If not found, try lowercase "pl_number"
                pl_number_attr = attributes.get('pl_number') # Use lowercase 'pl_number'
                if isinstance(pl_number_attr, dict):
                    pole_number = pl_number_attr.get('-Imported') or pl_number_attr.get('assessment')
                elif isinstance(pl_number_attr, str):
                    pole_number = pl_number_attr

            if not pole_number: # If still not found, try lowercase "dloc_number"
                dloc_number_attr = attributes.get('dloc_number') # Use lowercase 'dloc_number'
                if isinstance(dloc_number_attr, dict):
                    pole_number = dloc_number_attr.get('-Imported') or dloc_number_attr.get('assessment')
                elif isinstance(dloc_number_attr, str):
                    pole_number = dloc_number_attr
                    
            # For backward compatibility, check capitalized versions as well
            if not pole_number:
                pole_number = attributes.get('PL_number') or attributes.get('DLOC_number')
            
            norm_pole_number = normalize_pole_id(pole_number)
            
            # Safely get other attributes with type checking
            pole_owner_data = attributes.get('pole_owner') # Use lowercase 'pole_owner'
            pole_owner = None
            if isinstance(pole_owner_data, dict):
                pole_owner = pole_owner_data.get('multi_added') or pole_owner_data.get('assessment') or pole_owner_data.get('-Imported')
            elif isinstance(pole_owner_data, str):
                pole_owner = pole_owner_data
                
            # For backward compatibility, check capitalized version as well
            if not pole_owner:
                pole_owner_cap = attributes.get('PoleOwner')
                if isinstance(pole_owner_cap, dict):
                    pole_owner = pole_owner_cap.get('assessment') or pole_owner_cap.get('-Imported')
                elif isinstance(pole_owner_cap, str):
                    pole_owner = pole_owner_cap
            
            pole_height_data = attributes.get('pole_height') # Use lowercase 'pole_height'
            pole_height = None
            if isinstance(pole_height_data, dict) and pole_height_data:
                pole_height = next(iter(pole_height_data.values()), None)
            elif isinstance(pole_height_data, (str, int, float)): # Handle if it's a direct value
                pole_height = str(pole_height_data)
                
            # For backward compatibility, check capitalized version as well
            if not pole_height:
                pole_height_cap = attributes.get('PoleHeight')
                if isinstance(pole_height_cap, dict):
                    pole_height = pole_height_cap.get('assessment') or pole_height_cap.get('-Imported')
                elif isinstance(pole_height_cap, (str, int, float)):
                    pole_height = str(pole_height_cap)
            
            pole_class_data = attributes.get('pole_class') # Use lowercase 'pole_class'
            pole_class = None
            if isinstance(pole_class_data, dict) and pole_class_data:
                pole_class = pole_class_data.get('one') or next(iter(pole_class_data.values()), None)
            elif isinstance(pole_class_data, (str, int, float)): # Handle if it's a direct value
                pole_class = str(pole_class_data)
                
            # For backward compatibility, check capitalized version as well
            if not pole_class:
                pole_class_cap = attributes.get('PoleClass')
                if isinstance(pole_class_cap, dict):
                    pole_class = pole_class_cap.get('assessment') or pole_class_cap.get('-Imported')
                elif isinstance(pole_class_cap, (str, int, float)):
                    pole_class = str(pole_class_cap)
            
            pole_species_data = attributes.get('pole_species') # Use lowercase 'pole_species'
            pole_species = None
            if isinstance(pole_species_data, dict) and pole_species_data:
                pole_species = pole_species_data.get('one') or \
                               pole_species_data.get('-Imported') or \
                               pole_species_data.get('pole_species*') or \
                               next(iter(pole_species_data.values()), None)
            elif isinstance(pole_species_data, str):
                pole_species = pole_species_data
                
            # Special handling for birthmark_brand structure if that's where species is sometimes found
            if not pole_species:
                birthmark_brand_data = attributes.get('birthmark_brand', {})
                if isinstance(birthmark_brand_data, dict) and birthmark_brand_data:
                    first_birthmark_entry = next(iter(birthmark_brand_data.values()), {})
                    if isinstance(first_birthmark_entry, dict):
                        pole_species = first_birthmark_entry.get('pole_species*')
                        
            # For backward compatibility, check capitalized version as well
            if not pole_species:
                pole_species_cap = attributes.get('PoleSpecies')
                if isinstance(pole_species_cap, dict):
                    pole_species = pole_species_cap.get('assessment') or pole_species_cap.get('-Imported')
                elif isinstance(pole_species_cap, str):
                    pole_species = pole_species_cap
            
            # Get SPIDAcalc pole attributes if available
            spida_pole_height = None
            spida_pole_class = None
            spida_pole_species = None
            has_pole_attribute_conflict = False
            
            if spida and norm_pole_number in spida_lookup:
                loc = spida_lookup[norm_pole_number]
                # Extract pole attributes from SPIDAcalc
                spida_pole_height = None
                spida_pole_class = None
                spida_pole_species = None
                
                # Check if loc is a dictionary (expected) or a list (unexpected but possible)
                if isinstance(loc, dict):
                    # Normal case - loc is a dictionary
                    pole_tags = loc.get('poleTags', {})
                    if isinstance(pole_tags, dict):
                        spida_pole_height = pole_tags.get('height')
                        spida_pole_class = pole_tags.get('class')
                        spida_pole_species = pole_tags.get('species')
                elif isinstance(loc, list) and loc:
                    # Handle case where loc is a list - use the first item
                    print(f"[INFO] SPIDAcalc location for pole {pole_number} is a list with {len(loc)} items, using first item")
                    first_loc = loc[0]
                    if isinstance(first_loc, dict):
                        pole_tags = first_loc.get('poleTags', {})
                        if isinstance(pole_tags, dict):
                            spida_pole_height = pole_tags.get('height')
                            spida_pole_class = pole_tags.get('class')
                            spida_pole_species = pole_tags.get('species')
                
                # Check for conflicts
                if spida_pole_height and pole_height and spida_pole_height != pole_height:
                    has_pole_attribute_conflict = True
                    print(f"[INFO] Pole height conflict for pole {pole_number}: Katapult={pole_height}, SPIDA={spida_pole_height}")
                
                if spida_pole_class and pole_class and spida_pole_class != pole_class:
                    has_pole_attribute_conflict = True
                    print(f"[INFO] Pole class conflict for pole {pole_number}: Katapult={pole_class}, SPIDA={spida_pole_class}")
                
                if spida_pole_species and pole_species and spida_pole_species != pole_species:
                    has_pole_attribute_conflict = True
                    print(f"[INFO] Pole species conflict for pole {pole_number}: Katapult={pole_species}, SPIDA={spida_pole_species}")
                
                # Apply pole attribute conflict resolution strategy
                if has_pole_attribute_conflict:
                    if pole_attribute_strategy == 'PREFER_SPIDA':
                        print(f"[INFO] Using SPIDA pole attributes for pole {pole_number} (PREFER_SPIDA strategy)")
                        pole_height = spida_pole_height or pole_height
                        pole_class = spida_pole_class or pole_class
                        pole_species = spida_pole_species or pole_species
                    elif pole_attribute_strategy == 'HIGHLIGHT_DIFFERENCES':
                        # Mark conflicts for highlighting in the report
                        if spida_pole_height and pole_height and spida_pole_height != pole_height:
                            pole_height = f"{pole_height} (SPIDA: {spida_pole_height})"
                        if spida_pole_class and pole_class and spida_pole_class != pole_class:
                            pole_class = f"{pole_class} (SPIDA: {spida_pole_class})"
                        if spida_pole_species and pole_species and spida_pole_species != pole_species:
                            pole_species = f"{pole_species} (SPIDA: {spida_pole_species})"
                        print(f"[INFO] Highlighting pole attribute differences for pole {pole_number} (HIGHLIGHT_DIFFERENCES strategy)")
                    else:  # Default to PREFER_KATAPULT
                        print(f"[INFO] Using Katapult pole attributes for pole {pole_number} (PREFER_KATAPULT strategy)")
                        # No changes needed as we already have Katapult values
            
            pole_structure = f"{pole_height or ''}-{pole_class or ''} {pole_species or ''}".strip()
            if not pole_structure:
                # Try alternate attribute names
                pole_structure = attributes.get('pole_structure') or ''
            
            # Check lowercase version first
            construction_grade_data = attributes.get('construction_grade_analysis')
            construction_grade = None
            if isinstance(construction_grade_data, dict):
                construction_grade = construction_grade_data.get('assessment') or construction_grade_data.get('-Imported') or next(iter(construction_grade_data.values()), None)
            elif isinstance(construction_grade_data, str):
                construction_grade = construction_grade_data
                
            # Also try alternate attribute names for construction grade
            if not construction_grade:
                # Try other lowercase variations
                for attr_name in ['construction_grade', 'construction_grade_determination']:
                    attr_data = attributes.get(attr_name)
                    if isinstance(attr_data, dict):
                        construction_grade = attr_data.get('assessment') or attr_data.get('-Imported') or next(iter(attr_data.values()), None)
                        if construction_grade:
                            break
                    elif isinstance(attr_data, str):
                        construction_grade = attr_data
                        break
            
            final_passing_capacity_data = attributes.get('final_passing_capacity_%', {})
            final_passing_capacity_value = None
            if isinstance(final_passing_capacity_data, dict) and final_passing_capacity_data:
                final_passing_capacity_value = next(iter(final_passing_capacity_data.values()), None)
            elif isinstance(final_passing_capacity_data, str): # If it can be a direct string value
                final_passing_capacity_value = final_passing_capacity_data
                
            # For backward compatibility, check for assessment key as well
            if isinstance(final_passing_capacity_data, dict) and not final_passing_capacity_value:
                final_passing_capacity_value = final_passing_capacity_data.get('assessment')
                
            pla_percentage = f"{final_passing_capacity_value}%" if final_passing_capacity_value else 'N/A'

            # First get all the notes fields - needed for both proposed equipment and pole status
            # Check lowercase version first for kat_mr_notes
            kat_mr_notes_data = attributes.get('kat_mr_notes')
            kat_mr_notes = None
            if isinstance(kat_mr_notes_data, dict):
                kat_mr_notes = kat_mr_notes_data.get('assessment') or kat_mr_notes_data.get('-Imported') or next(iter(kat_mr_notes_data.values()), None)
            elif isinstance(kat_mr_notes_data, str):
                kat_mr_notes = kat_mr_notes_data
            
            # For backward compatibility, check capitalized version as well
            if not kat_mr_notes:
                kat_mr_notes_cap = attributes.get('kat_MR_notes')
                if isinstance(kat_mr_notes_cap, dict):
                    kat_mr_notes = kat_mr_notes_cap.get('assessment') or kat_mr_notes_cap.get('-Imported')
                elif isinstance(kat_mr_notes_cap, str):
                    kat_mr_notes = kat_mr_notes_cap
            
            # Check stress_MR_notes as well
            stress_mr_notes_data = attributes.get('stress_MR_notes')
            stress_mr_notes = None
            if isinstance(stress_mr_notes_data, dict):
                stress_mr_notes = stress_mr_notes_data.get('assessment') or stress_mr_notes_data.get('-Imported') or next(iter(stress_mr_notes_data.values()), None)
            elif isinstance(stress_mr_notes_data, str):
                stress_mr_notes = stress_mr_notes_data
            
            # For backward compatibility, check capitalized version as well
            if not stress_mr_notes:
                stress_mr_notes_cap = attributes.get('stress_MR_notes')
                if isinstance(stress_mr_notes_cap, dict):
                    stress_mr_notes = stress_mr_notes_cap.get('assessment') or stress_mr_notes_cap.get('-Imported')
                elif isinstance(stress_mr_notes_cap, str):
                    stress_mr_notes = stress_mr_notes_cap
                    
            # Collect all relevant notes fields for equipment detection
            notes_fields = []
            if kat_mr_notes:
                notes_fields.append(kat_mr_notes)
            if stress_mr_notes:
                notes_fields.append(stress_mr_notes)
                
            # Proposed Riser/Guy - Check SPIDAcalc data first, then fall back to Katapult notes
            proposed_riser = 'No'
            proposed_guy = 'No'
            
            # Check SPIDAcalc data for proposed risers and guys if available
            if spida and norm_pole_number in spida_lookup:
                spida_pole_data = spida_lookup[norm_pole_number]
                
                # Check for proposed riser in SPIDAcalc
                if check_proposed_riser_spida(spida_pole_data):
                    proposed_riser = 'Yes'
                    print(f"[INFO] Found proposed riser in SPIDAcalc data for pole {pole_number}")
                
                # Check for proposed guy in SPIDAcalc
                if check_proposed_guy_spida(spida_pole_data):
                    proposed_guy = 'Yes'
                    print(f"[INFO] Found proposed guy in SPIDAcalc data for pole {pole_number}")
                    
                # Get construction grade from SPIDAcalc if not already set
                if not construction_grade or construction_grade == 'N/A':
                    spida_construction_grade = get_construction_grade_spida(spida)
                    if spida_construction_grade:
                        construction_grade = spida_construction_grade
                        print(f"[INFO] Using construction grade '{construction_grade}' from SPIDAcalc for pole {pole_number}")
            
            # If still not found, check Katapult notes
            if proposed_riser == 'No':
                for note in notes_fields:
                    if check_proposed_equipment_in_notes(note, 'riser'):
                        proposed_riser = 'Yes'
                        print(f"[INFO] Found proposed riser in notes for pole {pole_number}")
                        break
            
            if proposed_guy == 'No':
                for note in notes_fields:
                    if check_proposed_equipment_in_notes(note, 'guy'):
                        proposed_guy = 'Yes'
                        print(f"[INFO] Found proposed guy in notes for pole {pole_number}")
                        break

            # Helper function to get pole number from node ID
            def get_pole_number_from_node_id(katapult, node_id):
                node = katapult.get('nodes', {}).get(node_id, {})
                attributes = node.get('attributes', {})
                
                # Check various possible paths for pole number - using same logic as main code
                pole_number = None
                pole_number_attr = attributes.get('PoleNumber') # Check capitalized "PoleNumber" first
                if isinstance(pole_number_attr, dict):
                    pole_number = pole_number_attr.get('-Imported') or pole_number_attr.get('assessment')
                elif isinstance(pole_number_attr, str):
                    pole_number = pole_number_attr

                if not pole_number: # If not found, try lowercase "pl_number"
                    pl_number_attr = attributes.get('pl_number') # Use lowercase 'pl_number'
                    if isinstance(pl_number_attr, dict):
                        pole_number = pl_number_attr.get('-Imported') or pl_number_attr.get('assessment')
                    elif isinstance(pl_number_attr, str):
                        pole_number = pl_number_attr

                if not pole_number: # If still not found, try lowercase "dloc_number"
                    dloc_number_attr = attributes.get('dloc_number') # Use lowercase 'dloc_number'
                    if isinstance(dloc_number_attr, dict):
                        pole_number = dloc_number_attr.get('-Imported') or dloc_number_attr.get('assessment')
                    elif isinstance(dloc_number_attr, str):
                        pole_number = dloc_number_attr
                        
                # For backward compatibility, check capitalized versions as well
                if not pole_number:
                    pole_number = attributes.get('PL_number') or attributes.get('DLOC_number')
                
                return pole_number
            
            # Existing Mid-Span Data (find lowest comm and lowest CPS electrical for spans connected to this pole)
            pole_connections = []
            
            # Only process connections that involve the current pole
            for conn_id, conn in katapult.get('connections', {}).items():
                # Check if this connection involves the current pole
                if conn.get('node_id_1') == node_id or conn.get('node_id_2') == node_id:
                    # Get the other pole number for the "To Pole" context
                    other_node_id = conn.get('node_id_2') if conn.get('node_id_1') == node_id else conn.get('node_id_1')
                    other_pole_number = get_pole_number_from_node_id(katapult, other_node_id)
                    
                    # Debug: Print connection info
                    print(f"[DEBUG] Processing connection {conn_id} between {pole_number} and {other_pole_number}")
                    print(f"[DEBUG] Connection structure: {json.dumps({k: type(v).__name__ for k, v in conn.items()}, indent=2)}")
                    print(f"[DEBUG] Connection {conn_id} has {len(conn.get('sections', {}))} sections")
                    
                    # Initialize lowest heights for this specific connection
                    connection_lowest_com = None
                    connection_lowest_cps = None
                    
                    # Process sections for this connection - sections is a dictionary with section_id as keys
                    for section_id, section in conn.get('sections', {}).items():
                        # Check if section is a dictionary before accessing its properties
                        if not isinstance(section, dict):
                            print(f"[DEBUG] Skipping non-dict section with ID {section_id}: {type(section)}")
                            continue
                            
                        print(f"[DEBUG] Section {section_id} structure: {json.dumps({k: type(v).__name__ for k, v in section.items()}, indent=2)}")
                        
                        # Photos are stored as a dictionary with photo_id as keys
                        photos = section.get('photos', {})
                        if not isinstance(photos, dict):
                            print(f"[DEBUG] Photos is not a dictionary: {type(photos)}")
                            continue
                            
                        for photo_id, photo_association in photos.items():
                            # Check if photo association is a dictionary before proceeding
                            if not isinstance(photo_association, dict):
                                print(f"[DEBUG] Skipping non-dict photo association: {photo_association}")
                                continue
                                
                            # FIX: Get the full photo data from the main photos dictionary
                            main_photo_data = katapult.get('photos', {}).get(photo_id, {})
                            if not isinstance(main_photo_data, dict):
                                print(f"[DEBUG] Skipping non-dict main_photo_data for ID {photo_id}")
                                continue
                                
                            # Now use main_photo_data to get photofirst_data
                            photofirst_data = main_photo_data.get('photofirst_data', {})
                            if not isinstance(photofirst_data, dict):
                                print(f"[DEBUG] Skipping photo with invalid photofirst_data: {photofirst_data}")
                                continue
                                
                            # Handle wire data as a dictionary (not a list)
                            wire_data = photofirst_data.get('wire', {})
                            print(f"[DEBUG] Wire data type: {type(wire_data)}, length: {len(wire_data) if hasattr(wire_data, '__len__') else 'N/A'}")
                            
                            wire_items = []
                            
                            if isinstance(wire_data, list):
                                wire_items = wire_data
                            elif isinstance(wire_data, dict):
                                wire_items = list(wire_data.values())  # Convert dict_values to list
                            else:
                                print(f"[DEBUG] Unexpected wire data type in connection section: {type(wire_data)}")
                                continue
                            
                            print(f"[DEBUG] Processing {len(wire_items)} wire items")
                            
                            # ---- START NEW DEBUG LOGGING ----
                            if wire_items:  # Only print if there are wires to process in this photo
                                all_trace_keys = list(katapult.get('traces', {}).keys())
                                print(f"[DEBUG] ---- Trace Lookup Debug for Photo {photo_id} ----")
                                print(f"[DEBUG] Number of traces available in katapult['traces']: {len(all_trace_keys)}")
                                if all_trace_keys:
                                    print(f"[DEBUG] Sample of available trace_ids in katapult['traces'] (first 20): {all_trace_keys[:20]}")
                                else:
                                    print(f"[DEBUG] katapult['traces'] appears to be empty or not found.")
                            # ---- END NEW DEBUG LOGGING ----
                                
                            for wire in wire_items:
                                if not isinstance(wire, dict):
                                    print(f"[DEBUG] Skipping non-dict wire in connection: {wire}")
                                    continue
                                    
                                # Get trace ID from wire
                                raw_trace_id_from_wire = wire.get('_trace')
                                print(f"[DEBUG] Raw _trace from wire: '{raw_trace_id_from_wire}'")
                                
                                if not raw_trace_id_from_wire:
                                    print(f"[DEBUG] Wire missing _trace ID in connection. Wire data: {json.dumps(wire)}")
                                    continue
                                
                                # Use our enhanced robust trace lookup function
                                trace_id = raw_trace_id_from_wire.strip()
                                print(f"[DEBUG] Looking up trace_id: '{trace_id}'")
                                trace = get_trace_by_id(katapult, trace_id)
                                
                                # Log the result for debugging
                                if trace:
                                    print(f"[DEBUG] SUCCESS: Found trace data for '{trace_id}'")
                                else:
                                    print(f"[DEBUG] NOTICE: No trace data found for '{trace_id}'")
                                
                                print(f"[DEBUG] Trace object content: {json.dumps(trace)}")

                                # Extract wire metadata using our helper function
                                wire_metadata = extract_wire_metadata(wire, trace)
                                owner = wire_metadata['owner']
                                cable_type = wire_metadata['cable_type']
                                is_proposed = wire_metadata['is_proposed']
                                
                                print(f"[DEBUG] Wire owner: {owner} (raw: '{trace.get('company', '')}'), cable type: {cable_type}")
                                
                                # Process wire height using helper function
                                h = process_wire_height(wire)
                                print(f"[DEBUG] Processed wire height: {h}")
                                if h is None:
                                    print(f"[DEBUG] Wire has invalid or missing height")
                                    continue
                                
                                # --- COMMUNICATION WIRES ---
                                # Expanded logic for communication classification
                                is_comm = False
                                
                                # If owner is not CPS, check for comm indicators in cable type or company name
                                if owner and 'cps' not in owner.lower():
                                    # Check for comm keywords in cable_type
                                    cable_type_comm = trace.get('cable_type', '') if isinstance(trace, dict) else ''
                                    if any(comm_type in (cable_type_comm or '').lower()
                                           for comm_type in ['com', 'fiber', 'telco', 'cable', 'telephone', 'catv']):
                                        is_comm = True
                                    
                                    # If company name itself suggests comm (fallback)
                                    elif any(comm_co in owner.lower() 
                                            for comm_co in ['att', 'spectrum', 'comcast', 'frontier', 'verizon', 'telco']):
                                        is_comm = True
                                
                                if is_comm:
                                    print(f"[DEBUG] Identified communication wire at height {h}")
                                    if connection_lowest_com is None or h < connection_lowest_com:
                                        connection_lowest_com = h
                                
                                # --- CPS ELECTRICAL WIRES ---
                                # Expanded logic for CPS electrical classification
                                is_cps_elec = False
                                
                                # If owner contains CPS, check for electrical indicators
                                if owner and 'cps' in owner.lower():
                                    # Broader check for electric-related types
                                    cable_type_elec = trace.get('cable_type', '') if isinstance(trace, dict) else ''
                                    if any(elec_type in (cable_type_elec or '').lower()
                                           for elec_type in ['neutral', 'secondary', 'primary', 'electric', 'power', 'phase']):
                                        is_cps_elec = True
                                    # If no cable type but it's CPS, assume it's electrical as fallback
                                    elif isinstance(trace, dict) and not trace.get('cable_type'):
                                        is_cps_elec = True
                                    elif not isinstance(trace, dict): # If trace is not a dict, and owner is CPS, assume electrical
                                        is_cps_elec = True

                                if is_cps_elec:
                                    print(f"[DEBUG] Identified CPS electrical wire at height {h}")
                                    if connection_lowest_cps is None or h < connection_lowest_cps:
                                        connection_lowest_cps = h
                    
                    # Add this connection's data to the pole's connections list
                    print(f"[DEBUG] Connection summary - lowest comm: {connection_lowest_com}, lowest CPS: {connection_lowest_cps}")
                    pole_connections.append({
                        'from_pole': pole_number,
                        'to_pole': other_pole_number,
                        'lowest_com': connection_lowest_com,
                        'lowest_cps': connection_lowest_cps
                    })
            
                # If pole has connections, use the first one for the main report
                # (This can be enhanced to handle multiple connections if needed)
                if pole_connections:
                    # Make sure connections have connection_id for later reference
                    for i, conn_summary in enumerate(pole_connections):
                        if 'connection_id' not in conn_summary and i < len(list(katapult.get('connections', {}).keys())):
                            conn_id = list(katapult.get('connections', {}).keys())[i]
                            conn_summary['connection_id'] = conn_id

                    primary_connection = pole_connections[0]  # Or use some selection logic
                    existing_midspan_lowest_com = inches_to_feet_inches_str(primary_connection['lowest_com'])
                    existing_midspan_lowest_cps_electrical = inches_to_feet_inches_str(primary_connection['lowest_cps'])
                    from_pole = primary_connection['from_pole']
                    to_pole = primary_connection['to_pole']
                    print(f"[DEBUG] Using midspan data from connection: {from_pole} to {to_pole}")
                else:
                    existing_midspan_lowest_com = 'N/A'
                    existing_midspan_lowest_cps_electrical = 'N/A'
                    from_pole = pole_number
                    to_pole = 'N/A'
                    print(f"[DEBUG] No connections found for pole {pole_number}")

            # DEBUG: Print normalized pole number
            print(f"[DEBUG] Katapult pole_number: {pole_number}, normalized: {norm_pole_number}")
            
            # Skip processing if we couldn't find a pole number
            if not pole_number:
                print(f"[DEBUG] Skipping node {node_id} - no pole number found")
                continue
                
            # Skip if we have target poles and this pole is not in the list
            if normalized_target_poles and norm_pole_number not in normalized_target_poles:
                print(f"[DEBUG] Skipping pole {pole_number} - not in target list")
                continue
            
            # Track owners with attachment height changes for midspan proposed calculation
            owners_with_pole_attachment_changes = set()
            
            # Attachers: build list with description, heights, etc.
            attacher_map = {}
            # --- SPIDAcalc as primary source for attachments ---
            if spida and norm_pole_number in spida_lookup:
                print(f"[DEBUG] Found matching SPIDAcalc location for pole {norm_pole_number}")
                loc = spida_lookup[norm_pole_number]
                measured_design = None
                recommended_design = None
                for d in loc.get('designs', []):
                    if d.get('label', '').lower() == 'measured design':
                        measured_design = d
                    if d.get('label', '').lower() == 'recommended design':
                        recommended_design = d
                # Build a dict of all unique attachments (wires and equipment) from both designs
                attachments = {}
                
                # Add extra debug info for pole PL410620
                if norm_pole_number == "410620":
                    print(f"[DEBUG] ===== DETAILED DEBUG FOR POLE PL410620 =====")
                    print(f"[DEBUG] Processing SPIDAcalc designs for pole PL410620")

                # Helper functions for key generation
                def create_simple_key(owner, desc):
                    return f"{owner}||{desc}".strip()
                    
                def create_detailed_key(owner, desc, usage_group=None, id_str=None):
                    normalized_owner = normalize_owner(owner)
                    key_parts = [normalized_owner]
                    if desc:
                        key_parts.append(desc.strip())
                    if usage_group:
                        key_parts.append(usage_group.strip())
                    if id_str:
                        key_parts.append(id_str.strip())
                    return "||".join(key_parts)

                # Measured Design (existing)
                if measured_design:
                    for wire in measured_design.get('structure', {}).get('wires', []):
                        owner = wire.get('owner', {}).get('id', '')
                        desc = wire.get('clientItem', {}).get('description', '')
                        usage_group = wire.get('usageGroup', '')
                        id_str = wire.get('id', '')
                        meters = wire.get('attachmentHeight', {}).get('value')
                        midspan_meters = wire.get('midspanHeight', {}).get('value')
                        
                        # Try both a simple key and a more detailed key
                        simple_key = create_simple_key(owner, desc)
                        detailed_key = create_detailed_key(owner, desc, usage_group, id_str)
                        
                        # For pole PL410620, log detailed wire information
                        if norm_pole_number == "410620":
                            print(f"[DEBUG] PL410620 Measured Wire: owner={owner}, desc={desc}, usage_group={usage_group}, id={id_str}, height={meters}m ({float(meters) * 39.3701 if meters is not None else 0} inches)")
                        
                        attachment_data = {
                            'description': f"{owner} {desc}".strip(),
                            'existing_height': meters_to_feet_inches_str(meters),
                            'proposed_height': 'N/A',
                            'midspan_proposed': 'N/A',
                            'raw_existing_height_inches': float(meters) * 39.3701 if meters is not None else 0,
                            'raw_existing_midspan_inches': float(midspan_meters) * 39.3701 if midspan_meters is not None else 0,
                            'existing_midspan_height': meters_to_feet_inches_str(midspan_meters) if midspan_meters is not None else 'N/A',
                            'wire_id': id_str,  # Store wire ID for more accurate matching
                            'usage_group': usage_group  # Store usage group for more accurate matching
                        }
                        
                        # Store under both keys to increase chance of matching
                        attachments[simple_key] = attachment_data
                        if simple_key != detailed_key:
                            attachments[detailed_key] = attachment_data
                            
                    for eq in measured_design.get('structure', {}).get('equipments', []):
                        owner = eq.get('owner', {}).get('id', '')
                        desc = eq.get('clientItem', {}).get('type', '')
                        id_str = eq.get('id', '')
                        meters = eq.get('attachmentHeight', {}).get('value')
                        
                        # Try both a simple key and a more detailed key
                        simple_key = create_simple_key(owner, desc)
                        detailed_key = create_detailed_key(owner, desc, None, id_str)
                        
                        # For pole PL410620, log detailed equipment information
                        if norm_pole_number == "410620":
                            print(f"[DEBUG] PL410620 Measured Equipment: owner={owner}, desc={desc}, id={id_str}, height={meters}m ({float(meters) * 39.3701 if meters is not None else 0} inches)")
                        
                        attachment_data = {
                            'description': f"{owner} {desc}".strip(),
                            'existing_height': meters_to_feet_inches_str(meters),
                            'proposed_height': 'N/A',
                            'midspan_proposed': 'N/A',
                            'raw_existing_height_inches': float(meters) * 39.3701 if meters is not None else 0,
                            'equipment_id': id_str  # Store equipment ID for more accurate matching
                        }
                        
                        # Store under both keys to increase chance of matching
                        attachments[simple_key] = attachment_data
                        if simple_key != detailed_key:
                            attachments[detailed_key] = attachment_data
                # Recommended Design (proposed)
                if recommended_design:
                    for wire in recommended_design.get('structure', {}).get('wires', []):
                        owner = wire.get('owner', {}).get('id', '')
                        desc = wire.get('clientItem', {}).get('description', '')
                        usage_group = wire.get('usageGroup', '')
                        id_str = wire.get('id', '')
                        meters = wire.get('attachmentHeight', {}).get('value')
                        midspan_meters = wire.get('midspanHeight', {}).get('value')
                        
                        # Try various keys to increase chances of matching
                        simple_key = create_simple_key(owner, desc)
                        detailed_key = create_detailed_key(owner, desc, usage_group, id_str)
                        
                        # For pole PL410620, log detailed wire information
                        if norm_pole_number == "410620":
                            print(f"[DEBUG] PL410620 Recommended Wire: owner={owner}, desc={desc}, usage_group={usage_group}, id={id_str}, height={meters}m ({float(meters) * 39.3701 if meters is not None else 0} inches)")
                            
                        # Try to match with existing attachment - try multiple matching strategies
                        matched_key = None
                        for try_key in [simple_key, detailed_key]:
                            if try_key in attachments:
                                matched_key = try_key
                                break
                        
                        # If no match found using keys, try to match by wire ID
                        if not matched_key:
                            for att_key, att_data in attachments.items():
                                if att_data.get('wire_id') == id_str and id_str:  # If we have IDs and they match
                                    matched_key = att_key
                                    break
                                    
                        # For Charter specifically, try to be more flexible with matching
                        if not matched_key and 'charter' in owner.lower():
                            for att_key, att_data in attachments.items():
                                att_desc = att_data.get('description', '')
                                if 'charter' in att_desc.lower() and (
                                    'fiber' in att_desc.lower() and 'fiber' in desc.lower() or
                                    'coax' in att_desc.lower() and 'coax' in desc.lower()
                                ):
                                    matched_key = att_key
                                    if norm_pole_number == "410620":
                                        print(f"[DEBUG] PL410620 Charter special match found: {att_desc}")
                                    break
                        
                        if matched_key:
                            # We found a matching existing attachment
                            existing_height_raw = attachments[matched_key].get('raw_existing_height_inches', 0)
                            proposed_height_raw = float(meters) * 39.3701 if meters is not None else 0
                            
                            # For pole PL410620, log detailed height comparison information
                            if norm_pole_number == "410620":
                                print(f"[DEBUG] PL410620 Height comparison for {owner} {desc}: existing={existing_height_raw} inches, proposed={proposed_height_raw} inches")
                            
                            # Check if heights are different (using small threshold to account for precision issues)
                            height_diff = abs(existing_height_raw - proposed_height_raw)
                            if height_diff > 0.1:
                                attachments[matched_key]['proposed_height'] = meters_to_feet_inches_str(meters)
                                attachments[matched_key]['raw_proposed_height_inches'] = proposed_height_raw
                                
                                # For pole PL410620, log when a height change is detected
                                if norm_pole_number == "410620":
                                    print(f"[DEBUG] PL410620 HEIGHT CHANGE DETECTED for {owner} {desc}: {inches_to_feet_inches_str(existing_height_raw)} to {meters_to_feet_inches_str(meters)}, diff={height_diff} inches")
                            else:
                                # Heights are the same, use N/A to indicate no change needed
                                attachments[matched_key]['proposed_height'] = 'N/A'
                                
                            # Process midspan heights
                            if midspan_meters is not None:
                                existing_midspan_raw = attachments[matched_key].get('raw_existing_midspan_inches', 0)
                                proposed_midspan_raw = float(midspan_meters) * 39.3701
                                
                                # Check if midspan heights are different
                                if abs(existing_midspan_raw - proposed_midspan_raw) > 0.1:
                                    attachments[matched_key]['midspan_proposed'] = meters_to_feet_inches_str(midspan_meters)
                                    attachments[matched_key]['raw_proposed_midspan_inches'] = proposed_midspan_raw
                                    print(f"[DEBUG] Midspan change detected for {matched_key}: {attachments[matched_key].get('existing_midspan_height', 'N/A')} to {meters_to_feet_inches_str(midspan_meters)}")
                        else:
                            # No matching existing attachment found - this is a new attachment
                            new_attachment_data = {
                                'description': f"{owner} {desc}".strip(),
                                'existing_height': 'N/A',
                                'proposed_height': meters_to_feet_inches_str(meters),
                                'midspan_proposed': 'N/A',
                                'raw_existing_height_inches': 0,
                                'raw_proposed_height_inches': float(meters) * 39.3701 if meters is not None else 0,
                                'wire_id': id_str,
                                'usage_group': usage_group
                            }
                            
                            # Store under both keys
                            attachments[simple_key] = new_attachment_data
                            if simple_key != detailed_key:
                                attachments[detailed_key] = new_attachment_data
                                
                    for eq in recommended_design.get('structure', {}).get('equipments', []):
                        owner = eq.get('owner', {}).get('id', '')
                        desc = eq.get('clientItem', {}).get('type', '')
                        id_str = eq.get('id', '')
                        meters = eq.get('attachmentHeight', {}).get('value')
                        
                        # Try various keys to increase chances of matching
                        simple_key = create_simple_key(owner, desc)
                        detailed_key = create_detailed_key(owner, desc, None, id_str)
                        
                        # For pole PL410620, log detailed equipment information
                        if norm_pole_number == "410620":
                            print(f"[DEBUG] PL410620 Recommended Equipment: owner={owner}, desc={desc}, id={id_str}, height={meters}m ({float(meters) * 39.3701 if meters is not None else 0} inches)")
                            
                        # Try to match with existing attachment
                        matched_key = None
                        for try_key in [simple_key, detailed_key]:
                            if try_key in attachments:
                                matched_key = try_key
                                break
                        
                        # If no match found using keys, try to match by equipment ID
                        if not matched_key:
                            for att_key, att_data in attachments.items():
                                if att_data.get('equipment_id') == id_str and id_str:  # If we have IDs and they match
                                    matched_key = att_key
                                    break
                        
                        if matched_key:
                            # We found a matching existing attachment
                            existing_height_raw = attachments[matched_key].get('raw_existing_height_inches', 0)
                            proposed_height_raw = float(meters) * 39.3701 if meters is not None else 0
                            
                            # Check if heights are different (using small threshold to account for precision issues)
                            if abs(existing_height_raw - proposed_height_raw) > 0.1:
                                attachments[matched_key]['proposed_height'] = meters_to_feet_inches_str(meters)
                                attachments[matched_key]['raw_proposed_height_inches'] = proposed_height_raw
                            else:
                                # Heights are the same, use N/A to indicate no change needed
                                attachments[matched_key]['proposed_height'] = 'N/A'
                        else:
                            # No matching existing attachment found - this is a new attachment
                            new_attachment_data = {
                                'description': f"{owner} {desc}".strip(),
                                'existing_height': 'N/A',
                                'proposed_height': meters_to_feet_inches_str(meters),
                                'midspan_proposed': 'N/A',
                                'raw_existing_height_inches': 0,
                                'raw_proposed_height_inches': float(meters) * 39.3701 if meters is not None else 0,
                                'equipment_id': id_str
                            }
                            
                            # Store under both keys
                            attachments[simple_key] = new_attachment_data
                            if simple_key != detailed_key:
                                attachments[detailed_key] = new_attachment_data
                # If any attachments found in SPIDAcalc, use them
                if attachments:
                    # Remove duplicate entries (same description)
                    unique_attachments = {}
                    attachment_keys_by_description = {}
                    
                    # First, group by description
                    for key, value in attachments.items():
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
                            value = attachments[key]
                            if (value.get('existing_height', 'N/A') != 'N/A' and 
                                value.get('proposed_height', 'N/A') != 'N/A'):
                                best_key = key
                                break
                        
                        unique_attachments[desc] = attachments[best_key]
                    
                    print(f"[DEBUG] SPIDAcalc attachments for pole {norm_pole_number}: {list(unique_attachments.keys())}")
                    
                    # For pole PL410620, log all consolidated attachments
                    if norm_pole_number == "410620":
                        for desc, value in unique_attachments.items():
                            print(f"[DEBUG] PL410620 Consolidated attachment: {desc}")
                            print(f"[DEBUG]   Existing height: {value.get('existing_height', 'N/A')}")
                            print(f"[DEBUG]   Proposed height: {value.get('proposed_height', 'N/A')}")
                            if value.get('existing_height', 'N/A') != 'N/A' and value.get('proposed_height', 'N/A') != 'N/A':
                                print(f"[DEBUG]   Height change detected: {value.get('existing_height')} -> {value.get('proposed_height')}")
                    
                    # Ensure all values in attachments are dictionaries with description field
                    attacher_map = {}
                    for desc, value in unique_attachments.items():
                        try:
                            # Check if this attachment has both existing and proposed heights that differ
                            if (value.get('existing_height', 'N/A') != 'N/A' and 
                                value.get('proposed_height', 'N/A') != 'N/A' and
                                value.get('existing_height') != value.get('proposed_height')):
                                
                                # Extract owner from the description (first part before space)
                                owner_parts = desc.split(' ', 1)
                                owner = owner_parts[0] if owner_parts else ''
                                
                                # Normalize the owner name for consistent comparison
                                normalized_owner = normalize_owner(owner)
                                
                                # Add to the set of owners with changes
                                if normalized_owner:
                                    owners_with_pole_attachment_changes.add(normalized_owner)
                                    print(f"[DEBUG] Found attachment height change for owner: {normalized_owner}")
                                    
                                    # For pole PL410620, log when an owner with change is found
                                    if norm_pole_number == "410620":
                                        print(f"[DEBUG] PL410620 OWNER WITH HEIGHT CHANGE: {normalized_owner}, {desc}, {value.get('existing_height')} -> {value.get('proposed_height')}")
                            
                            attacher_map[desc] = value
                        except Exception as e:
                            print(f"[DEBUG] Error processing attachment {desc}: {str(e)}")
                else:
                    print(f"[DEBUG] No SPIDAcalc attachments found for pole {norm_pole_number}")
            else:
                if spida:
                    print(f"[DEBUG] No matching SPIDAcalc location for pole {norm_pole_number}")
            # Store Katapult attachments separately for potential conflict resolution
            katapult_attachments = {}
            
            # Process Katapult node photos for attachments
            print(f"[DEBUG] Processing Katapult node photos for pole {norm_pole_number}")
            photo_count = len(node.get('photos', {}))
            print(f"[DEBUG] Katapult node has {photo_count} photos")
            for photo_id, photo in node.get('photos', {}).items():
                    try:
                        # Check if photo is a dictionary before accessing its properties
                        if not isinstance(photo, dict):
                            print(f"[DEBUG] Skipping non-dict photo in node photos: {photo}")
                            continue
                            
                        # Check if photofirst_data exists and is a dictionary
                        photofirst_data = photo.get('photofirst_data', {})
                        if not isinstance(photofirst_data, dict):
                            print(f"[DEBUG] Skipping node photo with invalid photofirst_data: {photofirst_data}")
                            continue
                        
                        # Check if wire data exists and is a list or dictionary
                        wire_data = photofirst_data.get('wire', [])
                        if not wire_data:
                            print(f"[DEBUG] No wire data found in photo {photo_id}")
                            continue
                            
                        # Handle wire data as either list or dictionary
                        wire_items = []
                        if isinstance(wire_data, list):
                            wire_items = wire_data
                        elif isinstance(wire_data, dict):
                            wire_items = wire_data.values()
                        else:
                            print(f"[DEBUG] Unexpected wire data type: {type(wire_data)}")
                            continue
                            
                        for wire in wire_items:
                            if not isinstance(wire, dict):
                                print(f"[DEBUG] Skipping non-dict wire: {wire}")
                                continue
                                
                            # Get trace ID from wire
                            raw_trace_id_from_wire = wire.get('_trace')
                            print(f"[DEBUG] Raw _trace from wire: '{raw_trace_id_from_wire}'")
                            
                            if not raw_trace_id_from_wire:
                                print(f"[DEBUG] Wire missing _trace ID. Wire data: {json.dumps(wire)}")
                                continue
                            
                            # Use our enhanced robust trace lookup function
                            trace_id = raw_trace_id_from_wire.strip()
                            print(f"[DEBUG] Looking up trace_id: '{trace_id}'")
                            trace = get_trace_by_id(katapult, trace_id)
                            
                            # Log the result for debugging
                            if trace:
                                print(f"[DEBUG] SUCCESS: Found trace data for '{trace_id}'")
                            else:
                                print(f"[DEBUG] NOTICE: No trace data found for '{trace_id}'")
                            
                            print(f"[DEBUG] Trace object content: {json.dumps(trace)}")

                            # Extract wire metadata using our helper function
                            wire_metadata = extract_wire_metadata(wire, trace)
                            owner = wire_metadata['owner']
                            cable_type = wire_metadata['cable_type']
                            is_proposed = wire_metadata['is_proposed']
                            
                            desc = f"{owner} {cable_type}".strip()
                            print(f"[DEBUG] Found Katapult wire: {desc} (cable type: '{cable_type}', proposed: {is_proposed})")
                            
                            existing_height = wire.get('_measured_height')
                            if not existing_height:
                                print(f"[DEBUG] Wire missing _measured_height")
                                continue
                                
                            try:
                                existing_height_float = float(existing_height)
                                current_height = 0
                                
                                if desc in attacher_map and isinstance(attacher_map[desc], dict):
                                    current_height = attacher_map[desc].get('raw_existing_height_inches', 0)
                                
                                if desc not in attacher_map or existing_height_float > current_height:
                                    attacher_map[desc] = {
                                        'description': desc,
                                        'existing_height': inches_to_feet_inches_str(existing_height),
                                        'raw_existing_height_inches': existing_height_float,
                                        'proposed_height': 'N/A',  # Only set if there's a change
                                        'midspan_proposed': 'N/A',
                                    }
                            except (ValueError, TypeError) as e:
                                print(f"[DEBUG] Error converting height '{existing_height}' to float: {str(e)}")
                    except Exception as e:
                        print(f"[DEBUG] Error processing photo {photo_id}: {str(e)}")
            # If still no attachers, show 'No attachers found.'
            attachers_list = []
            for key, value in attacher_map.items():
                try:
                    if isinstance(value, dict):
                        attachers_list.append(value)
                    else:
                        print(f"[DEBUG] Skipping non-dict attacher '{key}': {value}")
                except Exception as e:
                    print(f"[DEBUG] Error processing attacher '{key}': {str(e)}")
            
            # Calculate Midspan Proposed value based on owners with attachment height changes
            lowest_proposed_midspan_for_changed_type_inches = None
            
            if owners_with_pole_attachment_changes:
                print(f"[DEBUG] Pole {pole_number}: Found attachment height changes for owners: {owners_with_pole_attachment_changes}")
                
                # Collect all midspan heights for owners with changes
                midspan_heights_for_changed_owners = []
                
                # Iterate through all connections for this pole
                for conn_summary in pole_connections:
                    # For each connection, we need to re-process the wire data to find wires belonging to owners with changes
                    conn_id = conn_summary.get('connection_id')
                    
                    if not conn_id:
                        print(f"[DEBUG] Missing connection_id in connection summary, skipping")
                        continue
                    
                    print(f"[DEBUG] Processing connection {conn_id} for midspan proposed calculation")
                    
                    # Get the connection data
                    conn = katapult.get('connections', {}).get(conn_id, {})
                    
                    # Process sections for this connection
                    for section_id, section in conn.get('sections', {}).items():
                        print(f"[DEBUG] Processing section {section_id} for midspan heights")
                        
                        # Process photos in this section
                        for photo_id, photo_association in section.get('photos', {}).items():
                            # Get the full photo data
                            main_photo_data = katapult.get('photos', {}).get(photo_id, {})
                            if not isinstance(main_photo_data, dict):
                                print(f"[DEBUG] Invalid main_photo_data for photo {photo_id}, skipping")
                                continue
                                
                            photofirst_data = main_photo_data.get('photofirst_data', {})
                            if not isinstance(photofirst_data, dict):
                                print(f"[DEBUG] Invalid photofirst_data for photo {photo_id}, skipping")
                                continue
                            
                            # Get wire data
                            wire_data = photofirst_data.get('wire', {})
                            wire_items = []
                            
                            if isinstance(wire_data, list):
                                wire_items = wire_data
                            elif isinstance(wire_data, dict):
                                wire_items = list(wire_data.values())
                            else:
                                print(f"[DEBUG] Invalid wire_data type: {type(wire_data)} for photo {photo_id}, skipping")
                                continue
                            
                            print(f"[DEBUG] Found {len(wire_items)} wire items in photo {photo_id}")
                            
                            # Process each wire
                            for wire in wire_items:
                                if not isinstance(wire, dict):
                                    continue
                                
                                # Get trace ID and lookup trace data
                                trace_id = wire.get('_trace', '').strip()
                                if not trace_id:
                                    print(f"[DEBUG] Wire missing trace_id in photo {photo_id}, skipping")
                                    continue
                                
                                trace = get_trace_by_id(katapult, trace_id)
                                if not trace:
                                    print(f"[DEBUG] Could not find trace data for trace_id {trace_id}, skipping")
                                    continue
                                
                                # Extract wire metadata
                                wire_metadata = extract_wire_metadata(wire, trace)
                                owner = wire_metadata['owner']
                                cable_type = wire_metadata['cable_type']
                                
                                if not owner:
                                    print(f"[DEBUG] Wire has no owner, trace_id: {trace_id}, skipping")
                                    continue
                                
                                # Normalize owner name for consistent comparison
                                normalized_owner = normalize_owner(owner)
                                
                                # Check if this wire belongs to an owner with attachment height changes
                                if normalized_owner in owners_with_pole_attachment_changes:
                                    print(f"[DEBUG] Found wire for owner with changes: {normalized_owner} (cable_type: {cable_type})")
                                    
                                    # Process wire height
                                    h = process_wire_height(wire)
                                    if h is not None:
                                        print(f"[DEBUG] Wire height for {normalized_owner}: {h} inches")
                                        # Add this height to our collection
                                        midspan_heights_for_changed_owners.append((normalized_owner, h))
                
                # Now find the lowest midspan height among all collected heights
                if midspan_heights_for_changed_owners:
                    # Sort by height (ascending)
                    midspan_heights_for_changed_owners.sort(key=lambda x: x[1])
                    
                    # Get the lowest height
                    lowest_owner, lowest_height = midspan_heights_for_changed_owners[0]
                    lowest_proposed_midspan_for_changed_type_inches = lowest_height
                    
                    print(f"[DEBUG] Lowest midspan height for changed owners: {lowest_height} inches (owner: {lowest_owner})")
                    print(f"[DEBUG] All midspan heights for changed owners: {midspan_heights_for_changed_owners}")
                else:
                    print(f"[DEBUG] No midspan heights found for owners with changes")
            
            # Convert the lowest midspan height to feet-inches string format
            midspan_proposed_str = inches_to_feet_inches_str(lowest_proposed_midspan_for_changed_type_inches)
            print(f"[DEBUG] Mid-Span Proposed for pole {pole_number}: {midspan_proposed_str}")
            
            # Now process midspan proposed values for attachers - AFTER we've calculated the pole-level midspan value
            if spida and recommended_design and measured_design:
                # Check for midspan height changes in SPIDAcalc data
                for attacher in attachers_list:
                    desc = attacher.get('description', '')
                    # Extract owner from the description (first part before space)
                    owner_parts = desc.split(' ', 1)
                    owner = owner_parts[0] if owner_parts else ''
                    normalized_owner = normalize_owner(owner)
                    
                    # Only process if we have both proposed and existing heights and they're different
                    if (attacher.get('proposed_height', 'N/A') != 'N/A' and 
                        attacher.get('existing_height', 'N/A') != 'N/A' and 
                        attacher.get('proposed_height') != attacher.get('existing_height')):
                        
                        print(f"[DEBUG] Processing midspan proposed value for attachment with height change: {desc}")
                        
                        # First check direct SPIDAcalc data
                        measured_wires = measured_design.get('structure', {}).get('wires', [])
                        recommended_wires = recommended_design.get('structure', {}).get('wires', [])
                        
                        # Find matching wires by description
                        spida_midspan_found = False
                        for m_wire in measured_wires:
                            m_owner = m_wire.get('owner', {}).get('id', '')
                            m_desc = m_wire.get('clientItem', {}).get('description', '')
                            m_wire_desc = f"{m_owner} {m_desc}".strip()
                            
                            if m_wire_desc == desc:
                                # Found matching wire in measured design
                                m_midspan = m_wire.get('midspanHeight', {}).get('value')
                                
                                # Look for same wire in recommended design
                                for r_wire in recommended_wires:
                                    r_owner = r_wire.get('owner', {}).get('id', '')
                                    r_desc = r_wire.get('clientItem', {}).get('description', '')
                                    r_wire_desc = f"{r_owner} {r_desc}".strip()
                                    
                                    if r_wire_desc == desc:
                                        # Found matching wire in recommended design
                                        r_midspan = r_wire.get('midspanHeight', {}).get('value')
                                        
                                        # Check if midspan heights differ
                                        if m_midspan is not None and r_midspan is not None:
                                            m_midspan_inches = float(m_midspan) * 39.3701
                                            r_midspan_inches = float(r_midspan) * 39.3701
                                            
                                            # If midspan heights differ by more than 0.1 inch, populate proposed value
                                            if abs(m_midspan_inches - r_midspan_inches) > 0.1:
                                                attacher['midspan_proposed'] = meters_to_feet_inches_str(r_midspan)
                                                print(f"[DEBUG] SPIDAcalc midspan change detected for {desc}: {meters_to_feet_inches_str(m_midspan)} to {meters_to_feet_inches_str(r_midspan)}")
                                                spida_midspan_found = True
                                                
                        # If we couldn't find SPIDAcalc midspan data but we know this owner has a height change
                        # For Katapult midspan data - use the pole-level calculated value
                        if not spida_midspan_found and normalized_owner in owners_with_pole_attachment_changes:
                            if lowest_proposed_midspan_for_changed_type_inches is not None:
                                # Use the lowest midspan height for wires of this owner
                                attacher['midspan_proposed'] = midspan_proposed_str
                                print(f"[DEBUG] Using pole-level midspan proposed value for {desc}: {midspan_proposed_str}")
            # Determine pole status based on make-ready notes and other factors
            pole_status = "No Change"  # Default status
            
            # Check for make-ready notes that indicate work needed
            if kat_mr_notes and isinstance(kat_mr_notes, str) and len(kat_mr_notes.strip()) > 0:
                pole_status = "Make-Ready Required"
            
            # Check for PLA percentage below threshold
            if final_passing_capacity_value and isinstance(final_passing_capacity_value, str):
                try:
                    pla_value = float(final_passing_capacity_value)
                    if pla_value < 85.0:  # Assuming 85% is the threshold
                        pole_status = "Issue Detected"
                except (ValueError, TypeError):
                    pass  # Keep default status if conversion fails
            
            pole = {
                'pole_owner': pole_owner or 'N/A',
                'pole_number': pole_number or 'N/A',
                'pole_structure': pole_structure or 'N/A',
                'proposed_riser': proposed_riser,
                'proposed_guy': proposed_guy,
                'pla_percentage': pla_percentage,
                'construction_grade': construction_grade or 'N/A',
                'existing_midspan_lowest_com': existing_midspan_lowest_com,
                'existing_midspan_lowest_cps_electrical': existing_midspan_lowest_cps_electrical,
                'midspan_proposed': midspan_proposed_str,  # Add the midspan proposed field
                'from_pole': from_pole or 'N/A',
                'to_pole': to_pole or 'N/A',
                'connections': pole_connections,  # Store all connections for potential future use
                'attachers': attachers_list,
                # Geographic data for map display
                'latitude': node.get('latitude'),
                'longitude': node.get('longitude'),
                'status': pole_status,  # Status for map display
            }
            poles.append(pole)
        except Exception as e:
            print(f"[DEBUG] Error processing node {node_id}: {str(e)}")
            print(f"[DEBUG] Node data: {json.dumps(node, indent=2)}")
            raise  # Re-raise the exception after logging

    # Sort poles according to their order in the SPIDAcalc file if available
    if spida and spida_pole_order:
        # Create a function to get the sort key for each pole
        def get_pole_sort_key(pole):
            norm_pole_number = normalize_pole_id(pole.get('pole_number'))
            # If pole is in SPIDAcalc, use its order, otherwise use a high number to place it at the end
            return spida_pole_order.get(norm_pole_number, float('inf'))
        
        # Sort the poles list
        poles.sort(key=get_pole_sort_key)
        print(f"[INFO] Sorted {len(poles)} poles according to SPIDAcalc file order")
    
    return poles

def extract_wire_metadata(wire, trace):
    """
    Extract owner, cable type and other metadata from wire and trace data.
    
    Args:
        wire (dict): The wire data from Katapult
        trace (dict): The trace data from Katapult
        
    Returns:
        dict: Dictionary containing extracted metadata
    """
    owner = None
    cable_type = None
    wire_type = None
    
    # Extract owner with multiple fallbacks
    if isinstance(trace, dict):
        # Try direct company field
        owner = trace.get('company', '')
        
        # Fallback to attributes.attacher
        if (not owner or owner.strip() == '') and 'attributes' in trace:
            attacher = trace['attributes'].get('attacher', {})
            if isinstance(attacher, dict):
                owner = attacher.get('button_added', '') or attacher.get('-Imported', '')
            elif isinstance(attacher, str):
                owner = attacher
        
        # Additional fallback for owner field
        if (not owner or owner.strip() == '') and 'owner' in trace:
            trace_owner = trace.get('owner')
            if isinstance(trace_owner, dict):
                owner = trace_owner.get('id', '')
            elif isinstance(trace_owner, str):
                owner = trace_owner
                
        # Extract cable type with fallbacks
        cable_type = trace.get('cable_type', '')
        
        # Try to determine wire type from usageGroup or other indicators
        wire_type = trace.get('usageGroup', '').upper()
        
        # If no usageGroup, try to infer from cable_type
        if not wire_type and cable_type:
            cable_type_upper = cable_type.upper()
            if any(power_type in cable_type_upper for power_type in 
                  ['PRIMARY', 'NEUTRAL', 'SECONDARY', 'ELECTRICAL', 'POWER', 'PHASE']):
                wire_type = 'POWER'
            elif any(comm_type in cable_type_upper for comm_type in 
                    ['COM', 'FIBER', 'TELCO', 'CABLE', 'TELEPHONE', 'CATV']):
                wire_type = 'COMMUNICATION'
    
    # Normalize owner
    owner = normalize_owner(owner)
    
    # Final fallback for owner based on wire height
    if (not owner or owner.strip() == '') and wire:
        # Try to determine owner from other wire properties
        # For example, medium-high wires are often power, very high wires primary
        height = process_wire_height(wire)
        if height and height > 300:  # Very high wires (>25ft) are often power
            owner = "CPS ENERGY"  # Default to CPS for high wires
            wire_type = "POWER"
            if not cable_type:
                cable_type = "PRIMARY"
        elif height and height < 150:  # Low wires (<12.5ft) often communications
            if not wire_type:
                wire_type = "COMMUNICATION"
            if not cable_type:
                cable_type = "COMM LINE"
    
    # If we have a wire_type but no owner, make a reasonable guess
    if wire_type == 'POWER' and (not owner or owner.strip() == ''):
        owner = "CPS ENERGY"  # Assume power wires belong to the utility
    elif wire_type == 'COMMUNICATION' and (not owner or owner.strip() == ''):
        owner = "COMMUNICATIONS"  # Generic label for unidentified comm
    
    print(f"[DEBUG] Extracted wire metadata - Owner: '{owner}', Type: '{wire_type}', Cable: '{cable_type}'")
    
    return {
        'owner': owner,
        'cable_type': cable_type,
        'wire_type': wire_type,
        'is_proposed': trace.get('proposed', False) if isinstance(trace, dict) else False
    }

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

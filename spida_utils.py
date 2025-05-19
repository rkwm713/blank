# spida_utils.py
import re
from utils import normalize_pole_id

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

def get_pole_sequence_from_spidacalc(spida_data):
    """
    Determine the authoritative order of poles for the entire job from SPIDAcalc data.
    This sequence is essential for identifying backspans.
    
    Args:
        spida_data (dict): SPIDAcalc JSON data
        
    Returns:
        list: Ordered list of normalized pole IDs
    """
    pole_sequence = []
    
    if not spida_data:
        print(f"[DEBUG] No SPIDAcalc data provided, cannot extract pole sequence")
        return pole_sequence
    
    try:
        # Poles are ordered in leads > locations array
        for lead in spida_data.get('leads', []):
            for location in lead.get('locations', []):
                pole_label = location.get('label')
                if pole_label:
                    normalized_id = normalize_pole_id(pole_label)
                    if normalized_id and normalized_id not in pole_sequence:
                        pole_sequence.append(normalized_id)
    except Exception as e:
        print(f"[DEBUG] Error extracting pole sequence from SPIDAcalc: {str(e)}")
    
    print(f"[DEBUG] Extracted pole sequence from SPIDAcalc: {pole_sequence}")
    return pole_sequence

def filter_primary_operation_poles(pole_map):
    """
    Filter the pole map to identify which poles should be considered primary operations.
    Only poles that exist in the SPIDAcalc file should be marked as primary operations
    and receive sequence numbers.
    
    Args:
        pole_map (dict): The reconciliation map between SPIDAcalc and Katapult poles
        
    Returns:
        list: Normalized IDs of poles that should be treated as primary operations (in SPIDAcalc)
    """
    primary_poles = []
    
    for pole_id, info in pole_map.items():
        # Only consider poles that exist in SPIDAcalc as primary operations
        if info.get("spida_obj") is not None:
            primary_poles.append(pole_id)
            # Ensure the pole is explicitly marked as primary in the map
            info["is_primary"] = True
        else:
            # Explicitly mark non-SPIDAcalc poles as non-primary
            info["is_primary"] = False
            print(f"[DEBUG] Pole {pole_id} not found in SPIDAcalc, marked as reference only")
    
    print(f"[DEBUG] Identified {len(primary_poles)} primary operation poles (from SPIDAcalc): {primary_poles}")
    
    return primary_poles

def classify_pole_relationships(primary_poles, katapult_data, pole_map):
    """
    Classify the relationships between poles in the network to determine which are 
    reference poles, backspan poles, or primary operation poles.
    
    Args:
        primary_poles (list): List of normalized pole IDs that are primary operations
        katapult_data (dict): The full Katapult JSON data
        pole_map (dict): The reconciliation map between SPIDAcalc and Katapult
        
    Returns:
        dict: A mapping of primary poles to their related poles, categorized by relationship:
            {
                primary_pole_id: {
                    "reference_spans": [
                        {"to_pole": pole_id, "direction": direction, "is_backspan": bool}
                    ],
                    "main_span": {"to_pole": pole_id} or None
                }
            }
    """
    relationships = {}
    
    # Create node_id to pole_id mapping for quick lookups
    node_to_pole = {}
    for pole_id, info in pole_map.items():
        if info.get("katapult_node_id"):
            node_to_pole[info["katapult_node_id"]] = pole_id
    
    # Initialize relationship entries for each primary pole
    for pole_id in primary_poles:
        relationships[pole_id] = {
            "reference_spans": [],
            "main_span": None
        }
    
    # Process all connections in Katapult data
    for connection in katapult_data.get("connections", []):
        from_node = connection.get("from")
        to_node = connection.get("to")
        
        # Skip if missing node references
        if not from_node or not to_node:
            continue
        
        # Skip if can't map nodes to poles
        if from_node not in node_to_pole or to_node not in node_to_pole:
            continue
            
        from_pole = node_to_pole[from_node]
        to_pole = node_to_pole[to_node]
        
        # Get direction if available
        direction = connection.get("direction", "Unknown")
        
        # Check if this is a reference span
        is_reference = connection.get("button_added") == "reference"
        
        # Check if this is a backspan
        is_backspan = connection.get("backspan", False)
        
        # If from_pole is a primary pole, record this connection
        if from_pole in primary_poles:
            # If it's a reference span or backspan, add to references
            if is_reference or is_backspan:
                relationships[from_pole]["reference_spans"].append({
                    "to_pole": to_pole,
                    "direction": direction,
                    "is_backspan": is_backspan
                })
                print(f"[DEBUG] Added {'backspan' if is_backspan else 'reference'} from {from_pole} to {to_pole}")
            # Otherwise, if no main span is set yet, use this as the main span
            elif relationships[from_pole]["main_span"] is None:
                # Only set as main span if the to_pole is also a primary pole
                if to_pole in primary_poles:
                    relationships[from_pole]["main_span"] = {
                        "to_pole": to_pole
                    }
                    print(f"[DEBUG] Set main span from {from_pole} to {to_pole}")
                else:
                    # If to_pole is not primary, add as reference
                    relationships[from_pole]["reference_spans"].append({
                        "to_pole": to_pole,
                        "direction": direction,
                        "is_backspan": False
                    })
                    print(f"[DEBUG] Added non-primary reference from {from_pole} to {to_pole}")
    
    # Check for primary poles with no relationships
    for pole_id in primary_poles:
        if (not relationships[pole_id]["reference_spans"] and 
            relationships[pole_id]["main_span"] is None):
            print(f"[WARNING] Primary pole {pole_id} has no connected spans or references")
            
    return relationships

def get_pole_structure_spida(spida_pole_data):
    """
    Extract pole structure (height-class, species) from SPIDAcalc pole data.
    
    Args:
        spida_pole_data (dict): The pole data from SPIDAcalc for a single pole.
        
    Returns:
        str: Formatted pole structure string (e.g., "40-2 Southern Pine") or None.
    """
    if not spida_pole_data or not isinstance(spida_pole_data, dict):
        return None

    height = None
    pole_class = None # Renamed from 'class' to avoid keyword conflict
    species = None

    # SPIDAcalc often has pole details in 'poleTags' or directly in the pole object
    pole_tags = spida_pole_data.get('poleTags', {})
    if isinstance(pole_tags, dict):
        height = pole_tags.get('height')
        pole_class = pole_tags.get('class')
        species = pole_tags.get('species')

    # Fallback to direct attributes if not in poleTags
    if height is None:
        height = spida_pole_data.get('height')
    if pole_class is None:
        pole_class = spida_pole_data.get('class')
    if species is None:
        species = spida_pole_data.get('species')
        
    # Try to get from 'aliases' if still not found (common for height-class)
    if height is None or pole_class is None:
        aliases = spida_pole_data.get('aliases', [])
        if isinstance(aliases, list) and aliases:
            # Assuming the first alias might contain height-class like "40-2"
            first_alias_id = aliases[0].get('id')
            if isinstance(first_alias_id, str) and '-' in first_alias_id:
                parts = first_alias_id.split('-', 1)
                if height is None:
                    height = parts[0]
                if pole_class is None and len(parts) > 1:
                    pole_class = parts[1]
    
    if height and pole_class and species:
        return f"{height}-{pole_class} {species}"
    elif height and pole_class: # Species might be optional or defaulted elsewhere
        return f"{height}-{pole_class}"
    
    # Log if parts are missing
    missing_parts = []
    if not height: missing_parts.append("height")
    if not pole_class: missing_parts.append("class")
    if not species: missing_parts.append("species")
    if missing_parts:
        print(f"[DEBUG] Missing SPIDA pole structure parts for pole {spida_pole_data.get('externalId', 'Unknown')}: {', '.join(missing_parts)}")
        
    return None

def get_attacher_list_by_neutral(spida_pole_data):
    """
    Extract the list of attachers (owners) on a pole from the neutral wire's height downwards.
    This function processes both Measured and Recommended designs.
    
    Args:
        spida_pole_data (dict): The pole data from SPIDAcalc for a single pole.
        
    Returns:
        dict: A dictionary with two keys - 'measured' and 'recommended', each containing a list of 
              attachment objects sorted by height (descending) with details like:
                {
                    'owner': str,           # Owner ID/name
                    'type': str,            # Type (wire, equipment, guy, etc.)
                    'subtype': str,         # More specific type (e.g., COMMUNICATION_BUNDLE)
                    'height_m': float,      # Height in meters
                    'height_formatted': str, # Formatted height
                    'id': str               # Component ID
                }
    """
    if not spida_pole_data or not isinstance(spida_pole_data, dict):
        return {'measured': [], 'recommended': []}
    
    pole_label = spida_pole_data.get('label', 'Unknown Pole')
    print(f"[DEBUG] Getting attacher list for pole: {pole_label}")
    
    result = {
        'measured': [],
        'recommended': []
    }
    
    # Process each design
    for design in spida_pole_data.get('designs', []):
        design_label = design.get('label', '').lower()
        if design_label == 'measured design':
            key = 'measured'
        elif design_label == 'recommended design':
            key = 'recommended'
        else:
            continue  # Skip other designs
            
        print(f"[DEBUG] Processing {design_label} for pole {pole_label}")
        
        # Get the structure for this design
        structure = design.get('structure', {})
        if not structure:
            print(f"[DEBUG] No structure found in {design_label} for pole {pole_label}")
            continue
            
        # Step 1: Find the lowest neutral wire height
        neutral_height = None
        for wire in structure.get('wires', []):
            usage_group = wire.get('usageGroup', '').upper()
            if usage_group == 'NEUTRAL':
                height_value = wire.get('attachmentHeight', {}).get('value')
                if height_value is not None:
                    if neutral_height is None or height_value < neutral_height:
                        neutral_height = height_value
                        print(f"[DEBUG] Found neutral wire at height: {neutral_height}m in {design_label}")
        
        if neutral_height is None:
            print(f"[DEBUG] No neutral wire found in {design_label} for pole {pole_label}")
            continue
            
        # Step 2: Collect all attachments at or below neutral height
        attachments = []
        
        # Process wires
        for wire in structure.get('wires', []):
            height_value = wire.get('attachmentHeight', {}).get('value')
            owner_id = wire.get('owner', {}).get('id', 'Unknown')
            wire_id = wire.get('id', 'Unknown')
            
            # Only process wire if it has height and is at or below neutral height
            if height_value is not None and height_value <= neutral_height:
                usage_group = wire.get('usageGroup', '').upper()
                client_item = wire.get('clientItem', {})
                client_item_type = client_item.get('type', '')
                
                attachments.append({
                    'owner': owner_id,
                    'type': 'wire',
                    'subtype': usage_group if usage_group else client_item_type,
                    'height_m': height_value,
                    'height_formatted': f"{height_value:.4f} m",
                    'id': wire_id
                })
                print(f"[DEBUG] Added wire: {owner_id}, {usage_group}, {height_value}m, {wire_id}")
        
        # Process equipment
        for equip in structure.get('equipments', []):
            # Equipment can span a height range, so check if any part of it is at or below neutral
            attachment_height = equip.get('attachmentHeight', {}).get('value')
            bottom_height = equip.get('bottomHeight', {}).get('value', attachment_height)  # Use attachment if no bottom
            owner_id = equip.get('owner', {}).get('id', 'Unknown')
            equip_id = equip.get('id', 'Unknown')
            
            # If equipment's top or bottom is at or below neutral, include it
            if (attachment_height is not None and attachment_height <= neutral_height) or \
               (bottom_height is not None and bottom_height <= neutral_height):
                client_item = equip.get('clientItem', {})
                equip_type = client_item.get('type', 'Unknown')
                
                # Include equipment size/model in subtype if available
                size = client_item.get('size', '')
                subtype = f"{equip_type} - {size}" if size else equip_type
                
                attachments.append({
                    'owner': owner_id,
                    'type': 'equipment',
                    'subtype': subtype,
                    'height_m': attachment_height,  # Use top attachment point for sorting
                    'height_formatted': f"{attachment_height:.4f} m",
                    'id': equip_id,
                    'bottom_height_m': bottom_height,
                    'bottom_height_formatted': f"{bottom_height:.4f} m"
                })
                print(f"[DEBUG] Added equipment: {owner_id}, {equip_type}, top: {attachment_height}m, bottom: {bottom_height}m, {equip_id}")
        
        # Process guys
        for guy in structure.get('guys', []):
            height_value = guy.get('attachmentHeight', {}).get('value')
            owner_id = guy.get('owner', {}).get('id', 'Unknown')
            guy_id = guy.get('id', 'Unknown')
            
            # Only process guy if it has height and is at or below neutral height
            if height_value is not None and height_value <= neutral_height:
                client_item = guy.get('clientItem', {})
                guy_type = client_item.get('type', 'Guy Wire')
                
                attachments.append({
                    'owner': owner_id,
                    'type': 'guy',
                    'subtype': guy_type,
                    'height_m': height_value,
                    'height_formatted': f"{height_value:.4f} m",
                    'id': guy_id
                })
                print(f"[DEBUG] Added guy: {owner_id}, {guy_type}, {height_value}m, {guy_id}")
        
        # Process assemblies if present
        if 'assemblies' in structure:
            for assembly in structure.get('assemblies', []):
                # Get assembly details
                assembly_id = assembly.get('id', 'Unknown')
                owner_id = assembly.get('owner', {}).get('id', 'Unknown')
                distance_from_pole_top = assembly.get('distanceFromPoleTop', {}).get('value')
                
                if distance_from_pole_top is None:
                    print(f"[DEBUG] Assembly {assembly_id} has no distanceFromPoleTop, skipping")
                    continue
                
                # We need pole height to calculate absolute height of assembly components
                pole_height = structure.get('pole', {}).get('height')
                if not pole_height:
                    print(f"[DEBUG] Cannot determine pole height for assembly calculations, skipping assembly {assembly_id}")
                    continue
                
                # Calculate assembly top position (absolute AGL)
                assembly_top_height = pole_height - distance_from_pole_top
                
                # Get components from assembly
                assembly_components = []
                
                # Add assembly itself if it's at or below neutral
                if assembly_top_height <= neutral_height:
                    assembly_type = assembly.get('clientItem', {}).get('type', 'Assembly')
                    assembly_components.append({
                        'owner': owner_id,
                        'type': 'assembly',
                        'subtype': assembly_type,
                        'height_m': assembly_top_height,
                        'height_formatted': f"{assembly_top_height:.4f} m",
                        'id': assembly_id
                    })
                    print(f"[DEBUG] Added assembly: {owner_id}, {assembly_type}, {assembly_top_height}m, {assembly_id}")
                
                # Loop through contained equipment - this is simplified and may need enhancement
                # based on actual assembly structure in your data
                for item in assembly.get('items', []):
                    item_type = item.get('clientItem', {}).get('type', 'Unknown')
                    item_attach_height = item.get('attachmentHeight', {}).get('value')
                    
                    if item_attach_height is not None:
                        # Calculate absolute AGL for this item
                        item_absolute_height = assembly_top_height - item_attach_height
                        
                        if item_absolute_height <= neutral_height:
                            item_id = item.get('id', f"{assembly_id}_{item_type}")
                            
                            assembly_components.append({
                                'owner': owner_id,
                                'type': 'assembly_item',
                                'subtype': item_type,
                                'height_m': item_absolute_height,
                                'height_formatted': f"{item_absolute_height:.4f} m",
                                'id': item_id
                            })
                            print(f"[DEBUG] Added assembly item: {owner_id}, {item_type}, {item_absolute_height}m, {item_id}")
                
                # Add assembly components to main attachments list
                attachments.extend(assembly_components)
        
        # Sort all attachments by height (descending)
        sorted_attachments = sorted(
            attachments, 
            key=lambda x: x.get('height_m', 0), 
            reverse=True
        )
        
        # Add sorted list to result
        result[key] = sorted_attachments
    
    # Final count report
    print(f"[DEBUG] Found {len(result['measured'])} attachments in Measured Design and {len(result['recommended'])} in Recommended Design for pole {pole_label}")
    
    return result

def get_wep_info_for_wire(spida_pole_data, wire_id, design_label='Recommended Design'):
    """
    Find Wire End Points (WEPs) information for a specific wire.
    
    Args:
        spida_pole_data (dict): The pole data from SPIDAcalc for a single pole.
        wire_id (str): The ID of the wire to find WEPs for (e.g., "Wire#1")
        design_label (str): The design to look in ("Measured Design" or "Recommended Design")
        
    Returns:
        list: List of WEP objects containing ID and connection details
    """
    if not spida_pole_data or not isinstance(spida_pole_data, dict):
        return []
    
    # Find the specified design
    target_design = None
    for design in spida_pole_data.get('designs', []):
        if design.get('label') == design_label:
            target_design = design
            break
    
    if not target_design:
        print(f"[DEBUG] Design '{design_label}' not found for pole {spida_pole_data.get('label', 'Unknown')}")
        return []
    
    # Get the structure
    structure = target_design.get('structure', {})
    if not structure:
        return []
    
    wep_results = []
    
    # Find the wire in the wires array to get its connectionId
    wire_obj = None
    for wire in structure.get('wires', []):
        if wire.get('id') == wire_id:
            wire_obj = wire
            break
    
    if not wire_obj:
        print(f"[DEBUG] Wire '{wire_id}' not found in {design_label}")
        return []
    
    # Get direct connectionId if present
    connection_id = wire_obj.get('connectionId')
    if connection_id:
        # Find this WEP in wireEndPoints array
        for wep in structure.get('wireEndPoints', []):
            if wep.get('id') == connection_id:
                wep_results.append(wep)
                print(f"[DEBUG] Found direct WEP connection: {connection_id} for wire {wire_id}")
    
    # Search through all WEPs to find those referencing this wire
    for wep in structure.get('wireEndPoints', []):
        wep_wires = wep.get('wires', [])
        if wire_id in wep_wires:
            # Only add if not already in results (avoid duplicates)
            if not any(r.get('id') == wep.get('id') for r in wep_results):
                wep_results.append(wep)
                print(f"[DEBUG] Found WEP {wep.get('id')} referencing wire {wire_id}")
    
    # Enhance results with more information if available
    for wep in wep_results:
        # Add connection details if available
        connected_wire = wire_obj.get('connectedWire')
        if connected_wire:
            wep['connected_wire'] = connected_wire
            print(f"[DEBUG] Wire {wire_id} connects to {connected_wire}")
        
        # Add physical attachment point if available
        if 'wireEndPointPlacement' in wire_obj:
            vector = wire_obj.get('wireEndPointPlacement', {}).get('vector', {})
            if vector:
                wep['attachment_point'] = {
                    'x': vector.get('x'),
                    'y': vector.get('y'),
                    'z': vector.get('z')
                }
    
    return wep_results

def get_pla_percentage_spida(spida_pole_data, design_label="Recommended Design"):
    """
    Extract PLA (Percent Load Analysis) percentage from SPIDAcalc pole data.
    
    Args:
        spida_pole_data (dict): The pole data from SPIDAcalc for a single pole.
        design_label (str): The label of the design to check (e.g., "Recommended Design", "Measured Design").
        
    Returns:
        str: PLA percentage as a string (e.g., "78.70%") or "N/A".
    """
    if not spida_pole_data or not isinstance(spida_pole_data, dict):
        print(f"[DEBUG] No valid SPIDA pole data for PLA lookup")
        return "N/A"
    
    # Get pole ID for better logging
    pole_id = spida_pole_data.get('externalId', 'Unknown')
    print(f"[DEBUG] Extracting PLA percentage for pole {pole_id}")
    
    # Find the "Recommended Design" in the designs array
    recommended_design = None
    for design in spida_pole_data.get('designs', []):
        if design.get('label') == "Recommended Design":
            recommended_design = design
            print(f"[DEBUG] Found Recommended Design for pole {pole_id}")
            break
    
    if not recommended_design:
        print(f"[DEBUG] No Recommended Design found for pole {pole_id}")
        return "N/A"
    
    # Look for analysis results in the structure specified by the user
    # Path: designs["Recommended Design"].analysis[0].results[where component=="Pole" and analysisType=="STRESS"].actual
    analysis_list = recommended_design.get('analysis', [])
    if not analysis_list or len(analysis_list) == 0:
        print(f"[DEBUG] No analysis data found in Recommended Design for pole {pole_id}")
        return "N/A"
    
    # Usually the first analysis is the one we want (typically "Light - Grade C")
    analysis = analysis_list[0]
    print(f"[DEBUG] Checking analysis: {analysis.get('name', 'Unnamed')} for pole {pole_id}")
    
    # Get the results array
    results = analysis.get('results', [])
    if not results:
        print(f"[DEBUG] No results found in analysis for pole {pole_id}")
        return "N/A"
    
    # Find the result where component is "Pole" and analysisType is "STRESS"
    for result in results:
        if result.get('component') == "Pole" and result.get('analysisType') == "STRESS":
            actual_value = result.get('actual')
            print(f"[DEBUG] Found PLA value: {actual_value} with unit: {result.get('unit')}")
            
            if actual_value is not None:
                try:
                    # Convert to float for formatting
                    pla_float = float(actual_value)
                    
                    # Format the percentage with 2 decimal places
                    pla_percentage = f"{pla_float:.2f}%"
                    print(f"[DEBUG] Formatted PLA percentage for pole {pole_id}: {pla_percentage}")
                    return pla_percentage
                except (ValueError, TypeError) as e:
                    print(f"[DEBUG] Error converting PLA value to float: {str(e)}")
                    # Return as is if it's already a string
                    if isinstance(actual_value, str):
                        return actual_value
    
    print(f"[DEBUG] No matching STRESS analysis result found for pole {pole_id}")
    return "N/A"

def process_attachment_data(spida_attachment, katapult_attachment):
    """
    Process attachment data according to the updated logic for the Make-Ready report.
    
    Args:
        spida_attachment (dict): Attachment data from SPIDAcalc
        katapult_attachment (dict): Corresponding attachment data from Katapult
        
    Returns:
        dict: Processed attachment data with following keys:
            - description: Attacher description (Column L)
            - existing_height: Existing height formatted as ft-in (Column M)
            - proposed_height: Proposed height if changed, otherwise None (Column N)
            - midspan_height: Mid-span height if changed, otherwise None (Column O)
    """
    result = {}
    
    # Get attachment identifier for debugging
    att_id = None
    if spida_attachment and 'id' in spida_attachment:
        att_id = spida_attachment['id']
    elif katapult_attachment and 'id' in katapult_attachment:
        att_id = katapult_attachment['id']
    else:
        att_id = "unknown"
    
    print(f"[DEBUG] Processing attachment {att_id}")
    
    # Determine if this is a new installation
    is_new_installation = False
    if spida_attachment and spida_attachment.get('isNew', False):
        is_new_installation = True
        print(f"[DEBUG] Attachment {att_id} is new (SPIDAcalc isNew=True)")
    elif katapult_attachment and katapult_attachment.get('proposed', False):
        is_new_installation = True
        print(f"[DEBUG] Attachment {att_id} is new (Katapult proposed=True)")
    
    # Column L - Attacher Description (PRIMARY: SPIDAcalc)
    # SPIDAcalc is the ONLY source for description - never use Katapult for descriptions
    if spida_attachment:
        # First try to get owner ID as the primary identifier
        owner_id = spida_attachment.get('owner', {}).get('id')
        if owner_id:
            result['description'] = owner_id
            print(f"[DEBUG] Using SPIDAcalc owner ID for description: {owner_id}")
        # Fallback to description field if owner ID not available
        elif 'description' in spida_attachment:
            result['description'] = spida_attachment['description']
            print(f"[DEBUG] Using SPIDAcalc description: {result['description']}")
        else:
            result['description'] = "Unknown Attachment"
            print(f"[DEBUG] No SPIDAcalc description or owner ID found, using default")
    else:
        # No SPIDAcalc data - should rarely happen
        result['description'] = "Unknown Attachment"
        print(f"[DEBUG] No SPIDAcalc data available for description")
    
    # Column M - Existing Height
    # For existing attachments, get height from SPIDAcalc (primary) or Katapult (fallback)
    # For new installations, leave blank
    existing_height_in = None
    if not is_new_installation:
        if spida_attachment and 'existingHeight_in' in spida_attachment:
            existing_height_in = spida_attachment['existingHeight_in']
            print(f"[DEBUG] Using SPIDAcalc existing height: {existing_height_in}in")
        elif katapult_attachment and 'measured_height_in' in katapult_attachment:
            existing_height_in = katapult_attachment['measured_height_in']
            print(f"[DEBUG] Using Katapult measured height: {existing_height_in}in")
        
        # Format height as ft-in
        if existing_height_in is not None:
            result['existing_height'] = inches_to_ft_in(existing_height_in)
            print(f"[DEBUG] Formatted existing height: {result['existing_height']}")
        else:
            result['existing_height'] = None
            print(f"[DEBUG] No existing height found")
    else:
        result['existing_height'] = None  # New installation, no existing height
        print(f"[DEBUG] New installation - no existing height")
    
    # Column N - Proposed Height (Primary: SPIDAcalc)
    # Only show proposed height if there's a change from existing or it's a new installation
    changed = False
    proposed_height_in = None
    
    if is_new_installation:
        # For new installations - get proposed height from SPIDAcalc (primary) or Katapult (fallback)
        if spida_attachment and 'proposedHeight_in' in spida_attachment:
            proposed_height_in = spida_attachment['proposedHeight_in']
            changed = True
            print(f"[DEBUG] New installation - using SPIDAcalc proposed height: {proposed_height_in}in")
        elif katapult_attachment and 'measured_height_in' in katapult_attachment:
            proposed_height_in = katapult_attachment['measured_height_in']
            changed = True
            print(f"[DEBUG] New installation - using Katapult measured height: {proposed_height_in}in")
    else:
        # For existing attachments - only show if changed from existing
        if spida_attachment and 'proposedHeight_in' in spida_attachment:
            # If SPIDAcalc has a proposed height different from existing, use it
            if existing_height_in is not None and spida_attachment['proposedHeight_in'] != existing_height_in:
                proposed_height_in = spida_attachment['proposedHeight_in']
                changed = True
                print(f"[DEBUG] Existing attachment moved - using SPIDAcalc proposed height: {proposed_height_in}in")
        elif katapult_attachment and 'mr_move' in katapult_attachment and existing_height_in is not None:
            # Calculate new height based on mr_move
            mr_move = katapult_attachment['mr_move']
            if mr_move != 0:  # Only if there's an actual move
                proposed_height_in = existing_height_in + mr_move
                changed = True
                print(f"[DEBUG] Existing attachment moved - calculated from mr_move ({mr_move}in): {proposed_height_in}in")
    
    # Format proposed height if changed or new installation
    if changed and proposed_height_in is not None:
        result['proposed_height'] = inches_to_ft_in(proposed_height_in)
        print(f"[DEBUG] Formatted proposed height: {result['proposed_height']}")
    else:
        result['proposed_height'] = None  # No change
        print(f"[DEBUG] No proposed height (unchanged or not found)")
    
    # Column O - Mid-Span Proposed (ONLY use Katapult for this)
    # Only populate if there's a change in the attachment or it's a new installation
    if changed or is_new_installation:
        if katapult_attachment:
            # Check if attachment goes underground
            if katapult_attachment.get('goes_underground', False):
                result['midspan_height'] = "UG"
                print(f"[DEBUG] Attachment goes underground, marking as UG")
            elif 'midspanHeight_in' in katapult_attachment:
                midspan_height_in = katapult_attachment['midspanHeight_in']
                if midspan_height_in is not None:
                    result['midspan_height'] = inches_to_ft_in(midspan_height_in)
                    print(f"[DEBUG] Using midspan height from Katapult: {result['midspan_height']}")
                else:
                    result['midspan_height'] = None
                    print(f"[DEBUG] Midspan height is None in Katapult")
            else:
                # Try to get midspan from connection data if available
                wire_id = katapult_attachment.get('id')
                if wire_id and 'connection' in katapult_attachment:
                    print(f"[DEBUG] Looking for midspan height in connection sections")
                    for section in katapult_attachment['connection'].get('sections', []):
                        if section.get('wire_id') == wire_id:
                            if 'midspanHeight_in' in section:
                                result['midspan_height'] = inches_to_ft_in(section['midspanHeight_in'])
                                print(f"[DEBUG] Found midspan height in connection: {result['midspan_height']}")
                                break
                    else:
                        result['midspan_height'] = None
                        print(f"[DEBUG] No matching section found in connection")
                else:
                    result['midspan_height'] = None
                    print(f"[DEBUG] No connection data available")
        else:
            result['midspan_height'] = None
            print(f"[DEBUG] No Katapult data, cannot determine midspan height")
    else:
        result['midspan_height'] = None  # No change, no mid-span value
        print(f"[DEBUG] No change to attachment, not showing midspan height")
    
    # Summary log
    print(f"[DEBUG] Attachment {att_id} final values: desc='{result['description']}', existing={result['existing_height']}, proposed={result['proposed_height']}, midspan={result['midspan_height']}")
    
    return result

def inches_to_ft_in(height_in):
    """
    Convert height in inches to feet-inches format (e.g., 178.5 → "14'-10"").
    
    Args:
        height_in: Height in inches (float or int)
        
    Returns:
        Formatted height string
    """
    if height_in is None:
        return None
        
    # Convert to feet and inches
    feet = int(height_in) // 12
    inches = round(height_in % 12)
    
    # Handle case where inches rounds to 12
    if inches == 12:
        feet += 1
        inches = 0
        
    return f"{feet}'-{inches}\""

def generate_pole_attachment_report(spida_pole_data):
    """
    Generate a complete report of attachments on a pole from neutral downwards.
    Uses the get_attacher_list_by_neutral function for data collection.
    
    Args:
        spida_pole_data (dict): The pole data from SPIDAcalc for a single pole.
        
    Returns:
        dict: A dictionary with attacher information for measured and recommended designs.
    """
    pole_label = spida_pole_data.get('label', 'Unknown Pole')
    print(f"[DEBUG] Generating attachment report for pole: {pole_label}")
    
    # Get the attacher list from neutral downwards
    attachers = get_attacher_list_by_neutral(spida_pole_data)
    
    # Convert to a simpler format for report generation
    report = {
        'pole_id': pole_label,
        'measured': [],
        'recommended': []
    }
    
    # Process measured design attachments
    for attachment in attachers.get('measured', []):
        # Get owner and additional info
        owner = attachment.get('owner', 'Unknown')
        attachment_type = attachment.get('type', 'Unknown')
        subtype = attachment.get('subtype', '')
        
        # Format height as ft-in (convert from meters)
        height_m = attachment.get('height_m')
        if height_m is not None:
            # Convert meters to inches (1m = 39.3701in)
            height_in = height_m * 39.3701
            height_formatted = inches_to_ft_in(height_in)
        else:
            height_formatted = None
            
        # Add to report - use owner as primary identifier
        report['measured'].append({
            'description': owner,
            'type': f"{attachment_type} - {subtype}" if subtype else attachment_type,
            'existing_height': height_formatted,
            'id': attachment.get('id')
        })
    
    # Process recommended design attachments
    for attachment in attachers.get('recommended', []):
        # Get owner and additional info
        owner = attachment.get('owner', 'Unknown')
        attachment_type = attachment.get('type', 'Unknown')
        subtype = attachment.get('subtype', '')
        
        # Format height as ft-in (convert from meters)
        height_m = attachment.get('height_m')
        if height_m is not None:
            # Convert meters to inches (1m = 39.3701in)
            height_in = height_m * 39.3701
            height_formatted = inches_to_ft_in(height_in)
        else:
            height_formatted = None
            
        # In recommended design, we need to determine if this is a new/moved attachment
        # by comparing with the measured design
        
        # First, try to find matching attachment in measured design
        matching_measured = None
        for measured_attachment in attachers.get('measured', []):
            if (measured_attachment.get('owner') == owner and 
                measured_attachment.get('type') == attachment_type and
                measured_attachment.get('subtype') == subtype):
                matching_measured = measured_attachment
                break
        
        # Determine proposed height - only if different from measured or new installation
        proposed_height = None
        if matching_measured is None:  # New installation
            proposed_height = height_formatted
            print(f"[DEBUG] New {owner} {attachment_type} in recommended design: {proposed_height}")
        elif matching_measured.get('height_m') != height_m:  # Moved attachment
            proposed_height = height_formatted
            print(f"[DEBUG] Moved {owner} {attachment_type} in recommended design: {proposed_height}")
        
        # Add to report - use owner as primary identifier
        report['recommended'].append({
            'description': owner,
            'type': f"{attachment_type} - {subtype}" if subtype else attachment_type,
            'existing_height': None if matching_measured is None else matching_measured.get('height_formatted'),
            'proposed_height': proposed_height,
            'id': attachment.get('id')
        })
    
    print(f"[DEBUG] Generated report with {len(report['measured'])} measured and {len(report['recommended'])} recommended attachments")
    return report

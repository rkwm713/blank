# data_loader.py
import json
import logging
from utils import normalize_pole_id

logger = logging.getLogger(__name__)

def load_katapult_data(katapult_path):
    """
    Load and perform initial validation of Katapult JSON data.
    
    Args:
        katapult_path (str): Path to Katapult JSON file
        
    Returns:
        dict: Loaded Katapult data
    """
    logger.info(f"Loading Katapult data from {katapult_path}")
    with open(katapult_path, 'r', encoding='utf-8') as f:
        katapult = json.load(f)
    
    # Log some basic stats
    node_count = len(katapult.get('nodes', {}))
    connection_count = len(katapult.get('connections', {}))
    logger.info(f"Loaded Katapult data with {node_count} nodes and {connection_count} connections")
    
    return katapult

def load_spidacalc_data(spidacalc_path):
    """
    Load and perform initial validation of SPIDAcalc JSON data.
    
    Args:
        spidacalc_path (str): Path to SPIDAcalc JSON file
        
    Returns:
        dict: Loaded SPIDAcalc data
    """
    if not spidacalc_path:
        return None
        
    logger.info(f"Loading SPIDAcalc data from {spidacalc_path}")
    with open(spidacalc_path, 'r', encoding='utf-8') as f:
        spida = json.load(f)
    
    # Log some basic stats
    lead_count = len(spida.get('leads', []))
    location_count = sum(len(lead.get('locations', [])) for lead in spida.get('leads', []))
    logger.info(f"Loaded SPIDAcalc data with {lead_count} leads and {location_count} locations")
    
    return spida

def build_spida_lookups(spida):
    """
    Build lookup dictionaries for SPIDAcalc data.
    
    Args:
        spida (dict): SPIDAcalc data
        
    Returns:
        tuple: (spida_lookup, spida_wire_lookup, spida_pole_order)
    """
    if not spida:
        return {}, {}, {}
    
    # Dictionary to track the order of poles in the SPIDAcalc file
    spida_pole_order = {}
    pole_order_index = 0
    
    # Build wire lookup
    spida_wire_lookup = {}
    
    # Build location lookup
    spida_lookup = {}
    
    for lead in spida.get('leads', []):
        for loc in lead.get('locations', []):
            loc_pole = normalize_pole_id(loc.get('label'))
            
            # Track the order of poles in the SPIDAcalc file
            if loc_pole and loc_pole not in spida_pole_order:
                spida_pole_order[loc_pole] = pole_order_index
                pole_order_index += 1
            
            # Build wire lookup
            for design in loc.get('designs', []):
                for wire in design.get('structure', {}).get('wires', []):
                    from utils import normalize_owner
                    owner = normalize_owner(wire.get('owner', {}).get('id', ''))
                    endpoints = [loc_pole]
                    # Try to get other endpoint from wireEndPoints if available
                    if 'wireEndPoints' in wire:
                        endpoints += [normalize_pole_id(e.get('label')) for e in wire['wireEndPoints'] if e.get('label')]
                    endpoints = sorted(set([e for e in endpoints if e]))
                    key = (owner, tuple(endpoints))
                    spida_wire_lookup[key] = wire
            
            # Add to location lookup
            norm = normalize_pole_id(loc.get('label'))
            spida_lookup[norm] = loc
    
    return spida_lookup, spida_wire_lookup, spida_pole_order

def filter_target_poles(target_poles):
    """
    Process and normalize target pole list.
    
    Args:
        target_poles (list): List of pole IDs to process
        
    Returns:
        list: Normalized target pole IDs
    """
    if not target_poles:
        return None
    
    # Normalize all target pole IDs for consistent matching
    normalized_target_poles = [normalize_pole_id(pole) for pole in target_poles if pole]
    logger.info(f"Filtering to {len(normalized_target_poles)} target poles: {normalized_target_poles}")
    
    return normalized_target_poles
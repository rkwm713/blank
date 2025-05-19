# pole_attribute_processor.py
import logging
from utils import normalize_pole_id, extract_string_value
from spida_utils import get_construction_grade_spida, get_pole_structure_spida, get_pla_percentage_spida

logger = logging.getLogger(__name__)

def extract_pole_attributes_katapult(node, attributes):
    """
    Extract pole attributes primarily from Katapult node data.
    This function focuses on what Katapult provides directly.
    
    Args:
        node (dict): Node data from Katapult
        attributes (dict): Attributes dictionary from node
        
    Returns:
        dict: Dictionary of extracted Katapult pole attributes
    """
    pole_number = extract_pole_number(attributes) # Uses extract_string_value internally now
    pole_owner = extract_string_value(attributes.get('pole_owner') or attributes.get('PoleOwner'), 'N/A')
    
    # Katapult might have height, class, species but often less reliable than SPIDA for these
    kat_pole_height = extract_string_value(attributes.get('pole_height') or attributes.get('PoleHeight'), None)
    kat_pole_class = extract_string_value(attributes.get('pole_class') or attributes.get('PoleClass'), None)
    kat_pole_species = extract_string_value(attributes.get('pole_species') or attributes.get('PoleSpecies'), 'Southern Pine') # Default

    kat_pole_structure = None
    if kat_pole_height and kat_pole_class:
        kat_pole_structure = f"{kat_pole_height}-{kat_pole_class} {kat_pole_species}"
    elif attributes.get('pole_structure'): # Direct attribute
        kat_pole_structure = extract_string_value(attributes.get('pole_structure'))
    
    # Katapult doesn't typically provide construction_grade or PLA directly in a standard way for poles
    # These are usually derived from SPIDAcalc.

    return {
        'pole_number': pole_number,
        'norm_pole_number': normalize_pole_id(pole_number),
        'pole_owner': pole_owner,
        'pole_height_kat': kat_pole_height, # Store Katapult specific for potential comparison
        'pole_class_kat': kat_pole_class,
        'pole_species_kat': kat_pole_species,
        'pole_structure_kat': kat_pole_structure,
        # These will be filled/overridden by SPIDA data later
        'pole_structure': kat_pole_structure or "N/A", 
        'construction_grade': 'N/A',
        'pla_percentage': 'N/A',
        'latitude': node.get('latitude'),
        'longitude': node.get('longitude')
    }

def extract_pole_number(attributes):
    """Extract pole number from attributes with multiple fallbacks."""
    # Check capitalized "PoleNumber" first
    pole_number_attr = attributes.get('PoleNumber')
    if isinstance(pole_number_attr, dict):
        pole_number = pole_number_attr.get('-Imported') or pole_number_attr.get('assessment')
        if pole_number:
            return pole_number
    elif isinstance(pole_number_attr, str):
        return pole_number_attr

    # If not found, try lowercase "pl_number"
    pl_number_attr = attributes.get('pl_number')
    if isinstance(pl_number_attr, dict):
        pole_number = pl_number_attr.get('-Imported') or pl_number_attr.get('assessment')
        if pole_number:
            return pole_number
    elif isinstance(pl_number_attr, str):
        return pl_number_attr

    # If still not found, try lowercase "dloc_number"
    dloc_number_attr = attributes.get('dloc_number')
    if isinstance(dloc_number_attr, dict):
        pole_number = dloc_number_attr.get('-Imported') or dloc_number_attr.get('assessment')
        if pole_number:
            return pole_number
    elif isinstance(dloc_number_attr, str):
        return dloc_number_attr
        
    # For backward compatibility, check capitalized versions as well
    return attributes.get('PL_number') or attributes.get('DLOC_number')

# Similar extraction functions for other attributes
def extract_pole_owner(attributes):
    """Extract pole owner from attributes with multiple fallbacks."""
    pole_owner_data = attributes.get('pole_owner')
    if isinstance(pole_owner_data, dict):
        pole_owner = pole_owner_data.get('multi_added') or pole_owner_data.get('assessment') or pole_owner_data.get('-Imported')
        if pole_owner:
            return pole_owner
    elif isinstance(pole_owner_data, str):
        return pole_owner_data
    
    # Fallback to capitalized version
    pole_owner_cap = attributes.get('PoleOwner')
    if isinstance(pole_owner_cap, dict):
        return pole_owner_cap.get('assessment') or pole_owner_cap.get('-Imported')
    elif isinstance(pole_owner_cap, str):
        return pole_owner_cap
    
    return None

def extract_pole_height(attributes):
    """Extract pole height from attributes."""
    # Using extract_string_value for robustness
    pole_number = extract_string_value(attributes.get('PoleNumber'), None)
    if not pole_number:
        pole_number = extract_string_value(attributes.get('pl_number'), None)
    if not pole_number:
        pole_number = extract_string_value(attributes.get('dloc_number'), None)
    if not pole_number: # Check legacy capitalized versions
        pole_number = extract_string_value(attributes.get('PL_number'), None)
    if not pole_number:
        pole_number = extract_string_value(attributes.get('DLOC_number'), None)
    if not pole_number: # Check pole_tag as a common fallback
        pole_number = extract_string_value(attributes.get('pole_tag'), None)
    return pole_number if pole_number else "Unknown"


# Katapult specific extractors are simplified as SPIDA is preferred for these
def extract_pole_height_katapult(attributes):
    return extract_string_value(attributes.get('pole_height') or attributes.get('PoleHeight'), None)

def extract_pole_class_katapult(attributes):
    return extract_string_value(attributes.get('pole_class') or attributes.get('PoleClass'), None)

def extract_pole_species_katapult(attributes):
    # Default to Southern Pine if not specified, as per original logic
    return extract_string_value(attributes.get('pole_species') or attributes.get('PoleSpecies'), 'Southern Pine')

# Construction grade and PLA are primarily SPIDA concerns.
# Katapult attributes for these are not standard.

def extract_notes(attributes):
    """Extract make-ready notes from attributes."""
    # Extract various note fields
    kat_mr_notes = None
    stress_mr_notes = None
    
    # Check lowercase version first for kat_mr_notes
    kat_mr_notes_data = attributes.get('kat_mr_notes')
    if isinstance(kat_mr_notes_data, dict):
        kat_mr_notes = kat_mr_notes_data.get('assessment') or kat_mr_notes_data.get('-Imported') or next(iter(kat_mr_notes_data.values()), None)
    elif isinstance(kat_mr_notes_data, str):
        kat_mr_notes = kat_mr_notes_data
    
    # Check capitalized version as well
    if not kat_mr_notes:
        kat_mr_notes_cap = attributes.get('kat_MR_notes')
        if isinstance(kat_mr_notes_cap, dict):
            kat_mr_notes = kat_mr_notes_cap.get('assessment') or kat_mr_notes_cap.get('-Imported')
        elif isinstance(kat_mr_notes_cap, str):
            kat_mr_notes = kat_mr_notes_cap
    
    # Check stress_MR_notes as well
    stress_mr_notes_data = attributes.get('stress_MR_notes')
    # ...similar extraction logic...
    
    # Return all extracted notes
    return {
        'kat_mr_notes': kat_mr_notes,
        'stress_mr_notes': stress_mr_notes
    }

def resolve_pole_attribute_conflicts(katapult_attrs, spida_pole_data, full_spida_data, strategy='PREFER_KATAPULT'):
    """
    Resolve conflicts between Katapult and SPIDAcalc pole attributes.
    
    Args:
        katapult_attrs (dict): Pole attributes from Katapult (result of extract_pole_attributes_katapult)
        spida_pole_data (dict): SPIDAcalc data for the specific pole.
        full_spida_data (dict): The full SPIDAcalc JSON (needed for some global lookups like construction grade).
        strategy (str): Conflict resolution strategy ('PREFER_SPIDA', 'PREFER_KATAPULT', 'HIGHLIGHT_DIFFERENCES').
        
    Returns:
        dict: Resolved and augmented pole attributes.
    """
    resolved_attrs = dict(katapult_attrs) # Start with Katapult attributes

    # Extract SPIDA attributes
    # Ensure spida_pole_data and full_spida_data are not None before using them
    spida_pole_structure = None
    spida_construction_grade = None
    spida_pla_percentage = "N/A"

    if spida_pole_data:
        spida_pole_structure = get_pole_structure_spida(spida_pole_data)
        spida_pla_percentage = get_pla_percentage_spida(spida_pole_data) # Defaults to "Recommended Design"
    
    if full_spida_data:
        # For construction grade, pass the full SPIDA data, not just per-pole data
        spida_construction_grade = get_construction_grade_spida(full_spida_data)

    # --- Conflict Resolution & Merging ---
    # Pole Structure: SPIDA is generally preferred for accuracy.
    if spida_pole_structure:
        if strategy == 'HIGHLIGHT_DIFFERENCES' and resolved_attrs.get('pole_structure_kat') and resolved_attrs['pole_structure_kat'] != spida_pole_structure:
            resolved_attrs['pole_structure'] = f"{resolved_attrs['pole_structure_kat']} (SPIDA: {spida_pole_structure})"
        else: # PREFER_SPIDA or if Katapult is None
            resolved_attrs['pole_structure'] = spida_pole_structure
    elif not resolved_attrs.get('pole_structure'): # If SPIDA is None and Katapult was also None
        resolved_attrs['pole_structure'] = "N/A"


    # Construction Grade: Primarily from SPIDA. Katapult usually doesn't have this.
    if spida_construction_grade:
        resolved_attrs['construction_grade'] = spida_construction_grade
    elif not resolved_attrs.get('construction_grade'): # If SPIDA is None and Katapult was also None
        resolved_attrs['construction_grade'] = "N/A"

    # PLA Percentage: Primarily from SPIDA.
    if spida_pla_percentage and spida_pla_percentage != "N/A":
        resolved_attrs['pla_percentage'] = spida_pla_percentage
    elif not resolved_attrs.get('pla_percentage') or resolved_attrs.get('pla_percentage') == "N/A":
        resolved_attrs['pla_percentage'] = "N/A"

    # Log if SPIDA data was used for key fields
    if spida_pole_structure and resolved_attrs['pole_structure'] == spida_pole_structure:
        logger.debug(f"Pole {resolved_attrs.get('pole_number')}: Used SPIDA pole_structure ('{spida_pole_structure}')")
    if spida_construction_grade and resolved_attrs['construction_grade'] == spida_construction_grade:
        logger.debug(f"Pole {resolved_attrs.get('pole_number')}: Used SPIDA construction_grade ('{spida_construction_grade}')")
    if spida_pla_percentage != "N/A" and resolved_attrs['pla_percentage'] == spida_pla_percentage:
        logger.debug(f"Pole {resolved_attrs.get('pole_number')}: Used SPIDA pla_percentage ('{spida_pla_percentage}')")

    # Clean up temporary Katapult-specific fields if not highlighting
    if strategy != 'HIGHLIGHT_DIFFERENCES':
        resolved_attrs.pop('pole_height_kat', None)
        resolved_attrs.pop('pole_class_kat', None)
        resolved_attrs.pop('pole_species_kat', None)
        resolved_attrs.pop('pole_structure_kat', None)
        
    return resolved_attrs

# This function is now more of a wrapper or might be deprecated if SPIDA is always the source for these.
# For now, it's kept to show the original structure but SPIDA functions are preferred.
def extract_spida_pole_attributes(spida_pole_data):
    """
    Extracts basic pole attributes (height, class, species) from SPIDAcalc pole data.
    Prefer using get_pole_structure_spida for the combined string.
    
    Args:
        spida_pole_data (dict): SPIDAcalc pole data for a single pole.
        
    Returns:
        dict: Extracted SPIDAcalc pole attributes (height, class, species).
    """
    if not spida_pole_data or not isinstance(spida_pole_data, dict):
        return {}
    
    height = None
    pole_class_val = None # Renamed to avoid keyword clash
    species = None

    pole_tags = spida_pole_data.get('poleTags', {})
    if isinstance(pole_tags, dict):
        height = pole_tags.get('height')
        pole_class_val = pole_tags.get('class')
        species = pole_tags.get('species')

    # Fallback to direct attributes
    if height is None: height = spida_pole_data.get('height')
    if pole_class_val is None: pole_class_val = spida_pole_data.get('class')
    if species is None: species = spida_pole_data.get('species')
            
    return {
        'pole_height_spida': height,
        'pole_class_spida': pole_class_val,
        'pole_species_spida': species
    }

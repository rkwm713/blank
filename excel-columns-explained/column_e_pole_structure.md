# Column E – Pole Structure

> **Purpose** Define how the generator identifies and formats the **Pole Structure** field in Column E, which describes the physical characteristics of each utility pole. This specification details the extraction of height, class, and species information from both SPIDAcalc and Katapult, as well as handling edge cases where information is incomplete.

---

## 1 Definition

*Pole Structure* combines three key pole attributes in the format `<Height>-<Class> <Species>`, where:

- **Height** = Nominal pole length in feet (e.g., 40, 45, 50)
- **Class** = ANSI strength class (1-10 scale, where 1 is strongest, 10 is weakest)
- **Species** = Wood type or material (e.g., "Southern Pine", "Douglas Fir", "Steel")

The value is written once in Column E of the blue operation-header row and merged vertically across all attachment rows for that pole.

---

## 2 Data Sources

| Attribute | Primary Source | JSON Path                          | Fallback Source | Fallback Path                      |
|-----------|----------------|------------------------------------|-----------------|------------------------------------|
| Height-Class | SPIDAcalc   | `clientData.poles[*].aliases[0].id` | Katapult        | `attributes.pole_height.*` + `attributes.pole_class.*` |
| Species      | SPIDAcalc   | `clientData.poles[*].species`       | Hardcoded       | Default `"Southern Pine"` per CPS standard |

---

## 3 Extraction and Validation Algorithm

```python
def extract_pole_structure(pole_id, pole_map, spida_data, katapult_data):
    """
    Extract pole structure (height-class and species) for a given pole.
    
    Args:
        pole_id: Normalized pole ID (e.g., "PL398491")
        pole_map: The reconciliation map between SPIDAcalc and Katapult
        spida_data: Full SPIDAcalc JSON
        katapult_data: Full Katapult JSON
        
    Returns:
        Formatted pole structure string (e.g., "45-2 Southern Pine")
    """
    pole_info = pole_map.get(pole_id)
    if not pole_info:
        raise ValueError(f"Pole ID {pole_id} not found in pole map")
    
    # Try SPIDAcalc first (primary source)
    height_class = None
    species = None
    
    if pole_info["spida_obj"]:
        spida_pole = pole_info["spida_obj"]
        
        # Get height-class from aliases
        if "aliases" in spida_pole and spida_pole["aliases"]:
            height_class = spida_pole["aliases"][0]["id"]
        
        # Get species
        if "species" in spida_pole:
            species = spida_pole["species"]
    
    # If needed, fall back to Katapult
    if (not height_class or not species) and pole_info["katapult_obj"]:
        katapult_node = pole_info["katapult_obj"]
        attributes = katapult_node.get("attributes", {})
        
        # Get height and class separately if not found in SPIDAcalc
        if not height_class:
            height = first_value(attributes.get("pole_height", {}))
            pole_class = first_value(attributes.get("pole_class", {}))
            
            if height and pole_class:
                height_class = f"{height}-{pole_class}"
            else:
                log.warning(f"Incomplete pole structure data for {pole_id}")
                if height:
                    height_class = f"{height}-?"
                elif pole_class:
                    height_class = f"?-{pole_class}"
                else:
                    height_class = "Unknown"
    
    # Default species if not found
    if not species:
        species = "Southern Pine"  # CPS standard default
        log.info(f"Using default species 'Southern Pine' for pole {pole_id}")
    
    # Validate and format
    return format_pole_structure(height_class, species)
```

### 3.1 Helper Functions

```python
def first_value(attribute_dict):
    """
    Extract the first available value from a Katapult attribute dictionary.
    Katapult may store values in different formats based on the attribute type.
    
    Args:
        attribute_dict: Katapult attribute dictionary
        
    Returns:
        First value found or None if empty
    """
    if not attribute_dict:
        return None
    
    # Try common patterns in Katapult attributes
    if "-Imported" in attribute_dict and "value" in attribute_dict["-Imported"]:
        return attribute_dict["-Imported"]["value"]
    
    if "-Imported" in attribute_dict and "tagtext" in attribute_dict["-Imported"]:
        return attribute_dict["-Imported"]["tagtext"]
    
    # Check for direct value
    if "value" in attribute_dict:
        return attribute_dict["value"]
    
    # Last resort - try to get first value from any key
    for key, value in attribute_dict.items():
        if isinstance(value, dict) and "value" in value:
            return value["value"]
    
    return None

def format_pole_structure(height_class, species):
    """
    Format the pole structure string, ensuring consistent spacing and validation.
    
    Args:
        height_class: Height-class string (e.g., "45-2")
        species: Species string (e.g., "Southern Pine")
        
    Returns:
        Formatted pole structure string
    """
    # Validate height-class format if not "Unknown"
    if height_class != "Unknown":
        # Remove any whitespace
        height_class = height_class.strip()
        
        # Check for expected format (e.g., "45-2")
        if not re.match(r'^\d+\-\d+$|^\d+\-\?$|^\?\-\d+$', height_class):
            log.warning(f"Unusual height-class format: {height_class}")
    
    # Ensure species has proper capitalization (e.g., "Southern Pine")
    if species:
        species = ' '.join(word.capitalize() for word in species.split())
    
    return f"{height_class} {species}"
```

---

## 4 Integration with Report Generation

```python
# During primary pole processing
for pole_id in primary_poles:
    # Get pole info
    pole_info = pole_map[pole_id]
    
    # Write operation header
    current_row = get_next_row()
    write_cell(row=current_row, col="A", value=sequence_map[pole_id])
    write_cell(row=current_row, col="B", value=determine_action_code(pole_info))
    write_cell(row=current_row, col="C", value=POLE_OWNER_CONSTANT)
    write_cell(row=current_row, col="D", value=pole_id)  # Normalized pole ID
    
    # Get and write pole structure
    structure = extract_pole_structure(pole_id, pole_map, spida_data, katapult_data)
    write_cell(row=current_row, col="E", value=structure)
    
    # Merge cells for the header sections
    merge_range(f"A{current_row}:I{current_row + attachment_count}")
    
    # ... process attachments ...
```

---

## 5 Project CPS 6457E 03 – Sample Mapping

| Pole #       | Raw Height-Class | Raw Species     | Final Column E Value    |
|--------------|------------------|-----------------|-------------------------|
| **PL410620** | "40-4"           | "Southern Pine" | **40-4 Southern Pine**  |
| **PL398491** | "45-2"           | "Southern Pine" | **45-2 Southern Pine**  |
| **PL389359** | "45-4"           | "Southern Pine" | **45-4 Southern Pine**  |
| **PL404474** | "40-3"           | "Southern Pine" | **40-3 Southern Pine**  |
| **PL900997** | "45-2"           | "Southern Pine" | **45-2 Southern Pine**  |
| **PL370858** | "45-2"           | "Southern Pine" | **45-2 Southern Pine**  |

---

## 6 Relationship with Other Columns

| Column           | Relationship to Column E (Pole Structure)                                         |
|------------------|----------------------------------------------------------------------------------|
| **Column D**     | Pole ID is used to look up the corresponding structure data in both files         |
| **Columns L-O**  | Pole height may influence attachment height positions (validation relationship)   |
| **Columns J-K**  | No direct relationship, but both relate to physical characteristics               |
| **QC Sheet**     | Pole structure can be used for material quantity estimation and validation        |

---

## 7 Edge-case Handling

| Case                                  | Handling                                                  | Log Key                |
|--------------------------------------|-----------------------------------------------------------|------------------------|
| Missing aliases array in SPIDAcalc    | Safely handle empty array, fall back to Katapult          | `EMPTY_ALIASES_ARRAY`  |
| Missing height or class in Katapult   | Use partial data with "?" placeholder or mark as "Unknown"| `INCOMPLETE_STRUCTURE` |
| Non-standard height-class format      | Accept but log warning for QC review                      | `NON_STANDARD_FORMAT`  |
| Non-wood material (e.g., Steel)       | Handle as normal species variant (e.g., "45-3 Steel")     | `NON_WOOD_MATERIAL`    |
| Conflicting data between sources      | Prioritize SPIDAcalc, log conflicts                       | `SOURCE_CONFLICT`      |
| Missing data in both sources          | Use "Unknown Southern Pine" as last resort                | `STRUCTURE_MISSING`    |

---

## 8 Validation Rules

```python
def validate_pole_structure(pole_id, structure):
    """
    Validate pole structure data for completeness and reasonableness.
    
    Args:
        pole_id: Normalized pole ID 
        structure: Formatted pole structure string
        
    Returns:
        List of validation issues or empty list if valid
    """
    issues = []
    
    # Parse the structure
    parts = structure.split()
    height_class = parts[0] if parts else "Unknown"
    species = " ".join(parts[1:]) if len(parts) > 1 else "Unknown"
    
    # Check height-class format
    if height_class == "Unknown":
        issues.append(("WARNING", f"Unknown height-class for pole {pole_id}"))
    else:
        # Check for valid height-class format (e.g., "45-2")
        if not re.match(r'^\d+\-\d+$|^\d+\-\?$|^\?\-\d+$', height_class):
            issues.append(("WARNING", f"Non-standard height-class format: {height_class}"))
        else:
            # If format is standard, check for reasonable values
            try:
                height, class_val = height_class.replace("?", "0").split("-")
                height, class_val = int(height), int(class_val)
                
                # Typical height range for distribution poles
                if height > 0 and (height < 25 or height > 100):
                    issues.append(("WARNING", f"Unusual pole height: {height} feet"))
                
                # Valid class range is 1-10 (1 = strongest)
                if class_val > 0 and (class_val < 1 or class_val > 10):
                    issues.append(("WARNING", f"Unusual pole class: {class_val}"))
            except:
                # If we can't parse as numbers, it's already logged as non-standard
                pass
    
    # Check species
    if species == "Unknown":
        issues.append(("INFO", f"Default species used for pole {pole_id}"))
    elif species != "Southern Pine" and "Steel" not in species and "Concrete" not in species:
        issues.append(("INFO", f"Non-standard species: {species}"))
    
    return issues
```

---

## 9 Unit-test Checklist

```python
@pytest.mark.parametrize("height_class,species,expected", [
    ("45-2", "Southern Pine", "45-2 Southern Pine"),
    ("40-4", "Southern Pine", "40-4 Southern Pine"),
    ("45-2", "Douglas Fir", "45-2 Douglas Fir"),
    ("45-2", "steel", "45-2 Steel"),  # Test capitalization
    ("40-3", "southern pine", "40-3 Southern Pine"),  # Test capitalization
    ("  45-2  ", "Southern Pine", "45-2 Southern Pine"),  # Test whitespace trimming
    (None, "Southern Pine", "Unknown Southern Pine"),  # Test missing height-class
    ("45-2", None, "45-2 Southern Pine"),  # Test missing species
])
def test_format_pole_structure(height_class, species, expected):
    assert format_pole_structure(height_class, species) == expected

def test_spida_extraction():
    # Mock SPIDAcalc data with valid structure
    mock_spida = {
        "clientData": {
            "poles": [
                {
                    "aliases": [{"id": "45-2"}],
                    "species": "Southern Pine"
                }
            ]
        }
    }
    
    # Test successful extraction
    pole_map = {"PL398491": {"spida_obj": mock_spida["clientData"]["poles"][0]}}
    structure = extract_pole_structure("PL398491", pole_map, mock_spida, {})
    assert structure == "45-2 Southern Pine"
    
    # Test missing aliases
    mock_spida["clientData"]["poles"][0]["aliases"] = []
    structure = extract_pole_structure("PL398491", pole_map, mock_spida, {})
    assert "Unknown Southern Pine" in structure

def test_katapult_fallback():
    # Mock data with only Katapult info
    mock_katapult = {"nodes": {"node1": {"attributes": {
        "pole_height": {"-Imported": {"value": "45"}},
        "pole_class": {"-Imported": {"value": "2"}}
    }}}}
    
    # Test fallback to Katapult
    pole_map = {"PL398491": {
        "spida_obj": None,
        "katapult_obj": mock_katapult["nodes"]["node1"]
    }}
    structure = extract_pole_structure("PL398491", pole_map, {}, mock_katapult)
    assert structure == "45-2 Southern Pine"
```

---

## 10 Revision History

| Date       | Version | Notes                                                           |
|------------|---------|----------------------------------------------------------------|
| 2025-05-19 | v1.0    | Initial doc, includes mapping for six operation poles.          |
| 2025-05-20 | v2.0    | Enhanced with proper validation, helper functions, and edge cases |
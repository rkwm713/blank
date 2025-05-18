# Column D – Pole #

> **Purpose** Define how the generator identifies and formats the **Pole #** field (Column D), which serves as the primary identifier for electric pole structures throughout the Make-Ready report. This specification details the extraction, normalization, and validation of pole IDs from both SPIDAcalc and Katapult JSON files.

---

## 1 Definition

*Pole #* is the field-tag identifier stencilled on the physical pole structure (e.g., **PL398491**). It appears in three contexts in the report:

1. **Operation Header** – Blue row merged A-I (one per SPIDA pole)
2. **From/To Rows** – Light-blue rows at the end of each pole's operations section
3. **Reference Headers** – Orange/purple rows for reference spans (e.g., "Ref (North East) to PL401451")

Correctly identifying and reconciling pole numbers between SPIDAcalc and Katapult is critical as this field serves as the primary key for joining data between files and for field identification.

---

## 2 Data Sources

| Use Case                              | Primary Source | JSON Path                                           | Fallback Source | Fallback Path                                       |
|---------------------------------------|----------------|-----------------------------------------------------|-----------------|-----------------------------------------------------|
| **Primary Operation Poles**           | SPIDAcalc      | `design.structure.poles[i].externalId`              | Katapult        | `nodes[*].attributes.pole_tag["-Imported"].tagtext` |
| **Context Poles** (From/To, reference)| Katapult       | `nodes[*].attributes.pole_tag["-Imported"].tagtext` | None            | (Must exist in Katapult)                            |

---

## 3 Normalization Rules

All pole IDs must be normalized to ensure consistency:

```python
def normalize_pole_id(raw_id):
    """
    Normalize pole ID to standard format.
    
    Args:
        raw_id: Raw pole ID string from SPIDAcalc or Katapult
        
    Returns:
        Normalized pole ID string (e.g., "PL398491")
    """
    if not raw_id:
        raise ValueError("Pole ID cannot be empty or None")
        
    # Remove all whitespace and convert to uppercase
    clean_id = raw_id.strip().upper()
    
    # Add "PL" prefix if missing
    if not clean_id.startswith("PL"):
        clean_id = f"PL{clean_id}"
        
    # Validate the normalized ID
    if not re.match(r'^PL\d+$', clean_id):
        log.warning(f"Unusual pole ID format after normalization: {clean_id}")
        
    return clean_id
```

---

## 4 ID Reconciliation Between Files

A critical enhancement is ensuring pole IDs match correctly between SPIDAcalc and Katapult:

```python
def reconcile_pole_ids(spida_data, katapult_data):
    """
    Build a mapping between SPIDAcalc and Katapult pole IDs.
    
    Returns:
        Dictionary mapping normalized pole IDs to original IDs in each source
    """
    # Build lookup dictionaries
    spida_poles = {}
    for pole in spida_data["design"]["structure"]["poles"]:
        ext_id = pole.get("externalId")
        if ext_id:
            norm_id = normalize_pole_id(ext_id)
            spida_poles[norm_id] = {
                "original_id": ext_id,
                "spida_obj": pole
            }
    
    katapult_poles = {}
    for node_id, node in katapult_data["nodes"].items():
        if "pole_tag" in node["attributes"] and "-Imported" in node["attributes"]["pole_tag"]:
            tag_text = node["attributes"]["pole_tag"]["-Imported"].get("tagtext")
            if tag_text:
                norm_id = normalize_pole_id(tag_text)
                katapult_poles[norm_id] = {
                    "original_id": tag_text,
                    "node_id": node_id,
                    "katapult_obj": node
                }
    
    # Create reconciliation map
    pole_map = {}
    
    # First add all SPIDAcalc poles (primary operations)
    for norm_id, info in spida_poles.items():
        pole_map[norm_id] = {
            "spida_id": info["original_id"],
            "spida_obj": info["spida_obj"],
            "katapult_id": None,
            "katapult_obj": None,
            "katapult_node_id": None,
            "is_primary": True  # All SPIDAcalc poles are primary
        }
    
    # Then match or add Katapult poles
    for norm_id, info in katapult_poles.items():
        if norm_id in pole_map:
            # Match found - update with Katapult info
            pole_map[norm_id].update({
                "katapult_id": info["original_id"],
                "katapult_obj": info["katapult_obj"],
                "katapult_node_id": info["node_id"]
            })
        else:
            # Katapult-only pole (context pole)
            pole_map[norm_id] = {
                "spida_id": None,
                "spida_obj": None,
                "katapult_id": info["original_id"],
                "katapult_obj": info["katapult_obj"],
                "katapult_node_id": info["node_id"],
                "is_primary": False  # Not in SPIDAcalc, so context only
            }
    
    # Log reconciliation warnings
    primary_poles = [id for id, info in pole_map.items() if info["is_primary"]]
    log.info(f"Found {len(primary_poles)} primary operation poles")
    
    unmatched_spida = [id for id, info in pole_map.items() 
                      if info["is_primary"] and not info["katapult_id"]]
    if unmatched_spida:
        log.warning(f"Found {len(unmatched_spida)} SPIDAcalc poles not in Katapult: {unmatched_spida}")
    
    return pole_map
```

---

## 5 Integration with Report Generation

```python
# During initialization
pole_map = reconcile_pole_ids(spida_data, katapult_data)
primary_poles = [id for id, info in pole_map.items() if info["is_primary"]]

# Get sequence numbers for primary poles
sequence_map = generate_sequence_numbers(primary_poles)

# For each primary pole
for pole_id in primary_poles:
    # Get pole info
    pole_info = pole_map[pole_id]
    
    # Write operation header
    current_row = get_next_row()
    write_cell(row=current_row, col="A", value=sequence_map[pole_id])
    write_cell(row=current_row, col="B", value=determine_action_code(pole_info))
    write_cell(row=current_row, col="C", value=POLE_OWNER_CONSTANT)
    write_cell(row=current_row, col="D", value=pole_id)  # Use normalized ID
    
    # ... process attachments ...
    
    # Get connections for From/To rows
    connections = get_pole_connections(pole_id, katapult_data)
    for conn in connections:
        from_id = normalize_pole_id(conn["from_tag"])
        to_id = normalize_pole_id(conn["to_tag"])
        # ... write From/To rows ...
```

---

## 6 Example Transformations

| Input Source | Raw ID Value   | Normalized Result | Notes                       |
|--------------|----------------|-------------------|---------------------------- |
| SPIDAcalc    | `"PL398491"`   | `"PL398491"`      | Already in correct format   |
| Katapult     | `"370858"`     | `"PL370858"`      | Added PL prefix             |
| SPIDAcalc    | `"pl389359 "`  | `"PL389359"`      | Trimmed space, uppercased   |
| Katapult     | `"  PL404474"` | `"PL404474"`      | Trimmed leading space       |

---

## 7 Relationship with Other Columns

| Column               | Relationship to Column D (Pole #)                                                   |
|----------------------|------------------------------------------------------------------------------------|
| **Column A**         | Sequence numbers are assigned based on the ordered list of normalized pole IDs      |
| **Column B**         | Action codes are determined for each uniquely identified pole                       |
| **Column E**         | Pole structure is looked up using the normalized pole ID in both data sources       |
| **Columns J-K**      | Span metadata (lowest heights) is associated with pairs of normalized pole IDs      |
| **Columns L-O**      | Attachments are linked to their parent pole via normalized pole ID                  |

---

## 8 Edge-case Handling

| Case                                       | Handling                                             | Log Key                  |
|--------------------------------------------|------------------------------------------------------|--------------------------|
| Empty/null pole ID                         | Raise error - pole IDs are required                  | `EMPTY_POLE_ID`          |
| Pole in SPIDAcalc missing from Katapult    | Keep as primary with warning, use SPIDAcalc data only| `SPIDA_ONLY_POLE`        |
| Pole ID conflict (different but similar)   | Apply fuzzy matching, log warning if auto-resolved   | `POLE_ID_CONFLICT`       |
| Non-numeric ID after PL prefix             | Warn but preserve (could be special designation)     | `NON_STANDARD_POLE_ID`   |
| Duplicate normalized IDs                    | Raise error - pole IDs must be unique after normalization | `DUPLICATE_POLE_ID` |

---

## 9 Validation Checks

```python
def validate_pole_ids(pole_map):
    """Perform validation checks on pole IDs"""
    
    # Check for unnamed poles
    unnamed = [id for id in pole_map if not id or id == "PL"]
    if unnamed:
        raise ValueError(f"Found {len(unnamed)} poles with empty or invalid IDs")
    
    # Check for duplicate IDs after normalization
    norm_ids = list(pole_map.keys())
    duplicates = [id for id in set(norm_ids) if norm_ids.count(id) > 1]
    if duplicates:
        raise ValueError(f"Found duplicate normalized pole IDs: {duplicates}")
    
    # Check for unusual formats
    unusual = [id for id in pole_map if not re.match(r'^PL\d+$', id)]
    if unusual:
        log.warning(f"Found {len(unusual)} poles with unusual ID format: {unusual}")
    
    # Verify primary poles have SPIDAcalc data
    primary_without_spida = [id for id, info in pole_map.items() 
                            if info["is_primary"] and not info["spida_obj"]]
    if primary_without_spida:
        log.error(f"Primary poles missing SPIDAcalc data: {primary_without_spida}")
```

---

## 10 Unit-test Checklist

```python
def test_normalize_pole_id():
    """Test pole ID normalization"""
    assert normalize_pole_id("PL398491") == "PL398491"
    assert normalize_pole_id("370858") == "PL370858"
    assert normalize_pole_id("  pl389359  ") == "PL389359"
    
    # Test error cases
    with pytest.raises(ValueError):
        normalize_pole_id("")
    with pytest.raises(ValueError):
        normalize_pole_id(None)

def test_pole_id_reconciliation():
    """Test reconciliation between SPIDAcalc and Katapult"""
    # Mock data setup
    mock_spida = {"design": {"structure": {"poles": [
        {"externalId": "PL398491"},
        {"externalId": "PL389359"}
    ]}}}
    
    mock_katapult = {"nodes": {
        "node1": {"attributes": {"pole_tag": {"-Imported": {"tagtext": "398491"}}}},
        "node2": {"attributes": {"pole_tag": {"-Imported": {"tagtext": "PL389359"}}}},
        "node3": {"attributes": {"pole_tag": {"-Imported": {"tagtext": "370858"}}}}
    }}
    
    # Test reconciliation
    pole_map = reconcile_pole_ids(mock_spida, mock_katapult)
    
    # Verify results
    assert len(pole_map) == 3
    assert pole_map["PL398491"]["is_primary"] == True
    assert pole_map["PL389359"]["is_primary"] == True
    assert pole_map["PL370858"]["is_primary"] == False
    
    # Verify matching
    assert pole_map["PL398491"]["katapult_node_id"] == "node1"
    assert pole_map["PL389359"]["katapult_node_id"] == "node2"
```

---

## 11 Revision History

| Date       | Version | Notes                                                             |
|------------|---------|-------------------------------------------------------------------|
| 2025-05-19 | v1.0    | Initial column D spec – ties to two-pass pole-selection doc.      |
| 2025-05-20 | v2.0    | Enhanced with ID reconciliation, validation, and edge case handling |
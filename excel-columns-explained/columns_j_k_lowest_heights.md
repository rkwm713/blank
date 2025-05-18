# Columns J & K – Lowest Mid-Span Heights

> **Purpose** Define how the generator extracts and formats the **lowest mid-span heights** for each span in the Make-Ready report. Column J shows the lowest communication-space wire (non-CPS owners) and Column K shows the lowest CPS-owned electrical conductor, both measured at the span's midpoint.

---

## 1 Terminology and Definitions

| Term                | Definition                                                                                                       |
|---------------------|------------------------------------------------------------------------------------------------------------------|
| **Mid-Span Height** | Vertical clearance above ground (inches) at the lowest sag point between two poles                               |
| **Comm-space**      | Any attachment whose `owner` ≠ "CPS Energy" (Charter, AT&T, etc.)                                                |
| **CPS Electrical**  | Attachments owned by "CPS Energy" and categorized as `neutral`, `secondary`, or `service`                        |
| **Span**            | A section of wire/cable between two poles, identified by ordered pole IDs (From → To)                            |

Values are written in feet-inches format (e.g., `14'-10"`) or as `NA` when no data exists for that category.

---

## 2 Data Sources

| Value            | Primary Source | JSON Path                                           | Notes                                   |
|------------------|----------------|-----------------------------------------------------|------------------------------------------|
| **Mid-span heights** | Katapult      | `connections[*].sections[*].midspanHeight_in`       | Authoritative source for mid-span data   |
| **Wire metadata**    | Katapult      | `nodes[*].attachments.*[*]`                        | Used to determine owner and type         |
| **Pole identification** | Both       | See Column D specification                         | Needed to identify span endpoints        |

> **Important**: SPIDAcalc does not contain mid-span clearance data, so Katapult is the only source for these measurements. This makes proper handling of pole ID reconciliation especially critical for Columns J & K.

---

## 3 Enhanced Extraction Algorithm

```python
def extract_lowest_mid_span_heights(pole_map, katapult_data):
    """
    Extract the lowest mid-span heights for communication and CPS electrical wires.
    
    Args:
        pole_map: The reconciliation map between SPIDAcalc and Katapult
        katapult_data: Full Katapult JSON
        
    Returns:
        Dictionary mapping span pairs (from_pole, to_pole) to dict of 
        {"comm": height_in, "cps": height_in} where heights can be None
    """
    # Build a map of Katapult node IDs to normalized pole IDs
    node_id_to_pole_id = {}
    pole_id_to_node_id = {}
    
    for pole_id, info in pole_map.items():
        if info["katapult_node_id"]:
            node_id = info["katapult_node_id"]
            node_id_to_pole_id[node_id] = pole_id
            pole_id_to_node_id[pole_id] = node_id
    
    # Build wire metadata lookup: wire_id -> (owner, desc, type)
    wire_meta = {}
    wire_ids_missing_owner = set()
    
    for node_id, node in katapult_data["nodes"].items():
        if "attachments" not in node:
            continue
            
        for attachment_type, attachments in node["attachments"].items():
            if not isinstance(attachments, list):
                continue
                
            for attachment in attachments:
                if "id" in attachment:
                    wire_id = attachment["id"]
                    owner = attachment.get("owner", "")
                    desc = attachment.get("desc", "")
                    wire_type = attachment.get("type", "")
                    
                    wire_meta[wire_id] = {
                        "owner": owner,
                        "desc": desc,
                        "type": wire_type
                    }
                    
                    # Track wires with missing owner for logging
                    if not owner:
                        wire_ids_missing_owner.add(wire_id)
    
    if wire_ids_missing_owner:
        log.warning(f"Found {len(wire_ids_missing_owner)} wire IDs with missing owner information")
    
    # Initialize result map: (from_tag, to_tag) -> {"comm": min_h, "cps": min_h}
    span_low_heights = {}
    
    # Process all connections to find lowest heights
    for conn in katapult_data.get("connections", []):
        # Get normalized pole IDs for from/to nodes
        from_node_id = conn.get("from")
        to_node_id = conn.get("to")
        
        if not from_node_id or not to_node_id:
            log.warning(f"Connection missing from/to node IDs: {conn.get('id', 'unknown')}")
            continue
            
        if from_node_id not in node_id_to_pole_id or to_node_id not in node_id_to_pole_id:
            log.warning(f"Connection references unknown node: {from_node_id} → {to_node_id}")
            continue
        
        from_pole_id = node_id_to_pole_id[from_node_id]
        to_pole_id = node_id_to_pole_id[to_node_id]
        
        # Create a span identifier (ordered pair of pole IDs)
        span = (from_pole_id, to_pole_id)
        
        # Initialize heights for this span if not already present
        if span not in span_low_heights:
            span_low_heights[span] = {"comm": None, "cps": None}
        
        # Process each wire section in this span
        for section in conn.get("sections", []):
            wire_id = section.get("wire_id")
            height_in = section.get("midspanHeight_in")
            
            # Skip if missing critical data
            if not wire_id or not height_in:
                continue
                
            # Get wire metadata
            if wire_id not in wire_meta:
                log.warning(f"Wire ID {wire_id} not found in metadata")
                continue
                
            wire_info = wire_meta[wire_id]
            owner = wire_info["owner"]
            wire_type = wire_info["type"]
            
            # Determine category (comm or cps)
            if owner.startswith("CPS") and wire_type in ["neutral", "secondary", "service"]:
                category = "cps"
            elif owner and not owner.startswith("CPS"):
                category = "comm"
            else:
                # Skip wires that don't clearly fit either category
                log.info(f"Wire {wire_id} with owner '{owner}' and type '{wire_type}' skipped from height calculation")
                continue
            
            # Update minimum height if this is lower than current minimum
            current_min = span_low_heights[span][category]
            if current_min is None or height_in < current_min:
                span_low_heights[span][category] = height_in
                
                # Log critical clearance warnings
                if height_in < 120:  # Less than 10 feet
                    log.warning(f"CRITICAL: {category.upper()} clearance of {height_in}in ({format_height(height_in)}) on span {from_pole_id} → {to_pole_id}")
    
    return span_low_heights

def format_height(height_in):
    """
    Convert height in inches to feet-inches format (e.g., 178.5 → "14'-10"").
    
    Args:
        height_in: Height in inches (float or int)
        
    Returns:
        Formatted height string or "NA" if height is None
    """
    if height_in is None:
        return "NA"
        
    # Convert to feet and inches
    feet = int(height_in) // 12
    inches = round(height_in % 12)
    
    # Handle case where inches rounds to 12
    if inches == 12:
        feet += 1
        inches = 0
        
    return f"{feet}'-{inches}\""
```

---

## 4 Integration with Report Generation

```python
# During span data processing
def write_span_data(worksheet, current_row, from_pole_id, to_pole_id, span_heights):
    """
    Write span data including lowest mid-span heights.
    
    Args:
        worksheet: Excel worksheet object
        current_row: Row index to start writing
        from_pole_id: Normalized "From" pole ID
        to_pole_id: Normalized "To" pole ID
        span_heights: Dictionary of span heights from extract_lowest_mid_span_heights
    """
    # Identify the span (order matters)
    span = (from_pole_id, to_pole_id)
    span_reversed = (to_pole_id, from_pole_id)
    
    # Get heights data, checking both directions
    heights = None
    if span in span_heights:
        heights = span_heights[span]
    elif span_reversed in span_heights:
        heights = span_heights[span_reversed]
    
    # Write the lowest heights
    if heights:
        comm_height = format_height(heights.get("comm"))
        cps_height = format_height(heights.get("cps"))
    else:
        comm_height = "NA"
        cps_height = "NA"
    
    # Write to cells
    worksheet.write(current_row, 9, comm_height)  # Column J = index 9
    worksheet.write(current_row, 10, cps_height)  # Column K = index 10
    
    # Apply conditional formatting for critical clearances
    if heights:
        if heights.get("comm") and heights["comm"] < 120:
            # Apply critical warning format to comm height
            worksheet.write(current_row, 9, comm_height, formats["critical_warning"])
        
        if heights.get("cps") and heights["cps"] < 120:
            # Apply critical warning format to CPS height
            worksheet.write(current_row, 10, cps_height, formats["critical_warning"])
```

---

## 5 Project CPS 6457E 03 – Sample Mapping

| Span (From → To)         | Column J (Lowest Comm) | Column K (Lowest CPS) |
|--------------------------|------------------------|------------------------|
| **PL410620 → PL398491**  | 14'-10"                | 23'-10"                |
| **PL398491 → PL401451**  | NA                     | NA                     |
| **PL389359 → PL404474**  | 17'-8"                 | 22'-8"                 |
| **PL404474 → PL900997**  | 19'-6"                 | 23'-8"                 |
| **PL900997 → PL398490**  | NA                     | NA                     |
| **PL370858 → PL3268481** | 20'-8"                 | 21'-7"                 |

---

## 6 Relationship with Other Columns

| Column        | Relationship to Columns J/K (Lowest Heights)                                          |
|---------------|--------------------------------------------------------------------------------------|
| **Column D**  | Pole IDs determine which spans are analyzed for mid-span heights                      |
| **Columns L-O** | Individual attachment mid-span heights in Column O should be consistent with J/K minimums |
| **QC Sheet**  | Critical clearance violations should appear in both Column J/K highlighting and QC report |

---

## 7 Comprehensive Edge Case Handling

| Case                                          | Handling                                             | Log Key                    |
|-----------------------------------------------|------------------------------------------------------|-----------------------------|
| No `sections` for span                        | Write `NA` in both columns                           | `MIDSPAN_MISSING`           |
| Only CPS but no comm                          | `NA` in Column J, normal value in Column K           | `MIDSPAN_NO_COMM`           |
| Only comm but no CPS                          | Normal value in Column J, `NA` in Column K           | `MIDSPAN_NO_CPS`            |
| Mid-span value < 120 in (10 ft)               | Highlight cells red, log critical warning            | `CLEARANCE_CRITICAL`        |
| Wire ID not found in metadata                 | Log warning, skip that section                       | `WIRE_METADATA_MISSING`     |
| Missing owner information                     | Attempt to infer from wire type, log warning         | `OWNER_MISSING`             |
| Pole tags in span not found in pole map       | Log warning, continue with other spans               | `SPAN_POLE_UNRECOGNIZED`    |
| Multiple spans between same poles             | Process all, take minimum per category               | `MULTIPLE_SPANS_SAME_POLES` |
| Connection without from/to node IDs           | Log warning, skip that connection                    | `CONNECTION_INCOMPLETE`     |
| Height value is not numeric                   | Log error, treat as missing (NA)                     | `NON_NUMERIC_HEIGHT`        |
| Mid-span inches rounds to 12"                 | Correctly convert to next foot (e.g., 11'-12" → 12'-0") | `INCH_ROUNDING`         |

---

## 8 Validation Rules

```python
def validate_span_heights(span_heights, pole_map, minimum_clearance=120):
    """
    Validate all span heights for reasonableness and code compliance.
    
    Args:
        span_heights: Dictionary of span heights from extract_lowest_mid_span_heights
        pole_map: The reconciliation map between SPIDAcalc and Katapult
        minimum_clearance: Minimum acceptable clearance in inches (default 120 = 10 feet)
        
    Returns:
        List of validation issues
    """
    issues = []
    
    # Primary poles (operations) that should have span data
    primary_poles = set(id for id, info in pole_map.items() if info["is_primary"])
    
    # Spans with height data
    spans_with_data = set(span_heights.keys())
    
    # Check for spans with violations
    for span, heights in span_heights.items():
        from_pole, to_pole = span
        
        # Check for critical clearance violations
        if heights.get("comm") and heights["comm"] < minimum_clearance:
            issues.append((
                "ERROR", 
                f"Critical comm clearance violation: {format_height(heights['comm'])} "
                f"on span {from_pole} → {to_pole}"
            ))
            
        if heights.get("cps") and heights["cps"] < minimum_clearance:
            issues.append((
                "ERROR", 
                f"Critical CPS clearance violation: {format_height(heights['cps'])} "
                f"on span {from_pole} → {to_pole}"
            ))
        
        # Check for uncommon clearance gaps
        if heights.get("comm") and heights.get("cps"):
            gap = heights["cps"] - heights["comm"]
            if gap < 24:  # Less than 2 feet separation
                issues.append((
                    "WARNING", 
                    f"Small vertical separation ({gap}in) between CPS and comm "
                    f"on span {from_pole} → {to_pole}"
                ))
    
    # Check for missing span data on primary poles
    connected_poles = set()
    for from_pole, to_pole in spans_with_data:
        connected_poles.add(from_pole)
        connected_poles.add(to_pole)
    
    # Find primary poles with no span data
    isolated_poles = primary_poles - connected_poles
    if isolated_poles:
        issues.append((
            "WARNING",
            f"Found {len(isolated_poles)} primary poles with no span data: {sorted(isolated_poles)}"
        ))
    
    return issues
```

---

## 9 Unit Test Checklist

```python
@pytest.mark.parametrize("height_in,expected", [
    (178.5, "14'-10\""),
    (120, "10'-0\""),
    (284.4, "23'-8\""),
    (None, "NA"),
    (11.99, "1'-0\""),  # Should round to 1'-0" not 0'-12"
    (35.5, "2'-11\""),  # Test rounding
    (35.51, "3'-0\""),  # Test rounding up
])
def test_format_height(height_in, expected):
    """Test height formatting function"""
    assert format_height(height_in) == expected

def test_extract_lowest_heights():
    """Test extraction of lowest heights from connection data"""
    # Mock Katapult data
    mock_katapult = {
        "nodes": {
            "node1": {"attachments": {
                "wires": [
                    {"id": "wire1", "owner": "CPS Energy", "type": "neutral"},
                    {"id": "wire2", "owner": "AT&T", "type": "communication"}
                ]
            }},
            "node2": {"attachments": {
                "wires": [
                    {"id": "wire3", "owner": "CPS Energy", "type": "neutral"},
                    {"id": "wire4", "owner": "Charter", "type": "communication"}
                ]
            }}
        },
        "connections": [{
            "from": "node1",
            "to": "node2",
            "sections": [
                {"wire_id": "wire1", "midspanHeight_in": 250},
                {"wire_id": "wire2", "midspanHeight_in": 121.8},
                {"wire_id": "wire3", "midspanHeight_in": 278.4},
                {"wire_id": "wire4", "midspanHeight_in": 195.6}
            ]
        }]
    }
    
    # Mock pole map
    mock_pole_map = {
        "PL1": {"katapult_node_id": "node1", "is_primary": True},
        "PL2": {"katapult_node_id": "node2", "is_primary": True}
    }
    
    # Extract heights
    heights = extract_lowest_mid_span_heights(mock_pole_map, mock_katapult)
    
    # Check results
    assert ("PL1", "PL2") in heights
    assert heights[("PL1", "PL2")]["comm"] == 121.8  # Lowest comm wire
    assert heights[("PL1", "PL2")]["cps"] == 250     # Lowest CPS wire
    
    # Format the heights
    comm_height = format_height(heights[("PL1", "PL2")]["comm"])
    cps_height = format_height(heights[("PL1", "PL2")]["cps"])
    
    assert comm_height == "10'-2\""
    assert cps_height == "20'-10\""
```

---

## 10 Revision History

| Date       | Version | Notes                                                                      |
|------------|---------|----------------------------------------------------------------------------|
| 2025-05-19 | v1.0    | Initial spec for J-K extraction, includes sample table.                     |
| 2025-05-21 | v2.0    | Enhanced with pole ID reconciliation, validation, and comprehensive edge cases |
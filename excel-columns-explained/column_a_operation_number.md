# Column A – Sequence Number

> **Purpose** Define how the generator fills **Column A** with sequential numbering for each operation in the Make-Ready report. This column provides a unique identifier for each pole operation block for easier reference and tracking.

---

## 1 Definition

*Sequence Number* is an auto-incremented integer that starts at 1 and increases for each new operation header (blue row merged A-I). It appears only in the merged operation header row and helps stakeholders reference specific poles during review meetings and field work.

The value is written in Column A of the blue operation-header row and is merged vertically along with Columns B-I across all attachment rows for that pole.

---

## 2 Data Generation

```python
def generate_sequence_numbers(poles):
    """
    Generate sequential numbers for each operation in the report.
    
    Args:
        poles: List of primary poles from SPIDAcalc to be included in report
        
    Returns:
        Dictionary mapping pole externalId to sequence number
    """
    sequence_map = {}
    
    # Sort poles by a consistent order (e.g., route order if available, otherwise by tag)
    # This ensures sequence numbers are logical and follow the field route when possible
    sorted_poles = sort_poles_by_route_order(poles)
    
    for i, pole in enumerate(sorted_poles, start=1):
        pole_id = pole.get("externalId") or get_pole_tag_from_katapult(pole)
        sequence_map[pole_id] = i
    
    return sequence_map
```

## 3 Route-Based Ordering (Recommended)

For more intuitive field use, sequence numbers should follow the physical route order when available:

```python
def sort_poles_by_route_order(poles):
    """Sort poles according to route order if available in the Katapult data"""
    # First attempt: Use explicit route_order attribute if present
    if any("route_order" in p.get("attributes", {}) for p in poles):
        return sorted(poles, key=lambda p: p.get("attributes", {}).get("route_order", 9999))
    
    # Second attempt: Construct route from connections
    # For a linear route, we can start with a pole that has only one connection
    # and follow connections to build the complete route
    if katapult_connections_available:
        return construct_route_from_connections(poles, connections)
    
    # Fallback: Sort by pole tag numerically when possible
    return sorted(poles, key=lambda p: extract_numeric_part(p.get("externalId", "")))
```

## 4 Examples

| Column A | Column B        | Column C | Column D   | ... |
|----------|-----------------|----------|------------|-----|
| **1**    | (I) Installing  | CPS      | PL410620   | ... |
| **2**    | (R) Removing    | CPS      | PL398491   | ... |
| **3**    | (E) Existing    | CPS      | PL389359   | ... |
| **4**    | (I) Installing  | CPS      | PL404474   | ... |
| **5**    | (E) Existing    | CPS      | PL900997   | ... |
| **6**    | (I) Installing  | CPS      | PL370858   | ... |

*Example shows sequence numbers for the six operation poles in project CPS 6457E 03.*

---

## 5 Integration with Report Generation

The sequence number should be applied during the first pass of report generation along with the operation header:

```python
# During primary pass
sequence_map = generate_sequence_numbers(primary_poles)

for pole in primary_poles:
    pole_id = pole.get("externalId") or get_pole_tag_from_katapult(pole)
    
    # Write merged header cells A-I
    write_cell(row=current_row, col="A", value=sequence_map[pole_id])
    write_cell(row=current_row, col="B", value=f"({pole_action.name}) {pole_action_text[pole_action]}")
    # ... other header columns ...
    
    # Merge cells A-I vertically across all attachment rows
    merge_range(f"A{current_row}:I{current_row + attachment_count}")
```

---

## 6 Edge-case handling

| Case                               | Handling                                        | Log key              |
|------------------------------------|-------------------------------------------------|----------------------|
| No poles in SPIDAcalc              | Report contains no operation blocks             | `NO_PRIMARY_POLES`   |
| Cannot determine route order       | Fall back to numeric/alphanumeric pole tag sort | `NO_ROUTE_ORDER`     |
| Disconnected pole clusters         | Number each cluster sequentially                | `MULTIPLE_CLUSTERS`  |

---

## 7 Unit-test checklist

```python
def test_sequence_numbering():
    # Test basic sequential numbering
    poles = [{"externalId": f"PL{i}"} for i in range(100, 105)]
    sequence_map = generate_sequence_numbers(poles)
    assert len(sequence_map) == 5
    assert all(1 <= seq <= 5 for seq in sequence_map.values())
    
    # Test that each pole gets a unique number
    assert len(set(sequence_map.values())) == 5
    
    # Test sorting when route_order is available
    poles_with_route = [
        {"externalId": "PL102", "attributes": {"route_order": 3}},
        {"externalId": "PL101", "attributes": {"route_order": 1}},
        {"externalId": "PL103", "attributes": {"route_order": 2}}
    ]
    route_map = generate_sequence_numbers(poles_with_route)
    assert route_map["PL101"] == 1
    assert route_map["PL103"] == 2
    assert route_map["PL102"] == 3
```

---

## 8 Revision history

| Date       | Version | Notes                                                     |
|------------|---------|-----------------------------------------------------------|
| 2025-05-20 | v1.0    | Initial specification for Column A sequence numbering.    |
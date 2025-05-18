# Columns F & G – Proposed Riser & Proposed Guy

> **Purpose** Define how the generator determines and formats the **Proposed Riser** (Column F) and **Proposed Guy** (Column G) values in the operation-header row for each SPIDAcalc pole. These values indicate new installation plans for vertical conduits and anchor cables.

---

## 1 Definitions

| Column | Heading                       | Meaning                                                                                            |
| ------ | ----------------------------- | -------------------------------------------------------------------------------------------------- |
| **F**  | Proposed Riser (Yes/No) & QTY | Indicates if one or more new risers (vertical conduits into ground) will be installed on the pole. |
| **G**  | Proposed Guy (Yes/No) & QTY   | Indicates if one or more new down-guys (anchor cables) will be installed.                          |

Values are written as:

```
YES (<count>)   or   NO
```

The cells are merged vertically along with the rest of the operation header (Columns A-I).

---

## 2 Data Sources

Both SPIDAcalc and Katapult may contain information about proposed risers and guys:

| Column | Primary Source | JSON Path                                       | Secondary Source | JSON Path                                                 |
|--------|----------------|------------------------------------------------|------------------|-----------------------------------------------------------|
| **F**  | Katapult       | `nodes[*].attachments.riser[*]` where `proposed == true` | SPIDAcalc | `design.structure.poles[*].recommendedAttachments[*]` where `type == "riser"` |
| **G**  | Katapult       | `nodes[*].attachments.guying[*]` where `proposed == true` | SPIDAcalc | `design.structure.poles[*].recommendedAttachments[*]` where `type == "guying"` |

> **Note**: SPIDAcalc may use either a separate `recommendedAttachments` block or have regular attachments marked with `design.recommended == true`. Either way, these represent proposed additions.

---

## 3 Extraction and Formatting Algorithm

```python
def get_proposed_counts(pole_id, pole_map, spida_data, katapult_data):
    """
    Extract counts of proposed risers and guys for a given pole.
    
    Args:
        pole_id: Normalized pole ID
        pole_map: The reconciliation map between SPIDAcalc and Katapult
        spida_data: Full SPIDAcalc JSON
        katapult_data: Full Katapult JSON
        
    Returns:
        Tuple of (riser_count, guy_count)
    """
    riser_count = 0
    guy_count = 0
    
    # Get pole objects from both sources
    pole_info = pole_map.get(pole_id)
    if not pole_info:
        raise ValueError(f"Pole ID {pole_id} not found in pole map")
    
    # Check Katapult first (primary source)
    if pole_info["katapult_obj"]:
        katapult_node = pole_info["katapult_obj"]
        
        # Count proposed risers in Katapult
        if "attachments" in katapult_node and "riser" in katapult_node["attachments"]:
            riser_list = katapult_node["attachments"]["riser"]
            riser_count += sum(1 for r in riser_list if r.get("proposed") is True)
        
        # Count proposed guys in Katapult
        if "attachments" in katapult_node and "guying" in katapult_node["attachments"]:
            guy_list = katapult_node["attachments"]["guying"]
            guy_count += sum(1 for g in guy_list if g.get("proposed") is True)
    
    # Check SPIDAcalc (secondary source)
    if pole_info["spida_obj"]:
        spida_pole = pole_info["spida_obj"]
        
        # Handle SPIDAcalc v10+ with recommendedAttachments block
        if "design" in spida_pole and "recommendedAttachments" in spida_pole["design"]:
            recommended = spida_pole["design"]["recommendedAttachments"]
            riser_count += sum(1 for a in recommended if a.get("type") == "riser")
            guy_count += sum(1 for a in recommended if a.get("type") == "guying")
        
        # Alternative: check regular attachments with design.recommended flag
        if "attachments" in spida_pole:
            for att in spida_pole["attachments"]:
                if att.get("design", {}).get("recommended", False):
                    if att.get("type") == "riser":
                        riser_count += 1
                    elif att.get("type") == "guying":
                        guy_count += 1
    
    return riser_count, guy_count

def format_proposed_values(riser_count, guy_count):
    """
    Format the proposed riser and guy counts for Excel output.
    
    Args:
        riser_count: Count of proposed risers
        guy_count: Count of proposed guys
        
    Returns:
        Tuple of (riser_text, guy_text)
    """
    # Format as "YES (count)" or "NO"
    riser_text = f"YES ({riser_count})" if riser_count > 0 else "NO"
    guy_text = f"YES ({guy_count})" if guy_count > 0 else "NO"
    
    return riser_text, guy_text
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
    
    # Write columns A-E (previously defined)
    write_cell(row=current_row, col="A", value=sequence_map[pole_id])
    write_cell(row=current_row, col="B", value=ACTION_DISPLAY[determine_pole_action(attachments)])
    write_cell(row=current_row, col="C", value=POLE_OWNER_CONSTANT)
    write_cell(row=current_row, col="D", value=pole_id)
    write_cell(row=current_row, col="E", value=extract_pole_structure(pole_id, pole_map, spida_data, katapult_data))
    
    # Get and write proposed riser/guy counts
    riser_count, guy_count = get_proposed_counts(pole_id, pole_map, spida_data, katapult_data)
    riser_text, guy_text = format_proposed_values(riser_count, guy_count)
    
    write_cell(row=current_row, col="F", value=riser_text)
    write_cell(row=current_row, col="G", value=guy_text)
    
    # Merge cells for the header section
    merge_range(f"A{current_row}:I{current_row + attachment_count}")
    
    # ... process attachments ...
```

---

## 5 Project CPS 6457E 03 – Sample Mapping

| Pole #       | Proposed Riser (F) | Proposed Guy (G) |
|--------------|-------------------|-------------------|
| **PL410620** | YES (1)           | YES (1)           |
| **PL398491** | NO                | NO                |
| **PL389359** | NO                | NO                |
| **PL404474** | NO                | NO                |
| **PL900997** | YES (1)           | YES (1)           |
| **PL370858** | YES (1)           | YES (1)           |

*These counts come from Katapult's `riser` and `guying` arrays with `proposed` flag.*

---

## 6 Relationship with Other Columns

| Column          | Relationship to Columns F/G (Proposed Riser/Guy)                          |
|-----------------|--------------------------------------------------------------------------|
| **Column B**    | (I) Installing code is expected when F or G shows "YES"                  |
| **Columns L-O** | Risers and guys should appear in the attachment list with Proposed heights|
| **QC Sheet**    | Riser and guy counts help validate material estimates                     |

---

## 7 Edge-case Handling

| Case                                      | Handling                                           | Log Key                 |
|-------------------------------------------|----------------------------------------------------| ----------------------- |
| Missing attachment arrays in Katapult     | Treat as empty (count=0)                           | `MISSING_ATTACHMENT_ARRAY` |
| Duplicate entries in SPIDAcalc and Katapult | Count each unique installation once              | `DUPLICATE_INSTALLATIONS` |
| Proposed field missing but new attachment | Conservative approach: only count explicit `proposed == true` | `AMBIGUOUS_PROPOSED_FLAG` |
| Proposed field is non-boolean             | Interpret any truthy value as proposed             | `NON_BOOLEAN_PROPOSED` |
| `attachments` property missing entirely   | Handle gracefully, return zeros                    | `NO_ATTACHMENTS_PROPERTY` |

---

## 8 Validation Rules

```python
def validate_proposed_counts(pole_id, riser_count, guy_count, attachments, action_code):
    """
    Validate that the proposed counts are consistent with attachments and actions.
    
    Args:
        pole_id: Normalized pole ID
        riser_count: Count of proposed risers
        guy_count: Count of proposed guys
        attachments: List of attachment info objects
        action_code: Overall pole action code
        
    Returns:
        List of validation issues or empty list if valid
    """
    issues = []
    
    # Check for consistency with action code
    if (riser_count > 0 or guy_count > 0) and action_code != Action.I:
        issues.append(("WARNING", f"Proposed riser/guy but action code is not (I) Installing"))
    
    # Check for consistency with attachment list
    riser_in_attachments = any("riser" in a.description.lower() for a in attachments 
                              if a.action == Action.I)
    
    guy_in_attachments = any("guy" in a.description.lower() for a in attachments 
                             if a.action == Action.I)
    
    if riser_count > 0 and not riser_in_attachments:
        issues.append(("WARNING", f"Proposed riser count {riser_count} but no riser in attachment list"))
    
    if guy_count > 0 and not guy_in_attachments:
        issues.append(("WARNING", f"Proposed guy count {guy_count} but no guy in attachment list"))
    
    return issues
```

---

## 9 Unit-test Checklist

```python
@pytest.mark.parametrize("riser_list,guy_list,exp_r,exp_g", [
    # Basic cases
    ([{"proposed": True}], [{"proposed": True}], "YES (1)", "YES (1)"),
    ([], [], "NO", "NO"),
    ([{"proposed": True}, {"proposed": True}], [], "YES (2)", "NO"),
    
    # Edge cases
    (None, None, "NO", "NO"),
    ([{"proposed": False}], [{"proposed": None}], "NO", "NO"),
    ([{"proposed": 1}], [{"proposed": "yes"}], "YES (1)", "YES (1)")  # Truthy values
])
def test_proposed_riser_guy(riser_list, guy_list, exp_r, exp_g):
    """Test proposed riser and guy counting and formatting"""
    # Create mock node with the attachment lists
    mock_node = {"attachments": {}}
    if riser_list is not None:
        mock_node["attachments"]["riser"] = riser_list
    if guy_list is not None:
        mock_node["attachments"]["guying"] = guy_list
    
    # Mock pole map for testing
    mock_pole_map = {"PL12345": {"katapult_obj": mock_node, "spida_obj": None}}
    
    # Test counting function
    riser_count, guy_count = get_proposed_counts("PL12345", mock_pole_map, {}, {})
    riser_text, guy_text = format_proposed_values(riser_count, guy_count)
    
    assert riser_text == exp_r
    assert guy_text == exp_g
```

---

## 10 Revision History

| Date       | Version | Notes                                                 |
|------------|---------|-------------------------------------------------------|
| 2025-05-20 | v1.0    | Initial specification for Columns F & G               |
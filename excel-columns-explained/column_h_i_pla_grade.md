# Columns H & I – PLA (%) & Construction Grade

> **Purpose** Define how the generator extracts and formats the **Pole Loading Analysis (PLA)** percentage after proposed attachments (Column H) and the **Construction Grade of Analysis** (Column I) for each operation in the Make-Ready report.

---

## 1 Definitions

| Column | Heading                          | Meaning                                                                  |
|--------|----------------------------------|--------------------------------------------------------------------------|
| **H**  | PLA (%) with proposed attachment | The maximum pole utilization percentage under the proposed make‑ready configuration |
| **I**  | Construction Grade of Analysis   | The load-case grade (e.g., A, B, C) used for structural analysis         |

These values appear in the operation header row and are merged vertically across all attachment rows for that pole.

---

## 2 Data Sources

| Column | Primary Source | JSON Path                                | Fallback      | Notes                               |
|--------|----------------|------------------------------------------|---------------|-------------------------------------|
| **H**  | SPIDAcalc      | `leads[0].locations[i].poleResults[?(@.component=="Pole" && @.analysisType=="STRESS")].actual`   | None          | Decimal value (e.g., 0.7870)        |
| **I**  | Hard-coded     | Static value: "C"                        | SPIDAcalc     | Optional extraction from `leads[0].locations[i].poleResults[?(@.component=="Pole")].loadInfo` |

> **Note**: For all CPS Energy projects, Construction Grade is fixed to "C" per client directive. Future enhancement may allow extraction from SPIDAcalc if requirements change.

---

## 3 Extraction and Formatting Algorithm

```python
def extract_pla_data(pole_id, pole_map, spida_data):
    """
    Extract PLA percentage and construction grade for a given pole.
    
    Args:
        pole_id: Normalized pole ID
        pole_map: The reconciliation map between SPIDAcalc and Katapult
        spida_data: Full SPIDAcalc JSON
        
    Returns:
        Tuple of (pla_percentage, construction_grade)
    """
    # Default values if data is missing
    pla_percentage = "N/A"
    construction_grade = "C"  # Hard-coded for CPS Energy projects
    
    # Check if SPIDAcalc data is available
    pole_info = pole_map.get(pole_id)
    if not pole_info or not pole_info["spida_obj"]:
        log.warning(f"No SPIDAcalc data for pole {pole_id}, cannot extract PLA")
        return pla_percentage, construction_grade
    
    # Get SPIDAcalc location object
    spida_location = pole_info["spida_obj"]
    
    # Look for the poleResults section
    if "poleResults" not in spida_location:
        log.warning(f"SPIDAcalc pole {pole_id} has no poleResults, PLA data unavailable")
        return pla_percentage, construction_grade
    
    # Find the analysis result for the pole
    try:
        for result in spida_location.get("poleResults", []):
            if result.get("component") == "Pole" and result.get("analysisType") == "STRESS":
                # Found the matching result - extract utilization
                utilization = result.get("actual")
                if utilization is not None:
                    # Validate utilization is in reasonable range
                    if 0 <= utilization <= 1:
                        pla_percentage = f"{utilization * 100:.2f}%"
                    else:
                        log.warning(f"Pole {pole_id} has out-of-range utilization: {utilization}")
                        # Cap at valid range and format
                        capped = max(0, min(1, utilization))
                        pla_percentage = f"{capped * 100:.2f}%"
                
                # Extract construction grade if needed in future
                # if "loadInfo" in result:
                #    load_info = result.get("loadInfo")
                #    grade_match = re.search(r"Grade\s+([A-C])", load_info)
                #    if grade_match:
                #        construction_grade = grade_match.group(1)
                
                break
    except (IndexError, KeyError, TypeError) as e:
        log.error(f"Error extracting PLA data for pole {pole_id}: {str(e)}")
    
    return pla_percentage, construction_grade
```

---

## 4 Integration with Report Generation

```python
# During primary pole processing
for pole_id in primary_poles:
    # Get pole info
    pole_info = pole_map[pole_id]
    spida_location = find_pole_by_external_id(spida_data, pole_id)
    
    # Write operation header
    current_row = get_next_row()
    
    # Write columns A-G (previously defined)
    write_cell(row=current_row, col="A", value=sequence_map[pole_id])
    write_cell(row=current_row, col="B", value=ACTION_DISPLAY[determine_pole_action(attachments)])
    write_cell(row=current_row, col="C", value=POLE_OWNER_CONSTANT)
    write_cell(row=current_row, col="D", value=pole_id)
    write_cell(row=current_row, col="E", value=extract_pole_structure(pole_id, pole_map, spida_data, katapult_data))
    
    # Write riser and guy info (columns F-G)
    riser_count, guy_count = get_proposed_counts(pole_id, pole_map, spida_data, katapult_data)
    riser_text, guy_text = format_proposed_values(riser_count, guy_count)
    write_cell(row=current_row, col="F", value=riser_text)
    write_cell(row=current_row, col="G", value=guy_text)
    
    # Get and write PLA data
    pla_percentage, construction_grade = extract_pla_data(pole_id, pole_map, spida_data)
    write_cell(row=current_row, col="H", value=pla_percentage)
    write_cell(row=current_row, col="I", value=construction_grade)
    
    # Merge cells for the header section
    merge_range(f"A{current_row}:I{current_row + attachment_count}")
    
    # ... process attachments ...
```

---

## 5 Project CPS 6457E 03 – Sample Mapping

| Pole #       | PLA (%) with proposed attachment (H) | Construction Grade (I) |
|--------------|-------------------------------------|------------------------|
| **PL410620** | 78.70%                              | C                      |
| **PL398491** | 62.08%                              | C                      |
| **PL389359** | 84.86%                              | C                      |
| **PL404474** | 59.84%                              | C                      |
| **PL900997** | 64.73%                              | C                      |
| **PL370858** | 42.55%                              | C                      |

---

## 6 Relationship with Other Columns

| Column           | Relationship to Columns H/I (PLA %/Construction Grade)                   |
|------------------|-------------------------------------------------------------------------|
| **Column B**     | Action code (I/R/E) should align with PLA % - installs usually increase utilization |
| **Columns F/G**  | New risers/guys affect pole loading, reflected in PLA %                 |
| **QC Sheet**     | PLA % exceeding thresholds (typically >100%) should trigger warnings    |

---

## 7 Edge Case Handling

| Case                                      | Handling                                    | Log Key                  |
|-------------------------------------------|---------------------------------------------|--------------------------|
| Missing `poleResults` in SPIDAcalc        | Display "N/A" for PLA %                     | `PLA_RESULTS_MISSING`    |
| Pole ID not found in SPIDAcalc            | Display "N/A" for PLA %                     | `PLA_ID_MISSING`         |
| PLA value outside 0–1 range               | Clamp to 0-100% range and log warning       | `PLA_OUT_OF_RANGE`       |
| Multiple result sets in SPIDAcalc         | Use first applicable result                 | `MULTIPLE_RESULT_SETS`   |
| No location found for pole                | Display "N/A" for PLA %                     | `MISSING_LOCATION`       |
| Error during extraction                   | Log exception, display "N/A"                | `PLA_EXTRACTION_ERROR`   |

---

## 8 Validation Rules

```python
def validate_pla_data(pole_id, pla_percentage, construction_grade, action_code):
    """
    Validate that the PLA data is reasonable and consistent.
    
    Args:
        pole_id: Normalized pole ID
        pla_percentage: Formatted PLA percentage or "N/A"
        construction_grade: Construction grade of analysis
        action_code: Overall pole action code
        
    Returns:
        List of validation issues or empty list if valid
    """
    issues = []
    
    # Check if PLA is available
    if pla_percentage == "N/A":
        issues.append(("WARNING", f"PLA data not available for pole {pole_id}"))
        return issues
    
    # Parse percentage value for validation
    try:
        # Strip percentage sign and convert to float
        pla_value = float(pla_percentage.strip("%"))
        
        # Check for overloaded pole (>100%)
        if pla_value > 100:
            issues.append(("ERROR", f"Pole {pole_id} is overloaded: {pla_percentage}"))
        
        # Check for nearing capacity (>85%)
        elif pla_value > 85:
            issues.append(("WARNING", f"Pole {pole_id} is nearing capacity: {pla_percentage}"))
        
        # Check for very low utilization (<10%)
        elif pla_value < 10:
            issues.append(("INFO", f"Pole {pole_id} has unusually low utilization: {pla_percentage}"))
        
        # Check for consistency with action code
        if action_code == Action.I and pla_value < 30:
            issues.append(("INFO", f"Installing action with low PLA {pla_percentage} - verify analysis"))
        
    except ValueError:
        issues.append(("ERROR", f"Invalid PLA percentage format: {pla_percentage}"))
    
    # Validate construction grade
    if construction_grade not in ["A", "B", "C"]:
        issues.append(("WARNING", f"Unusual construction grade: {construction_grade}"))
    
    return issues
```

---

## 9 Unit Test Checklist

```python
@pytest.mark.parametrize("utilization,expected", [
    (0.7870, "78.70%"),
    (0.1000, "10.00%"),
    (0.0123, "1.23%"),
    (1.0000, "100.00%"),
    (0.0000, "0.00%"),
    # Edge cases
    (1.5000, "100.00%"),  # Should be capped at 100%
    (-0.100, "0.00%"),    # Should be capped at 0%
])
def test_pla_formatting(utilization, expected):
    """Test PLA percentage formatting"""
    # Mock SPIDAcalc data
    mock_location = {
        "poleResults": [
            {"component": "Pole", "analysisType": "STRESS", "actual": utilization}
        ]
    }
    
    # Mock pole map
    mock_pole_map = {"PL12345": {"spida_obj": mock_location}}
    
    # Test extraction and formatting
    pla_percentage, _ = extract_pla_data("PL12345", mock_pole_map, {})
    
    assert pla_percentage == expected

def test_missing_results():
    """Test handling of missing results section"""
    # Mock data without results
    mock_location = {}
    mock_pole_map = {"PL12345": {"spida_obj": mock_location}}
    
    # Test extraction
    pla_percentage, construction_grade = extract_pla_data("PL12345", mock_pole_map, {})
    
    # Verify defaults are used
    assert pla_percentage == "N/A"
    assert construction_grade == "C"
```

---

## 10 Revision History

| Date       | Version | Notes                                                    |
|------------|---------|----------------------------------------------------------|
| 2025-05-20 | v1.0    | Initial specification for Columns H & I                  |
| 2025-05-21 | v1.1    | Enhanced with validation, edge cases, and relationship to other columns |
| 2025-05-25 | v1.2    | Updated to use standardized JSON paths                   | 
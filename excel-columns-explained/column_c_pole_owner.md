# Column C – Pole Owner

> **Purpose** Define how the generator populates the **Pole Owner** field in Column C of the Make-Ready report, which identifies the utility that owns the physical pole structure. This specification also explains the relationship with attachment owners and potential future expansion.

---

## 1 Definition

*Pole Owner* identifies the utility company that owns the physical pole structure. For all CPS Energy projects, this value is hard-coded to **`CPS`** (exact three-letter string, no punctuation).

The value is written once in Column C of the blue operation-header row and is merged vertically across all attachment rows for that pole, regardless of which companies own the individual attachments on that pole.

---

## 2 Implementation

```python
# Global constant used for all Make-Ready reports in the CPS Energy service area
POLE_OWNER_CONSTANT = "CPS"

def write_pole_owner(worksheet, row_index, attachment_count):
    """
    Write the pole owner in Column C and apply appropriate merging.
    
    Args:
        worksheet: The Excel worksheet object
        row_index: Starting row for this pole's operation block
        attachment_count: Number of attachment rows that follow the header
    """
    # Write the value in the header row
    worksheet.write(row_index, 2, POLE_OWNER_CONSTANT)  # Column C = index 2
    
    # Merge vertically across all attachment rows (if any)
    if attachment_count > 0:
        worksheet.merge_range(row_index, 2, row_index + attachment_count, 2, POLE_OWNER_CONSTANT)
```

---

## 3 Rationale for Hard-coding

The pole owner is set to "CPS" for all reports generated under this tool because:

1. All poles in the CPS Energy service area relevant to these make-ready reports are owned by CPS Energy
2. Even if other owners' poles appear in the route (e.g., AT&T or Frontier), they would be processed in separate reports specific to those owners
3. Simplifies the user interface by avoiding extra input requirements
4. Eliminates potential errors from mismatched pole owner data in JSON files
5. Approved by CPS as the standard format for their Make-Ready projects

---

## 4 Integration with Other Columns

| Related Column | Relationship                                                                                    |
| -------------- | ----------------------------------------------------------------------------------------------- |
| **Column B**   | Action code (I/R/E) is independent of pole owner                                                |
| **Column D**   | Pole # uniquely identifies the structure, regardless of owner                                   |
| **Column L**   | Attacher Description in Column L may reference different companies that own attachments on the CPS pole |
| **Column J**   | "Lowest Comm" height only counts non-CPS attachments                                            |
| **Column K**   | "Lowest CPS" height only counts CPS-owned electrical attachments                                |

---

## 5 Attachment Owner vs. Pole Owner

While Column C always shows "CPS" as the pole owner, attachments on the pole have their own owners:

```python
# Example snippet - attaching companies appear in Column L but don't affect Column C
def process_attachments(worksheet, pole_data, row_index):
    """Process all attachments on a pole"""
    
    # Column C remains "CPS" regardless of attachment owner
    worksheet.write(row_index, 2, POLE_OWNER_CONSTANT)
    
    # Attachment data in Column L shows various owners
    for i, attachment in enumerate(sorted_attachments(pole_data), start=1):
        # The attaching company appears in the description (Column L)
        worksheet.write(row_index + i, 11, attachment.description)  # Column L = index 11
        # e.g., "AT&T Fiber Optic", "Charter/Spectrum Fiber", "CPS Supply Fiber"
```

---

## 6 Foreign Pole Support (Future Extension)

If the tool needs to support non-CPS poles in the future, implement this extensibility:

```python
def get_pole_owner(pole_data, default_owner="CPS"):
    """
    Determine the pole owner from data or configuration.
    
    Args:
        pole_data: The pole data from SPIDAcalc/Katapult
        default_owner: The default owner if not specified
        
    Returns:
        String representing pole owner
    """
    # First check project configuration (allows override)
    if project_config and "pole_owner" in project_config:
        return project_config["pole_owner"]
    
    # Then check the pole data itself
    if pole_data.get("owner"):
        return pole_data["owner"]
    
    # If Katapult has pole_owner attribute
    if "attributes" in pole_data and "pole_owner" in pole_data["attributes"]:
        return pole_data["attributes"]["pole_owner"]
    
    # Default to CPS for backward compatibility
    return default_owner
```

---

## 7 Edge Case Handling

| Case                                             | Handling                                                     | Log key                      |
|--------------------------------------------------|--------------------------------------------------------------|------------------------------|
| Non-CPS poles incorrectly included in project    | Still mark as "CPS" but log as potential issue               | `NON_CPS_POLE_WARNING`       |
| Pole ownership conflicts between data sources    | Use constant "CPS" and log the conflict                      | `POLE_OWNER_CONFLICT`        |
| Foreign utility report adaptation                | Require configuration parameter to override constant          | `CUSTOM_POLE_OWNER`          |
| Multiple owners claimed in joint-use poles       | Use "CPS" and log multi-ownership for reference              | `JOINT_OWNERSHIP_DETECTED`   |

---

## 8 Unit Test Checklist

```python
from mrrgen.columns import POLE_OWNER_CONSTANT, write_pole_owner
from unittest.mock import MagicMock

def test_pole_owner_constant():
    """Test the pole owner constant value"""
    assert POLE_OWNER_CONSTANT == "CPS"

def test_write_pole_owner():
    """Test writing and merging pole owner cells"""
    # Create a mock worksheet
    mock_worksheet = MagicMock()
    
    # Call the function with different attachment counts
    write_pole_owner(mock_worksheet, row_index=5, attachment_count=0)
    write_pole_owner(mock_worksheet, row_index=10, attachment_count=3)
    
    # Verify the worksheet.write was called with correct parameters
    mock_worksheet.write.assert_any_call(5, 2, "CPS")
    mock_worksheet.write.assert_any_call(10, 2, "CPS")
    
    # Verify merge_range was called only when attachments exist
    assert mock_worksheet.merge_range.call_count == 1
    mock_worksheet.merge_range.assert_called_with(10, 2, 13, 2, "CPS")

def test_future_extensibility():
    """Test the extensibility for future non-CPS poles"""
    # This is a placeholder for future development
    # If implementing non-CPS pole support, add test cases here
    pass
```

---

## 9 Display Formatting

For Excel report formatting, Column C should:

- Use the same styling as the operation header row (blue background for headers)
- Be vertically centered for better readability
- Use the same font and size as other header cells

```python
def apply_column_c_formatting(worksheet, formats):
    """Apply formatting to Column C"""
    # Set column width appropriate for "CPS" (can be narrow)
    worksheet.set_column('C:C', 5)  # 5 characters wide
    
    # Apply general formatting rules for header cells
    # (These happen during the operation header row creation)
```

---

## 10 Revision History

| Date       | Version | Notes                                                                            |
|------------|---------|----------------------------------------------------------------------------------|
| 2025-05-18 | v0.1    | Look-up logic based on Katapult / SPIDAcalc.                                     |
| 2025-05-19 | v2.0    | **Simplified** – constant string "CPS" as per client directive.                  |
| 2025-05-20 | v2.1    | Added integration details, edge cases, and future extensibility documentation.    |
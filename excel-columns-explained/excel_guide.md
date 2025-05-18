# Utility Pole Attachment Tracking Template Structure Guide

## Header Structure by Column

### COLUMN A:
- **Row 1**: Value "Operation Number"
- **Row 2**: Merged with Row 1
- **Row 3**: Merged with Row 1

### COLUMN B:
- **Row 1**: Value "Attachment Action: (I) Installing (R) Removing (E) Existing"
- **Row 2**: Merged with Row 1
- **Row 3**: Merged with Row 1

### COLUMN C:
- **Row 1**: Value "Pole Owner"
- **Row 2**: Merged with Row 1
- **Row 3**: Merged with Row 1

### COLUMN D:
- **Row 1**: Value "Pole #"
- **Row 2**: Merged with Row 1
- **Row 3**: Merged with Row 1

### COLUMN E:
- **Row 1**: Value "Pole Structure"
- **Row 2**: Merged with Row 1
- **Row 3**: Merged with Row 1

### COLUMN F:
- **Row 1**: Value "Proposed Riser (Yes/No) & QTY"
- **Row 2**: Merged with Row 1
- **Row 3**: Merged with Row 1

### COLUMN G:
- **Row 1**: Value "Proposed Guy (Yes/No) &"
- **Row 2**: Merged with Row 1
- **Row 3**: Merged with Row 1

### COLUMN H:
- **Row 1**: Value "PLA (%) with proposed attachment"
- **Row 2**: Merged with Row 1
- **Row 3**: Merged with Row 1

### COLUMN I:
- **Row 1**: Value "Construction Grade of Analysis"
- **Row 2**: Merged with Row 1
- **Row 3**: Merged with Row 1

### COLUMN J:
- **Row 1**: Value "Existing Mid-Span Data" (merged with Column K)
- **Row 2**: Empty (merged header from row 1 extends down)
- **Row 3**: Value "Height Lowest Com"

### COLUMN K:
- **Row 1**: Merged with Column J
- **Row 2**: Empty (merged header from row 1 extends down)
- **Row 3**: Value "Height Lowest CPS Electrical"

### COLUMN L:
- **Row 1**: Empty
- **Row 2**: Empty
- **Row 3**: Value "Attacher Description"

### COLUMN M:
- **Row 1**: Value "Make Ready Data" (merged with Column N)
- **Row 2**: Value "Attachment Height" (merged with Column M and N)
- **Row 3**: Value "Existing"

### COLUMN N:
- **Row 1**: Merged with Column M
- **Row 2**: Merged with Column M
- **Row 3**: Value "Proposed"

### COLUMN O:
- **Row 1**: Value "Mid-Span"
- **Row 2**: Value "(same span as existing)"
- **Row 3**: Value "Proposed"

## Operation Row Structure

For each operation, create a new section with the following structure:

### Operation Data Row:
- **Column A**: Operation number (e.g., "1", "2")
- **Column B**: Attachment action (e.g., "(I) Installing")
- **Column C**: Pole owner (e.g., "CPS")
- **Column D**: Pole number (e.g., "PL410620", "PL398491")
- **Column E**: Pole structure (e.g., "40-4 Southern Pine", "45-2 Southern Pine")
- **Column F**: Proposed riser status (e.g., "NO", "YES (I)")
- **Column G**: Proposed guy status (e.g., "NO", "YES (I)")
- **Column H**: PLA percentage (e.g., "78.70%", "62.08%")
- **Column I**: Construction grade (e.g., "C")

Merge cells in columns A-I vertically to span all rows for this operation, including the From/To Pole rows and any reference sections that follow.

## Data Organization Logic

### Primary Pole Attachments:
1. For the first row after the operation data row:
   - Enter height measurements in columns J-K (e.g., "14'-10"", "23'10"" or "NA", "NA")
   - List the first attachment in columns L-O (typically "Neutral")

2. For each subsequent attachment:
   - Create a new row
   - Column L: Attacher description (e.g., "CPS Supply Fiber", "AT&T Com Drop")
   - Column M: Existing height (formatted as XX'-YY")
   - Column N: Proposed height (if applicable)
   - Column O: Mid-span measurement (if applicable)

3. Common attachment ordering pattern:
   - Neutral
   - Power supply/electrical attachments
   - Communications attachments organized by provider
   - Street lights and other utility attachments

### From Pole/To Pole Section:
1. After listing all primary attachments, add two rows with light blue background (#D6E5F3):
   - Row 1: Merge columns J-K with text "From Pole"
   - Row 2: Merge columns J-K with text "To Pole"
2. Under "From Pole", enter the current pole number (e.g., "PL410620")
3. Under "To Pole", enter the connecting pole number (e.g., "PL398491")

### Reference Pole Sections:
1. After the primary From/To Pole section, continue with the next operation or add reference sections if needed
2. For reference sections:
   - Create a row with merged cells across columns L-O with colored background:
     - Orange (#FFCC99) for "Ref (North East) to service pole"
     - Purple (#CCCCFF) for "Ref (South East) to PL401451"
   - List all attachments for this reference direction
   - Add light blue From/To Pole rows after reference attachments (e.g., rows 38-39)

## Specific Implementation Details

### Operation 1 (rows 8-11):
- Main data in row 8
- Five attachments in rows 4-9:
  - Neutral (29'-6")
  - CPS Supply Fiber (28'-0")
  - Charter Spectrum Fiber Optic (24'-7", 21'-1")
  - AT&T Fiber Optic Com (23'-7")
  - AT&T Telco Com (22'-4")
  - AT&T Com Drop (21'-5", 15'-10")
- From/To Pole section in rows 10-11:
  - From: PL410620
  - To: PL398491

### Operation 2 (rows 25-39):
- Main data in row 25 with "NA" values in columns J-K
- Primary attachments in rows 12-29
- Reference sections:
  - "Ref (North East) to service pole" (orange, row 30) with attachments in rows 31-33
  - "Ref (South East) to PL401451" (purple, row 34) with attachment in row 35
- Final From/To Pole section in rows 38-39:
  - From: PL398491
  - To: PL401451

## Special Notations and Formatting

1. **Height Format**: All measurements use feet and inches with apostrophe and quote marks (e.g., 29'-6")

2. **Special Indicators**:
   - "UG" in column O (row 19) indicates Underground
   - "(I)" in "YES (I)" indicates Installing
   - Multi-row attachments with the same description (e.g., multiple "AT&T Com Drop" entries) represent different specific instances

3. **Organization Logic**:
   - Attachments appear to be listed from highest to lowest on the pole
   - Reference directions use cardinal points (North East, South East)
   - Each operation concludes with a From/To Pole connection

This template effectively maps the physical utility pole network, documenting both vertical relationships (attachments on each pole) and horizontal relationships (connections between poles).
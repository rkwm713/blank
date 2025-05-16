## Make-Ready Report Generator Workflow (GitHub Documentation)

This document outlines the complete workflow and processing logic used to generate Make-Ready Excel reports from Katapult and optional SPIDAcalc JSON files.

---

### Input Sources

```
+------------------------------+      +--------------------------------------+
| Katapult JSON File          |----->| Flask Upload Interface (app.py)      |
| (required)                  |      +--------------------------------------+
+------------------------------+                       |
                                                     | Optional
+------------------------------+                       |
| SPIDAcalc JSON File         |-----------------------+
| (optional)                  |
+------------------------------+
```

---

### Data Processing Pipeline

#### 1. Load and Parse JSON Files

* Module: `processor.core.load_data`
* Validates JSON structure.
* Loads `katapult_data` (required) and `spidacalc_data` (optional).

#### 2. Initialize Report Data Structures

* Setup dictionaries and lists to hold extracted and transformed data.
* Prepare containers for the detailed Make Ready table and Summary table.

#### 3. Pole Matching and ID Normalization

* Normalizes and matches poles across both data sources.
* SPIDAcalc Pole ID extraction:

  * `spidacalc_data['leads'][n]['locations'][x]['label']`
* Katapult Pole ID options:

  * `PoleNumber`, `PL_number`, `DLOC_number`, `electric_pole_tag`
* Creates a canonical Pole ID and builds a map for fast lookup.
* Output: `processing_poles_list` (with matched or standalone Katapult nodes).

#### 4. Pole Processing Loop (Per Pole)

Each pole in `processing_poles_list` is processed as follows:

**4a. Extract Pole-Level Data**

* Pole ID, owner, height, class, species
* PLA %, construction grade, lat/long, etc.
* SPIDAcalc enhancements if available

**4b. Unit Conversion**

* Katapult uses inches (e.g., `_measured_height`)
* SPIDAcalc uses meters (e.g., `attachmentHeight.value`)

**4c. Consolidate Attachments and Status**

* Merge attachments from:

  * Katapult `photos[].wire[]`
  * SPIDAcalc Measured Design and Recommended Design
* Determine existing vs. proposed
* Assign status: New / Existing / Removed / Modified

**4d. Extract Per-Attachment Data**

* Attacher name & description
* Existing and proposed height (after conflict resolution)
* Determine "Attachment Action" based on status

**4e. Mid-Span Data Extraction**

* From Katapult `connections[].sections[].measured_height`
* Determine:

  * Lowest Comm height
  * Lowest CPS electrical height

**4f. From Pole / To Pole Lookup**

* Lookup based on `connection_id` linked to node

**4g. Action Summary**

* Generate label for report: `( I )`, `( R )`, `( E )`
* Additional movement info (Raise/Lower X ft)

**4h. Row Construction**

* Build a dict for each row in the Excel output
* Includes all necessary cell values

---

### Report Generation (Excel)

* Module: `processor.excel_generator`
* Tooling: `openpyxl` or `SheetJS` (JS version)
* Sheet Structure:

  * Header rows (1-4): Static, styled, frozen
  * One block per Operation (pole):

    * Row 1: Pole-level header
    * Rows 2-n: Attachment details
    * Row x: From/To pole reference
    * Row x+1: Separator

---

### Output

```
+-----------------------------------+
| Make-Ready Excel Report (.xlsx)   |
+-----------------------------------+
```

Styled, structured, and exported file ready for submission to CPS or similar utilities.

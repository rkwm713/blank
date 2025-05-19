# `spida_utils.py` - Utilities for SPIDAcalc Data Processing

## 1. Overview

`spida_utils.py` is a Python module containing a collection of utility functions specifically designed to extract and process information from SPIDAcalc JSON data. These functions are crucial for interpreting SPIDAcalc's data structure to find details about proposed equipment (risers, guys), construction grades, pole sequences, pole structure, loading analysis (PLA), and attachment lists relative to neutral wires.

Key functionalities include:
*   Checking for proposed risers and guys by comparing "Measured Design" and "Recommended Design" sections.
*   Extracting the overall construction grade for the analysis.
*   Checking textual notes for indications of proposed equipment.
*   Determining the authoritative sequence of poles from the SPIDAcalc file structure.
*   Filtering a list of poles to identify "primary operation" poles (those present in SPIDAcalc).
*   Classifying pole relationships (though this function seems less directly used by the main processor for its output structure).
*   Extracting and formatting pole structure (height-class, species).
*   Extracting a list of attachers (owners) from the neutral wire downwards for both measured and recommended designs.
*   Finding Wire End Point (WEP) information for specific wires.
*   Extracting Percent Load Analysis (PLA) percentage from the "Recommended Design".
*   Processing individual attachment data to determine description, existing height, proposed height, and midspan height based on a combination of SPIDAcalc and Katapult data (this function seems to have a broader scope than just SPIDAcalc).
*   Converting inches to a "feet'-inches\"" string format (duplicate of utility in other modules).
*   Generating a comprehensive report of attachments from neutral downwards.

## 2. Key Imports and Modules

*   **`re`**: Standard Python library for regular expression operations, used for pattern matching in notes.
*   **`utils`**: A local module.
    *   `normalize_pole_id`: Standardizes pole ID formats.

## 3. Core Functions and Logic

### 3.1. `check_proposed_riser_spida(spida_pole_data)`

*   **Purpose**: Determines if a new riser is proposed for a pole by comparing risers in the "Recommended Design" to those in the "Measured Design".
*   **Logic**:
    1.  Identifies "Measured Design" and "Recommended Design" sections.
    2.  Extracts all equipment of type 'RISER' from the recommended design, storing key details (owner, size, direction).
    3.  If no measured design exists, any riser in the recommended design is considered proposed.
    4.  Extracts risers from the measured design.
    5.  Compares each recommended riser to the measured risers. If a recommended riser (based on owner and size) is not found in the measured list, it's considered proposed.
*   **Returns**: `True` if a proposed riser is found, `False` otherwise.

### 3.2. `check_proposed_guy_spida(spida_pole_data)`

*   **Purpose**: Similar to `check_proposed_riser_spida`, but for guy wires.
*   **Logic**: Follows the same pattern: compares guys (based on owner, size, type) in the "Recommended Design" to those in the "Measured Design".
*   **Returns**: `True` if a proposed guy is found, `False` otherwise.

### 3.3. `get_construction_grade_spida(spida_data)`

*   **Purpose**: Extracts the overall construction grade (e.g., "B", "C") from the SPIDAcalc data.
*   **Logic**: Looks within `spida_data.clientData.analysisCases` for an entry containing a `constructionGrade` field.
*   **Returns**: The construction grade string, or `None`.

### 3.4. `check_proposed_equipment_in_notes(notes_text, equipment_type)`

*   **Purpose**: Scans a string of notes (`notes_text`) for keywords indicating proposed equipment ('riser' or 'guy').
*   **Logic**: Uses regular expressions to search for patterns like "add riser", "install guy", "new riser", "proposed guy", etc., within the lowercase version of `notes_text`.
*   **Returns**: `True` if a pattern is matched, `False` otherwise.

### 3.5. `get_pole_sequence_from_spidacalc(spida_data)`

*   **Purpose**: Determines the order of poles as they appear in the SPIDAcalc file. This is important for establishing a sequence for tasks like backspan identification.
*   **Logic**: Iterates through `spida_data.leads`, then `locations` within each lead. Appends the normalized pole ID (`label`) of each location to a list, ensuring uniqueness.
*   **Returns**: An ordered list of normalized pole IDs.

### 3.6. `filter_primary_operation_poles(pole_map)`

*   **Purpose**: Identifies which poles from a `pole_map` (a reconciliation map between Katapult and SPIDAcalc poles) are considered "primary operations."
*   **Logic**: A pole is considered primary if its entry in `pole_map` has a `spida_obj` (meaning it was found in the SPIDAcalc data). Updates the `is_primary` flag in the `pole_map`.
*   **Returns**: A list of normalized IDs for primary operation poles.

### 3.7. `classify_pole_relationships(primary_poles, katapult_data, pole_map)`

*   **Purpose**: (Seems less directly used for the final Excel output structure but provides relationship context). Classifies connections from primary poles as "reference_spans" or a "main_span".
*   **Logic**: Iterates through Katapult connections. If a connection originates from a `primary_pole`:
    *   If marked as `button_added == 'reference'` or `backspan == True`, it's added to `reference_spans`.
    *   Otherwise, if the `to_pole` is also primary and no main span is set yet, it's set as the `main_span`.
    *   If `to_pole` is not primary, it's treated as a reference span.
*   **Returns**: A dictionary mapping primary pole IDs to their classified relationships.

### 3.8. `get_pole_structure_spida(spida_pole_data)`

*   **Purpose**: Extracts and formats the pole structure string (e.g., "40-2 Southern Pine") from SPIDAcalc data for a single pole.
*   **Logic**:
    1.  Checks `spida_pole_data.poleTags` for `height`, `class`, and `species`.
    2.  Falls back to direct attributes on `spida_pole_data` if not in `poleTags`.
    3.  Attempts to parse `height` and `class` from `spida_pole_data.aliases` if still not found (e.g., from an alias like "40-2").
    4.  If height, class, and species are found, formats them as "height-class species". If only height and class, "height-class".
*   **Returns**: The formatted pole structure string, or `None` if parts are missing.

### 3.9. `get_attacher_list_by_neutral(spida_pole_data)`

*   **Purpose**: Extracts a detailed list of all attachments (wires, equipment, guys, assembly items) found at or below the lowest neutral wire's height for a given pole, separately for "Measured Design" and "Recommended Design".
*   **Logic**:
    1.  For both measured and recommended designs:
        *   Finds the lowest neutral wire height.
        *   If a neutral is found, iterates through all wires, equipment, guys, and assembly items in that design.
        *   Collects items whose attachment height (or bottom height for equipment) is less than or equal to the neutral height.
        *   Stores detailed information for each collected attachment (owner, type, subtype, height in meters and formatted, ID).
        *   Sorts the collected attachments by height (descending).
*   **Returns**: A dictionary `{'measured': [...], 'recommended': [...]}` containing lists of attachment objects.

### 3.10. `get_wep_info_for_wire(spida_pole_data, wire_id, design_label='Recommended Design')`

*   **Purpose**: Finds Wire End Point (WEP) information for a specific `wire_id` within a given design (`design_label`).
*   **Logic**:
    1.  Locates the target design.
    2.  Finds the `wire_obj` matching `wire_id`.
    3.  If the `wire_obj` has a `connectionId`, finds the WEP with that ID in the `structure.wireEndPoints` array.
    4.  Also iterates through all WEPs to find any that list `wire_id` in their `wires` array.
    5.  Enhances WEP results with `connectedWire` and `attachment_point` (vector coordinates) if available on the `wire_obj`.
*   **Returns**: A list of WEP objects.

### 3.11. `get_pla_percentage_spida(spida_pole_data, design_label="Recommended Design")`

*   **Purpose**: Extracts the Percent Load Analysis (PLA) value from the specified design (typically "Recommended Design") in SPIDAcalc data.
*   **Logic**:
    1.  Finds the target design.
    2.  Looks in `design.analysis[0].results`.
    3.  Searches for a result entry where `component == "Pole"` and `analysisType == "STRESS"`.
    4.  Extracts the `actual` value (PLA percentage), formats it to two decimal places with a "%" sign.
*   **Returns**: The PLA percentage string (e.g., "78.70%"), or "N/A".

### 3.12. `process_attachment_data(spida_attachment, katapult_attachment)`

*   **Purpose**: (Seems to be a high-level processing function, potentially intended for merging/finalizing attachment data for the report, but its direct call site isn't in `make_ready_processor.py`). Processes and combines attachment data from SPIDAcalc and Katapult sources to determine final description, existing height, proposed height, and midspan height for reporting.
*   **Logic**:
    *   **Description (Column L)**: Prioritizes SPIDAcalc owner ID, then SPIDAcalc description.
    *   **Existing Height (Column M)**: For non-new installations, uses SPIDAcalc `existingHeight_in` or Katapult `measured_height_in`. Blank for new installs.
    *   **Proposed Height (Column N)**: For new installs, uses SPIDAcalc `proposedHeight_in` or Katapult `measured_height_in`. For existing attachments, shows SPIDAcalc `proposedHeight_in` if different from existing, or calculates from Katapult `mr_move`. Blank if no change.
    *   **Midspan Height (Column O)**: Only if changed or new install. Uses Katapult data: `goes_underground` ("UG"), `midspanHeight_in`, or midspan from connection sections.
*   **Returns**: A dictionary with `description`, `existing_height`, `proposed_height`, `midspan_height`.

### 3.13. `inches_to_ft_in(height_in)`

*   **Purpose**: Converts inches to a "feet'-inches\"" string. (Duplicate of utility in other modules).

### 3.14. `generate_pole_attachment_report(spida_pole_data)`

*   **Purpose**: Generates a structured report of attachments from neutral downwards for a pole, using `get_attacher_list_by_neutral`.
*   **Logic**:
    1.  Calls `get_attacher_list_by_neutral`.
    2.  Formats the results for both measured and recommended designs, converting heights to ft-in.
    3.  For recommended design attachments, it attempts to determine if it's new or moved by comparing with the measured design.
*   **Returns**: A dictionary `{'pole_id': ..., 'measured': [...], 'recommended': [...]}`.

## 4. Overall Role

This module is the primary interface for dissecting and interpreting SPIDAcalc JSON files. It provides targeted functions to extract specific engineering details that are often more reliable or only available in SPIDAcalc compared to field-collected Katapult data. These utilities are essential for populating accurate engineering data in the final make-ready report.

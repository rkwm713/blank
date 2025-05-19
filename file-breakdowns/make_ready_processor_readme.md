# `make_ready_processor.py` - Core Logic for Make-Ready Report Generation

## 1. Overview

`make_ready_processor.py` is the central processing engine for the make-ready report generation application. It orchestrates the loading of data from Katapult and SPIDAcalc JSON files, processes pole attributes, attachments, and connections, resolves conflicts, identifies neutral wires and attachments below them, and compiles all this information into a structured list of pole data dictionaries suitable for output (e.g., to an Excel report).

Key functionalities include:
*   Loading and preprocessing Katapult and SPIDAcalc data using `data_loader`.
*   Iterating through Katapult nodes, identifying poles, and filtering based on a target list if provided.
*   Extracting and resolving pole attributes (e.g., pole number, structure, PLA) from both Katapult and SPIDAcalc data using `pole_attribute_processor`.
*   Processing and consolidating pole attachments from both sources using `attachment_processor`.
*   Processing pole connections, midspan data, reference spans, and backspans using `connection_processor`.
*   Identifying neutral wires and attachments below the highest neutral using `neutral_identification` and `reference_utils.deduplicate_attachments`.
*   Counting proposed risers and guys using `spida_utils` and Katapult data.
*   Calculating a proposed midspan value based on owner changes and new installations.
*   Applying midspan values to attachments according to specific business rules.
*   Building a final, ordered list of attachers for each pole, incorporating reference and backspan information.
*   Determining an overall "pole action" (Install, Remove, Existing) and "pole status" (No Change, Make-Ready Required, Issue Detected).
*   Ordering the final list of processed poles based on their sequence in the SPIDAcalc file.

## 2. Key Imports and Modules

This module imports a significant number of functions from other local modules, highlighting its role as an orchestrator:

*   **`json`**: Standard JSON library.
*   **`logging`**: Standard logging library.
*   **`trace_utils`**: `get_trace_by_id`, `extract_wire_metadata`.
*   **`utils`**: `normalize_pole_id`, `inches_to_feet_inches_str`, `extract_string_value`.
*   **`data_loader`**: `load_katapult_data`, `load_spidacalc_data`, `build_spida_lookups`, `filter_target_poles`.
*   **`pole_attribute_processor`**: `extract_pole_attributes_katapult`, `extract_spida_pole_attributes`, `resolve_pole_attribute_conflicts`, `extract_notes`.
*   **`attachment_processor`**: `process_katapult_attachments`, `process_spidacalc_attachments`, `consolidate_attachments`, `identify_owners_with_changes`.
*   **`connection_processor`**: `process_pole_connections`.
*   **`spida_utils`**: `check_proposed_riser_spida`, `check_proposed_guy_spida`, `check_proposed_equipment_in_notes`, `get_construction_grade_spida`, `get_pole_sequence_from_spidacalc`, `filter_primary_operation_poles`.
*   **`reference_utils`**: `deduplicate_attachments`.
*   **`neutral_identification` (as `ni`)**: Contains functions for identifying neutral wires and attachments below them.
*   **`debug_logging`**: For `get_processing_logger`.
*   **`wire_utils`**: `parse_feet_inches_str_to_inches`.

## 3. Main Function: `process_make_ready_report(...)`

*   **Purpose**: The primary entry point for processing data and generating the make-ready report information.
*   **Parameters**:
    *   `katapult_path` (str): Path to Katapult JSON.
    *   `spidacalc_path` (str, optional): Path to SPIDAcalc JSON.
    *   `target_poles` (list, optional): Specific pole numbers to process.
    *   `attachment_height_strategy` (str, optional): Strategy for resolving attachment height conflicts (e.g., 'PREFER_KATAPULT').
    *   `pole_attribute_strategy` (str, optional): Strategy for resolving pole attribute conflicts.
*   **Logic**:
    1.  **Setup**: Initializes logging using `debug_logging.get_processing_logger()`.
    2.  **Data Loading**: Loads Katapult and SPIDAcalc data using `data_loader` functions. Builds SPIDAcalc lookup tables.
    3.  **Target Pole Filtering**: Normalizes `target_poles` list if provided.
    4.  **Pole Sequence**: Gets the pole sequence from SPIDAcalc (used for backspan identification).
    5.  **Pole Processing Loop**: Iterates through each `node` in `katapult.get('nodes', {})`.
        *   **Node Validation**: Calls `is_pole_node()` to check if the current node is a pole. Skips if not.
        *   **Attribute Extraction**: Extracts Katapult pole attributes using `extract_pole_attributes_katapult`. Skips if no pole number is found.
        *   **Target Filtering**: Skips if `norm_pole_number` is not in `normalized_target_poles` (if targets are specified).
        *   **SPIDAcalc Data Integration**:
            *   Checks if `norm_pole_number` exists in `spida_lookup`.
            *   If yes, retrieves `spida_pole_data` and calls `resolve_pole_attribute_conflicts` to merge/prioritize attributes from Katapult and SPIDAcalc based on `pole_attribute_strategy`.
        *   **Attachment Processing**:
            *   Processes Katapult attachments (`process_katapult_attachments`).
            *   Processes SPIDAcalc attachments if `spida_pole_data` exists (`process_spidacalc_attachments`).
            *   Consolidates attachments from both sources (`consolidate_attachments`).
            *   Identifies owners with attachment height changes (`identify_owners_with_changes`).
        *   **Connection Processing**: Calls `process_pole_connections` to get data about connected spans, midspan info, reference spans, and backspans.
        *   **Midspan Heights**: Calls `extract_lowest_midspan_heights` to get detailed midspan clearance data for all connected spans.
        *   **Neutral Wire Processing**: Calls `process_neutral_wires` to identify neutral wires and attachments below the highest neutral.
        *   **Proposed Riser/Guy**: Calls `count_proposed_riser_guy` to determine counts and formats "YES (count)" or "NO".
        *   **Midspan Proposed Value**: Calls `calculate_midspan_proposed` to determine an overall proposed midspan height for the pole if there are new installations or moves.
        *   **Apply Midspan Values**: Calls `apply_midspan_values` to update the `midspan_proposed` field in `attachers_list` and `attachments_below_neutral` based on business rules.
        *   **Final Attachers List**: Calls `build_final_attachers_list` to create the ordered list of attachments, including headers for reference/backspans.
        *   **Pole Action & Status**: Determines `pole_action` using `determine_pole_action` and `pole_status` using `determine_pole_status`.
        *   **Operation Number**: Assigns an operation number based on the pole's order in `spida_pole_order`.
        *   **Compile Pole Data**: Aggregates all processed information into a `pole` dictionary.
        *   Appends the `pole` dictionary to the `poles` list.
        *   Includes comprehensive `try-except` block for error logging during individual pole processing.
    6.  **Primary Pole Identification**: Calls `filter_primary_operation_poles` to identify poles that are considered "primary" (likely those present in SPIDAcalc). Sets an `is_primary` flag on each pole in the `poles` list.
    7.  **Sorting**: If SPIDAcalc data was used, sorts the `poles` list based on `spida_pole_order`.
*   **Returns**: The sorted list of processed `pole` data dictionaries.

## 4. Helper Functions within `make_ready_processor.py`

### 4.1. `is_pole_node(node)`

*   **Purpose**: Checks if a Katapult node dictionary represents a utility pole.
*   **Logic**: Checks `node.get('button')` against a list of valid pole types (`'aerial'`, `'pole'`, `'aerial_path'`). Also checks `node.get('attributes', {}).get('node_type', {})` for a value of `'pole'`.

### 4.2. `process_neutral_wires(node, katapult, spida_pole_data, attachers_list)`

*   **Purpose**: Orchestrates the identification of neutral wires and attachments below them.
*   **Logic**:
    1.  Uses `neutral_identification.identify_neutrals_katapult` and `neutral_identification.identify_neutrals_spidacalc` to find neutral wires from both sources.
    2.  Combines these and uses `neutral_identification.get_highest_neutral` to find the highest one.
    3.  Uses `neutral_identification.identify_attachments_below_neutral` to filter the `attachers_list`.
    4.  Deduplicates the resulting `attachments_below_neutral` using `reference_utils.deduplicate_attachments`.
    5.  Ensures the identified `highest_neutral` (if any) is included in the `attachments_below_neutral` list, marked with `is_neutral: True`.
    *   Returns a dictionary containing all identified neutral wires, the highest neutral, and the filtered list of attachments below neutral.

### 4.3. `check_proposed_equipment(spida_pole_data, attributes)` (Seems to be an older/alternative version of `count_proposed_riser_guy`)

*   **Purpose**: Checks for proposed risers and guys, first in SPIDAcalc data, then in Katapult notes.
*   **Logic**: Uses `spida_utils.check_proposed_riser_spida` and `spida_utils.check_proposed_guy_spida`. If not found, then checks extracted notes (from `extract_notes`) using `spida_utils.check_proposed_equipment_in_notes`.
*   Returns a dictionary `{'proposed_riser': 'Yes'/'No', 'proposed_guy': 'Yes'/'No'}`.

### 4.4. `calculate_midspan_proposed(pole_connections, owners_with_changes, katapult, attachers_list)`

*   **Purpose**: Calculates a single "Midspan Proposed" value for the pole if there are new installations or if any owner has attachment changes.
*   **Logic**:
    1.  Returns 'N/A' if no new installations and no owners with changes.
    2.  Otherwise, iterates through `pole_connections`, then sections, photos, and wires.
    3.  Collects heights of wires belonging to `owners_with_changes` or wires that are `is_proposed`, or if there are any `has_new_installations`.
    4.  If any such midspan heights are collected, it returns the lowest one found, formatted as a feet-inches string. Otherwise, returns 'N/A'.

### 4.5. `apply_midspan_values(attachers_list, midspan_proposed)`

*   **Purpose**: Applies the calculated `midspan_proposed` value to individual attachments in `attachers_list` based on specific rules (updated 2025-05-22).
*   **Logic**:
    *   **Moved Attachments**: If an attachment moved (existing and proposed heights differ) and its `midspan_proposed` is 'N/A', it's updated with the pole-level `midspan_proposed` (if not 'N/A').
    *   **New Installs**: If an attachment is a new install (no existing height, has proposed height), its `midspan_proposed` is forced to 'N/A' unless it's already 'UG'.
    *   **Existing/Unchanged**: Other attachments are left as is.

### 4.6. `build_final_attachers_list(attachers_list, reference_spans, backspan)`

*   **Purpose**: Constructs the final, ordered list of items to be displayed in the "Attachers" section of the report for a pole. This includes primary attachments, and headers and attachments for backspans and reference spans.
*   **Logic**:
    1.  Determines the height of the highest neutral wire from `attachers_list`.
    2.  Sorts the primary `attachers_list` (items not marked as headers) by height in descending order.
    3.  Appends the backspan header (if `backspan` exists), marked with `type: 'backspan_header'` and `style_hint: 'light-blue'`.
    4.  Filters and appends backspan attachments: only includes neutrals or attachments below the determined neutral height.
    5.  Appends headers for each reference span in `reference_spans`, marked with `type: 'reference_header'`. Style hint is 'purple' if "south east" is in description, otherwise 'orange'.
    6.  Filters and appends reference span attachments similarly (neutrals or below neutral height). For fiber optic attachments in reference spans, if `midspan_proposed` is 'N/A', it's set to their `existing_height`.
    *   Returns the `final_list`.

### 4.7. `determine_pole_status(attributes, pole_attrs)`

*   **Purpose**: Determines the overall status of the pole (e.g., "No Change", "Make-Ready Required", "Issue Detected").
*   **Logic**:
    *   Defaults to "No Change".
    *   If Katapult make-ready notes (`kat_mr_notes` from `extract_notes`) exist and are non-empty, status becomes "Make-Ready Required".
    *   If `passing_capacity` from `pole_attrs` is below 85.0, status becomes "Issue Detected" (this might override "Make-Ready Required" if both conditions are met, depending on execution order if not mutually exclusive).

### 4.8. `determine_pole_action(attachers)`

*   **Purpose**: Determines the pole-level attachment action code for Column B of the Excel report.
*   **Logic**:
    *   Iterates through `attachers` (skipping headers).
    *   Flags `has_install` if any attachment has no existing height but a proposed height, or `is_proposed` flag is true.
    *   Flags `has_removal` if any attachment has an existing height but proposed height is 'N/A' (and not flagged as proposed).
    *   Returns:
        *   "(I)nstalling" if `has_install` is true.
        *   "(R)emoving" if no installs and `has_removal` is true.
        *   "(E)xisting" otherwise.

### 4.9. `count_proposed_riser_guy(node, katapult, spida_pole_data)`

*   **Purpose**: Counts proposed risers and guys from both Katapult attachments and SPIDAcalc recommended designs.
*   **Logic**:
    *   **Katapult**: Checks `node.get('attachments', {})` for `riser` and `guying` arrays. Increments counts if items have a `proposed: True` flag or "proposed" in their description. Also checks `wires` array for guy wires.
    *   **SPIDAcalc**: If `spida_pole_data` is available, checks the "recommended design" for equipment of type 'RISER' and items in the `guys` array with types containing 'GUY' or 'DOWN'. Also checks SPIDAcalc notes for "add guy" or "proposed guy".
    *   Returns `riser_count`, `guy_count`.

### 4.10. `extract_lowest_midspan_heights(node_id, katapult)`

*   **Purpose**: For a given pole (`node_id`), iterates through all its connections and, for each connected span (to `other_pole_number`), finds the lowest midspan height for communication wires and CPS electrical wires.
*   **Logic**:
    1.  Iterates through all `connections` in `katapult` data.
    2.  Identifies connections involving `node_id` and determines the `other_id` and `other_pole_number`.
    3.  For each such connection/span:
        *   Initializes `lowest_comm` and `lowest_cps` midspan heights to `None`.
        *   Checks if the connection `button` is 'underground_path' to set `is_ug`.
        *   Iterates through `sections`, `photos`, and `wire` items within the connection.
        *   **Height Selection (2025-05-22 Rule)**: Prioritizes `_midspan_height`, then `midspanHeight_in` (on wire or section), and as a last resort `_measured_height` if others are missing, assuming it might represent midspan for some photos.
        *   Extracts `owner`, `wire_type`, and `usage_group` (falling back to trace data if wire record fields are missing).
        *   Classifies wires:
            *   If owner is 'CPS ENERGY', checks for electrical types/usage group to update `lowest_cps`.
            *   Otherwise, treats as communication and updates `lowest_comm`.
        *   Stores results in a dictionary keyed by `other_pole_number`, with values like `{'comm': 'X'-Y"', 'cps': 'A'-B"', 'is_ug': False}` or `{'comm': 'UG', 'cps': 'UG', 'is_ug': True}`.
    *   Returns this dictionary of midspan heights per connected pole.

## 5. Overall Workflow

The `process_make_ready_report` function acts as a pipeline:
Data Ingestion -> Attribute Processing -> Attachment Processing -> Connection Processing -> Neutral Analysis -> Final Aggregation & Formatting -> Sorting.

This module is critical for transforming raw input data into the comprehensive, structured format required for the final make-ready report.

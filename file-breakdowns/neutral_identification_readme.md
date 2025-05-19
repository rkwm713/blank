# `neutral_identification.py` - Neutral Wire Identification and Processing

## 1. Overview

`neutral_identification.py` is a Python module dedicated to identifying neutral wires on utility poles using data from Katapult and SPIDAcalc sources. It also includes logic to find attachments located below the highest identified neutral wire and provides utilities for height normalization and visualization.

Key functionalities include:
*   Defining patterns (`NEUTRAL_PATTERNS`) to identify neutral wires from descriptions.
*   Normalizing height values to inches for consistent comparison.
*   Identifying neutral wires in Katapult data by examining wire metadata, trace data (cable type, usage group).
*   Identifying neutral wires in SPIDAcalc data by examining wire descriptions and usage groups in the "measured design".
*   Determining the highest neutral wire when multiple are found.
*   Identifying and listing all attachments (from a consolidated list) that are physically located below the highest neutral wire.
*   Providing a text-based visualization of pole attachments relative to the neutral line for debugging or review.

## 2. Key Imports and Modules

*   **`re`**: Standard Python library for regular expression operations, used for matching neutral patterns.
*   **`logging`**: Standard Python library for logging.
*   **`utils`**: A local module.
    *   `inches_to_feet_inches_str`: Converts inches to a "X'-Y\"" string format.
*   **`wire_utils`**: A local module.
    *   `process_wire_height`: Extracts and processes the height of a wire (likely converting to inches).
*   **`trace_utils`**: A local module.
    *   `get_trace_by_id`: Retrieves Katapult trace information.
    *   `extract_wire_metadata`: Extracts metadata for a Katapult wire.
*   **`make_ready_processor`**: (Imported locally within `visualize_pole_attachments`) For `process_wire_height` - this seems like a potential circular dependency or a utility that should ideally be in a lower-level module like `wire_utils` or `utils`.

## 3. Global Variables

*   **`NEUTRAL_PATTERNS`**: A list of regular expression strings used to identify neutral wires from their descriptions. Includes terms like 'neutral', 'cps neutral', 'primary neutral', and also broader terms like 'power line', 'primary', 'transmission' which might indicate wires at or above neutral height.

## 4. Core Functions and Logic

### 4.1. `normalize_height_to_inches(height_value, unit='inches')`

*   **Purpose**: Converts a given `height_value` to inches.
*   **Logic**:
    *   Handles `None` input.
    *   Converts `height_value` to float.
    *   If `unit` is 'meters', multiplies by 39.3701.
    *   If `unit` is 'inches' or unknown (with a warning), returns the float value.
    *   Returns `None` on conversion error.

### 4.2. `is_neutral_wire(wire_description)`

*   **Purpose**: Checks if a `wire_description` string matches any of the defined `NEUTRAL_PATTERNS`.
*   **Logic**: Converts description to lowercase and uses `re.search` for each pattern.

### 4.3. `identify_neutrals_katapult(pole_data, katapult)`

*   **Purpose**: Identifies neutral wires from Katapult data associated with a specific pole.
*   **Logic**:
    1.  Iterates through `photos` in `pole_data`, then `wire` items within `photofirst_data`.
    2.  For each wire, retrieves its `_trace` ID and fetches `trace` data using `get_trace_by_id`.
    3.  Extracts `owner` and `cable_type` using `extract_wire_metadata`.
    4.  Determines if it's a neutral by checking:
        *   If `cable_type` (from wire metadata) contains "neutral".
        *   If `cable_type` or `usageGroup` from the `trace` data contains "neutral".
    5.  If identified as neutral, processes its height using `process_wire_height`, formats a description (e.g., "[Owner] Neutral"), and appends a dictionary with these details (including `is_neutral: True`) to a list.
    *   Returns the list of identified Katapult neutral wires.

### 4.4. `identify_neutrals_spidacalc(pole_data, spida_pole_data)`

*   **Purpose**: Identifies neutral wires from SPIDAcalc data for a specific pole.
*   **Logic**:
    1.  Finds the "measured design" within `spida_pole_data`.
    2.  Iterates through `wires` in the measured design's structure.
    3.  Determines if it's a neutral by checking:
        *   If `clientItem.description` contains "neutral".
        *   If `usageGroup` contains "neutral".
    4.  If identified as neutral, extracts owner, converts height from meters to inches, formats a description, and appends a dictionary to a list.
    *   Returns the list of identified SPIDAcalc neutral wires.

### 4.5. `get_highest_neutral(neutral_wires)`

*   **Purpose**: Finds the neutral wire with the greatest `raw_existing_height_inches` from a list of neutral wire dictionaries.
*   **Logic**: Iterates through the list, keeping track of the neutral with the maximum height found so far.

### 4.6. `identify_attachments_below_neutral(pole_data, highest_neutral, katapult, spida_pole_data)`

*   **Purpose**: Filters a list of pole attachers to include only those whose height is less than the `highest_neutral`'s height. Also merges SPIDAcalc attachments that meet this criterion.
*   **Logic**:
    1.  If `highest_neutral` is not found, returns an empty list.
    2.  Gets the `neutral_height` (in inches) from `highest_neutral`.
    3.  Iterates through `pole_data.get('attachers', [])`:
        *   Skips non-dictionary items or reference headers.
        *   Extracts `raw_existing_height_inches` (or `raw_proposed_height_inches` as fallback).
        *   If the attachment's height is less than `neutral_height`, it's added to `attachments_below_neutral`.
    4.  If `spida_pole_data` is provided, calls `identify_spida_attachments_below_neutral` to get SPIDA-originated attachments below the neutral.
    5.  Merges these SPIDA attachments into `attachments_below_neutral`, avoiding duplicates based on description and similar height.
    6.  Sorts the final `attachments_below_neutral` list by height in descending order.
    *   Returns the sorted list.

### 4.7. `identify_spida_attachments_below_neutral(spida_pole_data, neutral_height)`

*   **Purpose**: Specifically identifies attachments from SPIDAcalc's "measured design" (both wires and equipment) that are below a given `neutral_height`.
*   **Logic**:
    1.  Finds the "measured design".
    2.  Iterates through `wires`:
        *   Skips wires already identified as neutral.
        *   Converts attachment height from meters to inches.
        *   If height is less than `neutral_height`, creates an attachment dictionary and adds it to a list.
    3.  Iterates through `equipments`:
        *   Converts attachment height from meters to inches.
        *   If height is less than `neutral_height`, creates an attachment dictionary and adds it.
    *   Returns the list of SPIDAcalc attachments below neutral.

### 4.8. `visualize_pole_attachments(pole_data, neutral_height=None)`

*   **Purpose**: Creates a simple text-based visualization of pole attachments, showing their heights and marking the neutral line. Intended for logging/debugging.
*   **Logic**:
    1.  Extracts attachments with valid heights from `pole_data.get('attachers', [])`.
    2.  Sorts these attachments by height (descending).
    3.  Prints each attachment's height (inches and feet-inches string) and description.
    4.  If `neutral_height` is provided, marks attachments at that height with "[NEUTRAL]" and draws a dashed line to represent the neutral level if crossed while iterating.

## 5. Dependencies on Other Project Files

*   **`utils.py`**: For `inches_to_feet_inches_str`.
*   **`wire_utils.py`**: For `process_wire_height`.
*   **`trace_utils.py`**: For `get_trace_by_id`, `extract_wire_metadata`.
*   **`make_ready_processor.py`**: (Locally imported in `visualize_pole_attachments`) for `process_wire_height`. This suggests `process_wire_height` might be better placed in `wire_utils` or `utils` to avoid this potential circular dependency if `make_ready_processor` also imports from `neutral_identification`.

This module is crucial for establishing the vertical position of the neutral wire, which is a key reference point for assessing clearances and make-ready work for other attachments on the pole.

# `reference_utils.py` - Utilities for Processing Reference Spans and Attachments

## 1. Overview

`reference_utils.py` is a Python module containing helper functions specifically designed to process "reference spans" and "backspans" in the context of utility pole data, primarily from Katapult. It handles the extraction of attachment details within these special spans, determines directional information, and formats data for reporting.

Key functionalities include:
*   Calculating the cardinal direction between two nodes based on their latitude and longitude.
*   Creating a standardized "attacher" dictionary from Katapult wire data and its associated trace information, including existing/proposed heights and midspan values. This function also handles "underground" (UG) status.
*   Processing a given Katapult connection as a reference span or backspan, which involves:
    *   Generating a descriptive header (e.g., "Ref (North East) to PL12345", "Backspan to PL67890").
    *   Determining appropriate styling hints (colors) for these headers.
    *   Extracting all wire attachments within the span from its sections and photos.
    *   Sorting these attachments by height.
*   A utility for deduplicating a list of attachments based on owner, type, and height (though its direct use in `process_reference_span` is commented out or conditional).

## 2. Key Imports and Modules

*   **`re`**: Standard Python library for regular expression operations (used in `get_attacher_from_wire` for parsing, though not directly visible in the provided snippet, it's a common import for such tasks).
*   **`utils`**: A local module.
    *   `inches_to_feet_inches_str`: Converts inches to a "X'-Y\"" string format.
    *   `normalize_pole_id`: Standardizes pole ID formats.
    *   `normalize_owner`: Standardizes owner names.
    *   `get_pole_number_from_node_id`: Retrieves a pole number given a Katapult node ID, with fallback.
*   **`wire_utils`**: A local module.
    *   `process_wire_height`: Extracts and processes the height of a wire.
*   **`trace_utils`**: A local module.
    *   `extract_wire_metadata`: Extracts metadata (owner, cable type, proposed status) for a wire.
    *   `get_trace_by_id`: Retrieves Katapult trace information.

## 3. Core Functions and Logic

### 3.1. `get_direction_between_nodes(node1, node2)`

*   **Purpose**: Calculates an 8-point cardinal direction (N, NE, E, SE, S, SW, W, NW) from `node1` to `node2` based on their latitude and longitude.
*   **Logic**: Compares the difference in latitude (`lat_diff`) and longitude (`lon_diff`).
    *   If `abs(lat_diff)` is much greater than `abs(lon_diff)`, it's North or South.
    *   If `abs(lon_diff)` is much greater than `abs(lat_diff)`, it's East or West.
    *   Otherwise, it's a diagonal direction (NE, NW, SE, SW).
*   **Returns**: A string like "North East", or "Unknown Direction" if coordinates are missing.

### 3.2. `get_attacher_from_wire(wire, trace, section_midspan_height_in=None)`

*   **Purpose**: Converts raw Katapult `wire` data and its `trace` data into a standardized "attacher" dictionary.
*   **Logic**:
    1.  Extracts `owner`, `cable_type`, and `is_proposed` status using `extract_wire_metadata`.
    2.  Formats an `att_desc` (e.g., "Owner CableType").
    3.  Processes `existing_height_inches` using `process_wire_height`.
    4.  Determines `proposed_height_str`: If `is_proposed`, `existing_height_str` becomes "N/A" and `proposed_height_str` is set to the wire's height; otherwise, `proposed_height_str` is "N/A".
    5.  **Midspan Value (`midspan_val_str`) and Underground (`goes_underground`) Logic**:
        *   Checks for "underground" indicators in trace `cable_type`, `att_desc`, or wire attributes (`_underground`).
        *   If `goes_underground` is true, `midspan_val_str` is set to "UG".
        *   Otherwise, it prioritizes `section_midspan_height_in` (if provided), then the wire's own `_midspan_height`. Converts valid height to feet-inches string.
    *   Returns a dictionary containing `description`, `existing_height`, `proposed_height`, `midspan_proposed`, raw heights in inches, `is_proposed`, and `goes_underground`.

### 3.3. `process_reference_span(katapult, current_node_id, other_node_id, conn_id, conn_data, is_backspan=False, previous_pole_id=None)`

*   **Purpose**: Processes a specific connection (`conn_data`) as either a reference span or a backspan.
*   **Logic**:
    1.  **Identify Other Pole**: Gets the pole tag/number (`other_pole_tag_display`) for `other_node_id` using `get_pole_number_from_node_id`. For backspans, it uses `previous_pole_id` if available. Includes robust fallback and normalization logic for the display tag.
    2.  **Determine Header Text & Style**:
        *   **Direction**: Attempts to extract direction from connection attributes (checking keys like `direction_tag`, `direction`). If not found and not a backspan, calculates it using `get_direction_between_nodes`. For backspans, direction is "Backspan".
        *   **Style Hint**: For backspans, `header_style_hint` is "light-blue". For reference spans, it attempts to extract a color hint (orange or purple) from connection attributes (keys like `color_tag`, `color`). Defaults to "orange".
        *   Constructs `header_text` (e.g., "Ref (North East) to PL12345").
    3.  Creates a `header` dictionary with `type: 'reference_header'`, the `description`, `style_hint`, and empty height fields.
    4.  **Extract Attachments**:
        *   Iterates through `sections` in `conn_data`, then `photos` within sections.
        *   For each `wire` in `photofirst_data`:
            *   Retrieves `trace` data.
            *   Calls `get_attacher_from_wire` to create a standardized attacher dictionary, passing any `section.get('midspanHeight_in')`.
            *   Appends the attacher to `span_attachments`.
    5.  **Sort Attachments**: Sorts `span_attachments` by height (descending), prioritizing existing height, then proposed height.
    *   **Returns**: A tuple `(header, sorted_span_attachments)`.

### 3.4. `deduplicate_attachments(attachments)`

*   **Purpose**: Removes duplicate attachments from a list based on a key composed of owner, attachment type (derived from description), and existing height.
*   **Logic**:
    1.  Iterates through the input `attachments`.
    2.  For each `attachment`, creates a unique `key` string.
    3.  Uses a dictionary (`unique_attachments`) to store only the first occurrence of each key.
    *   Returns `list(unique_attachments.values())`.
    *   **Note**: The usage of this function in `process_reference_span` is conditional or commented out, suggesting that for reference spans, listing all captured attachments (even if seemingly redundant by this specific key) might be the desired behavior.

## 4. Overall Role

This module is crucial for handling the specific data extraction and formatting requirements for reference spans and backspans, which often need to be presented distinctly in reports. It ensures that attachments within these spans are correctly identified, their heights and midspan values processed, and a clear descriptive header is generated for grouping them. The direction calculation and robust pole ID handling contribute to the clarity of the output.

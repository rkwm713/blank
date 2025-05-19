# `connection_processor.py` - Utility for Processing Pole Connection Data

## 1. Overview

`connection_processor.py` is a Python module focused on analyzing and extracting information about connections between utility poles, primarily using Katapult data. It identifies connections involving a specific pole, determines the lowest attachment heights for communication (COM) and CPS electrical wires within those connections, and processes special "reference spans" and "backspans."

Key functionalities include:
*   Iterating through all connections in the Katapult dataset to find those relevant to a given pole.
*   For each relevant connection, processing wire data from associated photos to find the lowest COM and CPS electrical wire heights.
*   Identifying and processing "reference spans" based on specific attributes in the connection data.
*   Identifying and processing "backspans" if a pole sequence is provided, linking the current pole to the previous pole in the sequence.
*   Calculating overall midspan data for the pole based on its connections.
*   Classifying wires as communication or CPS electrical based on owner and cable type.

## 2. Key Imports and Modules

*   **`logging`**: Standard Python library for logging.
*   **`utils`**: A local module presumably containing utility functions:
    *   `get_pole_number_from_node_id`: Retrieves a pole number given a Katapult node ID.
    *   `inches_to_feet_inches_str`: Converts a measurement in inches to a string representation in feet and inches.
    *   `normalize_pole_id`: (Used for backspan processing) Standardizes pole ID formats.
*   **`trace_utils`**: A local module for handling Katapult trace data:
    *   `get_trace_by_id`: Retrieves trace information using a trace ID.
    *   `extract_wire_metadata`: Extracts metadata (owner, cable type) for a wire.
*   **`wire_utils`**: A local module for wire-specific processing:
    *   `process_wire_height`: Extracts and processes the height of a wire.
*   **`reference_utils`**: A local module dedicated to processing reference spans:
    *   `process_reference_span`: Extracts detailed information for a reference span.

## 3. Core Functions and Logic

### 3.1. `process_pole_connections(node_id, pole_number, katapult, pole_sequence)`

*   **Purpose**: Main function to process all connections related to a specific pole (`node_id`, `pole_number`).
*   **Parameters**:
    *   `node_id`: The Katapult node ID of the current pole.
    *   `pole_number`: The human-readable pole number of the current pole.
    *   `katapult`: The full Katapult dataset (dictionary).
    *   `pole_sequence`: An ordered list of pole IDs, used to determine backspans.
*   **Logic**:
    1.  **Initialization**: Initializes `pole_connections` list, `processed_connections` set (to avoid reprocessing), and `reference_spans` list.
    2.  **Iterate Connections**: Loops through all `connections` in the `katapult` data.
        *   Skips connections not involving the current `node_id`.
        *   Determines the `other_node_id` and `other_pole_number` for the connected pole.
        *   Initializes `connection_lowest_com` and `connection_lowest_cps` heights to `None`.
        *   **Process Sections and Photos**:
            *   Iterates through `sections` within the connection, then `photos` within each section.
            *   Retrieves `photofirst_data` for each photo.
            *   Processes `wire` data (handling list or dict format).
            *   For each `wire`:
                *   Gets `trace_id` and fetches `trace` data using `get_trace_by_id`.
                *   Extracts `owner` and `cable_type` using `extract_wire_metadata`.
                *   Gets wire height `h` using `process_wire_height`.
                *   Classifies the wire as communication (`is_comm`) using `classify_wire_communication` and as CPS electrical (`is_cps_elec`) using `classify_wire_cps_electrical`.
                *   Updates `connection_lowest_com` and `connection_lowest_cps` if the current wire `h` is lower than the existing minimum for its type.
        *   Appends a summary of the connection (from_pole, to_pole, lowest_com, lowest_cps) to `pole_connections`.
        *   **Reference Span Check**: Calls `check_if_reference_span` for the current connection.
            *   If true, calls `process_reference_span` to get detailed data for this reference span and adds it to `reference_spans`. Marks the connection as processed.
    3.  **Backspan Processing**:
        *   If `pole_sequence` is provided:
            *   Finds the index of the current `pole_number` (normalized) in the sequence.
            *   If it's not the first pole, identifies the `previous_pole_id` from the sequence.
            *   Finds the `previous_pole_node_id` in the Katapult data.
            *   Searches for the connection between the current pole and the `previous_pole_node_id` (if not already processed).
            *   If found, calls `process_reference_span` with `is_backspan=True` and stores the result in `backspan`. Marks this connection as processed.
    4.  **Midspan Data Calculation**: Calls `calculate_midspan_data` using the collected `pole_connections` to determine overall midspan heights for the pole.
    *   **Returns**: A tuple containing `pole_connections` (list of basic connection summaries), `midspan_data` (dict), `reference_spans` (list of detailed reference span dicts), and `backspan` (dict or None).

### 3.2. `classify_wire_communication(owner, cable_type, trace)`

*   **Purpose**: Determines if a wire is a communication wire.
*   **Logic**:
    *   If the `owner` is not CPS (case-insensitive "cps"):
        *   Checks the `cable_type` from the `trace` data for common communication terms (e.g., "com", "fiber", "telco", "cable", "catv").
        *   Checks the `owner` name for known communication company names (e.g., "att", "spectrum", "comcast").
    *   Returns `True` if any communication indicator is found, otherwise `False`.

### 3.3. `classify_wire_cps_electrical(owner, cable_type, trace)`

*   **Purpose**: Determines if a wire is a CPS (City Public Service) electrical wire.
*   **Logic**:
    *   If the `owner` is CPS (case-insensitive "cps"):
        *   Checks the `cable_type` from the `trace` data for common electrical terms (e.g., "neutral", "secondary", "primary", "electric").
        *   If `cable_type` is empty but the owner is CPS, it's assumed to be electrical.
        *   If `trace` data is unavailable but the owner is CPS, it's also assumed electrical.
    *   Returns `True` if classified as CPS electrical, otherwise `False`.

### 3.4. `check_if_reference_span(conn_id, conn_data)`

*   **Purpose**: Determines if a given connection is a "reference span" based on its attributes.
*   **Logic**: Checks for several indicators within the `conn_data['attributes']`:
    1.  `connection_type.button_added == 'reference'`
    2.  `button_added == 'reference'`
    3.  `reference` attribute is `True` (boolean or string "true").
    4.  Various span type attributes (`span_type`, `spanType`, `connection_classification`, `span_classification`) contain the word "reference" (case-insensitive). This handles cases where the value might be a direct string or a dictionary with the type as a value.
    *   Returns `True` if any condition is met, otherwise `False`.

### 3.5. `calculate_midspan_data(pole_connections, pole_number)`

*   **Purpose**: Calculates a summary of midspan data for the pole, focusing on the "primary" connection.
*   **Logic**:
    1.  Initializes `midspan_data` with default 'N/A' values.
    2.  If `pole_connections` is empty, returns the default data.
    3.  **Find Primary Connection**:
        *   Iterates through `pole_connections` to find the first connection that has a valid `to_pole` (not 'N/A'). This is considered the primary connection.
        *   If no such connection is found, defaults to the very first connection in the list.
    4.  If a `primary_connection` is identified:
        *   Populates `midspan_data` with `lowest_com` and `lowest_cps` from this connection (converted to feet-inches strings), and the `from_pole` and `to_pole` numbers.
    *   Returns the populated `midspan_data` dictionary.

## 4. Dependencies on Other Project Files

*   **`utils.py`**: Provides `get_pole_number_from_node_id`, `inches_to_feet_inches_str`, `normalize_pole_id`.
*   **`trace_utils.py`**: Provides `get_trace_by_id`, `extract_wire_metadata`.
*   **`wire_utils.py`**: Provides `process_wire_height`.
*   **`reference_utils.py`**: Provides `process_reference_span`.

This module is essential for understanding the network topology around a pole and for gathering height clearance data from connected spans, which is critical for make-ready engineering analysis.

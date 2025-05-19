# `excel_generator.py` - Excel Report Generation for Make Ready Data

## 1. Overview

`excel_generator.py` is a Python module responsible for creating a formatted Excel (.xlsx) "Make Ready Report" from processed pole data. It uses the `openpyxl` library to construct the spreadsheet, apply styling (fonts, fills, borders, alignment), set column widths, and populate the data in a structured layout that matches a specific report format.

Key functionalities include:
*   Defining and applying various cell styles (header fonts, fill colors, borders).
*   Setting specific column widths for readability.
*   Creating a complex multi-row header structure with merged cells.
*   Populating pole-level data (operation number, pole owner, pole number, structure, etc.).
*   Populating mid-span data (lowest communication and CPS electrical heights).
*   Listing individual attachers with their existing and proposed heights, and mid-span proposed values.
*   Handling special "Reference Span" and "Backspan" groups with distinct header styling.
*   Iterating through processed pole data and organizing it into the defined Excel structure.

The module includes helper functions for categorizing wires, finding lowest heights, processing connection heights to extract wire data, determining proposed heights (though simplified in the provided snippet), and identifying reference subgroups.

## 2. Key Imports and Modules

*   **`openpyxl`**: The primary library used for creating and manipulating Excel files.
    *   `Workbook`: For creating a new Excel workbook.
    *   `styles (Font, Alignment, PatternFill, Border, Side)`: For defining cell formatting.
    *   `utils (get_column_letter)`: Utility for converting column numbers to letters (though not explicitly used in the final `create_make_ready_excel` function, it's a common `openpyxl` utility).
*   **`trace_utils`**: A local module.
    *   `get_trace_by_id`: Used in `process_connection_heights` to get trace data for wire descriptions.
*   **`utils`**: A local module.
    *   `inches_to_feet_inches_str`: Converts inches to a "X'Y\"" string format.
    *   `extract_string_value`: Safely extracts a string value, handling cases where the input might be a dictionary or other non-string type.
*   **`wire_utils`**: A local module.
    *   `parse_feet_inches_str_to_inches` (aliased as `feet_inches_str_to_inches`): Converts a "X'Y\"" string format back to inches (though not directly used in the `create_make_ready_excel` function, it's imported).

## 3. Helper Functions

### 3.1. `categorize_wire(wire_type)`

*   **Purpose**: Categorizes a wire as 'COMM' (communication), 'CPS' (CPS Energy electrical), or 'OTHER' based on its description string.
*   **Logic**: Converts `wire_type` to lowercase and checks for keywords associated with COMM (fiber, comm, telco, spectrum, at&t) or CPS (cps, neutral, primary, secondary).

### 3.2. `find_lowest_height(wires)`

*   **Purpose**: Finds the wire entry with the numerically lowest height from a list of wire data tuples/lists.
*   **Logic**: Assumes `wires` is a list where each item contains height data, and compares the `['height']` value.

### 3.3. `find_proposed_for_category(proposed_heights, category)`

*   **Purpose**: Finds the lowest proposed height for a specific wire `category` (COMM, CPS, OTHER) from a dictionary of proposed heights.
*   **Logic**: Iterates through `proposed_heights`, categorizes each wire type using `categorize_wire`, and finds the minimum height for the target category.

### 3.4. `process_connection_heights(pole_data)`

*   **Purpose**: Extracts the lowest measured height for each unique wire type within each connection associated with a pole.
*   **Logic**:
    *   Iterates through `connections` in `pole_data`.
    *   For each connection, iterates through its `sections`, then `photos`, then `wire` data within `photofirst_data`.
    *   For each wire, gets its trace data to form a `wire_description` (owner + cable type).
    *   Gets the `_measured_height`.
    *   Stores the lowest `height_value` found for each `wire_description` within that connection.
    *   Returns a dictionary mapping `connection_id` to a dictionary of `wire_description` to height data.

### 3.5. `determine_proposed_heights(pole_data, connection_heights)`

*   **Purpose**: (Simplified/Placeholder) Intended to calculate proposed heights for wires based on move indicators or proposed flags.
*   **Logic**:
    *   Iterates through `connection_heights`.
    *   For each wire, checks for placeholder fields like `effective_move`, `mr_move`, or a `proposed` flag in trace data.
    *   If a move is indicated and a `_proposed_height` exists, it's used.
    *   Returns a dictionary mapping `connection_id` to `wire_type` to proposed height data.
    *   **Note**: The comment indicates this is a simplified check and real implementation would be more complex.

### 3.6. `identify_ref_subgroups(pole_data)`

*   **Purpose**: Identifies "Reference Span" or "Backspan" subgroups that require special formatting in the Excel report.
*   **Logic**:
    1.  **Primary Method**: Checks `pole_data.get('reference_spans', [])` (assumed to be pre-processed). If found, extracts header information (description, style_hint, to_pole) and attachments for each reference span.
    2.  **Fallback Method**: If `reference_spans` is empty, it iterates through `pole_data.get('connections', [])`.
        *   It attempts to identify reference spans by looking for keywords like 'service', 'red', or cardinal directions ('north', 'south', 'east', 'west') in the `to_pole` description of a connection.
        *   Constructs a label (e.g., "Ref (North East) to [to_pole_description]") and assigns a default style.
    *   Returns a list of dictionaries, each representing a reference group with its label, style hint, and attachments.

## 4. Main Function: `create_make_ready_excel(processed_pole_data, output_filepath)`

*   **Purpose**: Generates the complete Excel report.
*   **Logic**:
    1.  **Workbook Setup**: Creates a new `Workbook` and gets the active `worksheet`. Sets the title to "Make Ready Report".
    2.  **Styles Definition**: Defines various `Font`, `PatternFill`, `Alignment`, and `Border` styles for headers, data cells, and special sections (e.g., light blue, orange, purple fills).
    3.  **Column Widths**: Sets predefined widths for columns A through O.
    4.  **Header Creation (Rows 1-3)**:
        *   **Row 1**: Creates merged headers "Existing Mid-Span Data" (J-K) and "Make Ready Data" (L-O).
        *   **Rows 1-3 (Main Headers A-I)**: Sets values for main headers like "Operation Number", "Pole Owner", etc. These cells are merged vertically across rows 1-3.
        *   **Row 2 (Detail Headers J-O)**: Sets values for "Height Lowest Com", "Height Lowest CPS Electrical", "Attacher Description", "Attachment Height" (merged M-N), and "Mid-Span Proposed". These are merged vertically across rows 2-3 where appropriate (J, K, L).
        *   **Row 3 (Sub-headers for M-O)**: Sets "Existing" (M), "Proposed" (N) under "Attachment Height", and "Proposed" (O) under "Mid-Span Proposed".
        *   Applies header fonts, fills, alignment, and borders to all header cells.
    5.  **Freeze Panes**: Freezes panes at cell A4 to keep headers visible during scrolling.
    6.  **Data Population (Starting from `current_row = 4`)**:
        *   Iterates through `processed_pole_data`, focusing only on `pole.get('is_primary', False)` poles in the first pass.
        *   **Pole-Level Data (Columns A-I)**:
            *   Calculates the total number of rows needed for the current pole (attachers + midspan info + From/To headers + REF groups).
            *   Merges cells A-I vertically for the calculated `total_rows`.
            *   Fills in data like operation number (sequential for primary poles), pole action, owner ("CPS"), pole number, structure, proposed riser/guy, PLA, and construction grade. Uses `extract_string_value` for safety.
        *   **Midspan Data (Columns J-K)**:
            *   Retrieves `midspan_heights` from `pole_data`.
            *   Populates "Height Lowest Com" and "Height Lowest CPS Electrical" based on the `from_pole` and `to_pole` context. These cells are merged vertically down to the row before the "From/To Pole" headers.
        *   **Attachers Data (Columns L-O)**:
            *   Iterates through `pole.get('attachers', [])`.
            *   If an attacher item has `type` as 'reference_header' or 'backspan_header', it's formatted as a merged header row (L-O) with appropriate fill color (orange, purple, light-blue based on `style_hint` or label content).
            *   Otherwise, it's regular attacher data: "Attacher Description" (L), "Existing Height" (M), "Proposed Height" (N), "Mid-Span Proposed" (O).
            *   Applies borders and alignment.
        *   **From/To Pole Section (Columns J-K, L-O for midspan proposed)**:
            *   After all attachers for the current pole, adds a header row "From Pole" (J) and "To Pole" (K) with light blue fill.
            *   Adds a data row below it with the actual `from_pole` and `to_pole` values.
            *   The `midspan_proposed` value for the overall span is placed in column O of this data row.
        *   **REF Groups (Columns L-O)**:
            *   Iterates through `ref_groups` identified by `identify_ref_subgroups`.
            *   For each group, creates a header row (merged L-O) with the group's label and appropriate fill color.
            *   Lists the attachments within that REF group, populating description, existing height, proposed height, and midspan proposed. If pre-processed `attachments` are in `ref_group`, those are used; otherwise, it falls back to using `connection_heights` and `proposed_heights`.
        *   Adds a blank row with borders to separate poles.
        *   Increments `operation_number` for each primary pole.
    7.  **Save Workbook**: Saves the populated workbook to `output_filepath`.

## 5. Dependencies on Other Project Files

*   **`trace_utils.py`**: For `get_trace_by_id`.
*   **`utils.py`**: For `inches_to_feet_inches_str`, `extract_string_value`.
*   **`wire_utils.py`**: For `parse_feet_inches_str_to_inches` (though not directly used in the main generation logic).

This module is the final step in generating the user-facing Excel report, transforming complex processed data into a human-readable and specifically formatted spreadsheet.

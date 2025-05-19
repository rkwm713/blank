# `wire_utils.py` - Utilities for Wire Data Processing

## 1. Overview

`wire_utils.py` is a Python module containing utility functions specifically for processing data related to wires, particularly their heights, as found in Katapult and potentially SPIDAcalc JSON structures. It aims to robustly extract and convert height information into a consistent unit (inches).

Key functionalities include:
*   Parsing height strings in "feet'-inches\"" format (e.g., "3'-6\"") into a numerical value in inches.
*   Extracting wire height from a Katapult `wire` data object by checking multiple common keys where height information might be stored. This includes handling direct height values, nested height values (e.g., within `position` or `attachmentHeight` objects), and performing unit conversions if units like meters or feet are detected or implied by the key or value.

## 2. Key Imports and Modules

*   **`re`**: Standard Python library for regular expression operations, used in `parse_feet_inches_str_to_inches`.
*   **`utils`**: A local module.
    *   `extract_string_value`: Safely extracts a string value from potentially nested or non-string data, used here for logging wire identifiers.

## 3. Core Functions and Logic

### 3.1. `parse_feet_inches_str_to_inches(height_str)`

*   **Purpose**: Converts a string representing a height in feet and inches (e.g., "3'-6\"", "3' 6\"") into a total numerical value in inches.
*   **Logic**:
    1.  If `height_str` is not a string, returns `None`.
    2.  Uses `re.match(r"(\d+)'(?:-|\s*)?(\d+)\"?", height_str)` to parse feet and inches. The regex allows for an optional hyphen or space between feet and inches.
    3.  If a match is found, converts the captured feet and inches parts to integers and calculates total inches: `(feet * 12) + inches_part`.
    4.  If no regex match, it attempts to parse `height_str` directly as a float (in case the input is already in inches as a number).
    5.  Returns the calculated inches (float), or `None` if all parsing attempts fail.

### 3.2. `process_wire_height(wire)`

*   **Purpose**: Extracts a height value (in inches) from a Katapult `wire` dictionary by checking a predefined list of possible keys and handling potential unit conversions.
*   **Logic**:
    1.  If `wire` is `None` or not a dictionary, returns `None`.
    2.  Defines `height_keys_to_check` which includes common keys like `'_measured_height'`, `'measured_height'`, `'height'`, `'attachmentHeight'`, `'z'`, `'measuredHeight_in'`, etc.
    3.  Iterates through these keys:
        *   **Special Handling for `z`, `z_coord`**: If the key is 'z' or 'z_coord', it looks for it within a nested `wire.get('position')` dictionary.
        *   **Special Handling for `value` (SPIDAcalc `attachmentHeight` pattern)**: If the key is 'value' and the `wire` dictionary contains an `attachmentHeight` key (which is itself a dictionary like `{"value": X, "unit": "m"}`), it extracts the `value` and `unit`.
            *   If `unit` is 'm' or 'meters', converts the value to inches (value * 39.3701).
            *   If `unit` is 'ft' or 'feet', converts to inches (value * 12).
            *   Otherwise (or if unit is 'in', 'inches'), assumes the value is already in inches.
            *   Returns the calculated/extracted height in inches.
        *   **General Key Check**: For other keys, retrieves `raw_height_val = wire.get(key)`.
        *   If `raw_height_val` is found:
            *   If it's a string, attempts to parse it using `parse_feet_inches_str_to_inches`. If successful, returns the parsed inches.
            *   Otherwise, attempts to convert `raw_height_val` directly to a float.
                *   **Heuristic Unit Conversion**:
                    *   If the key was 'z', 'z_coord', or 'elevation' and the float value is small (e.g., < 15), it assumes the value was in meters and converts to inches.
                    *   If the key was 'height' and the value is in a certain range (15 <= value < 50), it's considered ambiguous but currently assumed to be inches. (The comment notes this needs careful consideration).
                *   Otherwise, assumes the float value is already in inches.
                *   Returns the height in inches.
            *   If parsing/conversion fails for the current key, it logs an error and continues to the next key.
    4.  If no valid height is found after checking all keys, logs a debug message and returns `None`.
*   **Returns**: The extracted height in inches as a float, or `None`.

## 4. Overall Role

This module centralizes the logic for interpreting and converting wire height data, which can be represented in various ways across different parts of the Katapult (and sometimes SPIDAcalc-like nested) JSON. By providing a single function (`process_wire_height`) that tries multiple extraction strategies, it makes the height processing more robust and easier to manage in other modules that deal with wire attachments. The `parse_feet_inches_str_to_inches` function is a necessary utility for handling common string formats for height.

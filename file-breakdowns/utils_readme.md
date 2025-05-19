# `utils.py` - General Utility Functions

## 1. Overview

`utils.py` is a Python module that provides a collection of general-purpose utility functions used across the make-ready report processing application. These functions handle common tasks such as unit conversions, string normalization, and robust data extraction from potentially complex or inconsistent data structures (particularly from Katapult JSON).

Key functionalities include:
*   Converting measurements from inches to a "feet'-inches\"" string format.
*   Converting measurements from meters to a "feet'-inches\"" string format (by first converting meters to inches).
*   Normalizing pole IDs, typically by extracting the trailing numeric portion.
*   Normalizing owner names to a consistent format (e.g., "ATT" and "AT AND T" to "AT&T").
*   Robustly extracting a pole number from a Katapult node's attributes by checking multiple common keys and handling nested dictionary structures.
*   Safely extracting a string value from various input types (string, dictionary, None), with a preference order for keys within dictionaries, designed to handle Katapult's attribute patterns.

## 2. Key Imports and Modules

*   **`re`**: Standard Python library for regular expression operations, used in `normalize_pole_id`.
*   **`math`**: Standard Python library for mathematical functions (though not explicitly used in the provided snippet, it's a common import for utility modules that might perform more complex calculations).

## 3. Core Functions and Logic

### 3.1. `inches_to_feet_inches_str(inches)`

*   **Purpose**: Converts a numerical value in inches to a formatted string representation (e.g., `42` -> `"3'-6\""`).
*   **Logic**:
    1.  Handles `None` input by returning 'N/A'.
    2.  Converts input `inches` to a float.
    3.  Calculates `feet` (integer part of `inches / 12`).
    4.  Calculates `rem_inches` (remainder of `inches % 12`, rounded to the nearest integer).
    5.  Handles a special case where `rem_inches` rounds up to 12: increments `feet` by 1 and sets `rem_inches` to 0.
    6.  Returns the formatted string (e.g., `f"{feet}'-{rem_inches}\""`).
    7.  Returns 'N/A' if any exception occurs during conversion.

### 3.2. `meters_to_feet_inches_str(meters)`

*   **Purpose**: Converts a numerical value in meters to a "feet'-inches\"" string format.
*   **Logic**:
    1.  Handles `None` input by returning 'N/A'.
    2.  Converts input `meters` to float and then to inches by multiplying by 39.3701.
    3.  Calls `inches_to_feet_inches_str()` with the converted inch value.
    4.  Returns 'N/A' if any exception occurs.

### 3.3. `normalize_pole_id(pole_id)`

*   **Purpose**: Extracts the numeric portion from a pole ID string, typically assuming the numbers are at the end.
*   **Logic**:
    1.  If `pole_id` is `None` or empty, returns `None`.
    2.  Uses `re.search(r'(\d+)$', str(pole_id))` to find one or more digits at the end of the string.
    3.  If a match is found, returns the captured numeric group (group 1). Otherwise, returns `None`.

### 3.4. `normalize_owner(owner)`

*   **Purpose**: Standardizes owner names for consistent comparison and display.
*   **Logic**:
    1.  If `owner` is `None` or empty, returns `None`.
    2.  Trims whitespace, converts to uppercase, and replaces '&' with 'AND'.
    3.  Specifically maps variations of "AT&T" (e.g., "ATT", "AT AND T") to "AT&T".
    4.  Maps variations of "CPS ENERGY" (e.g., "CPS") to "CPS ENERGY".
    5.  Returns the normalized owner string.

### 3.5. `get_pole_number_from_node_id(katapult, node_id, fallback_id=None)`

*   **Purpose**: Retrieves a pole number associated with a Katapult `node_id`, checking multiple common attribute keys and handling nested structures. Provides fallback options if a standard pole number isn't found.
*   **Logic**:
    1.  If `node_id` is invalid, returns `fallback_id` or "Unknown".
    2.  Retrieves the `node` data and its `attributes` from the `katapult` dataset.
    3.  Iterates through an ordered list of preferred attribute keys for pole numbers (e.g., 'PoleNumber', 'pl_number', 'dloc_number', and their capitalized versions, 'pole_tag', 'electric_pole_tag').
    4.  For each key, if the attribute exists:
        *   If it's a dictionary, attempts to extract the value from common sub-keys like '-Imported', 'assessment', 'button_added', 'tagtext'.
        *   If it's a direct string, uses that.
        *   Returns the first valid pole number found.
    5.  **Fallback for Reference/Service Poles**: If no standard pole number is found, checks `attributes.node_type`. If it indicates a 'reference', 'service', or 'anchor' node:
        *   Tries to find a descriptive name from attributes like 'name', 'label', 'scid', 'reference_name', 'description'.
        *   Formats a descriptive ID like "Reference-[name]" or "Service-[node_id_prefix]".
    6.  **Last Resort Fallback**: If still no number, returns `fallback_id` or a generic "Node-[node_id_prefix]".

### 3.6. `extract_string_value(value, default='N/A')`

*   **Purpose**: Safely extracts a string representation from a `value` that could be `None`, a simple type, or a (potentially nested) dictionary, common in Katapult attribute data.
*   **Logic**:
    1.  If `value` is `None`, returns `default`.
    2.  If `value` is a dictionary:
        *   Iterates through a list of `preferred_keys` (e.g., '-Imported', 'assessment', 'tagtext', 'value', 'name', 'id').
        *   If a preferred key is found:
            *   If its value (`val`) is another dictionary, it attempts to get a more specific sub-value (from 'tagtext', 'value', etc.) or takes the first value of the nested dict.
            *   If `val` is not a dictionary and not `None`, converts it to a string.
            *   Returns the first valid string found this way.
        *   If no preferred keys yield a value, it iterates through all values of the dictionary. If a non-dictionary, non-`None` value is found, it's returned as a string. If a dictionary value is found, it attempts to get a sub-value or its first value.
        *   If all attempts fail (e.g., empty dictionary or all values resolve to `None`), returns `default`.
    3.  If `value` is not a dictionary and not `None`, converts it to `str(value)`.
*   **Returns**: The extracted string or the `default`.

## 4. Overall Role

This module provides foundational helper functions that promote code reuse and robustness when dealing with the varied and sometimes unpredictable structures of input data, especially from Katapult. Normalization functions ensure consistency, while extraction utilities prevent errors when accessing deeply nested or optional data fields.

# `excel_utils.py` - Utility Functions for Excel Data Handling

## 1. Overview

`excel_utils.py` is a Python module containing various helper functions primarily designed to support data extraction, conversion, and categorization, likely in the context of preparing data for or processing data from Excel spreadsheets related to utility pole information.

Key functionalities include:
*   Safely extracting string values from potentially nested dictionary structures, common in Katapult data.
*   Converting measurements in inches to a "feet'-inches\"" string format.
*   Categorizing wire types (e.g., "COMM", "CPS", "OTHER") based on keywords in their descriptions.
*   Converting a 1-based column index to its corresponding Excel column letter (e.g., 1 to 'A').
*   Parsing height strings in "feet'-inches\"" format back into total inches.

Notably, some functions like `inches_to_feet_inches_str` and `categorize_wire` appear to duplicate functionality found in other modules (like `utils.py` or `excel_generator.py`), possibly for independence or to avoid circular dependencies.

## 2. Key Imports and Modules

*   **`re`**: (Imported locally within `parse_feet_inches`) Standard Python library for regular expression operations, used here for parsing height strings.

## 3. Core Functions and Logic

### 3.1. `extract_string_value(value, default='N/A')`

*   **Purpose**: Safely extracts a string representation from an input `value` that might be `None`, a simple type, or a nested dictionary (common in Katapult attribute structures).
*   **Logic**:
    1.  If `value` is `None`, returns the `default` string ('N/A').
    2.  If `value` is a dictionary:
        *   It iterates through a predefined list of common Katapult attribute keys (`'-Imported'`, `'assessment'`, `'button_added'`, `'tagtext'`).
        *   If one of these keys is found, it attempts to retrieve its value.
        *   If the nested value is itself a dictionary and contains `'tagtext'`, that `'tagtext'` value is returned.
        *   Otherwise, the string representation of the `nested_value` is returned.
        *   If none of the specific keys are found but the dictionary is not empty, it returns the string representation of the first value in the dictionary.
    3.  If `value` is not `None` and not a dictionary, its string representation (`str(value)`) is returned.
    4.  If all else fails (e.g., an empty dictionary was passed and no specific keys matched), the `default` string is returned.

### 3.2. `inches_to_feet_inches_str(inches)`

*   **Purpose**: Converts a numerical value in inches to a formatted string representation (e.g., `X'-Y"`).
*   **Logic**:
    1.  If `inches` is `None`, returns 'N/A'.
    2.  Tries to convert `inches` to a float.
    3.  Calculates `feet` (integer part of `inches / 12`).
    4.  Calculates `rem_inches` (remainder of `inches % 12`, rounded to the nearest integer).
    5.  Handles a special case where `rem_inches` rounds up to 12: increments `feet` by 1 and sets `rem_inches` to 0.
    6.  Returns the formatted string (e.g., `f"{feet}'-{rem_inches}\""`).
    7.  If any exception occurs during conversion (e.g., `ValueError`), returns 'N/A'.
    *   **Note**: The docstring mentions this duplicates a function from `utils.py` for independence.

### 3.3. `categorize_wire(wire_type)`

*   **Purpose**: Categorizes a wire as 'COMM' (communication), 'CPS' (CPS Energy electrical), or 'OTHER' based on keywords in its `wire_type` description string.
*   **Logic**:
    1.  If `wire_type` is empty or `None`, returns 'OTHER'.
    2.  Converts `wire_type` to lowercase.
    3.  Checks for communication-related keywords (e.g., 'fiber', 'telco', 'comm', 'charter', 'att', 'spectrum'). If found, returns 'COMM'.
    4.  Checks for CPS-related keywords (e.g., 'cps', 'electric', 'power', 'neutral'). If found, returns 'CPS'.
    5.  If neither category matches, defaults to 'OTHER'.

### 3.4. `get_excel_column_letter(column_index)`

*   **Purpose**: Converts a 1-based integer column index into its corresponding Excel column letter (e.g., 1 -> 'A', 26 -> 'Z', 27 -> 'AA').
*   **Logic**:
    1.  Uses a `while` loop that continues as long as `column_index` is greater than 0.
    2.  In each iteration:
        *   `divmod(column_index - 1, 26)` is used. Subtracting 1 maps the 1-based index to 0-based for modulo arithmetic with 26 (number of letters in the alphabet).
        *   `remainder` gives the 0-based index of the current letter (0 for 'A', 1 for 'B', etc.).
        *   `column_index` is updated with the quotient, effectively moving to the next "digit" in base-26.
        *   The character corresponding to `remainder` (`chr(65 + remainder)`) is prepended to the `result` string.
    3.  Returns the `result` string.

### 3.5. `parse_feet_inches(height_str)`

*   **Purpose**: Parses a height string in the format "X'-Y\"" (e.g., "35'-6\"") and converts it into total inches.
*   **Logic**:
    1.  If `height_str` is empty, `None`, or 'N/A', returns `None`.
    2.  Uses `re.search(r'(\d+)\'(?:-)?(\d+)"', height_str)` to find patterns matching feet and inches. The `(?:-)?` allows for an optional hyphen.
    3.  If a match is found:
        *   Extracts feet (group 1) and inches (group 2) as integers.
        *   Calculates total inches as `(feet * 12) + inches` and returns it.
    4.  If no regex match, it attempts to parse `height_str` directly as a float (in case the input is already in inches as a number).
    5.  If direct float conversion fails (raises `ValueError`), returns `None`.

## 4. Potential Usage Context

These utilities are likely used in conjunction with libraries like `openpyxl` when reading from or writing to Excel files that contain utility pole and attachment data.
*   `extract_string_value` would be useful when reading data that might have inconsistent or nested structures.
*   `inches_to_feet_inches_str` and `parse_feet_inches` handle conversions between numerical inch values and the common feet-inches string representation often used in reports.
*   `categorize_wire` helps in classifying attachments for specific processing or reporting rules.
*   `get_excel_column_letter` is a standard utility for programmatically addressing Excel cells by column letter when the column index is known.

This module provides a set of focused tools to manage common data transformations and extractions encountered in this domain.

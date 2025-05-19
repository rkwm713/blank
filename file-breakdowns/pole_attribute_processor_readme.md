# `pole_attribute_processor.py` - Processing and Resolving Pole Attributes

## 1. Overview

`pole_attribute_processor.py` is a Python module designed to extract, process, and consolidate various attributes of utility poles from different data sources, primarily Katapult and SPIDAcalc. It handles the complexities of varying attribute naming conventions and data structures, and provides logic to resolve conflicts when attributes are present in multiple sources.

Key functionalities include:
*   Extracting common pole attributes (pole number, owner, height, class, species, structure, coordinates) from Katapult node data.
*   Extracting specific attributes like pole structure, construction grade, and PLA (Percent Loading Analysis) percentage from SPIDAcalc data using helper functions from `spida_utils`.
*   Providing robust extraction for pole numbers and owners from Katapult attributes by checking multiple common keys and structures.
*   Extracting make-ready notes from Katapult attributes.
*   Resolving conflicts between Katapult-derived and SPIDAcalc-derived attributes based on a specified strategy (e.g., preferring SPIDAcalc data, which is common for engineering accuracy).
*   Normalizing pole numbers for consistent identification.

## 2. Key Imports and Modules

*   **`logging`**: Standard Python library for logging.
*   **`utils`**: A local module.
    *   `normalize_pole_id`: Standardizes pole ID formats.
    *   `extract_string_value`: Safely extracts a string value from potentially nested or non-string data, with a default.
*   **`spida_utils`**: A local module containing helper functions specifically for SPIDAcalc data extraction.
    *   `get_construction_grade_spida`: Extracts construction grade.
    *   `get_pole_structure_spida`: Extracts pole structure (e.g., "40-4 Southern Pine").
    *   `get_pla_percentage_spida`: Extracts PLA percentage.

## 3. Core Functions and Logic

### 3.1. `extract_pole_attributes_katapult(node, attributes)`

*   **Purpose**: Extracts a set of pole attributes primarily from Katapult `node` data and its `attributes` dictionary.
*   **Logic**:
    1.  Calls `extract_pole_number` to get the pole number.
    2.  Uses `extract_string_value` to get `pole_owner`.
    3.  Extracts Katapult-specific height, class, and species (e.g., `pole_height_kat`), defaulting species to "Southern Pine".
    4.  Constructs `kat_pole_structure` if height and class are available, or uses a direct `pole_structure` attribute if present.
    5.  Initializes `pole_structure`, `construction_grade`, and `pla_percentage` with Katapult values or 'N/A', as these are typically overridden by SPIDAcalc data.
    6.  Includes latitude and longitude from the `node`.
*   **Returns**: A dictionary of these attributes, including both raw Katapult values (suffixed with `_kat`) and fields intended for final resolved values.

### 3.2. `extract_pole_number(attributes)`

*   **Purpose**: Robustly extracts the pole number from a Katapult `attributes` dictionary by checking several common keys and structures.
*   **Logic**: Sequentially checks for keys like 'PoleNumber', 'pl_number', 'dloc_number' (and their capitalized legacy versions 'PL_number', 'DLOC_number'). For each key, it handles cases where the value might be a direct string or a nested dictionary (common Katapult patterns like `attributes['PoleNumber']['-Imported']` or `attributes['PoleNumber']['assessment']`).
*   **Returns**: The extracted pole number string, or `None` if not found.

### 3.3. `extract_pole_owner(attributes)`

*   **Purpose**: Extracts the pole owner from Katapult `attributes`, checking common keys like 'pole_owner' and 'PoleOwner' and handling nested dictionary structures.
*   **Returns**: The extracted pole owner string, or `None`.

### 3.4. `extract_pole_height(attributes)`

*   **Purpose**: Extracts pole height. **Note**: This function's implementation seems to be incorrectly extracting a *pole number* instead of a height, reusing the logic from `extract_pole_number` and also checking 'pole_tag'. This appears to be a bug or misnamed function based on its implementation. The `extract_pole_height_katapult` function is more aligned with extracting height.
*   **Returns**: A string (likely a pole number or "Unknown").

### 3.5. `extract_pole_height_katapult(attributes)`, `extract_pole_class_katapult(attributes)`, `extract_pole_species_katapult(attributes)`

*   **Purpose**: These functions specifically extract height, class, and species from Katapult attributes, checking both lowercase and capitalized key versions (e.g., 'pole_height' and 'PoleHeight'). `extract_pole_species_katapult` defaults to "Southern Pine".
*   **Returns**: The extracted string value, or `None` (or "Southern Pine" for species) if not found.

### 3.6. `extract_notes(attributes)`

*   **Purpose**: Extracts make-ready related notes from Katapult `attributes`.
*   **Logic**: Checks for keys like 'kat_mr_notes', 'kat_MR_notes', and 'stress_MR_notes', handling nested dictionary structures.
*   **Returns**: A dictionary `{'kat_mr_notes': ..., 'stress_mr_notes': ...}`.

### 3.7. `resolve_pole_attribute_conflicts(katapult_attrs, spida_pole_data, full_spida_data, strategy='PREFER_KATAPULT')`

*   **Purpose**: Merges pole attributes from Katapult (`katapult_attrs`) with those derived from SPIDAcalc data, resolving conflicts based on the given `strategy`.
*   **Logic**:
    1.  Starts with a copy of `katapult_attrs`.
    2.  If `spida_pole_data` (for the specific pole) is available:
        *   Calls `get_pole_structure_spida` to get `spida_pole_structure`.
        *   Calls `get_pla_percentage_spida` to get `spida_pla_percentage`.
    3.  If `full_spida_data` (the entire SPIDAcalc dataset) is available:
        *   Calls `get_construction_grade_spida` to get `spida_construction_grade`.
    4.  **Conflict Resolution**:
        *   **Pole Structure**: If `spida_pole_structure` is available, it's generally preferred. If `strategy` is 'HIGHLIGHT_DIFFERENCES' and Katapult structure also exists and differs, it creates a combined string. Otherwise, SPIDA value is used. If both are missing, defaults to "N/A".
        *   **Construction Grade**: If `spida_construction_grade` is available, it's used. Defaults to "N/A" if missing.
        *   **PLA Percentage**: If `spida_pla_percentage` is valid (not "N/A"), it's used. Defaults to "N/A".
    5.  Logs which SPIDAcalc values were used for these key fields.
    6.  If `strategy` is not 'HIGHLIGHT_DIFFERENCES', removes the temporary Katapult-specific fields (e.g., `pole_height_kat`) from the `resolved_attrs`.
*   **Returns**: The dictionary of resolved and augmented pole attributes.

### 3.8. `extract_spida_pole_attributes(spida_pole_data)`

*   **Purpose**: Extracts basic height, class, and species from SPIDAcalc `poleTags` or direct attributes for a single pole.
*   **Note**: The docstring suggests preferring `get_pole_structure_spida` for the combined structure string. This function seems to provide raw components.
*   **Returns**: A dictionary with `pole_height_spida`, `pole_class_spida`, `pole_species_spida`.

## 4. Overall Role

This module acts as a crucial data harmonization layer. It takes raw attribute data, which can be inconsistently structured or named, from Katapult, and combines it with more engineering-focused data from SPIDAcalc. The conflict resolution ensures that the most reliable or desired data source is prioritized for key attributes like pole structure and loading analysis results, which are critical for make-ready engineering decisions.

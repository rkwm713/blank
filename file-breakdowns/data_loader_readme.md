# `data_loader.py` - Utilities for Loading and Preprocessing Input Data

## 1. Overview

`data_loader.py` is a Python module responsible for loading data from Katapult and SPIDAcalc JSON files. It also includes functions for performing initial validation, building lookup structures for efficient data access (specifically for SPIDAcalc data), and normalizing lists of target pole IDs.

Key functionalities include:
*   Loading Katapult JSON data from a file path.
*   Loading SPIDAcalc JSON data from a file path (if provided).
*   Building lookup dictionaries from SPIDAcalc data to quickly find pole locations by normalized ID and wires by owner and endpoints.
*   Tracking the original order of poles as they appear in the SPIDAcalc file.
*   Normalizing a user-provided list of target pole IDs for consistent matching.

## 2. Key Imports and Modules

*   **`json`**: Standard Python library for parsing JSON data.
*   **`logging`**: Standard Python library for logging messages.
*   **`utils`**: A local module presumably containing utility functions:
    *   `normalize_pole_id`: Standardizes pole ID formats (e.g., removing prefixes/suffixes, standardizing case).
    *   `normalize_owner`: (Imported within `build_spida_lookups`) Standardizes owner names.

## 3. Core Functions and Logic

### 3.1. `load_katapult_data(katapult_path)`

*   **Purpose**: Loads Katapult JSON data from the specified file.
*   **Parameters**:
    *   `katapult_path` (str): The file path to the Katapult JSON file.
*   **Logic**:
    1.  Logs the loading action.
    2.  Opens and reads the file specified by `katapult_path` using `utf-8` encoding.
    3.  Parses the JSON content using `json.load()`.
    4.  Logs basic statistics about the loaded data: the number of nodes and connections found.
*   **Returns**: A dictionary containing the loaded Katapult data.

### 3.2. `load_spidacalc_data(spidacalc_path)`

*   **Purpose**: Loads SPIDAcalc JSON data from the specified file, if a path is provided.
*   **Parameters**:
    *   `spidacalc_path` (str): The file path to the SPIDAcalc JSON file. Can be `None`.
*   **Logic**:
    1.  If `spidacalc_path` is `None` or empty, returns `None` immediately.
    2.  Logs the loading action.
    3.  Opens and reads the file specified by `spidacalc_path` using `utf-8` encoding.
    4.  Parses the JSON content using `json.load()`.
    5.  Logs basic statistics: the number of "leads" and the total number of "locations" across all leads.
*   **Returns**: A dictionary containing the loaded SPIDAcalc data, or `None` if no path was provided.

### 3.3. `build_spida_lookups(spida)`

*   **Purpose**: Creates several lookup dictionaries from the loaded SPIDAcalc data to facilitate faster access to specific pieces of information.
*   **Parameters**:
    *   `spida` (dict): The loaded SPIDAcalc data.
*   **Logic**:
    1.  If `spida` data is not provided (e.g., `None`), returns empty dictionaries.
    2.  Initializes `spida_pole_order` (to track original pole sequence), `spida_wire_lookup`, and `spida_lookup` (for locations by pole ID).
    3.  Iterates through each `lead` in `spida.get('leads', [])`, then through each `loc` (location/pole) in `lead.get('locations', [])`.
        *   **Pole Order**: Normalizes the location's `label` (pole ID) using `normalize_pole_id`. If this normalized pole ID hasn't been seen, its order (an incrementing index) is recorded in `spida_pole_order`.
        *   **Wire Lookup (`spida_wire_lookup`)**:
            *   Iterates through `designs` within the location, then `wires` within each design's `structure`.
            *   Normalizes the wire `owner` using `normalize_owner` (imported locally within the function).
            *   Constructs a list of `endpoints` for the wire: starts with the current `loc_pole` and adds any pole labels found in `wire['wireEndPoints']`. These endpoints are normalized and sorted to create a consistent key.
            *   The `spida_wire_lookup` dictionary is keyed by a tuple `(owner, tuple(sorted_endpoints))` and stores the wire data.
        *   **Location Lookup (`spida_lookup`)**:
            *   The `spida_lookup` dictionary is keyed by the normalized pole ID (`norm`) and stores the entire location (`loc`) data.
*   **Returns**: A tuple containing three dictionaries: `spida_lookup`, `spida_wire_lookup`, and `spida_pole_order`.

### 3.4. `filter_target_poles(target_poles)`

*   **Purpose**: Normalizes a list of target pole IDs provided by the user.
*   **Parameters**:
    *   `target_poles` (list): A list of pole ID strings.
*   **Logic**:
    1.  If `target_poles` is `None` or empty, returns `None`.
    2.  Uses a list comprehension to iterate through the input `target_poles`. Each pole ID is normalized using `normalize_pole_id`. Only non-empty pole IDs are included.
    3.  Logs the number of normalized target poles and the list itself.
*   **Returns**: A list of normalized target pole IDs, or `None` if the input was empty.

## 4. Dependencies on Other Project Files

*   **`utils.py`**: Provides `normalize_pole_id` and (indirectly via `build_spida_lookups`) `normalize_owner`.

This module serves as the entry point for data ingestion and initial structuring, preparing the data for more complex processing by other modules in the application.

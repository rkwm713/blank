# `trace_utils.py` - Utilities for Katapult Trace Data

## 1. Overview

`trace_utils.py` is a Python module providing utility functions for working with "trace" data within Katapult JSON structures. Traces in Katapult often contain detailed information about linear features like wires, including their owner, type, and proposed status. This module helps in reliably accessing this trace data and extracting meaningful metadata.

Key functionalities include:
*   Robustly looking up trace data by its ID, accommodating different potential structures within the Katapult JSON for where traces might be stored.
*   Extracting key metadata (owner, cable type, proposed status) from a combination of wire-specific data and its associated trace data, prioritizing the trace data as a more reliable source.
*   Classifying a wire based on its trace data into categories like "CPS_ELECTRICAL", "COMMUNICATION", or "OTHER".

## 2. Key Imports and Modules

*   **`utils`**: A local module.
    *   `normalize_owner`: Standardizes owner names (e.g., "ATT" to "AT&T").
    *   `extract_string_value`: Safely extracts a string value from potentially nested or non-string data, with a default.

## 3. Core Functions and Logic

### 3.1. `get_trace_by_id(katapult, trace_id)`

*   **Purpose**: Retrieves a specific trace data dictionary from the main `katapult` JSON data using its `trace_id`. This function is designed to be robust to variations in how trace data might be structured within the `katapult['traces']` object.
*   **Logic**:
    1.  If `trace_id` is empty, returns an empty dictionary.
    2.  Checks several common paths where the trace might be located:
        *   Directly under `katapult['traces'][trace_id]`.
        *   Under `katapult['traces']['trace_data'][trace_id]`.
        *   Under `katapult['traces']['trace_items'][trace_id]`.
        *   As a nested dictionary: `katapult['traces'][some_key][trace_id]`.
    3.  If found, returns the trace dictionary.
    4.  If not found after checking all paths, logs a debug message and returns an empty dictionary.

### 3.2. `extract_wire_metadata(wire, trace)`

*   **Purpose**: Extracts and standardizes important metadata for a wire, such as its owner, cable type, and whether it's a proposed installation. It intelligently combines information from the `wire` object itself (often from photo annotation data) and its associated `trace` object (which usually contains more definitive attributes).
*   **Logic**:
    1.  Initializes a `result` dictionary with default 'Unknown' values for owner and cable type, and `is_proposed: False`.
    2.  **Prioritize Trace Data**:
        *   **Owner**: Attempts to get owner from `trace` using keys 'company', 'owner', then 'client'. Uses `extract_string_value` for safe extraction.
        *   **Cable Type**: Attempts to get cable type from `trace` using keys 'cable_type', 'type', then 'description'. Uses `extract_string_value`.
        *   **Proposed Status**: Checks `trace` for boolean flags ('proposed', 'is_proposed') or string/numeric indicators ('true', 'yes', 'proposed', 1) in fields like 'status'.
    3.  **Fallback to Wire Data**: If owner or cable type is still 'Unknown', or `is_proposed` is still false, it attempts to extract these from the `wire` object using similar key-checking logic (e.g., `_company`, `_cable_type`, `_proposed`).
    4.  **Normalize Owner**: Calls `normalize_owner` on the extracted owner name.
    5.  **Infer Cable Type**: If `cable_type` is still 'Unknown' but an owner is identified (e.g., 'CPS ENERGY', 'AT&T'), it makes a generic inference (e.g., "Communication" for AT&T).
    6.  Logs a debug message if both owner and cable type remain 'Unknown', indicating a lack of data.
*   **Returns**: The `result` dictionary containing `owner`, `cable_type`, and `is_proposed`.

### 3.3. `classify_wire(trace_data)`

*   **Purpose**: Classifies a wire into "CPS_ELECTRICAL", "COMMUNICATION", or "OTHER" based on its `trace_data`.
*   **Logic**:
    1.  If `trace_data` is not a dictionary, defaults to "OTHER".
    2.  **Primary Classification (usageGroup)**:
        *   If `trace_data.usageGroup` is 'POWER':
            *   If `trace_data.company` contains 'CPS', classifies as "CPS_ELECTRICAL".
            *   Otherwise, "OTHER" (non-CPS power).
        *   If `trace_data.usageGroup` is 'COMMUNICATION', classifies as "COMMUNICATION".
    3.  **Fallback Classification (company + cable_type)**:
        *   **CPS Electrical**: If `trace_data.company` contains 'CPS' AND (`trace_data.cable_type` contains electrical keywords like 'PRIMARY', 'NEUTRAL', 'SECONDARY', OR `cable_type` is empty), classifies as "CPS_ELECTRICAL".
        *   **Communication**: If `trace_data.company` matches known communication companies (AT&T, SPECTRUM, etc.) OR `trace_data.cable_type` contains communication keywords ('COM', 'FIBER', 'TELCO'), classifies as "COMMUNICATION".
    4.  If none of the above rules match, defaults to "OTHER".
*   **Returns**: The classification string.

## 4. Overall Role

This module provides essential low-level utilities for interpreting Katapult's trace data. Accurate trace lookup and metadata extraction are fundamental for correctly identifying wire characteristics, which in turn informs higher-level processing logic related to attachments, neutral identification, and connection analysis. The classification function helps in categorizing wires for specific business rules or reporting requirements.

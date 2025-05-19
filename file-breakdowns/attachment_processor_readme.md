# `attachment_processor.py` - Utility for Processing Pole Attachment Data

## 1. Overview

`attachment_processor.py` is a Python module designed to process, normalize, and consolidate data about attachments (like wires and equipment) on utility poles. It handles data from two primary sources: Katapult and SPIDAcalc. The module aims to create a unified and consistent view of attachments, resolving discrepancies and applying specific business logic for formatting descriptions and determining heights.

Key functionalities include:
*   Normalizing owner names and attachment descriptions (e.g., "Charter" and "Spectrum" to "Charter/Spectrum").
*   Extracting attachment details (owner, type, height) from Katapult's photo-based data.
*   Processing attachment details from SPIDAcalc's "measured design" and "recommended design" sections, including handling underground (UG) attachments.
*   Consolidating attachments from both sources, preferring SPIDAcalc data if available and applying rules for merging or updating records.
*   Identifying owners whose attachments have height changes (moves or new installs).
*   Applying specific rules for mid-span proposed heights based on recent (2025-05-22) business logic.
*   Formatting final attachment descriptions for reporting.

## 2. Key Imports and Modules

*   **`logging`**: Standard Python library for logging messages and debugging information.
*   **`utils`**: A local module presumably containing utility functions:
    *   `meters_to_feet_inches_str`: Converts a measurement in meters to a string representation in feet and inches.
    *   `normalize_owner`: Standardizes owner names (e.g., "ATT" to "AT&T").
    *   `inches_to_feet_inches_str`: Converts a measurement in inches to a string representation in feet and inches.
*   **`trace_utils`**: A local module for handling Katapult trace data:
    *   `get_trace_by_id`: Retrieves trace information from the Katapult dataset using a trace ID.
    *   `extract_wire_metadata`: Extracts metadata (owner, cable type, proposed status) for a wire from Katapult data.
*   **`wire_utils`**: A local module (though `process_wire_height` is imported but not directly used in the provided snippet, it might be used by `trace_utils` or other related modules).

## 3. Core Functions and Logic

### 3.1. `normalize_charter(desc)`

*   **Purpose**: Normalizes wire and equipment descriptions, with special handling for "Charter/Spectrum" and "Fiber Optic" variations. Also includes logic for AT&T communication types and CPS Energy fiber.
*   **Logic**:
    *   Converts the input description to lowercase for case-insensitive matching.
    *   If "charter" or "spectrum" is found, returns "Charter/Spectrum".
    *   If "fiber" is found without "optic", it standardizes to "Fiber Optic".
    *   Handles various AT&T descriptions (telco, drop, fiber, general com) and maps them to standardized forms like "Telco Com", "Com Drop", etc.
    *   Identifies "CPS Energy" fiber as "Supply Fiber".
    *   Returns the original description if no special normalization rule applies.

### 3.2. `process_katapult_attachments(node, katapult)`

*   **Purpose**: Extracts and processes attachment data from a single Katapult `node`'s photo information.
*   **Logic**:
    1.  Iterates through each `photo` associated with the `node`.
    2.  Skips invalid photo entries (not dictionaries or missing `photofirst_data`).
    3.  Accesses `wire` data within `photofirst_data`. Handles cases where `wire_data` might be a list or a dictionary.
    4.  For each `wire`:
        *   Retrieves the `_trace` ID and uses `get_trace_by_id` to fetch the corresponding trace data from the full `katapult` dataset.
        *   Uses `extract_wire_metadata` to get owner, cable type, and `is_proposed` status.
        *   Formats a standardized description using `format_attacher_description`.
        *   Gets the `_measured_height` (in inches).
        *   If an attachment with the same formatted description already exists in the `attacher_map`, it updates the entry only if the current wire's `existing_height_float` is greater. This ensures the highest recorded measurement for a given attachment type is kept.
        *   If the wire `is_proposed`, its `proposed_height` is set to its measured height (converted to feet-inches string). Otherwise, `proposed_height` is 'N/A'.
        *   Stores the attachment data in `attacher_map` keyed by the `formatted_desc`. Data includes description, existing height (string and raw inches), proposed height (string), midspan proposed ('N/A' for Katapult), and `is_proposed` flag.
    *   Returns the `attacher_map`.

### 3.3. `process_spidacalc_attachments(spida_pole_data, norm_pole_number=None)`

*   **Purpose**: Processes attachments from SPIDAcalc pole data, considering both "measured design" (existing state) and "recommended design" (proposed state).
*   **Logic**:
    1.  **Underground Detection**: Defines an inner helper `is_underground(desc, cable_type)` to check if an attachment description or type indicates it's an underground (UG) or riser component.
    2.  **Design Identification**: Locates the "measured design" and "recommended design" sections within `spida_pole_data`.
    3.  **Key Generation**: Defines an inner helper `make_key(owner, desc, cable_type)` to create a unique key for each attachment by combining normalized owner, normalized description, and (optionally) cable type. This helps in matching attachments between measured and recommended designs.
    4.  **Process Measured Design (Existing Attachments)**:
        *   Iterates through `wires` and `equipments` in the measured design.
        *   For each item, extracts owner, description, cable type, attachment height (in meters), and midspan height (if available).
        *   Converts heights from meters to feet-inches strings and raw inches.
        *   Marks `midspan_proposed` as 'UG' if `is_underground` is true, otherwise 'N/A'.
        *   Stores these existing attachments in the `attachments` dictionary using the generated `key`.
    5.  **Process Recommended Design (Proposed/Moved Attachments)**:
        *   Iterates through `wires` and `equipments` in the recommended design.
        *   For each item, extracts details similarly to the measured design.
        *   If an attachment with the same `key` already exists (from the measured design):
            *   It's considered an existing attachment that might have moved.
            *   Its `proposed_height` is updated with the height from the recommended design.
            *   If the height changed, it's a move.
            *   `midspan_proposed` is set to 'UG' if either the measured or recommended version is underground.
        *   If the `key` does not exist in `attachments`:
            *   It's considered a new installation.
            *   `existing_height` is 'N/A', and `proposed_height` is taken from the recommended design.
            *   `midspan_proposed` is 'UG' if underground, otherwise 'N/A'.
    *   Returns the `attachments` dictionary.

### 3.4. `consolidate_attachments(spida_attachments, katapult_attachments)`

*   **Purpose**: Merges attachment data from SPIDAcalc and Katapult sources, deduplicates entries, and applies specific logic for mid-span heights of moved attachments.
*   **Logic**:
    1.  **Initial Consolidation**:
        *   If `spida_attachments` are available, they are used as the primary source.
        *   Deduplicates SPIDAcalc entries based on `description`. If multiple SPIDA entries have the same description, it prioritizes the one that has both existing and proposed heights defined.
        *   If no `spida_attachments`, `katapult_attachments` are used directly.
    2.  **Mid-Span Logic for Moved Attachments (2025-05-22 Rule)**:
        *   Iterates through the `consolidated` attachments.
        *   If an attachment (identified by `desc`) exists in both `consolidated` (from SPIDA) and `katapult_attachments`:
            *   Checks if the SPIDA entry represents a "move" (existing height and proposed height are different and not 'N/A').
            *   If it's a move AND the SPIDA entry's `midspan_proposed` is 'N/A' (or empty):
                *   The `midspan_proposed` value from the corresponding `katapult_attachments` entry is copied to the SPIDA entry, provided the Katapult midspan value is not 'N/A'.
                *   Raw midspan inches from Katapult are also copied if available.
    3.  **Final List Creation and Sorting**:
        *   Converts the `consolidated` dictionary into a list of attachment dictionaries.
        *   Sorts this list primarily by `raw_existing_height_inches` in descending order (highest attachment first).
    *   Returns the sorted list of consolidated attachments.

### 3.5. `identify_owners_with_changes(attachers)`

*   **Purpose**: Identifies unique owners whose attachments have undergone a height change (move) or are newly proposed.
*   **Logic**:
    1.  Initializes an empty set `owners_with_changes`.
    2.  Iterates through the list of `attachers`.
    3.  For each `attacher`:
        *   Checks if `existing_height` and `proposed_height` are both valid (not 'N/A') and different.
        *   Also checks if the `is_proposed` flag is true.
        *   If either condition is met, it extracts the owner from the `description` string (takes the first part before a space), normalizes it using `normalize_owner`, and adds the normalized owner to the `owners_with_changes` set.
    *   Returns the set of owners.

### 3.6. `apply_midspan_values(attachers_list, midspan_proposed)`

*   **Purpose**: Applies mid-span proposed values to attachments based on specific rules, particularly for new and moved attachments (as per 2025-05-22 logic).
*   **Parameters**:
    *   `attachers_list`: The list of attachment dictionaries to modify.
    *   `midspan_proposed`: A general or span-level midspan proposed value that can be used as a fallback.
*   **Logic**:
    *   Iterates through each `attacher` in `attachers_list`.
    *   **Moved Attachments**: If an attachment has both existing and proposed heights and they differ (`moved`):
        *   If its `midspan_proposed` is currently 'N/A', it's updated with the `midspan_proposed` parameter (the span-level fallback), but only if the fallback is not 'N/A'. This preserves any specific midspan value already set (e.g., from Katapult via `consolidate_attachments`).
    *   **New Installs**: If an attachment has no `existing_height` but has a `proposed_height`:
        *   Its `midspan_proposed` is set to 'N/A', unless it's already marked as 'UG' (underground). This ensures new aerial installs don't inherit a span-level midspan value.
    *   **Other Cases**: For attachments that are unchanged or only have existing heights, their `midspan_proposed` value is left as is.

### 3.7. `format_attacher_description(owner, desc)`

*   **Purpose**: Creates a standardized, formatted description string for an attachment by combining its owner and description/type, applying specific formatting rules for entities like AT&T, CPS Energy, and Charter/Spectrum.
*   **Logic**:
    1.  Normalizes and cleans the input `owner` and `desc` strings.
    2.  **Neutral Wires**: If "neutral" is in `desc_lower`, returns "Neutral".
    3.  **AT&T**: If the owner is identified as AT&T (checking multiple variations like "at&t", "att"):
        *   If `desc_lower` contains "telco", returns "AT&T Telco Com".
        *   If "drop", returns "AT&T Com Drop".
        *   If "fiber" or "optic", returns "AT&T Fiber Optic Com".
        *   Otherwise, returns "AT&T [normalized_desc]" (using `normalize_charter` for the description part).
    4.  **CPS Energy**: If the owner is "CPS Energy" or similar:
        *   If `desc_lower` contains "fiber", returns "CPS Supply Fiber".
    5.  **Charter/Spectrum**: If owner or description indicates "Charter" or "Spectrum":
        *   If `desc_lower` contains "fiber" or "optic", returns "Charter/Spectrum Fiber Optic".
        *   Otherwise, returns "Charter/Spectrum [normalized_desc]".
    6.  **Default**: For other cases, it combines the `normalize_owner(owner)` result with `normalize_charter(desc)`. Ensures "AT&T" is consistently formatted if `normalize_owner` results in it.
    *   Returns the final formatted string, stripped of leading/trailing whitespace.

## 4. Dependencies on Other Project Files

*   **`utils.py`**: Provides `meters_to_feet_inches_str`, `normalize_owner`, `inches_to_feet_inches_str`.
*   **`trace_utils.py`**: Provides `get_trace_by_id` and `extract_wire_metadata` for Katapult data processing.
*   **`wire_utils.py`**: (Imported `process_wire_height` but not directly used in the snippet).

This module plays a crucial role in transforming raw data from different sources into a structured and consistent format suitable for generating make-ready reports.

[![Visualizing Pole Data — Katapult Engineering](https://tse2.mm.bing.net/th?id=OIP.pyWvtDTMFOVpVUOxe6K9ZQHaEW\&pid=Api)](https://www.katapultengineering.com/blog/visualizing-pole-data)



# Understanding Katapult JSON for Make-Ready Engineering

**Last Updated:** May 15, 2025

## 1. Introduction

This document serves as a comprehensive guide to the structure and key data elements of Katapult JSON files, particularly those exported from the Katapult Pro platform. It is intended to assist developers and engineers in accurately extracting and processing data necessary for generating Make-Ready Engineering reports.

## 2. Overview of Katapult JSON Structure

A typical Katapult JSON export is a single JSON object containing several top-level keys. The most pertinent keys for Make-Ready reporting include:

* **`nodes`**: Represents utility poles or structures.
* **`connections`**: Denotes spans between poles.
* **`traces`**: Contains information about cable ownership and types.
* **`photos`** or **`photo_summary`**: Holds photographic data and annotations.
* **`equipments`** (optional): Details about equipment instances.

## 3. Detailed Breakdown

### 3.1. Nodes (Poles)

Each entry in the `nodes` object corresponds to a utility pole.

* **Identifier**: Located in `attributes`, common keys include:

  * `PoleNumber`
  * `PL_number`
  * `DLOC_number`
  * `electric_pole_tag`

  *Action*: Normalize using `processor.utils.normalize_pole_id()` for consistency.

* **Geolocation**:

  * `latitude`
  * `longitude`

* **Address**: Found under `attributes['Address Object']['assessment']`, including:

  * `formatted_address`
  * `street_number`
  * `street_name`
  * `city`
  * `state`
  * `zip_code`

* **Physical Attributes**:

  * `PoleOwner`
  * `PoleHeight` (typically in feet)
  * `PoleClass`
  * `PoleSpecies` (e.g., "Southern Pine")

* **Analysis Data**:

  * `existing_capacity_%`
  * `final_passing_capacity_%`
  * `construction_grade_analysis`
  * `kat_work_type`
  * `work_type`
  * `mr_state`

### 3.2. Attachments (Wires and Equipment)

Attachments are primarily derived from photo annotations.

* **Photo Access**: Each node's `photos` object links `photo_id`s to the pole.

* **Annotations**: Within `photofirst_data`, access:

  * `wire`: Wire annotations.
  * `equipment`: Equipment annotations.

* **Wire Details**:

  * `_measured_height`: Height measurement (typically in inches; convert as needed).
  * `_trace`: Links to the `traces` object for ownership and type.

* **Trace Information**:

  * `company`: Owner of the cable/equipment.
  * `cable_type`: Type of cable (e.g., "Primary", "Neutral", "Fiber Optic Com").
  * `usageGroup` (optional): Additional categorization.

### 3.3. Connections (Spans)

Connections represent the physical spans between poles.

* **Endpoints**:

  * `node_id_1`
  * `node_id_2`

* **Sections**: Each connection may have multiple sections with:

  * `latitude`
  * `longitude`
  * Associated photos for mid-span measurements.

* **Attributes**:

  * `connection_type`: Describes the nature of the connection (e.g., "underground\_path").

## 4. Data Processing Considerations

* **Unit Conversion**: Ensure all measurements are converted to a consistent unit system (e.g., feet) using `processor.height_utils.py`.

* **Normalization**:

  * Pole identifiers should be standardized using `processor.utils.normalize_pole_id()`.
  * Attacher names and cable types may require normalization to ensure consistency across datasets.

* **Error Handling**: Implement robust error handling to manage missing or unexpected data structures.

* **Constants Management**: Utilize `processor.constants.py` to manage known string literals and avoid hard-coded values.

## 5. Conclusion

Understanding the structure and content of Katapult JSON files is crucial for accurate and efficient generation of Make-Ready Engineering reports. This guide provides the foundational knowledge required to navigate and process these datasets effectively.

---

If you require further assistance or have specific questions regarding the processing of Katapult JSON data, so do I...

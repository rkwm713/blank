[![SPIDAcalc | Bentley Systems | Infrastructure Engineering Software Company](https://tse3.mm.bing.net/th?id=OIP.klU6suDymhmqZuoMfgMQ_AHaE0\&pid=Api)](https://www.bentley.com/software/spidacalc/)

# Understanding SPIDAcalc JSON for Make-Ready Engineering Reports

**Last Updated:** May 15, 2025

---

## Overview

This document serves as a comprehensive guide to the structure and key data elements of SPIDAcalc JSON files, particularly focusing on their application in generating Make-Ready Engineering reports. It is intended for developers and engineers involved in data processing and analysis workflows that integrate SPIDAcalc outputs.

---

## 1. Introduction to SPIDAcalc JSON Structure

SPIDAcalc JSON files encapsulate detailed information about utility pole structures, including various design scenarios and analysis results. The primary components of a typical SPIDAcalc JSON file are:

* **Project Metadata**: General information about the project.
* **Leads**: Represent different segments or phases within the project.

  * **Locations**: Each location corresponds to a specific pole or structure.

    * **Label**: Identifier for the pole (e.g., "1-PL410620").
    * **Designs**: Different design scenarios for the pole, such as "Measured Design" and "Recommended Design".
    * **PoleResults**: Results from structural analysis, if available.
    * **PoleTags**: Additional tags or metadata associated with the pole.

---

## 2. Key Data Extraction Points

### 2.1. Pole Identification

* **Path**: `leads[n].locations[m].label`
* **Action**: Normalize this label using a consistent function (e.g., `normalize_pole_id`) to extract the core pole number for matching with other datasets.

### 2.2. Design Scenarios

Each pole may have multiple design scenarios:

* **Measured Design**: Represents the existing state of the pole.
* **Recommended Design**: Represents the proposed state after modifications.

**Path**: `leads[n].locations[m].designs[d]` where `designs[d].label` matches the desired scenario.

### 2.3. Pole Attributes

Within each design:

* **Path**: `design.structure.pole.clientItem`
* **Attributes**:

  * `height.value` and `height.unit`: Height of the pole.
  * `classOfPole`: Classification of the pole.
  * `species`: Material or species of the pole.

### 2.4. Attachments (Wires and Equipment)

Attachments are detailed within each design's structure:

* **Wires**:

  * **Path**: `design.structure.wires`
  * **Attributes**:

    * `owner.id`: Owner of the wire.
    * `clientItem.description` or `clientItem.size`: Description or size of the wire.
    * `attachmentHeight.value` and `attachmentHeight.unit`: Height and unit of the attachment.

* **Equipments**:

  * **Path**: `design.structure.equipments`
  * **Attributes**:

    * `owner.id`: Owner of the equipment.
    * `clientItem.type` and `clientItem.size`: Type and size of the equipment.
    * `attachmentHeight.value` and `attachmentHeight.unit`: Height and unit of the attachment.

### 2.5. Structural Analysis Results

If available, structural analysis results provide insights into the stress and load on the pole:

* **Path**: `leads[n].locations[m].poleResults`
* **Attributes**:

  * `component`: Component analyzed (e.g., "Pole").
  * `analysisType`: Type of analysis (e.g., "STRESS").
  * `actual`: Actual stress percentage.
  * `passes`: Boolean indicating if the component passes the analysis.
  * `loadInfo`: Additional load information.

---

## 3. Data Normalization and Processing Considerations

* **Units**: Ensure consistent units across all measurements. For example, convert all heights to feet if that is the standard for your reports.
* **Pole Identifiers**: Use a normalization function to standardize pole identifiers for matching across datasets.
* **Attachment Identification**: When comparing attachments between different designs, use a combination of `owner.id` and `clientItem.description` or `clientItem.type` to accurately track changes.
* **Design Presence**: Not all files may contain both "Measured Design" and "Recommended Design". Implement checks to handle such cases gracefully.

---

## 4. Integration with Data Processing Workflows

When integrating SPIDAcalc JSON data into your processing workflows:

* **Filtering**: Implement functionality to process specific poles based on a provided list of identifiers.
* **Conflict Resolution**: Allow users to specify strategies for handling discrepancies between different data sources (e.g., prefer SPIDAcalc data over another source).
* **Visualization**: Extract geographic data (latitude and longitude) for each pole to enable mapping and spatial analysis.

---

## 5. References

For further information and schema definitions, refer to the [SPIDA Software JSON Interfaces](https://github.com/spidasoftware/schema) repository. or I can actually help w/ this one...

---



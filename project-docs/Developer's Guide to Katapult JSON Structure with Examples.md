# Developer's Guide to Katapult JSON Structure with Examples

**Last Updated:** May 15, 2025
**Source Example:** `ryantest123 (1).json`

## 1. Purpose

This guide is intended for developers and AI agents who need to programmatically interact with Katapult JSON files. It provides a breakdown of common data structures and includes JSON snippets to illustrate where key information can be found. The focus is on extracting data relevant for tasks such as make-ready engineering, pole loading analysis input, and data integration for utility asset management.

## 2. High-Level File Structure

A Katapult JSON file typically represents a collection of field data and associated metadata for a utility infrastructure project. The root is a single JSON object containing several top-level keys.

```json
// Overall Structure (Simplified)
{
  "nodes": { // Poles/structures (See Snippet A)
    "NODE_ID_1": { /* ... pole data ... */ },
    "NODE_ID_2": { /* ... pole data ... */ }
  },
  "connections": { // Spans between nodes (See Snippet F)
    "CONNECTION_ID_1": { /* ... connection data ... */ },
    "CONNECTION_ID_2": { /* ... connection data ... */ }
  },
  "traces": { // Information about cables/equipment owners and types (See Snippet D)
    "TRACE_ID_1": { /* ... trace data ... */ },
    "TRACE_ID_2": { /* ... trace data ... */ }
  },
  "photos": { // Links photos to nodes/connections and contains annotation data (See Snippet C)
     // Structure can vary; sometimes photo details are in 'photo_summary'
     // In ryantest123 (1).json, photo details are nested under nodes/connections
     // For example: nodes.NODE_ID_1.photos.PHOTO_ID_1.photofirst_data
  },
  "photo_summary": { // Alternative location for detailed photo annotation data
    "PHOTO_ID_1": { /* ... detailed photo data including annotations ... */ }
  }
  // ... other top-level keys like 'job_creator', 'job_description', 'equipments', etc.
}

Key Relationships:nodes (poles) are central.nodes have photos associated with them.photos (specifically photofirst_data within them) contain wire and equipment annotations.These annotations have a _trace ID, which links to the traces object.The traces object provides the company (owner) and cable_type (description) for an attachment.connections link two nodes and have sections which can also have associated photos for mid-span details.3. Key Data Structures & Examples3.1. Node (Pole/Structure) DataPurpose: Basic information about each pole, its location, and attributes.Path: katapult_data['nodes'][NODE_ID]Snippet A: Node Object Example - From katapult_data['nodes']['-OJ_PMjpiNrD4UyT0JSz']

{
  "_created": {
    "method": "desktop",
    "timestamp": 1740089454603, // Timestamp (milliseconds since epoch)
    "uid": "kbNvEEKwX8cbpmlJK8Xk9Lsux562"
  },
  "attributes": { // **CRITICAL: Contains most descriptive data (See Snippet B)**
    // ... various attributes ...
  },
  "connections": { // Object listing connection_ids attached to this node
    "-OJ_PU-ftGPy7TovEc5a": true,
    "-OJ_PV-Z0dKkE9a5b9qA": true
  },
  "latitude": 29.290073033920113, // **Pole Latitude**
  "longitude": -98.40965693695148, // **Pole Longitude**
  "photos": { // Object listing photo_ids associated with this node (See Snippet C)
    "e81cf8fa-2752-4f48-87ac-8d0b7dad557e": {
      "_created": { /* ... */ },
      "photofirst_data": { /* ... attachment annotations here ... */ }
    }
  },
  "traces": { // Object listing trace_ids found on this node
    "-OJ_Pj99Rj_9rYnS5g-1": true // Example trace_id
  }
}

Key items for an agent/dev:NODE_ID (the key itself, e.g., "-OJ_PMjpiNrD4UyT0JSz"): Unique identifier for the pole within this JSON.attributes: Object containing detailed pole characteristics.latitude, longitude: Geographic coordinates.photos: Links to photo data where attachments are measured.connections: Links to spans connected to this pole.3.2. Node AttributesPurpose: Detailed characteristics of the pole.Path: katapult_data['nodes'][NODE_ID]['attributes']Snippet B: Node Attributes Example From katapult_data['nodes']['-OJ_PMjpiNrD4UyT0JSz']['attributes']

{
  "Address Object": { // Address details
    "assessment": {
      "formatted_address": "123 Main St, Anytown, TX 78201",
      "street_number": "123",
      "street_name": "Main St",
      "city": "Anytown",
      // ... other address components ...
    }
  },
  "PoleNumber": { // **CRITICAL: Pole Identifier for display/matching**
    "-Imported": "PL370858", // Or "assessment": "PL370858"
    "_created": { /* ... */ }
  },
  "PL_number": { "-Imported": "PL370858", /* ... */ }, // Alternative pole ID
  "electric_pole_tag": { "assessment": "370858", /* ... */ }, // Another pole ID variant
  "PoleOwner": { "assessment": "CPS Energy" }, // **Pole Owner**
  "PoleHeight": { "assessment": "40" }, // **Pole Height (typically feet)**
  "PoleClass": { "assessment": "3" }, // **Pole Class**
  "PoleSpecies": { "assessment": "Southern Pine" }, // **Pole Species**
  "existing_capacity_%": { // **Pole Loading/Capacity**
    "-ONzZgPSoM6vjZpVuZCA": "42.43" // Value is nested under a dynamic key
  },
  "final_passing_capacity_%": {
    "-ONzZigRJczUNfA6wSoG": "41.95"
  },
  "construction_grade_analysis": { "assessment": "B" }, // **Construction Grade**
  "kat_work_type": { "button_added": "make_ready_engineering" }, // Contextual work type
  "mr_state": { "button_added": "engineering_complete" } // Make-ready status
  // ... many other potential attributes ...
}

Key items for an agent/dev:PoleNumber['-Imported'] or PoleNumber['assessment']: Primary pole identifier. Needs normalization.Address Object.assessment.formatted_address: Street address.PoleOwner.assessment: Owner of the pole.PoleHeight.assessment, PoleClass.assessment, PoleSpecies.assessment: Physical characteristics.existing_capacity_% / final_passing_capacity_%: PLA values (extract the nested numerical value).construction_grade_analysis.assessment: Grade of construction.3.3. Photo Data and Wire AnnotationsPurpose: Accessing measured attachment heights and linking them to owners/types.Path: katapult_data['nodes'][NODE_ID]['photos'][PHOTO_ID]['photofirst_data']['wire'] (Based on ryantest123 (1).json structure)Alternative Path: katapult_data['photo_summary'][PHOTO_ID]['photofirst_data']['wire']Snippet C: Photo Wire Annotation Example From a node's ...['photos'][PHOTO_ID]['photofirst_data']['wire']

Example: katapult_data['nodes']['-OJ_PMjpiNrD4UyT0JSz']['photos']['e81cf8fa-2752-4f48-87ac-8d0b7dad557e']['photofirst_data']['wire']['-ONzZgPSoM6vjZpVuZCA']
// (Note: The actual wire data for this specific path might not be in the provided snippet, this is illustrative of structure)

{
  // "-ONzZgPSoM6vjZpVuZCA": { // This is the wire_annotation_id (key)
    "_measured_height": "355.5", // **Attachment Height (typically INCHES)**
    "_trace": "-OJ_Pj99Rj_9rYnS5g-1", // **CRITICAL: Links to 'traces' object (See Snippet D)**
    "original_user_height": "355.5",
    "height_is_approximate": false,
    "height_from_top": false,
    // ... other annotation metadata ...
  // }
}

Key items for an agent/dev:_measured_height: Attachment height, typically in INCHES. This value needs conversion._trace: Crucial ID that links this physical measurement to a specific cable/equipment type and owner via the traces object.3.4. Trace DataPurpose: Defining the owner (company) and type of a measured attachment.Path: katapult_data['traces']['trace_data'][TRACE_ID]Snippet D: Trace Data Example - From katapult_data['traces']['trace_data']['-OJ_Pj99Rj_9rYnS5g-1'] (linked from Snippet C)

{
  "_created": { /* ... */ },
  "cable_type": "Primary", // **Attachment Description/Type**
  "client_id": "some_client_id_string",
  "company": "CPS Energy", // **Attacher Name/Owner**
  "job_id": "-OJ_PImxL3908Pj_SLgs",
  "usageGroup": "POWER", // Broader categorization
  "user_description": "Primary Conductor"
  // ... other trace attributes ...
}
Key items for an agent/dev:company: Attacher Name/Owner of the wire/equipment.cable_type: Specific type/description of the wire/equipment (e.g., "Primary", "Neutral", "Fiber Optic Com", "Telco Com", "CATV Com").usageGroup: General category like "POWER", "COMMUNICATION".3.5. Equipment Annotations (Similar to Wires)Purpose: Details for non-wire equipment attached to poles.Path: katapult_data['nodes'][NODE_ID]['photos'][PHOTO_ID]['photofirst_data']['equipment'](Or katapult_data['photo_summary'][PHOTO_ID]['photofirst_data']['equipment'])Snippet E: Photo Equipment Annotation Example (Conceptual)// From a node's ...['photos'][PHOTO_ID]['photofirst_data']['equipment']
{
  // "EQUIPMENT_ANNOTATION_ID": { // This is the key
    "_measured_height": "280.0", // Height (typically INCHES)
    "_trace": "SOME_EQUIPMENT_TRACE_ID", // Links to 'traces' for owner/type
    "equipment_type_guess": "Transformer" // May have direct type info
    // ... other annotation metadata ...
  // }
}
Key items for an agent/dev:_measured_height: Height (typically INCHES)._trace: Links to traces for owner/type (similar to wires).May contain direct equipment type information.3.6. Connection (Span) DataPurpose: Information about spans between poles, including mid-span details.Path: katapult_data['connections'][CONNECTION_ID]Snippet F: Connection Object Example// From katapult_data['connections']['-OJ_PU-ftGPy7TovEc5a']
{
  "_created": { /* ... */ },
  "attributes": {
    "connection_type": { "button_added": "reference" }, // E.g., "aerial_path", "underground_path"
    "tracing_complete": { "auto": true }
    // ... other connection attributes ...
  },
  "button": "aerial_path", // Overall type of connection
  "node_id_1": "-OJ_PU-d5b_qyvPLb1ox", // **ID of the first connected pole**
  "node_id_2": "-OJ_PMjpiNrD4UyT0JSz", // **ID of the second connected pole**
  "sections": { // **CRITICAL: Details points along the span (See Snippet G)**
    "-OJj4T5K3z3UV0YPI68v": { /* ... section data ... */ }
    // ... other sections ...
  }
}
Key items for an agent/dev:node_id_1, node_id_2: IDs of the poles this connection links.sections: Object containing data for points along the span, crucial for mid-span clearances.button or attributes.connection_type.button_added: Indicates if the span is aerial or underground ("UG").3.7. Connection Section DataPurpose: Geographic points and potential photo links for mid-span measurements.Path: katapult_data['connections'][CONNECTION_ID]['sections'][SECTION_ID]Snippet G: Connection Section Example// From katapult_data['connections']['-OJ_PU-ftGPy7TovEc5a']['sections']['-OJj4T5K3z3UV0YPI68v']
{
  "_created": { /* ... */ },
  "latitude": 29.290058088162137, // **Mid-span point latitude**
  "longitude": -98.40987270576557, // **Mid-span point longitude**
  "photos": { // May link to photos taken at this mid-span point
    "PHOTO_ID_FOR_SECTION": {
      "photofirst_data": { /* ... wire/equipment annotations for mid-span ... */ }
    }
  },
  "sequence": 0 // Order of the section in the span
}
Key items for an agent/dev:latitude, longitude: Coordinates of this point in the span.photos: If present, this object links to photos taken at this mid-span location. These photos would contain photofirst_data with wire annotations, allowing for calculation of mid-span clearances using the same logic as pole attachments (Snippets C, D).4. Important Considerations for Developers & AI AgentsUnits: Height measurements from Katapult photos (_measured_height) are typically in INCHES. Always convert these to a consistent project-wide unit (e.g., feet) for calculations and reporting using processor.height_utils.py. Pole height from attributes is often in feet.Data Path Variability:The exact path to photofirst_data (containing wire/equipment annotations) can sometimes vary. It might be directly nested under nodes[...]['photos'][...] as in ryantest123 (1).json, or it might be in a top-level photo_summary[PHOTO_ID]. Code should be flexible or configurable to check potential paths.Attribute values (like PoleNumber) can be under an assessment key or an -Imported key. Check for both.Normalization:Pole Identifiers: Crucial for matching with other systems (like SPIDAcalc) or for user input. Use processor.utils.normalize_pole_id() from your project.Attacher Names (traces.trace_data.company) & Cable Types (traces.trace_data.cable_type): Consider normalizing these (e.g., "ATT" vs "AT&T") using mappings (e.g., in processor.constants.py) for consistent reporting and analysis.Dynamic Keys: Some objects, like existing_capacity_% under node attributes, have their actual value nested under a dynamically generated key (often a GUID). Your code will need to iterate Object.values() or Object.keys() to get to the actual data point.Optional Fields: Not all attributes or nested objects will be present for every element. Always code defensively using dict.get() with default values or try-except blocks to prevent KeyError exceptions.Constants: Use a dedicated module like processor.constants.py for defining known string literals (e.g., specific company names like "CPS Energy" for identifying utility lines, critical cable_type values like "Neutral", "Primary") to avoid hardcoding and improve maintainability.This guide and the provided snippets should offer a comprehensive starting point for understanding and extracting the necessary data from Katapult JSON files for your Make
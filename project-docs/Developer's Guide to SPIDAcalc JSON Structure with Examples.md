# Developer's Guide to SPIDAcalc JSON Structure with Examples

**Last Updated:** May 15, 2025
**Source Example:** `CPS_6457E_03_SPIDAcalc.json` (Version 11 schema)

## 1. Purpose

This guide is intended for developers and AI agents who need to programmatically interact with SPIDAcalc JSON files. It provides a breakdown of the common data structures and includes JSON snippets to illustrate where key information can be found. The focus is on extracting data relevant for tasks such as make-ready engineering, structural analysis review, and data integration.

## 2. High-Level File Structure

A SPIDAcalc JSON file typically represents a project containing one or more "leads," and each lead contains multiple "locations" (poles/structures). Each location can have several "designs" (e.g., existing vs. proposed states).

```json
// Overall Structure
{
  "label": "PROJECT_NAME", // (See Snippet A)
  "version": 11,
  // ... other project metadata ...
  "leads": [ // Array of leads (See Snippet B)
    {
      "label": "Lead",
      "locations": [ // Array of locations/poles (See Snippet B)
        {
          "label": "POLE_IDENTIFIER_1", // (See Snippet B)
          // ... location metadata ...
          "designs": [ // Array of designs for this pole (See Snippet C)
            {
              "label": "Measured Design", // Or "Recommended Design", etc.
              "structure": { // Contains pole, wires, equipment for this design (See Snippets D, E, F)
                "pole": { /* ... */ },
                "wires": [ /* ... */ ],
                "equipments": [ /* ... */ ]
              }
            }
          ],
          "poleResults": [ /* ... (See Snippet G) ... */ ]
        }
        // ... more locations ...
      ]
    }
    // ... more leads (rarely) ...
  ]
}
3. Key Data Structures & Examples3.1. Project InformationPurpose: General context about the SPIDAcalc file.Path: Root of the JSON object (spidacalc_data)Snippet A: Root Project Information{
  "label": "CPS_6457E_03",
  "dateModified": 1746193395463, // Timestamp (milliseconds since epoch)
  "clientFile": "TechServ_Light C_Static_Tension.client",
  "version": 11, // SPIDAcalc schema version
  "engineer": "Taylor Larsen",
  "comments": "",
  "generalLocation": "",
  "address": {
    "number": "", "street": "", "city": "",
    "county": "", "state": "", "zip_code": ""
  }
  // ... other project-level fields ...
}
Key items for an agent/dev:label: Project identifier.dateModified: For versioning or recency checks.version: Important if handling multiple SPIDAcalc schema versions.3.2. Leads and Locations (Poles)Purpose: Navigating to individual pole data.Path: spidacalc_data['leads'][lead_index]['locations'][location_index]Snippet B: Lead and Location Structure// From spidacalc_data['leads'][0]
{
  "label": "Lead", // Typically just "Lead"
  "locations": [
    {
      "label": "1-PL410620", // **CRITICAL: Pole Identifier for matching**
      "guid": "c3a0a1e6-1111-4e1e-872c-exampleguid1", // Internal SPIDA GUID for the location
      "latitude": null, // Often null at this level, check design or Katapult
      "longitude": null,
      "designs": [ /* ... see Snippet C ... */ ],
      "poleResults": [ /* ... see Snippet G ... */ ],
      "poleTags": []
    },
    {
      "label": "2-PL398491",
      // ... similar structure for other poles ...
    }
  ]
}
Key items for an agent/dev:locations[i].label: Primary identifier for the pole. Needs normalization (e.g., strip "1-") to match with other systems like Katapult.locations[i].guid: SPIDA's internal unique ID for this pole structure.locations[i].designs: Array holding the different states/analyses of this pole.3.3. Design ScenariosPurpose: Accessing specific states of a pole (e.g., existing vs. proposed).Path: location_data['designs'][design_index]Snippet C: Design Object ("Measured Design" Example)// From location_data['designs'][0] (assuming it's the "Measured Design")
{
  "label": "Measured Design", // **CRITICAL: Identifies the state (e.g., "Measured Design", "Recommended Design")**
  "layerType": "Measured", // Correlates with the label
  "guid": "d7b0b2f7-2222-4f2f-983d-exampleguid2", // Internal SPIDA GUID for this design
  "structure": { /* ... Contains pole, wires, equipment for THIS design ... See Snippets D, E, F ... */ },
  "analysisDate": 1746193326946,
  "notes": ""
}
Key items for an agent/dev:design.label: Essential for distinguishing between "Measured Design" (existing), "Recommended Design" (proposed), or other custom designs.design.structure: The object containing all physical components and their attachments for this specific design scenario.3.4. Pole Attributes (within a Design)Purpose: Getting physical characteristics of the pole itself for a specific design.Path: design_data['structure']['pole']Snippet D: Pole Structure Attributes// From design_data['structure']['pole']
{
  "guid": "e8c0c3g8-3333-4g3g-a94e-exampleguid3",
  "externalId": null, // Can be an ID from another system if populated
  "clientItem": { // Describes the pole type from the client's library
    "aliases": [{"id": "40-3"}], // Often Height-Class (e.g., 40ft, Class 3)
    "shape": "ROUND",
    "materialCategory": "WOOD",
    "classOfPole": "3",
    "species": "Southern Pine",
    "height": {"unit": "METRE", "value": 12.192000000000002}, // **Pole Height & Unit**
    "taper": 0.122, // meters per meter
    "groundlineCircumference": {"unit": "METRE", "value": 1.0138859686307006},
    "tipCircumference": {"unit": "METRE", "value": 0.5842},
    "density": {"unit": "KILOGRAM_PER_CUBIC_METRE", "value": 624.7200715844455},
    "maximumAllowableStress": {"unit": "PASCAL", "value": 5.515805834534689E7},
    "modulus": {"unit": "PASCAL", "value": 1.241056312770305E10} // Modulus of Elasticity
  },
  "embedment": {"unit": "METRE", "value": 1.8288}, // How deep the pole is set
  "lengthInstalled": {"unit": "METRE", "value": 12.192} // Same as height for non-custom poles
}
Key items for an agent/dev:clientItem.height.value and clientItem.height.unit: Pole's total length/height and its unit (typically METRE).clientItem.classOfPole: Pole class.clientItem.species: Pole material/species.clientItem.aliases[0].id: Often a shorthand for height-class.3.5. Wire Attachments (within a Design)Purpose: Getting details of individual wire attachments, their owners, and heights for a specific design.Path: design_data['structure']['wires'] (This is an array)Snippet E: Wire Attachment Example// From design_data['structure']['wires'][0]
{
  "id": "Wire#1", // Internal SPIDA ID for this wire on this pole/design
  "guid": "f9d0d4h9-4444-4h4h-ba5f-exampleguid4",
  "owner": {
    "industry": "UTILITY", // Or "COMMUNICATION", "MUNICIPAL", etc.
    "id": "CPS Energy" // **Attacher Name/Owner**
  },
  "clientItem": { // Describes the wire type from the client's library
    "type": "POWER_TRIPLEX", // Broad category
    "size": "336.4 ACSR", // Specific size
    "description": "336.4 ACSR - Merlin", // **Detailed Attachment Description**
    "material": "ACSR",
    "diameter": {"unit": "METRE", "value": 0.0183134},
    "weight": {"unit": "NEWTON_PER_METRE", "value": 6.7103960792}
  },
  "attachmentHeight": {
    "unit": "METRE", // **Unit for height**
    "value": 11.2268 // **Attachment Height from pole top or ground (check SPIDA settings)**
  },
  "attachmentStyle": "SIDE_POST_INSULATOR_WITH_CLAMP",
  "horizontalOffset": {"unit": "METRE", "value": 0.3048},
  "verticalOffset": {"unit": "METRE", "value": 0.0},
  "azimuth": {"unit": "DEGREE", "value": 0.0}, // Relative to a span direction
  "usageGroup": "POWER" // Category (POWER, COMMUNICATION, NEUTRAL, GUY, etc.)
}
Key items for an agent/dev:owner.id: Attacher Name.clientItem.description or clientItem.size: Attachment Description/Type.attachmentHeight.value and attachmentHeight.unit: Attachment Height and its unit (typically METRE).id: SPIDA's internal ID, useful for comparing the same attachment between "Measured" and "Recommended" designs.usageGroup: Helps categorize the attachment type.3.6. Equipment Attachments (within a Design)Purpose: Getting details of non-wire equipment, their owners, and heights for a specific design.Path: design_data['structure']['equipments'] (This is an array)Snippet F: Equipment Attachment Example// From design_data['structure']['equipments'][0]
{
  "id": "Equip#1", // Internal SPIDA ID
  "guid": "g0e0e5i0-5555-5i5i-cb6g-exampleguid5",
  "owner": {
    "industry": "UTILITY",
    "id": "CPS Energy" // **Attacher Name/Owner**
  },
  "clientItem": { // Describes the equipment type from the client's library
    "type": "TRANSFORMER", // **Attachment Type**
    "size": "25 kVA Single Phase", // **Attachment Description/Size**
    "weight": {"unit": "KILOGRAM", "value": 158.7573295},
    "height": {"unit": "METRE", "value": 0.6096} // Physical height of the equipment unit itself
  },
  "attachmentHeight": {
    "unit": "METRE", // **Unit for attachment height**
    "value": 9.2964 // **Attachment Height on pole**
  },
  "attachmentStyle": "BOLTED_THROUGH",
  "verticalOffset": {"unit": "METRE", "value": 0.0},
  "azimuth": {"unit": "DEGREE", "value": 0.0}
}
Key items for an agent/dev:owner.id: Attacher Name.clientItem.type and/or clientItem.size: Attachment Description/Type.attachmentHeight.value and attachmentHeight.unit: Attachment Height and its unit (typically METRE).id: SPIDA's internal ID.3.7. Pole Analysis ResultsPurpose: Understanding the structural analysis outcomes for the pole under specific designs/load cases.Path: location_data['poleResults'] (This is an array)Snippet G: Pole Analysis Result Example// From location_data['poleResults'][0]
{
  "actual": 42.55364272410659, // The calculated value (e.g., stress percentage)
  "allowable": 100.0, // The allowable limit for this value
  "unit": "PERCENT", // Unit of 'actual' and 'allowable'
  "analysisDate": 1746193326946,
  "component": "Pole", // What was analyzed (Pole, Guy, Anchor, specific Insulator#)
  "loadInfo": "Light - Grade C", // The NESC load case and construction grade
  "passes": true, // Boolean indicating if 'actual' is within 'allowable'
  "analysisType": "STRESS", // Type of analysis (STRESS, FORCE, TENSION)
  "designLabel": "Measured Design" // Which design this result pertains to
}
Key items for an agent/dev:component: What part of the structure the result is for.analysisType: The type of check performed.actual & allowable: The result and its limit.passes: Quick pass/fail status.loadInfo: Provides context on loading conditions.designLabel: Links the result back to a specific design scenario.4. Important Considerations for Developers & AI AgentsUnits: Be extremely careful with units. SPIDAcalc typically uses METERS for heights and dimensions. Your application will likely need to convert these (e.g., to feet) using processor.height_utils.py. Always check the ['unit'] field accompanying a value.Design Labels: The exact labels for designs (e.g., "Measured Design," "Recommended Design") are critical. Ensure your code correctly identifies the designs it needs to process.Attachment Identification: For comparing an attachment between "Measured" and "Recommended" states, the internal id (e.g., "Wire#1") is often the best link if it's preserved. If not, a composite key of owner and a normalized description might be needed.Normalization:Pole Identifiers (location.label): Must be normalized to match identifiers from other systems (e.g., Katapult).Attacher Names (owner.id) & Descriptions (clientItem.description/size/type): Consider normalizing these for consistent grouping and comparison, possibly using mappings defined in processor.constants.py.Schema Version: The example CPS_6457E_03_SPIDAcalc.json is based on version: 11. If processing files from different SPIDAcalc versions, be aware that paths or field names might vary. Robust code should check for key existence before access (e.g., using dict.get()).Optional Fields: Not all fields shown in examples will be present in every SPIDAcalc JSON or for every element. Code defensively.This guide and the snippets should provide a solid foundation for parsing and utilizing
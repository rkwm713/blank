# JSON Path Standardization Reference

This document serves as the single source of truth for all JSON paths used to extract data from Katapult and SPIDAcalc files. All other documentation should reference these paths to maintain consistency.

## Katapult JSON Paths

### Pole/Node Data

| Data Element | Standard JSON Path | Example Value |
|--------------|-------------------|---------------|
| Node ID | `nodes.<node_id>` | `-OJ_PMjpiNrD4UyT0JSz` |
| Pole Number | `nodes.<node_id>.attributes.PoleNumber['-Imported']` | `PL410620` |
| Pole Owner | `nodes.<node_id>.attributes.PoleOwner.assessment` | `CPS Energy` |
| Pole Height | `nodes.<node_id>.attributes.PoleHeight.assessment` | `40` |
| Pole Class | `nodes.<node_id>.attributes.PoleClass.assessment` | `3` |
| Pole Species | `nodes.<node_id>.attributes.PoleSpecies.assessment` | `Southern Pine` |
| Latitude | `nodes.<node_id>.latitude` | `29.290073033920113` |
| Longitude | `nodes.<node_id>.longitude` | `-98.40965693695148` |
| Existing Capacity | `nodes.<node_id>.attributes.existing_capacity_%.<dynamic_key>` | `42.43` |
| Final Capacity | `nodes.<node_id>.attributes.final_passing_capacity_%.<dynamic_key>` | `41.95` |
| Construction Grade | `nodes.<node_id>.attributes.construction_grade_analysis.assessment` | `C` |

### Attachment Data

| Data Element | Standard JSON Path | Example Value |
|--------------|-------------------|---------------|
| Wire Height | `nodes.<node_id>.photos.<photo_id>.photofirst_data.wire.<wire_id>._measured_height` | `330.61` |
| Equipment Height | `nodes.<node_id>.photos.<photo_id>.photofirst_data.equipment.<equip_id>._measured_height` | `280.0` |
| Wire Type | `traces.trace_data.<trace_id>.cable_type` | `Fiber Optic Com` |
| Owner/Company | `traces.trace_data.<trace_id>.company` | `AT&T` |
| Usage Group | `traces.trace_data.<trace_id>.usageGroup` | `COMMUNICATION` |
| Make Ready Move | `nodes.<node_id>.photos.<photo_id>.photofirst_data.wire.<wire_id>.mr_move` | `24.0` |
| Proposed Flag | `nodes.<node_id>.photos.<photo_id>.photofirst_data.wire.<wire_id>.proposed` | `true` |

### Connection Data

| Data Element | Standard JSON Path | Example Value |
|--------------|-------------------|---------------|
| Connection ID | `connections.<connection_id>` | `-OJ_QN1_yILRwv5lKaw7` |
| From Node | `connections.<connection_id>.node_id_1` | `-OJ_QN1ZoFM8EVIZXesW` |
| To Node | `connections.<connection_id>.node_id_2` | `-OJ_QLUJ-TR4p9hLQz72` |
| Connection Type | `connections.<connection_id>.button` | `aerial_path` |
| Midspan Height | `connections.<connection_id>.sections.<section_id>.midspanHeight_in` | `177.95` |
| Section Latitude | `connections.<connection_id>.sections.<section_id>.latitude` | `29.290058088162137` |
| Section Longitude | `connections.<connection_id>.sections.<section_id>.longitude` | `-98.40987270576557` |

## SPIDAcalc JSON Paths

### Pole Data

| Data Element | Standard JSON Path | Example Value |
|--------------|-------------------|---------------|
| Pole ID | `leads[0].locations[i].label` | `1-PL410620` |
| Clean Pole ID | `leads[0].locations[i].label.substring(2)` (if starts with "1-") | `PL410620` |
| Location GUID | `leads[0].locations[i].guid` | `c3a0a1e6-1111-4e1e-872c-exampleguid1` |
| Pole Alias | `leads[0].locations[i].designs[?(@.label=="Measured Design")].structure.pole.clientItem.aliases[0].id` | `40-3` |
| Pole Class | `leads[0].locations[i].designs[?(@.label=="Measured Design")].structure.pole.clientItem.classOfPole` | `3` |
| Pole Height (m) | `leads[0].locations[i].designs[?(@.label=="Measured Design")].structure.pole.clientItem.height.value` | `12.192000000000002` |
| Pole Species | `leads[0].locations[i].designs[?(@.label=="Measured Design")].structure.pole.clientItem.species` | `Southern Pine` |
| Latitude | `leads[0].locations[i].latitude` | (may be null) |
| Longitude | `leads[0].locations[i].longitude` | (may be null) |

### Analysis Results

| Data Element | Standard JSON Path | Example Value |
|--------------|-------------------|---------------|
| PLA Percent | `leads[0].locations[i].poleResults[?(@.component=="Pole" && @.analysisType=="STRESS")].actual` | `42.55364272410659` |
| Construction Grade | `leads[0].locations[i].poleResults[?(@.component=="Pole")].loadInfo` | `Light - Grade C` |
| Design Type | `leads[0].locations[i].designs[j].label` | `"Measured Design"` or `"Recommended Design"` |

### Attachment Data

| Data Element | Standard JSON Path | Example Value |
|--------------|-------------------|---------------|
| Wire ID | `leads[0].locations[i].designs[j].structure.wires[k].id` | `Wire#1` |
| Wire GUID | `leads[0].locations[i].designs[j].structure.wires[k].guid` | `f9d0d4h9-4444-4h4h-ba5f-exampleguid4` |
| Wire Owner | `leads[0].locations[i].designs[j].structure.wires[k].owner.id` | `CPS Energy` |
| Wire Type | `leads[0].locations[i].designs[j].structure.wires[k].clientItem.type` | `POWER_TRIPLEX` |
| Wire Description | `leads[0].locations[i].designs[j].structure.wires[k].clientItem.description` | `336.4 ACSR - Merlin` |
| Wire Height (m) | `leads[0].locations[i].designs[j].structure.wires[k].attachmentHeight.value` | `11.2268` |
| Equipment ID | `leads[0].locations[i].designs[j].structure.equipments[m].id` | `Equip#1` |
| Equipment Owner | `leads[0].locations[i].designs[j].structure.equipments[m].owner.id` | `CPS Energy` |
| Equipment Type | `leads[0].locations[i].designs[j].structure.equipments[m].clientItem.type` | `TRANSFORMER` |
| Equipment Description | `leads[0].locations[i].designs[j].structure.equipments[m].clientItem.size` | `25 kVA Single Phase` |
| Equipment Height (m) | `leads[0].locations[i].designs[j].structure.equipments[m].attachmentHeight.value` | `9.2964` |

## Helper Functions

### Extract Dynamic Value (Katapult)

```javascript
function extractDynamicValue(obj, fieldName) {
  if (!obj[fieldName]) return null;
  
  for (let key in obj[fieldName]) {
    // Skip metadata keys
    if (key === '_created' || key === '-Imported' || key === 'assessment') continue;
    return obj[fieldName][key];
  }
  return null;
}
```

### Finding SPIDA Pole by externalId

```javascript
function findPoleByExternalId(spidaJson, externalId) {
  for (const location of spidaJson.leads[0].locations) {
    let locationId = location.label;
    
    // Handle "1-" prefix if present
    if (locationId.startsWith("1-")) {
      locationId = locationId.substring(2);
    }
    
    if (locationId === externalId) {
      return location;
    }
  }
  return null;
}
```

### Finding Katapult Node by Pole Number

```javascript
function findNodeByPoleNumber(katapultJson, poleNumber) {
  for (const nodeId in katapultJson.nodes) {
    const node = katapultJson.nodes[nodeId];
    
    // Check for pole number in different possible locations
    const attributes = node.attributes || {};
    const poleNumPaths = [
      attributes.PoleNumber?.['-Imported'],
      attributes.PoleNumber?.assessment,
      attributes.PL_number?.['-Imported'],
      attributes.electric_pole_tag?.['-Imported']
    ];
    
    if (poleNumPaths.includes(poleNumber)) {
      return node;
    }
  }
  return null;
}
```

## Notes on Path Semantics

1. In Katapult, many fields use dynamic keys (like GUIDs) that must be extracted using a helper function
2. In SPIDAcalc, pole IDs may have a "1-" prefix that should be removed for consistency
3. SPIDAcalc uses METERS for heights while Katapult uses INCHES
4. For SPIDAcalc data, always use the location's `guid` to reference the pole internally, not the `id` 
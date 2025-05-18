# Make-Ready Report Generator Specification

> This document consolidates all column-level mappings, pole selection rules, and data extraction algorithms for generating the Make-Ready Excel report from SPIDAcalc and Katapult JSON exports.

---

## Overview

The web application ingests SPIDAcalc v10 and Katapult v8/9 JSON files, merges existing infrastructure data with proposed make-ready actions, and outputs a formatted Excel workbook matching the CPS standard Make-Ready template. Each column in the report is populated by deterministic logic outlined below.

---

## Pole Selection (Columns A–D)

**Primary poles** (operation sections) are **all poles listed in SPIDAcalc**, regardless of activity. Their **action codes**, however, derive from Katapult:

* **(I) Installing**: any attachment with `proposed == true` or new install.
* **(R) Removing**: present in SPIDAcalc but missing in Katapult.
* **(E) Existing**: only `mr_move` relocations.

**Context poles** (From/To rows and reference headers) include any Katapult connection endpoint (even if not in SPIDAcalc).

### Algorithm (simplified)

```python
# 1. Primary poles = {p.externalId for p in spida.poles}
# 2. Determine action per pole by scanning katapult attachments and mr_move
# 3. For each primary pole:
#    - Write operation header (Cols A–I)
#    - List attachments (Cols L–O)
#    - Inspect kat.connections touching this pole for From/To and reference spans
```

---

## Column B – Attachment Action

| Code | Description                                                                          |
| ---- | ------------------------------------------------------------------------------------ |
| (I)  | Installing – at least one new attachment (`proposed == true`) or absent in SPIDAcalc |
| (R)  | Removing   – no installs, at least one SPIDA-only attachment missing in Katapult     |
| (E)  | Existing   – all attachments remain (moves only)                                     |

*Attachment-level flags collapse to one code for the merged header across A–I.*

---

## Column C – Pole Owner

For all CPS Energy projects, **Pole Owner** is hard‑coded to:

```
CPS
```

No JSON lookup required.

---

## Column D – Pole

Source: SPIDAcalc → `pole.externalId` (fallback to Katapult `nodes[*].attributes.pole_tag['-Imported'].tagtext`).
Normalize to uppercase, prefix `PL` if missing, trim whitespace.

### Examples

* SPIDA `externalId = 'PL398491'` → `PL398491`
* Katapult tagtext `'370858'` → `PL370858`

---

## Column E – Pole Structure

Compose `<alias> <species>`:

* **SPIDAcalc**: `aliases[0].id` + `species` (e.g. `45-2` + `Southern Pine`).
* Fallback: Katapult `pole_height` + `pole_class`, default species `Southern Pine`.

### Project CPS 6457E 03 Mapping

| Pole #   | Pole Structure     |
| -------- | ------------------ |
| PL410620 | 40-4 Southern Pine |
| PL398491 | 45-2 Southern Pine |
| PL389359 | 45-4 Southern Pine |
| PL404474 | 40-3 Southern Pine |
| PL900997 | 45-2 Southern Pine |
| PL370858 | 45-2 Southern Pine |

---

## Columns J & K – Lowest Mid-Span Heights

For each **span** (From → To):

* **J**: lowest comm-space (`owner != 'CPS Energy'`) mid-span height.
* **K**: lowest CPS-electrical (`owner == 'CPS Energy'`) mid-span height.

Extract from Katapult `connection.sections[*].midspanHeight_in`, grouped by span, minimum per owner class, converted to `ft'-in"`; write `NA` if absent.

### Sample (CPS 6457E 03)

| Span                 | J – Comm | K – CPS |
| -------------------- | -------- | ------- |
| PL410620 → PL398491  | 14'-10"  | 23'-10" |
| PL398491 → PL401451  | NA       | NA      |
| PL389359 → PL404474  | 17'-8"   | 22'-8"  |
| PL404474 → PL900997  | 19'-6"   | 23'-8"  |
| PL900997 → PL398490  | NA       | NA      |
| PL370858 → PL3268481 | 20'-8"   | 21'-7"  |

---

## Columns L–O – Make-Ready Data Block

Under the **Make Ready Data → Attachment Height** header:

* **L – Attacher Description**: Katapult `desc` (fallback SPIDA).
* **M – Existing**: SPIDA `existingHeight_in` or Katapult `measured_height_in`.
* **N – Proposed**: new install height (`measured_height_in`) or `existing + mr_move`.
* **O – Mid-Span**: Katapult mid-span clearance; `UG` if underground.

### Row Rules

1. Sort by existing (or proposed) height descending.
2. Use per-attachment rules:

   * Existing/no move: M filled, N/O blank.
   * Move: M original, N new height.
   * New install: N height, O mid-span if present.
3. Omit removals (handled by `(R)` action).

### Subsections

Below the main block, insert:

* **Reference spans**: `Ref (<Direction>) to <Pole>` headers (orange/purple), list **all** attachments with existing & mid-span.
* **Backspan**: analogous block if `backspan == true`.
* **From/To rows**: light-blue merged rows marking span endpoints.

---

## Unit Tests & Revision History

* **Unit tests** cover each column’s edge cases (see per-section examples).
* **Revision history** tracks updates per section (see individual docs for details).

---

*This specification is the single source of truth for the AI agent and development team.*

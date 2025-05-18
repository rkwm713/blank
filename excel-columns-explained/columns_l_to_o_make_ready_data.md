# Columns L – O – Make‑Ready Data Block

> **Scope**  Defines how the generator fills the four columns that appear under the blue **“Make Ready Data → Attachment Height”** header.
>
> | Column | Excel heading        | Purpose                                                                                                   |
> | ------ | -------------------- | --------------------------------------------------------------------------------------------------------- |
> | **L**  | Attacher Description | Text label of the wire/equipment on the pole/span                                                         |
> | **M**  | Existing             | Pre‑make‑ready attachment height (ft‑in)                                                                  |
> | **N**  | Proposed             | Post‑make‑ready attachment height (ft‑in) if it will move **or** height of brand‑new install              |
> | **O**  | Mid‑Span Proposed    | Proposed mid‑span clearance of the same attachment *in the same span* (or `UG` when it dives underground) |

---

## 1 Data sources

| Value                    | Primary file / path                                                                                                           | Notes                                                                         |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| **Attacher Description** | Katapult → `desc` <br>Fallback: SPIDA `desc`                                                                                  | Keep verbatim (do **not** abbreviate).                                        |
| **Existing height**      | SPIDA → `attachments[*].existingHeight_in`<br>or Katapult `measured_height_in`                                                | Inches → ft‑in via `inches_to_ft_in()`; blank if attachment is *new install*. |
| **Proposed height**      | Katapult<br>• `proposed == true` → `measured_height_in`  (new install)<br>• `mr_move` → `existing + mr_move`  (raise / lower) | Blank if no change and not new.                                               |
| **Mid‑Span Proposed**    | Katapult `connection.sections[*].midspanHeight_in` that matches `wire_id` **after** adjustment                                | If the span goes underground flag **`UG`** instead of a number.               |

> SPIDAcalc does not track proposed heights; Katapult is authoritative for moves & installs.

---

## 2 Row generation order

1. **Sort attachments** by `existingHeight_in` **descending** (tallest first).  If existing blank (new install) use proposed height.
2. After listing all on‑pole attachments, insert **reference blocks** and **Backspan** headers exactly where Katapult flags `connection.button_added == "reference"` or `backspan == true`.
3. Leave a single empty row between operation groups (mirrors CPS template).

---

## 3 Attachment‑level action rules

| Scenario                 | Column M (Existing) | Column N (Proposed) | Column O (Mid‑Span) | Note                              |
| ------------------------ | ------------------- | ------------------- | ------------------- | --------------------------------- |
| **Existing, no move**    | height              | *(blank)*           | *(blank)*           | normal row                        |
| **Existing, raised**     | original ht         | new ht              | *(blank)*           | moves up                          |
| **Existing, lowered**    | original ht         | new ht              | *(blank)*           | moves down                        |
| **New aerial install**   | *(blank)*           | height              | mid‑span            | install                           |
| **New UG install**       | *(blank)*           | height              | `UG`                | riser/UG                          |
| **Removal**              | height              | *(blank)*           | *(blank)*           | not listed                        |
| **Reference attachment** | existing ht         | *(blank)*           | mid‑span            | listed under orange/purple header |
| **Reference + move**     | existing ht         | proposed ht         | mid‑span (proposed) | rare                              |

> **Update 2025‑05‑19** – Reference blocks now list **all** attachments with their mid‑span clearances so reviewers can verify no residual violations.

## 4 Algorithm (pseudo‑Python)

```python
rows = []
# primary on‑pole attachments first …

for ref in reference_spans:  # orange / purple blocks
    rows.append({
        "L": f"Ref ({ref.dir}) to {ref.to_tag}",
        "style": ref.colour,
        "merge": "L:O",
    })
    for att in sorted(ref.attachments, key=lambda a: a.sort_height, reverse=True):
        rows.append({
            "L": att.description,
            "M": to_ft(att.existing) if att.existing else "",
            "N": to_ft(att.proposed) if att.proposed else "",
            "O": "UG" if att.goes_underground else to_ft(att.midspan) if att.midspan else "",
        })
```

 Algorithm (pseudo‑Python)

```python
rows = []
for att in sorted(attachments, key=lambda a: a.sort_height, reverse=True):
    r = {}
    r["L"] = att.description
    r["M"] = to_ft(att.existing) if att.existing else ""
    r["N"] = to_ft(att.proposed) if att.proposed else ""
    if att.midspan is not None:
        r["O"] = to_ft(att.midspan)
    elif att.goes_underground:
        r["O"] = "UG"
    else:
        r["O"] = ""
    rows.append(r)

# reference blocks
for ref in reference_spans:
    rows.append({"L": f"Ref ({ref.dir}) to {ref.to_tag}", "style": ref.colour, "merge": "L:O"})
    for att in ref.attachments:
        ... (same filling logic)
```

---

## 5 Sample excerpt – PL410620 (matches screenshot)

| L Attacher                   | M Existing | N Proposed | O Mid‑Span |
| ---------------------------- | ---------- | ---------- | ---------- |
| Neutral                      | 29'-6"     |            |            |
| CPS Supply Fiber             | 28'-0"     |            |            |
| Charter/Spectrum Fiber Optic |            | 24'-7"     | 21'-1"     |
| AT\&T Fiber Optic Com        | 23'-7"     |            |            |
| AT\&T Telco Com              | 22'-4"     |            |            |
| AT\&T Com Drop               | 21'-5"     |            | 15'-10"    |

*(Empty row follows, then the next pole’s block.)*

---

## 6 Subsections: Main vs Reference Blocks

Once all attachments and their mid-span heights have been listed for the **primary span** (the current SPIDA pole → next SPIDA pole), the generator creates additional **subsections** to capture other span- and reference-related data.  These appear directly below the main block before the empty row:

* **Reference spans** (orange/purple):  For each Katapult connection flagged `button_added == "reference"`, insert a merged header `Ref (<Direction>) to <PoleTag>` shaded appropriately. Then list **all** attachments on that span—each with its existing height *and* its mid-span height—so reviewers can verify no clearance violations remain.
* **Backspan**:  If a connection has `backspan == true`, insert a header labeled `Backspan` (light-blue or distinct style) and list its attachments similarly.
* **From/To rows**:  After sub-blocks, the standard light‑blue *From Pole* / *To Pole* rows mark the endpoints of each span section.  These use tags from the Katapult JSON, even if the endpoint pole isn’t in SPIDAcalc.

> 💡 **Key**: Unlike the main section (which only shows on-pole data and *proposed* mid-span), subsections show **both** existing and proposed mid-span values for every attachment in that span.  This ensures complete traceability and clear verification.

## 7 Edge‑case handling

| Case                                           | Handling                                  | Log key                      |
| ---------------------------------------------- | ----------------------------------------- | ---------------------------- |
| Mid‑span value < 120 in                        | Flag critical in QC sheet                 | `MIDSPAN_CLEARANCE_CRITICAL` |
| Proposed height ↓ below existing               | Allowed (lowering), but highlight QC cell | `LOWER_PROPOSED`             |
| Description duplicates with multiple instances | List each instance on its own row         | —                            |
| New install but mid‑span missing               | `UG` if underground; else blank           | `MIDSPAN_MISSING`            |

---

## 7 Unit‑test skeleton

```python
@pytest.mark.parametrize("existing,proposed,mid,exp_m,exp_n,exp_o", [
    (336, None, None, "28'-0\"", "", ""),
    (295, 253, 253, "24'-7\"", "21'-1\"", "21'-1\""),
    (None, 257, 190, "", "21'-5\"", "15'-10\""),
])
```

---

## 8 Revision history

| Date       | Version | Notes                                                       |
| ---------- | ------- | ----------------------------------------------------------- |
| 2025‑05‑19 | v1.0    | Initial rules for L‑O generation, aligns with CPS template. |

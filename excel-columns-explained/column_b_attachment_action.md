# Column B – Attachment Action

> **Purpose** Define how the generator determines the **operation-level** code placed in Column B (`(I) Installing`, `(R) Removing`, or `(E) Existing`). This code represents the highest-priority action occurring at the pole, with installations taking precedence over removals, which take precedence over existing-only actions.

---

## 1 Definition

| Code    | Meaning    | When to use                                                                                            | Priority |
| ------- | ---------- | ------------------------------------------------------------------------------------------------------ | -------- |
| **(I)** | Installing | At least one attachment is new (`proposed == true` OR exists in Katapult but not in SPIDAcalc)         | Highest  |
| **(R)** | Removing   | No installs, but ≥1 removal (exists in SPIDAcalc but not in Katapult OR explicit `remove == true`)     | Middle   |
| **(E)** | Existing   | All attachments remain; only moves or make-ready relocations (with `mr_move` attribute in Katapult)    | Lowest   |

The chosen code is written once in Column B and vertically merged across Columns A-I for each pole operation section.

---

## 2 Data Sources & Recognition Logic

| Source     | Signal                                       | JSON Path(s)                                      | Interpreted As |
| ---------- | -------------------------------------------- | ------------------------------------------------- | -------------- |
| Katapult   | `proposed == true`                           | `nodes[*].attachments.*[*].proposed`              | **(I)** Install |
| Both       | In Katapult but not in SPIDAcalc             | Compare attachment IDs between files              | **(I)** Install |
| Both       | In SPIDAcalc but not in Katapult             | Compare attachment IDs between files              | **(R)** Remove  |
| Katapult   | `mr_move` present & attachment in both files | `nodes[*].attachments.*[*].mr_move`               | **(E)** Existing |
| Katapult   | Explicit `remove == true` flag               | `nodes[*].attachments.*[*].remove`                | **(R)** Remove  |
| Both       | Same attachment in both with no changes      | No changes between files                          | **(E)** Existing |

> **Important Note**: SPIDAcalc represents the *existing* state, while Katapult carries both existing and proposed design information. When determining actions, Katapult is the authoritative source for proposed changes.

---

## 3 Attachment Reconciliation Process

```python
def reconcile_attachments(spida_pole, katapult_node):
    """
    Match attachments between SPIDAcalc and Katapult for a given pole,
    and determine individual attachment actions.
    
    Returns:
        List of AttachmentInfo objects with action property set
    """
    result = []
    
    # Step 1: Create lookup maps
    spida_attachments = {att.id: att for att in get_spida_attachments(spida_pole)}
    katapult_attachments = {att.id: att for att in get_katapult_attachments(katapult_node)}
    
    # Step 2: Process attachments in Katapult (for installs, moves, and retained)
    for k_id, k_att in katapult_attachments.items():
        attachment_info = AttachmentInfo(
            id=k_id,
            description=k_att.desc,
            owner=k_att.owner
        )
        
        # Determine attachment-level action
        if k_att.get("proposed", False) or k_id not in spida_attachments:
            # New installation
            attachment_info.action = Action.I
            attachment_info.existing_height = None
            attachment_info.proposed_height = convert_to_inches(k_att.measured_height_in)
        elif k_att.get("remove", False):
            # Explicit removal flag
            attachment_info.action = Action.R
            attachment_info.existing_height = convert_to_inches(
                spida_attachments[k_id].existingHeight_in
            )
            attachment_info.proposed_height = None
        elif "mr_move" in k_att:
            # Existing with move
            attachment_info.action = Action.E
            attachment_info.existing_height = convert_to_inches(
                spida_attachments[k_id].existingHeight_in
            )
            # Calculate proposed height by applying mr_move
            attachment_info.proposed_height = attachment_info.existing_height + k_att.mr_move
        else:
            # Existing without change
            attachment_info.action = Action.E
            attachment_info.existing_height = convert_to_inches(
                spida_attachments[k_id].existingHeight_in or k_att.measured_height_in
            )
            attachment_info.proposed_height = None
            
        result.append(attachment_info)
    
    # Step 3: Process attachments only in SPIDAcalc (for removals)
    for s_id, s_att in spida_attachments.items():
        if s_id not in katapult_attachments:
            # Attachment in SPIDAcalc but not in Katapult = removal
            attachment_info = AttachmentInfo(
                id=s_id,
                description=s_att.description,
                owner=s_att.owner,
                action=Action.R,
                existing_height=convert_to_inches(s_att.existingHeight_in),
                proposed_height=None
            )
            result.append(attachment_info)
    
    return result
```

## 4 Pole-Level Action Determination

```python
from enum import Enum, auto

class Action(Enum):
    I = auto()  # Installing
    R = auto()  # Removing
    E = auto()  # Existing

# Maps enum to display text for Column B
ACTION_DISPLAY = {
    Action.I: "(I) Installing",
    Action.R: "(R) Removing",
    Action.E: "(E) Existing"
}

def determine_pole_action(attachments):
    """
    Determine the highest-priority action for a pole based on its attachments.
    
    Args:
        attachments: List of AttachmentInfo objects with action property set
        
    Returns:
        Action enum value (I, R, or E)
    """
    # Handle edge case: no attachments
    if not attachments:
        return Action.E  # Default to existing if no attachments
    
    # Check for highest priority action (I > R > E)
    if any(att.action == Action.I for att in attachments):
        return Action.I
    
    if any(att.action == Action.R for att in attachments):
        return Action.R
    
    return Action.E  # Only existing attachments or moves
```

---

## 5 Integration with Other Columns

| Related Column | Relationship                                                                                   |
| -------------- | ---------------------------------------------------------------------------------------------- |
| **Column A**   | Sequence numbers can follow action priority (I→R→E) or route order, as specified               |
| **Columns L-O**| Individual attachment actions determine which of M/N/O are populated and which remain blank     |
| **From/To rows**| Action code doesn't affect From/To rows; those depend only on connections                      |

---

## 6 Examples

### Example 1: Mixed actions on pole PL410620

```
Attachments:
- Neutral: Existing, no change
- CPS Supply Fiber: Existing, no change
- Charter/Spectrum Fiber Optic: New installation (proposed)
- AT&T Fiber Optic Com: Existing, no change
- AT&T Telco Com: Existing, no change
- AT&T Com Drop: Existing with mid-span height
```

**Result**: Column B = **(I) Installing** (due to new Charter/Spectrum fiber)

### Example 2: Removal on pole PL404474

```
Attachments:
- Neutral: Existing, no change
- CPS Supply Fiber: Existing, no change
- Charter/Spectrum Fiber: Existing, no change
- AT&T Telco Com: Existing, no change
- AT&T Com Drop: In SPIDAcalc but not in Katapult (removal)
```

**Result**: Column B = **(R) Removing** (due to AT&T drop removal)

### Example 3: Only relocations on pole PL370858

```
Attachments:
- Neutral: Existing with mr_move +12" (raise)
- CPS Supply Fiber: Existing, no change
- AT&T Fiber Optic: Existing, no change
- Charter/Spectrum Fiber: Existing with mr_move -6" (lower)
```

**Result**: Column B = **(E) Existing** (only moves, no installs or removals)

---

## 7 Edge-case handling

| Case                                     | Handling                                                    | Log key                    |
|------------------------------------------|-------------------------------------------------------------|----------------------------|
| No attachments on pole                   | Default to **(E) Existing**                                 | `NO_ATTACHMENTS`           |
| Attachment in Katapult without flags     | Treat as **(E) Existing** if in both files                  | `AMBIGUOUS_ATTACHMENT`     |
| ID mismatch between files                | Use custom matching logic to reconcile by height and type   | `ID_MISMATCH_RECONCILED`   |
| Both `proposed` and `mr_move` present    | Prioritize **(I) Installing** (`proposed` wins)            | `CONFLICTING_SIGNALS`      |
| Both `remove` and `mr_move` present      | Log warning, prioritize **(R) Removing** (`remove` wins)   | `REMOVE_WITH_MOVE_CONFLICT`|

---

## 8 Unit-test checklist

```python
import pytest
from mrrgen.actions import Action, determine_pole_action, AttachmentInfo

def test_determine_pole_action():
    # Test prioritization: I > R > E
    mixed_attachments = [
        AttachmentInfo(action=Action.I, id="a1"),
        AttachmentInfo(action=Action.R, id="a2"),
        AttachmentInfo(action=Action.E, id="a3")
    ]
    assert determine_pole_action(mixed_attachments) == Action.I
    
    # Test only removals
    removal_attachments = [
        AttachmentInfo(action=Action.R, id="a1"),
        AttachmentInfo(action=Action.E, id="a2")
    ]
    assert determine_pole_action(removal_attachments) == Action.R
    
    # Test only existing
    existing_attachments = [
        AttachmentInfo(action=Action.E, id="a1"),
        AttachmentInfo(action=Action.E, id="a2")
    ]
    assert determine_pole_action(existing_attachments) == Action.E
    
    # Test empty attachment list
    assert determine_pole_action([]) == Action.E

def test_edge_cases():
    # Test attachment with both proposed and mr_move flags
    att_info = reconcile_attachments(
        spida_pole={"attachments": [{"id": "a1", "existingHeight_in": 300}]},
        katapult_node={"attachments": {"wires": [
            {"id": "a1", "proposed": True, "mr_move": 12}
        ]}}
    )
    assert att_info[0].action == Action.I  # proposed takes precedence
```

---

## 9 Revision history

| Date       | Version | Notes                                                                     |
|------------|---------|---------------------------------------------------------------------------|
| 2025-05-19 | v1.0    | Initial doc added (mirrors PRD logic).                                    |
| 2025-05-20 | v2.0    | Enhanced reconciliation logic, added edge cases, aligned with other columns |
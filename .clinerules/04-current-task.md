# Rule 04: Follow the Current Task Instructions (Task Notes Template)

## Purpose

Ensure that AI agents and collaborators adhere strictly to the structure, logic, and processing requirements outlined in the current task's `task_###_notes.md` file. This rule guarantees traceable, reproducible, and consistent data handling across job-specific reports.

## Rule Logic

* **Read Before Execution**: Always read and parse the contents of the currently assigned `task_###_notes.md` file located under `/current_tasks/` before performing any data processing or generation logic.
* **No Deviation**: Do not rewrite or restructure the task file. Do not infer or assume alternative workflows. Follow it exactly as written unless a blocking error is encountered.
* **Respect Structure**: Ensure your outputs and intermediate steps align with:

  * Input/Output filenames
  * Pole filtering logic
  * Conflict resolution strategies
  * Unit conversion expectations
  * JSON-to-Excel column mappings
  * Special notes or overrides listed under Known Issues

## Input Handling

* Ensure all required files listed under **Section 2: Input Artifacts** are loaded.
* If optional files are listed (e.g., `target_poles_###.txt`), check existence before use.
* Use helper utilities like `normalize_pole_id()` or `height_utils.py` **only if referenced in the task instructions.**

## Output Validation

* Output files must match the paths and filenames defined in **Section 3: Output Deliverables**.
* Validate all column mappings (especially A–O) against **Section 4: Processing Requirements**.
* If discrepancies exist between SPIDAcalc and Katapult, apply the conflict resolution strategy explicitly defined in the task file.

## Logging & Auditability

* Every task must generate a `processing_log.txt` summarizing steps taken, counts of poles/attachments processed, and any warnings.
* If validation or comparison is required (e.g., with previous report versions), generate the expected diff logs or AI summaries listed under outputs.

## Exceptions

* If a field is missing or a file cannot be processed, fallback values (e.g., "N/A") are acceptable **only** if permitted in Section 5 or 6 of the task file.
* If the instructions are internally contradictory or impossible to follow, update task `Status` to **Blocked**, log the issue, and request manual resolution.

## Summary

This rule ensures every report generation task is:

* Isolated to a defined scope
* Consistent in its output
* Fully traceable to input JSONs and decisions
* Easy to review and troubleshoot later

Use `task_###_notes.md` as the single source of truth for that job's logic.

> 🔒 Do not freeform or extrapolate unless the file explicitly invites flexible logic. If unsure, escalate.

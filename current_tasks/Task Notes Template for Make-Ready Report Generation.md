# Task ID: [Unique Task Identifier, e.g., task_001_CPS6457E]

**Created:** YYYY-MM-DD
**Last Updated:** YYYY-MM-DD
**Assigned To:** [Developer Name / AI Agent ID]
**Priority:** [High | Medium | Low]
**Status:** [Pending | In Progress | Requires Review | Blocked | Completed]

---

## 1. Objective

*Provide a concise summary of the task's purpose, focusing on the specific job and desired outcomes.*

> **Example:**
> Generate the comprehensive Make-Ready Excel report for job `CPS_6457E_03`. This involves processing the provided Katapult JSON (`task_001_katapult.json`) and the associated SPIDAcalc JSON (`task_001_spidacalc.json`). The primary goal is to accurately populate Columns A–O of the report, detailing pole-level attributes, individual attachment existing/proposed heights, mid-span clearance data, and Pole Loading Analysis (PLA) metrics.

---

## 2. Input Artifacts

*List all input files and data sources required for the successful execution of this task. Specify if an artifact is optional.*

| Filename (Relative Path)    | Description                                                                 | Required   |
| :-------------------------- | :-------------------------------------------------------------------------- | :--------- |
| `task_001_katapult.json`    | Katapult JSON export containing field-collected data for the job.           | Yes        |
| `task_001_spidacalc.json`   | SPIDAcalc JSON export containing engineering analysis and proposed designs.   | Yes/No     |
| `target_poles_task_001.txt` | (Optional) Text file listing specific pole IDs to process, one per line.    | No         |
| `report_template_vX.xlsx`   | (Optional) Specific Excel template version to be populated, if not standard. | No         |

---

## 3. Output Deliverables

*Define the expected output files and any other artifacts resulting from this task.*

| Filename (Relative Path)        | Description                                                                                   |
| :------------------------------ | :-------------------------------------------------------------------------------------------- |
| `task_001_make_ready_report.xlsx` | The final, populated Make-Ready Excel report.                                                 |
| `task_001_summary_sheet.csv`    | (Optional) A CSV export of the summary sheet from the Excel report, if applicable.            |
| `task_001_processing_log.txt`   | Detailed log of processing steps, including any warnings, errors, or data conflicts encountered. |
| `task_001_ai_validation.txt`    | (If applicable) Summary report from an AI agent detailing validation checks and key findings.   |
| `task_001_data_diff.log`        | (Optional) If re-processing, a log detailing differences from a previous output version.        |

---

## 4. Processing Requirements & Logic

*Clarify specific data extraction rules, transformation logic, business rules, and conflict resolution strategies to be applied.*

* **Pole Identification:**
    * If `target_poles_task_001.txt` is provided, process only the listed pole IDs. Otherwise, process all relevant poles from the input JSONs.
    * Normalize all pole numbers from Katapult (`PoleNumber`) and SPIDAcalc (`location.label`) using `processor.utils.normalize_pole_id()`.
* **Height Data (Excel Columns M & N):**
    * **Existing Heights (Column M):** Primarily use Katapult `nodes[...].photos[...].photofirst_data.wire[...]._measured_height` (original unit: **INCHES**).
    * **Proposed Heights (Column N):** Primarily use SPIDAcalc `designs[label="Recommended Design"].structure.wires/equipments[...].attachmentHeight.value` (original unit: **METERS**).
    * **Unit Conversion:** All heights must be converted to **FEET** for the final report using `processor.height_utils.py`.
* **Attachment Actions (Excel Column B):**
    * If SPIDAcalc is available:
        * Attachment in "Recommended Design" but not "Measured Design" → implies **Installing**.
        * Attachment in "Measured Design" but not "Recommended Design" → implies **Removing**.
        * Attachment in both with height change → **Existing** (modification implied).
    * If SPIDAcalc is not available, all Katapult attachments are **Existing**.
* **Pole Attributes (Excel Column E):**
    * Default to Katapult data (e.g., `PoleHeight`, `PoleClass`, `PoleSpecies`).
    * If Katapult data is missing for an attribute, fallback to SPIDAcalc "Measured Design" data if available and consistent.
* **Proposed Risers/Guys (Excel Columns F & G):**
    * Determine "Yes/No" based on new or modified attachments in SPIDAcalc "Recommended Design" with `clientItem.type` containing "Riser" or `usageGroup` being "GUY" (or similar descriptions).
* **PLA (Excel Column H):**
    * Prioritize SPIDAcalc `poleResults` for the "Recommended Design" (e.g., `component=="Pole"`, `analysisType=="STRESS"`, `actual` value).
    * Fallback to Katapult `final_passing_capacity_%` if SPIDAcalc PLA is unavailable.
* **Mid-Span Data (Excel Columns J, K, O):**
    * Refer to `docs/README_Excel_Report.md` (ID: `excel_report_readme_v1`) for detailed logic on "From Pole"/"To Pole" and "Red (North East) to service pole" scenarios.
* **Attacher Name Normalization (Excel Column L):**
    * Use mappings from `processor.constants.py` for consistent display (e.g., "AT&T" for various input spellings).

---

## 5. Known Issues or Special Conditions for This Task

*Use this section to note any specific data anomalies, required overrides, or edge cases pertinent to *this particular task's input files*.*

> **Example:**
> * Katapult file `task_001_katapult.json` is missing `photo` objects for spans connected to pole `PL370858`. Mid-span data for these spans (Columns J, K, O) will likely be "N/A".
> * SPIDAcalc file `task_001_spidacalc.json` does not contain a `"Recommended Design"` for pole `PL410620`. For this pole, proposed heights (Column N) should default to existing heights, and PLA (Column H) should use Katapult's existing capacity.

---

## 6. Completion Criteria

*Define the minimum conditions that must be met for this task to be considered complete and successful.*

* [ ] All targeted or discoverable poles have been processed according to the defined rules.
* [ ] The Make-Ready Excel report (`task_001_make_ready_report.xlsx`) is generated without critical processing errors.
* [ ] All required columns (A–O) in the Excel report are populated with accurately mapped and transformed data.
* [ ] Attachment actions (Installing, Removing, Existing) and proposed heights are correctly determined based on available SPIDAcalc/Katapult data.
* [ ] Pole-level attributes and mid-span data are verified against source JSONs and appear as expected.
* [ ] A processing log (`task_001_processing_log.txt`) is generated, detailing the run.
* [ ] (If automated) The task status is updated to "Completed," and task files are archived as per project workflow.

---

## 7. References & Linked Project Documents

*Provide links to relevant project documentation that support this task.*

* **Excel Report Structure & Mapping:** `docs/README_Excel_Report.md` (ID: `excel_report_readme_v1`)
* **Katapult JSON Data Guide:** `docs/README_Katapult_JSON.md` (ID: `katapult_json_developer_guide_v1`)
* **SPIDAcalc JSON Data Guide:** `docs/README_SPIDAcalc_JSON.md` (ID: `spidacalc_json_developer_guide_v1`)
* **Project Constants & Mappings:** `processor/constants.py`
* **Normalization & Utility Functions:** `processor/utils.py`
* **Previous Similar Task (Example):** `archive/job_PREVIOUS_XYZ/job_PREVIOUS_XYZ_task_notes.md` (if applicable)


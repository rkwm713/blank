# README: Implementing the "Export to Excel" Feature

**Date:** May 16, 2025
**Task:** Add a feature to export the processed make-ready report data into an Excel file, formatted according to the provided specification.

## 1. Objective

The primary goal is to enable users to download a Make-Ready report in `.xlsx` format. This report should accurately reflect the data processed by `make_ready_processor.py` and adhere to the specific formatting, layout, and data mapping outlined in project documentation and visual examples.

## 2. Key References

*   **Data Mapping & Structure Guide:** `project-docs/Make-Ready Excel Report - Structure and Data Mapping.md`
*   **Target Excel Format (Screenshot):** `project-docs/excel_example.png`
*   **Primary Data Source Script:** `make_ready_processor.py`

## 3. Input Data for Excel Generation

The Excel generation logic will take as input the list of processed pole data dictionaries returned by the `process_make_ready_report` function in `make_ready_processor.py`. Each dictionary in this list represents a pole and contains:
*   Pole-level attributes (owner, number, structure, PLA, etc.).
*   Mid-span data (existing lowest communication and electrical heights, proposed mid-span values, from/to pole identifiers).
*   A list of `attachers`, where each attacher is a dictionary containing its description, existing height, and proposed height.
*   Geographic data (latitude, longitude) and a status summary for map integration.

## 4. Core Implementation Steps

### Step 1: Dependency Management

*   Add the `openpyxl` library to `requirements.txt` to enable Excel file creation and manipulation.
    ```
    flask==3.0.2
    python-dotenv==1.0.1
    openpyxl==<latest_version> 
    ```
    *(Note: Replace `<latest_version>` with the actual latest stable version of openpyxl at the time of implementation).*

### Step 2: Excel Generation Module/Function

Create a new Python module (e.g., `excel_generator.py`) or add functions to an existing relevant module (like `make_ready_processor.py` or a new `utils.py`).

*   **Main Function:**
    *   Define a function, e.g., `create_make_ready_excel(processed_pole_data: list, output_filepath: str)`.

*   **Workbook and Worksheet Setup:**
    *   Initialize an `openpyxl.Workbook()`.
    *   Get the active worksheet and set its title (e.g., "Make-Ready Report").

*   **Header Creation (Rows 1-2):**
    *   Populate cells A1:O2 with the static header titles as seen in `project-docs/excel_example.png`.
        *   Row 1: Merged cells for "Existing Mid-Span Data" (J1-2:K1-2) and "Make Ready Data" (L1:O1).
        *   Row 2: Individual column headers ("Operation Number", "Attachment Action", ..., "Proposed").
    *   Apply styling to header rows:
        *   Background color: Blue (e.g., `0070C0` or similar).
        *   Font color: Black, Bold.
        *   Text alignment: Center, Middle.
        *   Enable text wrapping for headers like "Attachment Action".
    *   Freeze the header rows (Rows 1 and 2) so they remain visible during scrolling (`worksheet.freeze_panes = 'A3'`).

*   **Column Widths:**
    *   Set appropriate widths for each column (A-O) to match the visual layout in `project-docs/excel_example.png` and ensure readability. (e.g., `ws.column_dimensions['A'].width = 10`).

*   **Populating Data (Starting from Row 3):**
    *   Iterate through each `pole_data` dictionary in the `processed_pole_data` list. Each pole represents an "Operation".
    *   Assign a sequential "Operation Number" (Column A).
    *   **Pole-Level Information (Columns A-I, K-L for midspan):**
        *   For each pole, determine the number of rows it will span (1 pole header row + number of attachments + 1 "From/To Pole" row + 1 separator row).
        *   **Column A (Operation Number):** Sequential number for the operation.
        *   **Column B (Attachment Action):** Use `pole_data.get('status', 'No Change')` or derive based on overall changes. This cell is typically merged vertically across all rows for the current pole operation.
        *   **Column C (Pole Owner):** `pole_data.get('pole_owner')`. Merged vertically.
        *   **Column D (Pole #):** `pole_data.get('pole_number')`. Merged vertically.
        *   **Column E (Pole Structure):** `pole_data.get('pole_structure')`. Merged vertically.
        *   **Column F (Proposed Riser (Yes/No)):** `pole_data.get('proposed_riser')`. Merged vertically.
        *   **Column G (Proposed Guy (Yes/No)):** `pole_data.get('proposed_guy')`. Merged vertically.
        *   **Column H (PLA (%) with proposed attachment):** `pole_data.get('pla_percentage')`. Merged vertically.
        *   **Column I (Construction Grade of Analysis):** `pole_data.get('construction_grade')`. Merged vertically.
        *   **Column J (Existing Mid-Span Data - Height Lowest Com):** `pole_data.get('existing_midspan_lowest_com')`. This cell is part of the pole-level block, typically merged across attachment rows.
        *   **Column K (Existing Mid-Span Data - Height Lowest CPS Electrical):** `pole_data.get('existing_midspan_lowest_cps_electrical')`. Merged similarly to Column J.

    *   **Attachment Details (Columns L-O, repeated for each attacher):**
        *   For each `attacher` dictionary in `pole_data['attachers']`:
            *   **Column L (Attacher Description):** `attacher.get('description')`.
            *   **Column M (Attachment Height - Existing):** `attacher.get('existing_height')`.
            *   **Column N (Attachment Height - Proposed):** `attacher.get('proposed_height')`.
            *   **Column O (Mid-Span (same span as existing) - Proposed):** `attacher.get('midspan_proposed')`.
        *   Handle special rows like "Ref (North East) to service pole" or "Ref (South East) to PL#######":
            *   These appear as distinct rows within the attachment block.
            *   They have specific background colors (e.g., light orange, light purple).
            *   The text for these rows will need to be derived from specific conditions or data fields not fully detailed but hinted at in the mapping document (e.g., specific connection types or notes). The `make_ready_processor.py` might need adjustments if this data isn't already prepared. For now, assume these are special attacher entries or require specific logic to insert.

    *   **"From Pole" / "To Pole" Row:**
        *   After all attachments for a pole, insert a row.
        *   Columns A-I would be blank or part of the merged pole-level cells.
        *   **Column J (From Pole):** `pole_data.get('from_pole')`. Style with blue background, white text.
        *   **Column K (To Pole):** `pole_data.get('to_pole')`. Style with blue background, white text.
        *   Columns L-O would be blank.

    *   **Separator Row:**
        *   After the "From Pole / To Pole" row, add a blank row or a row with a top border to visually separate pole operations. The screenshot shows a thick black line.

*   **Cell Formatting:**
    *   **Borders:** Apply thin black borders to all data cells. Apply a thick top border for rows starting a new pole operation (under the headers, and after each pole's block).
    *   **Alignment:**
        *   Generally, center align text in most cells, especially headers and pole-level data.
        *   Specific alignments (left/right) for numerical or descriptive data if it improves readability.
    *   **Number Formatting:** Ensure heights are displayed as "X ft Y in" or "X.Y%" as appropriate.
    *   **Conditional Formatting (Highlight Differences):**
        *   If `pole_attribute_strategy` was 'HIGHLIGHT_DIFFERENCES' and a pole attribute string (e.g., `pole_structure`) contains "(SPIDA: ...)", apply a distinct background color (e.g., yellow) to that cell.

### Step 3: Flask Integration (`app.py`)

*   **New Route:**
    *   Add a new Flask route, e.g., `@app.route('/download_excel_report', methods=['GET'])`.
*   **Route Logic:**
    1.  Retrieve the processed data. This might involve:
        *   Getting parameters (like uploaded file paths, target poles, strategies) from the session or request arguments.
        *   Calling `process_make_ready_report()` from `make_ready_processor.py` to get the `processed_pole_data`.
    2.  Define an output filename (e.g., `make_ready_report_<timestamp>.xlsx`).
    3.  Call the `create_make_ready_excel(processed_pole_data, output_filepath)` function.
    4.  Use Flask's `send_file(output_filepath, as_attachment=True)` to allow the user to download the generated Excel file.
    5.  Consider temporary file storage or in-memory generation (using `io.BytesIO`) for the Excel file to avoid disk clutter.

### Step 4: Frontend Update (`templates/results.html`)

*   Add an "Export to Excel" button or link on the results page.
    ```html
    <a href="{{ url_for('download_excel_report') }}" class="btn btn-success">Export to Excel</a>
    ```
    *(Ensure query parameters are passed if the download route needs them, e.g., to re-fetch data based on the current session/job ID).*

## 5. Testing Strategy

*   **Unit Tests:**
    *   Create test cases for the `create_make_ready_excel` function.
    *   Use sample `processed_pole_data` structures.
    *   Programmatically read the generated Excel file (using `openpyxl` in the test) to verify:
        *   Correct header content and basic styling.
        *   Accurate data placement in cells.
        *   Correct cell merging.
        *   Presence of conditional formatting markers (if possible to check, or verify input data that *should* trigger it).
*   **Manual Testing:**
    *   Generate Excel reports using various input Katapult (and SPIDAcalc, if applicable) JSON files.
    *   Visually compare the generated `.xlsx` files against `project-docs/excel_example.png` and the requirements in `project-docs/Make-Ready Excel Report - Structure and Data Mapping.md`.
    *   Verify all formatting, data accuracy, and special cases.

## 6. Visual Plan (Workflow)

```mermaid
graph TD
    subgraph User Interaction
        A[User uploads JSONs via index.html] --> B{app.py: /process_data};
        B --> C[make_ready_processor.py: process_data()];
        C --> D[results.html: Display Results];
        D -- Click 'Export to Excel' --> E{app.py: /download_excel_report};
    end

    subgraph Excel Generation
        E -- Gets processed_data --> F[excel_generator.py: create_make_ready_excel(processed_data)];
        F --> G[Generated Excel File (.xlsx)];
    end

    E --> H[User Downloads Excel File];

    subgraph Data & Configuration
        I[Katapult/SPIDAcalc JSONs] --> C;
        J[project-docs/Make-Ready Excel Report - Structure and Data Mapping.md] -- Guides --> F;
        K[project-docs/excel_example.png (Visual Guide)] -- Guides --> F;
        L[openpyxl library] -- Used by --> F;
    end

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style D fill:#f9f,stroke:#333,stroke-width:2px
    style H fill:#f9f,stroke:#333,stroke-width:2px
    style G fill:#ccf,stroke:#333,stroke-width:2px
    style I fill:#bbf,stroke:#333,stroke-width:2px
    style J fill:#bbf,stroke:#333,stroke-width:2px
    style K fill:#bbf,stroke:#333,stroke-width:2px
    style L fill:#bbf,stroke:#333,stroke-width:2px
```

This README should provide a comprehensive guide for implementing the Excel export feature.

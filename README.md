# Make-Ready Report Generation Application - README

## 1. Project Overview

This project is a Python-based web application designed to process utility pole data from Katapult and SPIDAcalc JSON files to generate comprehensive "Make-Ready Reports". The application allows users to upload these data files, specify target poles, and define conflict resolution strategies. It then processes the data to determine existing and proposed attachment heights, identify necessary make-ready work, analyze pole loading, and visualize pole locations. The final output is an Excel report detailing the findings for each pole.

The core functionality revolves around parsing complex JSON structures, normalizing data from different sources, applying business logic for engineering calculations (like neutral wire identification and attachments below it), and presenting the information in a structured and user-friendly format.

## 2. System Architecture and Module Interaction

The application is modular, with specific Python files handling distinct parts of the data processing and application logic. Here's how they generally interact:

```mermaid
graph TD
    A[app.py (Flask App)] --> B(Data Upload & UI)
    B --> C{make_ready_processor.py}
    C --> D[data_loader.py]
    C --> E[pole_attribute_processor.py]
    C --> F[attachment_processor.py]
    C --> G[connection_processor.py]
    C --> H[neutral_identification.py]
    C --> I[spida_utils.py]
    C --> J[reference_utils.py]
    C --> K[excel_generator.py]

    D --> L[utils.py]
    E --> L
    E --> I
    F --> L
    F --> M[trace_utils.py]
    F --> N[wire_utils.py]
    G --> L
    G --> M
    G --> N
    G --> J
    H --> L
    H --> M
    H --> N
    J --> L
    J --> M
    J --> N
    K --> M
    K --> L
    K --> N
    M --> L

    subgraph CoreProcessing
        C
    end

    subgraph DataInputOutput
        B
        D
        K
    end

    subgraph SpecializedProcessors
        E
        F
        G
        H
        I
        J
    end

    subgraph LowLevelUtilities
        L
        M
        N
    end

    O[debug_logging.py] -- Used by --> C
    P[excel_utils.py] -- Used by --> K
    P --> L
```

**Flow Description:**

1.  **`app.py`**: This is the main Flask web application. It handles:
    *   User interface (serving HTML templates like `index.html` and `results.html`).
    *   File uploads (Katapult and SPIDAcalc JSON).
    *   Receiving user inputs (target poles, conflict strategies).
    *   Session management.
    *   Initiating the data processing by calling `make_ready_processor.process_make_ready_report`.
    *   Serving the generated Excel report for download.
    *   Managing temporary files.

2.  **`make_ready_processor.py`**: This is the central orchestrator. It:
    *   Calls `data_loader.py` to load and perform initial validation of Katapult and SPIDAcalc data.
    *   Iterates through poles, calling various specialized processor modules:
        *   `pole_attribute_processor.py`: To extract and resolve conflicts for pole attributes (owner, structure, PLA, etc.).
        *   `attachment_processor.py`: To process, consolidate, and normalize attachment data (wires, equipment) from both sources.
        *   `connection_processor.py`: To analyze connections between poles, identify reference spans, backspans, and calculate midspan data.
        *   `neutral_identification.py`: To identify neutral wires and filter attachments below the highest neutral.
    *   Uses `spida_utils.py` for SPIDAcalc-specific data extraction (e.g., proposed risers/guys, construction grade).
    *   Uses `reference_utils.py` for detailed processing of reference and backspan attachments.
    *   Aggregates all processed data for each pole.
    *   The output of this module is a list of processed pole data dictionaries.

3.  **`data_loader.py`**:
    *   Loads Katapult JSON (`load_katapult_data`).
    *   Loads SPIDAcalc JSON (`load_spidacalc_data`).
    *   Builds lookup tables for SPIDAcalc data for efficient access (`build_spida_lookups`).
    *   Normalizes the list of target poles (`filter_target_poles`).

4.  **`pole_attribute_processor.py`**:
    *   Extracts pole attributes from Katapult (`extract_pole_attributes_katapult`).
    *   Uses functions from `spida_utils.py` to get attributes like structure, PLA, and construction grade from SPIDAcalc.
    *   Resolves conflicts between attributes from the two sources (`resolve_pole_attribute_conflicts`).

5.  **`attachment_processor.py`**:
    *   Processes attachments from Katapult photos (`process_katapult_attachments`).
    *   Processes attachments from SPIDAcalc designs (`process_spidacalc_attachments`).
    *   Consolidates attachments from both, applying rules for deduplication and conflict resolution (`consolidate_attachments`).
    *   Identifies owners with attachment changes (`identify_owners_with_changes`).
    *   Formats attachment descriptions (`format_attacher_description`).

6.  **`connection_processor.py`**:
    *   Identifies all connections for a pole from Katapult data.
    *   Determines lowest communication and CPS electrical wire heights in each span.
    *   Uses `reference_utils.py` to process reference spans and backspans in detail.
    *   Calculates overall midspan data for the pole.

7.  **`neutral_identification.py`**:
    *   Identifies neutral wires from Katapult and SPIDAcalc data using pattern matching and specific field checks.
    *   Determines the highest neutral wire.
    *   Filters the list of pole attachments to include only those below the highest neutral.

8.  **`spida_utils.py`**:
    *   Contains a suite of functions dedicated to extracting specific pieces of information from SPIDAcalc JSON, such as proposed equipment, construction grade, pole sequence, PLA percentage, and detailed attachment lists.

9.  **`reference_utils.py`**:
    *   Focuses on processing reference spans and backspans, including generating descriptive headers and extracting attachments within these spans.
    *   Calculates cardinal directions between poles.

10. **`excel_generator.py`**:
    *   Takes the list of processed pole data from `make_ready_processor.py`.
    *   Uses the `openpyxl` library to create a formatted Excel report according to a specific template structure.
    *   Includes helper functions for categorizing wires and identifying reference subgroups for Excel formatting.

11. **Utility Modules**:
    *   **`utils.py`**: Provides general helper functions for unit conversions (inches to feet-inches, meters to feet-inches), string normalization (pole IDs, owner names), and robust data extraction from nested dictionaries.
    *   **`trace_utils.py`**: Provides utilities for reliably looking up Katapult "trace" data (which contains wire attributes) and extracting metadata from wires and their traces.
    *   **`wire_utils.py`**: Contains functions for parsing height strings (feet-inches to inches) and processing wire heights from various Katapult data fields.
    *   **`excel_utils.py`**: Contains helper functions specifically for Excel generation or data preparation for Excel, such as string extraction, unit conversion, wire categorization, and Excel column letter conversion.
    *   **`debug_logging.py`**: Configures logging for the application, setting up file and console handlers with appropriate formatting and levels. Provides a function to log summaries of processed pole data.

## 3. Module Summaries

*   **`app.py`**: Flask web server, UI, file handling, main application flow control.
    *   *See `app_readme.md` for details.*
*   **`make_ready_processor.py`**: Core orchestration logic for processing pole data.
    *   *See `make_ready_processor_readme.md` for details.*
*   **`data_loader.py`**: Loads and preprocesses Katapult and SPIDAcalc JSON files.
    *   *See `data_loader_readme.md` for details.*
*   **`pole_attribute_processor.py`**: Extracts and resolves pole-specific attributes (owner, structure, PLA).
    *   *See `pole_attribute_processor_readme.md` for details.*
*   **`attachment_processor.py`**: Processes and consolidates wire and equipment attachments on poles.
    *   *See `attachment_processor_readme.md` for details.*
*   **`connection_processor.py`**: Analyzes connections between poles, including midspan data and special spans.
    *   *See `connection_processor_readme.md` for details.*
*   **`neutral_identification.py`**: Identifies neutral wires and filters attachments below them.
    *   *See `neutral_identification_readme.md` for details.*
*   **`spida_utils.py`**: Utilities specifically for extracting data from SPIDAcalc JSON.
    *   *See `spida_utils_readme.md` for details.*
*   **`reference_utils.py`**: Utilities for processing reference spans and backspans.
    *   *See `reference_utils_readme.md` for details.*
*   **`excel_generator.py`**: Generates the final Make-Ready Excel report.
    *   *See `excel_generator_readme.md` for details.*
*   **`utils.py`**: General-purpose helper functions (unit conversion, normalization, data extraction).
    *   *See `utils_readme.md` for details.*
*   **`trace_utils.py`**: Utilities for handling Katapult "trace" data (wire attributes).
    *   *See `trace_utils_readme.md` for details.*
*   **`wire_utils.py`**: Utilities for processing wire heights.
    *   *See `wire_utils_readme.md` for details.*
*   **`excel_utils.py`**: Helper functions for Excel data preparation and formatting.
    *   *See `excel_utils_readme.md` for details.*
*   **`debug_logging.py`**: Configures application logging.
    *   *See `debug_logging_readme.md` for details.*

## 4. Running the Application

(This section would typically describe how to set up and run the Flask application, e.g., `python app.py`. This information is inferred from the `app.py` content.)
The application is started by running `app.py`. It will host a web server (likely on `http://127.0.0.1:5000/` by default if using Flask's development server) where users can upload their JSON files and initiate the make-ready report generation.

## 5. Key Data Structures

*   **Katapult JSON**: Expected to contain `nodes` (poles, with attributes and photo data), `connections` (spans between nodes), `photos` (with `photofirst_data` containing wire/attachment details), and `traces` (attributes for wires).
*   **SPIDAcalc JSON**: Expected to contain `leads` and `locations` (poles), with `designs` ("Measured Design", "Recommended Design") that include `structure` data (wires, equipment, guys, poleTags, analysis results for PLA).
*   **Processed Pole Data (Internal)**: The `make_ready_processor.py` generates a list of dictionaries, where each dictionary represents a pole and contains all consolidated and processed information (attributes, attachers, midspan data, etc.) ready for Excel output.

This project demonstrates a comprehensive approach to a complex data integration and engineering reporting task, with clear separation of concerns across its modules.

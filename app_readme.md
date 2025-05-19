# `app.py` - Flask Web Application for Make Ready Reports

## 1. Overview

`app.py` is the main file for a Flask web application designed to process and generate "Make Ready Reports". Users can upload Katapult JSON data (mandatory) and SPIDAcalc JSON data (optional), along with a list of specific "target poles" to focus on. The application processes these inputs, displays the results (including a map visualization of pole locations), and allows users to download a consolidated report in Excel format.

The application emphasizes user feedback through flash messages, handles file uploads securely, validates input data, manages server-side sessions for storing processing parameters, and includes a mechanism for cleaning up temporary data files.

## 2. Key Imports and Modules

The application relies on several standard Python libraries and custom modules:

*   **Flask and related utilities**:
    *   `Flask`, `render_template`, `request`, `redirect`, `url_for`, `flash`, `send_file`, `session`: Core components for building the web application, handling requests, rendering HTML templates, managing user sessions, and sending files.
*   **Data Handling**:
    *   `json`: For parsing and serializing JSON data from the uploaded files and for temporary data storage.
*   **File System and System Utilities**:
    *   `os`: For path manipulations (joining paths, creating directories, checking file existence).
    *   `time`: For generating timestamps used in filenames and for session/temporary file management.
*   **Logging and Debugging**:
    *   `logging`: For application-level logging of events, errors, and debug information.
    *   `traceback`: For formatting and logging detailed stack traces during error handling.
*   **File Security**:
    *   `werkzeug.utils.secure_filename`: To ensure uploaded filenames are safe to store on the filesystem.
*   **Session Management**:
    *   `flask_session.Session`: For implementing filesystem-based server-side sessions, which is more robust for storing larger amounts of session-related metadata than default client-side cookies.
*   **Custom Processing Modules**:
    *   `make_ready_processor.process_make_ready_report`: A function from a local module responsible for the core logic of processing the Katapult and SPIDAcalc data to generate the report content.
    *   `excel_generator.create_make_ready_excel`: A function from a local module used to create the Excel (.xlsx) file from the processed report data.

## 3. Application Configuration

The Flask application is configured with several settings:

*   `app.secret_key = 'supersecretkey'`: A secret key essential for session security and enabling flash messages. **Note**: In a production environment, this should be a strong, randomly generated key and ideally stored securely (e.g., environment variable).
*   `app.config['UPLOAD_FOLDER'] = 'uploads'`: Specifies the directory where uploaded files will be stored.
*   `app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024`: Sets a maximum file size limit of 16MB for uploads.
*   `app.config['SESSION_TYPE'] = 'filesystem'`: Configures sessions to be stored on the server's filesystem.
*   `app.config['PERMANENT_SESSION_LIFETIME'] = 3600`: Sets the duration for permanent sessions to 1 hour (3600 seconds).
*   `app.config['SESSION_FILE_DIR'] = os.path.join(app.config['UPLOAD_FOLDER'], 'flask_session')`: Defines the subdirectory within `UPLOAD_FOLDER` where session files will be stored.
*   `TEMP_DATA_DIR = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_data')`: Defines a subdirectory for storing temporary JSON files containing processed data.

The application ensures that `UPLOAD_FOLDER`, `TEMP_DATA_DIR`, and `SESSION_FILE_DIR` are created if they do not already exist upon startup.

## 4. Core Functionality and Endpoints

### 4.1. Helper Functions

*   **`allowed_file(filename)`**:
    *   **Purpose**: Validates if an uploaded file has a `.json` extension.
    *   **Logic**: Checks if the filename string contains a period (`.`) and if the substring after the last period is `'json'` (case-insensitive).

### 4.2. Main Page Route

*   **`@app.route('/', methods=['GET']) def index():`**
    *   **Purpose**: Serves the main landing page of the application.
    *   **Logic**: Renders the `index.html` template, which presumably contains the file upload form.

### 4.3. File Upload and Processing Route

*   **`@app.route('/upload', methods=['POST']) def upload_file():`**
    *   **Purpose**: Handles the submission of Katapult and SPIDAcalc JSON files, target pole information, and conflict resolution strategies. It then processes this data and displays the results.
    *   **Logic**:
        1.  **Input Retrieval**:
            *   Gets the Katapult file (`request.files['katapult']`) and SPIDAcalc file (`request.files.get('spidacalc')`).
            *   Retrieves target pole numbers (`request.form.get('target_poles')`) and conflict resolution strategies for attachment height and pole attributes (`request.form.get(...)`).
        2.  **File Validation**:
            *   Ensures the Katapult file is provided.
            *   Uses `allowed_file()` to check if both Katapult and SPIDAcalc (if provided) files are `.json` files.
            *   Flashes appropriate error messages and redirects to the index page if validation fails.
        3.  **File Saving**:
            *   Secures filenames using `secure_filename()`.
            *   Saves valid uploaded files to the `app.config['UPLOAD_FOLDER']`.
        4.  **JSON Content Validation**:
            *   **Katapult JSON**: Reads the saved file, attempts to parse it as JSON. Verifies that the parsed data is a dictionary and contains a top-level key named `'nodes'`.
            *   **SPIDAcalc JSON (if provided)**: Similar validation, ensuring it's a dictionary and contains a top-level key named `'leads'`.
            *   Flashes errors and redirects if JSON is malformed or lacks required structure.
        5.  **Target Poles Parsing**:
            *   If `target_poles` text is provided, it's split by commas, spaces, or newlines using regex (`re.split(r'[,\s]+', ...)`) to create a list of individual pole numbers. Empty strings are filtered out.
        6.  **Data Processing**:
            *   Calls `process_make_ready_report()` with the paths to the saved Katapult and SPIDAcalc files, the list of target poles, and the chosen conflict resolution strategies.
            *   If `process_make_ready_report()` returns no data (e.g., no relevant poles found), a warning message is flashed.
        7.  **Temporary Data Storage & Session Management**:
            *   The processed `report_data` (potentially large) is saved to a temporary JSON file in `TEMP_DATA_DIR` (e.g., `processed_data_[timestamp].json`).
            *   The path to this temporary file, paths to the original uploaded files, target poles, strategies, and a timestamp are stored in the `session` object. This avoids storing large datasets directly in the session cookie or filesystem session file, keeping session data small.
        8.  **Geographic Data Preparation for Map**:
            *   Iterates through the `report_data` to extract geographic coordinates (`latitude`, `longitude`) and other relevant details (`pole_number`, `pole_owner`, `status`, etc.) for each pole.
            *   If geographic data is available, it calculates the average latitude and longitude to determine a central point for map display.
        9.  **Display Results**:
            *   Renders the `results.html` template, passing the processed `report_data` (as `poles`), the extracted `pole_geo_data`, and the `map_center`.
        10. **Comprehensive Error Handling**:
            *   The entire route is wrapped in `try-except` blocks to catch file errors, JSON decoding/validation errors, errors during the `process_make_ready_report` call, and any other unexpected exceptions.
            *   Errors are logged (including stack traces), user-friendly messages are flashed, and the user is redirected to the index page.

### 4.4. Excel Report Download Route

*   **`@app.route('/download_excel_report', methods=['GET']) def download_excel_report():`**
    *   **Purpose**: Allows the user to download the processed make-ready report as an Excel file.
    *   **Logic**:
        1.  **Retrieve Processed Data from Session/Temp File**:
            *   Attempts to get the `processed_data_path` from the current session.
            *   If the path is found and the corresponding temporary file exists, it loads the `processed_poles` data from this JSON file.
        2.  **Reprocess Data if Necessary**:
            *   If the temporary processed data cannot be loaded (e.g., file deleted, session expired), the application attempts to reprocess the data.
            *   It retrieves the original `katapult_path`, `spidacalc_path`, `target_poles`, and conflict strategies from the session.
            *   It verifies that the original Katapult input file still exists. If the SPIDAcalc file is missing but was originally provided, it proceeds with Katapult data only (logging a warning).
            *   Calls `process_make_ready_report()` again with these parameters.
            *   If reprocessing fails or yields no data, an appropriate flash message is shown.
        3.  **Generate Excel File**:
            *   A timestamp (from the session, or current time if not found) is used to create a unique filename for the Excel report (e.g., `make_ready_report_[timestamp].xlsx`) in the `UPLOAD_FOLDER`.
            *   Calls `create_make_ready_excel()` with the `processed_poles` data and the target `excel_path` to generate the spreadsheet.
        4.  **Send File for Download**:
            *   Uses `send_file()` to stream the generated Excel file to the user's browser as an attachment, with a generic download name "make_ready_report.xlsx" and the correct MIME type for `.xlsx` files.
        5.  **Error Handling**:
            *   Catches exceptions during the process, logs them, flashes an error message, and redirects to the index page.

### 4.5. Temporary File Cleanup

*   **`@app.before_request def cleanup_temp_files():`**
    *   **Purpose**: Automatically cleans up old temporary data files to prevent the `TEMP_DATA_DIR` from growing indefinitely.
    *   **Logic**:
        *   This function is decorated with `@app.before_request`, meaning it runs before every incoming request to the application.
        *   It iterates through all files in the `TEMP_DATA_DIR`.
        *   For each file, it checks its creation time (`os.path.getctime()`).
        *   If the file is older than 24 hours (86400 seconds), it is deleted using `os.remove()`.
        *   Any errors during the cleanup process are logged.

## 5. Application Execution

*   **`if __name__ == '__main__': app.run(debug=True)`**:
    *   This standard Python construct ensures that the Flask development server is started only when the script `app.py` is executed directly (not when imported as a module).
    *   `app.run(debug=True)` starts the server with debug mode enabled, which provides helpful debugging information and automatic reloading on code changes during development.

## 6. Dependencies on Other Project Files

*   **`make_ready_processor.py`**: Contains the `process_make_ready_report` function, which is central to the application's data processing logic.
*   **`excel_generator.py`**: Contains the `create_make_ready_excel` function, responsible for converting the processed data into an Excel spreadsheet.
*   **`templates/index.html`**: The HTML template for the main page with the file upload form.
*   **`templates/results.html`**: The HTML template used to display the processed results and the map.

## 7. Session Management Details

The application uses `Flask-Session` with a filesystem backend. This means:
*   Session data is not stored in client-side cookies (beyond a session ID).
*   Instead, session data is stored in files on the server, in the directory specified by `app.config['SESSION_FILE_DIR']`.
*   The application primarily stores file paths and processing parameters in the session, rather than large datasets, to keep session files small and efficient. The actual processed data is stored in separate temporary JSON files in `TEMP_DATA_DIR`.

This approach is more secure and robust for handling potentially sensitive or larger pieces of information related to a user's session.

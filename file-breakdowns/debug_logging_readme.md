# `debug_logging.py` - Logging Configuration and Utilities

## 1. Overview

`debug_logging.py` is a Python module responsible for setting up and managing logging for the make-ready report processing application. It ensures that log messages are written to both a timestamped file and the console, with different logging levels for each handler. It also provides a utility function to log a summary of processed pole data.

Key functionalities include:
*   Creating a dedicated logger named `make_ready_processor`.
*   Ensuring the `logs` directory exists.
*   Creating a unique log file for each processing run, named with a timestamp (e.g., `logs/make_ready_processing_YYYYMMDD_HHMMSS.log`).
*   Configuring a file handler to write `DEBUG` level (and above) messages to the log file.
*   Configuring a console handler to write `INFO` level (and above) messages to the standard output.
*   Using a shared formatter for consistent log message appearance.
*   Preventing duplicate handler attachment if the logger setup function is called multiple times.
*   Providing a function `log_pole_summary` to output a structured summary of key findings for a processed pole.

## 2. Key Imports and Modules

*   **`logging`**: Standard Python library for logging.
*   **`os`**: Standard Python library for interacting with the operating system, used here for creating directories (`os.makedirs`).
*   **`datetime` (from `datetime`)**: Standard Python library for working with dates and times, used here to generate timestamps for log filenames.

## 3. Core Functions and Logic

### 3.1. `get_processing_logger()`

*   **Purpose**: Sets up and returns a configured logger instance specifically for the "make-ready processing" part of the application.
*   **Logic**:
    1.  **Directory Creation**: Ensures that a directory named `logs` exists in the current working directory using `os.makedirs('logs', exist_ok=True)`.
    2.  **Log Filename**: Generates a unique log filename using the current timestamp (e.g., `logs/make_ready_processing_20230518_100700.log`).
    3.  **Get Logger**: Retrieves a logger instance named `make_ready_processor` using `logging.getLogger('make_ready_processor')`.
    4.  **Handler Check (Idempotency)**: Checks if the logger already has handlers attached (`if logger.handlers:`). If it does, the function assumes the logger is already configured and returns it immediately. This prevents adding multiple handlers if the function is called repeatedly, which would lead to duplicate log messages.
    5.  **Set Logger Level**: Sets the overall logging level for the `logger` to `logging.DEBUG`. This means it will process all messages of DEBUG level or higher.
    6.  **File Handler**:
        *   Creates a `logging.FileHandler` to write logs to the generated `log_file`.
        *   Sets the level for this handler to `logging.DEBUG`, so all debug messages (and above) go to the file.
    7.  **Console Handler**:
        *   Creates a `logging.StreamHandler` to write logs to the console (standard output).
        *   Sets the level for this handler to `logging.INFO` for more concise console output, showing only informational messages and errors.
    8.  **Formatter**:
        *   Creates a `logging.Formatter` with the format `%(asctime)s - %(levelname)s - %(message)s`.
        *   Applies this formatter to both the `file_handler` and `console_handler`.
    9.  **Add Handlers**: Adds the configured `file_handler` and `console_handler` to the `logger`.
    10. **Initial Log Message**: Logs an informational message indicating that logging has been initialized and the path to the log file.
*   **Returns**: The configured `logger` instance.

### 3.2. `log_pole_summary(logger, pole_data, neutral_wires, attachments_below_neutral)`

*   **Purpose**: Logs a formatted summary of key information about a processed pole, including details about neutral wires and attachments found below them.
*   **Parameters**:
    *   `logger`: The logger instance (obtained from `get_processing_logger()`) to use for logging.
    *   `pole_data` (dict): A dictionary containing data for the processed pole, expected to have a `pole_number`.
    *   `neutral_wires` (list): A list of dictionaries, where each dictionary represents a neutral wire and should contain `description` and `existing_height`.
    *   `attachments_below_neutral` (list): A list of dictionaries, where each dictionary represents an attachment found below the neutral wire(s) and should contain `description` and `existing_height`.
*   **Logic**:
    1.  Retrieves the `pole_number` from `pole_data` (defaults to 'Unknown').
    2.  Logs a header indicating the start of the summary for that pole.
    3.  Logs the count of `neutral_wires` found.
    4.  Logs the count of `attachments_below_neutral` found.
    5.  Iterates through `neutral_wires`, logging the description and existing height for each.
    6.  Iterates through `attachments_below_neutral`, logging the description and existing height for each.
    7.  Logs a footer to delimit the summary.
    All messages are logged at the `INFO` level.

## 4. Usage

This module is intended to be used by other parts of the application that perform make-ready processing.
Typically, `get_processing_logger()` would be called once at the beginning of a processing task to obtain a logger instance. This instance would then be passed around or used globally within that processing context.
The `log_pole_summary()` function would be called after processing individual poles to record specific findings in a structured way.

This setup ensures that detailed debug information is available in log files for troubleshooting, while the console provides a higher-level overview of the processing progress and significant events.

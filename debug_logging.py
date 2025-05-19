# debug_logging.py
import logging
import os
from datetime import datetime

def get_processing_logger():
    """
    Set up and return a logger for the make-ready processing.
    """
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create a unique log file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'logs/make_ready_processing_{timestamp}.log'
    
    # Configure / fetch logger
    logger = logging.getLogger('make_ready_processor')

    # If the logger already has handlers we assume it is fully configured and
    # simply return it.  This prevents duplicate handlers and duplicate log
    # lines when get_processing_logger() is called many times in the same
    # process.
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Create a file handler to log to a new file on first initialisation
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    # Create a console handler (INFO level for brevity)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Shared formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Attach handlers only once
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logging initialised, writing to {log_file}")

    return logger

def log_pole_summary(logger, pole_data, neutral_wires, attachments_below_neutral):
    """
    Log a summary of the processed pole data.
    """
    pole_number = pole_data.get('pole_number', 'Unknown')
    logger.info(f"======== Pole {pole_number} Summary ========")
    logger.info(f"Found {len(neutral_wires)} neutral wires")
    logger.info(f"Found {len(attachments_below_neutral)} attachments below neutral")
    
    # Log each neutral wire
    for i, neutral in enumerate(neutral_wires):
        desc = neutral.get('description', 'Unknown')
        height = neutral.get('existing_height', 'N/A')
        logger.info(f"Neutral {i+1}: {desc} at {height}")
    
    # Log each attachment below neutral
    for i, attachment in enumerate(attachments_below_neutral):
        desc = attachment.get('description', 'Unknown')
        height = attachment.get('existing_height', 'N/A')
        logger.info(f"Attachment below neutral {i+1}: {desc} at {height}")
    
    logger.info("=====================================")
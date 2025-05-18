"""
Enhanced logging module for tracing the attachment filtering process.

This module provides logging utilities specifically designed for debugging
the neutral wire identification and attachment filtering process.
"""

import logging
import os
import sys
from datetime import datetime
import re

# Constants
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_LOG_DIR = 'logs'

# Global logger dictionary to avoid duplicate configuration
loggers = {}

def get_logger(name, log_file=None, log_level=DEFAULT_LOG_LEVEL, 
               log_format=DEFAULT_LOG_FORMAT, console_output=True):
    """
    Get or create a logger with the given name and configuration.
    
    Args:
        name: Logger name
        log_file: Path to log file (optional)
        log_level: Logging level (default: INFO)
        log_format: Log format string (default: time - name - level - message)
        console_output: Whether to also log to console (default: True)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Check if logger already exists
    if name in loggers:
        return loggers[name]
        
    # Create new logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Add file handler if log_file is provided
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Store logger in dictionary
    loggers[name] = logger
    
    return logger

def get_processing_logger(pole_id=None):
    """
    Get a logger specifically for processing a pole.
    
    Args:
        pole_id: Optional pole ID to include in the log filename
        
    Returns:
        logging.Logger: Configured logger for pole processing
    """
    # Create log directory if it doesn't exist
    if not os.path.exists(DEFAULT_LOG_DIR):
        os.makedirs(DEFAULT_LOG_DIR)
    
    # Create log filename with timestamp and pole ID
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if pole_id:
        log_filename = f"{timestamp}_pole_{pole_id}.log"
    else:
        log_filename = f"{timestamp}_processing.log"
    
    log_path = os.path.join(DEFAULT_LOG_DIR, log_filename)
    
    # Create and return logger
    return get_logger(f"processing{'_'+str(pole_id) if pole_id else ''}", log_path)

def log_pole_summary(logger, pole_data, neutral_wires, attachments_below_neutral):
    """
    Log a summary of a pole's processing.
    
    Args:
        logger: Logger instance
        pole_data: Processed pole data dictionary
        neutral_wires: List of identified neutral wires
        attachments_below_neutral: List of attachments below the neutral
    """
    pole_number = pole_data.get('pole_number', 'Unknown')
    
    logger.info("\n" + "="*50)
    logger.info(f"POLE SUMMARY: {pole_number}")
    logger.info("="*50)
    
    # Log neutral wires
    logger.info(f"Found {len(neutral_wires)} neutral wire(s):")
    for i, neutral in enumerate(neutral_wires, 1):
        logger.info(f"  {i}. {neutral.get('description', 'Unknown')} at height {neutral.get('height')} inches (source: {neutral.get('source', 'Unknown')})")
    
    # Log highest neutral
    highest_neutral = max(neutral_wires, key=lambda w: w['height']) if neutral_wires else None
    if highest_neutral:
        logger.info(f"Highest neutral: {highest_neutral.get('description', 'Unknown')} at height {highest_neutral.get('height')} inches")
    else:
        logger.info("No neutral wires found!")
    
    # Log attachments below neutral
    logger.info(f"Found {len(attachments_below_neutral)} attachment(s) below neutral:")
    for i, attachment in enumerate(attachments_below_neutral, 1):
        logger.info(f"  {i}. {attachment.get('description', 'Unknown')} at height {attachment.get('existing_height', 'Unknown')}")
    
    logger.info("="*50)

def log_data_validation_issues(logger, pole_data):
    """
    Log potential data validation issues for a pole.
    
    Args:
        logger: Logger instance
        pole_data: Processed pole data dictionary
    """
    pole_number = pole_data.get('pole_number', 'Unknown')
    
    logger.info("\n" + "="*50)
    logger.info(f"DATA VALIDATION: {pole_number}")
    logger.info("="*50)
    
    # Check for attachers without height data
    missing_heights = []
    for attacher in pole_data.get('attachers', []):
        if attacher.get('existing_height') in (None, '', 'N/A'):
            missing_heights.append(attacher.get('description', 'Unknown'))
    
    if missing_heights:
        logger.warning(f"Found {len(missing_heights)} attachment(s) with missing height data:")
        for i, desc in enumerate(missing_heights, 1):
            logger.warning(f"  {i}. {desc}")
    else:
        logger.info("All attachments have height data.")
    
    # Check for potential height parsing issues
    parsing_issues = []
    for attacher in pole_data.get('attachers', []):
        height_str = attacher.get('existing_height')
        if height_str not in (None, '', 'N/A'):
            # Try to parse height string
            try:
                if isinstance(height_str, str) and "'" in height_str:
                    # Looks like "34'-2"" format, attempt to parse
                    feet_inches_match = re.search(r'(\d+)\'-(\d+)"', height_str)
                    if not feet_inches_match:
                        parsing_issues.append((attacher.get('description', 'Unknown'), height_str))
                elif not isinstance(height_str, (int, float)) and not str(height_str).replace('.', '', 1).isdigit():
                    # Not a valid number
                    parsing_issues.append((attacher.get('description', 'Unknown'), height_str))
            except:
                parsing_issues.append((attacher.get('description', 'Unknown'), height_str))
    
    if parsing_issues:
        logger.warning(f"Found {len(parsing_issues)} attachment(s) with potential height parsing issues:")
        for i, (desc, height) in enumerate(parsing_issues, 1):
            logger.warning(f"  {i}. {desc}: '{height}'")
    else:
        logger.info("All attachment heights can be parsed.")
    
    logger.info("="*50)

# For backward compatibility
def setup_basic_logging():
    """Set up basic logging to console."""
    logging.basicConfig(
        level=logging.INFO,
        format=DEFAULT_LOG_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)]
    ) 
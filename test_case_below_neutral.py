"""
Test case to verify that attachments below neutral are correctly identified and displayed.
"""

import json
import os
import tempfile
import make_ready_processor as mrp
import neutral_identification as ni
import excel_generator
import debug_logging
import re

# Set up logging
logger = debug_logging.get_logger('below_neutral_test')

def feet_inches_to_inches(feet_inches_str):
    """Convert a string like '29'-6"' to inches (354.0)."""
    # Parse feet and inches from the string
    match = re.search(r'(\d+)\'(?:-)?(\d+)"', feet_inches_str)
    if match:
        feet = int(match.group(1))
        inches = int(match.group(2))
        return (feet * 12) + inches
    return None

def test_below_neutral_identification():
    """Test that attachments below neutral are correctly identified and displayed."""
    # Create sample pole data with a neutral wire and attachments above and below it
    sample_pole = {
        "pole_owner": "CPS ENERGY",
        "pole_number": "PL410620",
        "pole_structure": "40-4 Southern Pine",
        "proposed_riser": "No",
        "proposed_guy": "No",
        "pla_percentage": "78.70%",
        "construction_grade": "C",
        "existing_midspan_lowest_com": "23'-10\"",
        "existing_midspan_lowest_cps_electrical": "29'-6\"",
        "midspan_proposed": "21'-4\"",
        "from_pole": "PL410620",
        "to_pole": "PL398491",
        "connections": [],
        "attachers": [
            {
                "description": "Neutral",
                "existing_height": "29'-6\"",  # Neutral wire at 29'6"
                "proposed_height": "N/A",
                "midspan_proposed": "N/A"
            },
            {
                "description": "CPS Supply Fiber",
                "existing_height": "28'-0\"",  # Below neutral
                "proposed_height": "N/A",
                "midspan_proposed": "N/A"
            },
            {
                "description": "Charter Spectrum Fiber Optic",
                "existing_height": "24'-7\"",  # Below neutral
                "proposed_height": "21'-1\"",
                "midspan_proposed": "N/A"
            },
            {
                "description": "AT&T Fiber Optic Com",
                "existing_height": "23'-7\"",  # Below neutral
                "proposed_height": "N/A",
                "midspan_proposed": "N/A"
            },
            {
                "description": "AT&T Telco Com",
                "existing_height": "22'-4\"",  # Below neutral
                "proposed_height": "N/A",
                "midspan_proposed": "N/A"
            },
            {
                "description": "AT&T Com Drop",
                "existing_height": "21'-5\"",  # Below neutral
                "proposed_height": "19'-10\"",
                "midspan_proposed": "N/A"
            }
        ]
    }
    
    # Create a neutral wire entry for identification
    highest_neutral = {
        'height': feet_inches_to_inches("29'-6\""),
        'description': 'Neutral',
        'source': 'test'
    }
    
    # Identify attachments below the neutral
    attachments_below_neutral = ni.identify_attachments_below_neutral(
        sample_pole, highest_neutral, {})
    
    # Add these to the pole data
    sample_pole['attachments_below_neutral'] = attachments_below_neutral
    
    # Generate Excel report
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
        output_path = temp_file.name
    
    excel_generator.create_make_ready_excel([sample_pole], output_path)
    
    print(f"Generated test Excel file: {output_path}")
    print(f"Highest neutral wire: {highest_neutral}")
    print(f"Found {len(attachments_below_neutral)} attachments below neutral:")
    for attachment in attachments_below_neutral:
        print(f"  - {attachment['description']} ({attachment['existing_height']})")
    
    # Verify the correct number of attachments below neutral
    expected_count = 6  # All attachers including the neutral itself with our new <= comparison
    assert len(attachments_below_neutral) == expected_count, \
           f"Expected {expected_count} attachments below neutral, found {len(attachments_below_neutral)}"
    
    return output_path, attachments_below_neutral

if __name__ == "__main__":
    output_path, attachments = test_below_neutral_identification()
    print(f"\nTest successful! Excel file generated at: {output_path}")
    print(f"Found {len(attachments)} attachments below the neutral wire:")
    for attachment in attachments:
        print(f"  - {attachment['description']} at {attachment['existing_height']}") 
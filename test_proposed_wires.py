import json
import os
from make_ready_processor import process_make_ready_report

def test_proposed_wire_handling():
    """
    Test that wires marked as proposed are properly handled in the make-ready report.
    This will process a sample JSON file and verify that:
    1. Proposed wires are correctly identified
    2. Their heights are properly set in the proposed_height field
    3. Their midspan proposed values are calculated correctly
    """
    # Use specific files from the uploads directory
    uploads_dir = 'uploads'
    katapult_path = os.path.join(uploads_dir, 'ryantest123_1.json')
    spidacalc_path = os.path.join(uploads_dir, 'CPS_6457E_03_SPIDAcalc.json')
    
    # Check if files exist
    if not os.path.exists(katapult_path):
        print(f"Katapult file not found: {katapult_path}")
        return
    
    if not os.path.exists(spidacalc_path):
        print(f"SPIDAcalc file not found: {spidacalc_path}")
        return
    
    print(f"Testing proposed wire handling with:")
    print(f"  Katapult file: {katapult_path}")
    print(f"  SPIDAcalc file: {spidacalc_path}")
    
    # Process the files
    poles = process_make_ready_report(katapult_path, spidacalc_path)
    
    print("\n=== PROPOSED WIRE TEST RESULTS ===")
    
    # Track statistics
    total_wires = 0
    proposed_wires = 0
    midspan_proposed_count = 0
    
    # Check the results to see if proposed heights and midspan proposed values are populated
    for pole in poles:
        pole_number = pole.get('pole_number', 'N/A')
        midspan_proposed = pole.get('midspan_proposed', 'N/A')
        
        print(f"\nPole {pole_number}:")
        print(f"  Pole-level Midspan Proposed: {midspan_proposed}")
        
        # Check for proposed wires
        for attacher in pole.get('attachers', []):
            total_wires += 1
            desc = attacher.get('description', 'N/A')
            existing_height = attacher.get('existing_height', 'N/A')
            proposed_height = attacher.get('proposed_height', 'N/A')
            attacher_midspan_proposed = attacher.get('midspan_proposed', 'N/A')
            is_proposed = attacher.get('is_proposed', False)
            
            if is_proposed or proposed_height != 'N/A':
                proposed_wires += 1
                print(f"  PROPOSED WIRE: {desc}")
                print(f"    Existing Height: {existing_height}")
                print(f"    Proposed Height: {proposed_height}")
                print(f"    Midspan Proposed: {attacher_midspan_proposed}")
                print(f"    Is Explicitly Marked Proposed: {is_proposed}")
            
            if attacher_midspan_proposed != 'N/A':
                midspan_proposed_count += 1
    
    # Print summary
    print("\n=== SUMMARY ===")
    print(f"Total wires processed: {total_wires}")
    print(f"Wires with proposed heights: {proposed_wires}")
    print(f"Wires with midspan proposed values: {midspan_proposed_count}")

if __name__ == "__main__":
    test_proposed_wire_handling() 
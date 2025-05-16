import json
import os
from make_ready_processor import process_make_ready_report

def test_midspan_proposed():
    """
    Test the midspan proposed calculation with a real data sample.
    This will process a sample JSON file and output detailed information
    about the midspan proposed calculations.
    """
    # Get a list of Katapult and SPIDAcalc files in the uploads directory
    uploads_dir = 'uploads'
    katapult_files = []
    spidacalc_files = []
    
    for file in os.listdir(uploads_dir):
        file_path = os.path.join(uploads_dir, file)
        if file_path.endswith('.json'):
            if 'Katapult' in file:
                katapult_files.append(file_path)
            elif 'SPIDAcalc' in file:
                spidacalc_files.append(file_path)
    
    # If we have both types of files, process the first pair
    if katapult_files and spidacalc_files:
        katapult_path = katapult_files[0]
        spidacalc_path = spidacalc_files[0]
        
        print(f"Testing with Katapult file: {katapult_path}")
        print(f"Testing with SPIDAcalc file: {spidacalc_path}")
        
        # Process the files
        poles = process_make_ready_report(katapult_path, spidacalc_path)
        
        # Check the results to see if midspan proposed values are populated
        for pole in poles:
            pole_number = pole.get('pole_number', 'N/A')
            midspan_proposed = pole.get('midspan_proposed', 'N/A')
            
            print(f"\nPole {pole_number}:")
            print(f"  Midspan Proposed: {midspan_proposed}")
            
            # Check for attachers with height changes
            attachers_with_changes = []
            for attacher in pole.get('attachers', []):
                existing_height = attacher.get('existing_height', 'N/A')
                proposed_height = attacher.get('proposed_height', 'N/A')
                attacher_midspan_proposed = attacher.get('midspan_proposed', 'N/A')
                
                if existing_height != 'N/A' and proposed_height != 'N/A' and existing_height != proposed_height:
                    attachers_with_changes.append({
                        'description': attacher.get('description', 'N/A'),
                        'existing_height': existing_height,
                        'proposed_height': proposed_height,
                        'midspan_proposed': attacher_midspan_proposed
                    })
            
            if attachers_with_changes:
                print(f"  Attachers with height changes:")
                for i, attacher in enumerate(attachers_with_changes):
                    print(f"    {i+1}. {attacher['description']}")
                    print(f"       Existing Height: {attacher['existing_height']}")
                    print(f"       Proposed Height: {attacher['proposed_height']}")
                    print(f"       Midspan Proposed: {attacher['midspan_proposed']}")
            else:
                print("  No attachers with height changes found.")
    else:
        print("No suitable test files found in uploads directory.")

if __name__ == "__main__":
    test_midspan_proposed()

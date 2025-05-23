from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
import json
import os
import time
import logging
import traceback
from werkzeug.utils import secure_filename
from flask_session import Session  # Add import for Flask-Session
from make_ready_processor import process_make_ready_report
from excel_generator import create_make_ready_excel

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SESSION_TYPE'] = 'filesystem'  # Use filesystem-based sessions instead of cookies
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # Session lifetime in seconds (1 hour)
app.config['SESSION_FILE_DIR'] = os.path.join(app.config['UPLOAD_FOLDER'], 'flask_session')

# Initialize Flask-Session
Session(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# Create a directory for temporary processed data
TEMP_DATA_DIR = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_data')
os.makedirs(TEMP_DATA_DIR, exist_ok=True)
# Create directory for Flask sessions
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'json'

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'katapult' not in request.files or request.files['katapult'].filename == '':
            flash('Katapult JSON file is required.', 'danger')
            return redirect(url_for('index'))
        
        katapult_file = request.files['katapult']
        spidacalc_file = request.files.get('spidacalc')

        if not allowed_file(katapult_file.filename):
            flash('Invalid Katapult file type. Please upload a .json file.', 'danger')
            return redirect(url_for('index'))

        # Save Katapult file
        katapult_filename = secure_filename(katapult_file.filename)
        katapult_path = os.path.join(app.config['UPLOAD_FOLDER'], katapult_filename)
        katapult_file.save(katapult_path)
        
        # Verify Katapult JSON is valid
        try:
            with open(katapult_path, 'r', encoding='utf-8') as f:
                katapult_data = json.load(f)
            if not isinstance(katapult_data, dict):
                raise ValueError("Katapult JSON must be an object")
            if 'nodes' not in katapult_data:
                raise ValueError("Katapult JSON must contain a 'nodes' field")
        except json.JSONDecodeError as e:
            flash(f'Invalid Katapult JSON format: {str(e)}', 'danger')
            return redirect(url_for('index'))
        except ValueError as e:
            flash(f'Invalid Katapult JSON structure: {str(e)}', 'danger')
            return redirect(url_for('index'))

        # Handle SPIDAcalc file if provided
        spidacalc_path = None
        if spidacalc_file and spidacalc_file.filename != '':
            if not allowed_file(spidacalc_file.filename):
                flash('Invalid SPIDAcalc file type. Please upload a .json file.', 'danger')
                return redirect(url_for('index'))
            
            spidacalc_filename = secure_filename(spidacalc_file.filename)
            spidacalc_path = os.path.join(app.config['UPLOAD_FOLDER'], spidacalc_filename)
            spidacalc_file.save(spidacalc_path)
            
            # Verify SPIDAcalc JSON is valid
            try:
                with open(spidacalc_path, 'r', encoding='utf-8') as f:
                    spidacalc_data = json.load(f)
                if not isinstance(spidacalc_data, dict):
                    raise ValueError("SPIDAcalc JSON must be an object")
                if 'leads' not in spidacalc_data:
                    raise ValueError("SPIDAcalc JSON must contain a 'leads' field")
            except json.JSONDecodeError as e:
                flash(f'Invalid SPIDAcalc JSON format: {str(e)}', 'danger')
                return redirect(url_for('index'))
            except ValueError as e:
                flash(f'Invalid SPIDAcalc JSON structure: {str(e)}', 'danger')
                return redirect(url_for('index'))

        # Process target poles if provided
        target_poles = None
        target_poles_text = request.form.get('target_poles', '').strip()
        if target_poles_text:
            # Split by commas, spaces, or newlines and filter out empty strings
            import re
            target_poles = [pole.strip() for pole in re.split(r'[,\s]+', target_poles_text) if pole.strip()]
            logger.info(f"Processing {len(target_poles)} target poles: {target_poles}")
        
        # Get conflict resolution strategies
        attachment_height_strategy = request.form.get('attachment_height_strategy', 'PREFER_KATAPULT')
        pole_attribute_strategy = request.form.get('pole_attribute_strategy', 'PREFER_KATAPULT')
        logger.info(f"Using conflict resolution strategies - Attachment Height: {attachment_height_strategy}, Pole Attributes: {pole_attribute_strategy}")
            
        # Process the files
        try:
            report_data = process_make_ready_report(
                katapult_path, 
                spidacalc_path, 
                target_poles=target_poles,
                attachment_height_strategy=attachment_height_strategy,
                pole_attribute_strategy=pole_attribute_strategy
            )
            if not report_data:
                flash('No pole data found in the uploaded files.', 'warning')
                return redirect(url_for('index'))
            
            # Save processed data to a temporary file instead of storing it in the session
            timestamp = int(time.time())
            processed_data_path = os.path.join(TEMP_DATA_DIR, f"processed_data_{timestamp}.json")
            with open(processed_data_path, 'w') as f:
                json.dump(report_data, f)
            
            # Only store file paths and parameters in session (much smaller)
            session['processed_data_path'] = processed_data_path
            session['katapult_path'] = katapult_path
            session['spidacalc_path'] = spidacalc_path
            session['target_poles'] = target_poles
            session['attachment_height_strategy'] = attachment_height_strategy
            session['pole_attribute_strategy'] = pole_attribute_strategy
            session['timestamp'] = timestamp
                
            # Extract geographic data for map display
            pole_geo_data = []
            for pole in report_data:
                if pole.get('latitude') and pole.get('longitude'):
                    pole_geo_data.append({
                        'pole_number': pole.get('pole_number'),
                        'pole_owner': pole.get('pole_owner'),
                        'pole_structure': pole.get('pole_structure'),
                        'latitude': pole.get('latitude'),
                        'longitude': pole.get('longitude'),
                        'status': pole.get('status', 'No Change')
                    })
            
            # Calculate map center if we have geo data
            map_center = None
            if pole_geo_data:
                total_lat = sum(p['latitude'] for p in pole_geo_data)
                total_lng = sum(p['longitude'] for p in pole_geo_data)
                count = len(pole_geo_data)
                map_center = {
                    'latitude': total_lat / count,
                    'longitude': total_lng / count
                }
            
            return render_template('results.html', 
                                  poles=report_data, 
                                  pole_geo_data=pole_geo_data,
                                  map_center=map_center)
        except Exception as e:
            logger.error(f"Error processing files: {str(e)}")
            logger.error(traceback.format_exc())
            flash(f'Error processing files: {str(e)}', 'danger')
            return redirect(url_for('index'))

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f'An unexpected error occurred: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/download_excel_report', methods=['GET'])
def download_excel_report():
    try:
        # Try to get the processed data path from session
        processed_data_path = session.get('processed_data_path')
        
        processed_poles = None
        if processed_data_path and os.path.exists(processed_data_path):
            # Load processed data from the temporary file
            try:
                with open(processed_data_path, 'r') as f:
                    processed_poles = json.load(f)
            except Exception as e:
                logger.error(f"Error loading processed data: {str(e)}")
                # Will continue to try reprocessing
        
        # If no processed data available, try to reprocess
        if not processed_poles:
            # Get parameters from session
            katapult_path = session.get('katapult_path')
            spidacalc_path = session.get('spidacalc_path')
            target_poles = session.get('target_poles')
            attachment_height_strategy = session.get('attachment_height_strategy')
            pole_attribute_strategy = session.get('pole_attribute_strategy')
            
            # Check if the input files exist
            if not katapult_path or not os.path.exists(katapult_path):
                flash('Please upload the files again. The original files are no longer available.', 'warning')
                return redirect(url_for('index'))
            
            # Check if SPIDAcalc path exists if it was provided
            if spidacalc_path and not os.path.exists(spidacalc_path):
                spidacalc_path = None
                logger.warning("SPIDAcalc file no longer exists, proceeding with Katapult only")
            
            logger.info(f"Reprocessing data from: Katapult={katapult_path}, SPIDAcalc={spidacalc_path}")
            processed_poles = process_make_ready_report(
                katapult_path, 
                spidacalc_path, 
                target_poles=target_poles,
                attachment_height_strategy=attachment_height_strategy,
                pole_attribute_strategy=pole_attribute_strategy
            )
            
            if not processed_poles:
                flash('No pole data found for export. Please try uploading the files again.', 'warning')
                return redirect(url_for('index'))
        
        # Generate a timestamped filename
        timestamp = session.get('timestamp', int(time.time()))
        excel_filename = f"make_ready_report_{timestamp}.xlsx"
        excel_path = os.path.join(app.config['UPLOAD_FOLDER'], excel_filename)
        
        # Generate Excel file
        create_make_ready_excel(processed_poles, excel_path)
        
        # Send file for download
        return send_file(
            excel_path,
            as_attachment=True,
            download_name="make_ready_report.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        logger.error(f"Error generating Excel report: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f'Error generating Excel report: {str(e)}', 'danger')
        return redirect(url_for('index'))

# Clean up temporary files periodically
@app.before_request
def cleanup_temp_files():
    try:
        # Clean up files older than 1 day
        current_time = time.time()
        for filename in os.listdir(TEMP_DATA_DIR):
            file_path = os.path.join(TEMP_DATA_DIR, filename)
            if os.path.isfile(file_path):
                file_creation_time = os.path.getctime(file_path)
                if current_time - file_creation_time > 86400:  # 24 hours in seconds
                    os.remove(file_path)
    except Exception as e:
        logger.error(f"Error cleaning up temporary files: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)

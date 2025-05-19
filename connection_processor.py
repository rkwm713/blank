# connection_processor.py
import logging
from utils import get_pole_number_from_node_id, inches_to_feet_inches_str
from trace_utils import get_trace_by_id, extract_wire_metadata
from wire_utils import process_wire_height
from reference_utils import process_reference_span

logger = logging.getLogger(__name__)

def process_pole_connections(node_id, pole_number, katapult, pole_sequence):
    """
    Process connections for a pole.
    
    Args:
        node_id (str): Node ID of the pole
        pole_number (str): Pole number
        katapult (dict): Full Katapult data
        pole_sequence (list): Ordered sequence of pole IDs
        
    Returns:
        tuple: (pole_connections, midspan_data, reference_spans)
    """
    pole_connections = []
    processed_connections = set()
    reference_spans = []
    
    # Process each connection involving this pole
    for conn_id, conn in katapult.get('connections', {}).items():
        # Skip if not involving this pole
        if conn.get('node_id_1') != node_id and conn.get('node_id_2') != node_id:
            continue
        
        # Get the other pole number
        other_node_id = conn.get('node_id_2') if conn.get('node_id_1') == node_id else conn.get('node_id_1')
        other_pole_number = get_pole_number_from_node_id(katapult, other_node_id)
        
        # Process connection data
        connection_lowest_com = None
        connection_lowest_cps = None
        
        # Process sections for this connection
        for section_id, section in conn.get('sections', {}).items():
            if not isinstance(section, dict):
                continue
                
            # Process photos in each section
            for photo_id, photo_association in section.get('photos', {}).items():
                if not isinstance(photo_association, dict):
                    continue
                    
                # Get the full photo data
                main_photo_data = katapult.get('photos', {}).get(photo_id, {})
                if not isinstance(main_photo_data, dict):
                    continue
                    
                # Get photofirst data
                photofirst_data = main_photo_data.get('photofirst_data', {})
                if not isinstance(photofirst_data, dict):
                    continue
                    
                # Process wire data
                wire_data = photofirst_data.get('wire', {})
                wire_items = []
                
                if isinstance(wire_data, list):
                    wire_items = wire_data
                elif isinstance(wire_data, dict):
                    wire_items = list(wire_data.values())
                else:
                    continue
                
                # Process each wire
                for wire in wire_items:
                    if not isinstance(wire, dict):
                        continue
                        
                    # Get trace data
                    trace_id = wire.get('_trace', '').strip()
                    if not trace_id:
                        continue
                    
                    trace = get_trace_by_id(katapult, trace_id)
                    
                    # Extract metadata
                    wire_meta = extract_wire_metadata(wire, trace)
                    owner = wire_meta['owner']
                    cable_type = wire_meta['cable_type']
                    
                    # Get wire height
                    h = process_wire_height(wire)
                    if h is None:
                        continue
                    
                    # Classify wire
                    is_comm = classify_wire_communication(owner, cable_type, trace)
                    is_cps_elec = classify_wire_cps_electrical(owner, cable_type, trace)
                    
                    # Update lowest heights
                    if is_comm and (connection_lowest_com is None or h < connection_lowest_com):
                        connection_lowest_com = h
                    
                    if is_cps_elec and (connection_lowest_cps is None or h < connection_lowest_cps):
                        connection_lowest_cps = h
        
        # Add to connections list
        pole_connections.append({
            'connection_id': conn_id,
            'from_pole': pole_number,
            'to_pole': other_pole_number,
            'lowest_com': connection_lowest_com,
            'lowest_cps': connection_lowest_cps
        })
        
        # Is this a reference span?
        is_reference = check_if_reference_span(conn_id, conn)
        
        if is_reference:
            # Process as reference span
            ref_header, ref_attachments = process_reference_span(
                katapult, 
                current_node_id=node_id,
                other_node_id=other_node_id,
                conn_id=conn_id,
                conn_data=conn,
                is_backspan=False
            )
            
            reference_spans.append({
                'header': ref_header,
                'attachments': ref_attachments
            })
            
            # Mark as processed
            processed_connections.add(conn_id)
    
    # If we have a pole sequence, check for backspan
    backspan = None
    if pole_sequence:
        from utils import normalize_pole_id
        norm_pole_number = normalize_pole_id(pole_number)
        try:
            current_pole_index = pole_sequence.index(norm_pole_number)
            if current_pole_index > 0:
                previous_pole_id = pole_sequence[current_pole_index - 1]
                
                # Find the node ID for the previous pole
                previous_pole_node_id = None
                for node_id_check, node_data in katapult.get('nodes', {}).items():
                    check_pole_number = get_pole_number_from_node_id(katapult, node_id_check)
                    if check_pole_number and normalize_pole_id(check_pole_number) == previous_pole_id:
                        previous_pole_node_id = node_id_check
                        break
                
                if previous_pole_node_id:
                    # Find the connection between this pole and the previous pole
                    for conn_id, conn_data in katapult.get('connections', {}).items():
                        if conn_id in processed_connections:
                            continue
                            
                        if (
                            (conn_data.get('node_id_1') == node_id and conn_data.get('node_id_2') == previous_pole_node_id) or
                            (conn_data.get('node_id_2') == node_id and conn_data.get('node_id_1') == previous_pole_node_id)
                        ):
                            # Process as backspan
                            backspan_header, backspan_attachments = process_reference_span(
                                katapult, 
                                current_node_id=node_id,
                                other_node_id=previous_pole_node_id,
                                conn_id=conn_id,
                                conn_data=conn_data,
                                is_backspan=True,
                                previous_pole_id=previous_pole_id
                            )
                            
                            backspan = {
                                'header': backspan_header,
                                'attachments': backspan_attachments
                            }
                            
                            # Mark as processed
                            processed_connections.add(conn_id)
                            break
        except ValueError:
            # Pole not found in sequence
            pass
    
    # Find primary span data
    midspan_data = calculate_midspan_data(pole_connections, pole_number)
    
    return pole_connections, midspan_data, reference_spans, backspan

def classify_wire_communication(owner, cable_type, trace):
    """Determine if a wire is a communication wire."""
    # If owner is not CPS, check for comm indicators
    if owner and 'cps' not in owner.lower():
        # Check cable type in trace
        if trace:
            cable_type_comm = trace.get('cable_type', '')
            if any(comm_type in (cable_type_comm or '').lower()
                   for comm_type in ['com', 'fiber', 'telco', 'cable', 'telephone', 'catv']):
                return True
        
        # Check owner name for comm companies
        if any(comm_co in owner.lower() 
              for comm_co in ['att', 'spectrum', 'comcast', 'frontier', 'verizon', 'telco']):
            return True
    
    return False

def classify_wire_cps_electrical(owner, cable_type, trace):
    """Determine if a wire is a CPS electrical wire."""
    # Check if owner is CPS
    if owner and 'cps' in owner.lower():
        # Check cable type
        if trace:
            cable_type_elec = trace.get('cable_type', '')
            if any(elec_type in (cable_type_elec or '').lower()
                   for elec_type in ['neutral', 'secondary', 'primary', 'electric', 'power', 'phase']):
                return True
            
            # If no cable type but owner is CPS, assume it's electrical
            elif not cable_type_elec:
                return True
        
        # If trace not available but owner is CPS, assume electrical
        return True
    
    return False

def check_if_reference_span(conn_id, conn_data):
    """Determine if a connection is a reference span."""
    connection_attributes = conn_data.get('attributes', {})
    
    # Method 1: Check connection_type.button_added
    connection_type_attrs = connection_attributes.get('connection_type', {})
    if isinstance(connection_type_attrs, dict) and connection_type_attrs.get('button_added') == 'reference':
        return True
    
    # Method 2: Check direct button_added
    if connection_attributes.get('button_added') == 'reference':
        return True
    
    # Method 3: Check reference attribute
    ref_attr = connection_attributes.get('reference')
    if ref_attr is True or (isinstance(ref_attr, str) and ref_attr.lower() == 'true'):
        return True
    
    # Method 4: Check various span type attributes
    for key in ['span_type', 'spanType', 'connection_classification', 'span_classification']:
        span_type_value = connection_attributes.get(key)
        if span_type_value:
            if isinstance(span_type_value, dict):
                span_type = next(iter(span_type_value.values()), None)
            else:
                span_type = span_type_value
            
            if span_type and isinstance(span_type, str) and 'reference' in span_type.lower():
                return True
    
    return False

def calculate_midspan_data(pole_connections, pole_number):
    """Calculate midspan data for a pole."""
    # Default values
    midspan_data = {
        'existing_midspan_lowest_com': 'N/A',
        'existing_midspan_lowest_cps_electrical': 'N/A',
        'from_pole': pole_number,
        'to_pole': 'N/A'
    }
    
    if not pole_connections:
        return midspan_data
    
    # Find the best connection to use
    primary_connection = None
    
    # First try to find a connection with valid to_pole
    for conn in pole_connections:
        if conn.get('from_pole') and conn.get('to_pole') and conn['to_pole'] != 'N/A':
            primary_connection = conn
            break
    
    # If not found, use the first connection
    if not primary_connection and pole_connections:
        primary_connection = pole_connections[0]
    
    if primary_connection:
        midspan_data = {
            'existing_midspan_lowest_com': inches_to_feet_inches_str(primary_connection['lowest_com']),
            'existing_midspan_lowest_cps_electrical': inches_to_feet_inches_str(primary_connection['lowest_cps']),
            'from_pole': primary_connection['from_pole'] or pole_number,
            'to_pole': primary_connection['to_pole'] or 'N/A'
        }
    
    return midspan_data
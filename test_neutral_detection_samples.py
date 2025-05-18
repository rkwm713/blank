"""
Sample tests for neutral wire detection and attachment filtering.

This file contains sample test cases that verify the neutral wire detection
and attachment filtering logic with realistic data examples.
"""

import unittest
import json
import os
from unittest.mock import patch, MagicMock

import neutral_identification as ni
import debug_logging

# Configure test logger
debug_logging.setup_basic_logging()
logger = debug_logging.get_logger('test_neutral_detection_samples')

class TestNeutralDetectionSamples(unittest.TestCase):
    """Test cases for neutral wire detection with sample data."""
    
    def setUp(self):
        """Set up test data for each test."""
        # Create sample Katapult pole data
        self.sample_katapult_pole = {
            'pole_number': 'SAMPLE123',
            'photos': {
                'photo1': {
                    'photofirst_data': {
                        'wire': [
                            {
                                '_trace': 'trace_neutral',
                                '_measured_height': '336'  # 28'-0"
                            },
                            {
                                '_trace': 'trace_primary',
                                '_measured_height': '360'  # 30'-0"
                            },
                            {
                                '_trace': 'trace_comm1',
                                '_measured_height': '306'  # 25'-6"
                            },
                            {
                                '_trace': 'trace_comm2',
                                '_measured_height': '264'  # 22'-0"
                            }
                        ]
                    }
                }
            },
            'attachers': [
                {
                    'description': 'CPS ENERGY NEUTRAL',
                    'existing_height': "28'-0\""
                },
                {
                    'description': 'CPS ENERGY PRIMARY',
                    'existing_height': "30'-0\""
                },
                {
                    'description': 'AT&T FIBER',
                    'existing_height': "25'-6\""
                },
                {
                    'description': 'SPECTRUM CATV',
                    'existing_height': "22'-0\""
                }
            ]
        }
        
        # Create sample Katapult data with traces
        self.sample_katapult = {
            'traces': {
                'trace_neutral': {
                    'company': 'CPS ENERGY',
                    'cable_type': 'NEUTRAL'
                },
                'trace_primary': {
                    'company': 'CPS ENERGY',
                    'cable_type': 'PRIMARY'
                },
                'trace_comm1': {
                    'company': 'AT&T',
                    'cable_type': 'FIBER'
                },
                'trace_comm2': {
                    'company': 'SPECTRUM',
                    'cable_type': 'CATV'
                }
            }
        }
        
        # Create sample SPIDAcalc pole data
        self.sample_spidacalc_pole = {
            'designs': [
                {
                    'label': 'Measured Design',
                    'structure': {
                        'wires': [
                            {
                                'owner': {'id': 'CPS ENERGY'},
                                'clientItem': {'type': 'NEUTRAL', 'description': 'NEUTRAL WIRE'},
                                'usageGroup': 'NEUTRAL',
                                'attachmentHeight': {'value': 8.53}  # ~28'-0" in meters
                            },
                            {
                                'owner': {'id': 'CPS ENERGY'},
                                'clientItem': {'type': 'PRIMARY', 'description': 'PRIMARY WIRE'},
                                'usageGroup': 'PRIMARY',
                                'attachmentHeight': {'value': 9.14}  # ~30'-0" in meters
                            },
                            {
                                'owner': {'id': 'AT&T'},
                                'clientItem': {'type': 'FIBER', 'description': 'FIBER OPTIC'},
                                'usageGroup': 'COMMUNICATION',
                                'attachmentHeight': {'value': 7.77}  # ~25'-6" in meters
                            },
                            {
                                'owner': {'id': 'SPECTRUM'},
                                'clientItem': {'type': 'CATV', 'description': 'CABLE TV'},
                                'usageGroup': 'COMMUNICATION',
                                'attachmentHeight': {'value': 6.71}  # ~22'-0" in meters
                            }
                        ]
                    }
                }
            ]
        }
    
    def test_katapult_neutral_identification(self):
        """Test identifying neutral wires from Katapult data."""
        # Mock get_trace_by_id to return our sample trace data
        with patch('neutral_identification.get_trace_by_id', side_effect=lambda k, tid: self.sample_katapult['traces'].get(tid, {})):
            neutral_wires = ni.identify_neutrals_katapult(self.sample_katapult_pole, self.sample_katapult)
            
            # We should find one neutral wire (CPS ENERGY NEUTRAL)
            self.assertEqual(len(neutral_wires), 1)
            self.assertEqual(neutral_wires[0]['height'], 336.0)
            self.assertEqual(neutral_wires[0]['description'], 'CPS ENERGY NEUTRAL')
    
    def test_spidacalc_neutral_identification(self):
        """Test identifying neutral wires from SPIDAcalc data."""
        neutral_wires = ni.identify_neutrals_spidacalc(self.sample_katapult_pole, self.sample_spidacalc_pole)
        
        # We should find one neutral wire
        self.assertEqual(len(neutral_wires), 1)
        self.assertAlmostEqual(neutral_wires[0]['height'], 335.8, places=1)  # 8.53 meters ≈ 335.8 inches
        # Test that the description contains both the owner and neutral keyword
        self.assertIn('CPS ENERGY', neutral_wires[0]['description'].upper())
        self.assertIn('NEUTRAL', neutral_wires[0]['description'].upper())
    
    def test_highest_neutral_identification(self):
        """Test finding the highest neutral wire when both sources have neutral data."""
        # Create neutrals from both sources with slightly different heights
        neutral_katapult = {
            'height': 336.0,
            'description': 'CPS ENERGY NEUTRAL (Katapult)',
            'source': 'katapult'
        }
        
        neutral_spida = {
            'height': 335.8,
            'description': 'CPS ENERGY NEUTRAL (SPIDAcalc)',
            'source': 'spidacalc'
        }
        
        highest_neutral = ni.get_highest_neutral([neutral_katapult, neutral_spida])
        
        # Katapult neutral should be identified as highest
        self.assertEqual(highest_neutral['height'], 336.0)
        self.assertEqual(highest_neutral['source'], 'katapult')
    
    @patch('neutral_identification.visualize_pole_attachments')
    def test_attachments_below_neutral(self, mock_visualize):
        """Test identifying attachments below the neutral wire."""
        # Create a sample neutral wire
        neutral_wire = {
            'height': 336.0,  # 28'-0"
            'description': 'CPS ENERGY NEUTRAL',
            'source': 'test'
        }
        
        # Identify attachments below this neutral
        attachments = ni.identify_attachments_below_neutral(
            self.sample_katapult_pole, neutral_wire, self.sample_katapult)
        
        # We expect two attachments below the neutral (AT&T FIBER and SPECTRUM CATV)
        self.assertEqual(len(attachments), 2)
        
        # Verify the descriptions match what we expect
        descriptions = sorted([a['description'] for a in attachments])
        self.assertEqual(descriptions, ['AT&T FIBER', 'SPECTRUM CATV'])
        
        # Verify attachments at or above neutral are not included
        for attachment in attachments:
            self.assertNotEqual(attachment['description'], 'CPS ENERGY NEUTRAL')
            self.assertNotEqual(attachment['description'], 'CPS ENERGY PRIMARY')
    
    @patch('neutral_identification.visualize_pole_attachments')
    def test_no_neutral_wire(self, mock_visualize):
        """Test behavior when no neutral wire is found."""
        # Create a pole with no neutral in attachers
        pole_no_neutral = {
            'pole_number': 'NO_NEUTRAL_123',
            'attachers': [
                {
                    'description': 'AT&T FIBER',
                    'existing_height': "25'-6\""
                },
                {
                    'description': 'SPECTRUM CATV',
                    'existing_height': "22'-0\""
                }
            ]
        }
        
        # Run with no neutral wire
        attachments = ni.identify_attachments_below_neutral(
            pole_no_neutral, None, None)
        
        # Should include all attachments when no neutral is found
        self.assertEqual(len(attachments), 2)
        descriptions = sorted([a['description'] for a in attachments])
        self.assertEqual(descriptions, ['AT&T FIBER', 'SPECTRUM CATV'])
    
    def test_edge_case_multiple_neutrals(self):
        """Test case with multiple neutrals at different heights."""
        # Create a sample with two neutrals at different heights
        pole_multiple_neutrals = {
            'pole_number': 'MULTI_NEUTRAL_123',
            'photos': {
                'photo1': {
                    'photofirst_data': {
                        'wire': [
                            {
                                '_trace': 'trace_neutral1',
                                '_measured_height': '336'  # 28'-0"
                            },
                            {
                                '_trace': 'trace_neutral2',
                                '_measured_height': '324'  # 27'-0"
                            },
                            {
                                '_trace': 'trace_comm1',
                                '_measured_height': '306'  # 25'-6"
                            }
                        ]
                    }
                }
            }
        }
        
        katapult_data = {
            'traces': {
                'trace_neutral1': {
                    'company': 'CPS ENERGY',
                    'cable_type': 'NEUTRAL'
                },
                'trace_neutral2': {
                    'company': 'CPS ENERGY',
                    'cable_type': 'SECONDARY NEUTRAL'
                },
                'trace_comm1': {
                    'company': 'AT&T',
                    'cable_type': 'FIBER'
                }
            }
        }
        
        # Mock get_trace_by_id to return our sample trace data
        with patch('neutral_identification.get_trace_by_id', side_effect=lambda k, tid: katapult_data['traces'].get(tid, {})):
            neutral_wires = ni.identify_neutrals_katapult(pole_multiple_neutrals, katapult_data)
            
            # We should find two neutral wires
            self.assertEqual(len(neutral_wires), 2)
            
            # Highest should be identified correctly
            highest_neutral = ni.get_highest_neutral(neutral_wires)
            self.assertEqual(highest_neutral['height'], 336.0)

if __name__ == '__main__':
    unittest.main() 
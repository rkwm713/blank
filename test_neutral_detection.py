"""
Unit tests for neutral wire detection and attachment filtering logic.

This module contains tests to verify the correct functioning of the neutral wire
identification and attachment filtering logic in the make-ready report generation.
"""

import unittest
import json
import os
from unittest.mock import patch, MagicMock

import neutral_identification as ni

class TestNeutralWireIdentification(unittest.TestCase):
    """Test cases for neutral wire identification functions."""
    
    def test_is_neutral_wire(self):
        """Test the is_neutral_wire function with various descriptions."""
        # Positive cases - these should be identified as neutral wires
        self.assertTrue(ni.is_neutral_wire("neutral"))
        self.assertTrue(ni.is_neutral_wire("CPS ENERGY NEUTRAL"))
        self.assertTrue(ni.is_neutral_wire("primary neutral"))
        self.assertTrue(ni.is_neutral_wire("SecondaryNeutral"))
        self.assertTrue(ni.is_neutral_wire("CPS neutral wire"))
        self.assertTrue(ni.is_neutral_wire("electric utility neutral"))
        
        # Negative cases - these should NOT be identified as neutral wires
        self.assertFalse(ni.is_neutral_wire(""))
        self.assertFalse(ni.is_neutral_wire(None))
        self.assertFalse(ni.is_neutral_wire("fiber"))
        self.assertFalse(ni.is_neutral_wire("AT&T CATV"))
        self.assertFalse(ni.is_neutral_wire("SPECTRUM Fiber"))
        self.assertFalse(ni.is_neutral_wire("CPS primary"))  # without "neutral"
    
    def test_normalize_height_to_inches(self):
        """Test height normalization function."""
        # Test inches conversion (no change)
        self.assertEqual(ni.normalize_height_to_inches(36.0, 'inches'), 36.0)
        self.assertEqual(ni.normalize_height_to_inches("36.0", 'inches'), 36.0)
        
        # Test meters conversion
        meters_value = 1.0  # 1 meter = 39.3701 inches
        expected_inches = 39.3701
        self.assertAlmostEqual(ni.normalize_height_to_inches(meters_value, 'meters'), expected_inches)
        
        # Test handling of invalid inputs
        self.assertIsNone(ni.normalize_height_to_inches(None))
        self.assertIsNone(ni.normalize_height_to_inches("not a number"))
        
        # Test default unit
        self.assertEqual(ni.normalize_height_to_inches(36.0), 36.0)  # Default is inches
    
    def test_get_highest_neutral(self):
        """Test finding the highest neutral wire."""
        # Create test data
        neutral_wires = [
            {'height': 300.0, 'description': 'Neutral 1'},
            {'height': 350.0, 'description': 'Neutral 2'},  # Highest
            {'height': 320.0, 'description': 'Neutral 3'}
        ]
        
        # Test with multiple neutrals
        highest = ni.get_highest_neutral(neutral_wires)
        self.assertEqual(highest['height'], 350.0)
        self.assertEqual(highest['description'], 'Neutral 2')
        
        # Test with single neutral
        single_neutral = [{'height': 300.0, 'description': 'Neutral 1'}]
        highest = ni.get_highest_neutral(single_neutral)
        self.assertEqual(highest['height'], 300.0)
        
        # Test with empty list
        self.assertIsNone(ni.get_highest_neutral([]))
        self.assertIsNone(ni.get_highest_neutral(None))

class TestAttachmentFiltering(unittest.TestCase):
    """Test cases for attachment filtering logic."""
    
    def setUp(self):
        """Set up test data for each test."""
        # Create a sample pole data structure
        self.pole_data = {
            'pole_number': 'TEST123',
            'attachers': [
                {
                    'description': 'AT&T Fiber',
                    'existing_height': "25'-6\""  # 306 inches
                },
                {
                    'description': 'CPS Primary',
                    'existing_height': "30'-0\""  # 360 inches
                },
                {
                    'description': 'CPS Neutral',
                    'existing_height': "28'-0\""  # 336 inches
                },
                {
                    'description': 'SPECTRUM CATV',
                    'existing_height': "22'-0\""  # 264 inches
                },
                {
                    'description': 'Missing Height',
                    'existing_height': None
                }
            ]
        }
        
        # Create a sample neutral wire
        self.neutral_wire = {
            'height': 336.0,  # 28'-0"
            'description': 'CPS Neutral',
            'source': 'test'
        }
    
    @patch('neutral_identification.visualize_pole_attachments')
    def test_identify_attachments_below_neutral(self, mock_visualize):
        """Test identifying attachments below the neutral wire."""
        # Run the function
        attachments = ni.identify_attachments_below_neutral(
            self.pole_data, self.neutral_wire, None)
        
        # Verify the visualization was called
        mock_visualize.assert_called_once()
        
        # We expect two attachments below the neutral at 28'-0" (336 inches):
        # - AT&T Fiber at 25'-6" (306 inches)
        # - SPECTRUM CATV at 22'-0" (264 inches)
        self.assertEqual(len(attachments), 2)
        
        # Verify the descriptions match what we expect
        descriptions = [a['description'] for a in attachments]
        self.assertIn('AT&T Fiber', descriptions)
        self.assertIn('SPECTRUM CATV', descriptions)
        
        # Verify attachments at or above neutral are not included
        self.assertNotIn('CPS Primary', descriptions)
        self.assertNotIn('CPS Neutral', descriptions)
        
        # Verify attachment with missing height is not included
        self.assertNotIn('Missing Height', descriptions)
    
    @patch('neutral_identification.visualize_pole_attachments')
    def test_no_neutral_wire(self, mock_visualize):
        """Test behavior when no neutral wire is found."""
        # Run with no neutral wire
        attachments = ni.identify_attachments_below_neutral(
            self.pole_data, None, None)
        
        # Should include all attachments when no neutral is found
        self.assertEqual(len(attachments), 5)
    
    @patch('neutral_identification.visualize_pole_attachments')
    def test_exactly_at_neutral_height(self, mock_visualize):
        """Test behavior for attachment exactly at neutral height."""
        # Add an attachment exactly at neutral height
        self.pole_data['attachers'].append({
            'description': 'Exact Match',
            'existing_height': "28'-0\""  # 336 inches, same as neutral
        })
        
        # Run the function
        attachments = ni.identify_attachments_below_neutral(
            self.pole_data, self.neutral_wire, None)
        
        # Attachment at exactly neutral height should be included (<= comparison)
        descriptions = [a['description'] for a in attachments]
        self.assertIn('Exact Match', descriptions)

class TestEndToEndIntegration(unittest.TestCase):
    """Integration tests for the entire neutral/attachment identification process."""
    
    @patch('neutral_identification.get_trace_by_id')
    def test_katapult_neutral_identification(self, mock_get_trace):
        """Test identifying neutral wires from Katapult data."""
        # Mock the trace data that would be returned
        mock_get_trace.return_value = {
            'company': 'CPS ENERGY',
            'cable_type': 'NEUTRAL'
        }
        
        # Create a sample pole with photo containing a neutral wire
        pole_data = {
            'pole_number': 'TEST456',
            'photos': {
                'photo1': {
                    'photofirst_data': {
                        'wire': [
                            {
                                '_trace': 'trace123',
                                '_measured_height': '336'  # 28'-0"
                            }
                        ]
                    }
                }
            }
        }
        
        # Call the function
        neutral_wires = ni.identify_neutrals_katapult(pole_data, {})
        
        # Verify a neutral wire was identified
        self.assertEqual(len(neutral_wires), 1)
        self.assertEqual(neutral_wires[0]['height'], 336.0)
        self.assertEqual(neutral_wires[0]['source'], 'katapult')

if __name__ == '__main__':
    unittest.main() 
"""
Tests for utility functions.
"""

import pytest
import pandas as pd
import os
import tempfile
from unittest.mock import patch, mock_open
from dop1.utils import load_data, validate_data, save_results, format_patient_data, create_summary_report
from dop1.exceptions import ValidationError


class TestUtils:
    """Test cases for utility functions."""
    
    def test_load_data_success(self):
        """Test successful data loading."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,GROUP,Age,Gender,ALP,BMI,GNRI,eGFR,SII,FT4,PDW,Creatinine,FT3,RDW_SD\n")
            f.write("1000529,1,1,0,0,1,1,0,1,0,0,0,0,1\n")
            temp_file = f.name
        
        try:
            data = load_data(temp_file)
            assert isinstance(data, pd.DataFrame)
            assert len(data) == 1
            assert data.iloc[0]['id'] == 1000529
        finally:
            os.unlink(temp_file)
    
    def test_load_data_file_not_found(self):
        """Test loading non-existent file."""
        with pytest.raises(ValidationError, match="File not found"):
            load_data("non_existent_file.csv")
    
    def test_load_data_empty_file(self):
        """Test loading empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_file = f.name
        
        try:
            with pytest.raises(ValidationError, match="File is empty"):
                load_data(temp_file)
        finally:
            os.unlink(temp_file)
    
    def test_validate_data_success(self):
        """Test successful data validation."""
        data = pd.DataFrame({
            'id': [1000529, 1000530],
            'GROUP': [1, 0],
            'Age': [1, 0],
            'Gender': [0, 1],
            'ALP': [0, 1],
            'BMI': [1, 0],
            'GNRI': [1, 0],
            'eGFR': [0, 1],
            'SII': [1, 0],
            'FT4': [0, 1],
            'PDW': [0, 1],
            'Creatinine': [0, 1],
            'FT3': [0, 1],
            'RDW_SD': [1, 0]
        })
        
        # Should not raise any exception
        validate_data(data)
    
    def test_validate_data_missing_columns(self):
        """Test validation with missing columns."""
        data = pd.DataFrame({
            'id': [1000529],
            'GROUP': [1]
        })
        
        with pytest.raises(ValidationError, match="Missing required columns"):
            validate_data(data)
    
    def test_validate_data_null_values(self):
        """Test validation with null values in critical columns."""
        data = pd.DataFrame({
            'id': [1000529, None],
            'GROUP': [1, 0],
            'Age': [1, 0],
            'Gender': [0, 1],
            'ALP': [0, 1],
            'BMI': [1, 0],
            'GNRI': [1, 0],
            'eGFR': [0, 1],
            'SII': [1, 0],
            'FT4': [0, 1],
            'PDW': [0, 1],
            'Creatinine': [0, 1],
            'FT3': [0, 1],
            'RDW_SD': [1, 0]
        })
        
        with pytest.raises(ValidationError, match="contains null values"):
            validate_data(data)
    
    def test_validate_data_invalid_group_values(self):
        """Test validation with invalid GROUP values."""
        data = pd.DataFrame({
            'id': [1000529],
            'GROUP': [2],  # Invalid value
            'Age': [1],
            'Gender': [0],
            'ALP': [0],
            'BMI': [1],
            'GNRI': [1],
            'eGFR': [0],
            'SII': [1],
            'FT4': [0],
            'PDW': [0],
            'Creatinine': [0],
            'FT3': [0],
            'RDW_SD': [1]
        })
        
        with pytest.raises(ValidationError, match="GROUP column must contain only 0 or 1 values"):
            validate_data(data)
    
    def test_save_results_string(self):
        """Test saving string results."""
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = os.path.join(temp_dir, "test_result.txt")
            save_results("Test result", filepath)
            
            with open(filepath, 'r') as f:
                content = f.read()
            assert content == "Test result"
    
    def test_save_results_dict(self):
        """Test saving dictionary results."""
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = os.path.join(temp_dir, "test_result.json")
            results = {"prediction": "Test", "confidence": 0.95}
            save_results(results, filepath)
            
            with open(filepath, 'r') as f:
                content = f.read()
            assert "Test" in content
            assert "0.95" in content
    
    def test_format_patient_data_dict(self):
        """Test formatting patient data from dictionary."""
        patient_data = {'id': 1000529, 'GROUP': 1, 'Age': 1}
        result = format_patient_data(patient_data)
        expected = "id:1000529 GROUP:1 Age:1"
        assert result == expected
    
    def test_format_patient_data_series(self):
        """Test formatting patient data from pandas Series."""
        patient_data = pd.Series({'id': 1000529, 'GROUP': 1, 'Age': 1})
        result = format_patient_data(patient_data)
        expected = "id:1000529 GROUP:1 Age:1"
        assert result == expected
    
    def test_create_summary_report(self):
        """Test creating summary report."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some mock result files
            for i in range(3):
                with open(os.path.join(temp_dir, f"No.{i}_sample_id_100052{i}_output.txt"), 'w') as f:
                    f.write(f"Result {i}")
            
            # Create error log
            with open(os.path.join(temp_dir, "error_log.txt"), 'w') as f:
                f.write("Sample 0 error: Test error\n")
                f.write("Sample 1 error: Another error\n")
            
            create_summary_report(temp_dir)
            
            # Check if summary file was created
            summary_file = os.path.join(temp_dir, "summary_report.txt")
            assert os.path.exists(summary_file)
            
            with open(summary_file, 'r') as f:
                content = f.read()
                assert "Total samples processed: 3" in content
                assert "Errors encountered: 2" in content


if __name__ == "__main__":
    pytest.main([__file__])

"""
Tests for DOPPredictor class.
"""

import pytest
import pandas as pd
import os
from unittest.mock import Mock, patch
from dop1.predictor import DOPPredictor
from dop1.exceptions import DOPError, ValidationError, APIError


class TestDOPPredictor:
    """Test cases for DOPPredictor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.api_key = "test-api-key"
        self.predictor = DOPPredictor(api_key=self.api_key)
        
        # Sample patient data
        self.sample_patient = {
            'id': 1000529,
            'GROUP': 1,
            'Age': 1,
            'Gender': 0,
            'ALP': 0,
            'BMI': 1,
            'GNRI': 1,
            'eGFR': 0,
            'SII': 1,
            'FT4': 0,
            'PDW': 0,
            'Creatinine': 0,
            'FT3': 0,
            'RDW_SD': 1
        }
        
        # Sample DataFrame
        self.sample_data = pd.DataFrame([self.sample_patient])
    
    def test_init_with_api_key(self):
        """Test initialization with API key."""
        predictor = DOPPredictor(api_key="test-key")
        assert predictor.api_key == "test-key"
        assert predictor.base_url == "https://api.ocoolai.com/v1"
        assert predictor.model == "gpt-5"
    
    def test_init_without_api_key(self):
        """Test initialization without API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(DOPError, match="API key not provided"):
                DOPPredictor()
    
    def test_init_with_env_api_key(self):
        """Test initialization with API key from environment."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'env-key'}):
            predictor = DOPPredictor()
            assert predictor.api_key == 'env-key'
    
    def test_custom_configuration(self):
        """Test initialization with custom configuration."""
        predictor = DOPPredictor(
            api_key="test-key",
            base_url="https://custom.api.com/v1",
            model="gpt-4"
        )
        assert predictor.base_url == "https://custom.api.com/v1"
        assert predictor.model == "gpt-4"
    
    @patch('dop1.predictor.OpenAI')
    def test_predict_single_success(self, mock_openai):
        """Test successful single prediction."""
        # Mock API response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Prediction result"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        predictor = DOPPredictor(api_key="test-key")
        result = predictor.predict_single(self.sample_patient)
        
        assert result == "Prediction result"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('dop1.predictor.OpenAI')
    def test_predict_single_api_error(self, mock_openai):
        """Test single prediction with API error."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        predictor = DOPPredictor(api_key="test-key")
        
        with pytest.raises(APIError, match="Failed to make prediction"):
            predictor.predict_single(self.sample_patient)
    
    def test_predict_single_with_series(self):
        """Test single prediction with pandas Series."""
        with patch.object(self.predictor, 'client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Prediction result"
            mock_client.chat.completions.create.return_value = mock_response
            
            patient_series = pd.Series(self.sample_patient)
            result = self.predictor.predict_single(patient_series)
            
            assert result == "Prediction result"
    
    @patch('dop1.predictor.pd.read_csv')
    @patch('dop1.predictor.validate_data')
    @patch('dop1.predictor.os.makedirs')
    @patch('dop1.predictor.os.path.exists')
    def test_process_batch_success(self, mock_exists, mock_makedirs, mock_validate, mock_read_csv):
        """Test successful batch processing."""
        # Setup mocks
        mock_read_csv.return_value = self.sample_data
        mock_validate.return_value = None
        mock_exists.return_value = False
        
        with patch.object(self.predictor, 'predict_single') as mock_predict:
            mock_predict.return_value = "Prediction result"
            
            with patch('builtins.open', mock_open()) as mock_file:
                self.predictor.process_batch("test.csv", "output_dir")
                
                # Verify calls
                mock_read_csv.assert_called_once_with("test.csv")
                mock_validate.assert_called_once_with(self.sample_data)
                mock_makedirs.assert_called_once_with("output_dir", exist_ok=True)
                mock_predict.assert_called_once()
                mock_file.assert_called()
    
    @patch('dop1.predictor.pd.read_csv')
    def test_process_batch_validation_error(self, mock_read_csv):
        """Test batch processing with validation error."""
        mock_read_csv.return_value = self.sample_data
        
        with patch('dop1.predictor.validate_data') as mock_validate:
            mock_validate.side_effect = ValidationError("Invalid data")
            
            with pytest.raises(DOPError, match="Batch processing failed"):
                self.predictor.process_batch("test.csv")
    
    def test_get_model_info(self):
        """Test getting model information."""
        info = self.predictor.get_model_info()
        
        assert info["model"] == "gpt-5"
        assert info["base_url"] == "https://api.ocoolai.com/v1"
        assert info["api_key_set"] is True


def mock_open():
    """Mock open function for testing."""
    from unittest.mock import mock_open as original_mock_open
    return original_mock_open()


if __name__ == "__main__":
    pytest.main([__file__])

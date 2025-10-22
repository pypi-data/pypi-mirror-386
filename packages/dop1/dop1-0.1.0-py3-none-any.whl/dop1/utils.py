"""
Utility functions for DOP1 package.
"""

import pandas as pd
import os
from typing import Union, Dict, Any
from .exceptions import ValidationError


def load_data(filepath: str) -> pd.DataFrame:
    """
    Load data from CSV file.
    
    Args:
        filepath: Path to CSV file
        
    Returns:
        Loaded DataFrame
        
    Raises:
        ValidationError: If file cannot be loaded or is invalid
    """
    try:
        if not os.path.exists(filepath):
            raise ValidationError(f"File not found: {filepath}")
        
        data = pd.read_csv(filepath)
        
        if data.empty:
            raise ValidationError("File is empty")
        
        return data
        
    except pd.errors.EmptyDataError:
        raise ValidationError("File is empty")
    except pd.errors.ParserError as e:
        raise ValidationError(f"Error parsing CSV file: {str(e)}")
    except Exception as e:
        raise ValidationError(f"Error loading file: {str(e)}")


def validate_data(data: pd.DataFrame) -> None:
    """
    Validate patient data format.
    
    Args:
        data: DataFrame to validate
        
    Raises:
        ValidationError: If data format is invalid
    """
    required_columns = [
        'id', 'GROUP', 'Age', 'Gender', 'ALP', 'BMI', 'GNRI', 
        'eGFR', 'SII', 'FT4', 'PDW', 'Creatinine', 'FT3', 'RDW_SD'
    ]
    
    # Check required columns
    missing_columns = set(required_columns) - set(data.columns)
    if missing_columns:
        raise ValidationError(f"Missing required columns: {missing_columns}")
    
    # Check for empty values in critical columns
    critical_columns = ['id', 'GROUP']
    for col in critical_columns:
        if data[col].isnull().any():
            raise ValidationError(f"Column '{col}' contains null values")
    
    # Check GROUP values are 0 or 1
    if not data['GROUP'].isin([0, 1]).all():
        raise ValidationError("GROUP column must contain only 0 or 1 values")
    
    # Check data types
    numeric_columns = ['Age', 'Gender', 'ALP', 'BMI', 'GNRI', 'eGFR', 'SII', 'FT4', 'PDW', 'Creatinine', 'FT3', 'RDW_SD']
    for col in numeric_columns:
        if col in data.columns:
            if not pd.api.types.is_numeric_dtype(data[col]):
                try:
                    data[col] = pd.to_numeric(data[col], errors='coerce')
                except:
                    raise ValidationError(f"Column '{col}' must be numeric")


def save_results(results: Union[str, Dict[str, Any]], filepath: str) -> None:
    """
    Save results to file.
    
    Args:
        results: Results to save (string or dictionary)
        filepath: Path to save file
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        if isinstance(results, dict):
            # Save as JSON
            import json
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        else:
            # Save as text
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(results))
                
    except Exception as e:
        raise ValidationError(f"Error saving results: {str(e)}")


def format_patient_data(patient_data: Union[Dict, pd.Series]) -> str:
    """
    Format patient data for API input.
    
    Args:
        patient_data: Patient data as dictionary or pandas Series
        
    Returns:
        Formatted string for API input
    """
    if isinstance(patient_data, dict):
        return ' '.join([f"{k}:{v}" for k, v in patient_data.items()])
    else:
        return ' '.join([f"{col}:{patient_data[col]}" for col in patient_data.index])


def create_summary_report(results_dir: str, output_file: str = "summary_report.txt") -> None:
    """
    Create a summary report of processing results.
    
    Args:
        results_dir: Directory containing result files
        output_file: Output file for summary report
    """
    try:
        result_files = [f for f in os.listdir(results_dir) if f.endswith('.txt') and f.startswith('No.')]
        error_files = [f for f in os.listdir(results_dir) if f == 'error_log.txt']
        
        summary = {
            "total_processed": len(result_files),
            "successful_predictions": len(result_files),
            "errors": 0
        }
        
        if error_files:
            error_file_path = os.path.join(results_dir, 'error_log.txt')
            if os.path.exists(error_file_path):
                with open(error_file_path, 'r', encoding='utf-8') as f:
                    error_count = len(f.readlines())
                summary["errors"] = error_count
        
        # Save summary
        summary_path = os.path.join(results_dir, output_file)
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("DOP1 Processing Summary Report\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Total samples processed: {summary['total_processed']}\n")
            f.write(f"Successful predictions: {summary['successful_predictions']}\n")
            f.write(f"Errors encountered: {summary['errors']}\n")
            f.write(f"Success rate: {summary['successful_predictions']/max(summary['total_processed'], 1)*100:.1f}%\n")
        
    except Exception as e:
        raise ValidationError(f"Error creating summary report: {str(e)}")

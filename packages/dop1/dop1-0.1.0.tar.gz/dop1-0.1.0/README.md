# DOP1 - Diabetes Osteoporosis Prediction Package

A Python package for AI-powered analysis of diabetes complicated with osteoporosis using machine learning and OpenAI's GPT models.

## Features

- **AI-Powered Analysis**: Uses OpenAI's GPT models for intelligent prediction of osteoporosis risk in diabetic patients
- **Comprehensive Data Processing**: Handles laboratory and clinical feature data
- **Batch Processing**: Efficiently processes large datasets with progress tracking
- **Error Handling**: Robust error handling with detailed logging
- **Configurable API**: Flexible API endpoint and key configuration
- **Command Line Interface**: Easy-to-use CLI for batch processing
- **Comprehensive Testing**: Full test suite with coverage reporting

## Installation

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/dop-research/dop1.git
cd dop1

# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e .[dev]

# Run tests
make test
```

### Using pip (when published)

```bash
pip install dop1
```

## Quick Start

### Python API

```python
from dop1 import DOPPredictor

# Initialize the predictor
predictor = DOPPredictor(api_key="your-api-key")

# Analyze a single patient
patient_data = {
    'id': 1000529,
    'GROUP': 1,  # This will be predicted
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

result = predictor.predict_single(patient_data)
print(f"Prediction: {result}")

# Process a batch of patients from CSV
predictor.process_batch("patients.csv", output_dir="results")
```

### Command Line Interface

```bash
# Set API key
export OPENAI_API_KEY="your-api-key-here"

# Process a CSV file
dop1 predict data.csv --output results/

# Use custom model
dop1 predict data.csv --model gpt-4 --output results/

# Show help
dop1 --help
```

## Data Format

The package expects CSV files with the following columns:

| Column | Description | Values |
|--------|-------------|---------|
| `id` | Patient identifier | Any unique identifier |
| `GROUP` | Target variable | 0 = low bone mass/normal, 1 = osteoporosis/severe osteoporosis |
| `Age` | Age group | 0 or 1 |
| `Gender` | Gender | 0 = male, 1 = female |
| `ALP` | Alkaline phosphatase | 0 or 1 |
| `BMI` | Body Mass Index | 0 or 1 |
| `GNRI` | Geriatric Nutritional Risk Index | 0 or 1 |
| `eGFR` | Estimated Glomerular Filtration Rate | 0 or 1 |
| `SII` | Systemic Immune-Inflammation Index | 0 or 1 |
| `FT4` | Free Thyroxine | 0 or 1 |
| `PDW` | Platelet Distribution Width | 0 or 1 |
| `Creatinine` | Serum Creatinine | 0 or 1 |
| `FT3` | Free Triiodothyronine | 0 or 1 |
| `RDW_SD` | Red Cell Distribution Width | 0 or 1 |

## Configuration

### Environment Variables

```bash
export OPENAI_API_KEY="your-api-key-here"
export OPENAI_BASE_URL="https://api.ocoolai.com/v1"  # Optional
export DOP1_MODEL="gpt-5"  # Optional
```

### Programmatic Configuration

```python
predictor = DOPPredictor(
    api_key="your-api-key",
    base_url="https://api.ocoolai.com/v1",
    model="gpt-5"
)
```

## Examples

### Basic Usage

See `examples/basic_usage.py` for a complete example.

### Sample Data

Use `examples/sample_data.csv` as a template for your data format.

## Development

### Running Tests

```bash
# Run all tests
make test

# Run tests without coverage
make test-fast

# Run specific test file
pytest tests/test_predictor.py -v
```

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Run all checks
make check
```

### Building

```bash
# Build package
make build

# Clean build artifacts
make clean
```

## API Reference

### DOPPredictor Class

#### `__init__(api_key, base_url, model)`
Initialize the predictor with API configuration.

#### `predict_single(patient_data)`
Predict osteoporosis risk for a single patient.

#### `process_batch(filepath, output_dir, skip_existing)`
Process a batch of patients from CSV file.

#### `get_model_info()`
Get information about the current model configuration.

### Utility Functions

#### `load_data(filepath)`
Load patient data from CSV file.

#### `validate_data(data)`
Validate patient data format.

#### `save_results(results, filepath)`
Save results to file.

## Error Handling

The package provides custom exceptions:

- `DOPError`: Base exception class
- `ValidationError`: Data validation errors
- `APIError`: API call failures
- `ConfigurationError`: Configuration issues
- `FileError`: File operation errors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the examples

## Changelog

### v0.1.0
- Initial release
- Basic prediction functionality
- Batch processing
- CLI interface
- Comprehensive testing

# TLPyTools

TransLink's Python Tools - A comprehensive toolkit for transportation modeling and forecasting developed by the TransLink Forecasting Team.

## Overview

TLPyTools provides a suite of utilities and tools designed to support various aspects of transportation modeling workflows, from data management and processing to cloud synchronization and model orchestration. Built specifically for the TransLink Forecasting Team's modeling needs.

## Installation

> **Note**: TLPyTools requires Python 3.10 or higher. ActivitySim and PopulationSim are available for development installations using uv sync.

### Using uv (Recommended)

TLPyTools uses [uv](https://docs.astral.sh/uv/) for fast and reliable dependency management.

#### Installing uv

**Option 1: Direct download (Recommended for Windows)**
1. Download uv Windows executable - [uv-x86_64-pc-windows-msvc.zip](https://github.com/astral-sh/uv/releases/download/0.8.13/uv-x86_64-pc-windows-msvc.zip)
2. Move all files within the zip file downloaded (including `uv.exe`, `uvw.exe`, `uvx.exe`) into a new folder `C:\ProgramData\uv`
3. Add `C:\ProgramData\uv` to the system environment variable PATH.
4. Open a new command prompt and test the command `uv --help`

**Option 2: Install script (Recommended for Linux/macOS)**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
After installation, restart your terminal or run:
```bash
source ~/.bashrc  # or ~/.zshrc depending on your shell
```

#### Installing TLPyTools with uv

```bash
# Clone and install the package
git clone https://github.com/TransLinkForecasting/tlpytools.git
cd tlpytools

# Install core package only
uv sync

# Install with ORCA orchestrator support
uv sync --extra orca

# Install with full development environment (includes GIS tools, visualization, etc.)
uv sync --extra dev

# Install multiple extras (common combinations)
uv sync --extra dev --extra orca

# For development with ActivitySim and PopulationSim (git dependencies available via uv)
# Note: ActivitySim/PopulationSim are only available for development, not through PyPI
uv sync --extra dev --extra orca --group activitysim
```

### Using pip (Alternative)

You can still use pip for installation, but ActivitySim and PopulationSim are not available as extras due to PyPI restrictions on git dependencies:

```bash
# Core package only
pip install tlpytools

# With ORCA orchestrator support  
pip install tlpytools[orca]

# With full development environment
pip install tlpytools[dev]

# Multiple extras
pip install tlpytools[dev,orca]

# Development installation (without ActivitySim - use uv for that)
git clone https://github.com/TransLinkForecasting/tlpytools.git
cd tlpytools
pip install -e .[dev,orca]
```

## Core Modules

### Data Management (`tlpytools.data`)

Utilities for data processing and manipulation:

- **DataFrame Operations**: Enhanced pandas functionality for transportation data
- **Spatial Data Support**: Optional GIS operations (requires `geopandas`)
- **Data Validation**: Tools for checking data integrity and consistency

```python
from tlpytools.data import read_spatial_data, validate_dataframe

# Load spatial data (if geopandas available)
gdf = read_spatial_data("zones.shp")

# Validate data structure
is_valid = validate_dataframe(df, required_columns=['zone_id', 'households'])
```

### Data Storage (`tlpytools.data_store`)

Comprehensive data storage and retrieval functionality:

- **Multiple Backends**: Support for various storage formats
- **Metadata Management**: Automatic tracking of data lineage
- **Version Control**: Built-in data versioning capabilities

```python
from tlpytools.data_store import DataStore

store = DataStore("my_project")
store.save_data(df, "travel_times", metadata={"source": "model_run_1"})
retrieved_df = store.load_data("travel_times")
```

### SQL Server Integration (`tlpytools.sql_server`)

Tools for working with SQL Server databases:

- **Connection Management**: Simplified database connections
- **Query Utilities**: Helper functions for common operations
- **Bulk Operations**: Efficient data loading and extraction

```python
from tlpytools.sql_server import SQLServerConnection

with SQLServerConnection("server_name", "database_name") as conn:
    df = conn.query("SELECT * FROM travel_data WHERE year = 2023")
    conn.bulk_insert(new_data, "staging_table")
```

### Cloud Storage (`tlpytools.adls_server`)

Azure Data Lake Storage integration:

- **File Synchronization**: Upload/download with conflict resolution
- **Batch Operations**: Efficient handling of large datasets
- **Authentication**: Secure connection management

```python
from tlpytools.adls_server import adls_util

# Upload files to cloud storage
adls_util.upload_files(local_path="data/", remote_path="project/data/")

# Download with pattern matching
adls_util.download_files(remote_pattern="outputs/*.csv", local_path="results/")
```

### Configuration Management (`tlpytools.config`)

Centralized configuration handling:

- **YAML Support**: Human-readable configuration files
- **Environment Variables**: Runtime configuration overrides
- **Validation**: Schema validation for configuration files

```python
from tlpytools.config import load_config, validate_config

config = load_config("model_config.yaml")
if validate_config(config, schema="model_schema.json"):
    print("Configuration is valid")
```

### Logging (`tlpytools.log`)

Enhanced logging capabilities:

- **Structured Logging**: Consistent log formatting across projects
- **Multiple Outputs**: Console and file logging with different levels
- **Performance Tracking**: Built-in timing and profiling support

```python
from tlpytools.log import setup_logger

logger = setup_logger("my_model", log_file="model.log")
logger.info("Starting model run")
logger.performance("Model completed", execution_time=120.5)
```

## ORCA Model Orchestration

TLPyTools includes the ORCA (Orchestrated Regional Comprehensive Analysis) transportation model orchestrator as an optional component.

### Quick Start with ORCA

```bash
# Install with ORCA support
pip install tlpytools[orca]

# Initialize a new model databank
python -m tlpytools.orca --action initialize_databank --databank db_example

# Run the complete model workflow
python -m tlpytools.orca --action run_models --databank db_example
```

### ORCA Features

- **Multi-Model Coordination**: Orchestrates ActivitySim, commercial vehicle models, and traffic assignment
- **Cloud Integration**: Automatic synchronization with Azure Data Lake Storage
- **State Management**: Resume interrupted model runs from any point
- **Configurable Workflows**: YAML-based configuration for complex modeling pipelines

For detailed ORCA documentation, see [README_ORCA.md](README_ORCA.md).

## Key Features

### 🔧 **Modular Design**
- Independent modules with optional dependencies
- Use only what you need without heavy dependency chains
- Clear separation of concerns for easier maintenance

### 🚀 **Performance Optimized**
- Efficient data processing with pandas and NumPy
- Chunked operations for large datasets
- Optional performance monitoring and profiling

### ☁️ **Cloud Ready**
- Native Azure integration for data storage and processing
- Secure authentication and connection management
- Efficient file synchronization with conflict resolution

### 🔄 **Production Ready**
- Comprehensive error handling and logging
- State management for long-running processes
- Configurable retry logic and timeout handling

### 🧪 **Testing Support**
- Built-in validation utilities
- Mock objects for testing cloud operations
- Comprehensive test suite included

## Usage Examples

### Basic Data Pipeline

```python
from tlpytools.data import process_survey_data
from tlpytools.data_store import DataStore
from tlpytools.log import setup_logger

# Setup logging
logger = setup_logger("data_pipeline")

# Process survey data
processed_data = process_survey_data("survey_2023.csv")
logger.info(f"Processed {len(processed_data)} survey records")

# Store results
store = DataStore("survey_analysis")
store.save_data(processed_data, "processed_survey_2023")
```

### Cloud Synchronization Workflow

```python
from tlpytools.adls_server import adls_util
from tlpytools.config import load_config

# Load cloud configuration
config = load_config("cloud_config.yaml")

# Sync local results to cloud
adls_util.upload_directory(
    local_path="model_outputs/",
    remote_path=f"projects/{config['project_name']}/outputs/",
    conflict_resolution="timestamp"
)
```

### SQL Server Integration

```python
from tlpytools.sql_server import SQLServerConnection
from tlpytools.data import validate_dataframe

# Connect and validate data
with SQLServerConnection("prod_server", "transport_db") as conn:
    # Load reference data
    zones = conn.query("SELECT * FROM zones WHERE active = 1")
    
    # Validate structure
    if validate_dataframe(zones, required_columns=['zone_id', 'area_type']):
        print(f"Loaded {len(zones)} valid zones")
```

## Dependencies

### Core Dependencies
- `pandas>=1.1` - Data manipulation and analysis
- `numpy>=1.18` - Numerical computing
- `sqlalchemy>=1.4` - SQL toolkit and ORM
- `pyodbc>=4.0` - SQL Server connectivity
- `pyyaml>=5.4` - YAML configuration files
- `azure-core>=1.34` - Azure SDK core functionality
- `azure-identity>=1.23` - Azure authentication
- `azure-storage-blob>=12.24` - Azure Blob Storage
- `azure-storage-file-datalake>=12.18` - Azure Data Lake Storage

### Optional Dependencies

**ORCA Module (`uv sync --extra orca` or `pip install tlpytools[orca]`):**
- `psutil>=5.8.0` - System monitoring and performance tracking
- `unittest-xml-reporting>=3.2.0` - Enhanced test reporting

**ActivitySim Module (Development only - via `uv sync --group activitysim`):**
- `activitysim` - TransLink's customized ActivitySim (from GitHub, not available on PyPI)
- `populationsim` - Synthetic population generation tool (from GitHub, not available on PyPI)

> **Note**: ActivitySim and PopulationSim are only available through `uv sync --group activitysim` for development installations due to PyPI restrictions on git dependencies. They are not available as pip extras.

**Development Environment (`uv sync --extra dev` or `pip install tlpytools[dev]`):**

*Geospatial Analysis Tools:*
- `geopandas>=0.13.0` - Geospatial data manipulation
- `GDAL>=3.6.0` - Geospatial data abstraction library
- `Shapely>=2.0.0` - Geometric operations
- `Fiona>=1.9.0` - Vector data I/O
- `pyproj>=3.4.0` - Cartographic projections
- `Rtree>=1.0.0` - Spatial indexing
- `Cartopy>=0.21.0` - Cartographic projections for matplotlib
- `contextily>=1.5.0` - Web map tiles for matplotlib
- `folium>=0.14.0` - Interactive maps

*Visualization and Dashboard Tools:*
- `plotly>=5.17.0` - Interactive plotting
- `dash>=2.14.0` - Web application framework
- `dash-extensions>=1.0.0` - Additional Dash components
- `dash-leaflet>=0.1.0` - Leaflet maps for Dash
- `panel>=1.3.0` - High-level dashboard framework

*Development and Code Quality:*
- `black>=23.0.0` - Code formatting
- `ruff>=0.1.0` - Fast Python linter
- `pytest>=7.4.0` - Testing framework
- `pytest-cov>=4.1.0` - Coverage reporting
- `mypy>=1.5.0` - Static type checking
- `pre-commit>=3.4.0` - Git pre-commit hooks

*Other Utilities:*
- `polyline>=2.0.0` - Polyline encoding/decoding
- `jupyter>=1.0.0` - Jupyter ecosystem
- `ipykernel>=6.25.0` - IPython kernel for Jupyter

### Manual GDAL Installation

GDAL is not included in the default dependencies due to compilation complexity, but can be added manually for advanced geospatial operations:

```bash
# Add GDAL to your project
uv add "GDAL>=3.6.0"
```

**Prerequisites for successful GDAL compilation:**

**Windows:**
- Install Visual Studio Build Tools or Visual Studio Community
- Ensure C++ build tools are included
- Add Visual Studio tools to your PATH environment variable

**Linux (Ubuntu/Debian):**
```bash
# Install build dependencies
sudo apt-get update
sudo apt-get install build-essential libgdal-dev gdal-bin
```

**Linux (RHEL/CentOS/Fedora):**
```bash
# Install build dependencies
sudo dnf install gcc-c++ gdal-devel gdal
# or for older systems: sudo yum install gcc-c++ gdal-devel gdal
```

**Note:** GDAL compilation can be time-consuming and may fail on some systems due to missing system libraries. If you encounter issues, consider using system package managers or Docker environments for more reliable installations.

## Configuration

TLPyTools uses YAML configuration files for most components. Example configuration:

```yaml
# tlpytools_config.yaml
data_store:
  backend: "local"
  base_path: "data/"
  versioning: true

cloud:
  provider: "azure"
  storage_account: "your_account"
  container: "your_container"

logging:
  level: "INFO"
  file_output: true
  console_output: true
```

Load configuration in your code:

```python
from tlpytools.config import load_config

config = load_config("tlpytools_config.yaml")
```

## Error Handling

TLPyTools provides graceful error handling for optional dependencies:

```python
# This works even if geopandas is not installed
from tlpytools.data import read_spatial_data

try:
    gdf = read_spatial_data("zones.shp")
except ImportError as e:
    print(f"Spatial operations not available: {e}")
    # Fallback to regular CSV reading
    df = pd.read_csv("zones.csv")
```

## Testing

Run the test suite:

```bash
# Using uv (recommended)
uv run pytest

# Run all tests with coverage
uv run pytest --cov=tests

# Run specific module tests
uv run pytest tests/test_data.py

# Run ORCA tests specifically
uv run pytest src/tlpytools/orca/tests/

# Using pip (alternative)
python -m pytest

# Run with coverage
python -m pytest --cov=tests
```

## Contributing

We welcome contributions to TLPyTools! Please follow these guidelines:

1. **Fork the repository** and create a feature branch
2. **Install development dependencies**: `pip install -e .[dev]`
3. **Write tests** for new functionality
4. **Follow code style** guidelines (run `black` and `ruff`)
5. **Update documentation** as needed
6. **Submit a pull request** with a clear description

### Development Setup

#### Using uv (Recommended)

```bash
# Install uv if not already installed
pip install uv

# Clone the repository
git clone https://github.com/TransLinkForecasting/tlpytools.git
cd tlpytools

# Quick setup using Makefile
make dev-setup

# Or manual setup:
# Install full development environment (includes GIS tools, visualization, etc.)
uv sync --extra dev --extra orca

# Note: ActivitySim and PopulationSim can be added with --group activitysim
# when working in a development setup (they're not PyPI extras but are uv dependency groups)

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run tests
uv run pytest

# Run code formatting
uv run black src/
uv run ruff check src/

# Run type checking
uv run mypy src/
```

#### Common Development Tasks

```bash
# Using the provided Makefile (recommended)
make help          # Show all available commands
make install-all   # Install all dependencies
make test          # Run tests
make test-cov      # Run tests with coverage
make lint          # Check code style
make format        # Format code
make type-check    # Run type checking
make check-all     # Run all quality checks
```

#### Using pip (Alternative)

```bash
# Clone the repository
git clone https://github.com/TransLinkForecasting/tlpytools.git
cd tlpytools

# Create development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode (without ActivitySim - use uv for ActivitySim)
pip install -e .[orca,dev]

# Run tests
python -m pytest
```

## Support

- **Documentation**: Comprehensive module documentation available
- **Examples**: See `examples/` directory for usage examples
- **Issues**: Report bugs and feature requests on GitHub Issues
- **Email**: Contact the TransLink Forecasting Team at forecasting@translink.ca

## License

This project is proprietary software developed by TransLink. All rights reserved.

## Version History

- **0.1.11**:
  - bump versions - 
    - all dependency versions
    - activitysim version to https://github.com/TransLinkForecasting/activitysim/commit/5e781a705800fecc627a4a580781d596cd1a54e3
    - populationsim version to https://github.com/TransLinkForecasting/populationsim/commit/2d274d72985024096cb4637573261718c6684a13
  - fix `--project` argument inconsistency across adls util and batch api caller
  - test different Azure Auth methods, added notes to recommend AZ CLI in .env.examples
- **0.1.10**:
  - Add support for uploading of inputs folder to ADLS, this will allow orca commands to access shared inputs data
- **0.1.9**:
  - Add support for package-level .env file support to simplify set up and provide more flexibility
- **0.1.8**:
  - Set Python version to 3.10 to align with activitysim
  - Add Azure Batch API caller part of orca
  - Add unified logger for better maintainability
  - Improve Azure credential handling to allow for differences between local testing and cloud production
  - Fix minor bugs with workflows and release pipelines
- **0.1.7**: 
  - Migration to uv for dependency management
  - Fixed PyPI deployment: Moved ActivitySim and PopulationSim to uv dependency groups (no longer PyPI extras)
  - ActivitySim now available via `uv sync --group activitysim` for development only
  - Comprehensive dev dependencies for geospatial analysis tools (GDAL, Shapely, GeoPandas, etc.)
  - Added visualization tools (Plotly, Dash, Panel, Folium)
  - Enhanced development tooling (Black, Ruff, MyPy, Pre-commit)
  - ORCA namespace reorganization, improved modularity
- **0.1.6.1**: Add data store support for RESUME_AFTER functionality, add ADLS and Azure SQL Server support
- **0.1.6.0**: Enhanced cloud synchronization, performance monitoring
- **0.1.5.x**: Core module stabilization, testing improvements
- **0.1.4.x**: Initial SQL Server integration, configuration management
- **0.1.3.x**: Data storage utilities, logging enhancements
- **0.1.2.x**: Cloud storage integration, ADLS support
- **0.1.1.x**: Core data processing utilities
- **0.1.0.x**: Initial release with basic functionality

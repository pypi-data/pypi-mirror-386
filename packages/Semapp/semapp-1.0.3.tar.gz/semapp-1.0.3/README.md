# SEMapp - SEM Data Visualization Application

A PyQt5-based desktop application for visualizing and analyzing Scanning Electron Microscope (SEM) data. SEMapp supports both standard and COMPLUS4T KLARF file formats, providing an intuitive interface for defect mapping and image analysis.

## Features

### Core Functionality
- **KLARF File Support**: Parse and extract defect data from `.001` (KLARF) files
- **Dual Mode Operation**:
  - **Standard Mode**: Process SEM data from structured subdirectories
  - **COMPLUS4T Mode**: Handle multi-wafer KLARF files with automatic wafer detection
- **Interactive Wafer Mapping**: Visual representation of defect positions on wafer surface
- **Image Visualization**: Display TIFF images corresponding to defect locations
- **Dynamic Defect Filtering**: Real-time defect filtering based on size threshold (COMPLUS4T mode)

### Data Processing
- **Automatic File Organization**: Organize TIFF files into wafer-specific subfolders
- **Coordinate Extraction**: Extract and convert defect coordinates from KLARF format
- **CSV Export**: Save defect mapping data for external analysis
- **Batch Processing**: Process multiple wafers in a single session

### User Interface
- **Wafer Selection**: Grid-based wafer slot selection (1-26)
- **Image Type Selection**: Choose from different image scales and types
- **Defect Size Slider**: Dynamic threshold control for defect visualization (COMPLUS4T mode)
- **Interactive Plot**: Click on defect positions to view corresponding images
- **Settings Configuration**: Customize image types and processing parameters

## Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Install from PyPI
```bash
pip install semapp
```

### Install from Source
```bash
git clone https://github.com/yourusername/semapp.git
cd semapp
pip install -e .
```

### Dependencies
The following packages will be installed automatically:
- PyQt5 >= 5.15.0
- matplotlib >= 3.3.0
- pandas >= 1.1.0
- Pillow >= 8.0.0
- numpy >= 1.19.0

## Quick Start

### Launching the Application
```bash
# From command line after installation
semapp

# Or run directly from source
python -m semapp.main
```

### Basic Workflow

1. **Select a Directory**
   - Click "Select Folder" to choose your data directory
   - Application automatically detects standard or COMPLUS4T mode

2. **Choose a Wafer**
   - Select a wafer slot from the grid (1-26)
   - Available wafers are highlighted

3. **Open TIFF Data**
   - Click "Open TIFF" to load defect data and images
   - Wafer mapping is displayed automatically

4. **Analyze Defects**
   - Click on defect points in the map to view corresponding images
   - Use the defect size slider (COMPLUS4T mode) to filter by threshold
   - Red points indicate defects above threshold, blue points below

## File Structure

### Standard Mode
```
project_directory/
├── 1/                          # Wafer slot 1
│   ├── data.tif               # TIFF image file
│   ├── recipe_file.001        # KLARF defect file
│   └── mapping.csv            # Generated coordinate mapping
├── 2/                          # Wafer slot 2
│   ├── data.tif
│   ├── recipe_file.001
│   └── mapping.csv
└── ...
```

### COMPLUS4T Mode
```
project_directory/
├── data.tiff                   # Single TIFF file with all defects
├── recipe_file.001             # KLARF file containing multiple wafer IDs
├── 16/                         # Subfolder created for wafer ID 16
│   └── mapping.csv             # Wafer-specific mapping
├── 21/                         # Subfolder created for wafer ID 21
│   └── mapping.csv
└── ...
```

## KLARF File Format

SEMapp parses KLARF (`.001`) files to extract:
- **Wafer IDs**: `WaferID "@16";` (COMPLUS4T mode)
- **Sample Size**: Total number of defects
- **Die Pitch**: X and Y spacing between dies
- **Die Origin**: Reference origin coordinates
- **Sample Center**: Wafer center location
- **Defect List**: Individual defect data including:
  - Position (X, Y coordinates)
  - Size (nm)
  - Defect ID

## Settings Configuration

### Image Type Settings
Configure available image types and scales in the settings dialog:
- **Scale**: Image scale factor (e.g., 1µm, 5µm, 10µm)
- **Image Type**: Description of image type (e.g., Optic, SEM)

Settings are saved to `settings_data.json` for persistence across sessions.

### Data Processing Options
- **Split & Rename**: Organize files into wafer subfolders
- **Rename Files**: Batch rename files based on coordinates
- **Clean Folders**: Remove temporary/unwanted files

## Troubleshooting

### Common Issues

**TIFF file not found**
- Ensure TIFF files are named `data.tif` (standard mode)
- Check that TIFF files have `.tiff` or `.tif` extension
- Verify folder structure matches expected format

**Wafer IDs not detected**
- Confirm KLARF file contains "COMPLUS4T" keyword
- Check WaferID format: `WaferID "@<number>";`
- Ensure wafer IDs are between 1 and 26

**Coordinates not displaying**
- Verify KLARF file contains DefectList section
- Check that DiePitch, DieOrigin, and SampleCenterLocation are defined
- Ensure defect data format matches expected structure

**Images not loading**
- Confirm TIFF file is valid and not corrupted
- Check file permissions for read access
- Verify sufficient memory for large TIFF files

## Development

### Project Structure
```
semapp/
├── __init__.py                 # Package initialization
├── main.py                     # Application entry point
├── Layout/                     # UI components
│   ├── create_button.py        # Button controls and wafer selection
│   ├── main_window_att.py      # Main window layout
│   ├── settings.py             # Settings dialog
│   └── styles.py               # UI style definitions
├── Plot/                       # Plotting and visualization
│   ├── frame_attributes.py     # Plot frame and mapping
│   ├── styles.py               # Plot styles
│   └── utils.py                # Plotting utilities
└── Processing/                 # Data processing
    └── processing.py           # File processing and KLARF parsing
```

### Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with PyQt5 for the graphical interface
- Matplotlib for data visualization
- Pandas for data manipulation
- Pillow for image processing

## Contact

For questions, issues, or suggestions, please open an issue on GitHub.

---

**Version**: 1.0.2  
**Status**: Production Ready


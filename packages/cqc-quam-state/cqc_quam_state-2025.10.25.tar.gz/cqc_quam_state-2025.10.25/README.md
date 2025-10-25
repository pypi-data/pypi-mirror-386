# CQC QUAM State

A command-line tool for managing CQC QuAM (Quantum Abstract Machine) state configuration.

## Overview

This package provides access to calibrated quantum device configurations and state files. It includes:

- Pre-calibrated QuAM state files (JSON format)
- CLI tools for managing and loading state configurations
- Environment variable management for QuAM state paths

To quickly set the `QUAM_STATE_PATH` environment variable to the current calibrated state (after installing and activating the environment):

```bash
source load-cqc-quam
```

**Note**: The package version follows the format `YYYY.MM.DD[.X]` where `YYYY.MM.DD` indicates the date of the last calibration, and the optional `.X` is a sub-version for multiple releases on the same day.

## Installation

Install the package using `uv` (recommended) or `pip`. Make sure to use the latest version to get the most recent calibration data:

### Using uv (recommended)

```bash
uv venv
source .venv/bin/activate
uv pip install cqc-quam-state==2025.6.4.1
```

### Using pip

```bash
pip install cqc-quam-state==2025.6.4.1
```

### Installing the latest version

To install the most recent calibration data, check for the latest version:

```bash
# Find the latest version
pip index versions cqc-quam-state

# Install the latest version (e.g., if there are multiple releases today)
pip install cqc-quam-state==2025.6.4.3
```

## Usage

### Quick Start

The simplest way to use this package is to source the provided script, which sets the `QUAM_STATE_PATH` environment variable:

```bash
source load-cqc-quam
```

This will set `QUAM_STATE_PATH` to point to the current calibrated state files included in the package.

### CLI Commands

The package also provides a `cqc-quam-state` CLI tool for more advanced usage:

#### Get Help

```bash
cqc-quam-state --help
```

#### Available Commands

- **`info`**: Display information about the current state
- **`load`**: Output the export command for setting `QUAM_STATE_PATH` (used by the `load-cqc-quam` script)
- **`set`**: Set configuration values (placeholder for future functionality)

#### Examples

Display current state information:

```bash
cqc-quam-state info
```

Get the export command for the QuAM state path:

```bash
cqc-quam-state load
```

Set configuration values:

```bash
cqc-quam-state set
```
(In development, the idea is to set the IP address and port of the OPX and octave and the calibration db dynamically here)

## State Files

The package includes pre-calibrated state files in the `quam_state/` directory:

- **`state.json`**: Main QuAM state configuration containing octave settings, RF outputs, and calibration parameters
- **`wiring.json`**: Wiring configuration for the quantum device setup

These files are automatically included when you install the package and can be accessed via the `QUAM_STATE_PATH` environment variable.

## Version Information

The package uses a date-based versioning system with optional sub-versions:

### Version Format: `YYYY.MM.DD[.X]`

- **`YYYY.MM.DD`**: The calibration date ( generated from `date +"%Y.%-m.%-d"`)
- **`.X`**: Optional sub-version for multiple releases on the same day

### Version Examples

- **`2025.6.4`**: First release on June 4, 2025
- **`2025.6.4.1`**: Second release on June 4, 2025 (updated calibration)
- **`2025.6.4.2`**: Third release on June 4, 2025
- **`2025.6.5`**: First release on June 5, 2025

## Troubleshooting

### Environment Variable Not Set

If the `QUAM_STATE_PATH` environment variable is not set after sourcing the script:

1. Ensure you're in the correct virtual environment
2. Verify the package is installed: `pip show cqc-quam-state`
3. Try running the load command directly: `cqc-quam-state load`

### Package Not Found

If you get import errors:

1. Check if the package is installed: `pip list | grep cqc-quam-state`
2. Ensure you're using the correct Python environment
3. Try reinstalling: `pip install --force-reinstall cqc-quam-state`


## License

This project is licensed under the MIT License.

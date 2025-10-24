# AI GPU Packages Installer

A Python package that automatically detects your NVIDIA GPU, determines the appropriate CUDA and PyTorch versions, and installs them for you.

## Installation

```bash
pip install ai-gpu-pkgs
```

## Usage

```bash
ai-gpu-pkgs setup
```

This command will:

1. Detect if you have an NVIDIA GPU
2. Check your current CUDA installation
3. Ask if you want to create a new virtual environment
4. Install PyTorch with CUDA support
5. Verify the installation

## Requirements

- Python 3.8+
- NVIDIA GPU with CUDA support
- Internet connection for downloading packages

## Features

- Automatic GPU detection
- CUDA version detection
- Virtual environment creation (optional)
- PyTorch installation with CUDA support
- Installation verification

## Development

To install in development mode:

```bash
git clone https://github.com/mrbeandev/cuda-auto-installer.git
cd cuda-auto-installer
pip install -e .
```

## License

MIT License

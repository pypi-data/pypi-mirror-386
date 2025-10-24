# Installation Guide

This guide provides comprehensive installation instructions for the LBMD SOTA Enhancement Framework across different platforms and environments.

## System Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space for framework and datasets
- **OS**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)

### Recommended Requirements
- **Python**: 3.9 or higher
- **RAM**: 32GB for large-scale experiments
- **GPU**: CUDA-compatible GPU with 8GB+ VRAM
- **Storage**: 100GB+ SSD for optimal performance
- **CPU**: 8+ cores for parallel processing

## Installation Methods

### Method 1: Install from PyPI (Recommended)

```bash
# Install the latest stable release
pip install lbmd-sota

# Install with GPU support
pip install lbmd-sota[gpu]

# Install with all optional dependencies
pip install lbmd-sota[all]
```

### Method 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/lbmd-research/lbmd-sota.git
cd lbmd-sota

# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e .[dev]
```

### Method 3: Docker Installation

```bash
# Pull the official Docker image
docker pull lbmdresearch/lbmd-sota:latest

# Run with GPU support
docker run --gpus all -it lbmdresearch/lbmd-sota:latest

# Run with volume mounting for data
docker run --gpus all -v /path/to/data:/data -it lbmdresearch/lbmd-sota:latest
```

### Method 4: Conda Installation

```bash
# Create a new conda environment
conda create -n lbmd-sota python=3.9
conda activate lbmd-sota

# Install from conda-forge
conda install -c conda-forge lbmd-sota

# Or install from source in conda environment
pip install -e .
```

## Platform-Specific Instructions

### Windows

#### Prerequisites
```powershell
# Install Python 3.9+ from python.org or Microsoft Store
# Install Git for Windows
# Install Visual Studio Build Tools (for some dependencies)

# Verify installations
python --version
git --version
```

#### Installation
```powershell
# Clone and install
git clone https://github.com/lbmd-research/lbmd-sota.git
cd lbmd-sota
pip install -e .

# Install CUDA toolkit for GPU support (optional)
# Download from https://developer.nvidia.com/cuda-downloads
```

#### Common Issues
- **Visual Studio Build Tools**: Some dependencies require C++ compilation
- **CUDA Path**: Ensure CUDA is in system PATH for GPU support
- **Long Path Support**: Enable long path support in Windows for deep directory structures

### macOS

#### Prerequisites
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python and Git
brew install python@3.9 git

# Install Xcode command line tools
xcode-select --install
```

#### Installation
```bash
# Clone and install
git clone https://github.com/lbmd-research/lbmd-sota.git
cd lbmd-sota
pip3 install -e .

# For Apple Silicon Macs, use conda for better compatibility
conda create -n lbmd-sota python=3.9
conda activate lbmd-sota
pip install -e .
```

#### Common Issues
- **Apple Silicon**: Some dependencies may need conda for ARM64 compatibility
- **OpenMP**: Install libomp for parallel processing: `brew install libomp`
- **Permissions**: Use `pip install --user` if encountering permission issues

### Linux (Ubuntu/Debian)

#### Prerequisites
```bash
# Update package list
sudo apt update

# Install Python, pip, and development tools
sudo apt install python3.9 python3.9-pip python3.9-dev git build-essential

# Install CUDA toolkit (for GPU support)
# Follow instructions at https://developer.nvidia.com/cuda-downloads
```

#### Installation
```bash
# Clone and install
git clone https://github.com/lbmd-research/lbmd-sota.git
cd lbmd-sota
pip3 install -e .

# Verify GPU support (if applicable)
python3 -c "import torch; print(torch.cuda.is_available())"
```

#### Common Issues
- **CUDA Version**: Ensure PyTorch CUDA version matches system CUDA
- **Permissions**: Add user to docker group for Docker usage: `sudo usermod -aG docker $USER`
- **Memory**: Increase swap space for large experiments

### Linux (CentOS/RHEL)

#### Prerequisites
```bash
# Install EPEL repository
sudo yum install epel-release

# Install Python and development tools
sudo yum install python39 python39-pip python39-devel git gcc gcc-c++

# Install CUDA toolkit (for GPU support)
# Follow NVIDIA's CentOS installation guide
```

#### Installation
```bash
# Clone and install
git clone https://github.com/lbmd-research/lbmd-sota.git
cd lbmd-sota
pip3.9 install -e .
```

## Virtual Environment Setup

### Using venv (Recommended)

```bash
# Create virtual environment
python -m venv lbmd-sota-env

# Activate (Linux/macOS)
source lbmd-sota-env/bin/activate

# Activate (Windows)
lbmd-sota-env\Scripts\activate

# Install framework
pip install -e .

# Deactivate when done
deactivate
```

### Using conda

```bash
# Create environment with specific Python version
conda create -n lbmd-sota python=3.9 numpy scipy matplotlib

# Activate environment
conda activate lbmd-sota

# Install framework
pip install -e .

# Deactivate when done
conda deactivate
```

## GPU Support Setup

### NVIDIA CUDA

```bash
# Check NVIDIA driver
nvidia-smi

# Install CUDA toolkit (version 11.8 recommended)
# Download from https://developer.nvidia.com/cuda-downloads

# Verify CUDA installation
nvcc --version

# Install PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verify GPU support in Python
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### AMD ROCm (Experimental)

```bash
# Install ROCm (Linux only)
# Follow AMD's ROCm installation guide

# Install PyTorch with ROCm support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.4.2
```

## Dependency Management

### Core Dependencies

The framework automatically installs these core dependencies:

```
torch>=1.8.0
torchvision>=0.9.0
numpy>=1.19.0
scipy>=1.7.0
scikit-learn>=0.24.0
matplotlib>=3.3.0
seaborn>=0.11.0
pandas>=1.3.0
opencv-python>=4.5.0
tqdm>=4.60.0
pyyaml>=5.4.0
```

### Optional Dependencies

Install optional dependencies for specific features:

```bash
# Visualization enhancements
pip install plotly bokeh dash

# Advanced statistical analysis
pip install statsmodels pingouin

# Performance profiling
pip install memory-profiler psutil

# Development tools
pip install pytest black flake8 mypy

# Documentation generation
pip install sphinx sphinx-rtd-theme

# Jupyter notebook support
pip install jupyter ipywidgets
```

### Development Dependencies

For contributors and developers:

```bash
# Install development dependencies
pip install -e .[dev]

# Or manually install
pip install pytest pytest-cov black flake8 mypy pre-commit sphinx
```

## Verification

### Basic Installation Test

```python
# Test basic import
python -c "import lbmd_sota; print('Installation successful!')"

# Test core components
python -c "
from lbmd_sota.core import LBMDConfig
from lbmd_sota.empirical_validation import MultiDatasetEvaluator
from lbmd_sota.visualization import InteractiveManifoldExplorer
print('All core components imported successfully!')
"
```

### Comprehensive Test Suite

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_core.py -v
python -m pytest tests/test_empirical_validation.py -v
python -m pytest tests/test_visualization.py -v

# Run with coverage report
python -m pytest tests/ --cov=lbmd_sota --cov-report=html
```

### Performance Benchmark

```python
# Run performance benchmark
from lbmd_sota.evaluation import PerformanceTester

tester = PerformanceTester()
results = tester.run_quick_benchmark()
print(f"Installation performance score: {results.overall_score}")
```

## Configuration

### Initial Setup

```bash
# Create configuration directory
mkdir -p ~/.lbmd-sota/configs

# Copy default configuration
cp configs/default_config.yaml ~/.lbmd-sota/configs/

# Set environment variables (optional)
export LBMD_CONFIG_DIR=~/.lbmd-sota/configs
export LBMD_DATA_DIR=~/lbmd-data
export LBMD_CACHE_DIR=~/lbmd-cache
```

### Configuration File

Create a basic configuration file:

```yaml
# ~/.lbmd-sota/configs/basic_config.yaml
datasets:
  data_dir: "~/lbmd-data"
  cache_dir: "~/lbmd-cache"

models:
  checkpoint_dir: "~/lbmd-models"

computation:
  device: "auto"  # auto, cpu, cuda
  num_workers: 4
  batch_size: 8

visualization:
  output_dir: "~/lbmd-results"
  figure_format: "png"
  interactive: true
```

## Troubleshooting

### Common Installation Issues

#### Import Errors
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Reinstall in development mode
pip uninstall lbmd-sota
pip install -e .
```

#### CUDA Issues
```bash
# Check CUDA compatibility
python -c "import torch; print(torch.version.cuda)"

# Reinstall PyTorch with correct CUDA version
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### Memory Issues
```bash
# Check available memory
python -c "import psutil; print(f'Available RAM: {psutil.virtual_memory().available / 1e9:.1f} GB')"

# Reduce batch size in configuration
# Set OMP_NUM_THREADS=1 to reduce memory usage
export OMP_NUM_THREADS=1
```

#### Permission Issues
```bash
# Install in user directory
pip install --user -e .

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows
pip install -e .
```

### Getting Help

- **Documentation**: Check the [API documentation](api/) and [tutorials](tutorials/)
- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions in GitHub Discussions
- **Community**: Join the LBMD research community

### Uninstallation

```bash
# Uninstall package
pip uninstall lbmd-sota

# Remove configuration and cache (optional)
rm -rf ~/.lbmd-sota
rm -rf ~/lbmd-cache

# Remove conda environment (if used)
conda remove -n lbmd-sota --all
```

## Next Steps

After successful installation:

1. **Quick Start**: Follow the [Quick Start Guide](quickstart.md)
2. **Tutorials**: Work through the [tutorial notebooks](tutorials/)
3. **Examples**: Explore the [example scripts](examples/)
4. **Configuration**: Customize your [configuration](configuration.md)
5. **API Reference**: Browse the [API documentation](api/)

## Support

If you encounter issues during installation:

1. Check this troubleshooting section
2. Search existing [GitHub issues](https://github.com/lbmd-research/lbmd-sota/issues)
3. Create a new issue with:
   - Operating system and version
   - Python version
   - Complete error message
   - Installation method used
   - Hardware specifications (especially for GPU issues)
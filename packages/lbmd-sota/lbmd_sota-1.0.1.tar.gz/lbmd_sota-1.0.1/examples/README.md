# LBMD SOTA Framework Examples

This directory contains comprehensive examples demonstrating the capabilities of the LBMD SOTA Enhancement Framework. Each example is self-contained and includes detailed explanations.

## 📁 Example Categories

### 🚀 Basic Examples
- [`basic_analysis.py`](basic_analysis.py) - Simple boundary analysis workflow
- [`interactive_lbmd_demo.py`](interactive_lbmd_demo.py) - Interactive comprehensive demo with real-time parameter adjustment
- [`popular_datasets_analysis.py`](popular_datasets_analysis.py) - Analysis on popular CV datasets (COCO, Cityscapes, Pascal VOC, ADE20K)

### 📓 Interactive Notebooks
- [`notebooks/01_lbmd_quickstart_demo.ipynb`](notebooks/01_lbmd_quickstart_demo.ipynb) - Interactive quickstart tutorial
- [`notebooks/02_lbmd_visualization_demo.ipynb`](notebooks/02_lbmd_visualization_demo.ipynb) - Advanced visualization techniques

### 🏥 Case Studies
- [`case_studies/medical_imaging_case_study.py`](case_studies/medical_imaging_case_study.py) - Medical image segmentation analysis
- [`case_studies/autonomous_driving_case_study.py`](case_studies/autonomous_driving_case_study.py) - Traffic scene boundary analysis

### 🔬 Analysis Examples
- [`comparative_analysis_demo.py`](comparative_analysis_demo.py) - Baseline method comparison
- [`empirical_validation_demo.py`](empirical_validation_demo.py) - Multi-dataset evaluation
- [`statistical_analysis_demo.py`](statistical_analysis_demo.py) - Statistical validation

### 🚀 Model Improvement Examples
- [`architecture_enhancement_demo.py`](architecture_enhancement_demo.py) - Model architecture improvements
- [`loss_function_demo.py`](loss_function_demo.py) - Custom boundary-aware loss functions
- [`data_augmentation_demo.py`](data_augmentation_demo.py) - Targeted augmentation strategies

### 🎨 Visualization Examples
- [`interactive_manifold_demo.py`](interactive_manifold_demo.py) - Interactive 3D visualizations
- [`publication_figures_demo.py`](publication_figures_demo.py) - Publication-quality figures
- [`dashboard_demo.py`](dashboard_demo.py) - Real-time analysis dashboard

### 🧮 Advanced Examples
- [`theoretical_analysis_demo.py`](theoretical_analysis_demo.py) - Theoretical framework usage
- [`large_scale_experiment_demo.py`](large_scale_experiment_demo.py) - Distributed experiments
- [`custom_component_demo.py`](custom_component_demo.py) - Framework extension

## 🎯 Quick Start Examples

### Run Basic Analysis
```bash
python examples/basic_analysis.py --dataset coco --model maskrcnn
```

### Interactive Demo (Recommended for Beginners)
```bash
python examples/interactive_lbmd_demo.py --jupyter
```

### Popular Datasets Analysis
```bash
python examples/popular_datasets_analysis.py --datasets coco cityscapes pascal_voc --num-samples 10
```

### Medical Imaging Case Study
```bash
python examples/case_studies/medical_imaging_case_study.py --num-cases 5
```

### Autonomous Driving Case Study
```bash
python examples/case_studies/autonomous_driving_case_study.py --num-scenes 5
```

### Compare Methods
```bash
python examples/comparative_analysis_demo.py --baseline gradcam --baseline lime
```

### Generate Visualizations
```bash
python examples/visualization_demo.py --interactive --output ./results
```

## 📋 Prerequisites

### Software Requirements
- Python 3.8+
- LBMD SOTA Framework installed
- PyTorch 1.8+
- Additional dependencies per example

### Hardware Requirements
- **Basic Examples**: 8GB RAM, CPU
- **Advanced Examples**: 16GB+ RAM, GPU recommended
- **Large-Scale Examples**: 32GB+ RAM, multiple GPUs

### Data Requirements
Most examples will automatically download sample data. For full datasets:
- **COCO**: ~20GB
- **Cityscapes**: ~11GB
- **Pascal VOC**: ~2GB

## 🚀 Running Examples

### Method 1: Direct Execution
```bash
# Run specific example
python examples/basic_analysis.py

# With custom parameters
python examples/basic_analysis.py --config custom_config.yaml --output ./my_results
```

### Method 2: Module Execution
```bash
# Run as module
python -m examples.basic_analysis

# With parameters
python -m examples.basic_analysis --help
```

### Method 3: Interactive Mode
```bash
# Start Python and import
python
>>> from examples import basic_analysis
>>> basic_analysis.run_demo()
```

## 📖 Example Descriptions

### Basic Analysis (`basic_analysis.py`)
**Purpose**: Demonstrate core LBMD functionality  
**Duration**: 5-10 minutes  
**Requirements**: 8GB RAM, sample dataset

```python
# Key features demonstrated:
- Model loading and configuration
- Boundary analysis workflow
- Basic result visualization
- Statistical summary generation
```

**Usage**:
```bash
python examples/basic_analysis.py --model maskrcnn --layer backbone.layer4
```

### Interactive Demo (`interactive_lbmd_demo.py`)
**Purpose**: Comprehensive interactive demonstration with real-time parameter adjustment  
**Duration**: 15-30 minutes  
**Requirements**: 8GB RAM, Jupyter notebook environment (optional)

```python
# Key features demonstrated:
- Interactive parameter tuning
- Real-time visualization updates
- Multi-dataset comparison
- Baseline method comparison
- Export capabilities
```

**Usage**:
```bash
# For Jupyter notebook mode
python examples/interactive_lbmd_demo.py --jupyter

# For command line mode
python examples/interactive_lbmd_demo.py
```

### Popular Datasets Analysis (`popular_datasets_analysis.py`)
**Purpose**: Comprehensive analysis across multiple popular computer vision datasets  
**Duration**: 30-60 minutes  
**Requirements**: 16GB RAM, GPU recommended

```python
# Key features demonstrated:
- Multi-dataset evaluation (COCO, Cityscapes, Pascal VOC, ADE20K, Medical)
- Cross-dataset comparison
- Standardized metrics
- Statistical significance testing
- Synthetic data generation for each dataset type
```

**Usage**:
```bash
python examples/popular_datasets_analysis.py \
    --datasets coco cityscapes pascal_voc ade20k medical \
    --num-samples 10 \
    --output-dir ./multi_dataset_results
```

### Medical Imaging Case Study (`case_studies/medical_imaging_case_study.py`)
**Purpose**: Specialized analysis for medical image segmentation  
**Duration**: 20-40 minutes  
**Requirements**: 12GB RAM, medical imaging knowledge helpful

```python
# Key features demonstrated:
- Medical dataset handling (brain MRI, chest CT, dermoscopy, etc.)
- Clinical metric calculation
- Boundary analysis for diagnostic accuracy
- Regulatory compliance considerations
- Case study generation with detailed explanations
```

**Usage**:
```bash
python examples/case_studies/medical_imaging_case_study.py \
    --num-cases 5 \
    --output-dir ./medical_case_study_results
```

### Autonomous Driving Case Study (`case_studies/autonomous_driving_case_study.py`)
**Purpose**: Safety-critical boundary analysis for autonomous driving scenarios  
**Duration**: 20-40 minutes  
**Requirements**: 12GB RAM, understanding of autonomous driving helpful

```python
# Key features demonstrated:
- Traffic scene analysis (urban, highway, residential, construction zones)
- Safety metric evaluation
- Real-time processing considerations
- Failure impact assessment
- Multi-class boundary analysis (vehicles, pedestrians, infrastructure)
```

**Usage**:
```bash
python examples/case_studies/autonomous_driving_case_study.py \
    --num-scenes 5 \
    --output-dir ./autonomous_driving_case_study_results
```

### Configuration Demo (`configuration_demo.py`)
**Purpose**: Show configuration system capabilities  
**Duration**: 3-5 minutes  
**Requirements**: Minimal

```python
# Key features demonstrated:
- YAML configuration loading
- Parameter validation
- Configuration inheritance
- Environment variable integration
```

### Empirical Validation Demo (`empirical_validation_demo.py`)
**Purpose**: Multi-dataset evaluation workflow  
**Duration**: 30-60 minutes  
**Requirements**: 16GB RAM, GPU recommended

```python
# Key features demonstrated:
- Multi-dataset evaluation
- Statistical significance testing
- Correlation analysis
- Ablation studies
```

**Usage**:
```bash
python examples/empirical_validation_demo.py \
    --datasets coco cityscapes \
    --models maskrcnn solo yolact \
    --output ./validation_results
```

### Comparative Analysis Demo (`comparative_analysis_demo.py`)
**Purpose**: Compare LBMD with baseline methods  
**Duration**: 20-30 minutes  
**Requirements**: 12GB RAM, GPU recommended

```python
# Key features demonstrated:
- Baseline method implementation
- Quantitative comparison metrics
- Failure mode analysis
- Unique insight identification
```

### Model Improvement Demos

#### Architecture Enhancement (`architecture_enhancement_demo.py`)
```python
# Demonstrates:
- Weakness identification
- Architecture modification suggestions
- Performance improvement validation
```

#### Loss Function Design (`loss_function_demo.py`)
```python
# Demonstrates:
- Boundary-aware loss functions
- Adaptive loss weighting
- Training integration
```

#### Data Augmentation (`data_augmentation_demo.py`)
```python
# Demonstrates:
- Weakness-based augmentation
- Boundary-focused techniques
- Pipeline integration
```

### Visualization Demos

#### Interactive Manifold (`interactive_manifold_demo.py`)
```python
# Demonstrates:
- 3D manifold visualization
- Interactive parameter adjustment
- Real-time updates
```

#### Publication Figures (`publication_figures_demo.py`)
```python
# Demonstrates:
- Automated figure generation
- Publication-quality styling
- Multi-format export
```

#### Dashboard (`dashboard_demo.py`)
```python
# Demonstrates:
- Web-based dashboard
- Real-time analysis
- Collaborative features
```

### Application Examples

#### Medical Imaging (`medical_imaging_demo.py`)
**Purpose**: Medical image segmentation analysis  
**Dataset**: Medical imaging samples  
**Focus**: Clinical interpretation and validation

```python
# Key features:
- Medical dataset handling
- Clinical metric calculation
- Regulatory compliance considerations
- Case study generation
```

#### Autonomous Driving (`autonomous_driving_demo.py`)
**Purpose**: Traffic scene boundary analysis  
**Dataset**: Cityscapes or custom traffic data  
**Focus**: Safety-critical interpretation

```python
# Key features:
- Traffic scene analysis
- Safety metric evaluation
- Real-time processing considerations
- Failure impact assessment
```

## 🔧 Configuration

### Example Configuration File
```yaml
# examples/config/demo_config.yaml
datasets:
  data_dir: "./data"
  cache_dir: "./cache"
  batch_size: 8

models:
  checkpoint_dir: "./models"
  architecture: "maskrcnn_r50_fpn"

lbmd_parameters:
  k_neurons: 20
  epsilon: 0.1
  tau: 0.5
  manifold_method: "umap"

visualization:
  output_dir: "./results"
  figure_format: "png"
  interactive: true

computation:
  device: "auto"
  num_workers: 4
  mixed_precision: true
```

### Environment Variables
```bash
# Set common paths
export LBMD_DATA_DIR="./data"
export LBMD_CACHE_DIR="./cache"
export LBMD_OUTPUT_DIR="./results"

# Set computation preferences
export LBMD_DEVICE="cuda"
export LBMD_NUM_WORKERS="8"
```

## 📊 Expected Outputs

### Analysis Results
- **Boundary scores**: Neuron responsiveness rankings
- **Manifold coordinates**: 2D/3D visualization data
- **Cluster assignments**: Boundary pattern groups
- **Statistical metrics**: Correlation and significance tests

### Visualizations
- **Boundary overlays**: Detected boundaries on images
- **Manifold plots**: 2D/3D scatter plots with clusters
- **Statistical charts**: Correlation plots, histograms
- **Interactive dashboards**: Web-based exploration tools

### Reports
- **HTML reports**: Comprehensive analysis summaries
- **CSV data**: Tabular results for further analysis
- **JSON metadata**: Experiment configuration and metrics

## 🐛 Troubleshooting

### Common Issues

#### Memory Errors
```bash
# Reduce batch size
python examples/basic_analysis.py --batch-size 2

# Use CPU instead of GPU
python examples/basic_analysis.py --device cpu
```

#### Missing Data
```bash
# Download sample data
python examples/download_sample_data.py

# Use synthetic data
python examples/basic_analysis.py --synthetic-data
```

#### Slow Performance
```bash
# Reduce dataset size
python examples/basic_analysis.py --max-images 10

# Use fewer workers
python examples/basic_analysis.py --num-workers 2
```

#### Import Errors
```bash
# Check installation
python -c "import lbmd_sota; print('OK')"

# Reinstall if needed
pip install --upgrade lbmd-sota
```

### Debug Mode
```bash
# Enable debug logging
python examples/basic_analysis.py --debug

# Verbose output
python examples/basic_analysis.py --verbose
```

## 🎓 Learning Progression

### Beginner Path
1. `basic_analysis.py` - Understand core concepts
2. `configuration_demo.py` - Learn configuration system
3. `visualization_demo.py` - Explore visualization options

### Intermediate Path
4. `empirical_validation_demo.py` - Multi-dataset analysis
5. `comparative_analysis_demo.py` - Method comparison
6. `statistical_analysis_demo.py` - Statistical validation

### Advanced Path
7. `architecture_enhancement_demo.py` - Model improvement
8. `theoretical_analysis_demo.py` - Theoretical framework
9. `large_scale_experiment_demo.py` - Production workflows

### Application Path
10. Choose domain-specific examples:
    - `medical_imaging_demo.py`
    - `autonomous_driving_demo.py`
    - `quality_control_demo.py`

## 📈 Performance Benchmarks

### Execution Times (approximate)
- **Basic Analysis**: 2-5 minutes
- **Comparative Analysis**: 10-20 minutes
- **Empirical Validation**: 30-120 minutes
- **Large-Scale Experiments**: 2-24 hours

### Memory Usage (approximate)
- **Basic Examples**: 2-4GB
- **Advanced Examples**: 8-16GB
- **Large-Scale Examples**: 16-64GB

### GPU Acceleration
- **Speedup**: 5-20x faster with GPU
- **Memory**: GPU memory usage typically 2-4GB
- **Compatibility**: CUDA 11.0+ recommended

## 🤝 Contributing Examples

### Adding New Examples
1. Create example file in appropriate category
2. Follow naming convention: `{topic}_demo.py`
3. Include comprehensive docstring
4. Add command-line argument parsing
5. Include error handling and logging
6. Update this README

### Example Template
```python
#!/usr/bin/env python3
"""
LBMD SOTA Framework - {Example Name} Demo

This example demonstrates {key functionality}.

Usage:
    python examples/{filename}.py [options]

Requirements:
    - {list requirements}

Expected Output:
    - {describe outputs}
"""

import argparse
import logging
from pathlib import Path

from lbmd_sota.core import LBMDConfig
# ... other imports

def main():
    """Main demonstration function."""
    parser = argparse.ArgumentParser(description=__doc__)
    # Add arguments
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Run demonstration
    try:
        run_demo(args)
    except Exception as e:
        logging.error(f"Demo failed: {e}")
        return 1
    
    return 0

def run_demo(args):
    """Run the actual demonstration."""
    # Implementation here
    pass

if __name__ == "__main__":
    exit(main())
```

## 📚 Additional Resources

### Documentation
- [API Reference](../docs/api/) - Detailed API documentation
- [Tutorials](../docs/tutorials/) - Step-by-step learning materials
- [Configuration Guide](../docs/configuration.md) - Configuration reference

### Community
- [GitHub Discussions](https://github.com/lbmd-research/lbmd-sota/discussions) - Q&A and discussions
- [Issues](https://github.com/lbmd-research/lbmd-sota/issues) - Bug reports and feature requests
- [Research Papers](https://lbmd-research.github.io/papers/) - Academic publications

### Support
- **Example Issues**: Report problems with specific examples
- **Feature Requests**: Suggest new examples or improvements
- **Community Help**: Ask questions in GitHub Discussions

---

**Ready to explore?** Start with `basic_analysis.py` and work your way through the examples that match your interests and use case!
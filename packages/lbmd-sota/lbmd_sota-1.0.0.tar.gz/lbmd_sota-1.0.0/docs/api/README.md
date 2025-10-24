# LBMD SOTA Framework API Documentation

This directory contains comprehensive API documentation for all components of the LBMD SOTA Enhancement Framework.

## Documentation Structure

- [`core/`](core/) - Core interfaces, data models, and configuration
- [`empirical_validation/`](empirical_validation/) - Multi-dataset evaluation and statistical analysis
- [`comparative_analysis/`](comparative_analysis/) - Baseline comparison and failure analysis
- [`model_improvement/`](model_improvement/) - Architecture enhancement and loss design
- [`visualization/`](visualization/) - Interactive visualizations and figure generation
- [`theoretical_framework/`](theoretical_framework/) - Mathematical formalization and topological analysis
- [`evaluation/`](evaluation/) - Experiment orchestration and performance testing

## Quick Reference

### Core Classes

```python
from lbmd_sota.core import LBMDConfig, LBMDResults, BoundaryMetrics
from lbmd_sota.empirical_validation import MultiDatasetEvaluator
from lbmd_sota.comparative_analysis import BaselineComparator
from lbmd_sota.model_improvement import ArchitectureEnhancer
from lbmd_sota.visualization import InteractiveManifoldExplorer
from lbmd_sota.theoretical_framework import TopologicalAnalyzer
```

### Configuration

All components use the unified configuration system:

```python
from lbmd_sota.core.config import load_global_config

config = load_global_config("configs/my_experiment.yaml")
```

### Error Handling

The framework provides structured error handling:

```python
from lbmd_sota.core.interfaces import (
    LBMDError, DatasetError, ModelArchitectureError,
    ManifoldConstructionError, VisualizationError
)
```

## Getting Started

1. **Installation**: See [Installation Guide](../installation.md)
2. **Configuration**: See [Configuration Guide](../configuration.md)
3. **Tutorials**: See [Tutorial Notebooks](../tutorials/)
4. **Examples**: See [Example Scripts](../examples/)

## API Conventions

### Method Naming
- `initialize()`: Component initialization and setup
- `analyze()`: Core analysis methods
- `generate()`: Output generation methods
- `validate()`: Validation and testing methods

### Return Types
- Analysis methods return structured data models from `lbmd_sota.core.data_models`
- Generation methods return file paths or visualization objects
- Validation methods return boolean success flags and detailed reports

### Error Handling
- All methods raise specific exception types for different error conditions
- Methods include comprehensive logging for debugging
- Graceful degradation when possible with warning messages

### Configuration
- All components accept configuration dictionaries or objects
- Default configurations provided for all parameters
- Validation of configuration parameters on initialization

## Performance Considerations

### Memory Management
- Large datasets are processed in batches to manage memory usage
- Automatic cleanup of intermediate results
- Memory profiling available through performance testing tools

### Computational Efficiency
- GPU acceleration supported where applicable
- Parallel processing for independent operations
- Caching of expensive computations

### Scalability
- Distributed execution support for large-scale experiments
- Configurable batch sizes and worker counts
- Progress tracking for long-running operations

## Version Compatibility

- **Python**: 3.8+ required, 3.9+ recommended
- **PyTorch**: 1.8+ required, 2.0+ recommended
- **CUDA**: 11.0+ for GPU acceleration
- **Dependencies**: See `requirements.txt` for complete list

## Support

- **Issues**: Report bugs and feature requests on GitHub
- **Discussions**: Community discussions and questions
- **Documentation**: This API documentation and tutorials
- **Examples**: Working code examples for all major features
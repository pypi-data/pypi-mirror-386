# Quick Start Guide

Get up and running with the LBMD SOTA Enhancement Framework in minutes!

## 🚀 5-Minute Quick Start

### 1. Install the Framework

```bash
# Install from PyPI (recommended)
pip install lbmd-sota

# Or install from source
git clone https://github.com/lbmd-research/lbmd-sota.git
cd lbmd-sota
pip install -e .
```

### 2. Verify Installation

```python
import lbmd_sota
print("✅ LBMD SOTA Framework installed successfully!")
```

### 3. Run Your First Analysis

```python
from lbmd_sota.core import LBMDConfig
from lbmd_sota.empirical_validation import MultiDatasetEvaluator
from lbmd_sota.visualization import InteractiveManifoldExplorer

# Create configuration
config = LBMDConfig({
    'lbmd_parameters': {
        'k_neurons': 20,
        'epsilon': 0.1,
        'tau': 0.5,
        'manifold_method': 'umap'
    }
})

# Initialize evaluator
evaluator = MultiDatasetEvaluator(config)
evaluator.initialize()

# Run analysis (with your model and data)
results = evaluator.analyze_boundary_manifolds(model, input_tensor)

# Visualize results
explorer = InteractiveManifoldExplorer(config.visualization)
explorer.create_interactive_manifold(results.manifold_data)
```

## 📖 What is LBMD?

**Latent Boundary Manifold Decomposition (LBMD)** is a mechanistic interpretability method for understanding how instance segmentation models process object boundaries.

### Key Capabilities

- 🔍 **Boundary Analysis**: Identify neurons that respond to object boundaries
- 🗺️ **Manifold Visualization**: Explore high-dimensional boundary representations
- 📊 **Statistical Validation**: Rigorous quantitative analysis with significance testing
- 🔧 **Model Improvement**: Actionable insights for enhancing model performance
- 📈 **Comparative Analysis**: Compare with existing interpretability methods

### Core Concepts

- **Boundary Responsiveness**: How strongly neurons activate near object boundaries
- **Manifold Structure**: Geometric organization of boundary patterns in latent space
- **Transition Strength**: Clarity of boundaries between different object regions
- **Cluster Analysis**: Groups of similar boundary processing patterns

## 🎯 Use Cases

### Research Applications
- **Mechanistic Interpretability**: Understand how models process boundaries
- **Model Analysis**: Identify architectural strengths and weaknesses
- **Failure Diagnosis**: Analyze why segmentation fails in specific cases
- **Method Comparison**: Compare interpretability approaches quantitatively

### Practical Applications
- **Medical Imaging**: Analyze boundary detection in medical scans
- **Autonomous Driving**: Understand object boundary processing in traffic scenes
- **Quality Control**: Inspect boundary detection in manufacturing
- **Scientific Imaging**: Analyze boundary patterns in research images

## 🛠️ Framework Components

### 1. Empirical Validation Engine
```python
from lbmd_sota.empirical_validation import MultiDatasetEvaluator

evaluator = MultiDatasetEvaluator(config)
results = evaluator.run_comprehensive_evaluation(['coco', 'cityscapes'], ['maskrcnn', 'solo'])
```

### 2. Comparative Analysis System
```python
from lbmd_sota.comparative_analysis import BaselineComparator

comparator = BaselineComparator(config)
comparison = comparator.compare_with_baselines(image_tensor)
```

### 3. Model Improvement Toolkit
```python
from lbmd_sota.model_improvement import ArchitectureEnhancer

enhancer = ArchitectureEnhancer(config)
suggestions = enhancer.suggest_architecture_improvements(lbmd_results)
```

### 4. Visualization Platform
```python
from lbmd_sota.visualization import InteractiveManifoldExplorer

explorer = InteractiveManifoldExplorer(config)
visualization = explorer.create_interactive_manifold(manifold_data)
```

### 5. Theoretical Framework
```python
from lbmd_sota.theoretical_framework import TopologicalAnalyzer

analyzer = TopologicalAnalyzer(config)
properties = analyzer.compute_topological_properties(manifold)
```

## 📊 Example Results

### Boundary Detection
```python
# Analyze boundary responsiveness
boundary_scores = results.boundary_scores
print(f"Top boundary neuron score: {max(boundary_scores):.3f}")
print(f"Boundary coverage: {np.mean(results.boundary_mask):.1%}")
```

### Manifold Analysis
```python
# Explore manifold structure
n_clusters = len(np.unique(results.clusters))
print(f"Discovered {n_clusters} boundary pattern clusters")

# Analyze transitions
avg_transition = np.mean(list(results.transition_strengths.values()))
print(f"Average transition strength: {avg_transition:.3f}")
```

### Statistical Validation
```python
# Validate correlations
correlation_report = evaluator.validate_correlation_claims(0.78)
print(f"Correlation significance: p < {correlation_report.p_value:.3f}")
```

## 🎓 Learning Path

### Beginner (30 minutes)
1. **[Quick Start Tutorial](tutorials/01_quickstart.ipynb)** - Basic concepts and first analysis
2. **[Configuration Guide](tutorials/02_configuration.ipynb)** - Customizing analysis parameters
3. **[Data Loading](tutorials/03_data_loading.ipynb)** - Working with different datasets

### Intermediate (2 hours)
4. **[Boundary Analysis](tutorials/04_boundary_analysis.ipynb)** - Deep dive into boundary detection
5. **[Manifold Exploration](tutorials/05_manifold_exploration.ipynb)** - Interactive visualization
6. **[Statistical Validation](tutorials/06_statistical_validation.ipynb)** - Rigorous analysis methods

### Advanced (4+ hours)
7. **[Comparative Analysis](tutorials/07_baseline_comparison.ipynb)** - Compare with other methods
8. **[Model Improvement](tutorials/10_architecture_enhancement.ipynb)** - Enhance model performance
9. **[Large-Scale Experiments](tutorials/17_large_scale_experiments.ipynb)** - Production workflows

## 🔧 Configuration

### Basic Configuration
```yaml
# config.yaml
datasets:
  data_dir: "./data"
  batch_size: 8

models:
  architecture: "maskrcnn_r50_fpn"
  checkpoint_dir: "./models"

lbmd_parameters:
  k_neurons: 20
  epsilon: 0.1
  tau: 0.5
  manifold_method: "umap"

visualization:
  output_dir: "./results"
  interactive: true
```

### Load Configuration
```python
from lbmd_sota.core.config import load_global_config

config = load_global_config("config.yaml")
```

## 📈 Performance Tips

### Memory Optimization
```python
# Use smaller batch sizes for large images
config.datasets.batch_size = 4

# Enable gradient checkpointing
config.computation.gradient_checkpointing = True

# Use mixed precision
config.computation.mixed_precision = True
```

### Speed Optimization
```python
# Use multiple workers
config.computation.num_workers = 8

# Enable caching
config.datasets.cache_dir = "./cache"

# Use GPU acceleration
config.computation.device = "cuda"
```

## 🐛 Troubleshooting

### Common Issues

**Import Error**
```bash
# Reinstall framework
pip uninstall lbmd-sota
pip install lbmd-sota
```

**CUDA Issues**
```python
# Check CUDA availability
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
```

**Memory Issues**
```python
# Reduce batch size
config.datasets.batch_size = 2

# Clear cache
torch.cuda.empty_cache()
```

**Slow Performance**
```python
# Check number of workers
import multiprocessing
print(f"Available CPUs: {multiprocessing.cpu_count()}")

# Optimize worker count
config.computation.num_workers = min(8, multiprocessing.cpu_count())
```

## 📚 Next Steps

### Explore Tutorials
- **[All Tutorials](tutorials/)** - Comprehensive learning materials
- **[API Documentation](api/)** - Detailed reference
- **[Examples](examples/)** - Working code examples

### Join the Community
- **[GitHub Repository](https://github.com/lbmd-research/lbmd-sota)** - Source code and issues
- **[Discussions](https://github.com/lbmd-research/lbmd-sota/discussions)** - Community Q&A
- **[Research Papers](https://lbmd-research.github.io/papers/)** - Academic publications

### Contribute
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute
- **[Development Setup](docs/development.md)** - Developer environment
- **[Issue Templates](https://github.com/lbmd-research/lbmd-sota/issues/new/choose)** - Report bugs or request features

## 🎉 Success!

You're now ready to explore the powerful capabilities of the LBMD SOTA Enhancement Framework. Start with the [Quick Start Tutorial](tutorials/01_quickstart.ipynb) to dive deeper into boundary manifold analysis!

---

**Need Help?** 
- 📖 Check the [documentation](api/)
- 💬 Ask in [discussions](https://github.com/lbmd-research/lbmd-sota/discussions)
- 🐛 Report issues on [GitHub](https://github.com/lbmd-research/lbmd-sota/issues)
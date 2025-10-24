"""
LBMD SOTA Framework - Latent Boundary Manifold Decomposition for State-of-the-Art Mechanistic Interpretability

This package provides a comprehensive framework for analyzing and interpreting neural network
boundary detection capabilities through manifold decomposition techniques.

Main Components:
- Core: Configuration, data models, and interfaces
- Empirical Validation: Multi-dataset evaluation and statistical analysis
- Comparative Analysis: Baseline method comparison and failure mode analysis
- Model Improvement: Architecture enhancement and boundary-aware training
- Visualization: Interactive exploration and publication-quality figures
- Theoretical Framework: Mathematical formalization and topological analysis
- Evaluation: Comprehensive reporting and experiment orchestration

Usage:
    from lbmd_sota import LBMDConfig, MultiDatasetEvaluator
    
    config = LBMDConfig.from_file('config.yaml')
    evaluator = MultiDatasetEvaluator(config)
    results = evaluator.analyze_model(model, dataset)
"""

__version__ = "1.0.1"
__author__ = "LBMD Research Team"
__email__ = "research@lbmd.ai"
__license__ = "MIT"

# Core imports
from lbmd_sota.core.config import LBMDConfig
from lbmd_sota.core.data_models import LBMDResults, StatisticalMetrics, TopologicalProperties
from lbmd_sota.core.analyzer import LBMDAnalyzer
from lbmd_sota.core.interfaces import (
    DatasetInterface,
    ModelInterface,
    BoundaryDetectorInterface,
    ManifoldLearnerInterface
)

# Main components
from lbmd_sota.empirical_validation.multi_dataset_evaluator import MultiDatasetEvaluator
from lbmd_sota.comparative_analysis.baseline_comparator import BaselineComparator
from lbmd_sota.model_improvement.architecture_enhancer import ArchitectureEnhancer
from lbmd_sota.visualization.interactive_manifold_explorer import InteractiveManifoldExplorer
from lbmd_sota.evaluation.experiment_orchestrator import ExperimentOrchestrator

# Utility functions
def get_version():
    """Get the current version of the LBMD SOTA framework."""
    return __version__

def get_config_template():
    """Get a template configuration dictionary."""
    return {
        'datasets': {
            'data_dir': './data',
            'cache_dir': './cache',
            'batch_size': 8
        },
        'models': {
            'checkpoint_dir': './models',
            'architecture': 'maskrcnn_r50_fpn'
        },
        'lbmd_parameters': {
            'k_neurons': 20,
            'epsilon': 0.1,
            'tau': 0.5,
            'manifold_method': 'umap'
        },
        'visualization': {
            'output_dir': './results',
            'interactive': True,
            'figure_format': 'png'
        },
        'computation': {
            'device': 'auto',
            'num_workers': 4,
            'mixed_precision': True
        }
    }

def quick_start():
    """Print quick start instructions."""
    print("""
🚀 LBMD SOTA Framework Quick Start

1. Basic Analysis:
   from lbmd_sota import LBMDConfig, MultiDatasetEvaluator
   
   config = LBMDConfig(get_config_template())
   evaluator = MultiDatasetEvaluator(config)
   results = evaluator.analyze_model(model, dataset)

2. Interactive Demo:
   python -m lbmd_sota.examples.interactive_demo

3. Command Line Tools:
   lbmd-demo --help
   lbmd-analyze --model maskrcnn --dataset coco
   lbmd-compare --baseline gradcam

4. Documentation:
   Visit: https://lbmd-sota.readthedocs.io/
    """)

# Package metadata
__all__ = [
    # Version info
    '__version__',
    'get_version',
    
    # Core classes
    'LBMDConfig',
    'LBMDAnalyzer',
    'LBMDResults',
    'StatisticalMetrics',
    'TopologicalProperties',
    
    # Interfaces
    'DatasetInterface',
    'ModelInterface',
    'BoundaryDetectorInterface',
    'ManifoldLearnerInterface',
    
    # Main components
    'MultiDatasetEvaluator',
    'BaselineComparator',
    'ArchitectureEnhancer',
    'InteractiveManifoldExplorer',
    'ExperimentOrchestrator',
    
    # Utilities
    'get_config_template',
    'quick_start',
]
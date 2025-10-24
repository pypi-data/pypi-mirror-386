# Core Interfaces API Reference

The core interfaces module defines abstract base classes and protocols that establish the framework's architecture and ensure consistent behavior across all components.

## Abstract Base Classes

### EmpiricalValidationEngine

Base class for empirical validation components.

```python
from lbmd_sota.core.interfaces import EmpiricalValidationEngine

class EmpiricalValidationEngine(ABC):
    """Abstract base class for empirical validation components."""
    
    @abstractmethod
    def run_comprehensive_evaluation(self, datasets: List[str], models: List[str]) -> ValidationResults:
        """Run comprehensive evaluation across datasets and models."""
        pass
    
    @abstractmethod
    def validate_correlation_claims(self, correlation_threshold: float = 0.78) -> CorrelationReport:
        """Validate correlation claims with statistical significance testing."""
        pass
    
    @abstractmethod
    def perform_ablation_studies(self, parameter_ranges: Dict) -> AblationResults:
        """Perform systematic ablation studies."""
        pass
    
    @abstractmethod
    def generate_statistical_report(self) -> StatisticalSummary:
        """Generate comprehensive statistical analysis report."""
        pass
```

**Usage Example:**
```python
from lbmd_sota.empirical_validation import MultiDatasetEvaluator

evaluator = MultiDatasetEvaluator(config)
evaluator.initialize()

# Run comprehensive evaluation
results = evaluator.run_comprehensive_evaluation(
    datasets=['coco', 'cityscapes'],
    models=['maskrcnn', 'solo']
)

# Validate correlation claims
correlation_report = evaluator.validate_correlation_claims(0.78)
```

### ComparativeAnalysisSystem

Base class for comparative analysis components.

```python
class ComparativeAnalysisSystem(ABC):
    """Abstract base class for comparative analysis components."""
    
    @abstractmethod
    def compare_with_baselines(self, image_batch: torch.Tensor) -> ComparisonResults:
        """Compare LBMD insights with baseline interpretability methods."""
        pass
    
    @abstractmethod
    def analyze_failure_modes(self, failed_predictions: List) -> FailureAnalysis:
        """Analyze segmentation failure modes using LBMD insights."""
        pass
    
    @abstractmethod
    def quantify_unique_insights(self, baseline_results: Dict) -> UniquenessMetrics:
        """Quantify unique insights provided by LBMD vs baselines."""
        pass
```

**Usage Example:**
```python
from lbmd_sota.comparative_analysis import BaselineComparator

comparator = BaselineComparator(config)
comparator.initialize()

# Compare with baseline methods
comparison_results = comparator.compare_with_baselines(image_tensor)

# Analyze failure modes
failure_analysis = comparator.analyze_failure_modes(failed_predictions)
```

### ModelImprovementToolkit

Base class for model improvement components.

```python
class ModelImprovementToolkit(ABC):
    """Abstract base class for model improvement components."""
    
    @abstractmethod
    def suggest_architecture_improvements(self, lbmd_analysis: LBMDResults) -> ArchitecturalSuggestions:
        """Suggest architectural improvements based on LBMD analysis."""
        pass
    
    @abstractmethod
    def design_boundary_loss(self, boundary_metrics: BoundaryMetrics) -> torch.nn.Module:
        """Design boundary-aware loss functions."""
        pass
    
    @abstractmethod
    def create_augmentation_strategy(self, weakness_analysis: WeaknessReport) -> AugmentationPipeline:
        """Create targeted data augmentation strategies."""
        pass
```

**Usage Example:**
```python
from lbmd_sota.model_improvement import ArchitectureEnhancer

enhancer = ArchitectureEnhancer(config)
enhancer.initialize()

# Get architecture suggestions
suggestions = enhancer.suggest_architecture_improvements(lbmd_results)

# Design boundary loss
loss_module = enhancer.design_boundary_loss(boundary_metrics)
```

### VisualizationPlatform

Base class for visualization components.

```python
class VisualizationPlatform(ABC):
    """Abstract base class for visualization components."""
    
    @abstractmethod
    def create_interactive_manifold(self, manifold_data: ManifoldData) -> InteractiveVisualization:
        """Create interactive manifold visualizations."""
        pass
    
    @abstractmethod
    def generate_publication_figures(self, results: LBMDResults) -> List[Figure]:
        """Generate publication-quality figures."""
        pass
    
    @abstractmethod
    def launch_analysis_dashboard(self, config: DashboardConfig) -> Dashboard:
        """Launch real-time analysis dashboard."""
        pass
```

**Usage Example:**
```python
from lbmd_sota.visualization import InteractiveManifoldExplorer

explorer = InteractiveManifoldExplorer(config)
explorer.initialize()

# Create interactive visualization
visualization = explorer.create_interactive_manifold(manifold_data)

# Generate publication figures
figures = explorer.generate_publication_figures(lbmd_results)
```

### TheoreticalFramework

Base class for theoretical framework components.

```python
class TheoreticalFramework(ABC):
    """Abstract base class for theoretical framework components."""
    
    @abstractmethod
    def formalize_boundary_manifolds(self) -> MathematicalDefinition:
        """Provide rigorous mathematical definitions."""
        pass
    
    @abstractmethod
    def compute_topological_properties(self, manifold: Manifold) -> TopologicalProperties:
        """Compute topological properties of boundary manifolds."""
        pass
    
    @abstractmethod
    def analyze_cognitive_alignment(self, neural_boundaries: BoundaryData, 
                                  human_data: HumanPerceptionData) -> AlignmentMetrics:
        """Analyze alignment with human perception."""
        pass
```

**Usage Example:**
```python
from lbmd_sota.theoretical_framework import TopologicalAnalyzer

analyzer = TopologicalAnalyzer(config)
analyzer.initialize()

# Compute topological properties
properties = analyzer.compute_topological_properties(manifold)

# Analyze cognitive alignment
alignment = analyzer.analyze_cognitive_alignment(neural_boundaries, human_data)
```

## Protocol Classes

### Configurable

Protocol for components that accept configuration.

```python
from typing import Protocol

class Configurable(Protocol):
    """Protocol for configurable components."""
    
    def initialize(self, config: Optional[Dict] = None) -> None:
        """Initialize component with configuration."""
        ...
    
    def get_config(self) -> Dict:
        """Get current configuration."""
        ...
    
    def update_config(self, config: Dict) -> None:
        """Update configuration."""
        ...
```

### Cacheable

Protocol for components that support result caching.

```python
class Cacheable(Protocol):
    """Protocol for components that support caching."""
    
    def enable_caching(self, cache_dir: str) -> None:
        """Enable result caching."""
        ...
    
    def clear_cache(self) -> None:
        """Clear cached results."""
        ...
    
    def get_cache_info(self) -> CacheInfo:
        """Get cache statistics."""
        ...
```

### Serializable

Protocol for components that can be serialized.

```python
class Serializable(Protocol):
    """Protocol for serializable components."""
    
    def save(self, filepath: str) -> None:
        """Save component state to file."""
        ...
    
    def load(self, filepath: str) -> None:
        """Load component state from file."""
        ...
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        ...
```

## Exception Classes

### Base Exception

```python
class LBMDError(Exception):
    """Base exception for LBMD-related errors."""
    
    def __init__(self, message: str, component: Optional[str] = None, 
                 details: Optional[Dict] = None):
        super().__init__(message)
        self.component = component
        self.details = details or {}
        self.timestamp = datetime.now()
```

### Specific Exceptions

```python
class DatasetError(LBMDError):
    """Raised when dataset loading or processing fails."""
    pass

class ModelArchitectureError(LBMDError):
    """Raised when model architecture is not supported."""
    pass

class ManifoldConstructionError(LBMDError):
    """Raised when manifold learning fails."""
    pass

class VisualizationError(LBMDError):
    """Raised when visualization generation fails."""
    pass

class ConfigurationError(LBMDError):
    """Raised when configuration is invalid."""
    pass

class ValidationError(LBMDError):
    """Raised when validation fails."""
    pass
```

**Usage Example:**
```python
try:
    evaluator.run_comprehensive_evaluation(datasets, models)
except DatasetError as e:
    print(f"Dataset error in {e.component}: {e}")
    print(f"Details: {e.details}")
except ModelArchitectureError as e:
    print(f"Model architecture error: {e}")
except LBMDError as e:
    print(f"General LBMD error: {e}")
```

## Utility Functions

### Component Registration

```python
def register_component(component_type: str, component_class: type) -> None:
    """Register a component class for dynamic loading."""
    pass

def get_component(component_type: str, component_name: str) -> type:
    """Get a registered component class."""
    pass

def list_components(component_type: str) -> List[str]:
    """List available components of a given type."""
    pass
```

### Validation Utilities

```python
def validate_config(config: Dict, schema: Dict) -> bool:
    """Validate configuration against schema."""
    pass

def validate_data_format(data: Any, expected_type: type) -> bool:
    """Validate data format and type."""
    pass

def validate_requirements(requirements: List[str]) -> bool:
    """Validate that all requirements are satisfied."""
    pass
```

## Best Practices

### Implementation Guidelines

1. **Inherit from appropriate base classes**: All components should inherit from the relevant abstract base class
2. **Implement all abstract methods**: Ensure complete implementation of the interface contract
3. **Use type hints**: Provide comprehensive type annotations for all methods
4. **Handle errors gracefully**: Raise appropriate exception types with detailed messages
5. **Support configuration**: Accept and validate configuration parameters
6. **Enable logging**: Use the framework's logging system for debugging and monitoring

### Error Handling

1. **Specific exceptions**: Raise specific exception types rather than generic exceptions
2. **Detailed messages**: Provide clear, actionable error messages
3. **Context information**: Include component name and relevant details in exceptions
4. **Graceful degradation**: When possible, provide fallback behavior rather than failing completely

### Performance Considerations

1. **Lazy initialization**: Initialize expensive resources only when needed
2. **Memory management**: Clean up resources and intermediate results
3. **Caching support**: Implement caching for expensive operations
4. **Progress tracking**: Provide progress information for long-running operations

## See Also

- [Data Models API](data_models.md) - Core data structures and models
- [Configuration API](config.md) - Configuration management system
- [Examples](../../examples/) - Working examples using the interfaces
- [Tutorials](../../tutorials/) - Step-by-step implementation guides
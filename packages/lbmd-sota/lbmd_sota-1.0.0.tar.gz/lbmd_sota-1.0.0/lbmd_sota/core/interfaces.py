"""
Base interfaces and abstract classes for LBMD SOTA framework extensibility.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Union
import torch
import numpy as np
from dataclasses import dataclass


class DatasetInterface(ABC):
    """Abstract interface for dataset loading and processing."""
    
    @abstractmethod
    def load_data(self, split: str = "train") -> Dict[str, Any]:
        """Load dataset split with standardized format."""
        pass
    
    @abstractmethod
    def get_sample(self, index: int) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """Get a single sample with image and annotations."""
        pass
    
    @abstractmethod
    def validate_format(self) -> bool:
        """Validate dataset format compatibility."""
        pass


class ModelInterface(ABC):
    """Abstract interface for model loading and feature extraction."""
    
    @abstractmethod
    def load_model(self, checkpoint_path: str) -> torch.nn.Module:
        """Load model from checkpoint."""
        pass
    
    @abstractmethod
    def extract_features(self, input_tensor: torch.Tensor, layer_names: List[str]) -> Dict[str, torch.Tensor]:
        """Extract features from specified layers."""
        pass
    
    @abstractmethod
    def get_layer_names(self) -> List[str]:
        """Get available layer names for feature extraction."""
        pass


class BoundaryDetectorInterface(ABC):
    """Abstract interface for boundary detection algorithms."""
    
    @abstractmethod
    def detect_boundaries(self, features: torch.Tensor, **kwargs) -> np.ndarray:
        """Detect boundaries in feature space."""
        pass
    
    @abstractmethod
    def compute_boundary_scores(self, features: torch.Tensor) -> np.ndarray:
        """Compute boundary strength scores."""
        pass


class ManifoldLearnerInterface(ABC):
    """Abstract interface for manifold learning methods."""
    
    @abstractmethod
    def fit_transform(self, features: torch.Tensor) -> np.ndarray:
        """Fit manifold learner and transform features."""
        pass
    
    @abstractmethod
    def transform(self, features: torch.Tensor) -> np.ndarray:
        """Transform features using fitted manifold learner."""
        pass


class ClusteringAlgorithmInterface(ABC):
    """Abstract interface for clustering algorithms."""
    
    @abstractmethod
    def fit_predict(self, features: Union[torch.Tensor, np.ndarray]) -> np.ndarray:
        """Fit clustering algorithm and predict cluster labels."""
        pass
    
    @abstractmethod
    def predict(self, features: Union[torch.Tensor, np.ndarray]) -> np.ndarray:
        """Predict cluster labels for new features."""
        pass


class StatisticalAnalyzerInterface(ABC):
    """Abstract interface for statistical analysis methods."""
    
    @abstractmethod
    def compute_correlation(self, x: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Compute correlation with confidence intervals."""
        pass
    
    @abstractmethod
    def test_significance(self, data: np.ndarray, alpha: float = 0.05) -> Dict[str, Any]:
        """Perform statistical significance testing."""
        pass


class VisualizationInterface(ABC):
    """Abstract interface for visualization components."""
    
    @abstractmethod
    def create_figure(self, data: Any, **kwargs) -> Any:
        """Create visualization figure."""
        pass
    
    @abstractmethod
    def save_figure(self, figure: Any, filepath: str, **kwargs) -> None:
        """Save figure to file."""
        pass


class ExperimentInterface(ABC):
    """Abstract interface for experiment execution."""
    
    @abstractmethod
    def setup_experiment(self, config: Dict[str, Any]) -> None:
        """Setup experiment with configuration."""
        pass
    
    @abstractmethod
    def run_experiment(self) -> Dict[str, Any]:
        """Execute experiment and return results."""
        pass
    
    @abstractmethod
    def cleanup_experiment(self) -> None:
        """Cleanup experiment resources."""
        pass


# Base classes for common functionality

class BaseComponent(ABC):
    """Base class for all LBMD components."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize component."""
        pass
    
    def is_initialized(self) -> bool:
        """Check if component is initialized."""
        return self._initialized


class BaseEvaluator(BaseComponent):
    """Base class for evaluation components."""
    
    @abstractmethod
    def evaluate(self, data: Any) -> Dict[str, Any]:
        """Evaluate data and return metrics."""
        pass


class BaseAnalyzer(BaseComponent):
    """Base class for analysis components."""
    
    @abstractmethod
    def analyze(self, data: Any) -> Dict[str, Any]:
        """Analyze data and return insights."""
        pass


class BaseVisualizer(BaseComponent):
    """Base class for visualization components."""
    
    @abstractmethod
    def visualize(self, data: Any, **kwargs) -> Any:
        """Create visualization from data."""
        pass
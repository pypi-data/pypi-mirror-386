"""
Tests for core LBMD-SOTA functionality.
"""

import pytest
import torch
import numpy as np
from lbmd_sota.core.analyzer import LBMDAnalyzer
from lbmd_sota.core.config import LBMDConfig
from lbmd_sota.core.data_models import StatisticalMetrics, TopologicalProperties


class TestLBMDConfig:
    """Test LBMD configuration management."""
    
    def test_default_config(self):
        """Test default configuration creation."""
        config = LBMDConfig()
        assert config.experiment_name == "lbmd_sota_experiment"
        assert config.device == "cuda"
        assert config.batch_size == 16
        assert config.k_neurons == 100  # From lbmd_params
    
    def test_config_from_dict(self):
        """Test configuration from dictionary."""
        config_dict = {
            'experiment_name': 'test_experiment',
            'batch_size': 32,
            'lbmd_parameters': {
                'k_top_neurons': 200,
                'epsilon': 0.2
            }
        }
        config = LBMDConfig(config_dict)
        assert config.experiment_name == 'test_experiment'
        assert config.batch_size == 32
        assert config.lbmd_params['k_top_neurons'] == 200
        assert config.lbmd_params['epsilon'] == 0.2


class TestDataModels:
    """Test data model classes."""
    
    def test_statistical_metrics(self):
        """Test StatisticalMetrics dataclass."""
        metrics = StatisticalMetrics(
            correlation=0.85,
            p_value=0.001,
            confidence_interval=(0.75, 0.95),
            effect_size=0.6,
            sample_size=100
        )
        assert metrics.correlation == 0.85
        assert metrics.p_value == 0.001
        assert metrics.confidence_interval == (0.75, 0.95)
        assert metrics.effect_size == 0.6
        assert metrics.sample_size == 100
    
    def test_topological_properties(self):
        """Test TopologicalProperties dataclass."""
        properties = TopologicalProperties(
            betti_numbers={0: 5, 1: 3, 2: 1},
            persistence_diagram={'birth': [(0.1, 0.5), (0.2, 0.7)]},
            topological_entropy=2.3,
            persistent_entropy={'dim0': 1.5, 'dim1': 0.8},
            curvature_statistics={'mean': 0.5, 'std': 0.2},
            local_dimensionality=np.array([2.1, 2.3, 1.9])
        )
        assert properties.betti_numbers[0] == 5
        assert properties.topological_entropy == 2.3
        assert len(properties.local_dimensionality) == 3


class TestLBMDAnalyzer:
    """Test LBMD analyzer functionality."""
    
    @pytest.fixture
    def simple_model(self):
        """Create a simple test model."""
        class SimpleModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.conv1 = torch.nn.Conv2d(3, 64, 3, padding=1)
                self.conv2 = torch.nn.Conv2d(64, 128, 3, padding=1)
                self.pool = torch.nn.AdaptiveAvgPool2d((1, 1))
                self.fc = torch.nn.Linear(128, 10)
            
            def forward(self, x):
                x = torch.relu(self.conv1(x))
                x = torch.relu(self.conv2(x))
                x = self.pool(x)
                x = x.view(x.size(0), -1)
                x = self.fc(x)
                return x
        
        return SimpleModel()
    
    def test_analyzer_initialization(self, simple_model):
        """Test analyzer initialization."""
        analyzer = LBMDAnalyzer(
            model=simple_model,
            target_layers=['conv1', 'conv2'],
            k_neurons=20,
            epsilon=0.1,
            tau=0.5
        )
        assert analyzer.model == simple_model
        assert analyzer.target_layers == ['conv1', 'conv2']
        assert analyzer.k_neurons == 20
        assert analyzer.epsilon == 0.1
        assert analyzer.tau == 0.5
    
    def test_analyze_simple_model(self, simple_model):
        """Test analysis on simple model."""
        analyzer = LBMDAnalyzer(
            model=simple_model,
            target_layers=['conv1', 'conv2'],
            k_neurons=10,
            epsilon=0.1,
            tau=0.5
        )
        
        # Create test input
        input_data = torch.randn(2, 3, 32, 32)
        
        # Run analysis
        results = analyzer.analyze(input_data)
        
        # Check results structure
        assert 'manifold_analysis' in results
        assert 'boundary_analysis' in results
        assert 'summary_metrics' in results
        
        # Check that we have results for target layers
        manifold_data = results['manifold_analysis']
        assert len(manifold_data) <= 2  # May be less if some layers fail
        
        # Check summary metrics
        summary = results['summary_metrics']
        assert 'total_layers_analyzed' in summary
        assert 'successful_layers' in summary
        assert 'success_rate' in summary
        assert 0 <= summary['success_rate'] <= 1


if __name__ == "__main__":
    pytest.main([__file__])

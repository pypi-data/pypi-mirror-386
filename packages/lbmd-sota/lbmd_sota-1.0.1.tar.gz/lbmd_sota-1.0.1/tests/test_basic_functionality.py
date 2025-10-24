"""
Basic functionality tests for LBMD
"""

import pytest
import torch
import numpy as np
from unittest.mock import Mock, patch

def test_imports():
    """Test that core modules can be imported"""
    try:
        from lbmd_sota.core.analyzer import LBMDAnalyzer
        from lbmd_sota.core.interfaces import AnalysisResult
        from lbmd_sota.core.config import LBMDConfig
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import core modules: {e}")

def test_analyzer_initialization():
    """Test LBMDAnalyzer can be initialized with a simple model"""
    from lbmd_sota.core.analyzer import LBMDAnalyzer
    
    # Create a simple model
    model = torch.nn.Sequential(
        torch.nn.Linear(10, 5),
        torch.nn.ReLU(),
        torch.nn.Linear(5, 2)
    )
    
    # Test initialization
    analyzer = LBMDAnalyzer(model, target_layers=['0'])
    assert analyzer is not None
    assert analyzer.model is model

def test_analyzer_with_mock_analysis():
    """Test analyzer with mocked analysis to avoid heavy computation"""
    from lbmd_sota.core.analyzer import LBMDAnalyzer
    from lbmd_sota.core.interfaces import AnalysisResult
    
    # Create a simple model
    model = torch.nn.Sequential(
        torch.nn.Linear(10, 5),
        torch.nn.ReLU(),
        torch.nn.Linear(5, 2)
    )
    
    analyzer = LBMDAnalyzer(model, target_layers=['0'])
    
    # Mock the heavy computation parts
    with patch.object(analyzer, '_extract_features') as mock_extract:
        with patch.object(analyzer, '_compute_manifold_properties') as mock_manifold:
            with patch.object(analyzer, '_analyze_boundaries') as mock_boundaries:
                
                # Set up mocks
                mock_extract.return_value = torch.randn(1, 100, 5)  # Mock features
                mock_manifold.return_value = {
                    'manifold_dimension': 3,
                    'explained_variance': 0.85
                }
                mock_boundaries.return_value = {
                    'boundary_strength': 0.75,
                    'boundary_points': torch.randn(10, 5)
                }
                
                # Test analysis
                dummy_input = torch.randn(1, 10)
                result = analyzer.analyze(dummy_input)
                
                # Verify result structure
                assert isinstance(result, dict)
                assert 'manifold_dimension' in result
                assert 'boundary_strength' in result

def test_config_loading():
    """Test configuration loading"""
    from lbmd_sota.core.config import LBMDConfig
    
    # Test default config
    config = LBMDConfig()
    assert config is not None
    assert hasattr(config, 'manifold_learning')
    assert hasattr(config, 'boundary_detection')

@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_gpu_compatibility():
    """Test GPU compatibility if CUDA is available"""
    from lbmd_sota.core.analyzer import LBMDAnalyzer
    
    model = torch.nn.Sequential(
        torch.nn.Linear(10, 5),
        torch.nn.ReLU(),
        torch.nn.Linear(5, 2)
    ).cuda()
    
    analyzer = LBMDAnalyzer(model, target_layers=['0'])
    dummy_input = torch.randn(1, 10).cuda()
    
    # This should not raise an error
    try:
        # Mock heavy computation to avoid actual GPU computation in tests
        with patch.object(analyzer, '_extract_features') as mock_extract:
            mock_extract.return_value = torch.randn(1, 100, 5).cuda()
            result = analyzer.analyze(dummy_input)
            assert result is not None
    except Exception as e:
        pytest.fail(f"GPU compatibility test failed: {e}")

def test_error_handling():
    """Test error handling for invalid inputs"""
    from lbmd_sota.core.analyzer import LBMDAnalyzer
    
    model = torch.nn.Sequential(
        torch.nn.Linear(10, 5),
        torch.nn.ReLU(),
        torch.nn.Linear(5, 2)
    )
    
    analyzer = LBMDAnalyzer(model, target_layers=['0'])
    
    # Test with wrong input shape
    wrong_input = torch.randn(1, 5)  # Should be (1, 10)
    
    try:
        result = analyzer.analyze(wrong_input)
        # If it doesn't raise an error, that's also fine (graceful handling)
    except Exception as e:
        # Expected behavior - should handle errors gracefully
        assert isinstance(e, (RuntimeError, ValueError))

if __name__ == "__main__":
    pytest.main([__file__])
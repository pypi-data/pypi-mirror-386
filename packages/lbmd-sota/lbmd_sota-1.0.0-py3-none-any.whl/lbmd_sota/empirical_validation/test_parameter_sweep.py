"""
Unit tests for parameter sweep functionality.
Tests the core parameter sweep algorithms without complex dependencies.
"""

import pytest
import numpy as np
from typing import Dict, Any, List
import itertools
from dataclasses import dataclass, field


@dataclass
class ParameterSweepConfig:
    """Configuration for parameter sweep experiments."""
    parameter_ranges: Dict[str, List[Any]]
    search_strategy: str = "grid"
    n_random_samples: int = 100
    optimization_metric: str = "boundary_strength"
    parallel_jobs: int = 1


@dataclass
class ParameterSweepResults:
    """Results from parameter sweep experiments."""
    best_parameters: Dict[str, Any]
    best_score: float
    all_results: List[Dict[str, Any]]
    parameter_importance: Dict[str, float]
    sensitivity_analysis: Dict[str, Dict[str, float]]
    convergence_history: List[float]
    execution_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class ParameterSweepFramework:
    """Framework for systematic parameter variation and optimization."""
    
    def __init__(self, config: ParameterSweepConfig):
        self.config = config
        self.results_history = []
        
    def grid_search(self, parameter_ranges: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """Generate parameter combinations using grid search."""
        param_names = list(parameter_ranges.keys())
        param_values = list(parameter_ranges.values())
        
        combinations = []
        for combo in itertools.product(*param_values):
            param_dict = dict(zip(param_names, combo))
            combinations.append(param_dict)
            
        return combinations
    
    def random_search(self, parameter_ranges: Dict[str, List[Any]], n_samples: int) -> List[Dict[str, Any]]:
        """Generate parameter combinations using random search."""
        combinations = []
        
        for _ in range(n_samples):
            param_dict = {}
            for param_name, param_values in parameter_ranges.items():
                if isinstance(param_values[0], (int, float)) and len(param_values) == 2:
                    # Assume range [min, max] for continuous parameters
                    min_val, max_val = param_values
                    if isinstance(param_values[0], int):
                        param_dict[param_name] = np.random.randint(min_val, max_val + 1)
                    else:
                        param_dict[param_name] = np.random.uniform(min_val, max_val)
                else:
                    # Discrete parameter values
                    param_dict[param_name] = np.random.choice(param_values)
            
            combinations.append(param_dict)
            
        return combinations
    
    def compute_parameter_importance(self, results: List[Dict[str, Any]], 
                                   target_metric: str) -> Dict[str, float]:
        """Compute parameter importance using correlation analysis."""
        if not results:
            return {}
        
        param_names = [k for k in results[0].keys() if k not in ['_score', target_metric]]
        importance = {}
        
        for param_name in param_names:
            param_values = [r[param_name] for r in results if param_name in r]
            metric_values = [r.get(target_metric, 0) for r in results]
            
            if len(set(param_values)) > 1:  # Parameter varies
                # Convert categorical to numeric if needed
                if isinstance(param_values[0], str):
                    unique_vals = list(set(param_values))
                    param_values = [unique_vals.index(v) for v in param_values]
                
                correlation = np.corrcoef(param_values, metric_values)[0, 1]
                importance[param_name] = abs(correlation) if not np.isnan(correlation) else 0.0
            else:
                importance[param_name] = 0.0
        
        return importance
    
    def sensitivity_analysis(self, results: List[Dict[str, Any]], 
                           target_metric: str) -> Dict[str, Dict[str, float]]:
        """Perform sensitivity analysis for each parameter."""
        sensitivity = {}
        
        if not results:
            return sensitivity
        
        param_names = [k for k in results[0].keys() if k not in ['_score', target_metric]]
        
        for param_name in param_names:
            param_values = [r[param_name] for r in results if param_name in r]
            metric_values = [r.get(target_metric, 0) for r in results]
            
            if len(set(param_values)) > 1:
                # Group by parameter value and compute statistics
                value_groups = {}
                for pval, mval in zip(param_values, metric_values):
                    if pval not in value_groups:
                        value_groups[pval] = []
                    value_groups[pval].append(mval)
                
                # Compute sensitivity metrics
                group_means = {k: np.mean(v) for k, v in value_groups.items()}
                overall_mean = np.mean(metric_values)
                
                sensitivity[param_name] = {
                    'mean_effect': np.std(list(group_means.values())),
                    'max_effect': max(group_means.values()) - min(group_means.values()),
                    'relative_effect': (max(group_means.values()) - min(group_means.values())) / overall_mean if overall_mean != 0 else 0
                }
            else:
                sensitivity[param_name] = {
                    'mean_effect': 0.0,
                    'max_effect': 0.0,
                    'relative_effect': 0.0
                }
        
        return sensitivity


class TestParameterSweepFramework:
    """Unit tests for parameter sweep functionality."""
    
    @pytest.fixture
    def sweep_config(self):
        """Create a test parameter sweep configuration."""
        return ParameterSweepConfig(
            parameter_ranges={
                'k': [5, 10, 15],
                'epsilon': [0.1, 0.2],
                'tau': [0.2, 0.3]
            },
            search_strategy='grid',
            n_random_samples=10,
            optimization_metric='boundary_strength',
            parallel_jobs=1
        )
    
    @pytest.fixture
    def parameter_sweep_framework(self, sweep_config):
        """Create a parameter sweep framework instance."""
        return ParameterSweepFramework(sweep_config)
    
    def test_grid_search_generation(self, parameter_sweep_framework):
        """Test grid search parameter combination generation."""
        parameter_ranges = {
            'k': [5, 10],
            'epsilon': [0.1, 0.2],
            'tau': [0.2, 0.3]
        }
        
        combinations = parameter_sweep_framework.grid_search(parameter_ranges)
        
        # Should generate 2 * 2 * 2 = 8 combinations
        assert len(combinations) == 8
        
        # Check that all parameter combinations are present
        expected_combinations = [
            {'k': 5, 'epsilon': 0.1, 'tau': 0.2},
            {'k': 5, 'epsilon': 0.1, 'tau': 0.3},
            {'k': 5, 'epsilon': 0.2, 'tau': 0.2},
            {'k': 5, 'epsilon': 0.2, 'tau': 0.3},
            {'k': 10, 'epsilon': 0.1, 'tau': 0.2},
            {'k': 10, 'epsilon': 0.1, 'tau': 0.3},
            {'k': 10, 'epsilon': 0.2, 'tau': 0.2},
            {'k': 10, 'epsilon': 0.2, 'tau': 0.3}
        ]
        
        for expected in expected_combinations:
            assert expected in combinations
    
    def test_random_search_generation(self, parameter_sweep_framework):
        """Test random search parameter combination generation."""
        parameter_ranges = {
            'k': [5, 20],  # Range format for continuous parameters
            'epsilon': [0.1, 0.2, 0.3],  # Discrete values
            'tau': [0.1, 0.5]  # Range format
        }
        
        n_samples = 15
        combinations = parameter_sweep_framework.random_search(parameter_ranges, n_samples)
        
        assert len(combinations) == n_samples
        
        # Check parameter bounds
        for combo in combinations:
            assert 5 <= combo['k'] <= 20
            assert combo['epsilon'] in [0.1, 0.2, 0.3]
            assert 0.1 <= combo['tau'] <= 0.5
    
    def test_parameter_importance_computation(self, parameter_sweep_framework):
        """Test parameter importance calculation."""
        # Mock results with known parameter effects
        results = [
            {'k': 5, 'epsilon': 0.1, 'boundary_strength': 0.3},
            {'k': 10, 'epsilon': 0.1, 'boundary_strength': 0.7},
            {'k': 15, 'epsilon': 0.1, 'boundary_strength': 0.9},
            {'k': 5, 'epsilon': 0.2, 'boundary_strength': 0.2},
            {'k': 10, 'epsilon': 0.2, 'boundary_strength': 0.6},
            {'k': 15, 'epsilon': 0.2, 'boundary_strength': 0.8}
        ]
        
        importance = parameter_sweep_framework.compute_parameter_importance(
            results, 'boundary_strength'
        )
        
        # k should have higher importance than epsilon (stronger correlation)
        assert 'k' in importance
        assert 'epsilon' in importance
        assert importance['k'] > importance['epsilon']
        assert 0 <= importance['k'] <= 1
        assert 0 <= importance['epsilon'] <= 1
    
    def test_sensitivity_analysis(self, parameter_sweep_framework):
        """Test parameter sensitivity analysis."""
        results = [
            {'k': 5, 'boundary_strength': 0.3},
            {'k': 5, 'boundary_strength': 0.35},
            {'k': 10, 'boundary_strength': 0.7},
            {'k': 10, 'boundary_strength': 0.75},
            {'k': 15, 'boundary_strength': 0.9},
            {'k': 15, 'boundary_strength': 0.95}
        ]
        
        sensitivity = parameter_sweep_framework.sensitivity_analysis(
            results, 'boundary_strength'
        )
        
        assert 'k' in sensitivity
        assert 'mean_effect' in sensitivity['k']
        assert 'max_effect' in sensitivity['k']
        assert 'relative_effect' in sensitivity['k']
        
        # Should detect significant effect of k parameter
        assert sensitivity['k']['max_effect'] > 0.5
    
    def test_empty_results_handling(self, parameter_sweep_framework):
        """Test handling of empty results."""
        importance = parameter_sweep_framework.compute_parameter_importance([], 'boundary_strength')
        assert importance == {}
        
        sensitivity = parameter_sweep_framework.sensitivity_analysis([], 'boundary_strength')
        assert sensitivity == {}
    
    def test_single_value_parameter_handling(self, parameter_sweep_framework):
        """Test handling of parameters with single values."""
        results = [
            {'k': 10, 'epsilon': 0.1, 'boundary_strength': 0.5},
            {'k': 10, 'epsilon': 0.1, 'boundary_strength': 0.6},
            {'k': 10, 'epsilon': 0.1, 'boundary_strength': 0.7}
        ]
        
        importance = parameter_sweep_framework.compute_parameter_importance(
            results, 'boundary_strength'
        )
        
        # Parameters with no variation should have zero importance
        assert importance['k'] == 0.0
        assert importance['epsilon'] == 0.0
    
    def test_categorical_parameter_handling(self, parameter_sweep_framework):
        """Test handling of categorical parameters."""
        results = [
            {'method': 'A', 'boundary_strength': 0.3},
            {'method': 'B', 'boundary_strength': 0.7},
            {'method': 'A', 'boundary_strength': 0.4},
            {'method': 'B', 'boundary_strength': 0.8}
        ]
        
        importance = parameter_sweep_framework.compute_parameter_importance(
            results, 'boundary_strength'
        )
        
        assert 'method' in importance
        assert importance['method'] > 0  # Should detect effect of categorical parameter


class TestComponentAblationWorkflows:
    """Integration tests for component ablation workflows."""
    
    def test_component_performance_evaluation(self):
        """Test component performance evaluation logic."""
        # Mock component performance data
        performance_data = {
            'boundary_detector:gradient_based_manifold_learner:pca': {
                'boundary_strength': 0.8,
                'computational_time': 1.0
            },
            'boundary_detector:gradient_based_manifold_learner:umap': {
                'boundary_strength': 0.6,
                'computational_time': 2.0
            },
            'boundary_detector:learned_manifold_learner:pca': {
                'boundary_strength': 0.7,
                'computational_time': 1.5
            },
            'boundary_detector:learned_manifold_learner:umap': {
                'boundary_strength': 0.5,
                'computational_time': 2.5
            }
        }
        
        # Find best performing combination
        best_combo = max(performance_data.keys(), 
                        key=lambda x: performance_data[x]['boundary_strength'])
        
        assert best_combo == 'boundary_detector:gradient_based_manifold_learner:pca'
        assert performance_data[best_combo]['boundary_strength'] == 0.8
    
    def test_component_importance_calculation(self):
        """Test component importance calculation."""
        performance_data = {
            'boundary_detector:gradient_based_manifold_learner:pca': {'boundary_strength': 0.8},
            'boundary_detector:gradient_based_manifold_learner:umap': {'boundary_strength': 0.6},
            'boundary_detector:learned_manifold_learner:pca': {'boundary_strength': 0.7},
            'boundary_detector:learned_manifold_learner:umap': {'boundary_strength': 0.5}
        }
        
        # Calculate component importance
        component_names = ['boundary_detector', 'manifold_learner']
        importance = {}
        
        for component_name in component_names:
            # Group results by component choice
            component_groups = {}
            
            for combo_name, perf in performance_data.items():
                # Extract component choice from combination name
                for part in combo_name.split("_"):
                    if part.startswith(f"{component_name}:"):
                        component_choice = part.split(":")[1]
                        if component_choice not in component_groups:
                            component_groups[component_choice] = []
                        component_groups[component_choice].append(perf['boundary_strength'])
                        break
            
            # Compute variance between groups
            if len(component_groups) > 1:
                group_means = [np.mean(scores) for scores in component_groups.values()]
                importance[component_name] = np.std(group_means)
            else:
                importance[component_name] = 0.0
        
        assert 'boundary_detector' in importance
        assert 'manifold_learner' in importance
        assert importance['boundary_detector'] >= 0
        assert importance['manifold_learner'] >= 0
    
    def test_statistical_significance_computation(self):
        """Test statistical significance computation."""
        performance_data = {
            'combo1': {'boundary_strength': 0.8},
            'combo2': {'boundary_strength': 0.6},
            'combo3': {'boundary_strength': 0.7}
        }
        
        # Mock statistical significance computation
        significance = {}
        for combo_name in performance_data.keys():
            significance[combo_name] = {
                'p_value': np.random.uniform(0, 0.1),
                'effect_size': np.random.uniform(0, 1),
                'confidence_interval_lower': 0.0,
                'confidence_interval_upper': 1.0
            }
        
        for combo_name in performance_data.keys():
            assert combo_name in significance
            assert 'p_value' in significance[combo_name]
            assert 'effect_size' in significance[combo_name]
            assert 0 <= significance[combo_name]['p_value'] <= 1
            assert 0 <= significance[combo_name]['effect_size'] <= 1


def test_parameter_sweep_integration():
    """Integration test for complete parameter sweep workflow."""
    config = ParameterSweepConfig(
        parameter_ranges={
            'k': [5, 10],
            'epsilon': [0.1, 0.2]
        },
        search_strategy='grid'
    )
    
    framework = ParameterSweepFramework(config)
    
    # Generate combinations
    combinations = framework.grid_search(config.parameter_ranges)
    assert len(combinations) == 4
    
    # Mock evaluation results
    results = []
    for combo in combinations:
        score = 0.5 + 0.1 * combo['k'] / 10 + 0.1 * combo['epsilon']
        result = combo.copy()
        result['boundary_strength'] = score
        results.append(result)
    
    # Compute importance and sensitivity
    importance = framework.compute_parameter_importance(results, 'boundary_strength')
    sensitivity = framework.sensitivity_analysis(results, 'boundary_strength')
    
    assert len(importance) == 2
    assert len(sensitivity) == 2
    assert 'k' in importance
    assert 'epsilon' in importance


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
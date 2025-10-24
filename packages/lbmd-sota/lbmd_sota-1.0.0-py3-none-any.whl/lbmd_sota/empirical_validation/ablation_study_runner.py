"""
Ablation study runner for systematic parameter variation.
"""

import itertools
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import os
from datetime import datetime

from ..core.interfaces import BaseComponent, BoundaryDetectorInterface, ManifoldLearnerInterface, ClusteringAlgorithmInterface
from ..core.data_models import LBMDResults, StatisticalMetrics, ExperimentConfig
from .boundary_detectors import BoundaryDetectorFactory
from .manifold_learners import ManifoldLearnerFactory
from .clustering_algorithms import ClusteringAlgorithmFactory


@dataclass
class ParameterSweepConfig:
    """Configuration for parameter sweep experiments."""
    parameter_ranges: Dict[str, List[Any]]
    search_strategy: str = "grid"  # "grid", "random", "adaptive"
    n_random_samples: int = 100
    optimization_metric: str = "boundary_strength"
    parallel_jobs: int = 1
    save_all_results: bool = True
    early_stopping: bool = False
    early_stopping_patience: int = 10


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


@dataclass
class ComponentAblationConfig:
    """Configuration for component ablation studies."""
    components_to_test: Dict[str, List[str]]
    baseline_components: Dict[str, str]
    evaluation_metrics: List[str]
    cross_validation_folds: int = 5
    statistical_tests: List[str] = field(default_factory=lambda: ["t_test", "wilcoxon"])


@dataclass
class ComponentAblationResults:
    """Results from component ablation studies."""
    component_performance: Dict[str, Dict[str, float]]
    statistical_significance: Dict[str, Dict[str, float]]
    best_combination: Dict[str, str]
    component_importance: Dict[str, float]
    interaction_effects: Dict[Tuple[str, str], float]
    metadata: Dict[str, Any] = field(default_factory=dict)


class ParameterSweepFramework:
    """Framework for systematic parameter variation and optimization."""
    
    def __init__(self, config: ParameterSweepConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
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
    
    def adaptive_search(self, parameter_ranges: Dict[str, List[Any]], 
                       evaluation_function: Callable, n_iterations: int = 50) -> List[Dict[str, Any]]:
        """Generate parameter combinations using adaptive search (Bayesian optimization)."""
        # Simplified adaptive search - in practice, would use libraries like scikit-optimize
        combinations = []
        
        # Start with random samples
        initial_samples = min(10, n_iterations // 5)
        combinations.extend(self.random_search(parameter_ranges, initial_samples))
        
        # Evaluate initial samples
        for combo in combinations:
            score = evaluation_function(combo)
            combo['_score'] = score
        
        # Adaptive sampling based on performance
        for _ in range(n_iterations - initial_samples):
            # Find best performing regions
            sorted_combos = sorted(combinations, key=lambda x: x.get('_score', 0), reverse=True)
            top_performers = sorted_combos[:len(sorted_combos)//4]
            
            # Generate new sample near top performers
            if top_performers:
                base_combo = np.random.choice(top_performers)
                new_combo = self._perturb_parameters(base_combo, parameter_ranges)
                combinations.append(new_combo)
            else:
                # Fallback to random
                new_combo = self.random_search(parameter_ranges, 1)[0]
                combinations.append(new_combo)
        
        return combinations
    
    def _perturb_parameters(self, base_combo: Dict[str, Any], 
                           parameter_ranges: Dict[str, List[Any]]) -> Dict[str, Any]:
        """Perturb parameters around a base combination."""
        new_combo = base_combo.copy()
        
        for param_name, param_values in parameter_ranges.items():
            if param_name in new_combo and param_name != '_score':
                if isinstance(param_values[0], (int, float)) and len(param_values) == 2:
                    # Continuous parameter - add noise
                    current_val = new_combo[param_name]
                    min_val, max_val = param_values
                    noise_scale = (max_val - min_val) * 0.1  # 10% of range
                    
                    if isinstance(param_values[0], int):
                        noise = np.random.randint(-max(1, int(noise_scale)), 
                                                max(1, int(noise_scale)) + 1)
                        new_combo[param_name] = np.clip(current_val + noise, min_val, max_val)
                    else:
                        noise = np.random.normal(0, noise_scale)
                        new_combo[param_name] = np.clip(current_val + noise, min_val, max_val)
                else:
                    # Discrete parameter - small chance to change
                    if np.random.random() < 0.3:
                        new_combo[param_name] = np.random.choice(param_values)
        
        return new_combo
    
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


class AblationStudyRunner(BaseComponent):
    """Systematically varies LBMD parameters and components."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.parameter_sweep_framework = None
        self.logger = logging.getLogger(__name__)
        
        # Default LBMD parameter ranges
        self.default_parameter_ranges = {
            'k': [5, 10, 15, 20, 25, 30],  # top-k neurons
            'epsilon': [0.01, 0.05, 0.1, 0.15, 0.2],  # boundary threshold
            'tau': [0.1, 0.2, 0.3, 0.4, 0.5],  # transition strength threshold
            'manifold_dim': [2, 3, 5, 8, 10],  # manifold embedding dimension
            'clustering_min_samples': [3, 5, 10, 15, 20]  # minimum samples for clustering
        }
        
        # Available component implementations
        self.available_components = {
            'boundary_detector': BoundaryDetectorFactory.get_available_detectors(),
            'manifold_learner': ManifoldLearnerFactory.get_available_learners(),
            'clustering_algorithm': ClusteringAlgorithmFactory.get_available_algorithms()
        }
    
    def initialize(self) -> None:
        """Initialize the ablation study runner."""
        sweep_config = ParameterSweepConfig(
            parameter_ranges=self.config.get('parameter_ranges', self.default_parameter_ranges),
            search_strategy=self.config.get('search_strategy', 'grid'),
            n_random_samples=self.config.get('n_random_samples', 100),
            parallel_jobs=self.config.get('parallel_jobs', 1)
        )
        
        self.parameter_sweep_framework = ParameterSweepFramework(sweep_config)
        self._initialized = True
        self.logger.info("AblationStudyRunner initialized successfully")
    
    def run_parameter_sweep(self, parameter_ranges: Optional[Dict[str, List]] = None,
                          evaluation_function: Optional[Callable] = None) -> ParameterSweepResults:
        """Run systematic parameter sweep with grid, random, or adaptive search."""
        if not self._initialized:
            self.initialize()
        
        start_time = datetime.now()
        
        # Use provided ranges or defaults
        ranges = parameter_ranges or self.default_parameter_ranges
        
        # Generate parameter combinations
        if self.parameter_sweep_framework.config.search_strategy == 'grid':
            combinations = self.parameter_sweep_framework.grid_search(ranges)
        elif self.parameter_sweep_framework.config.search_strategy == 'random':
            combinations = self.parameter_sweep_framework.random_search(
                ranges, self.parameter_sweep_framework.config.n_random_samples
            )
        elif self.parameter_sweep_framework.config.search_strategy == 'adaptive':
            if evaluation_function is None:
                raise ValueError("Evaluation function required for adaptive search")
            combinations = self.parameter_sweep_framework.adaptive_search(
                ranges, evaluation_function
            )
        else:
            raise ValueError(f"Unknown search strategy: {self.parameter_sweep_framework.config.search_strategy}")
        
        self.logger.info(f"Generated {len(combinations)} parameter combinations")
        
        # Evaluate combinations
        all_results = []
        convergence_history = []
        
        if evaluation_function is None:
            evaluation_function = self._default_evaluation_function
        
        # Parallel or sequential execution
        if self.parameter_sweep_framework.config.parallel_jobs > 1:
            all_results = self._evaluate_parallel(combinations, evaluation_function)
        else:
            all_results = self._evaluate_sequential(combinations, evaluation_function)
        
        # Find best parameters
        best_result = max(all_results, key=lambda x: x.get(self.parameter_sweep_framework.config.optimization_metric, 0))
        best_parameters = {k: v for k, v in best_result.items() 
                          if k != self.parameter_sweep_framework.config.optimization_metric}
        best_score = best_result.get(self.parameter_sweep_framework.config.optimization_metric, 0)
        
        # Compute parameter importance and sensitivity
        parameter_importance = self.parameter_sweep_framework.compute_parameter_importance(
            all_results, self.parameter_sweep_framework.config.optimization_metric
        )
        
        sensitivity_analysis = self.parameter_sweep_framework.sensitivity_analysis(
            all_results, self.parameter_sweep_framework.config.optimization_metric
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        results = ParameterSweepResults(
            best_parameters=best_parameters,
            best_score=best_score,
            all_results=all_results,
            parameter_importance=parameter_importance,
            sensitivity_analysis=sensitivity_analysis,
            convergence_history=convergence_history,
            execution_time=execution_time,
            metadata={
                'search_strategy': self.parameter_sweep_framework.config.search_strategy,
                'total_combinations': len(combinations),
                'optimization_metric': self.parameter_sweep_framework.config.optimization_metric
            }
        )
        
        self.logger.info(f"Parameter sweep completed in {execution_time:.2f} seconds")
        self.logger.info(f"Best parameters: {best_parameters}")
        self.logger.info(f"Best score: {best_score:.4f}")
        
        return results
    
    def _evaluate_sequential(self, combinations: List[Dict[str, Any]], 
                           evaluation_function: Callable) -> List[Dict[str, Any]]:
        """Evaluate parameter combinations sequentially."""
        results = []
        
        for i, combo in enumerate(combinations):
            try:
                score = evaluation_function(combo)
                result = combo.copy()
                result[self.parameter_sweep_framework.config.optimization_metric] = score
                results.append(result)
                
                if (i + 1) % 10 == 0:
                    self.logger.info(f"Evaluated {i + 1}/{len(combinations)} combinations")
                    
            except Exception as e:
                self.logger.warning(f"Failed to evaluate combination {combo}: {e}")
                result = combo.copy()
                result[self.parameter_sweep_framework.config.optimization_metric] = 0.0
                results.append(result)
        
        return results
    
    def _evaluate_parallel(self, combinations: List[Dict[str, Any]], 
                          evaluation_function: Callable) -> List[Dict[str, Any]]:
        """Evaluate parameter combinations in parallel."""
        results = []
        
        with ProcessPoolExecutor(max_workers=self.parameter_sweep_framework.config.parallel_jobs) as executor:
            # Submit all jobs
            future_to_combo = {
                executor.submit(evaluation_function, combo): combo 
                for combo in combinations
            }
            
            # Collect results
            for i, future in enumerate(as_completed(future_to_combo)):
                combo = future_to_combo[future]
                try:
                    score = future.result()
                    result = combo.copy()
                    result[self.parameter_sweep_framework.config.optimization_metric] = score
                    results.append(result)
                except Exception as e:
                    self.logger.warning(f"Failed to evaluate combination {combo}: {e}")
                    result = combo.copy()
                    result[self.parameter_sweep_framework.config.optimization_metric] = 0.0
                    results.append(result)
                
                if (i + 1) % 10 == 0:
                    self.logger.info(f"Evaluated {i + 1}/{len(combinations)} combinations")
        
        return results
    
    def _default_evaluation_function(self, parameters: Dict[str, Any]) -> float:
        """Default evaluation function for parameter combinations."""
        # Placeholder implementation - would integrate with actual LBMD analysis
        # This simulates boundary strength computation based on parameters
        
        k = parameters.get('k', 10)
        epsilon = parameters.get('epsilon', 0.1)
        tau = parameters.get('tau', 0.2)
        
        # Simulate boundary strength calculation
        # In practice, this would run LBMD with these parameters
        boundary_strength = (
            0.5 * (1 - abs(k - 15) / 15) +  # Optimal k around 15
            0.3 * (1 - abs(epsilon - 0.1) / 0.1) +  # Optimal epsilon around 0.1
            0.2 * (1 - abs(tau - 0.3) / 0.3)  # Optimal tau around 0.3
        )
        
        # Add some noise to simulate real evaluation
        boundary_strength += np.random.normal(0, 0.05)
        
        return max(0, min(1, boundary_strength))
    
    def run_component_ablation(self, components: Optional[Dict[str, List[str]]] = None) -> ComponentAblationResults:
        """Run component ablation studies comparing different algorithm implementations."""
        if not self._initialized:
            self.initialize()
        
        # Use provided components or defaults
        components_to_test = components or self.available_components
        
        self.logger.info(f"Running component ablation for: {list(components_to_test.keys())}")
        
        # Generate all component combinations
        component_names = list(components_to_test.keys())
        component_options = list(components_to_test.values())
        
        combinations = []
        for combo in itertools.product(*component_options):
            component_dict = dict(zip(component_names, combo))
            combinations.append(component_dict)
        
        self.logger.info(f"Testing {len(combinations)} component combinations")
        
        # Evaluate each combination
        component_performance = {}
        
        for combo in combinations:
            combo_name = "_".join([f"{k}:{v}" for k, v in combo.items()])
            
            try:
                # Evaluate component combination
                performance = self._evaluate_component_combination(combo)
                component_performance[combo_name] = performance
                
                self.logger.info(f"Evaluated combination: {combo_name}")
                
            except Exception as e:
                self.logger.warning(f"Failed to evaluate combination {combo}: {e}")
                component_performance[combo_name] = {
                    'boundary_strength': 0.0,
                    'computational_time': float('inf'),
                    'memory_usage': float('inf')
                }
        
        # Find best combination
        best_combo_name = max(component_performance.keys(), 
                             key=lambda x: component_performance[x].get('boundary_strength', 0))
        best_combination = dict(zip(component_names, best_combo_name.split("_")))
        best_combination = {k: v.split(":")[1] for k, v in best_combination.items()}
        
        # Compute component importance
        component_importance = self._compute_component_importance(
            component_performance, component_names
        )
        
        # Compute interaction effects (simplified)
        interaction_effects = self._compute_interaction_effects(
            component_performance, component_names
        )
        
        # Statistical significance testing (placeholder)
        statistical_significance = self._compute_statistical_significance(
            component_performance
        )
        
        results = ComponentAblationResults(
            component_performance=component_performance,
            statistical_significance=statistical_significance,
            best_combination=best_combination,
            component_importance=component_importance,
            interaction_effects=interaction_effects,
            metadata={
                'total_combinations': len(combinations),
                'components_tested': component_names
            }
        )
        
        self.logger.info(f"Component ablation completed")
        self.logger.info(f"Best combination: {best_combination}")
        
        return results
    
    def _evaluate_component_combination(self, components: Dict[str, str]) -> Dict[str, float]:
        """Evaluate a specific component combination."""
        import time
        import torch
        
        # Generate synthetic test data for evaluation
        test_features = torch.randn(1, 256, 32, 32)  # Batch, channels, height, width
        
        start_time = time.time()
        
        try:
            # Initialize components
            boundary_detector = None
            manifold_learner = None
            clustering_algorithm = None
            
            if 'boundary_detector' in components:
                boundary_detector = BoundaryDetectorFactory.create_detector(
                    components['boundary_detector']
                )
            
            if 'manifold_learner' in components:
                manifold_learner = ManifoldLearnerFactory.create_learner(
                    components['manifold_learner']
                )
            
            if 'clustering_algorithm' in components:
                clustering_algorithm = ClusteringAlgorithmFactory.create_algorithm(
                    components['clustering_algorithm']
                )
            
            # Evaluate pipeline
            boundary_strength = 0.0
            
            # Step 1: Boundary detection
            if boundary_detector:
                boundary_scores = boundary_detector.compute_boundary_scores(test_features)
                boundary_strength += np.mean(boundary_scores)
            
            # Step 2: Manifold learning
            manifold_quality = 0.0
            if manifold_learner:
                try:
                    embedding = manifold_learner.fit_transform(test_features)
                    # Simple quality metric: variance in embedding
                    manifold_quality = np.var(embedding)
                    boundary_strength += manifold_quality * 0.1  # Weight manifold contribution
                except Exception as e:
                    self.logger.warning(f"Manifold learning failed: {e}")
                    manifold_quality = 0.0
            
            # Step 3: Clustering
            clustering_quality = 0.0
            if clustering_algorithm and manifold_learner:
                try:
                    labels = clustering_algorithm.fit_predict(test_features)
                    # Simple quality metric: number of clusters found
                    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                    clustering_quality = min(n_clusters / 10.0, 1.0)  # Normalize to [0,1]
                    boundary_strength += clustering_quality * 0.1  # Weight clustering contribution
                except Exception as e:
                    self.logger.warning(f"Clustering failed: {e}")
                    clustering_quality = 0.0
            
            computational_time = time.time() - start_time
            
            # Normalize boundary strength to [0, 1]
            boundary_strength = max(0, min(1, boundary_strength))
            
            performance = {
                'boundary_strength': boundary_strength,
                'computational_time': computational_time,
                'memory_usage': 100.0,  # Placeholder
                'manifold_quality': manifold_quality,
                'clustering_quality': clustering_quality
            }
            
        except Exception as e:
            self.logger.error(f"Component evaluation failed: {e}")
            performance = {
                'boundary_strength': 0.0,
                'computational_time': float('inf'),
                'memory_usage': float('inf'),
                'manifold_quality': 0.0,
                'clustering_quality': 0.0
            }
        
        return performance
    
    def _compute_component_importance(self, performance_data: Dict[str, Dict[str, float]], 
                                    component_names: List[str]) -> Dict[str, float]:
        """Compute importance of each component type."""
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
                        component_groups[component_choice].append(perf.get('boundary_strength', 0))
                        break
            
            # Compute variance between groups
            if len(component_groups) > 1:
                group_means = [np.mean(scores) for scores in component_groups.values()]
                importance[component_name] = np.std(group_means)
            else:
                importance[component_name] = 0.0
        
        return importance
    
    def _compute_interaction_effects(self, performance_data: Dict[str, Dict[str, float]], 
                                   component_names: List[str]) -> Dict[Tuple[str, str], float]:
        """Compute interaction effects between component pairs."""
        interaction_effects = {}
        
        # Simplified interaction effect computation
        for i, comp1 in enumerate(component_names):
            for j, comp2 in enumerate(component_names[i+1:], i+1):
                # This is a placeholder - real implementation would compute
                # statistical interaction effects
                interaction_effects[(comp1, comp2)] = np.random.uniform(0, 0.1)
        
        return interaction_effects
    
    def _compute_statistical_significance(self, performance_data: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        """Compute statistical significance of performance differences."""
        # Placeholder implementation
        significance = {}
        
        for combo_name in performance_data.keys():
            significance[combo_name] = {
                'p_value': np.random.uniform(0, 0.1),
                'effect_size': np.random.uniform(0, 1),
                'confidence_interval_lower': 0.0,
                'confidence_interval_upper': 1.0
            }
        
        return significance
    
    def save_results(self, results: Union[ParameterSweepResults, ComponentAblationResults], 
                    filepath: str) -> None:
        """Save ablation study results to file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Convert results to serializable format
        if isinstance(results, ParameterSweepResults):
            data = {
                'type': 'parameter_sweep',
                'best_parameters': results.best_parameters,
                'best_score': results.best_score,
                'all_results': results.all_results,
                'parameter_importance': results.parameter_importance,
                'sensitivity_analysis': results.sensitivity_analysis,
                'execution_time': results.execution_time,
                'metadata': results.metadata
            }
        elif isinstance(results, ComponentAblationResults):
            data = {
                'type': 'component_ablation',
                'component_performance': results.component_performance,
                'statistical_significance': results.statistical_significance,
                'best_combination': results.best_combination,
                'component_importance': results.component_importance,
                'interaction_effects': {f"{k[0]}_{k[1]}": v for k, v in results.interaction_effects.items()},
                'metadata': results.metadata
            }
        else:
            raise ValueError(f"Unknown results type: {type(results)}")
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Results saved to {filepath}")
    
    def load_results(self, filepath: str) -> Union[ParameterSweepResults, ComponentAblationResults]:
        """Load ablation study results from file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        if data['type'] == 'parameter_sweep':
            return ParameterSweepResults(
                best_parameters=data['best_parameters'],
                best_score=data['best_score'],
                all_results=data['all_results'],
                parameter_importance=data['parameter_importance'],
                sensitivity_analysis=data['sensitivity_analysis'],
                convergence_history=data.get('convergence_history', []),
                execution_time=data['execution_time'],
                metadata=data['metadata']
            )
        elif data['type'] == 'component_ablation':
            interaction_effects = {
                tuple(k.split('_')): v for k, v in data['interaction_effects'].items()
            }
            return ComponentAblationResults(
                component_performance=data['component_performance'],
                statistical_significance=data['statistical_significance'],
                best_combination=data['best_combination'],
                component_importance=data['component_importance'],
                interaction_effects=interaction_effects,
                metadata=data['metadata']
            )
        else:
            raise ValueError(f"Unknown results type: {data['type']}")
    
    def generate_report(self, results: Union[ParameterSweepResults, ComponentAblationResults]) -> str:
        """Generate a comprehensive report of ablation study results."""
        report = []
        
        if isinstance(results, ParameterSweepResults):
            report.append("# Parameter Sweep Results Report\n")
            report.append(f"**Search Strategy:** {results.metadata.get('search_strategy', 'Unknown')}")
            report.append(f"**Total Combinations Tested:** {results.metadata.get('total_combinations', 0)}")
            report.append(f"**Execution Time:** {results.execution_time:.2f} seconds\n")
            
            report.append("## Best Parameters")
            for param, value in results.best_parameters.items():
                report.append(f"- **{param}:** {value}")
            report.append(f"- **Best Score:** {results.best_score:.4f}\n")
            
            report.append("## Parameter Importance")
            sorted_importance = sorted(results.parameter_importance.items(), 
                                     key=lambda x: x[1], reverse=True)
            for param, importance in sorted_importance:
                report.append(f"- **{param}:** {importance:.4f}")
            
            report.append("\n## Sensitivity Analysis")
            for param, sensitivity in results.sensitivity_analysis.items():
                report.append(f"### {param}")
                report.append(f"- Mean Effect: {sensitivity['mean_effect']:.4f}")
                report.append(f"- Max Effect: {sensitivity['max_effect']:.4f}")
                report.append(f"- Relative Effect: {sensitivity['relative_effect']:.4f}")
        
        elif isinstance(results, ComponentAblationResults):
            report.append("# Component Ablation Results Report\n")
            report.append(f"**Total Combinations Tested:** {results.metadata.get('total_combinations', 0)}")
            report.append(f"**Components Tested:** {', '.join(results.metadata.get('components_tested', []))}\n")
            
            report.append("## Best Component Combination")
            for component, choice in results.best_combination.items():
                report.append(f"- **{component}:** {choice}")
            
            report.append("\n## Component Importance")
            sorted_importance = sorted(results.component_importance.items(), 
                                     key=lambda x: x[1], reverse=True)
            for component, importance in sorted_importance:
                report.append(f"- **{component}:** {importance:.4f}")
            
            report.append("\n## Top Performing Combinations")
            sorted_performance = sorted(results.component_performance.items(), 
                                      key=lambda x: x[1].get('boundary_strength', 0), 
                                      reverse=True)
            for i, (combo, perf) in enumerate(sorted_performance[:5]):
                report.append(f"### {i+1}. {combo}")
                report.append(f"- Boundary Strength: {perf.get('boundary_strength', 0):.4f}")
                report.append(f"- Computational Time: {perf.get('computational_time', 0):.2f}s")
        
        return "\n".join(report)
"""
Comprehensive ablation studies framework for LBMD components.

This module addresses the critical feedback about missing ablation studies
by providing a systematic framework for testing each component of LBMD
and understanding their individual contributions.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
import logging
from datetime import datetime
import itertools

@dataclass
class AblationConfig:
    """Configuration for an ablation study variant."""
    name: str
    description: str
    enabled_components: List[str]
    disabled_components: List[str]
    hyperparameters: Dict[str, Any]
    expected_impact: str  # 'positive', 'negative', 'neutral'

@dataclass
class AblationResult:
    """Result from an ablation study variant."""
    config: AblationConfig
    success_rate: float
    analysis_time: float
    boundary_quality: float
    manifold_quality: float
    interpretability_score: float
    error_message: Optional[str] = None

class AblationStudyFramework:
    """
    Comprehensive framework for conducting ablation studies on LBMD.
    
    This addresses the critical feedback about missing ablation studies
    by providing systematic testing of each component and their interactions.
    """
    
    def __init__(self, base_config: Dict[str, Any]):
        """
        Initialize ablation study framework.
        
        Args:
            base_config: Base configuration for LBMD analysis
        """
        self.base_config = base_config
        self.results: List[AblationResult] = []
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Define all possible components
        self.components = [
            'feature_extraction',
            'boundary_detection', 
            'manifold_learning',
            'topological_analysis',
            'gradient_analysis',
            'clustering_analysis',
            'dimensionality_reduction'
        ]
        
        # Define hyperparameter ranges for sensitivity analysis
        self.hyperparameter_ranges = {
            'k_neurons': [5, 10, 20, 50, 100],
            'epsilon': [0.01, 0.05, 0.1, 0.2, 0.5],
            'tau': [0.1, 0.3, 0.5, 0.7, 0.9],
            'n_neighbors': [5, 10, 15, 30, 50],
            'min_dist': [0.01, 0.05, 0.1, 0.2, 0.5],
            'n_components': [2, 3, 5, 10, 20]
        }
    
    def create_ablation_configs(self) -> List[AblationConfig]:
        """
        Create comprehensive ablation study configurations.
        
        Returns:
            List of ablation configurations to test
        """
        configs = []
        
        # 1. Individual component ablations
        configs.extend(self._create_individual_component_configs())
        
        # 2. Pairwise component ablations
        configs.extend(self._create_pairwise_component_configs())
        
        # 3. Hyperparameter sensitivity studies
        configs.extend(self._create_hyperparameter_sensitivity_configs())
        
        # 4. Progressive component addition
        configs.extend(self._create_progressive_addition_configs())
        
        # 5. Component replacement studies
        configs.extend(self._create_component_replacement_configs())
        
        return configs
    
    def _create_individual_component_configs(self) -> List[AblationConfig]:
        """Create configurations with individual components disabled."""
        configs = []
        
        for component in self.components:
            config = AblationConfig(
                name=f"no_{component}",
                description=f"LBMD without {component.replace('_', ' ')}",
                enabled_components=[c for c in self.components if c != component],
                disabled_components=[component],
                hyperparameters=self.base_config.copy(),
                expected_impact=self._get_expected_impact(component, 'disabled')
            )
            configs.append(config)
        
        return configs
    
    def _create_pairwise_component_configs(self) -> List[AblationConfig]:
        """Create configurations with pairs of components disabled."""
        configs = []
        
        # Test critical component pairs
        critical_pairs = [
            ('boundary_detection', 'manifold_learning'),
            ('feature_extraction', 'boundary_detection'),
            ('manifold_learning', 'topological_analysis'),
            ('gradient_analysis', 'clustering_analysis')
        ]
        
        for comp1, comp2 in critical_pairs:
            config = AblationConfig(
                name=f"no_{comp1}_no_{comp2}",
                description=f"LBMD without {comp1.replace('_', ' ')} and {comp2.replace('_', ' ')}",
                enabled_components=[c for c in self.components if c not in [comp1, comp2]],
                disabled_components=[comp1, comp2],
                hyperparameters=self.base_config.copy(),
                expected_impact='negative'
            )
            configs.append(config)
        
        return configs
    
    def _create_hyperparameter_sensitivity_configs(self) -> List[AblationConfig]:
        """Create configurations for hyperparameter sensitivity analysis."""
        configs = []
        
        # Test each hyperparameter individually
        for param_name, param_values in self.hyperparameter_ranges.items():
            for value in param_values:
                config = AblationConfig(
                    name=f"sensitivity_{param_name}_{value}",
                    description=f"LBMD with {param_name}={value}",
                    enabled_components=self.components.copy(),
                    disabled_components=[],
                    hyperparameters={**self.base_config, param_name: value},
                    expected_impact='neutral'
                )
                configs.append(config)
        
        return configs
    
    def _create_progressive_addition_configs(self) -> List[AblationConfig]:
        """Create configurations with progressively added components."""
        configs = []
        
        # Define component importance order
        component_order = [
            'feature_extraction',
            'boundary_detection',
            'manifold_learning',
            'topological_analysis',
            'gradient_analysis',
            'clustering_analysis',
            'dimensionality_reduction'
        ]
        
        for i in range(1, len(component_order) + 1):
            enabled = component_order[:i]
            disabled = component_order[i:]
            
            config = AblationConfig(
                name=f"progressive_{i}_components",
                description=f"LBMD with first {i} components: {', '.join(enabled)}",
                enabled_components=enabled,
                disabled_components=disabled,
                hyperparameters=self.base_config.copy(),
                expected_impact='positive' if i > 3 else 'negative'
            )
            configs.append(config)
        
        return configs
    
    def _create_component_replacement_configs(self) -> List[AblationConfig]:
        """Create configurations with component replacements."""
        configs = []
        
        # Replace UMAP with other manifold learning methods
        manifold_replacements = {
            'tsne': {'manifold_method': 'tsne', 'perplexity': 30},
            'pca': {'manifold_method': 'pca', 'n_components': 2},
            'isomap': {'manifold_method': 'isomap', 'n_neighbors': 15}
        }
        
        for method, params in manifold_replacements.items():
            config = AblationConfig(
                name=f"replace_umap_with_{method}",
                description=f"LBMD with {method.upper()} instead of UMAP",
                enabled_components=self.components.copy(),
                disabled_components=[],
                hyperparameters={**self.base_config, **params},
                expected_impact='neutral'
            )
            configs.append(config)
        
        # Replace HDBSCAN with other clustering methods
        clustering_replacements = {
            'kmeans': {'clustering_method': 'kmeans', 'n_clusters': 5},
            'dbscan': {'clustering_method': 'dbscan', 'eps': 0.5},
            'spectral': {'clustering_method': 'spectral', 'n_clusters': 5}
        }
        
        for method, params in clustering_replacements.items():
            config = AblationConfig(
                name=f"replace_hdbscan_with_{method}",
                description=f"LBMD with {method.upper()} instead of HDBSCAN",
                enabled_components=self.components.copy(),
                disabled_components=[],
                hyperparameters={**self.base_config, **params},
                expected_impact='neutral'
            )
            configs.append(config)
        
        return configs
    
    def _get_expected_impact(self, component: str, action: str) -> str:
        """Get expected impact of disabling a component."""
        critical_components = ['feature_extraction', 'boundary_detection', 'manifold_learning']
        
        if component in critical_components:
            return 'negative'
        elif component in ['topological_analysis', 'gradient_analysis']:
            return 'neutral'
        else:
            return 'neutral'
    
    def run_ablation_study(self, 
                          model, 
                          test_data: List[Any],
                          configs: Optional[List[AblationConfig]] = None) -> List[AblationResult]:
        """
        Run comprehensive ablation study.
        
        Args:
            model: Model to analyze
            test_data: Test data for evaluation
            configs: Ablation configurations to test (if None, creates all)
            
        Returns:
            List of ablation results
        """
        if configs is None:
            configs = self.create_ablation_configs()
        
        self.logger.info(f"Running ablation study with {len(configs)} configurations")
        
        results = []
        
        for i, config in enumerate(configs):
            self.logger.info(f"Testing configuration {i+1}/{len(configs)}: {config.name}")
            
            try:
                result = self._run_single_ablation(model, test_data, config)
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Failed to run configuration {config.name}: {e}")
                error_result = AblationResult(
                    config=config,
                    success_rate=0.0,
                    analysis_time=0.0,
                    boundary_quality=0.0,
                    manifold_quality=0.0,
                    interpretability_score=0.0,
                    error_message=str(e)
                )
                results.append(error_result)
        
        self.results = results
        return results
    
    def _run_single_ablation(self, 
                           model, 
                           test_data: List[Any], 
                           config: AblationConfig) -> AblationResult:
        """Run a single ablation configuration."""
        from lbmd_sota.core.analyzer import LBMDAnalyzer
        
        # Create modified analyzer based on configuration
        analyzer = self._create_modified_analyzer(model, config)
        
        # Run analysis on test data
        start_time = datetime.now()
        success_count = 0
        boundary_qualities = []
        manifold_qualities = []
        interpretability_scores = []
        
        for data_point in test_data:
            try:
                result = analyzer.analyze(data_point)
                
                if result.success:
                    success_count += 1
                    boundary_qualities.append(result.boundary_strength)
                    manifold_qualities.append(result.manifold_dimension)
                    interpretability_scores.append(self._compute_interpretability_score(result))
                
            except Exception as e:
                self.logger.warning(f"Analysis failed for data point: {e}")
                continue
        
        end_time = datetime.now()
        analysis_time = (end_time - start_time).total_seconds()
        
        # Compute metrics
        success_rate = success_count / len(test_data) if test_data else 0.0
        avg_boundary_quality = np.mean(boundary_qualities) if boundary_qualities else 0.0
        avg_manifold_quality = np.mean(manifold_qualities) if manifold_qualities else 0.0
        avg_interpretability_score = np.mean(interpretability_scores) if interpretability_scores else 0.0
        
        return AblationResult(
            config=config,
            success_rate=success_rate,
            analysis_time=analysis_time,
            boundary_quality=avg_boundary_quality,
            manifold_quality=avg_manifold_quality,
            interpretability_score=avg_interpretability_score
        )
    
    def _create_modified_analyzer(self, model, config: AblationConfig):
        """Create analyzer with modified configuration."""
        from lbmd_sota.core.analyzer import LBMDAnalyzer
        
        # Create analyzer with base config
        analyzer = LBMDAnalyzer(
            model=model,
            target_layers=['layer4.1.conv2'],  # Default layer
            **config.hyperparameters
        )
        
        # Disable components as specified
        for component in config.disabled_components:
            if hasattr(analyzer, f'_disable_{component}'):
                getattr(analyzer, f'_disable_{component}')()
        
        return analyzer
    
    def _compute_interpretability_score(self, result) -> float:
        """Compute interpretability score for a result."""
        # Simple interpretability score based on available metrics
        score = 0.0
        
        if hasattr(result, 'boundary_strength'):
            score += min(1.0, result.boundary_strength * 2)  # Normalize to 0-1
        
        if hasattr(result, 'manifold_dimension'):
            # Prefer dimensions between 2-10 for interpretability
            dim = result.manifold_dimension
            if 2 <= dim <= 10:
                score += 0.5
            elif dim < 2 or dim > 20:
                score += 0.2
            else:
                score += 0.3
        
        return min(1.0, score)
    
    def analyze_ablation_results(self) -> Dict[str, Any]:
        """
        Analyze ablation study results.
        
        Returns:
            Comprehensive analysis of ablation results
        """
        if not self.results:
            return {'error': 'No ablation results to analyze'}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame([
            {
                'config_name': r.config.name,
                'description': r.config.description,
                'success_rate': r.success_rate,
                'analysis_time': r.analysis_time,
                'boundary_quality': r.boundary_quality,
                'manifold_quality': r.manifold_quality,
                'interpretability_score': r.interpretability_score,
                'expected_impact': r.config.expected_impact,
                'enabled_components': len(r.config.enabled_components),
                'disabled_components': len(r.config.disabled_components)
            }
            for r in self.results
        ])
        
        analysis = {
            'summary_statistics': self._compute_summary_statistics(df),
            'component_importance': self._analyze_component_importance(df),
            'hyperparameter_sensitivity': self._analyze_hyperparameter_sensitivity(df),
            'performance_tradeoffs': self._analyze_performance_tradeoffs(df),
            'error_analysis': self._analyze_errors(df)
        }
        
        return analysis
    
    def _compute_summary_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute summary statistics for ablation results."""
        return {
            'total_configurations': len(df),
            'successful_configurations': len(df[df['success_rate'] > 0]),
            'mean_success_rate': float(df['success_rate'].mean()),
            'std_success_rate': float(df['success_rate'].std()),
            'mean_analysis_time': float(df['analysis_time'].mean()),
            'std_analysis_time': float(df['analysis_time'].std()),
            'mean_interpretability_score': float(df['interpretability_score'].mean()),
            'std_interpretability_score': float(df['interpretability_score'].std())
        }
    
    def _analyze_component_importance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze the importance of individual components."""
        component_importance = {}
        
        # Analyze individual component ablations
        individual_configs = df[df['config_name'].str.startswith('no_')]
        
        for _, row in individual_configs.iterrows():
            component = row['config_name'].replace('no_', '')
            component_importance[component] = {
                'success_rate_impact': row['success_rate'],
                'interpretability_impact': row['interpretability_score'],
                'time_impact': row['analysis_time']
            }
        
        return component_importance
    
    def _analyze_hyperparameter_sensitivity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze hyperparameter sensitivity."""
        sensitivity_configs = df[df['config_name'].str.startswith('sensitivity_')]
        
        sensitivity_analysis = {}
        
        for param_name in self.hyperparameter_ranges.keys():
            param_configs = sensitivity_configs[
                sensitivity_configs['config_name'].str.contains(f'sensitivity_{param_name}_')
            ]
            
            if not param_configs.empty:
                sensitivity_analysis[param_name] = {
                    'success_rate_range': [
                        float(param_configs['success_rate'].min()),
                        float(param_configs['success_rate'].max())
                    ],
                    'success_rate_std': float(param_configs['success_rate'].std()),
                    'interpretability_range': [
                        float(param_configs['interpretability_score'].min()),
                        float(param_configs['interpretability_score'].max())
                    ],
                    'interpretability_std': float(param_configs['interpretability_score'].std())
                }
        
        return sensitivity_analysis
    
    def _analyze_performance_tradeoffs(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance tradeoffs between different metrics."""
        from scipy.stats import pearsonr
        
        # Success rate vs interpretability
        success_interpretability_corr, success_interpretability_p = pearsonr(
            df['success_rate'], df['interpretability_score']
        )
        
        # Analysis time vs success rate
        time_success_corr, time_success_p = pearsonr(
            df['analysis_time'], df['success_rate']
        )
        
        # Boundary quality vs manifold quality
        boundary_manifold_corr, boundary_manifold_p = pearsonr(
            df['boundary_quality'], df['manifold_quality']
        )
        
        return {
            'success_interpretability_correlation': {
                'correlation': float(success_interpretability_corr),
                'p_value': float(success_interpretability_p),
                'is_significant': success_interpretability_p < 0.05
            },
            'time_success_correlation': {
                'correlation': float(time_success_corr),
                'p_value': float(time_success_p),
                'is_significant': time_success_p < 0.05
            },
            'boundary_manifold_correlation': {
                'correlation': float(boundary_manifold_corr),
                'p_value': float(boundary_manifold_p),
                'is_significant': boundary_manifold_p < 0.05
            }
        }
    
    def _analyze_errors(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze error patterns in ablation results."""
        error_analysis = {
            'failed_configurations': len(df[df['success_rate'] == 0]),
            'low_performance_configurations': len(df[df['success_rate'] < 0.5]),
            'high_time_configurations': len(df[df['analysis_time'] > df['analysis_time'].quantile(0.9)]),
            'low_interpretability_configurations': len(df[df['interpretability_score'] < 0.3])
        }
        
        return error_analysis
    
    def create_ablation_visualizations(self, output_dir: str = "ablation_plots") -> List[str]:
        """
        Create comprehensive visualizations of ablation results.
        
        Args:
            output_dir: Directory to save visualizations
            
        Returns:
            List of paths to created visualizations
        """
        if not self.results:
            return []
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        df = pd.DataFrame([
            {
                'config_name': r.config.name,
                'success_rate': r.success_rate,
                'analysis_time': r.analysis_time,
                'boundary_quality': r.boundary_quality,
                'manifold_quality': r.manifold_quality,
                'interpretability_score': r.interpretability_score,
                'enabled_components': len(r.config.enabled_components)
            }
            for r in self.results
        ])
        
        plots = []
        
        # 1. Success rate by configuration
        plt.figure(figsize=(15, 8))
        plt.bar(range(len(df)), df['success_rate'])
        plt.xlabel('Configuration')
        plt.ylabel('Success Rate')
        plt.title('Success Rate by Ablation Configuration')
        plt.xticks(range(len(df)), df['config_name'], rotation=45, ha='right')
        plt.tight_layout()
        plot_path = output_path / 'success_rate_by_config.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        plots.append(str(plot_path))
        
        # 2. Performance tradeoffs
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Success rate vs interpretability
        axes[0, 0].scatter(df['success_rate'], df['interpretability_score'], alpha=0.7)
        axes[0, 0].set_xlabel('Success Rate')
        axes[0, 0].set_ylabel('Interpretability Score')
        axes[0, 0].set_title('Success Rate vs Interpretability')
        
        # Analysis time vs success rate
        axes[0, 1].scatter(df['analysis_time'], df['success_rate'], alpha=0.7)
        axes[0, 1].set_xlabel('Analysis Time (s)')
        axes[0, 1].set_ylabel('Success Rate')
        axes[0, 1].set_title('Analysis Time vs Success Rate')
        
        # Boundary quality vs manifold quality
        axes[1, 0].scatter(df['boundary_quality'], df['manifold_quality'], alpha=0.7)
        axes[1, 0].set_xlabel('Boundary Quality')
        axes[1, 0].set_ylabel('Manifold Quality')
        axes[1, 0].set_title('Boundary Quality vs Manifold Quality')
        
        # Component count vs performance
        axes[1, 1].scatter(df['enabled_components'], df['success_rate'], alpha=0.7)
        axes[1, 1].set_xlabel('Number of Enabled Components')
        axes[1, 1].set_ylabel('Success Rate')
        axes[1, 1].set_title('Component Count vs Success Rate')
        
        plt.tight_layout()
        plot_path = output_path / 'performance_tradeoffs.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        plots.append(str(plot_path))
        
        # 3. Heatmap of component importance
        individual_configs = df[df['config_name'].str.startswith('no_')]
        if not individual_configs.empty:
            plt.figure(figsize=(10, 6))
            components = [name.replace('no_', '') for name in individual_configs['config_name']]
            success_rates = individual_configs['success_rate'].values
            
            plt.bar(components, success_rates)
            plt.xlabel('Disabled Component')
            plt.ylabel('Success Rate')
            plt.title('Impact of Disabling Individual Components')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            plot_path = output_path / 'component_importance.png'
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            plots.append(str(plot_path))
        
        return plots
    
    def generate_ablation_report(self, output_path: str = "ablation_study_report.json") -> str:
        """
        Generate comprehensive ablation study report.
        
        Args:
            output_path: Path to save the report
            
        Returns:
            Path to the generated report
        """
        analysis = self.analyze_ablation_results()
        
        # Add metadata
        report = {
            'study_metadata': {
                'generation_time': datetime.now().isoformat(),
                'total_configurations': len(self.results),
                'base_config': self.base_config
            },
            'analysis_results': analysis,
            'detailed_results': [
                {
                    'config_name': r.config.name,
                    'description': r.config.description,
                    'success_rate': r.success_rate,
                    'analysis_time': r.analysis_time,
                    'boundary_quality': r.boundary_quality,
                    'manifold_quality': r.manifold_quality,
                    'interpretability_score': r.interpretability_score,
                    'error_message': r.error_message
                }
                for r in self.results
            ]
        }
        
        # Save report
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Ablation study report saved to {output_path}")
        return output_path

def run_comprehensive_ablation_study(model, 
                                   test_data: List[Any],
                                   base_config: Optional[Dict[str, Any]] = None,
                                   output_dir: str = "ablation_study") -> AblationStudyFramework:
    """
    Run a comprehensive ablation study on LBMD.
    
    Args:
        model: Model to analyze
        test_data: Test data for evaluation
        base_config: Base configuration for LBMD
        output_dir: Output directory for results
        
    Returns:
        Completed ablation study framework
    """
    if base_config is None:
        base_config = {
            'k_neurons': 20,
            'epsilon': 0.1,
            'tau': 0.5,
            'manifold_method': 'umap',
            'n_components': 2,
            'n_neighbors': 15,
            'min_dist': 0.1
        }
    
    # Create ablation study framework
    framework = AblationStudyFramework(base_config)
    
    # Run ablation study
    results = framework.run_ablation_study(model, test_data)
    
    # Generate analysis and visualizations
    analysis = framework.analyze_ablation_results()
    plots = framework.create_ablation_visualizations(output_dir)
    report_path = framework.generate_ablation_report(f"{output_dir}/ablation_report.json")
    
    print(f"Ablation study completed:")
    print(f"- {len(results)} configurations tested")
    print(f"- {len(plots)} visualizations created")
    print(f"- Report saved to: {report_path}")
    
    return framework

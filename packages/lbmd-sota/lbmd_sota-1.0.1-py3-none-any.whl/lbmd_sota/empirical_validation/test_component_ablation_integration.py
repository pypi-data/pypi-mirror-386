"""
Integration tests for component ablation workflows.
Tests the complete pipeline of boundary detection, manifold learning, and clustering.
"""

import pytest
import numpy as np
import torch
from typing import Dict, Any, List, Tuple
import tempfile
import os
from unittest.mock import Mock, patch

from .boundary_detectors import (
    BoundaryDetectorFactory, 
    compare_boundary_methods,
    evaluate_boundary_detection,
    compute_boundary_consistency
)
from .manifold_learners import (
    ManifoldLearnerFactory,
    compare_manifold_methods
)
from .clustering_algorithms import (
    ClusteringAlgorithmFactory,
    compare_clustering_algorithms,
    evaluate_clustering,
    find_optimal_clusters
)
from .ablation_study_runner import AblationStudyRunner


class TestBoundaryDetectionAblation:
    """Integration tests for boundary detection ablation studies."""
    
    @pytest.fixture
    def test_features(self):
        """Generate test features with known boundary structure."""
        # Create features with clear boundaries
        features = torch.zeros(1, 32, 16, 16)
        
        # Add some structure that should create boundaries
        features[0, :16, :8, :8] = 1.0  # Top-left quadrant
        features[0, 16:, 8:, 8:] = 1.0  # Bottom-right quadrant
        features[0, :16, 8:, :8] = 0.5  # Top-right quadrant
        features[0, 16:, :8, 8:] = 0.5  # Bottom-left quadrant
        
        # Add some noise
        features += torch.randn_like(features) * 0.1
        
        return features
    
    def test_boundary_detector_comparison(self, test_features):
        """Test comparison of different boundary detection methods."""
        methods = ['gradient_based', 'learned', 'hybrid']
        
        # Configure methods
        configs = {
            'gradient_based': {
                'gradient_threshold': 0.1,
                'smoothing_sigma': 1.0,
                'edge_method': 'sobel'
            },
            'learned': {
                'model_type': 'isolation_forest',
                'contamination': 0.1
            },
            'hybrid': {
                'gradient_weight': 0.6,
                'learned_weight': 0.4,
                'fusion_method': 'weighted_average'
            }
        }
        
        results = compare_boundary_methods(test_features, methods, configs)
        
        # Verify all methods completed successfully
        for method in methods:
            assert method in results
            assert results[method]['success']
            assert results[method]['boundaries'] is not None
            assert results[method]['boundary_scores'] is not None
            
            # Check output shapes
            expected_shape = test_features.shape[2:]  # Spatial dimensions
            assert results[method]['boundaries'].shape == expected_shape
            assert results[method]['boundary_scores'].shape == expected_shape
            
            # Check boundary detection statistics
            n_boundary_pixels = results[method]['n_boundary_pixels']
            assert n_boundary_pixels > 0
            assert n_boundary_pixels < np.prod(expected_shape)  # Not all pixels should be boundaries
    
    def test_boundary_detection_consistency(self, test_features):
        """Test consistency between different boundary detection runs."""
        detector = BoundaryDetectorFactory.create_detector('gradient_based')
        
        # Run detection multiple times
        boundaries1 = detector.detect_boundaries(test_features)
        boundaries2 = detector.detect_boundaries(test_features)
        
        # Should be identical for deterministic methods
        consistency = compute_boundary_consistency(boundaries1, boundaries2)
        assert consistency == 1.0  # Perfect consistency expected
    
    def test_boundary_detection_evaluation_metrics(self, test_features):
        """Test boundary detection evaluation with synthetic ground truth."""
        # Create synthetic ground truth boundaries
        gt_boundaries = np.zeros((16, 16), dtype=np.uint8)
        gt_boundaries[7:9, :] = 1  # Horizontal boundary
        gt_boundaries[:, 7:9] = 1  # Vertical boundary
        
        # Test gradient-based detector
        detector = BoundaryDetectorFactory.create_detector('gradient_based')
        predicted_boundaries = detector.detect_boundaries(test_features)
        
        # Evaluate performance
        metrics = evaluate_boundary_detection(predicted_boundaries, gt_boundaries)
        
        # Check that metrics are computed
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1_score' in metrics
        assert 'accuracy' in metrics
        
        # Metrics should be in valid ranges
        for metric_name in ['precision', 'recall', 'f1_score', 'accuracy']:
            assert 0 <= metrics[metric_name] <= 1
    
    def test_boundary_detector_parameter_sensitivity(self, test_features):
        """Test sensitivity of boundary detectors to parameter changes."""
        # Test gradient-based detector with different thresholds
        thresholds = [0.05, 0.1, 0.15, 0.2]
        results = []
        
        for threshold in thresholds:
            config = {'gradient_threshold': threshold}
            detector = BoundaryDetectorFactory.create_detector('gradient_based', config)
            boundaries = detector.detect_boundaries(test_features)
            boundary_scores = detector.compute_boundary_scores(test_features)
            
            results.append({
                'threshold': threshold,
                'n_boundaries': np.sum(boundaries),
                'mean_score': np.mean(boundary_scores),
                'max_score': np.max(boundary_scores)
            })
        
        # Verify that changing threshold affects results
        n_boundaries = [r['n_boundaries'] for r in results]
        assert len(set(n_boundaries)) > 1  # Should produce different results
        
        # Lower thresholds should generally produce more boundaries
        assert n_boundaries[0] >= n_boundaries[-1]


class TestManifoldLearningAblation:
    """Integration tests for manifold learning ablation studies."""
    
    @pytest.fixture
    def structured_features(self):
        """Generate features with known manifold structure."""
        # Create features that lie on a 2D manifold embedded in higher dimensions
        n_samples = 100
        t = np.linspace(0, 2*np.pi, n_samples)
        
        # Swiss roll-like structure
        x = t * np.cos(t)
        y = t * np.sin(t)
        z = np.random.normal(0, 0.1, n_samples)
        
        # Embed in higher dimensional space
        features = np.zeros((n_samples, 32))
        features[:, 0] = x
        features[:, 1] = y
        features[:, 2] = z
        features[:, 3:] = np.random.normal(0, 0.05, (n_samples, 29))
        
        # Reshape to spatial format for consistency
        features_spatial = features.reshape(1, 32, 10, 10)
        return torch.tensor(features_spatial, dtype=torch.float32)
    
    def test_manifold_learner_comparison(self, structured_features):
        """Test comparison of different manifold learning methods."""
        methods = ['pca', 'umap']
        
        configs = {
            'pca': {'n_components': 2, 'whiten': False},
            'umap': {'n_components': 2, 'n_neighbors': 5, 'min_dist': 0.1}
        }
        
        results = compare_manifold_methods(structured_features, methods, configs)
        
        # Verify all methods completed successfully
        for method in methods:
            assert method in results
            assert results[method]['success']
            assert results[method]['embedding'] is not None
            
            # Check embedding shape
            embedding = results[method]['embedding']
            assert embedding.shape[1] == 2  # 2D embedding
            assert embedding.shape[0] == 100  # Number of samples
            
            # Check quality metrics
            quality = results[method]['quality_metrics']
            assert 'embedding_variance' in quality
            assert 'embedding_range' in quality
            assert quality['embedding_variance'] > 0
            assert quality['embedding_range'] > 0
    
    def test_manifold_learning_dimensionality_effect(self, structured_features):
        """Test effect of different embedding dimensions."""
        dimensions = [2, 3, 5]
        method = 'pca'
        
        results = []
        for dim in dimensions:
            config = {'n_components': dim}
            learner = ManifoldLearnerFactory.create_learner(method, config)
            embedding = learner.fit_transform(structured_features)
            
            results.append({
                'dimension': dim,
                'embedding_shape': embedding.shape,
                'explained_variance': getattr(learner.embedding_model, 'explained_variance_ratio_', None)
            })
        
        # Verify embeddings have correct dimensions
        for i, result in enumerate(results):
            expected_dim = dimensions[i]
            assert result['embedding_shape'][1] == expected_dim
    
    def test_manifold_learning_reproducibility(self, structured_features):
        """Test reproducibility of manifold learning methods."""
        config = {'n_components': 2, 'random_state': 42}
        
        # Test PCA (should be deterministic)
        learner1 = ManifoldLearnerFactory.create_learner('pca', config)
        learner2 = ManifoldLearnerFactory.create_learner('pca', config)
        
        embedding1 = learner1.fit_transform(structured_features)
        embedding2 = learner2.fit_transform(structured_features)
        
        # Should be identical (or very close due to numerical precision)
        np.testing.assert_allclose(embedding1, embedding2, rtol=1e-10)
    
    def test_manifold_transform_consistency(self, structured_features):
        """Test consistency of transform method with fit_transform."""
        config = {'n_components': 2, 'random_state': 42}
        learner = ManifoldLearnerFactory.create_learner('pca', config)
        
        # Fit and transform
        embedding1 = learner.fit_transform(structured_features)
        
        # Transform same data
        embedding2 = learner.transform(structured_features)
        
        # Should be identical
        np.testing.assert_allclose(embedding1, embedding2, rtol=1e-10)


class TestClusteringAblation:
    """Integration tests for clustering ablation studies."""
    
    @pytest.fixture
    def clustered_features(self):
        """Generate features with known cluster structure."""
        # Create 3 distinct clusters
        cluster_centers = [
            [2, 2], [-2, -2], [2, -2]
        ]
        n_samples_per_cluster = 20
        
        features = []
        labels = []
        
        for i, center in enumerate(cluster_centers):
            # Generate samples around each center
            cluster_samples = np.random.multivariate_normal(
                center, [[0.5, 0], [0, 0.5]], n_samples_per_cluster
            )
            features.append(cluster_samples)
            labels.extend([i] * n_samples_per_cluster)
        
        features = np.vstack(features)
        
        # Pad with additional dimensions and reshape to spatial format
        features_padded = np.zeros((len(features), 16))
        features_padded[:, :2] = features
        features_padded[:, 2:] = np.random.normal(0, 0.1, (len(features), 14))
        
        # Reshape to spatial format
        features_spatial = features_padded.reshape(1, 16, int(np.sqrt(len(features))), -1)
        features_spatial = features_spatial[:, :, :8, :8]  # Adjust to valid spatial dimensions
        
        return torch.tensor(features_spatial, dtype=torch.float32), np.array(labels[:64])  # Match spatial size
    
    def test_clustering_algorithm_comparison(self, clustered_features):
        """Test comparison of different clustering algorithms."""
        features, ground_truth = clustered_features
        
        algorithms = ['kmeans', 'hdbscan']
        configs = {
            'kmeans': {'n_clusters': 3, 'random_state': 42},
            'hdbscan': {'min_cluster_size': 5, 'min_samples': 3}
        }
        
        results = compare_clustering_algorithms(features, algorithms, configs, ground_truth)
        
        # Verify all algorithms completed successfully
        for algorithm in algorithms:
            assert algorithm in results
            assert results[algorithm]['success']
            assert results[algorithm]['labels'] is not None
            
            # Check evaluation metrics
            metrics = results[algorithm]['evaluation_metrics']
            assert 'silhouette_score' in metrics
            assert 'adjusted_rand_score' in metrics
            assert 'normalized_mutual_info' in metrics
            
            # Metrics should be in valid ranges
            if not np.isnan(metrics['silhouette_score']):
                assert -1 <= metrics['silhouette_score'] <= 1
            assert 0 <= metrics['adjusted_rand_score'] <= 1
            assert 0 <= metrics['normalized_mutual_info'] <= 1
    
    def test_clustering_evaluation_metrics(self, clustered_features):
        """Test clustering evaluation metrics computation."""
        features, ground_truth = clustered_features
        
        # Test K-means clustering
        clusterer = ClusteringAlgorithmFactory.create_algorithm(
            'kmeans', {'n_clusters': 3, 'random_state': 42}
        )
        labels = clusterer.fit_predict(features)
        
        # Prepare features for evaluation
        features_flat = features.squeeze(0).transpose(1, 2, 0).reshape(-1, features.shape[1])
        
        # Evaluate clustering
        metrics = evaluate_clustering(features_flat, labels, ground_truth)
        
        # Check all expected metrics are present
        expected_metrics = [
            'silhouette_score', 'inertia', 'adjusted_rand_score', 
            'normalized_mutual_info', 'n_clusters', 'n_noise_points',
            'largest_cluster_size', 'smallest_cluster_size'
        ]
        
        for metric in expected_metrics:
            assert metric in metrics
        
        # Check metric validity
        assert metrics['n_clusters'] > 0
        assert metrics['n_noise_points'] >= 0
        assert metrics['largest_cluster_size'] > 0
        assert metrics['smallest_cluster_size'] > 0
    
    def test_optimal_cluster_finding(self, clustered_features):
        """Test automatic optimal cluster number detection."""
        features, _ = clustered_features
        
        # Test elbow method with K-means
        result = find_optimal_clusters(
            features, 
            algorithm='kmeans',
            k_range=(2, 6),
            config={'random_state': 42}
        )
        
        assert 'k_values' in result
        assert 'inertias' in result
        assert 'silhouette_scores' in result
        assert 'optimal_k_elbow' in result
        assert 'optimal_k_silhouette' in result
        
        # Should find reasonable number of clusters (around 3 for our test data)
        if result['optimal_k_silhouette'] is not None:
            assert 2 <= result['optimal_k_silhouette'] <= 6
    
    def test_clustering_parameter_sensitivity(self, clustered_features):
        """Test sensitivity of clustering to parameter changes."""
        features, _ = clustered_features
        
        # Test K-means with different numbers of clusters
        k_values = [2, 3, 4, 5]
        results = []
        
        for k in k_values:
            clusterer = ClusteringAlgorithmFactory.create_algorithm(
                'kmeans', {'n_clusters': k, 'random_state': 42}
            )
            labels = clusterer.fit_predict(features)
            
            # Prepare features for evaluation
            features_flat = features.squeeze(0).transpose(1, 2, 0).reshape(-1, features.shape[1])
            metrics = evaluate_clustering(features_flat, labels)
            
            results.append({
                'k': k,
                'silhouette_score': metrics['silhouette_score'],
                'inertia': metrics['inertia']
            })
        
        # Verify that different k values produce different results
        silhouette_scores = [r['silhouette_score'] for r in results if not np.isnan(r['silhouette_score'])]
        if len(silhouette_scores) > 1:
            assert len(set(np.round(silhouette_scores, 3))) > 1  # Should produce different scores


class TestIntegratedAblationWorkflows:
    """Integration tests for complete ablation study workflows."""
    
    @pytest.fixture
    def complex_features(self):
        """Generate complex features for integrated testing."""
        # Create features with multiple structures
        features = torch.randn(1, 64, 16, 16)
        
        # Add structured patterns
        features[0, :32, :8, :8] = 2.0  # Strong signal in one region
        features[0, 32:, 8:, 8:] = -2.0  # Strong opposite signal
        features[0, :32, 8:, :8] = 1.0  # Medium signal
        features[0, 32:, :8, 8:] = -1.0  # Medium opposite signal
        
        # Add noise
        features += torch.randn_like(features) * 0.3
        
        return features
    
    def test_complete_ablation_pipeline(self, complex_features):
        """Test complete ablation study pipeline."""
        config = {
            'parameter_ranges': {
                'k': [5, 10],
                'epsilon': [0.1, 0.2]
            },
            'search_strategy': 'grid',
            'parallel_jobs': 1
        }
        
        runner = AblationStudyRunner(config)
        runner.initialize()
        
        # Test parameter sweep
        param_results = runner.run_parameter_sweep()
        
        assert param_results.best_parameters is not None
        assert param_results.best_score > 0
        assert len(param_results.all_results) == 4  # 2 * 2 combinations
        
        # Test component ablation
        components = {
            'boundary_detector': ['gradient_based'],
            'manifold_learner': ['pca'],
            'clustering_algorithm': ['kmeans']
        }
        
        comp_results = runner.run_component_ablation(components)
        
        assert comp_results.best_combination is not None
        assert comp_results.component_importance is not None
        assert len(comp_results.component_performance) == 1
    
    def test_cross_component_interactions(self, complex_features):
        """Test interactions between different components."""
        # Test how boundary detection affects manifold learning
        boundary_detector = BoundaryDetectorFactory.create_detector('gradient_based')
        boundary_scores = boundary_detector.compute_boundary_scores(complex_features)
        
        # Use boundary scores to weight features
        weighted_features = complex_features * torch.tensor(boundary_scores).unsqueeze(0).unsqueeze(0)
        
        # Compare manifold learning on original vs weighted features
        learner = ManifoldLearnerFactory.create_learner('pca', {'n_components': 2})
        
        embedding_original = learner.fit_transform(complex_features)
        
        learner_weighted = ManifoldLearnerFactory.create_learner('pca', {'n_components': 2})
        embedding_weighted = learner_weighted.fit_transform(weighted_features)
        
        # Embeddings should be different
        assert not np.allclose(embedding_original, embedding_weighted, rtol=0.1)
    
    def test_ablation_study_reproducibility(self, complex_features):
        """Test reproducibility of ablation studies."""
        config = {
            'parameter_ranges': {
                'k': [5, 10],
                'epsilon': [0.1, 0.2]
            },
            'search_strategy': 'grid',
            'parallel_jobs': 1
        }
        
        # Run ablation study twice
        runner1 = AblationStudyRunner(config)
        runner1.initialize()
        results1 = runner1.run_parameter_sweep()
        
        runner2 = AblationStudyRunner(config)
        runner2.initialize()
        results2 = runner2.run_parameter_sweep()
        
        # Results should be similar (allowing for some randomness in evaluation)
        assert results1.best_parameters == results2.best_parameters
        assert abs(results1.best_score - results2.best_score) < 0.1
    
    def test_ablation_study_with_real_components(self, complex_features):
        """Test ablation study with real component implementations."""
        config = {'parallel_jobs': 1}
        runner = AblationStudyRunner(config)
        runner.initialize()
        
        # Test with multiple real components
        components = {
            'boundary_detector': ['gradient_based', 'learned'],
            'manifold_learner': ['pca', 'umap']
        }
        
        results = runner.run_component_ablation(components)
        
        # Should complete successfully
        assert len(results.component_performance) == 4  # 2 * 2 combinations
        
        # All combinations should have valid performance metrics
        for combo_name, performance in results.component_performance.items():
            assert 'boundary_strength' in performance
            assert 'computational_time' in performance
            assert 0 <= performance['boundary_strength'] <= 1
            assert performance['computational_time'] > 0
    
    def test_error_recovery_in_ablation_pipeline(self, complex_features):
        """Test error recovery during ablation studies."""
        config = {'parallel_jobs': 1}
        runner = AblationStudyRunner(config)
        runner.initialize()
        
        # Mock a component evaluation that sometimes fails
        original_evaluate = runner._evaluate_component_combination
        
        def failing_evaluate(components):
            if 'learned' in components.get('boundary_detector', ''):
                raise RuntimeError("Simulated component failure")
            return original_evaluate(components)
        
        runner._evaluate_component_combination = failing_evaluate
        
        # Test with components that include failing one
        components = {
            'boundary_detector': ['gradient_based', 'learned'],
            'manifold_learner': ['pca']
        }
        
        results = runner.run_component_ablation(components)
        
        # Should handle failures gracefully
        assert len(results.component_performance) == 2
        
        # Failed combination should have zero performance
        failed_combo = None
        for combo_name, performance in results.component_performance.items():
            if 'learned' in combo_name:
                failed_combo = combo_name
                assert performance['boundary_strength'] == 0.0
                assert performance['computational_time'] == float('inf')
        
        assert failed_combo is not None


class TestAblationResultsAnalysis:
    """Tests for ablation results analysis and interpretation."""
    
    def test_parameter_importance_ranking(self):
        """Test parameter importance ranking functionality."""
        # Create mock results with known parameter effects
        results = []
        
        # k parameter has strong effect
        for k in [5, 10, 15, 20]:
            for epsilon in [0.1, 0.2]:
                score = 0.5 + 0.3 * (k / 20.0)  # k has positive effect
                score += 0.1 * np.random.random()  # Add noise
                results.append({
                    'k': k,
                    'epsilon': epsilon,
                    'boundary_strength': score
                })
        
        # Compute importance
        config = ParameterSweepConfig(parameter_ranges={})
        framework = ParameterSweepFramework(config)
        importance = framework.compute_parameter_importance(results, 'boundary_strength')
        
        # k should have higher importance than epsilon
        assert importance['k'] > importance['epsilon']
        assert importance['k'] > 0.5  # Should detect strong effect
    
    def test_sensitivity_analysis_interpretation(self):
        """Test sensitivity analysis interpretation."""
        # Create results with different sensitivity patterns
        results = []
        
        # Parameter with high sensitivity
        for k in [5, 15, 25]:
            for epsilon in [0.1, 0.2]:
                if k == 5:
                    score = 0.3
                elif k == 15:
                    score = 0.9  # Optimal value
                else:
                    score = 0.4
                
                score += 0.05 * np.random.random()
                results.append({
                    'k': k,
                    'epsilon': epsilon,
                    'boundary_strength': score
                })
        
        config = ParameterSweepConfig(parameter_ranges={})
        framework = ParameterSweepFramework(config)
        sensitivity = framework.sensitivity_analysis(results, 'boundary_strength')
        
        # k should show high sensitivity
        assert 'k' in sensitivity
        assert sensitivity['k']['max_effect'] > 0.5  # Large effect range
        assert sensitivity['k']['relative_effect'] > 0.5  # Large relative effect
    
    def test_component_interaction_analysis(self):
        """Test component interaction effect analysis."""
        config = {'parallel_jobs': 1}
        runner = AblationStudyRunner(config)
        runner.initialize()
        
        # Mock performance data with interaction effects
        performance_data = {
            'boundary_detector:gradient_based_manifold_learner:pca': {'boundary_strength': 0.7},
            'boundary_detector:gradient_based_manifold_learner:umap': {'boundary_strength': 0.6},
            'boundary_detector:learned_manifold_learner:pca': {'boundary_strength': 0.5},
            'boundary_detector:learned_manifold_learner:umap': {'boundary_strength': 0.9}  # Strong interaction
        }
        
        component_names = ['boundary_detector', 'manifold_learner']
        interactions = runner._compute_interaction_effects(performance_data, component_names)
        
        # Should detect interaction between components
        assert ('boundary_detector', 'manifold_learner') in interactions
        assert interactions[('boundary_detector', 'manifold_learner')] >= 0


# Utility test functions

def test_ablation_test_utilities():
    """Test utility functions for ablation testing."""
    # Test feature generation
    features = generate_test_features(batch_size=2, channels=32, height=8, width=8)
    assert features.shape == (2, 32, 8, 8)
    
    # Test mock evaluation function
    eval_func = create_mock_evaluation_function({'k': 10, 'epsilon': 0.1})
    
    # Test with optimal parameters
    optimal_score = eval_func({'k': 10, 'epsilon': 0.1})
    suboptimal_score = eval_func({'k': 5, 'epsilon': 0.2})
    
    assert optimal_score > suboptimal_score


def generate_test_features(batch_size=1, channels=64, height=8, width=8):
    """Generate synthetic test features for ablation studies."""
    return torch.randn(batch_size, channels, height, width)


def create_mock_evaluation_function(optimal_params=None):
    """Create a mock evaluation function with known optimal parameters."""
    if optimal_params is None:
        optimal_params = {'k': 15, 'epsilon': 0.1, 'tau': 0.3}
    
    def evaluation_function(params):
        score = 1.0
        for param_name, optimal_value in optimal_params.items():
            if param_name in params:
                # Gaussian-like function around optimal value
                diff = abs(params[param_name] - optimal_value) / optimal_value
                score *= np.exp(-diff**2)
        
        # Add small amount of noise
        score += np.random.normal(0, 0.05)
        return max(0, min(1, score))
    
    return evaluation_function


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
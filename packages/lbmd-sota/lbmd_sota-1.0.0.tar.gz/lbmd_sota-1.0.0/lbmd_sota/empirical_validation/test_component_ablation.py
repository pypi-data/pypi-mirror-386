"""
Test script for component ablation functionality.
"""

import torch
import numpy as np
import logging
from typing import Dict, Any

from .boundary_detectors import BoundaryDetectorFactory, compare_boundary_methods
from .manifold_learners import ManifoldLearnerFactory, compare_manifold_methods
from .clustering_algorithms import ClusteringAlgorithmFactory, compare_clustering_algorithms
from .ablation_study_runner import AblationStudyRunner


def test_boundary_detectors():
    """Test all boundary detection algorithms."""
    print("Testing Boundary Detectors...")
    
    # Generate test features
    test_features = torch.randn(1, 128, 16, 16)
    
    # Test each detector type
    detector_types = BoundaryDetectorFactory.get_available_detectors()
    
    for detector_type in detector_types:
        print(f"\nTesting {detector_type} detector:")
        
        try:
            # Create detector
            detector = BoundaryDetectorFactory.create_detector(detector_type)
            
            # Test boundary detection
            boundaries = detector.detect_boundaries(test_features)
            boundary_scores = detector.compute_boundary_scores(test_features)
            
            print(f"  Boundaries shape: {boundaries.shape}")
            print(f"  Boundary scores shape: {boundary_scores.shape}")
            print(f"  Boundary pixels detected: {np.sum(boundaries)}")
            print(f"  Mean boundary score: {np.mean(boundary_scores):.4f}")
            print(f"  ✓ {detector_type} detector working correctly")
            
        except Exception as e:
            print(f"  ✗ {detector_type} detector failed: {e}")


def test_manifold_learners():
    """Test all manifold learning algorithms."""
    print("\n\nTesting Manifold Learners...")
    
    # Generate test features
    test_features = torch.randn(1, 64, 8, 8)
    
    # Test each learner type
    learner_types = ManifoldLearnerFactory.get_available_learners()
    
    for learner_type in learner_types:
        print(f"\nTesting {learner_type} learner:")
        
        try:
            # Create learner
            config = {'n_components': 2}
            learner = ManifoldLearnerFactory.create_learner(learner_type, config)
            
            # Test manifold learning
            embedding = learner.fit_transform(test_features)
            
            print(f"  Embedding shape: {embedding.shape}")
            print(f"  Embedding range: [{np.min(embedding):.4f}, {np.max(embedding):.4f}]")
            print(f"  ✓ {learner_type} learner working correctly")
            
            # Test transform on new data (if supported)
            if learner_type in ['umap', 'pca', 'isomap', 'kernel_pca']:
                try:
                    new_features = torch.randn(1, 64, 8, 8)
                    new_embedding = learner.transform(new_features)
                    print(f"  Transform on new data: {new_embedding.shape}")
                except Exception as e:
                    print(f"  Transform on new data failed: {e}")
            
        except Exception as e:
            print(f"  ✗ {learner_type} learner failed: {e}")


def test_clustering_algorithms():
    """Test all clustering algorithms."""
    print("\n\nTesting Clustering Algorithms...")
    
    # Generate test features (2D for easier clustering)
    test_features = torch.randn(1, 32, 4, 4)
    
    # Test each algorithm type
    algorithm_types = ClusteringAlgorithmFactory.get_available_algorithms()
    
    for algorithm_type in algorithm_types:
        print(f"\nTesting {algorithm_type} clustering:")
        
        try:
            # Create algorithm
            config = {}
            if algorithm_type in ['kmeans', 'spectral', 'agglomerative']:
                config['n_clusters'] = 3
            elif algorithm_type == 'gaussian_mixture':
                config['n_components'] = 3
            elif algorithm_type in ['hdbscan', 'dbscan']:
                config['min_samples'] = 2
            
            clusterer = ClusteringAlgorithmFactory.create_algorithm(algorithm_type, config)
            
            # Test clustering
            labels = clusterer.fit_predict(test_features)
            
            unique_labels = set(labels)
            n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
            n_noise = np.sum(labels == -1) if -1 in labels else 0
            
            print(f"  Labels shape: {labels.shape}")
            print(f"  Number of clusters: {n_clusters}")
            print(f"  Number of noise points: {n_noise}")
            print(f"  ✓ {algorithm_type} clustering working correctly")
            
            # Test predict on new data (if supported)
            if algorithm_type in ['kmeans', 'gaussian_mixture']:
                try:
                    new_features = torch.randn(1, 32, 4, 4)
                    new_labels = clusterer.predict(new_features)
                    print(f"  Predict on new data: {new_labels.shape}")
                except Exception as e:
                    print(f"  Predict on new data failed: {e}")
            
        except Exception as e:
            print(f"  ✗ {algorithm_type} clustering failed: {e}")


def test_component_comparison():
    """Test component comparison functions."""
    print("\n\nTesting Component Comparison Functions...")
    
    # Generate test features
    test_features = torch.randn(1, 64, 8, 8)
    
    # Test boundary detector comparison
    print("\nTesting boundary detector comparison:")
    try:
        boundary_methods = ['gradient_based', 'learned', 'hybrid']
        boundary_results = compare_boundary_methods(test_features, boundary_methods)
        
        for method, result in boundary_results.items():
            if result['success']:
                print(f"  {method}: boundary strength = {np.mean(result['boundary_scores']):.4f}")
            else:
                print(f"  {method}: failed - {result.get('error', 'unknown error')}")
        
        print("  ✓ Boundary detector comparison working")
    except Exception as e:
        print(f"  ✗ Boundary detector comparison failed: {e}")
    
    # Test manifold learner comparison
    print("\nTesting manifold learner comparison:")
    try:
        manifold_methods = ['umap', 'pca', 'tsne']
        manifold_results = compare_manifold_methods(test_features, manifold_methods)
        
        for method, result in manifold_results.items():
            if result['success']:
                quality = result['quality_metrics']
                print(f"  {method}: trustworthiness = {quality['trustworthiness']:.4f}")
            else:
                print(f"  {method}: failed - {result.get('error', 'unknown error')}")
        
        print("  ✓ Manifold learner comparison working")
    except Exception as e:
        print(f"  ✗ Manifold learner comparison failed: {e}")
    
    # Test clustering algorithm comparison
    print("\nTesting clustering algorithm comparison:")
    try:
        clustering_methods = ['kmeans', 'hdbscan']
        clustering_configs = {
            'kmeans': {'n_clusters': 3},
            'hdbscan': {'min_cluster_size': 2}
        }
        clustering_results = compare_clustering_algorithms(
            test_features, clustering_methods, clustering_configs
        )
        
        for method, result in clustering_results.items():
            if result['success']:
                metrics = result['evaluation_metrics']
                print(f"  {method}: silhouette = {metrics['silhouette_score']:.4f}, "
                      f"clusters = {result['n_clusters']}")
            else:
                print(f"  {method}: failed - {result.get('error', 'unknown error')}")
        
        print("  ✓ Clustering algorithm comparison working")
    except Exception as e:
        print(f"  ✗ Clustering algorithm comparison failed: {e}")


def test_ablation_study_runner():
    """Test the ablation study runner."""
    print("\n\nTesting Ablation Study Runner...")
    
    try:
        # Create ablation study runner
        config = {
            'parameter_ranges': {
                'k': [5, 10, 15],
                'epsilon': [0.05, 0.1, 0.15],
                'tau': [0.1, 0.2, 0.3]
            },
            'search_strategy': 'grid',
            'parallel_jobs': 1
        }
        
        runner = AblationStudyRunner(config)
        runner.initialize()
        
        print("  ✓ Ablation study runner initialized")
        
        # Test parameter sweep (small scale)
        print("\nTesting parameter sweep:")
        param_ranges = {
            'k': [5, 10],
            'epsilon': [0.1, 0.15]
        }
        
        sweep_results = runner.run_parameter_sweep(param_ranges)
        
        print(f"  Best parameters: {sweep_results.best_parameters}")
        print(f"  Best score: {sweep_results.best_score:.4f}")
        print(f"  Total combinations tested: {len(sweep_results.all_results)}")
        print("  ✓ Parameter sweep working")
        
        # Test component ablation (small scale)
        print("\nTesting component ablation:")
        components = {
            'boundary_detector': ['gradient_based', 'learned'],
            'manifold_learner': ['pca', 'umap'],
            'clustering_algorithm': ['kmeans', 'hdbscan']
        }
        
        ablation_results = runner.run_component_ablation(components)
        
        print(f"  Best combination: {ablation_results.best_combination}")
        print(f"  Component importance: {ablation_results.component_importance}")
        print(f"  Total combinations tested: {len(ablation_results.component_performance)}")
        print("  ✓ Component ablation working")
        
    except Exception as e:
        print(f"  ✗ Ablation study runner failed: {e}")


def run_all_tests():
    """Run all component ablation tests."""
    print("=" * 60)
    print("LBMD Component Ablation Testing")
    print("=" * 60)
    
    # Set up logging
    logging.basicConfig(level=logging.WARNING)  # Reduce log noise during testing
    
    # Run individual component tests
    test_boundary_detectors()
    test_manifold_learners()
    test_clustering_algorithms()
    
    # Run comparison tests
    test_component_comparison()
    
    # Run integrated ablation study test
    test_ablation_study_runner()
    
    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
"""
Multiple clustering algorithms for LBMD ablation studies.
"""

import numpy as np
import torch
from typing import Dict, Any, Optional, Tuple, List, Union
from abc import ABC, abstractmethod
import logging

# Clustering imports
from sklearn.cluster import KMeans, SpectralClustering, AgglomerativeClustering, DBSCAN
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, adjusted_rand_score, normalized_mutual_info_score
import hdbscan

from ..core.interfaces import ClusteringAlgorithmInterface


class BaseClusteringAlgorithm(ClusteringAlgorithmInterface):
    """Base class for clustering algorithms."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.clustering_model = None
        self.labels_ = None
        self.n_clusters_ = None
    
    @abstractmethod
    def fit_predict(self, features: Union[torch.Tensor, np.ndarray]) -> np.ndarray:
        """Fit the clustering algorithm and predict cluster labels."""
        pass
    
    @abstractmethod
    def predict(self, features: Union[torch.Tensor, np.ndarray]) -> np.ndarray:
        """Predict cluster labels for new features."""
        pass
    
    def _prepare_features(self, features: Union[torch.Tensor, np.ndarray]) -> np.ndarray:
        """Prepare features for clustering."""
        if isinstance(features, torch.Tensor):
            if features.dim() == 4:  # Batch dimension
                features = features.squeeze(0)
            features_np = features.detach().cpu().numpy()
        else:
            features_np = features
        
        # If features are spatial (3D: channels, height, width), flatten spatial dimensions
        if features_np.ndim == 3:
            features_flat = features_np.transpose(1, 2, 0).reshape(-1, features_np.shape[0])
        elif features_np.ndim == 2:
            features_flat = features_np
        else:
            raise ValueError(f"Unsupported feature shape: {features_np.shape}")
        
        return features_flat
    
    def get_cluster_centers(self) -> Optional[np.ndarray]:
        """Get cluster centers if available."""
        if hasattr(self.clustering_model, 'cluster_centers_'):
            return self.clustering_model.cluster_centers_
        elif hasattr(self.clustering_model, 'means_'):
            return self.clustering_model.means_
        else:
            return None


class KMeansClusterer(BaseClusteringAlgorithm):
    """K-Means clustering algorithm."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.n_clusters = self.config.get('n_clusters', 8)
        self.init = self.config.get('init', 'k-means++')
        self.n_init = self.config.get('n_init', 10)
        self.max_iter = self.config.get('max_iter', 300)
        self.tol = self.config.get('tol', 1e-4)
        self.random_state = self.config.get('random_state', 42)
    
    def fit_predict(self, features: Union[torch.Tensor, np.ndarray]) -> np.ndarray:
        """Fit K-Means and predict cluster labels."""
        # Prepare features
        features_flat = self._prepare_features(features)
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features_flat)
        
        # Initialize and fit K-Means
        self.clustering_model = KMeans(
            n_clusters=self.n_clusters,
            init=self.init,
            n_init=self.n_init,
            max_iter=self.max_iter,
            tol=self.tol,
            random_state=self.random_state
        )
        
        # Fit and predict
        self.labels_ = self.clustering_model.fit_predict(features_scaled)
        self.n_clusters_ = self.n_clusters
        self.is_fitted = True
        
        self.logger.info(f"K-Means clustering completed with {self.n_clusters} clusters")
        return self.labels_
    
    def predict(self, features: Union[torch.Tensor, np.ndarray]) -> np.ndarray:
        """Predict cluster labels for new features."""
        if not self.is_fitted:
            raise ValueError("K-Means model must be fitted before predict")
        
        # Prepare features
        features_flat = self._prepare_features(features)
        features_scaled = self.scaler.transform(features_flat)
        
        # Predict
        labels = self.clustering_model.predict(features_scaled)
        return labels


class HDBSCANClusterer(BaseClusteringAlgorithm):
    """HDBSCAN (Hierarchical Density-Based Spatial Clustering) algorithm."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.min_cluster_size = self.config.get('min_cluster_size', 5)
        self.min_samples = self.config.get('min_samples', None)
        self.metric = self.config.get('metric', 'euclidean')
        self.alpha = self.config.get('alpha', 1.0)
        self.cluster_selection_epsilon = self.config.get('cluster_selection_epsilon', 0.0)
        self.cluster_selection_method = self.config.get('cluster_selection_method', 'eom')
    
    def fit_predict(self, features: Union[torch.Tensor, np.ndarray]) -> np.ndarray:
        """Fit HDBSCAN and predict cluster labels."""
        # Prepare features
        features_flat = self._prepare_features(features)
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features_flat)
        
        # Initialize and fit HDBSCAN
        self.clustering_model = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=self.min_samples,
            metric=self.metric,
            alpha=self.alpha,
            cluster_selection_epsilon=self.cluster_selection_epsilon,
            cluster_selection_method=self.cluster_selection_method
        )
        
        # Fit and predict
        self.labels_ = self.clustering_model.fit_predict(features_scaled)
        self.n_clusters_ = len(set(self.labels_)) - (1 if -1 in self.labels_ else 0)
        self.is_fitted = True
        
        self.logger.info(f"HDBSCAN clustering completed with {self.n_clusters_} clusters "
                        f"and {np.sum(self.labels_ == -1)} noise points")
        return self.labels_
    
    def predict(self, features: Union[torch.Tensor, np.ndarray]) -> np.ndarray:
        """Predict cluster labels for new features."""
        if not self.is_fitted:
            raise ValueError("HDBSCAN model must be fitted before predict")
        
        # Prepare features
        features_flat = self._prepare_features(features)
        features_scaled = self.scaler.transform(features_flat)
        
        # HDBSCAN approximate predict
        labels, strengths = hdbscan.approximate_predict(self.clustering_model, features_scaled)
        return labels


class SpectralClusterer(BaseClusteringAlgorithm):
    """Spectral clustering algorithm."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.n_clusters = self.config.get('n_clusters', 8)
        self.eigen_solver = self.config.get('eigen_solver', None)
        self.n_components = self.config.get('n_components', None)
        self.random_state = self.config.get('random_state', 42)
        self.n_init = self.config.get('n_init', 10)
        self.gamma = self.config.get('gamma', 1.0)
        self.affinity = self.config.get('affinity', 'rbf')
        self.n_neighbors = self.config.get('n_neighbors', 10)
    
    def fit_predict(self, features: Union[torch.Tensor, np.ndarray]) -> np.ndarray:
        """Fit Spectral clustering and predict cluster labels."""
        # Prepare features
        features_flat = self._prepare_features(features)
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features_flat)
        
        # Initialize and fit Spectral clustering
        self.clustering_model = SpectralClustering(
            n_clusters=self.n_clusters,
            eigen_solver=self.eigen_solver,
            n_components=self.n_components,
            random_state=self.random_state,
            n_init=self.n_init,
            gamma=self.gamma,
            affinity=self.affinity,
            n_neighbors=self.n_neighbors
        )
        
        # Fit and predict
        self.labels_ = self.clustering_model.fit_predict(features_scaled)
        self.n_clusters_ = self.n_clusters
        self.is_fitted = True
        
        self.logger.info(f"Spectral clustering completed with {self.n_clusters} clusters")
        return self.labels_
    
    def predict(self, features: Union[torch.Tensor, np.ndarray]) -> np.ndarray:
        """Predict cluster labels for new features."""
        # Note: Spectral clustering doesn't support predict on new data
        self.logger.warning("Spectral clustering doesn't support predict on new data. Use fit_predict instead.")
        return self.fit_predict(features)


class GaussianMixtureClusterer(BaseClusteringAlgorithm):
    """Gaussian Mixture Model clustering algorithm."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.n_components = self.config.get('n_components', 8)
        self.covariance_type = self.config.get('covariance_type', 'full')
        self.tol = self.config.get('tol', 1e-3)
        self.reg_covar = self.config.get('reg_covar', 1e-6)
        self.max_iter = self.config.get('max_iter', 100)
        self.n_init = self.config.get('n_init', 1)
        self.init_params = self.config.get('init_params', 'kmeans')
        self.random_state = self.config.get('random_state', 42)
    
    def fit_predict(self, features: Union[torch.Tensor, np.ndarray]) -> np.ndarray:
        """Fit Gaussian Mixture Model and predict cluster labels."""
        # Prepare features
        features_flat = self._prepare_features(features)
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features_flat)
        
        # Initialize and fit GMM
        self.clustering_model = GaussianMixture(
            n_components=self.n_components,
            covariance_type=self.covariance_type,
            tol=self.tol,
            reg_covar=self.reg_covar,
            max_iter=self.max_iter,
            n_init=self.n_init,
            init_params=self.init_params,
            random_state=self.random_state
        )
        
        # Fit and predict
        self.clustering_model.fit(features_scaled)
        self.labels_ = self.clustering_model.predict(features_scaled)
        self.n_clusters_ = self.n_components
        self.is_fitted = True
        
        self.logger.info(f"Gaussian Mixture clustering completed with {self.n_components} components")
        return self.labels_
    
    def predict(self, features: Union[torch.Tensor, np.ndarray]) -> np.ndarray:
        """Predict cluster labels for new features."""
        if not self.is_fitted:
            raise ValueError("Gaussian Mixture model must be fitted before predict")
        
        # Prepare features
        features_flat = self._prepare_features(features)
        features_scaled = self.scaler.transform(features_flat)
        
        # Predict
        labels = self.clustering_model.predict(features_scaled)
        return labels
    
    def predict_proba(self, features: Union[torch.Tensor, np.ndarray]) -> np.ndarray:
        """Predict cluster probabilities for new features."""
        if not self.is_fitted:
            raise ValueError("Gaussian Mixture model must be fitted before predict")
        
        # Prepare features
        features_flat = self._prepare_features(features)
        features_scaled = self.scaler.transform(features_flat)
        
        # Predict probabilities
        probabilities = self.clustering_model.predict_proba(features_scaled)
        return probabilities


class AgglomerativeClusterer(BaseClusteringAlgorithm):
    """Agglomerative (Hierarchical) clustering algorithm."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.n_clusters = self.config.get('n_clusters', 8)
        self.affinity = self.config.get('affinity', 'euclidean')
        self.linkage = self.config.get('linkage', 'ward')
        self.distance_threshold = self.config.get('distance_threshold', None)
    
    def fit_predict(self, features: Union[torch.Tensor, np.ndarray]) -> np.ndarray:
        """Fit Agglomerative clustering and predict cluster labels."""
        # Prepare features
        features_flat = self._prepare_features(features)
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features_flat)
        
        # Initialize and fit Agglomerative clustering
        # Note: 'affinity' parameter was renamed to 'metric' in newer sklearn versions
        try:
            self.clustering_model = AgglomerativeClustering(
                n_clusters=self.n_clusters if self.distance_threshold is None else None,
                metric=self.affinity,
                linkage=self.linkage,
                distance_threshold=self.distance_threshold
            )
        except TypeError:
            # Fallback for older sklearn versions
            self.clustering_model = AgglomerativeClustering(
                n_clusters=self.n_clusters if self.distance_threshold is None else None,
                linkage=self.linkage,
                distance_threshold=self.distance_threshold
            )
        
        # Fit and predict
        self.labels_ = self.clustering_model.fit_predict(features_scaled)
        self.n_clusters_ = len(set(self.labels_))
        self.is_fitted = True
        
        self.logger.info(f"Agglomerative clustering completed with {self.n_clusters_} clusters")
        return self.labels_
    
    def predict(self, features: Union[torch.Tensor, np.ndarray]) -> np.ndarray:
        """Predict cluster labels for new features."""
        # Note: Agglomerative clustering doesn't support predict on new data
        self.logger.warning("Agglomerative clustering doesn't support predict on new data. Use fit_predict instead.")
        return self.fit_predict(features)


class DBSCANClusterer(BaseClusteringAlgorithm):
    """DBSCAN (Density-Based Spatial Clustering) algorithm."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.eps = self.config.get('eps', 0.5)
        self.min_samples = self.config.get('min_samples', 5)
        self.metric = self.config.get('metric', 'euclidean')
        self.algorithm = self.config.get('algorithm', 'auto')
        self.leaf_size = self.config.get('leaf_size', 30)
        self.n_jobs = self.config.get('n_jobs', -1)
    
    def fit_predict(self, features: Union[torch.Tensor, np.ndarray]) -> np.ndarray:
        """Fit DBSCAN and predict cluster labels."""
        # Prepare features
        features_flat = self._prepare_features(features)
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features_flat)
        
        # Initialize and fit DBSCAN
        self.clustering_model = DBSCAN(
            eps=self.eps,
            min_samples=self.min_samples,
            metric=self.metric,
            algorithm=self.algorithm,
            leaf_size=self.leaf_size,
            n_jobs=self.n_jobs
        )
        
        # Fit and predict
        self.labels_ = self.clustering_model.fit_predict(features_scaled)
        self.n_clusters_ = len(set(self.labels_)) - (1 if -1 in self.labels_ else 0)
        self.is_fitted = True
        
        self.logger.info(f"DBSCAN clustering completed with {self.n_clusters_} clusters "
                        f"and {np.sum(self.labels_ == -1)} noise points")
        return self.labels_
    
    def predict(self, features: Union[torch.Tensor, np.ndarray]) -> np.ndarray:
        """Predict cluster labels for new features."""
        # Note: DBSCAN doesn't support predict on new data
        self.logger.warning("DBSCAN doesn't support predict on new data. Use fit_predict instead.")
        return self.fit_predict(features)


class ClusteringAlgorithmFactory:
    """Factory for creating clustering algorithm instances."""
    
    _algorithms = {
        'kmeans': KMeansClusterer,
        'hdbscan': HDBSCANClusterer,
        'spectral': SpectralClusterer,
        'gaussian_mixture': GaussianMixtureClusterer,
        'agglomerative': AgglomerativeClusterer,
        'dbscan': DBSCANClusterer
    }
    
    @classmethod
    def create_algorithm(cls, algorithm_type: str, config: Optional[Dict[str, Any]] = None) -> BaseClusteringAlgorithm:
        """Create a clustering algorithm instance."""
        if algorithm_type not in cls._algorithms:
            raise ValueError(f"Unknown algorithm type: {algorithm_type}. "
                           f"Available types: {list(cls._algorithms.keys())}")
        
        algorithm_class = cls._algorithms[algorithm_type]
        return algorithm_class(config)
    
    @classmethod
    def get_available_algorithms(cls) -> List[str]:
        """Get list of available algorithm types."""
        return list(cls._algorithms.keys())
    
    @classmethod
    def register_algorithm(cls, name: str, algorithm_class: type) -> None:
        """Register a new algorithm type."""
        if not issubclass(algorithm_class, BaseClusteringAlgorithm):
            raise ValueError("Algorithm class must inherit from BaseClusteringAlgorithm")
        cls._algorithms[name] = algorithm_class


# Utility functions for clustering evaluation

def evaluate_clustering(features: np.ndarray, 
                       labels: np.ndarray,
                       ground_truth_labels: Optional[np.ndarray] = None) -> Dict[str, float]:
    """Evaluate clustering performance using various metrics."""
    metrics = {}
    
    # Internal validation metrics (don't require ground truth)
    if len(set(labels)) > 1:  # Need at least 2 clusters
        try:
            metrics['silhouette_score'] = silhouette_score(features, labels)
        except Exception as e:
            metrics['silhouette_score'] = np.nan
            logging.warning(f"Could not compute silhouette score: {e}")
    else:
        metrics['silhouette_score'] = np.nan
    
    # Compute inertia (within-cluster sum of squares) for K-means-like algorithms
    try:
        inertia = 0.0
        unique_labels = set(labels)
        for label in unique_labels:
            if label == -1:  # Skip noise points
                continue
            cluster_points = features[labels == label]
            if len(cluster_points) > 0:
                centroid = np.mean(cluster_points, axis=0)
                inertia += np.sum((cluster_points - centroid) ** 2)
        metrics['inertia'] = inertia
    except Exception:
        metrics['inertia'] = np.nan
    
    # External validation metrics (require ground truth)
    if ground_truth_labels is not None:
        try:
            metrics['adjusted_rand_score'] = adjusted_rand_score(ground_truth_labels, labels)
            metrics['normalized_mutual_info'] = normalized_mutual_info_score(ground_truth_labels, labels)
        except Exception as e:
            metrics['adjusted_rand_score'] = np.nan
            metrics['normalized_mutual_info'] = np.nan
            logging.warning(f"Could not compute external validation metrics: {e}")
    
    # Basic statistics
    metrics['n_clusters'] = len(set(labels)) - (1 if -1 in labels else 0)
    metrics['n_noise_points'] = np.sum(labels == -1) if -1 in labels else 0
    metrics['largest_cluster_size'] = np.max(np.bincount(labels[labels >= 0])) if np.any(labels >= 0) else 0
    metrics['smallest_cluster_size'] = np.min(np.bincount(labels[labels >= 0])) if np.any(labels >= 0) else 0
    
    return metrics


def compare_clustering_algorithms(features: Union[torch.Tensor, np.ndarray],
                                algorithms: List[str],
                                configs: Optional[Dict[str, Dict[str, Any]]] = None,
                                ground_truth_labels: Optional[np.ndarray] = None) -> Dict[str, Dict[str, Any]]:
    """Compare multiple clustering algorithms on the same features."""
    if configs is None:
        configs = {}
    
    results = {}
    
    # Prepare features once
    if isinstance(features, torch.Tensor):
        if features.dim() == 4:
            features = features.squeeze(0)
        features_np = features.detach().cpu().numpy()
    else:
        features_np = features
    
    if features_np.ndim == 3:
        features_flat = features_np.transpose(1, 2, 0).reshape(-1, features_np.shape[0])
    else:
        features_flat = features_np
    
    for algorithm in algorithms:
        try:
            # Create algorithm
            config = configs.get(algorithm, {})
            clusterer = ClusteringAlgorithmFactory.create_algorithm(algorithm, config)
            
            # Fit and predict
            labels = clusterer.fit_predict(features)
            
            # Evaluate clustering
            evaluation_metrics = evaluate_clustering(features_flat, labels, ground_truth_labels)
            
            results[algorithm] = {
                'labels': labels,
                'n_clusters': clusterer.n_clusters_,
                'evaluation_metrics': evaluation_metrics,
                'config': config,
                'success': True,
                'cluster_centers': clusterer.get_cluster_centers()
            }
            
        except Exception as e:
            results[algorithm] = {
                'labels': None,
                'n_clusters': None,
                'evaluation_metrics': None,
                'config': configs.get(algorithm, {}),
                'success': False,
                'error': str(e),
                'cluster_centers': None
            }
    
    return results


def find_optimal_clusters(features: Union[torch.Tensor, np.ndarray],
                         algorithm: str = 'kmeans',
                         k_range: Tuple[int, int] = (2, 15),
                         config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Find optimal number of clusters using elbow method and silhouette analysis."""
    if config is None:
        config = {}
    
    # Prepare features
    if isinstance(features, torch.Tensor):
        if features.dim() == 4:
            features = features.squeeze(0)
        features_np = features.detach().cpu().numpy()
    else:
        features_np = features
    
    if features_np.ndim == 3:
        features_flat = features_np.transpose(1, 2, 0).reshape(-1, features_np.shape[0])
    else:
        features_flat = features_np
    
    k_values = range(k_range[0], k_range[1] + 1)
    inertias = []
    silhouette_scores = []
    
    for k in k_values:
        try:
            # Update config with current k
            current_config = config.copy()
            if algorithm in ['kmeans', 'spectral', 'agglomerative']:
                current_config['n_clusters'] = k
            elif algorithm == 'gaussian_mixture':
                current_config['n_components'] = k
            else:
                # For density-based algorithms, skip this analysis
                continue
            
            # Create and fit algorithm
            clusterer = ClusteringAlgorithmFactory.create_algorithm(algorithm, current_config)
            labels = clusterer.fit_predict(features)
            
            # Compute metrics
            evaluation_metrics = evaluate_clustering(features_flat, labels)
            inertias.append(evaluation_metrics.get('inertia', np.nan))
            silhouette_scores.append(evaluation_metrics.get('silhouette_score', np.nan))
            
        except Exception as e:
            inertias.append(np.nan)
            silhouette_scores.append(np.nan)
    
    # Find optimal k using elbow method (for inertia)
    optimal_k_elbow = None
    if not all(np.isnan(inertias)):
        # Simple elbow detection: find point with maximum curvature
        valid_inertias = [(k, inertia) for k, inertia in zip(k_values, inertias) if not np.isnan(inertia)]
        if len(valid_inertias) >= 3:
            # Compute second derivative approximation
            second_derivatives = []
            for i in range(1, len(valid_inertias) - 1):
                d2 = valid_inertias[i-1][1] - 2*valid_inertias[i][1] + valid_inertias[i+1][1]
                second_derivatives.append((valid_inertias[i][0], d2))
            
            if second_derivatives:
                optimal_k_elbow = max(second_derivatives, key=lambda x: x[1])[0]
    
    # Find optimal k using silhouette score
    optimal_k_silhouette = None
    if not all(np.isnan(silhouette_scores)):
        valid_silhouettes = [(k, score) for k, score in zip(k_values, silhouette_scores) if not np.isnan(score)]
        if valid_silhouettes:
            optimal_k_silhouette = max(valid_silhouettes, key=lambda x: x[1])[0]
    
    return {
        'k_values': list(k_values),
        'inertias': inertias,
        'silhouette_scores': silhouette_scores,
        'optimal_k_elbow': optimal_k_elbow,
        'optimal_k_silhouette': optimal_k_silhouette,
        'algorithm': algorithm,
        'config': config
    }
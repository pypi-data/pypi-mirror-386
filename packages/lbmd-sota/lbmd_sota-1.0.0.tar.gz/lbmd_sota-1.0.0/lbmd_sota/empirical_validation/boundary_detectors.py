"""
Modular boundary detection algorithms for LBMD ablation studies.
"""

import numpy as np
import torch
import torch.nn.functional as F
from typing import Dict, Any, Optional, Tuple, List
from abc import ABC, abstractmethod
from scipy import ndimage
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
import logging

from ..core.interfaces import BoundaryDetectorInterface


class BaseBoundaryDetector(BoundaryDetectorInterface):
    """Base class for boundary detection algorithms."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
    
    @abstractmethod
    def detect_boundaries(self, features: torch.Tensor, **kwargs) -> np.ndarray:
        """Detect boundaries in feature space."""
        pass
    
    @abstractmethod
    def compute_boundary_scores(self, features: torch.Tensor) -> np.ndarray:
        """Compute boundary strength scores."""
        pass


class GradientBasedBoundaryDetector(BaseBoundaryDetector):
    """Gradient-based boundary detection using feature gradients."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.gradient_threshold = self.config.get('gradient_threshold', 0.1)
        self.smoothing_sigma = self.config.get('smoothing_sigma', 1.0)
        self.edge_method = self.config.get('edge_method', 'sobel')  # 'sobel', 'canny', 'laplacian'
    
    def detect_boundaries(self, features: torch.Tensor, **kwargs) -> np.ndarray:
        """Detect boundaries using gradient-based methods."""
        if features.dim() == 4:  # Batch dimension
            features = features.squeeze(0)
        
        # Convert to numpy for processing
        if isinstance(features, torch.Tensor):
            features_np = features.detach().cpu().numpy()
        else:
            features_np = features
        
        # Compute gradients for each channel
        boundaries = np.zeros(features_np.shape[1:])  # Spatial dimensions only
        
        for channel in range(features_np.shape[0]):
            channel_data = features_np[channel]
            
            if self.edge_method == 'sobel':
                grad_x = ndimage.sobel(channel_data, axis=0)
                grad_y = ndimage.sobel(channel_data, axis=1)
                gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            
            elif self.edge_method == 'laplacian':
                gradient_magnitude = np.abs(ndimage.laplace(channel_data))
            
            elif self.edge_method == 'canny':
                # Simplified Canny-like approach
                grad_x = ndimage.sobel(channel_data, axis=0)
                grad_y = ndimage.sobel(channel_data, axis=1)
                gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
                
                # Non-maximum suppression (simplified)
                gradient_magnitude = ndimage.maximum_filter(gradient_magnitude, size=3)
            
            else:
                raise ValueError(f"Unknown edge method: {self.edge_method}")
            
            # Smooth gradients
            if self.smoothing_sigma > 0:
                gradient_magnitude = ndimage.gaussian_filter(gradient_magnitude, 
                                                           sigma=self.smoothing_sigma)
            
            boundaries += gradient_magnitude
        
        # Normalize and threshold
        boundaries = boundaries / features_np.shape[0]  # Average across channels
        boundary_mask = boundaries > self.gradient_threshold
        
        return boundary_mask.astype(np.uint8)
    
    def compute_boundary_scores(self, features: torch.Tensor) -> np.ndarray:
        """Compute continuous boundary strength scores."""
        if features.dim() == 4:  # Batch dimension
            features = features.squeeze(0)
        
        # Convert to numpy for processing
        if isinstance(features, torch.Tensor):
            features_np = features.detach().cpu().numpy()
        else:
            features_np = features
        
        # Compute gradient magnitudes
        boundary_scores = np.zeros(features_np.shape[1:])
        
        for channel in range(features_np.shape[0]):
            channel_data = features_np[channel]
            
            grad_x = ndimage.sobel(channel_data, axis=0)
            grad_y = ndimage.sobel(channel_data, axis=1)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            
            if self.smoothing_sigma > 0:
                gradient_magnitude = ndimage.gaussian_filter(gradient_magnitude, 
                                                           sigma=self.smoothing_sigma)
            
            boundary_scores += gradient_magnitude
        
        # Normalize
        boundary_scores = boundary_scores / features_np.shape[0]
        
        # Normalize to [0, 1] range
        if boundary_scores.max() > 0:
            boundary_scores = boundary_scores / boundary_scores.max()
        
        return boundary_scores


class LearnedBoundaryDetector(BaseBoundaryDetector):
    """Learned boundary detection using neural network-based approaches."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.model_type = self.config.get('model_type', 'isolation_forest')  # 'isolation_forest', 'autoencoder'
        self.contamination = self.config.get('contamination', 0.1)
        self.n_estimators = self.config.get('n_estimators', 100)
        self.random_state = self.config.get('random_state', 42)
        
        self.boundary_model = None
        self.scaler = StandardScaler()
        self.is_fitted = False
    
    def detect_boundaries(self, features: torch.Tensor, **kwargs) -> np.ndarray:
        """Detect boundaries using learned models."""
        if not self.is_fitted:
            self._fit_boundary_model(features)
        
        # Prepare features for model
        features_flat = self._prepare_features(features)
        
        # Predict boundaries
        if self.model_type == 'isolation_forest':
            anomaly_scores = self.boundary_model.decision_function(features_flat)
            # Convert to boundary mask (anomalies are potential boundaries)
            boundary_mask = anomaly_scores < 0  # Negative scores indicate anomalies
        else:
            raise NotImplementedError(f"Model type {self.model_type} not implemented")
        
        # Reshape back to spatial dimensions
        original_shape = features.shape[2:] if features.dim() == 4 else features.shape[1:]
        boundary_mask = boundary_mask.reshape(original_shape)
        
        return boundary_mask.astype(np.uint8)
    
    def compute_boundary_scores(self, features: torch.Tensor) -> np.ndarray:
        """Compute continuous boundary strength scores using learned model."""
        if not self.is_fitted:
            self._fit_boundary_model(features)
        
        # Prepare features for model
        features_flat = self._prepare_features(features)
        
        # Get continuous scores
        if self.model_type == 'isolation_forest':
            scores = self.boundary_model.decision_function(features_flat)
            # Convert to boundary strength (higher values = stronger boundaries)
            boundary_scores = -scores  # Invert so negative anomaly scores become positive boundary scores
            boundary_scores = np.maximum(boundary_scores, 0)  # Clip negative values
        else:
            raise NotImplementedError(f"Model type {self.model_type} not implemented")
        
        # Normalize to [0, 1] range
        if boundary_scores.max() > 0:
            boundary_scores = boundary_scores / boundary_scores.max()
        
        # Reshape back to spatial dimensions
        original_shape = features.shape[2:] if features.dim() == 4 else features.shape[1:]
        boundary_scores = boundary_scores.reshape(original_shape)
        
        return boundary_scores
    
    def _prepare_features(self, features: torch.Tensor) -> np.ndarray:
        """Prepare features for machine learning model."""
        if features.dim() == 4:  # Batch dimension
            features = features.squeeze(0)
        
        # Convert to numpy
        if isinstance(features, torch.Tensor):
            features_np = features.detach().cpu().numpy()
        else:
            features_np = features
        
        # Flatten spatial dimensions, keep channel dimension
        # Shape: (channels, height, width) -> (height*width, channels)
        features_flat = features_np.transpose(1, 2, 0).reshape(-1, features_np.shape[0])
        
        # Scale features
        features_scaled = self.scaler.transform(features_flat)
        
        return features_scaled
    
    def _fit_boundary_model(self, features: torch.Tensor) -> None:
        """Fit the boundary detection model."""
        # Prepare features
        features_flat = self._prepare_features_for_fitting(features)
        
        # Fit scaler
        self.scaler.fit(features_flat)
        features_scaled = self.scaler.transform(features_flat)
        
        # Fit boundary model
        if self.model_type == 'isolation_forest':
            self.boundary_model = IsolationForest(
                contamination=self.contamination,
                n_estimators=self.n_estimators,
                random_state=self.random_state,
                n_jobs=-1
            )
            self.boundary_model.fit(features_scaled)
        else:
            raise NotImplementedError(f"Model type {self.model_type} not implemented")
        
        self.is_fitted = True
        self.logger.info(f"Fitted {self.model_type} boundary detector")
    
    def _prepare_features_for_fitting(self, features: torch.Tensor) -> np.ndarray:
        """Prepare features for model fitting (same as _prepare_features but without scaling)."""
        if features.dim() == 4:  # Batch dimension
            features = features.squeeze(0)
        
        # Convert to numpy
        if isinstance(features, torch.Tensor):
            features_np = features.detach().cpu().numpy()
        else:
            features_np = features
        
        # Flatten spatial dimensions, keep channel dimension
        features_flat = features_np.transpose(1, 2, 0).reshape(-1, features_np.shape[0])
        
        return features_flat


class HybridBoundaryDetector(BaseBoundaryDetector):
    """Hybrid boundary detection combining gradient-based and learned approaches."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.gradient_weight = self.config.get('gradient_weight', 0.6)
        self.learned_weight = self.config.get('learned_weight', 0.4)
        self.fusion_method = self.config.get('fusion_method', 'weighted_average')  # 'weighted_average', 'max', 'product'
        
        # Initialize component detectors
        gradient_config = self.config.get('gradient_config', {})
        learned_config = self.config.get('learned_config', {})
        
        self.gradient_detector = GradientBasedBoundaryDetector(gradient_config)
        self.learned_detector = LearnedBoundaryDetector(learned_config)
    
    def detect_boundaries(self, features: torch.Tensor, **kwargs) -> np.ndarray:
        """Detect boundaries using hybrid approach."""
        # Get boundary scores from both methods
        gradient_scores = self.gradient_detector.compute_boundary_scores(features)
        learned_scores = self.learned_detector.compute_boundary_scores(features)
        
        # Fuse the scores
        if self.fusion_method == 'weighted_average':
            combined_scores = (self.gradient_weight * gradient_scores + 
                             self.learned_weight * learned_scores)
        elif self.fusion_method == 'max':
            combined_scores = np.maximum(gradient_scores, learned_scores)
        elif self.fusion_method == 'product':
            combined_scores = gradient_scores * learned_scores
        else:
            raise ValueError(f"Unknown fusion method: {self.fusion_method}")
        
        # Threshold to get binary mask
        threshold = self.config.get('boundary_threshold', 0.5)
        boundary_mask = combined_scores > threshold
        
        return boundary_mask.astype(np.uint8)
    
    def compute_boundary_scores(self, features: torch.Tensor) -> np.ndarray:
        """Compute continuous boundary strength scores using hybrid approach."""
        # Get boundary scores from both methods
        gradient_scores = self.gradient_detector.compute_boundary_scores(features)
        learned_scores = self.learned_detector.compute_boundary_scores(features)
        
        # Fuse the scores
        if self.fusion_method == 'weighted_average':
            combined_scores = (self.gradient_weight * gradient_scores + 
                             self.learned_weight * learned_scores)
        elif self.fusion_method == 'max':
            combined_scores = np.maximum(gradient_scores, learned_scores)
        elif self.fusion_method == 'product':
            combined_scores = gradient_scores * learned_scores
        else:
            raise ValueError(f"Unknown fusion method: {self.fusion_method}")
        
        return combined_scores


class BoundaryDetectorFactory:
    """Factory for creating boundary detector instances."""
    
    _detectors = {
        'gradient_based': GradientBasedBoundaryDetector,
        'learned': LearnedBoundaryDetector,
        'hybrid': HybridBoundaryDetector
    }
    
    @classmethod
    def create_detector(cls, detector_type: str, config: Optional[Dict[str, Any]] = None) -> BaseBoundaryDetector:
        """Create a boundary detector instance."""
        if detector_type not in cls._detectors:
            raise ValueError(f"Unknown detector type: {detector_type}. "
                           f"Available types: {list(cls._detectors.keys())}")
        
        detector_class = cls._detectors[detector_type]
        return detector_class(config)
    
    @classmethod
    def get_available_detectors(cls) -> List[str]:
        """Get list of available detector types."""
        return list(cls._detectors.keys())
    
    @classmethod
    def register_detector(cls, name: str, detector_class: type) -> None:
        """Register a new detector type."""
        if not issubclass(detector_class, BaseBoundaryDetector):
            raise ValueError("Detector class must inherit from BaseBoundaryDetector")
        cls._detectors[name] = detector_class


# Utility functions for boundary detection evaluation

def evaluate_boundary_detection(predicted_boundaries: np.ndarray, 
                              ground_truth_boundaries: np.ndarray) -> Dict[str, float]:
    """Evaluate boundary detection performance."""
    # Flatten arrays for evaluation
    pred_flat = predicted_boundaries.flatten()
    gt_flat = ground_truth_boundaries.flatten()
    
    # Compute metrics
    true_positives = np.sum((pred_flat == 1) & (gt_flat == 1))
    false_positives = np.sum((pred_flat == 1) & (gt_flat == 0))
    false_negatives = np.sum((pred_flat == 0) & (gt_flat == 1))
    true_negatives = np.sum((pred_flat == 0) & (gt_flat == 0))
    
    # Calculate metrics
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    accuracy = (true_positives + true_negatives) / len(pred_flat)
    
    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'accuracy': accuracy,
        'true_positives': true_positives,
        'false_positives': false_positives,
        'false_negatives': false_negatives,
        'true_negatives': true_negatives
    }


def compute_boundary_consistency(boundaries1: np.ndarray, boundaries2: np.ndarray) -> float:
    """Compute consistency between two boundary detection results."""
    # Jaccard similarity
    intersection = np.sum((boundaries1 == 1) & (boundaries2 == 1))
    union = np.sum((boundaries1 == 1) | (boundaries2 == 1))
    
    jaccard = intersection / union if union > 0 else 1.0
    return jaccard


def compare_boundary_methods(features: torch.Tensor, 
                           methods: List[str],
                           configs: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Dict[str, Any]]:
    """Compare multiple boundary detection methods on the same features."""
    if configs is None:
        configs = {}
    
    results = {}
    
    for method in methods:
        try:
            # Create detector
            config = configs.get(method, {})
            detector = BoundaryDetectorFactory.create_detector(method, config)
            
            # Detect boundaries and compute scores
            boundaries = detector.detect_boundaries(features)
            boundary_scores = detector.compute_boundary_scores(features)
            
            results[method] = {
                'boundaries': boundaries,
                'boundary_scores': boundary_scores,
                'config': config,
                'success': True,
                'n_boundary_pixels': np.sum(boundaries),
                'mean_boundary_score': np.mean(boundary_scores),
                'max_boundary_score': np.max(boundary_scores)
            }
            
        except Exception as e:
            results[method] = {
                'boundaries': None,
                'boundary_scores': None,
                'config': configs.get(method, {}),
                'success': False,
                'error': str(e)
            }
    
    return results
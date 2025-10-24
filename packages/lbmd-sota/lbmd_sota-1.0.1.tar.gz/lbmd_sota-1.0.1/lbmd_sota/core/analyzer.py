"""
Core LBMD Analyzer for direct model analysis.
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Any, Optional, Union
import logging
from pathlib import Path

from .interfaces import ModelInterface
from .data_models import LBMDResults
from ..empirical_validation.boundary_detectors import GradientBasedBoundaryDetector
from ..empirical_validation.manifold_learners import UMAPLearner


class LBMDAnalyzer:
    """
    Core LBMD analyzer for direct model analysis.
    
    This class provides a simplified interface for analyzing neural networks
    using Latent Boundary Manifold Decomposition techniques.
    """
    
    def __init__(
        self,
        model: nn.Module,
        target_layers: List[str],
        device: Optional[torch.device] = None,
        k_neurons: int = 20,
        epsilon: float = 0.1,
        tau: float = 0.5,
        manifold_method: str = 'umap'
    ):
        """
        Initialize LBMD analyzer.
        
        Args:
            model: PyTorch model to analyze
            target_layers: List of layer names to analyze
            device: Device to run analysis on
            k_neurons: Number of top neurons to analyze
            epsilon: Boundary detection threshold
            tau: Manifold separation threshold
            manifold_method: Manifold learning method ('umap', 'tsne', 'pca')
        """
        self.model = model
        self.target_layers = target_layers
        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # LBMD parameters
        self.k_neurons = k_neurons
        self.epsilon = epsilon
        self.tau = tau
        self.manifold_method = manifold_method
        
        # Initialize components
        self.boundary_detector = GradientBasedBoundaryDetector({
            'epsilon': epsilon,
            'k_neurons': k_neurons
        })
        
        self.manifold_learner = UMAPLearner({
            'n_components': 2,
            'n_neighbors': 15,
            'min_dist': 0.1
        })
        
        # Hooks for feature extraction
        self.hooks = []
        self.features = {}
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def _register_hooks(self):
        """Register forward hooks for feature extraction."""
        self.features = {}
        
        def get_activation(name):
            def hook(model, input, output):
                if isinstance(output, torch.Tensor):
                    self.features[name] = output.detach()
                elif isinstance(output, (list, tuple)):
                    self.features[name] = output[0].detach() if len(output) > 0 else None
            return hook
        
        # Register hooks for target layers
        for layer_name in self.target_layers:
            try:
                layer = self._get_layer_by_name(layer_name)
                if layer is not None:
                    hook = layer.register_forward_hook(get_activation(layer_name))
                    self.hooks.append(hook)
                    self.logger.debug(f"Registered hook for layer: {layer_name}")
            except Exception as e:
                self.logger.warning(f"Could not register hook for layer {layer_name}: {e}")
    
    def _get_layer_by_name(self, layer_name: str) -> Optional[nn.Module]:
        """Get layer by name from model."""
        try:
            # Handle nested layer names (e.g., 'features.0.conv1')
            parts = layer_name.split('.')
            layer = self.model
            
            for part in parts:
                if hasattr(layer, part):
                    layer = getattr(layer, part)
                elif part.isdigit() and hasattr(layer, '__getitem__'):
                    layer = layer[int(part)]
                else:
                    return None
            
            return layer
        except Exception:
            return None
    
    def _remove_hooks(self):
        """Remove all registered hooks."""
        for hook in self.hooks:
            hook.remove()
        self.hooks = []
    
    def analyze(self, input_data: torch.Tensor) -> Dict[str, Any]:
        """
        Perform LBMD analysis on input data.
        
        Args:
            input_data: Input tensor to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Ensure model is in eval mode
            self.model.eval()
            
            # Move input to device
            input_data = input_data.to(self.device)
            
            # Register hooks
            self._register_hooks()
            
            # Forward pass to extract features
            with torch.no_grad():
                _ = self.model(input_data)
            
            # Analyze each layer
            results = {
                'manifold_analysis': {},
                'boundary_analysis': {},
                'summary_metrics': {}
            }
            
            for layer_name in self.target_layers:
                if layer_name in self.features:
                    layer_results = self._analyze_layer(
                        layer_name, 
                        self.features[layer_name]
                    )
                    results['manifold_analysis'][layer_name] = layer_results
            
            # Compute summary metrics
            results['summary_metrics'] = self._compute_summary_metrics(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            raise
        finally:
            self._remove_hooks()
    
    def _analyze_layer(self, layer_name: str, features: torch.Tensor) -> Dict[str, Any]:
        """Analyze a single layer's features."""
        try:
            # Reshape features for analysis
            batch_size = features.shape[0]
            
            # Handle different feature shapes
            if len(features.shape) == 4:  # Conv features (B, C, H, W)
                features_flat = features.view(batch_size, features.shape[1], -1)
                features_flat = features_flat.permute(0, 2, 1)  # (B, H*W, C)
                features_2d = features_flat.reshape(-1, features.shape[1])
            elif len(features.shape) == 3:  # Transformer features (B, N, C)
                features_2d = features.reshape(-1, features.shape[-1])
            elif len(features.shape) == 2:  # FC features (B, C)
                features_2d = features
            else:
                self.logger.warning(f"Unsupported feature shape for {layer_name}: {features.shape}")
                return {}
            
            # Convert to numpy for analysis
            features_np = features_2d.cpu().numpy()
            
            # Simple boundary detection for different feature shapes
            try:
                if len(features.shape) >= 3:  # Spatial features
                    boundary_mask = self.boundary_detector.detect_boundaries(features_2d)
                    boundary_indices = np.where(boundary_mask.flatten())[0].tolist()
                else:  # 1D features - use statistical outliers as boundaries
                    # Use standard deviation to find boundary points
                    feature_std = np.std(features_np, axis=1)
                    threshold = np.mean(feature_std) + 2 * np.std(feature_std)
                    boundary_indices = np.where(feature_std > threshold)[0].tolist()
                
                boundary_info = {
                    'boundary_indices': boundary_indices,
                    'boundary_scores': [1.0] * len(boundary_indices)
                }
            except Exception as e:
                self.logger.warning(f"Boundary detection failed for {layer_name}: {e}")
                boundary_info = {
                    'boundary_indices': [],
                    'boundary_scores': []
                }
            
            # Manifold learning with error handling
            try:
                features_tensor = torch.from_numpy(features_np).float()
                manifold_embedding = self.manifold_learner.fit_transform(features_tensor)
            except Exception as e:
                self.logger.warning(f"Manifold learning failed for {layer_name}: {e}")
                manifold_embedding = None
            
            # Compute metrics
            manifold_dimension = self._estimate_intrinsic_dimension(features_np)
            boundary_strength = self._compute_boundary_strength(boundary_info)
            
            return {
                'layer_name': layer_name,
                'feature_shape': list(features.shape),
                'manifold_dimension': manifold_dimension,
                'boundary_strength': boundary_strength,
                'manifold_embedding': manifold_embedding.tolist() if manifold_embedding is not None else None,
                'boundary_points': boundary_info.get('boundary_indices', []),
                'num_boundaries': len(boundary_info.get('boundary_indices', [])),
                'analysis_successful': True
            }
            
        except Exception as e:
            self.logger.error(f"Layer analysis failed for {layer_name}: {e}")
            return {
                'layer_name': layer_name,
                'analysis_successful': False,
                'error': str(e)
            }
    
    def _estimate_intrinsic_dimension(self, features: np.ndarray) -> float:
        """Estimate intrinsic dimension of feature manifold."""
        try:
            # Simple PCA-based dimension estimation
            from sklearn.decomposition import PCA
            
            # Subsample if too many points
            if features.shape[0] > 1000:
                indices = np.random.choice(features.shape[0], 1000, replace=False)
                features_sub = features[indices]
            else:
                features_sub = features
            
            pca = PCA()
            pca.fit(features_sub)
            
            # Find number of components explaining 95% variance
            cumsum = np.cumsum(pca.explained_variance_ratio_)
            dim_95 = np.argmax(cumsum >= 0.95) + 1
            
            return float(dim_95)
            
        except Exception as e:
            self.logger.warning(f"Dimension estimation failed: {e}")
            return float(features.shape[1])  # Fallback to ambient dimension
    
    def _compute_boundary_strength(self, boundary_info: Dict[str, Any]) -> float:
        """Compute overall boundary strength metric."""
        try:
            boundary_indices = boundary_info.get('boundary_indices', [])
            boundary_scores = boundary_info.get('boundary_scores', [])
            
            if not boundary_scores:
                return 0.0
            
            # Average boundary strength
            return float(np.mean(boundary_scores))
            
        except Exception:
            return 0.0
    
    def _compute_summary_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Compute summary metrics across all layers."""
        manifold_data = results.get('manifold_analysis', {})
        
        if not manifold_data:
            return {}
        
        # Collect metrics
        dimensions = []
        strengths = []
        successful_layers = 0
        
        for layer_name, layer_data in manifold_data.items():
            if layer_data.get('analysis_successful', False):
                successful_layers += 1
                if 'manifold_dimension' in layer_data:
                    dimensions.append(layer_data['manifold_dimension'])
                if 'boundary_strength' in layer_data:
                    strengths.append(layer_data['boundary_strength'])
        
        summary = {
            'total_layers_analyzed': len(manifold_data),
            'successful_layers': successful_layers,
            'success_rate': successful_layers / len(manifold_data) if manifold_data else 0.0
        }
        
        if dimensions:
            summary.update({
                'avg_manifold_dimension': float(np.mean(dimensions)),
                'max_manifold_dimension': float(np.max(dimensions)),
                'min_manifold_dimension': float(np.min(dimensions))
            })
        
        if strengths:
            summary.update({
                'avg_boundary_strength': float(np.mean(strengths)),
                'max_boundary_strength': float(np.max(strengths)),
                'min_boundary_strength': float(np.min(strengths))
            })
        
        return summary
    
    def __del__(self):
        """Cleanup hooks on deletion."""
        self._remove_hooks()
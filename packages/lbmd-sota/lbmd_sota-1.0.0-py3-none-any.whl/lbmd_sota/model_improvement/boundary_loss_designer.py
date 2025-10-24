"""
Boundary loss designer for creating custom loss functions.
"""

from typing import Dict, List, Any, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from ..core.interfaces import BaseComponent
from ..core.data_models import BoundaryMetrics, LBMDResults


class BoundaryLossDesigner(BaseComponent):
    """Creates custom loss functions that incorporate boundary clarity metrics."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.boundary_weight = config.get('boundary_weight', 1.0)
        self.clarity_weight = config.get('clarity_weight', 0.5)
        self.separation_weight = config.get('separation_weight', 0.3)
        self.adaptive_weighting = config.get('adaptive_weighting', True)
        
    def initialize(self) -> None:
        """Initialize the boundary loss designer."""
        self._loss_components = self._initialize_loss_components()
        self._initialized = True
    
    def _initialize_loss_components(self) -> Dict[str, nn.Module]:
        """Initialize different loss components."""
        return {
            'boundary_clarity': BoundaryClarityLoss(),
            'manifold_separation': ManifoldSeparationLoss(),
            'transition_consistency': TransitionConsistencyLoss(),
            'topological_preservation': TopologicalPreservationLoss()
        }
    
    def compute_adaptive_weights(self, boundary_metrics: BoundaryMetrics, 
                               lbmd_results: Optional[LBMDResults] = None) -> Dict[str, float]:
        """Compute adaptive weights based on current boundary performance."""
        weights = {}
        
        # Base weights
        base_boundary_weight = self.boundary_weight
        base_clarity_weight = self.clarity_weight
        base_separation_weight = self.separation_weight
        
        if self.adaptive_weighting and boundary_metrics:
            # Increase boundary weight if boundary strength is low
            if boundary_metrics.boundary_strength < 0.5:
                weights['boundary_clarity'] = base_boundary_weight * 2.0
            else:
                weights['boundary_clarity'] = base_boundary_weight
            
            # Increase clarity weight if transition clarity is low
            if boundary_metrics.transition_clarity < 0.6:
                weights['transition_consistency'] = base_clarity_weight * 1.5
            else:
                weights['transition_consistency'] = base_clarity_weight
            
            # Increase separation weight if manifold separation is low
            if boundary_metrics.manifold_separation < 0.7:
                weights['manifold_separation'] = base_separation_weight * 1.8
            else:
                weights['manifold_separation'] = base_separation_weight
            
            # Topological preservation weight based on complexity
            if boundary_metrics.topological_persistence < 0.5:
                weights['topological_preservation'] = 0.2
            else:
                weights['topological_preservation'] = 0.1
        else:
            # Use fixed weights
            weights = {
                'boundary_clarity': base_boundary_weight,
                'transition_consistency': base_clarity_weight,
                'manifold_separation': base_separation_weight,
                'topological_preservation': 0.1
            }
        
        return weights
    
    def design_boundary_loss(self, boundary_metrics: BoundaryMetrics, 
                           lbmd_results: Optional[LBMDResults] = None) -> nn.Module:
        """Design custom loss function based on boundary metrics."""
        if not self._initialized:
            self.initialize()
        
        # Compute adaptive weights
        weights = self.compute_adaptive_weights(boundary_metrics, lbmd_results)
        
        # Create composite boundary loss
        return CompositeBoundaryLoss(
            loss_components=self._loss_components,
            weights=weights,
            boundary_metrics=boundary_metrics
        )
    
    def create_boundary_clarity_loss(self, target_clarity: float = 0.8) -> nn.Module:
        """Create a loss function specifically for boundary clarity."""
        return BoundaryClarityLoss(target_clarity=target_clarity)
    
    def create_manifold_separation_loss(self, margin: float = 1.0) -> nn.Module:
        """Create a loss function for manifold separation enhancement."""
        return ManifoldSeparationLoss(margin=margin)
    
    def create_adaptive_boundary_loss(self, adaptation_rate: float = 0.1) -> nn.Module:
        """Create an adaptive boundary loss that adjusts during training."""
        return AdaptiveBoundaryLoss(
            loss_components=self._loss_components,
            adaptation_rate=adaptation_rate
        )


class BoundaryClarityLoss(nn.Module):
    """Loss function for improving boundary clarity using LBMD metrics."""
    
    def __init__(self, target_clarity: float = 0.8, smoothness_weight: float = 0.1):
        super().__init__()
        self.target_clarity = target_clarity
        self.smoothness_weight = smoothness_weight
        
    def forward(self, predictions: torch.Tensor, targets: torch.Tensor, 
                boundary_scores: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Compute boundary clarity loss.
        
        Args:
            predictions: Model predictions [B, C, H, W]
            targets: Ground truth masks [B, C, H, W]
            boundary_scores: LBMD boundary scores [B, H, W]
        """
        # Standard segmentation loss
        base_loss = F.binary_cross_entropy_with_logits(predictions, targets)
        
        if boundary_scores is None:
            return base_loss
        
        # Compute boundary regions
        boundary_mask = (boundary_scores > 0.5).float()
        
        # Enhanced loss for boundary regions
        boundary_predictions = predictions * boundary_mask.unsqueeze(1)
        boundary_targets = targets * boundary_mask.unsqueeze(1)
        
        boundary_loss = F.binary_cross_entropy_with_logits(
            boundary_predictions, boundary_targets, reduction='none'
        )
        
        # Weight by boundary strength
        weighted_boundary_loss = boundary_loss * boundary_scores.unsqueeze(1)
        boundary_loss = weighted_boundary_loss.mean()
        
        # Smoothness regularization for boundary regions
        if self.smoothness_weight > 0:
            smoothness_loss = self._compute_smoothness_loss(predictions, boundary_mask)
            boundary_loss += self.smoothness_weight * smoothness_loss
        
        return base_loss + boundary_loss
    
    def _compute_smoothness_loss(self, predictions: torch.Tensor, 
                               boundary_mask: torch.Tensor) -> torch.Tensor:
        """Compute smoothness loss for boundary regions."""
        # Compute gradients
        grad_x = torch.abs(predictions[:, :, :, 1:] - predictions[:, :, :, :-1])
        grad_y = torch.abs(predictions[:, :, 1:, :] - predictions[:, :, :-1, :])
        
        # Apply boundary mask
        boundary_mask_x = boundary_mask[:, :, 1:] * boundary_mask[:, :, :-1]
        boundary_mask_y = boundary_mask[:, 1:, :] * boundary_mask[:, :-1, :]
        
        # Weighted smoothness loss
        smoothness_x = (grad_x * boundary_mask_x.unsqueeze(1)).mean()
        smoothness_y = (grad_y * boundary_mask_y.unsqueeze(1)).mean()
        
        return smoothness_x + smoothness_y


class ManifoldSeparationLoss(nn.Module):
    """Loss function for enhancing manifold separation."""
    
    def __init__(self, margin: float = 1.0, temperature: float = 0.1):
        super().__init__()
        self.margin = margin
        self.temperature = temperature
        
    def forward(self, features: torch.Tensor, cluster_labels: torch.Tensor,
                manifold_coords: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Compute manifold separation loss.
        
        Args:
            features: Feature representations [B, D]
            cluster_labels: Cluster assignments [B]
            manifold_coords: Manifold coordinates [B, 2]
        """
        if manifold_coords is not None:
            # Use manifold coordinates for separation
            return self._manifold_separation_loss(manifold_coords, cluster_labels)
        else:
            # Use feature space for separation
            return self._feature_separation_loss(features, cluster_labels)
    
    def _manifold_separation_loss(self, manifold_coords: torch.Tensor, 
                                cluster_labels: torch.Tensor) -> torch.Tensor:
        """Compute separation loss in manifold space."""
        unique_labels = torch.unique(cluster_labels)
        total_loss = 0.0
        num_pairs = 0
        
        for i, label_i in enumerate(unique_labels):
            mask_i = (cluster_labels == label_i)
            coords_i = manifold_coords[mask_i]
            
            for j, label_j in enumerate(unique_labels):
                if i >= j:
                    continue
                    
                mask_j = (cluster_labels == label_j)
                coords_j = manifold_coords[mask_j]
                
                # Compute inter-cluster distances
                distances = torch.cdist(coords_i, coords_j)
                min_distance = torch.min(distances)
                
                # Encourage separation with margin
                separation_loss = F.relu(self.margin - min_distance)
                total_loss += separation_loss
                num_pairs += 1
        
        return total_loss / max(num_pairs, 1)
    
    def _feature_separation_loss(self, features: torch.Tensor, 
                               cluster_labels: torch.Tensor) -> torch.Tensor:
        """Compute separation loss in feature space."""
        unique_labels = torch.unique(cluster_labels)
        
        # Compute cluster centroids
        centroids = []
        for label in unique_labels:
            mask = (cluster_labels == label)
            centroid = features[mask].mean(dim=0)
            centroids.append(centroid)
        
        centroids = torch.stack(centroids)
        
        # Compute inter-centroid distances
        centroid_distances = torch.cdist(centroids, centroids)
        
        # Remove diagonal (self-distances)
        mask = ~torch.eye(len(centroids), dtype=torch.bool, device=centroids.device)
        inter_distances = centroid_distances[mask]
        
        # Encourage large inter-cluster distances
        separation_loss = F.relu(self.margin - inter_distances).mean()
        
        return separation_loss


class TransitionConsistencyLoss(nn.Module):
    """Loss function for maintaining consistent transitions between clusters."""
    
    def __init__(self, consistency_weight: float = 1.0):
        super().__init__()
        self.consistency_weight = consistency_weight
        
    def forward(self, predictions: torch.Tensor, transition_strengths: Dict[Tuple[int, int], float],
                cluster_assignments: torch.Tensor) -> torch.Tensor:
        """
        Compute transition consistency loss.
        
        Args:
            predictions: Model predictions [B, C, H, W]
            transition_strengths: Transition strengths between clusters
            cluster_assignments: Cluster assignments [B, H, W]
        """
        total_loss = 0.0
        num_transitions = 0
        
        for (cluster_i, cluster_j), strength in transition_strengths.items():
            # Find transition regions
            mask_i = (cluster_assignments == cluster_i)
            mask_j = (cluster_assignments == cluster_j)
            
            # Compute transition boundary
            transition_mask = self._compute_transition_boundary(mask_i, mask_j)
            
            if transition_mask.sum() > 0:
                # Compute prediction consistency in transition regions
                transition_preds = predictions * transition_mask.unsqueeze(1)
                consistency_loss = self._compute_consistency_loss(transition_preds, strength)
                total_loss += consistency_loss
                num_transitions += 1
        
        return total_loss / max(num_transitions, 1)
    
    def _compute_transition_boundary(self, mask_i: torch.Tensor, 
                                   mask_j: torch.Tensor) -> torch.Tensor:
        """Compute boundary between two cluster regions."""
        # Dilate masks to find boundaries
        kernel = torch.ones(3, 3, device=mask_i.device)
        
        mask_i_dilated = F.conv2d(mask_i.float().unsqueeze(1), 
                                 kernel.unsqueeze(0).unsqueeze(0), 
                                 padding=1) > 0
        mask_j_dilated = F.conv2d(mask_j.float().unsqueeze(1), 
                                 kernel.unsqueeze(0).unsqueeze(0), 
                                 padding=1) > 0
        
        # Transition boundary is where dilated masks overlap
        transition_boundary = mask_i_dilated.squeeze(1) & mask_j_dilated.squeeze(1)
        
        return transition_boundary
    
    def _compute_consistency_loss(self, transition_predictions: torch.Tensor, 
                                strength: float) -> torch.Tensor:
        """Compute consistency loss for transition regions."""
        # Compute gradient magnitude in transition regions
        grad_x = torch.abs(transition_predictions[:, :, :, 1:] - 
                          transition_predictions[:, :, :, :-1])
        grad_y = torch.abs(transition_predictions[:, :, 1:, :] - 
                          transition_predictions[:, :, :-1, :])
        
        gradient_magnitude = (grad_x.mean() + grad_y.mean()) / 2
        
        # Target gradient should be proportional to transition strength
        target_gradient = strength
        consistency_loss = F.mse_loss(gradient_magnitude, 
                                    torch.tensor(target_gradient, device=gradient_magnitude.device))
        
        return consistency_loss


class TopologicalPreservationLoss(nn.Module):
    """Loss function for preserving topological properties."""
    
    def __init__(self, preservation_weight: float = 0.1):
        super().__init__()
        self.preservation_weight = preservation_weight
        
    def forward(self, predictions: torch.Tensor, 
                topological_properties: Dict[str, Any]) -> torch.Tensor:
        """
        Compute topological preservation loss.
        
        Args:
            predictions: Model predictions [B, C, H, W]
            topological_properties: Target topological properties
        """
        # Compute current topological properties from predictions
        current_properties = self._compute_topological_properties(predictions)
        
        # Compare with target properties
        topology_loss = 0.0
        
        if 'euler_characteristic' in topological_properties:
            target_euler = topological_properties['euler_characteristic']
            current_euler = current_properties.get('euler_characteristic', 0)
            euler_loss = F.mse_loss(torch.tensor(current_euler, dtype=torch.float32),
                                   torch.tensor(target_euler, dtype=torch.float32))
            topology_loss += euler_loss
        
        if 'betti_numbers' in topological_properties:
            target_betti = topological_properties['betti_numbers']
            current_betti = current_properties.get('betti_numbers', [0])
            
            # Compare Betti numbers
            for i, (target_b, current_b) in enumerate(zip(target_betti, current_betti)):
                betti_loss = F.mse_loss(torch.tensor(current_b, dtype=torch.float32),
                                       torch.tensor(target_b, dtype=torch.float32))
                topology_loss += betti_loss
        
        return self.preservation_weight * topology_loss
    
    def _compute_topological_properties(self, predictions: torch.Tensor) -> Dict[str, Any]:
        """Compute topological properties from predictions."""
        # Simplified topological computation
        # In practice, this would use more sophisticated topological analysis
        
        # Threshold predictions to get binary masks
        binary_masks = (torch.sigmoid(predictions) > 0.5).float()
        
        properties = {}
        
        # Compute approximate Euler characteristic
        # This is a simplified version - real implementation would use proper topology
        for b in range(binary_masks.size(0)):
            mask = binary_masks[b, 0].cpu().numpy()
            
            # Count connected components (approximation)
            from scipy import ndimage
            labeled_array, num_features = ndimage.label(mask)
            
            # Approximate Euler characteristic as number of components
            properties['euler_characteristic'] = num_features
            properties['betti_numbers'] = [num_features, 0]  # Simplified
            
            break  # Only compute for first batch item
        
        return properties


class CompositeBoundaryLoss(nn.Module):
    """Composite loss function combining multiple boundary-aware components."""
    
    def __init__(self, loss_components: Dict[str, nn.Module], 
                 weights: Dict[str, float],
                 boundary_metrics: BoundaryMetrics):
        super().__init__()
        self.loss_components = nn.ModuleDict(loss_components)
        self.weights = weights
        self.boundary_metrics = boundary_metrics
        
    def forward(self, predictions: torch.Tensor, targets: torch.Tensor,
                lbmd_data: Optional[Dict[str, Any]] = None) -> Dict[str, torch.Tensor]:
        """
        Compute composite boundary loss.
        
        Args:
            predictions: Model predictions
            targets: Ground truth targets
            lbmd_data: Additional LBMD data (boundary scores, manifold coords, etc.)
        """
        losses = {}
        total_loss = 0.0
        
        # Extract LBMD data if available
        boundary_scores = lbmd_data.get('boundary_scores') if lbmd_data else None
        manifold_coords = lbmd_data.get('manifold_coords') if lbmd_data else None
        cluster_labels = lbmd_data.get('cluster_labels') if lbmd_data else None
        transition_strengths = lbmd_data.get('transition_strengths') if lbmd_data else {}
        topological_props = lbmd_data.get('topological_properties') if lbmd_data else {}
        
        # Compute boundary clarity loss
        if 'boundary_clarity' in self.loss_components and 'boundary_clarity' in self.weights:
            clarity_loss = self.loss_components['boundary_clarity'](
                predictions, targets, boundary_scores
            )
            losses['boundary_clarity'] = clarity_loss
            total_loss += self.weights['boundary_clarity'] * clarity_loss
        
        # Compute manifold separation loss
        if ('manifold_separation' in self.loss_components and 
            'manifold_separation' in self.weights and 
            manifold_coords is not None and cluster_labels is not None):
            
            # Flatten spatial dimensions for manifold loss
            B, C, H, W = predictions.shape
            features = predictions.view(B, C, -1).permute(0, 2, 1).reshape(-1, C)
            flat_cluster_labels = cluster_labels.view(-1) if cluster_labels is not None else None
            flat_manifold_coords = manifold_coords.view(-1, manifold_coords.size(-1)) if manifold_coords is not None else None
            
            separation_loss = self.loss_components['manifold_separation'](
                features, flat_cluster_labels, flat_manifold_coords
            )
            losses['manifold_separation'] = separation_loss
            total_loss += self.weights['manifold_separation'] * separation_loss
        
        # Compute transition consistency loss
        if ('transition_consistency' in self.loss_components and 
            'transition_consistency' in self.weights and 
            transition_strengths):
            
            consistency_loss = self.loss_components['transition_consistency'](
                predictions, transition_strengths, cluster_labels
            )
            losses['transition_consistency'] = consistency_loss
            total_loss += self.weights['transition_consistency'] * consistency_loss
        
        # Compute topological preservation loss
        if ('topological_preservation' in self.loss_components and 
            'topological_preservation' in self.weights and 
            topological_props):
            
            topology_loss = self.loss_components['topological_preservation'](
                predictions, topological_props
            )
            losses['topological_preservation'] = topology_loss
            total_loss += self.weights['topological_preservation'] * topology_loss
        
        losses['total'] = total_loss
        return losses


class AdaptiveBoundaryLoss(nn.Module):
    """Adaptive boundary loss that adjusts weights during training."""
    
    def __init__(self, loss_components: Dict[str, nn.Module], 
                 adaptation_rate: float = 0.1):
        super().__init__()
        self.loss_components = nn.ModuleDict(loss_components)
        self.adaptation_rate = adaptation_rate
        
        # Initialize adaptive weights
        self.register_buffer('adaptive_weights', torch.ones(len(loss_components)))
        self.component_names = list(loss_components.keys())
        
    def forward(self, predictions: torch.Tensor, targets: torch.Tensor,
                lbmd_data: Optional[Dict[str, Any]] = None,
                update_weights: bool = True) -> Dict[str, torch.Tensor]:
        """Compute adaptive boundary loss with weight updates."""
        losses = {}
        component_losses = []
        
        # Compute individual loss components
        for i, (name, component) in enumerate(self.loss_components.items()):
            if name == 'boundary_clarity':
                boundary_scores = lbmd_data.get('boundary_scores') if lbmd_data else None
                loss = component(predictions, targets, boundary_scores)
            elif name == 'manifold_separation':
                if lbmd_data:
                    B, C, H, W = predictions.shape
                    features = predictions.view(B, C, -1).permute(0, 2, 1).reshape(-1, C)
                    cluster_labels = lbmd_data.get('cluster_labels')
                    manifold_coords = lbmd_data.get('manifold_coords')
                    if cluster_labels is not None:
                        flat_cluster_labels = cluster_labels.view(-1)
                        flat_manifold_coords = manifold_coords.view(-1, manifold_coords.size(-1)) if manifold_coords is not None else None
                        loss = component(features, flat_cluster_labels, flat_manifold_coords)
                    else:
                        loss = torch.tensor(0.0, device=predictions.device)
                else:
                    loss = torch.tensor(0.0, device=predictions.device)
            else:
                # For other components, use default parameters
                loss = torch.tensor(0.0, device=predictions.device)
            
            losses[name] = loss
            component_losses.append(loss)
        
        # Update adaptive weights based on loss magnitudes
        if update_weights and len(component_losses) > 0:
            component_losses_tensor = torch.stack(component_losses)
            
            # Compute relative importance (inverse of loss magnitude)
            with torch.no_grad():
                loss_magnitudes = torch.abs(component_losses_tensor) + 1e-8
                relative_importance = 1.0 / loss_magnitudes
                relative_importance = relative_importance / relative_importance.sum()
                
                # Update weights with momentum
                self.adaptive_weights = (1 - self.adaptation_rate) * self.adaptive_weights + \
                                      self.adaptation_rate * relative_importance
        
        # Compute weighted total loss
        total_loss = sum(self.adaptive_weights[i] * loss 
                        for i, loss in enumerate(component_losses))
        
        losses['total'] = total_loss
        losses['weights'] = {name: self.adaptive_weights[i].item() 
                           for i, name in enumerate(self.component_names)}
        
        return losses
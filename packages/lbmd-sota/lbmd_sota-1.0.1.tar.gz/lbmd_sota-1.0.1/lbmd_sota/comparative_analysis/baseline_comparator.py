"""
Baseline comparator for evaluating LBMD against existing interpretability methods.
"""

from typing import Dict, List, Any, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from scipy import ndimage
from sklearn.linear_model import Ridge
from sklearn.metrics import accuracy_score
import cv2
import time
import psutil
import os

from ..core.interfaces import BaseComponent
from ..core.data_models import ComparisonResults, BaselineResults, LBMDResults


class GradCAM:
    """Grad-CAM implementation for instance segmentation models."""
    
    def __init__(self, model: nn.Module, target_layer: str):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        self.hooks = []
        
    def _register_hooks(self):
        """Register forward and backward hooks."""
        def forward_hook(module, input, output):
            self.activations = output.detach()
            
        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()
            
        # Find target layer and register hooks
        for name, module in self.model.named_modules():
            if name == self.target_layer:
                self.hooks.append(module.register_forward_hook(forward_hook))
                self.hooks.append(module.register_backward_hook(backward_hook))
                break
                
    def _remove_hooks(self):
        """Remove registered hooks."""
        for hook in self.hooks:
            hook.remove()
        self.hooks = []
        
    def generate_cam(self, input_tensor: torch.Tensor, class_idx: Optional[int] = None) -> np.ndarray:
        """Generate Grad-CAM heatmap."""
        self._register_hooks()
        
        # Forward pass
        self.model.eval()
        output = self.model(input_tensor)
        
        # Get prediction if class_idx not specified
        if class_idx is None:
            if isinstance(output, dict):
                # Handle Mask R-CNN style output
                scores = output.get('scores', output.get('pred_logits', None))
                if scores is not None:
                    class_idx = torch.argmax(scores[0]).item()
                else:
                    class_idx = 0
            else:
                class_idx = torch.argmax(output).item()
        
        # Backward pass
        self.model.zero_grad()
        if isinstance(output, dict):
            # Handle different output formats
            if 'scores' in output:
                target = output['scores'][0][class_idx] if len(output['scores']) > 0 else torch.tensor(0.0)
            elif 'pred_logits' in output:
                target = output['pred_logits'][0, class_idx] if output['pred_logits'].numel() > 0 else torch.tensor(0.0)
            else:
                target = torch.tensor(0.0)
        else:
            target = output[0, class_idx]
            
        target.backward()
        
        # Generate CAM
        if self.gradients is not None and self.activations is not None:
            weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)
            cam = torch.sum(weights * self.activations, dim=1, keepdim=True)
            cam = F.relu(cam)
            
            # Normalize
            cam = cam.squeeze().cpu().numpy()
            if cam.ndim == 0:
                cam = np.array([[cam]])
            elif cam.ndim == 1:
                cam = cam.reshape(1, -1)
                
            cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
        else:
            # Fallback if hooks didn't capture data
            cam = np.zeros((input_tensor.shape[2], input_tensor.shape[3]))
            
        self._remove_hooks()
        return cam


class IntegratedGradients:
    """Integrated Gradients implementation for boundary-focused analysis."""
    
    def __init__(self, model: nn.Module):
        self.model = model
        
    def generate_gradients(self, input_tensor: torch.Tensor, baseline: Optional[torch.Tensor] = None,
                          steps: int = 50, target_class: Optional[int] = None) -> np.ndarray:
        """Generate integrated gradients."""
        if baseline is None:
            baseline = torch.zeros_like(input_tensor)
            
        # Generate path from baseline to input
        alphas = torch.linspace(0, 1, steps).to(input_tensor.device)
        gradients = []
        
        for alpha in alphas:
            interpolated = baseline + alpha * (input_tensor - baseline)
            interpolated.requires_grad_(True)
            
            # Forward pass
            output = self.model(interpolated)
            
            # Get target score
            if isinstance(output, dict):
                if 'scores' in output and len(output['scores']) > 0:
                    if target_class is None:
                        target_class = torch.argmax(output['scores'][0]).item()
                    score = output['scores'][0][target_class] if target_class < len(output['scores'][0]) else torch.tensor(0.0)
                elif 'pred_logits' in output:
                    if target_class is None:
                        target_class = torch.argmax(output['pred_logits'][0]).item()
                    score = output['pred_logits'][0, target_class] if target_class < output['pred_logits'].shape[1] else torch.tensor(0.0)
                else:
                    score = torch.tensor(0.0)
            else:
                if target_class is None:
                    target_class = torch.argmax(output[0]).item()
                score = output[0, target_class] if target_class < output.shape[1] else torch.tensor(0.0)
            
            # Backward pass
            self.model.zero_grad()
            score.backward()
            
            if interpolated.grad is not None:
                gradients.append(interpolated.grad.detach().cpu().numpy())
            else:
                gradients.append(np.zeros_like(input_tensor.cpu().numpy()))
        
        # Integrate gradients
        if gradients:
            integrated_grads = np.mean(gradients, axis=0)
            integrated_grads = integrated_grads * (input_tensor - baseline).cpu().numpy()
        else:
            integrated_grads = np.zeros_like(input_tensor.cpu().numpy())
            
        return integrated_grads


class LIMESegmentation:
    """LIME adaptation for segmentation tasks."""
    
    def __init__(self, model: nn.Module, num_samples: int = 1000):
        self.model = model
        self.num_samples = num_samples
        
    def _generate_superpixels(self, image: np.ndarray, n_segments: int = 100) -> np.ndarray:
        """Generate superpixels using SLIC algorithm."""
        from skimage.segmentation import slic
        from skimage.util import img_as_float
        
        if image.ndim == 4:
            image = image[0]  # Remove batch dimension
        if image.shape[0] == 3:  # CHW to HWC
            image = np.transpose(image, (1, 2, 0))
            
        image_float = img_as_float(image)
        segments = slic(image_float, n_segments=n_segments, compactness=10, sigma=1)
        return segments
        
    def _perturb_image(self, image: torch.Tensor, segments: np.ndarray, 
                      active_segments: np.ndarray) -> torch.Tensor:
        """Perturb image by masking inactive segments."""
        perturbed = image.clone()
        
        if perturbed.ndim == 4:
            perturbed = perturbed[0]  # Remove batch dimension
            
        for i in range(segments.max() + 1):
            if i not in active_segments:
                mask = segments == i
                if perturbed.shape[0] == 3:  # CHW format
                    perturbed[:, mask] = 0
                else:  # HWC format
                    perturbed[mask] = 0
                    
        return perturbed.unsqueeze(0) if perturbed.ndim == 3 else perturbed
        
    def explain_instance(self, input_tensor: torch.Tensor, target_class: Optional[int] = None) -> np.ndarray:
        """Generate LIME explanation for segmentation."""
        # Convert to numpy for superpixel generation
        image_np = input_tensor.squeeze().cpu().numpy()
        segments = self._generate_superpixels(image_np)
        
        n_segments = segments.max() + 1
        
        # Generate random samples
        samples = []
        predictions = []
        
        for _ in range(self.num_samples):
            # Randomly select active segments
            active_segments = np.random.choice(n_segments, 
                                             size=np.random.randint(1, n_segments + 1), 
                                             replace=False)
            
            # Create perturbed image
            perturbed = self._perturb_image(input_tensor, segments, active_segments)
            
            # Get prediction
            with torch.no_grad():
                output = self.model(perturbed)
                
            # Extract prediction score
            if isinstance(output, dict):
                if 'scores' in output and len(output['scores']) > 0:
                    if target_class is None:
                        target_class = torch.argmax(output['scores'][0]).item()
                    score = output['scores'][0][target_class].item() if target_class < len(output['scores'][0]) else 0.0
                elif 'pred_logits' in output:
                    if target_class is None:
                        target_class = torch.argmax(output['pred_logits'][0]).item()
                    score = output['pred_logits'][0, target_class].item() if target_class < output['pred_logits'].shape[1] else 0.0
                else:
                    score = 0.0
            else:
                if target_class is None:
                    target_class = torch.argmax(output[0]).item()
                score = output[0, target_class].item() if target_class < output.shape[1] else 0.0
            
            # Create binary feature vector
            features = np.zeros(n_segments)
            features[active_segments] = 1
            
            samples.append(features)
            predictions.append(score)
        
        # Fit linear model
        if len(samples) > 0 and len(set(predictions)) > 1:
            X = np.array(samples)
            y = np.array(predictions)
            
            model = Ridge(alpha=1.0)
            model.fit(X, y)
            
            # Get feature importance
            importance = model.coef_
        else:
            importance = np.zeros(n_segments)
        
        # Map back to image space
        explanation = np.zeros_like(segments, dtype=float)
        for i in range(n_segments):
            explanation[segments == i] = importance[i]
            
        return explanation


class BaselineComparator(BaseComponent):
    """Implements and runs baseline interpretability methods."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.grad_cam = None
        self.integrated_gradients = None
        self.lime = None
        
    def initialize(self) -> None:
        """Initialize the baseline comparator."""
        self._initialized = True
        
    def _setup_methods(self, model: nn.Module, target_layer: str = None):
        """Setup interpretability methods for given model."""
        # Find a suitable target layer if not specified
        if target_layer is None:
            # Look for common layer names in segmentation models
            layer_names = [name for name, _ in model.named_modules()]
            target_candidates = [
                'backbone.layer4', 'backbone.res5', 'fpn.inner_blocks.3',
                'roi_heads.box_head', 'mask_head', 'conv5'
            ]
            
            target_layer = None
            for candidate in target_candidates:
                if any(candidate in name for name in layer_names):
                    target_layer = next(name for name in layer_names if candidate in name)
                    break
                    
            if target_layer is None and layer_names:
                # Fallback to a middle layer
                target_layer = layer_names[len(layer_names) // 2]
        
        self.grad_cam = GradCAM(model, target_layer)
        self.integrated_gradients = IntegratedGradients(model)
        self.lime = LIMESegmentation(model, num_samples=self.config.get('lime_samples', 500))
        
    def run_grad_cam(self, model: nn.Module, input_tensor: torch.Tensor, 
                    target_layer: str = None, class_idx: int = None) -> BaselineResults:
        """Run Grad-CAM analysis."""
        start_time = time.time()
        process = psutil.Process(os.getpid())
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        if self.grad_cam is None or self.grad_cam.target_layer != target_layer:
            self._setup_methods(model, target_layer)
            
        try:
            saliency_map = self.grad_cam.generate_cam(input_tensor, class_idx)
            
            # Resize to input dimensions if needed
            if saliency_map.shape != input_tensor.shape[2:]:
                saliency_map = cv2.resize(saliency_map, 
                                        (input_tensor.shape[3], input_tensor.shape[2]))
        except Exception as e:
            print(f"Grad-CAM failed: {e}")
            saliency_map = np.zeros((input_tensor.shape[2], input_tensor.shape[3]))
        
        end_time = time.time()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        return BaselineResults(
            method_name="Grad-CAM",
            saliency_maps=saliency_map,
            attention_weights=None,
            feature_importance=saliency_map.flatten(),
            computational_time=end_time - start_time,
            memory_usage=end_memory - start_memory
        )
        
    def run_integrated_gradients(self, model: nn.Module, input_tensor: torch.Tensor,
                               target_class: int = None, steps: int = 50) -> BaselineResults:
        """Run Integrated Gradients analysis."""
        start_time = time.time()
        process = psutil.Process(os.getpid())
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        if self.integrated_gradients is None:
            self._setup_methods(model)
            
        try:
            gradients = self.integrated_gradients.generate_gradients(
                input_tensor, target_class=target_class, steps=steps
            )
            
            # Convert to saliency map (magnitude of gradients)
            if gradients.ndim == 4:  # NCHW
                saliency_map = np.mean(np.abs(gradients[0]), axis=0)
            elif gradients.ndim == 3:  # CHW
                saliency_map = np.mean(np.abs(gradients), axis=0)
            else:
                saliency_map = np.abs(gradients)
                
        except Exception as e:
            print(f"Integrated Gradients failed: {e}")
            saliency_map = np.zeros((input_tensor.shape[2], input_tensor.shape[3]))
            gradients = np.zeros_like(input_tensor.cpu().numpy())
        
        end_time = time.time()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        return BaselineResults(
            method_name="Integrated Gradients",
            saliency_maps=saliency_map,
            attention_weights=gradients,
            feature_importance=saliency_map.flatten(),
            computational_time=end_time - start_time,
            memory_usage=end_memory - start_memory
        )
        
    def run_lime(self, model: nn.Module, input_tensor: torch.Tensor,
                target_class: int = None) -> BaselineResults:
        """Run LIME analysis."""
        start_time = time.time()
        process = psutil.Process(os.getpid())
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        if self.lime is None:
            self._setup_methods(model)
            
        try:
            explanation = self.lime.explain_instance(input_tensor, target_class)
        except Exception as e:
            print(f"LIME failed: {e}")
            explanation = np.zeros((input_tensor.shape[2], input_tensor.shape[3]))
        
        end_time = time.time()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        return BaselineResults(
            method_name="LIME",
            saliency_maps=explanation,
            attention_weights=None,
            feature_importance=explanation.flatten(),
            computational_time=end_time - start_time,
            memory_usage=end_memory - start_memory
        )
        
    def compare_with_baselines(self, model: nn.Module, input_tensor: torch.Tensor,
                             lbmd_results: LBMDResults, target_layer: str = None,
                             target_class: int = None) -> Dict[str, BaselineResults]:
        """Compare LBMD insights with baseline methods."""
        if not self._initialized:
            self.initialize()
            
        baseline_results = {}
        
        # Run Grad-CAM
        try:
            baseline_results['grad_cam'] = self.run_grad_cam(
                model, input_tensor, target_layer, target_class
            )
        except Exception as e:
            print(f"Failed to run Grad-CAM: {e}")
            
        # Run Integrated Gradients
        try:
            baseline_results['integrated_gradients'] = self.run_integrated_gradients(
                model, input_tensor, target_class
            )
        except Exception as e:
            print(f"Failed to run Integrated Gradients: {e}")
            
        # Run LIME
        try:
            baseline_results['lime'] = self.run_lime(
                model, input_tensor, target_class
            )
        except Exception as e:
            print(f"Failed to run LIME: {e}")
            
        return baseline_results
        
    def get_supported_methods(self) -> List[str]:
        """Get list of supported baseline methods."""
        return ['grad_cam', 'integrated_gradients', 'lime']
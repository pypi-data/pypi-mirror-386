"""
Augmentation strategy for targeted data augmentation based on LBMD insights.
"""

from typing import Dict, List, Any, Tuple, Optional, Callable
import torch
import torch.nn.functional as F
import numpy as np
import cv2
from scipy import ndimage
from ..core.interfaces import BaseComponent
from ..core.data_models import AugmentationPipeline, WeaknessReport, LBMDResults


class AugmentationStrategy(BaseComponent):
    """Develops targeted data augmentation based on identified weaknesses."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.augmentation_intensity = config.get('augmentation_intensity', 0.5)
        self.boundary_focus_weight = config.get('boundary_focus_weight', 2.0)
        self.adversarial_strength = config.get('adversarial_strength', 0.1)
        self.synthetic_boundary_prob = config.get('synthetic_boundary_prob', 0.3)
        
    def initialize(self) -> None:
        """Initialize the augmentation strategy."""
        self._augmentation_methods = self._initialize_augmentation_methods()
        self._weakness_to_augmentation_map = self._create_weakness_mapping()
        self._initialized = True
    
    def _initialize_augmentation_methods(self) -> Dict[str, Callable]:
        """Initialize different augmentation methods."""
        return {
            'boundary_blur': self._boundary_blur_augmentation,
            'boundary_noise': self._boundary_noise_augmentation,
            'boundary_erosion': self._boundary_erosion_augmentation,
            'boundary_dilation': self._boundary_dilation_augmentation,
            'synthetic_boundaries': self._synthetic_boundary_augmentation,
            'adversarial_boundaries': self._adversarial_boundary_augmentation,
            'boundary_occlusion': self._boundary_occlusion_augmentation,
            'boundary_distortion': self._boundary_distortion_augmentation,
            'multi_scale_boundaries': self._multi_scale_boundary_augmentation,
            'boundary_mixing': self._boundary_mixing_augmentation
        }
    
    def _create_weakness_mapping(self) -> Dict[str, List[str]]:
        """Create mapping from weakness types to appropriate augmentations."""
        return {
            'weak_boundary_detection': [
                'boundary_blur', 'boundary_noise', 'synthetic_boundaries'
            ],
            'poor_boundary_clarity': [
                'boundary_erosion', 'boundary_dilation', 'boundary_distortion'
            ],
            'boundary_occlusion_sensitivity': [
                'boundary_occlusion', 'adversarial_boundaries'
            ],
            'scale_invariance_issues': [
                'multi_scale_boundaries', 'boundary_mixing'
            ],
            'class_specific_boundary_weakness': [
                'synthetic_boundaries', 'boundary_mixing', 'adversarial_boundaries'
            ]
        }
    
    def analyze_boundary_weaknesses(self, lbmd_results: LBMDResults, 
                                  failure_cases: List[Dict[str, Any]]) -> WeaknessReport:
        """Analyze boundary weaknesses from LBMD results and failure cases."""
        weaknesses = []
        severity_scores = []
        affected_classes = set()
        spatial_distributions = []
        
        # Analyze boundary strength weaknesses
        boundary_scores = lbmd_results.boundary_scores
        weak_boundary_mask = boundary_scores < 0.5
        
        if weak_boundary_mask.sum() > 0.3 * weak_boundary_mask.size:
            weaknesses.append('weak_boundary_detection')
            severity_scores.append(1.0 - np.mean(boundary_scores))
            spatial_distributions.append(weak_boundary_mask.astype(float))
        
        # Analyze transition clarity
        transition_strengths = list(lbmd_results.transition_strengths.values())
        if transition_strengths:
            avg_transition_strength = np.mean(transition_strengths)
            if avg_transition_strength < 0.6:
                weaknesses.append('poor_boundary_clarity')
                severity_scores.append(1.0 - avg_transition_strength)
                
                # Create spatial distribution for transition weaknesses
                transition_map = np.zeros_like(boundary_scores)
                for (cluster_i, cluster_j), strength in lbmd_results.transition_strengths.items():
                    if strength < 0.6:
                        # Reshape clusters to match boundary_scores shape if needed
                        if lbmd_results.clusters.shape != boundary_scores.shape:
                            # Skip this transition if shapes don't match
                            continue
                        mask_i = (lbmd_results.clusters == cluster_i)
                        mask_j = (lbmd_results.clusters == cluster_j)
                        boundary_region = self._compute_boundary_region(mask_i, mask_j)
                        if boundary_region.shape == transition_map.shape:
                            transition_map += boundary_region * (1.0 - strength)
                
                spatial_distributions.append(transition_map)
        
        # Analyze failure cases
        for failure_case in failure_cases:
            failure_type = failure_case.get('type', 'unknown')
            affected_class = failure_case.get('class', 'unknown')
            affected_classes.add(affected_class)
            
            if failure_type == 'boundary_occlusion':
                if 'boundary_occlusion_sensitivity' not in weaknesses:
                    weaknesses.append('boundary_occlusion_sensitivity')
                    severity_scores.append(failure_case.get('severity', 0.5))
                    spatial_distributions.append(failure_case.get('spatial_mask', np.zeros_like(boundary_scores)))
            
            elif failure_type == 'scale_variation':
                if 'scale_invariance_issues' not in weaknesses:
                    weaknesses.append('scale_invariance_issues')
                    severity_scores.append(failure_case.get('severity', 0.5))
                    spatial_distributions.append(failure_case.get('spatial_mask', np.zeros_like(boundary_scores)))
        
        # Create composite weakness report
        if weaknesses:
            primary_weakness = weaknesses[np.argmax(severity_scores)]
            max_severity = max(severity_scores)
            
            # Combine spatial distributions
            combined_spatial = np.zeros_like(boundary_scores)
            for spatial_dist in spatial_distributions:
                if spatial_dist.shape == combined_spatial.shape:
                    combined_spatial += spatial_dist
            combined_spatial = np.clip(combined_spatial, 0, 1)
            
            suggested_fixes = self._weakness_to_augmentation_map.get(primary_weakness, [])
            
            return WeaknessReport(
                weakness_type=primary_weakness,
                affected_classes=list(affected_classes),
                severity_score=max_severity,
                spatial_distribution=combined_spatial,
                suggested_fixes=suggested_fixes
            )
        else:
            # No significant weaknesses found
            return WeaknessReport(
                weakness_type='none',
                affected_classes=[],
                severity_score=0.0,
                spatial_distribution=np.zeros_like(boundary_scores),
                suggested_fixes=[]
            )
    
    def _compute_boundary_region(self, mask_i: np.ndarray, mask_j: np.ndarray) -> np.ndarray:
        """Compute boundary region between two masks."""
        # Dilate both masks
        kernel = np.ones((3, 3), np.uint8)
        mask_i_dilated = cv2.dilate(mask_i.astype(np.uint8), kernel, iterations=1)
        mask_j_dilated = cv2.dilate(mask_j.astype(np.uint8), kernel, iterations=1)
        
        # Boundary is where dilated masks overlap
        boundary_region = (mask_i_dilated & mask_j_dilated).astype(float)
        return boundary_region
    
    def create_augmentation_strategy(self, weakness_analysis: WeaknessReport) -> AugmentationPipeline:
        """Create targeted augmentation strategy based on weakness analysis."""
        if not self._initialized:
            self.initialize()
        
        weakness_type = weakness_analysis.weakness_type
        severity = weakness_analysis.severity_score
        spatial_distribution = weakness_analysis.spatial_distribution
        
        # Select appropriate augmentation methods
        augmentation_methods = self._weakness_to_augmentation_map.get(weakness_type, [])
        
        # Calculate expected improvements
        expected_improvements = {}
        for method in augmentation_methods:
            # Base improvement scaled by severity
            base_improvement = {
                'boundary_blur': 0.1,
                'boundary_noise': 0.08,
                'boundary_erosion': 0.12,
                'boundary_dilation': 0.12,
                'synthetic_boundaries': 0.15,
                'adversarial_boundaries': 0.18,
                'boundary_occlusion': 0.14,
                'boundary_distortion': 0.11,
                'multi_scale_boundaries': 0.16,
                'boundary_mixing': 0.13
            }.get(method, 0.1)
            
            expected_improvements[method] = min(base_improvement * (1 + severity), 0.25)
        
        # Create implementation details
        implementation_details = {
            'weakness_type': weakness_type,
            'severity_score': severity,
            'spatial_focus_map': spatial_distribution.tolist() if spatial_distribution is not None else None,
            'augmentation_intensity': self.augmentation_intensity * (1 + severity * 0.5),
            'boundary_focus_weight': self.boundary_focus_weight,
            'target_classes': weakness_analysis.affected_classes
        }
        
        return AugmentationPipeline(
            augmentation_strategies=augmentation_methods,
            target_weaknesses=[weakness_type],
            expected_improvements=expected_improvements,
            implementation_details=implementation_details
        )
    
    def apply_augmentation_pipeline(self, image: np.ndarray, mask: np.ndarray,
                                  pipeline: AugmentationPipeline) -> Tuple[np.ndarray, np.ndarray]:
        """Apply the augmentation pipeline to an image and mask pair."""
        augmented_image = image.copy()
        augmented_mask = mask.copy()
        
        spatial_focus_map = None
        if pipeline.implementation_details.get('spatial_focus_map'):
            spatial_focus_map = np.array(pipeline.implementation_details['spatial_focus_map'])
            if spatial_focus_map.shape != image.shape[:2]:
                spatial_focus_map = cv2.resize(spatial_focus_map, 
                                             (image.shape[1], image.shape[0]))
        
        # Apply each augmentation method
        for method_name in pipeline.augmentation_strategies:
            if method_name in self._augmentation_methods:
                augmentation_func = self._augmentation_methods[method_name]
                
                # Apply augmentation with spatial focus
                augmented_image, augmented_mask = augmentation_func(
                    augmented_image, augmented_mask, 
                    spatial_focus_map, pipeline.implementation_details
                )
        
        return augmented_image, augmented_mask
    
    def _boundary_blur_augmentation(self, image: np.ndarray, mask: np.ndarray,
                                  spatial_focus: Optional[np.ndarray],
                                  params: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """Apply boundary-focused blur augmentation."""
        intensity = params.get('augmentation_intensity', 0.5)
        
        # Create boundary mask
        boundary_mask = self._extract_boundary_mask(mask)
        
        # Apply spatial focus if available
        if spatial_focus is not None:
            boundary_mask = boundary_mask * spatial_focus
        
        # Apply Gaussian blur to boundary regions
        blur_kernel_size = int(5 + intensity * 10)
        if blur_kernel_size % 2 == 0:
            blur_kernel_size += 1
        
        blurred_image = cv2.GaussianBlur(image, (blur_kernel_size, blur_kernel_size), 0)
        
        # Blend original and blurred image based on boundary mask
        augmented_image = image * (1 - boundary_mask[:, :, np.newaxis]) + \
                         blurred_image * boundary_mask[:, :, np.newaxis]
        
        return augmented_image.astype(image.dtype), mask
    
    def _boundary_noise_augmentation(self, image: np.ndarray, mask: np.ndarray,
                                   spatial_focus: Optional[np.ndarray],
                                   params: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """Apply boundary-focused noise augmentation."""
        intensity = params.get('augmentation_intensity', 0.5)
        
        # Create boundary mask
        boundary_mask = self._extract_boundary_mask(mask)
        
        # Apply spatial focus if available
        if spatial_focus is not None:
            boundary_mask = boundary_mask * spatial_focus
        
        # Generate noise
        noise = np.random.normal(0, intensity * 25, image.shape)
        
        # Apply noise only to boundary regions
        augmented_image = image + noise * boundary_mask[:, :, np.newaxis]
        augmented_image = np.clip(augmented_image, 0, 255)
        
        return augmented_image.astype(image.dtype), mask
    
    def _boundary_erosion_augmentation(self, image: np.ndarray, mask: np.ndarray,
                                     spatial_focus: Optional[np.ndarray],
                                     params: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """Apply boundary erosion augmentation."""
        intensity = params.get('augmentation_intensity', 0.5)
        
        # Apply spatial focus to determine erosion strength
        erosion_strength = intensity
        if spatial_focus is not None:
            erosion_strength = intensity * (1 + np.mean(spatial_focus))
        
        # Apply morphological erosion
        kernel_size = int(3 + erosion_strength * 4)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        
        augmented_mask = mask.copy()
        for class_id in np.unique(mask):
            if class_id == 0:  # Skip background
                continue
            
            class_mask = (mask == class_id).astype(np.uint8)
            eroded_mask = cv2.erode(class_mask, kernel, iterations=1)
            augmented_mask[class_mask == 1] = 0
            augmented_mask[eroded_mask == 1] = class_id
        
        return image, augmented_mask
    
    def _boundary_dilation_augmentation(self, image: np.ndarray, mask: np.ndarray,
                                      spatial_focus: Optional[np.ndarray],
                                      params: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """Apply boundary dilation augmentation."""
        intensity = params.get('augmentation_intensity', 0.5)
        
        # Apply spatial focus to determine dilation strength
        dilation_strength = intensity
        if spatial_focus is not None:
            dilation_strength = intensity * (1 + np.mean(spatial_focus))
        
        # Apply morphological dilation
        kernel_size = int(3 + dilation_strength * 4)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        
        augmented_mask = mask.copy()
        for class_id in np.unique(mask):
            if class_id == 0:  # Skip background
                continue
            
            class_mask = (mask == class_id).astype(np.uint8)
            dilated_mask = cv2.dilate(class_mask, kernel, iterations=1)
            augmented_mask[dilated_mask == 1] = class_id
        
        return image, augmented_mask
    
    def _synthetic_boundary_augmentation(self, image: np.ndarray, mask: np.ndarray,
                                       spatial_focus: Optional[np.ndarray],
                                       params: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """Create synthetic boundary scenarios for training enhancement."""
        intensity = params.get('augmentation_intensity', 0.5)
        
        # Create synthetic objects with challenging boundaries
        augmented_image = image.copy()
        augmented_mask = mask.copy()
        
        # Add synthetic circular objects with varying boundary clarity
        num_synthetic_objects = int(1 + intensity * 3)
        
        for _ in range(num_synthetic_objects):
            # Random position and size
            h, w = image.shape[:2]
            center_x = np.random.randint(w // 4, 3 * w // 4)
            center_y = np.random.randint(h // 4, 3 * h // 4)
            max_radius = max(20, min(h, w) // 8)
            radius = np.random.randint(10, max_radius)
            
            # Create synthetic object mask
            y, x = np.ogrid[:h, :w]
            synthetic_mask = ((x - center_x) ** 2 + (y - center_y) ** 2) <= radius ** 2
            
            # Add boundary blur to make it challenging
            boundary_blur_radius = int(radius * 0.2 * intensity)
            if boundary_blur_radius > 0:
                synthetic_mask = cv2.GaussianBlur(
                    synthetic_mask.astype(np.float32), 
                    (boundary_blur_radius * 2 + 1, boundary_blur_radius * 2 + 1), 
                    0
                ) > 0.5
            
            # Add synthetic object to mask (use next available class ID)
            max_class_id = np.max(mask)
            synthetic_class_id = max_class_id + 1
            augmented_mask[synthetic_mask] = synthetic_class_id
            
            # Modify image in synthetic region
            synthetic_color = np.random.randint(0, 256, 3)
            augmented_image[synthetic_mask] = synthetic_color
        
        return augmented_image, augmented_mask
    
    def _adversarial_boundary_augmentation(self, image: np.ndarray, mask: np.ndarray,
                                         spatial_focus: Optional[np.ndarray],
                                         params: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """Apply adversarial boundary perturbations for robustness testing."""
        intensity = params.get('augmentation_intensity', 0.5)
        adversarial_strength = self.adversarial_strength * intensity
        
        # Create boundary mask
        boundary_mask = self._extract_boundary_mask(mask)
        
        # Apply spatial focus if available
        if spatial_focus is not None:
            boundary_mask = boundary_mask * spatial_focus
        
        # Generate adversarial perturbations
        # Simplified adversarial noise (in practice, would use FGSM or PGD)
        perturbation = np.random.uniform(-adversarial_strength, adversarial_strength, image.shape)
        perturbation *= 255  # Scale to image range
        
        # Apply perturbations only to boundary regions
        augmented_image = image + perturbation * boundary_mask[:, :, np.newaxis]
        augmented_image = np.clip(augmented_image, 0, 255)
        
        return augmented_image.astype(image.dtype), mask
    
    def _boundary_occlusion_augmentation(self, image: np.ndarray, mask: np.ndarray,
                                       spatial_focus: Optional[np.ndarray],
                                       params: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """Apply boundary occlusion augmentation."""
        intensity = params.get('augmentation_intensity', 0.5)
        
        # Create boundary mask
        boundary_mask = self._extract_boundary_mask(mask)
        
        # Apply spatial focus if available
        if spatial_focus is not None:
            boundary_mask = boundary_mask * spatial_focus
        
        # Create occlusion patches along boundaries
        num_occlusions = int(1 + intensity * 5)
        
        augmented_image = image.copy()
        
        for _ in range(num_occlusions):
            # Find boundary pixels
            boundary_pixels = np.where(boundary_mask > 0.5)
            if len(boundary_pixels[0]) == 0:
                continue
            
            # Select random boundary pixel
            idx = np.random.randint(len(boundary_pixels[0]))
            center_y, center_x = boundary_pixels[0][idx], boundary_pixels[1][idx]
            
            # Create occlusion patch
            patch_size = int(10 + intensity * 20)
            y1 = max(0, center_y - patch_size // 2)
            y2 = min(image.shape[0], center_y + patch_size // 2)
            x1 = max(0, center_x - patch_size // 2)
            x2 = min(image.shape[1], center_x + patch_size // 2)
            
            # Fill with random color or black
            if np.random.random() > 0.5:
                occlusion_color = np.random.randint(0, 256, 3)
            else:
                occlusion_color = [0, 0, 0]  # Black occlusion
            
            augmented_image[y1:y2, x1:x2] = occlusion_color
        
        return augmented_image, mask
    
    def _boundary_distortion_augmentation(self, image: np.ndarray, mask: np.ndarray,
                                        spatial_focus: Optional[np.ndarray],
                                        params: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """Apply boundary distortion augmentation."""
        intensity = params.get('augmentation_intensity', 0.5)
        
        # Create boundary mask
        boundary_mask = self._extract_boundary_mask(mask)
        
        # Apply spatial focus if available
        if spatial_focus is not None:
            boundary_mask = boundary_mask * spatial_focus
        
        # Create distortion field
        h, w = image.shape[:2]
        distortion_strength = intensity * 10
        
        # Generate random displacement field
        displacement_x = np.random.uniform(-distortion_strength, distortion_strength, (h, w))
        displacement_y = np.random.uniform(-distortion_strength, distortion_strength, (h, w))
        
        # Apply boundary mask to limit distortion to boundary regions
        displacement_x *= boundary_mask
        displacement_y *= boundary_mask
        
        # Create coordinate grids
        y_coords, x_coords = np.mgrid[0:h, 0:w]
        new_x_coords = x_coords + displacement_x
        new_y_coords = y_coords + displacement_y
        
        # Clip coordinates to image bounds
        new_x_coords = np.clip(new_x_coords, 0, w - 1)
        new_y_coords = np.clip(new_y_coords, 0, h - 1)
        
        # Apply distortion using interpolation
        from scipy.ndimage import map_coordinates
        
        augmented_image = np.zeros_like(image)
        for c in range(image.shape[2]):
            augmented_image[:, :, c] = map_coordinates(
                image[:, :, c], [new_y_coords, new_x_coords], 
                order=1, mode='nearest'
            )
        
        # Apply same distortion to mask
        augmented_mask = map_coordinates(
            mask.astype(float), [new_y_coords, new_x_coords], 
            order=0, mode='nearest'
        ).astype(mask.dtype)
        
        return augmented_image, augmented_mask
    
    def _multi_scale_boundary_augmentation(self, image: np.ndarray, mask: np.ndarray,
                                         spatial_focus: Optional[np.ndarray],
                                         params: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """Apply multi-scale boundary augmentation."""
        intensity = params.get('augmentation_intensity', 0.5)
        
        # Create multiple scales of the image
        scales = [0.5, 0.75, 1.0, 1.25, 1.5]
        scale = np.random.choice(scales)
        
        h, w = image.shape[:2]
        new_h, new_w = int(h * scale), int(w * scale)
        
        # Resize image and mask
        resized_image = cv2.resize(image, (new_w, new_h))
        resized_mask = cv2.resize(mask, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
        
        # Crop or pad to original size
        if scale > 1.0:
            # Crop to original size
            start_y = (new_h - h) // 2
            start_x = (new_w - w) // 2
            augmented_image = resized_image[start_y:start_y + h, start_x:start_x + w]
            augmented_mask = resized_mask[start_y:start_y + h, start_x:start_x + w]
        else:
            # Pad to original size
            pad_y = (h - new_h) // 2
            pad_x = (w - new_w) // 2
            
            augmented_image = np.zeros_like(image)
            augmented_mask = np.zeros_like(mask)
            
            augmented_image[pad_y:pad_y + new_h, pad_x:pad_x + new_w] = resized_image
            augmented_mask[pad_y:pad_y + new_h, pad_x:pad_x + new_w] = resized_mask
        
        return augmented_image, augmented_mask
    
    def _boundary_mixing_augmentation(self, image: np.ndarray, mask: np.ndarray,
                                    spatial_focus: Optional[np.ndarray],
                                    params: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """Apply boundary mixing augmentation (mix boundaries from different images)."""
        # This is a simplified version - in practice, would need access to other images
        intensity = params.get('augmentation_intensity', 0.5)
        
        # Create boundary mask
        boundary_mask = self._extract_boundary_mask(mask)
        
        # Apply spatial focus if available
        if spatial_focus is not None:
            boundary_mask = boundary_mask * spatial_focus
        
        # Create synthetic boundary mixing by duplicating and shifting boundaries
        augmented_image = image.copy()
        augmented_mask = mask.copy()
        
        # Shift boundary regions slightly to create mixing effect
        shift_x = int(np.random.uniform(-5, 5) * intensity)
        shift_y = int(np.random.uniform(-5, 5) * intensity)
        
        # Create shifted boundary mask
        shifted_boundary_mask = np.roll(boundary_mask, shift_x, axis=1)
        shifted_boundary_mask = np.roll(shifted_boundary_mask, shift_y, axis=0)
        
        # Mix original and shifted boundary regions
        mixing_weight = 0.3 * intensity
        mixed_regions = (boundary_mask > 0.5) & (shifted_boundary_mask > 0.5)
        
        if np.any(mixed_regions):
            # Blend image regions
            augmented_image[mixed_regions] = (
                (1 - mixing_weight) * image[mixed_regions] +
                mixing_weight * np.roll(np.roll(image, shift_x, axis=1), shift_y, axis=0)[mixed_regions]
            )
        
        return augmented_image, augmented_mask
    
    def _extract_boundary_mask(self, mask: np.ndarray) -> np.ndarray:
        """Extract boundary mask from segmentation mask."""
        # Compute gradients to find boundaries
        grad_x = np.abs(np.diff(mask, axis=1, prepend=mask[:, :1]))
        grad_y = np.abs(np.diff(mask, axis=0, prepend=mask[:1, :]))
        
        # Combine gradients
        boundary_mask = (grad_x > 0) | (grad_y > 0)
        
        # Dilate to make boundaries thicker
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        boundary_mask = cv2.dilate(boundary_mask.astype(np.uint8), kernel, iterations=1)
        
        return boundary_mask.astype(float)


class BoundaryAugmentationDataset:
    """Dataset wrapper that applies boundary-aware augmentations."""
    
    def __init__(self, base_dataset, augmentation_strategy: AugmentationStrategy,
                 augmentation_pipeline: AugmentationPipeline, augmentation_prob: float = 0.5):
        self.base_dataset = base_dataset
        self.augmentation_strategy = augmentation_strategy
        self.augmentation_pipeline = augmentation_pipeline
        self.augmentation_prob = augmentation_prob
    
    def __len__(self):
        return len(self.base_dataset)
    
    def __getitem__(self, idx):
        # Get base sample
        sample = self.base_dataset[idx]
        image = sample['image']
        mask = sample['mask']
        
        # Apply augmentation with probability
        if np.random.random() < self.augmentation_prob:
            # Convert to numpy if needed
            if isinstance(image, torch.Tensor):
                image_np = image.permute(1, 2, 0).numpy()
                mask_np = mask.numpy()
            else:
                image_np = image
                mask_np = mask
            
            # Apply augmentation pipeline
            augmented_image, augmented_mask = self.augmentation_strategy.apply_augmentation_pipeline(
                image_np, mask_np, self.augmentation_pipeline
            )
            
            # Convert back to tensor if needed
            if isinstance(sample['image'], torch.Tensor):
                sample['image'] = torch.from_numpy(augmented_image).permute(2, 0, 1)
                sample['mask'] = torch.from_numpy(augmented_mask)
            else:
                sample['image'] = augmented_image
                sample['mask'] = augmented_mask
        
        return sample
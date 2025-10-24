"""
Test suite for model improvement toolkit components.
"""

import pytest
import torch
import numpy as np
from unittest.mock import Mock, patch
from scipy.spatial import ConvexHull

from .architecture_enhancer import ArchitectureEnhancer, SpatialAttentionModule, BoundarySkipConnection
from .boundary_loss_designer import BoundaryLossDesigner, BoundaryClarityLoss, ManifoldSeparationLoss
from .augmentation_strategy import AugmentationStrategy, BoundaryAugmentationDataset
from ..core.data_models import (
    LBMDResults, BoundaryMetrics, ArchitecturalSuggestions, 
    WeaknessReport, AugmentationPipeline, StatisticalMetrics, TopologicalProperties
)


class TestArchitectureEnhancer:
    """Test cases for ArchitectureEnhancer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'boundary_strength_threshold': 0.5,
            'transition_clarity_threshold': 0.6,
            'manifold_separation_threshold': 0.7
        }
        self.enhancer = ArchitectureEnhancer(self.config)
        
        # Create mock LBMD results
        self.mock_lbmd_results = self._create_mock_lbmd_results()
    
    def _create_mock_lbmd_results(self):
        """Create mock LBMD results for testing."""
        boundary_scores = np.random.rand(64, 64) * 0.4  # Weak boundaries
        boundary_mask = boundary_scores > 0.3
        manifold_coords = np.random.rand(100, 2)
        pixel_coords = np.random.rand(100, 2)
        is_boundary = np.random.rand(100) > 0.5
        clusters = np.random.randint(0, 5, 100)
        
        # Weak transition strengths
        transition_strengths = {
            (0, 1): 0.4,
            (1, 2): 0.3,
            (2, 3): 0.5
        }
        
        cluster_hulls = {}
        for i in range(5):
            cluster_points = manifold_coords[clusters == i]
            if len(cluster_points) >= 3:
                cluster_hulls[i] = ConvexHull(cluster_points)
        
        statistical_metrics = StatisticalMetrics(
            correlation=0.6,
            p_value=0.05,
            confidence_interval=(0.4, 0.8),
            effect_size=0.3,
            sample_size=100
        )
        
        topological_properties = TopologicalProperties(
            betti_numbers=[3, 1],
            persistence_diagram=np.random.rand(10, 2),
            euler_characteristic=3,
            genus=1,
            curvature_metrics={'mean_curvature': 0.5}
        )
        
        return LBMDResults(
            layer_name='test_layer',
            boundary_scores=boundary_scores,
            boundary_mask=boundary_mask,
            manifold_coords=manifold_coords,
            pixel_coords=pixel_coords,
            is_boundary=is_boundary,
            clusters=clusters,
            transition_strengths=transition_strengths,
            cluster_hulls=cluster_hulls,
            statistical_metrics=statistical_metrics,
            topological_properties=topological_properties
        )
    
    def test_initialization(self):
        """Test enhancer initialization."""
        self.enhancer.initialize()
        assert self.enhancer._initialized
        assert hasattr(self.enhancer, '_enhancement_strategies')
        assert hasattr(self.enhancer, '_architecture_patterns')
    
    def test_analyze_weak_boundary_representations(self):
        """Test weak boundary analysis."""
        self.enhancer.initialize()
        weak_representations = self.enhancer.analyze_weak_boundary_representations(self.mock_lbmd_results)
        
        assert isinstance(weak_representations, dict)
        assert 'boundary_detection' in weak_representations
        assert 'transition_clarity' in weak_representations
        assert all(0 <= score <= 1 for score in weak_representations.values())
    
    def test_suggest_architectural_modifications(self):
        """Test architectural modification suggestions."""
        self.enhancer.initialize()
        weak_representations = {'boundary_detection': 0.8, 'transition_clarity': 0.6}
        
        suggestions = self.enhancer.suggest_architectural_modifications(weak_representations)
        
        assert isinstance(suggestions, dict)
        assert len(suggestions) > 0
        
        for suggestion_name, details in suggestions.items():
            assert 'type' in details
            assert 'description' in details
            assert 'expected_improvement' in details
            assert 'complexity' in details
    
    def test_suggest_architecture_improvements(self):
        """Test complete architecture improvement suggestion."""
        suggestions = self.enhancer.suggest_architecture_improvements(self.mock_lbmd_results)
        
        assert isinstance(suggestions, ArchitecturalSuggestions)
        assert isinstance(suggestions.weak_layers, list)
        assert isinstance(suggestions.suggested_modifications, dict)
        assert isinstance(suggestions.expected_improvements, dict)
        assert isinstance(suggestions.implementation_complexity, dict)
        assert isinstance(suggestions.priority_ranking, list)
    
    def test_compare_architectures_boundary_processing(self):
        """Test architecture comparison functionality."""
        self.enhancer.initialize()
        architectures = ['arch1', 'arch2']
        lbmd_results = {
            'arch1': self.mock_lbmd_results,
            'arch2': self.mock_lbmd_results
        }
        
        comparison = self.enhancer.compare_architectures_boundary_processing(architectures, lbmd_results)
        
        assert isinstance(comparison, dict)
        assert 'arch1' in comparison
        assert 'arch2' in comparison
        
        for arch_name, metrics in comparison.items():
            assert 'boundary_detection' in metrics
            assert 'transition_clarity' in metrics
            assert 'overall_capability' in metrics


class TestSpatialAttentionModule:
    """Test cases for SpatialAttentionModule."""
    
    def test_forward_pass(self):
        """Test forward pass of spatial attention module."""
        module = SpatialAttentionModule(in_channels=64)
        input_tensor = torch.randn(2, 64, 32, 32)
        
        output = module(input_tensor)
        
        assert output.shape == input_tensor.shape
        assert not torch.allclose(output, input_tensor)  # Should modify input


class TestBoundaryLossDesigner:
    """Test cases for BoundaryLossDesigner."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'boundary_weight': 1.0,
            'clarity_weight': 0.5,
            'separation_weight': 0.3
        }
        self.designer = BoundaryLossDesigner(self.config)
        
        # Create mock boundary metrics
        self.mock_boundary_metrics = BoundaryMetrics(
            boundary_strength=0.4,
            transition_clarity=0.5,
            manifold_separation=0.6,
            topological_persistence=0.3,
            statistical_significance=0.05,
            spatial_coherence=0.7,
            temporal_stability=0.8
        )
    
    def test_initialization(self):
        """Test designer initialization."""
        self.designer.initialize()
        assert self.designer._initialized
        assert hasattr(self.designer, '_loss_components')
    
    def test_compute_adaptive_weights(self):
        """Test adaptive weight computation."""
        self.designer.initialize()
        weights = self.designer.compute_adaptive_weights(self.mock_boundary_metrics)
        
        assert isinstance(weights, dict)
        assert 'boundary_clarity' in weights
        assert 'transition_consistency' in weights
        assert 'manifold_separation' in weights
        assert all(weight > 0 for weight in weights.values())
    
    def test_design_boundary_loss(self):
        """Test boundary loss design."""
        loss_module = self.designer.design_boundary_loss(self.mock_boundary_metrics)
        
        assert isinstance(loss_module, torch.nn.Module)
        
        # Test forward pass
        predictions = torch.randn(2, 3, 32, 32)
        targets = torch.randint(0, 2, (2, 3, 32, 32)).float()
        
        loss_dict = loss_module(predictions, targets)
        assert isinstance(loss_dict, dict)
        assert 'total' in loss_dict
        assert isinstance(loss_dict['total'], torch.Tensor)


class TestBoundaryClarityLoss:
    """Test cases for BoundaryClarityLoss."""
    
    def test_forward_pass(self):
        """Test forward pass of boundary clarity loss."""
        loss_fn = BoundaryClarityLoss()
        
        predictions = torch.randn(2, 3, 32, 32)
        targets = torch.randint(0, 2, (2, 3, 32, 32)).float()
        boundary_scores = torch.rand(2, 32, 32)
        
        loss = loss_fn(predictions, targets, boundary_scores)
        
        assert isinstance(loss, torch.Tensor)
        assert loss.dim() == 0  # Scalar loss
        assert loss.item() >= 0
    
    def test_without_boundary_scores(self):
        """Test loss computation without boundary scores."""
        loss_fn = BoundaryClarityLoss()
        
        predictions = torch.randn(2, 3, 32, 32)
        targets = torch.randint(0, 2, (2, 3, 32, 32)).float()
        
        loss = loss_fn(predictions, targets)
        
        assert isinstance(loss, torch.Tensor)
        assert loss.dim() == 0


class TestAugmentationStrategy:
    """Test cases for AugmentationStrategy."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'augmentation_intensity': 0.5,
            'boundary_focus_weight': 2.0,
            'adversarial_strength': 0.1
        }
        self.strategy = AugmentationStrategy(self.config)
        
        # Create mock weakness report
        self.mock_weakness_report = WeaknessReport(
            weakness_type='weak_boundary_detection',
            affected_classes=['person', 'car'],
            severity_score=0.7,
            spatial_distribution=np.random.rand(64, 64),
            suggested_fixes=['boundary_blur', 'synthetic_boundaries']
        )
    
    def test_initialization(self):
        """Test strategy initialization."""
        self.strategy.initialize()
        assert self.strategy._initialized
        assert hasattr(self.strategy, '_augmentation_methods')
        assert hasattr(self.strategy, '_weakness_to_augmentation_map')
    
    def test_create_augmentation_strategy(self):
        """Test augmentation strategy creation."""
        pipeline = self.strategy.create_augmentation_strategy(self.mock_weakness_report)
        
        assert isinstance(pipeline, AugmentationPipeline)
        assert isinstance(pipeline.augmentation_strategies, list)
        assert isinstance(pipeline.target_weaknesses, list)
        assert isinstance(pipeline.expected_improvements, dict)
        assert isinstance(pipeline.implementation_details, dict)
    
    def test_apply_augmentation_pipeline(self):
        """Test augmentation pipeline application."""
        self.strategy.initialize()
        
        # Create test image and mask
        image = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
        mask = np.random.randint(0, 5, (64, 64), dtype=np.uint8)
        
        pipeline = self.strategy.create_augmentation_strategy(self.mock_weakness_report)
        
        augmented_image, augmented_mask = self.strategy.apply_augmentation_pipeline(
            image, mask, pipeline
        )
        
        assert augmented_image.shape == image.shape
        assert augmented_mask.shape == mask.shape
        assert augmented_image.dtype == image.dtype
        assert augmented_mask.dtype == mask.dtype
    
    def test_boundary_blur_augmentation(self):
        """Test boundary blur augmentation."""
        self.strategy.initialize()
        
        image = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
        mask = np.random.randint(0, 5, (64, 64), dtype=np.uint8)
        spatial_focus = np.random.rand(64, 64)
        params = {'augmentation_intensity': 0.5}
        
        aug_image, aug_mask = self.strategy._boundary_blur_augmentation(
            image, mask, spatial_focus, params
        )
        
        assert aug_image.shape == image.shape
        assert aug_mask.shape == mask.shape
        assert np.array_equal(aug_mask, mask)  # Mask should be unchanged
    
    def test_synthetic_boundary_augmentation(self):
        """Test synthetic boundary augmentation."""
        self.strategy.initialize()
        
        image = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
        mask = np.random.randint(0, 3, (64, 64), dtype=np.uint8)
        params = {'augmentation_intensity': 0.5}
        
        aug_image, aug_mask = self.strategy._synthetic_boundary_augmentation(
            image, mask, None, params
        )
        
        assert aug_image.shape == image.shape
        assert aug_mask.shape == mask.shape
        # Should have added new objects
        assert np.max(aug_mask) >= np.max(mask)


class TestBoundaryAugmentationDataset:
    """Test cases for BoundaryAugmentationDataset."""
    
    def test_dataset_wrapper(self):
        """Test dataset wrapper functionality."""
        # Mock base dataset
        base_dataset = Mock()
        base_dataset.__len__ = Mock(return_value=10)
        
        sample = {
            'image': torch.randn(3, 64, 64),
            'mask': torch.randint(0, 5, (64, 64))
        }
        base_dataset.__getitem__ = Mock(return_value=sample)
        
        # Create augmentation components
        strategy = AugmentationStrategy({'augmentation_intensity': 0.5})
        strategy.initialize()
        
        weakness_report = WeaknessReport(
            weakness_type='weak_boundary_detection',
            affected_classes=['person'],
            severity_score=0.5,
            spatial_distribution=np.random.rand(64, 64),
            suggested_fixes=['boundary_blur']
        )
        
        pipeline = strategy.create_augmentation_strategy(weakness_report)
        
        # Create augmented dataset
        aug_dataset = BoundaryAugmentationDataset(
            base_dataset, strategy, pipeline, augmentation_prob=1.0
        )
        
        assert len(aug_dataset) == 10
        
        # Test sample retrieval
        aug_sample = aug_dataset[0]
        assert 'image' in aug_sample
        assert 'mask' in aug_sample
        assert aug_sample['image'].shape == sample['image'].shape
        assert aug_sample['mask'].shape == sample['mask'].shape


if __name__ == '__main__':
    pytest.main([__file__])
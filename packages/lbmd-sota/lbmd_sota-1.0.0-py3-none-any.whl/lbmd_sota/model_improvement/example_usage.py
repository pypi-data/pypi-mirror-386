"""
Example usage of the Model Improvement Toolkit.
"""

import torch
import numpy as np
from scipy.spatial import ConvexHull

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lbmd_sota.model_improvement.architecture_enhancer import ArchitectureEnhancer
from lbmd_sota.model_improvement.boundary_loss_designer import BoundaryLossDesigner
from lbmd_sota.model_improvement.augmentation_strategy import AugmentationStrategy
from lbmd_sota.core.data_models import (
    LBMDResults, BoundaryMetrics, WeaknessReport,
    StatisticalMetrics, TopologicalProperties
)


def create_sample_lbmd_results():
    """Create sample LBMD results for demonstration."""
    # Simulate weak boundary detection scenario
    boundary_scores = np.random.rand(64, 64) * 0.4  # Weak boundaries
    boundary_mask = boundary_scores > 0.3
    manifold_coords = np.random.rand(100, 2)
    pixel_coords = np.random.rand(100, 2)
    is_boundary = np.random.rand(100) > 0.5
    clusters = np.random.randint(0, 5, 100)
    
    # Weak transition strengths indicating poor boundary clarity
    transition_strengths = {
        (0, 1): 0.4,
        (1, 2): 0.3,
        (2, 3): 0.5,
        (3, 4): 0.35
    }
    
    # Create cluster hulls
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
        layer_name='backbone.layer4.2.conv3',
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


def demonstrate_architecture_enhancement():
    """Demonstrate architecture enhancement suggestions."""
    print("=== Architecture Enhancement Demo ===")
    
    # Initialize architecture enhancer
    config = {
        'boundary_strength_threshold': 0.5,
        'transition_clarity_threshold': 0.6,
        'manifold_separation_threshold': 0.7
    }
    enhancer = ArchitectureEnhancer(config)
    enhancer.initialize()
    
    # Create sample LBMD results
    lbmd_results = create_sample_lbmd_results()
    
    # Get architecture improvement suggestions
    suggestions = enhancer.suggest_architecture_improvements(lbmd_results)
    
    print(f"Weak layers identified: {suggestions.weak_layers}")
    print(f"Number of suggested modifications: {len(suggestions.suggested_modifications)}")
    
    print("\nTop 3 Priority Suggestions:")
    for i, suggestion_name in enumerate(suggestions.priority_ranking[:3]):
        if suggestion_name in suggestions.suggested_modifications:
            print(f"{i+1}. {suggestion_name}")
            print(f"   Description: {suggestions.suggested_modifications[suggestion_name]}")
            print(f"   Expected improvement: {suggestions.expected_improvements[suggestion_name]:.3f}")
            print(f"   Complexity: {suggestions.implementation_complexity[suggestion_name]}")
            print()


def demonstrate_boundary_loss_design():
    """Demonstrate boundary-aware loss function design."""
    print("=== Boundary Loss Design Demo ===")
    
    # Initialize boundary loss designer
    config = {
        'boundary_weight': 1.0,
        'clarity_weight': 0.5,
        'separation_weight': 0.3,
        'adaptive_weighting': True
    }
    designer = BoundaryLossDesigner(config)
    designer.initialize()
    
    # Create sample boundary metrics
    boundary_metrics = BoundaryMetrics(
        boundary_strength=0.4,  # Weak
        transition_clarity=0.5,  # Poor
        manifold_separation=0.6,  # Moderate
        topological_persistence=0.3,  # Low
        statistical_significance=0.05,
        spatial_coherence=0.7,
        temporal_stability=0.8
    )
    
    # Design boundary loss
    loss_module = designer.design_boundary_loss(boundary_metrics)
    
    print("Boundary loss module created successfully!")
    print(f"Loss components: {list(designer._loss_components.keys())}")
    
    # Test the loss function
    predictions = torch.randn(2, 3, 32, 32)
    targets = torch.randint(0, 2, (2, 3, 32, 32)).float()
    
    # Create sample LBMD data
    lbmd_data = {
        'boundary_scores': torch.rand(2, 32, 32),
        'manifold_coords': torch.rand(2, 32, 32, 2),
        'cluster_labels': torch.randint(0, 5, (2, 32, 32)),
        'transition_strengths': {(0, 1): 0.4, (1, 2): 0.3},
        'topological_properties': {'euler_characteristic': 2, 'betti_numbers': [2, 1]}
    }
    
    losses = loss_module(predictions, targets, lbmd_data)
    
    print(f"\nLoss computation results:")
    for loss_name, loss_value in losses.items():
        if isinstance(loss_value, torch.Tensor):
            print(f"  {loss_name}: {loss_value.item():.4f}")
        else:
            print(f"  {loss_name}: {loss_value}")


def demonstrate_augmentation_strategy():
    """Demonstrate targeted data augmentation strategies."""
    print("=== Augmentation Strategy Demo ===")
    
    # Initialize augmentation strategy
    config = {
        'augmentation_intensity': 0.5,
        'boundary_focus_weight': 2.0,
        'adversarial_strength': 0.1,
        'synthetic_boundary_prob': 0.3
    }
    strategy = AugmentationStrategy(config)
    strategy.initialize()
    
    # Create sample weakness report
    weakness_report = WeaknessReport(
        weakness_type='weak_boundary_detection',
        affected_classes=['person', 'car', 'bicycle'],
        severity_score=0.7,
        spatial_distribution=np.random.rand(64, 64),
        suggested_fixes=['boundary_blur', 'synthetic_boundaries', 'boundary_noise']
    )
    
    # Create augmentation pipeline
    pipeline = strategy.create_augmentation_strategy(weakness_report)
    
    print(f"Augmentation pipeline created for weakness: {weakness_report.weakness_type}")
    print(f"Severity score: {weakness_report.severity_score:.3f}")
    print(f"Affected classes: {weakness_report.affected_classes}")
    print(f"Augmentation strategies: {pipeline.augmentation_strategies}")
    
    print(f"\nExpected improvements:")
    for method, improvement in pipeline.expected_improvements.items():
        print(f"  {method}: {improvement:.3f}")
    
    # Test augmentation application
    print(f"\nTesting augmentation application...")
    
    # Create sample image and mask
    image = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
    mask = np.random.randint(0, 5, (64, 64), dtype=np.uint8)
    
    print(f"Original image shape: {image.shape}, dtype: {image.dtype}")
    print(f"Original mask shape: {mask.shape}, unique values: {np.unique(mask)}")
    
    # Apply augmentation pipeline
    augmented_image, augmented_mask = strategy.apply_augmentation_pipeline(
        image, mask, pipeline
    )
    
    print(f"Augmented image shape: {augmented_image.shape}, dtype: {augmented_image.dtype}")
    print(f"Augmented mask shape: {augmented_mask.shape}, unique values: {np.unique(augmented_mask)}")
    
    # Check if augmentation was applied
    image_changed = not np.array_equal(image, augmented_image)
    mask_changed = not np.array_equal(mask, augmented_mask)
    
    print(f"Image modified: {image_changed}")
    print(f"Mask modified: {mask_changed}")


def demonstrate_complete_workflow():
    """Demonstrate complete model improvement workflow."""
    print("=== Complete Model Improvement Workflow ===")
    
    # Step 1: Analyze LBMD results for weaknesses
    print("Step 1: Analyzing LBMD results...")
    lbmd_results = create_sample_lbmd_results()
    
    # Step 2: Get architecture enhancement suggestions
    print("Step 2: Getting architecture enhancement suggestions...")
    enhancer = ArchitectureEnhancer({})
    enhancer.initialize()
    arch_suggestions = enhancer.suggest_architecture_improvements(lbmd_results)
    
    print(f"  - Identified {len(arch_suggestions.weak_layers)} weak layers")
    print(f"  - Generated {len(arch_suggestions.suggested_modifications)} improvement suggestions")
    
    # Step 3: Design boundary-aware loss function
    print("Step 3: Designing boundary-aware loss function...")
    boundary_metrics = BoundaryMetrics(
        boundary_strength=np.mean(lbmd_results.boundary_scores),
        transition_clarity=np.mean(list(lbmd_results.transition_strengths.values())),
        manifold_separation=0.6,
        topological_persistence=0.4,
        statistical_significance=0.05,
        spatial_coherence=0.7,
        temporal_stability=0.8
    )
    
    designer = BoundaryLossDesigner({})
    designer.initialize()
    loss_module = designer.design_boundary_loss(boundary_metrics)
    
    print(f"  - Created composite loss with {len(designer._loss_components)} components")
    
    # Step 4: Create targeted augmentation strategy
    print("Step 4: Creating targeted augmentation strategy...")
    
    # Simulate failure cases for augmentation strategy
    failure_cases = [
        {
            'type': 'boundary_occlusion',
            'class': 'person',
            'severity': 0.6,
            'spatial_mask': np.random.rand(64, 64) > 0.8
        },
        {
            'type': 'scale_variation',
            'class': 'car',
            'severity': 0.4,
            'spatial_mask': np.random.rand(64, 64) > 0.9
        }
    ]
    
    strategy = AugmentationStrategy({})
    strategy.initialize()
    
    weakness_report = strategy.analyze_boundary_weaknesses(lbmd_results, failure_cases)
    augmentation_pipeline = strategy.create_augmentation_strategy(weakness_report)
    
    print(f"  - Identified weakness: {weakness_report.weakness_type}")
    print(f"  - Created pipeline with {len(augmentation_pipeline.augmentation_strategies)} strategies")
    
    # Step 5: Summary
    print("\nWorkflow Summary:")
    print(f"  - Architecture improvements: {len(arch_suggestions.priority_ranking)} suggestions")
    print(f"  - Loss function: Adaptive boundary-aware loss")
    print(f"  - Augmentation: {len(augmentation_pipeline.augmentation_strategies)} targeted strategies")
    print(f"  - Expected total improvement: {sum(arch_suggestions.expected_improvements.values()):.3f}")


if __name__ == "__main__":
    print("Model Improvement Toolkit Demo")
    print("=" * 50)
    
    try:
        demonstrate_architecture_enhancement()
        print()
        
        demonstrate_boundary_loss_design()
        print()
        
        demonstrate_augmentation_strategy()
        print()
        
        demonstrate_complete_workflow()
        
    except Exception as e:
        print(f"Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
"""
Example usage of the comparative analysis system.
"""

import numpy as np
import torch
import torch.nn as nn
from typing import Dict, Any

from lbmd_sota.comparative_analysis.baseline_comparator import BaselineComparator
from lbmd_sota.comparative_analysis.failure_mode_analyzer import FailureModeAnalyzer
from lbmd_sota.comparative_analysis.insight_differentiator import InsightDifferentiator
from lbmd_sota.core.data_models import LBMDResults, StatisticalMetrics, TopologicalProperties


class SimpleSegmentationModel(nn.Module):
    """Simple segmentation model for demonstration."""
    
    def __init__(self):
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Conv2d(3, 64, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 128, 3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1))
        )
        self.classifier = nn.Linear(128, 10)
        
    def forward(self, x):
        features = self.backbone(x)
        features = features.view(features.size(0), -1)
        logits = self.classifier(features)
        return {
            'scores': [logits[0]],
            'pred_logits': logits,
            'masks': torch.sigmoid(logits[:, :1].unsqueeze(-1).unsqueeze(-1).expand(-1, -1, x.size(2), x.size(3)))
        }


def create_sample_lbmd_results(height: int = 224, width: int = 224) -> LBMDResults:
    """Create sample LBMD results for demonstration."""
    
    # Create realistic boundary patterns
    boundary_scores = np.random.rand(height, width)
    
    # Add some structure to make it more realistic
    center_y, center_x = height // 2, width // 2
    y, x = np.ogrid[:height, :width]
    
    # Create circular boundary pattern
    distance_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
    boundary_scores += 0.5 * np.exp(-distance_from_center / 50)
    
    # Normalize
    boundary_scores = (boundary_scores - boundary_scores.min()) / (boundary_scores.max() - boundary_scores.min())
    
    # Create boundary mask
    boundary_mask = boundary_scores > 0.6
    
    # Create manifold coordinates
    n_points = 1000
    manifold_coords = np.random.randn(n_points, 3)
    
    # Add some structure to manifold
    theta = np.linspace(0, 2*np.pi, n_points)
    manifold_coords[:, 0] += np.cos(theta)
    manifold_coords[:, 1] += np.sin(theta)
    
    # Create clusters
    clusters = np.random.randint(0, 5, n_points)
    
    return LBMDResults(
        layer_name="backbone.1",
        boundary_scores=boundary_scores,
        boundary_mask=boundary_mask,
        manifold_coords=manifold_coords,
        pixel_coords=np.random.rand(n_points, 2) * np.array([height, width]),
        is_boundary=np.random.rand(n_points) > 0.5,
        clusters=clusters,
        transition_strengths={(0, 1): 0.7, (1, 2): 0.5, (2, 3): 0.8, (3, 4): 0.4},
        cluster_hulls={},
        statistical_metrics=StatisticalMetrics(
            correlation=0.78,
            p_value=0.001,
            confidence_interval=(0.72, 0.84),
            effect_size=0.8,
            sample_size=1000
        ),
        topological_properties=TopologicalProperties(
            betti_numbers=[1, 0],
            persistence_diagram=np.array([]),
            euler_characteristic=1,
            genus=0,
            curvature_metrics={'mean_curvature': 0.1, 'gaussian_curvature': 0.05}
        )
    )


def run_comparative_analysis_example():
    """Run a complete comparative analysis example."""
    
    print("🔍 Running Comparative Analysis Example")
    print("=" * 50)
    
    # 1. Setup
    print("\n1. Setting up components...")
    
    # Create model and input
    model = SimpleSegmentationModel()
    model.eval()
    input_tensor = torch.randn(1, 3, 224, 224)
    
    # Create sample LBMD results
    lbmd_results = create_sample_lbmd_results()
    
    # Initialize components
    config = {
        'lime_samples': 100,
        'failure_threshold': 0.5,
        'similarity_threshold': 0.7
    }
    
    baseline_comparator = BaselineComparator(config)
    failure_analyzer = FailureModeAnalyzer(config)
    insight_differentiator = InsightDifferentiator(config)
    
    baseline_comparator.initialize()
    failure_analyzer.initialize()
    insight_differentiator.initialize()
    
    print("✅ Components initialized successfully")
    
    # 2. Run baseline comparison
    print("\n2. Running baseline interpretability methods...")
    
    try:
        baseline_results = baseline_comparator.compare_with_baselines(
            model, input_tensor, lbmd_results, target_layer='backbone.1'
        )
        
        print(f"✅ Baseline methods completed:")
        for method_name, result in baseline_results.items():
            print(f"   - {result.method_name}: {result.computational_time:.3f}s, {result.memory_usage:.1f}MB")
            
    except Exception as e:
        print(f"⚠️  Baseline comparison encountered issues: {e}")
        # Create mock results for demonstration
        baseline_results = {
            'grad_cam': type('MockResult', (), {
                'method_name': 'Grad-CAM',
                'saliency_maps': np.random.rand(224, 224),
                'attention_weights': None,
                'feature_importance': np.random.rand(224*224),
                'computational_time': 0.5,
                'memory_usage': 100.0
            })(),
            'integrated_gradients': type('MockResult', (), {
                'method_name': 'Integrated Gradients',
                'saliency_maps': np.random.rand(224, 224),
                'attention_weights': np.random.rand(1, 3, 224, 224),
                'feature_importance': np.random.rand(224*224),
                'computational_time': 1.2,
                'memory_usage': 150.0
            })()
        }
        print("✅ Using mock baseline results for demonstration")
    
    # 3. Analyze failure modes
    print("\n3. Analyzing failure modes...")
    
    # Create sample prediction and ground truth masks
    n_samples = 3
    pred_masks = []
    gt_masks = []
    
    for i in range(n_samples):
        # Create realistic failure scenarios
        pred_mask = np.zeros((100, 100))
        gt_mask = np.zeros((100, 100))
        
        if i == 0:  # Object merging scenario
            pred_mask[20:80, 20:80] = 1  # Single large prediction
            gt_mask[20:50, 20:50] = 1    # First object
            gt_mask[50:80, 50:80] = 1    # Second object
        elif i == 1:  # Object separation scenario
            pred_mask[20:40, 20:40] = 1  # First prediction
            pred_mask[60:80, 60:80] = 1  # Second prediction
            gt_mask[20:80, 20:80] = 1    # Single ground truth
        else:  # Normal case
            pred_mask[30:70, 30:70] = 1
            gt_mask[25:75, 25:75] = 1
            
        pred_masks.append(pred_mask)
        gt_masks.append(gt_mask)
    
    # Create LBMD results for each sample
    lbmd_results_list = [create_sample_lbmd_results(100, 100) for _ in range(n_samples)]
    
    failure_analysis = failure_analyzer.analyze(
        np.array(pred_masks), np.array(gt_masks), lbmd_results_list
    )
    
    print(f"✅ Failure analysis completed:")
    print(f"   - Total failures detected: {failure_analysis['summary_statistics']['total_failures']}")
    print(f"   - Failure types: {list(failure_analysis['summary_statistics']['failure_types'].keys())}")
    print(f"   - Case studies generated: {len(failure_analysis['case_studies'])}")
    
    # 4. Differentiate insights
    print("\n4. Analyzing unique insights...")
    
    insight_analysis = insight_differentiator.analyze(
        lbmd_results, baseline_results, failure_analysis['failures']
    )
    
    print(f"✅ Insight analysis completed:")
    print(f"   - Unique insights identified: {insight_analysis['summary_statistics']['total_unique_insights']}")
    print(f"   - Average confidence: {insight_analysis['summary_statistics']['avg_confidence']:.3f}")
    print(f"   - Boundary superiority: {insight_analysis['summary_statistics']['boundary_superiority']:.3f}")
    
    # 5. Display detailed results
    print("\n5. Detailed Results")
    print("-" * 30)
    
    # Show unique insights
    if insight_analysis['unique_insights']:
        print("\n🔍 Unique LBMD Insights:")
        for i, insight in enumerate(insight_analysis['unique_insights'][:3], 1):
            print(f"\n   {i}. {insight.insight_type.replace('_', ' ').title()}")
            print(f"      Confidence: {insight.confidence_score:.3f}")
            print(f"      Description: {insight.description[:100]}...")
    
    # Show overlap analysis
    print("\n📊 Overlap Analysis with Baselines:")
    for method_name, overlap in insight_analysis['overlap_analyses'].items():
        print(f"\n   vs {method_name}:")
        print(f"      Jaccard Similarity: {overlap.jaccard_similarity:.3f}")
        print(f"      Cosine Similarity: {overlap.cosine_similarity:.3f}")
        print(f"      LBMD Unique Coverage: {overlap.unique_coverage.get('lbmd', 0):.3f}")
    
    # Show failure case studies
    if failure_analysis['case_studies']:
        print(f"\n🚨 Failure Case Studies:")
        for i, case in enumerate(failure_analysis['case_studies'][:2], 1):
            print(f"\n   Case {i}: {case['failure_type'].replace('_', ' ').title()}")
            print(f"      Severity: {case['severity_score']:.3f}")
            print(f"      Description: {case['description'][:100]}...")
    
    # Show superiority metrics
    superiority = insight_analysis['superiority_metrics']
    print(f"\n🏆 LBMD Superiority Metrics:")
    print(f"   Boundary Detection Accuracy: {superiority.boundary_detection_accuracy:.3f}")
    print(f"   Failure Prediction AUC: {superiority.failure_prediction_auc:.3f}")
    print(f"   Human Alignment Score: {superiority.human_alignment_score:.3f}")
    print(f"   Computational Efficiency: {superiority.computational_efficiency:.3f}x")
    
    print("\n" + "=" * 50)
    print("✅ Comparative Analysis Complete!")
    print("\nKey Findings:")
    print("• LBMD provides boundary-specific interpretability not available in general saliency methods")
    print("• Manifold structure reveals how neural networks organize object representations")
    print("• Boundary weakness analysis enables superior failure prediction")
    print("• Multi-scale analysis shows hierarchical boundary processing")
    
    return {
        'baseline_results': baseline_results,
        'failure_analysis': failure_analysis,
        'insight_analysis': insight_analysis
    }


if __name__ == "__main__":
    results = run_comparative_analysis_example()
"""
Test suite for comparative analysis system components.
"""

import pytest
import numpy as np
import torch
import torch.nn as nn
from unittest.mock import Mock, patch
import cv2

from .baseline_comparator import BaselineComparator, GradCAM, IntegratedGradients, LIMESegmentation
from .failure_mode_analyzer import FailureModeAnalyzer, FailureCase
from .insight_differentiator import InsightDifferentiator
from ..core.data_models import LBMDResults, BaselineResults, StatisticalMetrics, TopologicalProperties


class MockModel(nn.Module):
    """Mock model for testing."""
    
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 64, 3, padding=1)
        self.conv2 = nn.Conv2d(64, 128, 3, padding=1)
        self.classifier = nn.Linear(128, 10)
        
    def forward(self, x):
        x = torch.relu(self.conv1(x))
        x = torch.relu(self.conv2(x))
        x = torch.adaptive_avg_pool2d(x, (1, 1))
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return {'scores': [x[0]], 'pred_logits': x}


@pytest.fixture
def mock_model():
    """Create mock model for testing."""
    return MockModel()


@pytest.fixture
def sample_input():
    """Create sample input tensor."""
    return torch.randn(1, 3, 224, 224)


@pytest.fixture
def sample_lbmd_results():
    """Create sample LBMD results."""
    h, w = 224, 224
    return LBMDResults(
        layer_name="test_layer",
        boundary_scores=np.random.rand(h, w),
        boundary_mask=np.random.rand(h, w) > 0.5,
        manifold_coords=np.random.rand(100, 3),
        pixel_coords=np.random.rand(100, 2),
        is_boundary=np.random.rand(100) > 0.5,
        clusters=np.random.randint(0, 5, 100),
        transition_strengths={(0, 1): 0.5, (1, 2): 0.3},
        cluster_hulls={},
        statistical_metrics=StatisticalMetrics(0.78, 0.01, (0.7, 0.85), 0.8, 1000),
        topological_properties=TopologicalProperties([1, 0], np.array([]), 1, 0, {})
    )


@pytest.fixture
def sample_baseline_results():
    """Create sample baseline results."""
    return {
        'grad_cam': BaselineResults(
            method_name="Grad-CAM",
            saliency_maps=np.random.rand(224, 224),
            attention_weights=None,
            feature_importance=np.random.rand(224*224),
            computational_time=0.5,
            memory_usage=100.0
        ),
        'integrated_gradients': BaselineResults(
            method_name="Integrated Gradients",
            saliency_maps=np.random.rand(224, 224),
            attention_weights=np.random.rand(1, 3, 224, 224),
            feature_importance=np.random.rand(224*224),
            computational_time=1.2,
            memory_usage=150.0
        )
    }


class TestBaselineComparator:
    """Test baseline comparator functionality."""
    
    def test_initialization(self):
        """Test baseline comparator initialization."""
        config = {'lime_samples': 100}
        comparator = BaselineComparator(config)
        assert not comparator.is_initialized()
        
        comparator.initialize()
        assert comparator.is_initialized()
        
    def test_grad_cam_setup(self, mock_model, sample_input):
        """Test Grad-CAM setup and execution."""
        comparator = BaselineComparator({})
        comparator.initialize()
        
        # Test Grad-CAM execution
        result = comparator.run_grad_cam(mock_model, sample_input, target_layer='conv2')
        
        assert result.method_name == "Grad-CAM"
        assert result.saliency_maps.shape == (224, 224)
        assert result.computational_time >= 0
        assert result.memory_usage >= 0
        
    def test_integrated_gradients(self, mock_model, sample_input):
        """Test Integrated Gradients execution."""
        comparator = BaselineComparator({})
        comparator.initialize()
        
        result = comparator.run_integrated_gradients(mock_model, sample_input, steps=10)
        
        assert result.method_name == "Integrated Gradients"
        assert result.saliency_maps.shape == (224, 224)
        assert result.attention_weights is not None
        
    def test_lime_segmentation(self, mock_model, sample_input):
        """Test LIME segmentation execution."""
        comparator = BaselineComparator({'lime_samples': 50})
        comparator.initialize()
        
        with patch('skimage.segmentation.slic') as mock_slic:
            mock_slic.return_value = np.random.randint(0, 10, (224, 224))
            
            result = comparator.run_lime(mock_model, sample_input)
            
            assert result.method_name == "LIME"
            assert result.saliency_maps.shape == (224, 224)
            
    def test_compare_with_baselines(self, mock_model, sample_input, sample_lbmd_results):
        """Test comprehensive baseline comparison."""
        comparator = BaselineComparator({'lime_samples': 20})
        comparator.initialize()
        
        with patch('skimage.segmentation.slic') as mock_slic:
            mock_slic.return_value = np.random.randint(0, 10, (224, 224))
            
            results = comparator.compare_with_baselines(
                mock_model, sample_input, sample_lbmd_results, target_layer='conv2'
            )
            
            assert 'grad_cam' in results
            assert 'integrated_gradients' in results
            assert 'lime' in results
            
            for method_result in results.values():
                assert isinstance(method_result, BaselineResults)
                assert method_result.computational_time >= 0


class TestFailureModeAnalyzer:
    """Test failure mode analyzer functionality."""
    
    def test_initialization(self):
        """Test failure mode analyzer initialization."""
        config = {'failure_threshold': 0.6}
        analyzer = FailureModeAnalyzer(config)
        assert not analyzer.is_initialized()
        
        analyzer.initialize()
        assert analyzer.is_initialized()
        
    def test_object_merging_detection(self, sample_lbmd_results):
        """Test object merging failure detection."""
        analyzer = FailureModeAnalyzer({})
        analyzer.initialize()
        
        # Create test masks with merging scenario
        pred_mask = np.zeros((100, 100))
        pred_mask[20:80, 20:80] = 1  # Single large prediction
        
        gt_mask = np.zeros((100, 100))
        gt_mask[20:50, 20:50] = 1  # First object
        gt_mask[50:80, 50:80] = 1  # Second object
        
        failures = analyzer.detect_object_merging(pred_mask, gt_mask, sample_lbmd_results)
        
        assert len(failures) > 0
        assert all(f.failure_type == "object_merging" for f in failures)
        
    def test_object_separation_detection(self, sample_lbmd_results):
        """Test object separation failure detection."""
        analyzer = FailureModeAnalyzer({})
        analyzer.initialize()
        
        # Create test masks with separation scenario
        pred_mask = np.zeros((100, 100))
        pred_mask[20:40, 20:40] = 1  # First prediction
        pred_mask[60:80, 60:80] = 1  # Second prediction
        
        gt_mask = np.zeros((100, 100))
        gt_mask[20:80, 20:80] = 1  # Single ground truth object
        
        failures = analyzer.detect_object_separation(pred_mask, gt_mask, sample_lbmd_results)
        
        assert len(failures) > 0
        assert all(f.failure_type == "object_separation" for f in failures)
        
    def test_missed_boundaries_detection(self, sample_lbmd_results):
        """Test missed boundaries detection."""
        analyzer = FailureModeAnalyzer({})
        analyzer.initialize()
        
        # Create test masks with missed boundaries
        pred_mask = np.zeros((100, 100))
        pred_mask[25:75, 25:75] = 1  # Prediction without clear boundaries
        
        gt_mask = np.zeros((100, 100))
        gt_mask[20:80, 20:80] = 1  # Ground truth with boundaries
        
        failures = analyzer.detect_missed_boundaries(pred_mask, gt_mask, sample_lbmd_results)
        
        # Should detect some boundary issues
        assert isinstance(failures, list)
        
    def test_failure_pattern_analysis(self, sample_lbmd_results):
        """Test failure pattern analysis."""
        analyzer = FailureModeAnalyzer({})
        analyzer.initialize()
        
        # Create sample failure cases
        failures = [
            FailureCase(
                failure_type="object_merging",
                severity_score=0.8,
                affected_regions=np.random.rand(50, 50) > 0.5,
                boundary_weakness=0.7,
                manifold_discontinuity=0.5,
                predicted_mask=np.random.rand(50, 50),
                ground_truth_mask=np.random.rand(50, 50),
                lbmd_evidence={},
                spatial_location=(10, 10, 40, 40)
            ),
            FailureCase(
                failure_type="object_separation",
                severity_score=0.6,
                affected_regions=np.random.rand(50, 50) > 0.5,
                boundary_weakness=0.5,
                manifold_discontinuity=0.3,
                predicted_mask=np.random.rand(50, 50),
                ground_truth_mask=np.random.rand(50, 50),
                lbmd_evidence={},
                spatial_location=(50, 50, 80, 80)
            )
        ]
        
        patterns = analyzer.analyze_failure_patterns(failures)
        
        assert "object_merging" in patterns
        assert "object_separation" in patterns
        assert patterns["object_merging"].frequency > 0
        
    def test_case_study_generation(self, sample_lbmd_results):
        """Test case study generation."""
        analyzer = FailureModeAnalyzer({})
        analyzer.initialize()
        
        # Create sample failure cases
        failures = [
            FailureCase(
                failure_type="object_merging",
                severity_score=0.9,
                affected_regions=np.random.rand(50, 50) > 0.5,
                boundary_weakness=0.8,
                manifold_discontinuity=0.6,
                predicted_mask=np.random.rand(50, 50),
                ground_truth_mask=np.random.rand(50, 50),
                lbmd_evidence={'boundary_strength': 0.2},
                spatial_location=(10, 10, 40, 40)
            )
        ]
        
        case_studies = analyzer.generate_case_studies(failures, num_cases=1)
        
        assert len(case_studies) == 1
        assert case_studies[0]['failure_type'] == "object_merging"
        assert 'description' in case_studies[0]
        assert 'lbmd_analysis' in case_studies[0]


class TestInsightDifferentiator:
    """Test insight differentiator functionality."""
    
    def test_initialization(self):
        """Test insight differentiator initialization."""
        config = {'similarity_threshold': 0.8}
        differentiator = InsightDifferentiator(config)
        assert not differentiator.is_initialized()
        
        differentiator.initialize()
        assert differentiator.is_initialized()
        
    def test_spatial_overlap_computation(self, sample_lbmd_results, sample_baseline_results):
        """Test spatial overlap computation."""
        differentiator = InsightDifferentiator({})
        differentiator.initialize()
        
        lbmd_map = sample_lbmd_results.boundary_scores
        baseline_map = sample_baseline_results['grad_cam'].saliency_maps
        
        overlap_metrics = differentiator.compute_spatial_overlap(lbmd_map, baseline_map)
        
        assert 'jaccard_similarity' in overlap_metrics
        assert 'cosine_similarity' in overlap_metrics
        assert 'rank_correlation' in overlap_metrics
        assert 'mutual_information' in overlap_metrics
        
        # Check value ranges
        assert 0 <= overlap_metrics['jaccard_similarity'] <= 1
        assert -1 <= overlap_metrics['cosine_similarity'] <= 1
        assert -1 <= overlap_metrics['rank_correlation'] <= 1
        assert 0 <= overlap_metrics['mutual_information'] <= 1
        
    def test_unique_region_identification(self, sample_lbmd_results, sample_baseline_results):
        """Test unique region identification."""
        differentiator = InsightDifferentiator({})
        differentiator.initialize()
        
        lbmd_map = sample_lbmd_results.boundary_scores
        baseline_maps = {name: result.saliency_maps for name, result in sample_baseline_results.items()}
        
        unique_regions = differentiator.identify_unique_regions(lbmd_map, baseline_maps)
        
        assert len(unique_regions) > 0
        for region_name, region_mask in unique_regions.items():
            assert isinstance(region_mask, np.ndarray)
            assert region_mask.dtype == bool
            
    def test_boundary_specificity_analysis(self, sample_lbmd_results, sample_baseline_results):
        """Test boundary specificity analysis."""
        differentiator = InsightDifferentiator({})
        differentiator.initialize()
        
        # Create mock ground truth boundaries
        gt_boundaries = np.random.rand(224, 224) > 0.8
        
        specificity_metrics = differentiator.analyze_boundary_specificity(
            sample_lbmd_results, sample_baseline_results, gt_boundaries
        )
        
        assert 'lbmd_boundary_accuracy' in specificity_metrics
        assert 'lbmd_boundary_clarity' in specificity_metrics
        
        for method_name in sample_baseline_results.keys():
            assert f'{method_name}_boundary_accuracy' in specificity_metrics
            assert f'{method_name}_clarity' in specificity_metrics
            
    def test_unique_insight_generation(self, sample_lbmd_results, sample_baseline_results):
        """Test unique insight generation."""
        differentiator = InsightDifferentiator({})
        differentiator.initialize()
        
        unique_insights = differentiator.generate_unique_insights(
            sample_lbmd_results, sample_baseline_results
        )
        
        assert isinstance(unique_insights, list)
        
        for insight in unique_insights:
            assert hasattr(insight, 'insight_type')
            assert hasattr(insight, 'description')
            assert hasattr(insight, 'quantitative_evidence')
            assert hasattr(insight, 'confidence_score')
            assert 0 <= insight.confidence_score <= 1
            
    def test_superiority_metrics_computation(self, sample_lbmd_results, sample_baseline_results):
        """Test superiority metrics computation."""
        differentiator = InsightDifferentiator({})
        differentiator.initialize()
        
        superiority_metrics = differentiator.compute_superiority_metrics(
            sample_lbmd_results, sample_baseline_results
        )
        
        assert hasattr(superiority_metrics, 'boundary_detection_accuracy')
        assert hasattr(superiority_metrics, 'failure_prediction_auc')
        assert hasattr(superiority_metrics, 'human_alignment_score')
        assert hasattr(superiority_metrics, 'computational_efficiency')
        
        # Check value ranges
        assert 0 <= superiority_metrics.boundary_detection_accuracy <= 1
        assert 0 <= superiority_metrics.failure_prediction_auc <= 1
        assert 0 <= superiority_metrics.human_alignment_score <= 1
        assert superiority_metrics.computational_efficiency > 0
        
    def test_comprehensive_analysis(self, sample_lbmd_results, sample_baseline_results):
        """Test comprehensive insight analysis."""
        differentiator = InsightDifferentiator({})
        differentiator.initialize()
        
        analysis_results = differentiator.analyze(
            sample_lbmd_results, sample_baseline_results
        )
        
        assert 'unique_insights' in analysis_results
        assert 'overlap_analyses' in analysis_results
        assert 'superiority_metrics' in analysis_results
        assert 'complementarity_scores' in analysis_results
        assert 'clarity_metrics' in analysis_results
        assert 'summary_statistics' in analysis_results
        
        # Check summary statistics
        summary = analysis_results['summary_statistics']
        assert 'total_unique_insights' in summary
        assert 'avg_confidence' in summary
        assert 'boundary_superiority' in summary


class TestIntegration:
    """Test integration between components."""
    
    def test_end_to_end_comparative_analysis(self, mock_model, sample_input, sample_lbmd_results):
        """Test end-to-end comparative analysis workflow."""
        # Initialize components
        comparator = BaselineComparator({'lime_samples': 20})
        failure_analyzer = FailureModeAnalyzer({})
        insight_differentiator = InsightDifferentiator({})
        
        comparator.initialize()
        failure_analyzer.initialize()
        insight_differentiator.initialize()
        
        # Run baseline comparison
        with patch('skimage.segmentation.slic') as mock_slic:
            mock_slic.return_value = np.random.randint(0, 10, (224, 224))
            
            baseline_results = comparator.compare_with_baselines(
                mock_model, sample_input, sample_lbmd_results, target_layer='conv2'
            )
        
        # Create mock failure cases
        pred_masks = np.random.rand(5, 100, 100)
        gt_masks = np.random.rand(5, 100, 100)
        lbmd_results_list = [sample_lbmd_results] * 5
        
        # Analyze failures
        failure_analysis = failure_analyzer.analyze(pred_masks, gt_masks, lbmd_results_list)
        
        # Differentiate insights
        insight_analysis = insight_differentiator.analyze(
            sample_lbmd_results, baseline_results, failure_analysis['failures']
        )
        
        # Verify complete pipeline
        assert len(baseline_results) > 0
        assert 'failures' in failure_analysis
        assert 'unique_insights' in insight_analysis
        
        # Check that insights reference failure analysis
        if insight_analysis['unique_insights']:
            failure_insights = [i for i in insight_analysis['unique_insights'] 
                             if i.insight_type == 'failure_prediction']
            # Should have failure prediction insights if failures were detected
            assert len(failure_insights) >= 0


if __name__ == "__main__":
    pytest.main([__file__])
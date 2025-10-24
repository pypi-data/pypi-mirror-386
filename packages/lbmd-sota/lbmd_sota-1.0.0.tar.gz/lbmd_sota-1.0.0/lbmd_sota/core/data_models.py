"""
Core data models and structures for LBMD SOTA framework.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
from scipy.spatial import ConvexHull


@dataclass
class StatisticalMetrics:
    """Statistical metrics for boundary analysis."""
    correlation: float
    p_value: float
    confidence_interval: Tuple[float, float]
    effect_size: float
    sample_size: int


@dataclass
class TopologicalProperties:
    """Topological properties of boundary manifolds."""
    betti_numbers: Dict[int, int]
    persistence_diagram: Dict[str, List[Tuple[float, float]]]
    topological_entropy: float
    persistent_entropy: Dict[str, float]
    curvature_statistics: Dict[str, float]
    local_dimensionality: np.ndarray
    persistence_landscapes: Dict[str, np.ndarray]
    euler_characteristic: Optional[int] = None
    genus: Optional[int] = None


@dataclass
class LBMDResults:
    """Comprehensive results from LBMD analysis."""
    layer_name: str
    boundary_scores: np.ndarray
    boundary_mask: np.ndarray
    manifold_coords: np.ndarray
    pixel_coords: np.ndarray
    is_boundary: np.ndarray
    clusters: np.ndarray
    transition_strengths: Dict[Tuple[int, int], float]
    cluster_hulls: Dict[int, ConvexHull]
    statistical_metrics: StatisticalMetrics
    topological_properties: TopologicalProperties
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DatasetResults:
    """Results for a specific dataset."""
    dataset_name: str
    num_samples: int
    lbmd_results: List[LBMDResults]
    performance_metrics: Dict[str, float]
    failure_cases: List[Dict[str, Any]]


@dataclass
class ModelResults:
    """Results for a specific model architecture."""
    model_name: str
    architecture_type: str
    layer_results: Dict[str, LBMDResults]
    overall_metrics: Dict[str, float]
    computational_cost: Dict[str, float]


@dataclass
class CorrelationAnalysis:
    """Correlation analysis between boundary metrics and performance."""
    correlation_coefficient: float
    p_value: float
    confidence_interval: Tuple[float, float]
    sample_correlations: List[float]
    bootstrap_results: Dict[str, Any]


@dataclass
class SignificanceTest:
    """Statistical significance test results."""
    test_statistic: float
    p_value: float
    critical_value: float
    effect_size: float
    power_analysis: Dict[str, float]


@dataclass
class EffectSizeAnalysis:
    """Effect size analysis for practical significance."""
    cohens_d: float
    eta_squared: float
    confidence_interval: Tuple[float, float]
    interpretation: str





@dataclass
class ValidationResults:
    """Results from empirical validation across datasets and models."""
    dataset_results: Dict[str, DatasetResults]
    model_results: Dict[str, ModelResults]
    correlation_analysis: CorrelationAnalysis
    statistical_significance: SignificanceTest
    effect_sizes: EffectSizeAnalysis
    cross_validation_scores: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BaselineResults:
    """Results from baseline interpretability methods."""
    method_name: str
    saliency_maps: np.ndarray
    attention_weights: Optional[np.ndarray]
    feature_importance: np.ndarray
    computational_time: float
    memory_usage: float


@dataclass
class UniqueInsight:
    """Unique insight provided by LBMD vs baselines."""
    insight_type: str
    description: str
    quantitative_evidence: Dict[str, float]
    visual_evidence: Optional[np.ndarray]
    confidence_score: float


@dataclass
class OverlapAnalysis:
    """Analysis of overlap between different interpretability methods."""
    jaccard_similarity: float
    cosine_similarity: float
    rank_correlation: float
    unique_coverage: Dict[str, float]


@dataclass
class SuperiorityMetrics:
    """Metrics demonstrating LBMD superiority over baselines."""
    boundary_detection_accuracy: float
    failure_prediction_auc: float
    human_alignment_score: float
    computational_efficiency: float


@dataclass
class ComparisonResults:
    """Results comparing LBMD with baseline methods."""
    lbmd_insights: LBMDResults
    baseline_results: Dict[str, BaselineResults]
    unique_insights: List[UniqueInsight]
    overlap_analysis: OverlapAnalysis
    superiority_metrics: SuperiorityMetrics
    statistical_comparison: Dict[str, SignificanceTest]


@dataclass
class BoundaryMetrics:
    """Quantitative metrics for boundary analysis."""
    boundary_strength: float
    transition_clarity: float
    manifold_separation: float
    topological_persistence: float
    statistical_significance: float
    spatial_coherence: float
    temporal_stability: float


@dataclass
class ArchitecturalSuggestions:
    """Suggestions for architectural improvements based on LBMD analysis."""
    weak_layers: List[str]
    suggested_modifications: Dict[str, str]
    expected_improvements: Dict[str, float]
    implementation_complexity: Dict[str, str]
    priority_ranking: List[str]


@dataclass
class WeaknessReport:
    """Report of identified weaknesses in boundary detection."""
    weakness_type: str
    affected_classes: List[str]
    severity_score: float
    spatial_distribution: np.ndarray
    suggested_fixes: List[str]


@dataclass
class AugmentationPipeline:
    """Data augmentation pipeline based on LBMD insights."""
    augmentation_strategies: List[str]
    target_weaknesses: List[str]
    expected_improvements: Dict[str, float]
    implementation_details: Dict[str, Any]


@dataclass
class ExperimentConfig:
    """Configuration for LBMD experiments."""
    experiment_name: str
    datasets: List[str]
    models: List[str]
    parameters: Dict[str, Any]
    output_directory: str
    random_seed: int = 42
    parallel_jobs: int = 1
    save_intermediate: bool = True


@dataclass
class ManifoldData:
    """Data structure for manifold representations."""
    coordinates: np.ndarray
    labels: np.ndarray
    distances: np.ndarray
    neighborhoods: Dict[int, List[int]]
    embedding_method: str
    parameters: Dict[str, Any]


@dataclass
class InteractiveVisualization:
    """Interactive visualization data structure."""
    plot_data: Dict[str, Any]
    interaction_callbacks: Dict[str, callable]
    layout_config: Dict[str, Any]
    export_options: List[str]


@dataclass
class Figure:
    """Publication-quality figure data structure."""
    figure_object: Any
    caption: str
    metadata: Dict[str, Any]
    export_formats: List[str]
    size_inches: Tuple[float, float]


@dataclass
class Dashboard:
    """Real-time analysis dashboard data structure."""
    components: List[str]
    layout: Dict[str, Any]
    data_sources: Dict[str, str]
    update_frequency: float
    user_permissions: Dict[str, List[str]]


@dataclass
class MathematicalDefinition:
    """Mathematical definition for theoretical concepts."""
    concept_name: str
    formal_definition: str
    mathematical_notation: str
    assumptions: List[str]
    proofs: List[str]
    references: List[str]


@dataclass
class AlignmentMetrics:
    """Metrics for alignment between neural and human perception."""
    correlation_coefficient: float
    mutual_information: float
    rank_correlation: float
    classification_agreement: float
    boundary_agreement: float


@dataclass
class ValidationResults:
    """Results from empirical validation across datasets and models."""
    dataset_results: Dict[str, DatasetResults]
    model_results: Dict[str, ModelResults]
    correlation_analysis: CorrelationAnalysis
    statistical_significance: SignificanceTest
    effect_sizes: EffectSizeAnalysis
    overall_metrics: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
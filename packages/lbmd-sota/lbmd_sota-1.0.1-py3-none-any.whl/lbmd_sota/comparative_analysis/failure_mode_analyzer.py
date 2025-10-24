"""
Failure mode analyzer for identifying segmentation failure patterns.
"""

from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import torch
import cv2
from scipy import ndimage
from scipy.spatial.distance import cdist
from sklearn.cluster import DBSCAN
from sklearn.metrics import jaccard_score
from dataclasses import dataclass
import matplotlib.pyplot as plt

from ..core.interfaces import BaseAnalyzer
from ..core.data_models import WeaknessReport, LBMDResults


@dataclass
class FailureCase:
    """Data structure for individual failure cases."""
    failure_type: str
    severity_score: float
    affected_regions: np.ndarray
    boundary_weakness: float
    manifold_discontinuity: float
    predicted_mask: np.ndarray
    ground_truth_mask: np.ndarray
    lbmd_evidence: Dict[str, Any]
    spatial_location: Tuple[int, int, int, int]  # bbox coordinates


@dataclass
class FailurePattern:
    """Data structure for failure patterns."""
    pattern_name: str
    frequency: float
    severity_distribution: np.ndarray
    spatial_distribution: np.ndarray
    boundary_characteristics: Dict[str, float]
    affected_classes: List[str]
    diagnostic_features: Dict[str, Any]


class FailureModeAnalyzer(BaseAnalyzer):
    """Identifies and categorizes segmentation failures using LBMD insights."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.failure_threshold = config.get('failure_threshold', 0.5)
        self.boundary_weakness_threshold = config.get('boundary_weakness_threshold', 0.3)
        self.min_region_size = config.get('min_region_size', 100)
        
    def initialize(self) -> None:
        """Initialize the failure mode analyzer."""
        self._initialized = True
        
    def detect_object_merging(self, predicted_mask: np.ndarray, ground_truth_mask: np.ndarray,
                            lbmd_results: LBMDResults) -> List[FailureCase]:
        """Detect cases where separate objects are incorrectly merged."""
        failures = []
        
        # Find connected components in predictions and ground truth
        pred_labels, pred_num = ndimage.label(predicted_mask > 0.5)
        gt_labels, gt_num = ndimage.label(ground_truth_mask > 0.5)
        
        # Check if multiple GT objects map to single prediction
        for pred_id in range(1, pred_num + 1):
            pred_region = pred_labels == pred_id
            
            # Find overlapping GT objects
            overlapping_gt = []
            for gt_id in range(1, gt_num + 1):
                gt_region = gt_labels == gt_id
                overlap = np.sum(pred_region & gt_region)
                if overlap > self.min_region_size:
                    overlapping_gt.append(gt_id)
                    
            # If one prediction overlaps with multiple GT objects, it's a merge
            if len(overlapping_gt) > 1:
                # Calculate severity based on boundary weakness
                boundary_mask = lbmd_results.boundary_mask
                region_boundaries = pred_region & boundary_mask
                boundary_strength = np.mean(lbmd_results.boundary_scores[region_boundaries]) if np.any(region_boundaries) else 0.0
                
                # Calculate manifold discontinuity
                manifold_coords = lbmd_results.manifold_coords
                if manifold_coords is not None and len(manifold_coords) > 0:
                    # Ensure manifold coords match the region size
                    region_flat = pred_region.flatten()
                    if len(manifold_coords) == len(region_flat):
                        region_coords = manifold_coords[region_flat]
                        if len(region_coords) > 1:
                            distances = cdist(region_coords, region_coords)
                            manifold_discontinuity = np.std(distances)
                        else:
                            manifold_discontinuity = 0.0
                    else:
                        # Sample manifold coords if dimensions don't match
                        n_region_pixels = np.sum(pred_region)
                        if n_region_pixels > 0 and len(manifold_coords) > n_region_pixels:
                            sampled_coords = manifold_coords[:n_region_pixels]
                            distances = cdist(sampled_coords, sampled_coords)
                            manifold_discontinuity = np.std(distances)
                        else:
                            manifold_discontinuity = 0.0
                else:
                    manifold_discontinuity = 0.0
                
                # Calculate spatial location (bounding box)
                y_coords, x_coords = np.where(pred_region)
                if len(y_coords) > 0:
                    bbox = (int(np.min(x_coords)), int(np.min(y_coords)), 
                           int(np.max(x_coords)), int(np.max(y_coords)))
                else:
                    bbox = (0, 0, 0, 0)
                
                severity = 1.0 - boundary_strength + 0.5 * (manifold_discontinuity / (manifold_discontinuity + 1.0))
                
                failure = FailureCase(
                    failure_type="object_merging",
                    severity_score=severity,
                    affected_regions=pred_region,
                    boundary_weakness=1.0 - boundary_strength,
                    manifold_discontinuity=manifold_discontinuity,
                    predicted_mask=predicted_mask,
                    ground_truth_mask=ground_truth_mask,
                    lbmd_evidence={
                        'overlapping_objects': len(overlapping_gt),
                        'boundary_strength': boundary_strength,
                        'manifold_coords': region_coords if 'region_coords' in locals() else None
                    },
                    spatial_location=bbox
                )
                failures.append(failure)
                
        return failures
        
    def detect_object_separation(self, predicted_mask: np.ndarray, ground_truth_mask: np.ndarray,
                               lbmd_results: LBMDResults) -> List[FailureCase]:
        """Detect cases where single objects are incorrectly separated."""
        failures = []
        
        # Find connected components
        pred_labels, pred_num = ndimage.label(predicted_mask > 0.5)
        gt_labels, gt_num = ndimage.label(ground_truth_mask > 0.5)
        
        # Check if single GT object maps to multiple predictions
        for gt_id in range(1, gt_num + 1):
            gt_region = gt_labels == gt_id
            
            # Find overlapping predictions
            overlapping_pred = []
            for pred_id in range(1, pred_num + 1):
                pred_region = pred_labels == pred_id
                overlap = np.sum(pred_region & gt_region)
                if overlap > self.min_region_size:
                    overlapping_pred.append(pred_id)
                    
            # If one GT object overlaps with multiple predictions, it's separation
            if len(overlapping_pred) > 1:
                # Analyze boundary weakness between separated parts
                separation_boundaries = []
                for i, pred_id1 in enumerate(overlapping_pred):
                    for pred_id2 in overlapping_pred[i+1:]:
                        region1 = pred_labels == pred_id1
                        region2 = pred_labels == pred_id2
                        
                        # Find boundary between regions
                        dilated1 = ndimage.binary_dilation(region1, iterations=2)
                        dilated2 = ndimage.binary_dilation(region2, iterations=2)
                        boundary_region = dilated1 & dilated2
                        
                        if np.any(boundary_region):
                            boundary_strength = np.mean(lbmd_results.boundary_scores[boundary_region])
                            separation_boundaries.append(boundary_strength)
                
                avg_boundary_weakness = 1.0 - np.mean(separation_boundaries) if separation_boundaries else 1.0
                
                # Calculate manifold analysis
                manifold_coords = lbmd_results.manifold_coords
                if manifold_coords is not None and len(manifold_coords) > 0:
                    # Ensure manifold coords match the region size
                    region_flat = gt_region.flatten()
                    if len(manifold_coords) == len(region_flat):
                        gt_coords = manifold_coords[region_flat]
                        if len(gt_coords) > 1:
                            # Check for manifold gaps
                            clustering = DBSCAN(eps=0.5, min_samples=5)
                            clusters = clustering.fit_predict(gt_coords)
                            n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
                            manifold_discontinuity = n_clusters / len(overlapping_pred) if len(overlapping_pred) > 0 else 0.0
                        else:
                            manifold_discontinuity = 0.0
                    else:
                        # Sample manifold coords if dimensions don't match
                        n_region_pixels = np.sum(gt_region)
                        if n_region_pixels > 0 and len(manifold_coords) > n_region_pixels:
                            sampled_coords = manifold_coords[:n_region_pixels]
                            if len(sampled_coords) > 1:
                                clustering = DBSCAN(eps=0.5, min_samples=5)
                                clusters = clustering.fit_predict(sampled_coords)
                                n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
                                manifold_discontinuity = n_clusters / len(overlapping_pred) if len(overlapping_pred) > 0 else 0.0
                            else:
                                manifold_discontinuity = 0.0
                        else:
                            manifold_discontinuity = 0.0
                else:
                    manifold_discontinuity = 0.0
                
                # Calculate spatial location
                y_coords, x_coords = np.where(gt_region)
                if len(y_coords) > 0:
                    bbox = (int(np.min(x_coords)), int(np.min(y_coords)), 
                           int(np.max(x_coords)), int(np.max(y_coords)))
                else:
                    bbox = (0, 0, 0, 0)
                
                severity = avg_boundary_weakness + 0.3 * manifold_discontinuity
                
                failure = FailureCase(
                    failure_type="object_separation",
                    severity_score=severity,
                    affected_regions=gt_region,
                    boundary_weakness=avg_boundary_weakness,
                    manifold_discontinuity=manifold_discontinuity,
                    predicted_mask=predicted_mask,
                    ground_truth_mask=ground_truth_mask,
                    lbmd_evidence={
                        'separated_parts': len(overlapping_pred),
                        'boundary_strengths': separation_boundaries,
                        'manifold_clusters': n_clusters if 'n_clusters' in locals() else 0
                    },
                    spatial_location=bbox
                )
                failures.append(failure)
                
        return failures
        
    def detect_missed_boundaries(self, predicted_mask: np.ndarray, ground_truth_mask: np.ndarray,
                               lbmd_results: LBMDResults) -> List[FailureCase]:
        """Detect cases where object boundaries are missed or poorly defined."""
        failures = []
        
        # Extract boundaries from masks
        pred_boundaries = self._extract_boundaries(predicted_mask)
        gt_boundaries = self._extract_boundaries(ground_truth_mask)
        
        # Find regions where GT boundaries exist but predictions don't
        missed_boundaries = gt_boundaries & ~pred_boundaries
        
        if np.any(missed_boundaries):
            # Analyze LBMD evidence for missed boundaries
            boundary_scores = lbmd_results.boundary_scores
            missed_regions = ndimage.label(missed_boundaries)[0]
            
            for region_id in range(1, np.max(missed_regions) + 1):
                region_mask = missed_regions == region_id
                
                if np.sum(region_mask) < self.min_region_size:
                    continue
                    
                # Calculate boundary weakness in missed region
                region_boundary_scores = boundary_scores[region_mask]
                avg_boundary_strength = np.mean(region_boundary_scores) if len(region_boundary_scores) > 0 else 0.0
                boundary_weakness = 1.0 - avg_boundary_strength
                
                # Analyze manifold structure
                manifold_coords = lbmd_results.manifold_coords
                if manifold_coords is not None and len(manifold_coords) > 0:
                    # Ensure manifold coords match the region size
                    region_flat = region_mask.flatten()
                    if len(manifold_coords) == len(region_flat):
                        region_coords = manifold_coords[region_flat]
                        if len(region_coords) > 1:
                            # Check manifold smoothness
                            distances = cdist(region_coords, region_coords)
                            manifold_discontinuity = np.std(distances)
                        else:
                            manifold_discontinuity = 0.0
                    else:
                        # Sample manifold coords if dimensions don't match
                        n_region_pixels = np.sum(region_mask)
                        if n_region_pixels > 0 and len(manifold_coords) > n_region_pixels:
                            sampled_coords = manifold_coords[:n_region_pixels]
                            if len(sampled_coords) > 1:
                                distances = cdist(sampled_coords, sampled_coords)
                                manifold_discontinuity = np.std(distances)
                            else:
                                manifold_discontinuity = 0.0
                        else:
                            manifold_discontinuity = 0.0
                else:
                    manifold_discontinuity = 0.0
                
                # Calculate spatial location
                y_coords, x_coords = np.where(region_mask)
                if len(y_coords) > 0:
                    bbox = (int(np.min(x_coords)), int(np.min(y_coords)), 
                           int(np.max(x_coords)), int(np.max(y_coords)))
                else:
                    bbox = (0, 0, 0, 0)
                
                severity = boundary_weakness + 0.2 * (manifold_discontinuity / (manifold_discontinuity + 1.0))
                
                failure = FailureCase(
                    failure_type="missed_boundaries",
                    severity_score=severity,
                    affected_regions=region_mask,
                    boundary_weakness=boundary_weakness,
                    manifold_discontinuity=manifold_discontinuity,
                    predicted_mask=predicted_mask,
                    ground_truth_mask=ground_truth_mask,
                    lbmd_evidence={
                        'boundary_strength': avg_boundary_strength,
                        'region_size': np.sum(region_mask),
                        'manifold_smoothness': 1.0 / (1.0 + manifold_discontinuity)
                    },
                    spatial_location=bbox
                )
                failures.append(failure)
                
        return failures
        
    def _extract_boundaries(self, mask: np.ndarray, kernel_size: int = 3) -> np.ndarray:
        """Extract boundaries from segmentation mask."""
        if mask.dtype != np.uint8:
            mask = (mask > 0.5).astype(np.uint8)
            
        # Use morphological operations to find boundaries
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        eroded = cv2.erode(mask, kernel, iterations=1)
        boundaries = mask - eroded
        
        return boundaries > 0
        
    def analyze_failure_patterns(self, failures: List[FailureCase]) -> Dict[str, FailurePattern]:
        """Analyze patterns in failure cases."""
        patterns = {}
        
        # Group failures by type
        failure_types = {}
        for failure in failures:
            if failure.failure_type not in failure_types:
                failure_types[failure.failure_type] = []
            failure_types[failure.failure_type].append(failure)
            
        # Analyze each failure type
        for failure_type, type_failures in failure_types.items():
            if not type_failures:
                continue
                
            # Calculate frequency
            frequency = len(type_failures) / len(failures) if failures else 0.0
            
            # Analyze severity distribution
            severities = [f.severity_score for f in type_failures]
            severity_distribution = np.array(severities)
            
            # Analyze spatial distribution
            spatial_coords = []
            for f in type_failures:
                x1, y1, x2, y2 = f.spatial_location
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                spatial_coords.append([center_x, center_y])
                
            spatial_distribution = np.array(spatial_coords) if spatial_coords else np.array([])
            
            # Analyze boundary characteristics
            boundary_weaknesses = [f.boundary_weakness for f in type_failures]
            manifold_discontinuities = [f.manifold_discontinuity for f in type_failures]
            
            boundary_characteristics = {
                'avg_boundary_weakness': np.mean(boundary_weaknesses),
                'std_boundary_weakness': np.std(boundary_weaknesses),
                'avg_manifold_discontinuity': np.mean(manifold_discontinuities),
                'std_manifold_discontinuity': np.std(manifold_discontinuities)
            }
            
            # Extract diagnostic features
            diagnostic_features = {
                'severity_range': (np.min(severities), np.max(severities)),
                'most_severe_case': max(type_failures, key=lambda x: x.severity_score),
                'spatial_spread': np.std(spatial_distribution) if len(spatial_distribution) > 1 else 0.0
            }
            
            pattern = FailurePattern(
                pattern_name=failure_type,
                frequency=frequency,
                severity_distribution=severity_distribution,
                spatial_distribution=spatial_distribution,
                boundary_characteristics=boundary_characteristics,
                affected_classes=[],  # Would need class information
                diagnostic_features=diagnostic_features
            )
            
            patterns[failure_type] = pattern
            
        return patterns
        
    def generate_case_studies(self, failures: List[FailureCase], num_cases: int = 5) -> List[Dict[str, Any]]:
        """Generate detailed case studies for specific failure modes."""
        case_studies = []
        
        # Sort failures by severity
        sorted_failures = sorted(failures, key=lambda x: x.severity_score, reverse=True)
        
        # Select diverse cases
        selected_cases = []
        failure_types_seen = set()
        
        for failure in sorted_failures:
            if len(selected_cases) >= num_cases:
                break
                
            # Prioritize diverse failure types
            if failure.failure_type not in failure_types_seen or len(selected_cases) < 3:
                selected_cases.append(failure)
                failure_types_seen.add(failure.failure_type)
                
        # Generate detailed analysis for each case
        for i, failure in enumerate(selected_cases):
            case_study = {
                'case_id': i + 1,
                'failure_type': failure.failure_type,
                'severity_score': failure.severity_score,
                'description': self._generate_failure_description(failure),
                'lbmd_analysis': self._analyze_lbmd_evidence(failure),
                'diagnostic_summary': self._generate_diagnostic_summary(failure),
                'suggested_improvements': self._suggest_improvements(failure)
            }
            case_studies.append(case_study)
            
        return case_studies
        
    def _generate_failure_description(self, failure: FailureCase) -> str:
        """Generate human-readable description of failure case."""
        descriptions = {
            'object_merging': f"Multiple objects incorrectly merged into single prediction. "
                            f"Boundary weakness: {failure.boundary_weakness:.3f}, "
                            f"Manifold discontinuity: {failure.manifold_discontinuity:.3f}",
            'object_separation': f"Single object incorrectly separated into multiple predictions. "
                               f"Boundary weakness: {failure.boundary_weakness:.3f}, "
                               f"Manifold discontinuity: {failure.manifold_discontinuity:.3f}",
            'missed_boundaries': f"Object boundaries not detected or poorly defined. "
                               f"Boundary weakness: {failure.boundary_weakness:.3f}, "
                               f"Manifold discontinuity: {failure.manifold_discontinuity:.3f}"
        }
        
        return descriptions.get(failure.failure_type, "Unknown failure type")
        
    def _analyze_lbmd_evidence(self, failure: FailureCase) -> Dict[str, Any]:
        """Analyze LBMD evidence for failure case."""
        evidence = failure.lbmd_evidence.copy()
        
        # Add interpretations
        if 'boundary_strength' in evidence:
            strength = evidence['boundary_strength']
            if strength < 0.3:
                evidence['boundary_interpretation'] = "Very weak boundaries detected"
            elif strength < 0.6:
                evidence['boundary_interpretation'] = "Moderate boundary strength"
            else:
                evidence['boundary_interpretation'] = "Strong boundaries detected"
                
        if failure.manifold_discontinuity > 0.5:
            evidence['manifold_interpretation'] = "High manifold discontinuity suggests feature space fragmentation"
        else:
            evidence['manifold_interpretation'] = "Smooth manifold structure"
            
        return evidence
        
    def _generate_diagnostic_summary(self, failure: FailureCase) -> str:
        """Generate diagnostic summary for failure case."""
        summary_parts = []
        
        if failure.boundary_weakness > 0.7:
            summary_parts.append("Critical boundary detection weakness")
        elif failure.boundary_weakness > 0.4:
            summary_parts.append("Moderate boundary detection issues")
            
        if failure.manifold_discontinuity > 0.5:
            summary_parts.append("Fragmented feature representation")
            
        if failure.severity_score > 0.8:
            summary_parts.append("High-severity failure requiring immediate attention")
            
        return "; ".join(summary_parts) if summary_parts else "Minor segmentation discrepancy"
        
    def _suggest_improvements(self, failure: FailureCase) -> List[str]:
        """Suggest improvements based on failure analysis."""
        suggestions = []
        
        if failure.boundary_weakness > 0.6:
            suggestions.append("Enhance boundary detection mechanisms in model architecture")
            suggestions.append("Add boundary-focused loss terms during training")
            
        if failure.manifold_discontinuity > 0.5:
            suggestions.append("Improve feature space continuity through regularization")
            suggestions.append("Consider multi-scale feature fusion")
            
        if failure.failure_type == "object_merging":
            suggestions.append("Increase sensitivity to object boundaries")
            suggestions.append("Add contrastive learning for object separation")
            
        elif failure.failure_type == "object_separation":
            suggestions.append("Improve feature coherence within objects")
            suggestions.append("Add spatial consistency constraints")
            
        elif failure.failure_type == "missed_boundaries":
            suggestions.append("Enhance edge detection capabilities")
            suggestions.append("Increase boundary supervision during training")
            
        return suggestions
        
    def analyze(self, predicted_masks: np.ndarray, ground_truth_masks: np.ndarray,
               lbmd_results: List[LBMDResults]) -> Dict[str, Any]:
        """Analyze failure modes in segmentation predictions."""
        if not self._initialized:
            self.initialize()
            
        all_failures = []
        
        # Process each sample
        for i, (pred_mask, gt_mask, lbmd_result) in enumerate(zip(predicted_masks, ground_truth_masks, lbmd_results)):
            # Detect different types of failures
            merging_failures = self.detect_object_merging(pred_mask, gt_mask, lbmd_result)
            separation_failures = self.detect_object_separation(pred_mask, gt_mask, lbmd_result)
            boundary_failures = self.detect_missed_boundaries(pred_mask, gt_mask, lbmd_result)
            
            all_failures.extend(merging_failures + separation_failures + boundary_failures)
            
        # Analyze patterns
        failure_patterns = self.analyze_failure_patterns(all_failures)
        
        # Generate case studies
        case_studies = self.generate_case_studies(all_failures)
        
        # Create summary statistics
        summary_stats = {
            'total_failures': len(all_failures),
            'failure_types': {ftype: len([f for f in all_failures if f.failure_type == ftype]) 
                            for ftype in set(f.failure_type for f in all_failures)},
            'avg_severity': np.mean([f.severity_score for f in all_failures]) if all_failures else 0.0,
            'severity_distribution': np.histogram([f.severity_score for f in all_failures], bins=10)[0] if all_failures else np.array([])
        }
        
        return {
            'failures': all_failures,
            'patterns': failure_patterns,
            'case_studies': case_studies,
            'summary_statistics': summary_stats,
            'diagnostic_tools': {
                'boundary_weakness_analysis': self._create_boundary_weakness_report(all_failures),
                'manifold_analysis': self._create_manifold_analysis_report(all_failures),
                'spatial_analysis': self._create_spatial_analysis_report(all_failures)
            }
        }
        
    def _create_boundary_weakness_report(self, failures: List[FailureCase]) -> Dict[str, Any]:
        """Create boundary weakness analysis report."""
        if not failures:
            return {}
            
        weaknesses = [f.boundary_weakness for f in failures]
        
        return {
            'mean_weakness': np.mean(weaknesses),
            'std_weakness': np.std(weaknesses),
            'weakness_distribution': np.histogram(weaknesses, bins=10),
            'critical_cases': len([w for w in weaknesses if w > 0.8]),
            'moderate_cases': len([w for w in weaknesses if 0.4 < w <= 0.8]),
            'mild_cases': len([w for w in weaknesses if w <= 0.4])
        }
        
    def _create_manifold_analysis_report(self, failures: List[FailureCase]) -> Dict[str, Any]:
        """Create manifold analysis report."""
        if not failures:
            return {}
            
        discontinuities = [f.manifold_discontinuity for f in failures]
        
        return {
            'mean_discontinuity': np.mean(discontinuities),
            'std_discontinuity': np.std(discontinuities),
            'discontinuity_distribution': np.histogram(discontinuities, bins=10),
            'fragmented_cases': len([d for d in discontinuities if d > 0.5]),
            'smooth_cases': len([d for d in discontinuities if d <= 0.2])
        }
        
    def _create_spatial_analysis_report(self, failures: List[FailureCase]) -> Dict[str, Any]:
        """Create spatial analysis report."""
        if not failures:
            return {}
            
        # Extract spatial information
        locations = [f.spatial_location for f in failures]
        centers = [((x1 + x2) / 2, (y1 + y2) / 2) for x1, y1, x2, y2 in locations]
        sizes = [(x2 - x1) * (y2 - y1) for x1, y1, x2, y2 in locations]
        
        return {
            'spatial_distribution': np.array(centers) if centers else np.array([]),
            'size_distribution': np.array(sizes) if sizes else np.array([]),
            'clustering_tendency': self._analyze_spatial_clustering(centers) if centers else 0.0
        }
        
    def _analyze_spatial_clustering(self, centers: List[Tuple[float, float]]) -> float:
        """Analyze spatial clustering of failures."""
        if len(centers) < 2:
            return 0.0
            
        # Use DBSCAN to detect clusters
        clustering = DBSCAN(eps=50, min_samples=2)
        clusters = clustering.fit_predict(centers)
        
        # Calculate clustering tendency
        n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
        clustering_tendency = n_clusters / len(centers) if len(centers) > 0 else 0.0
        
        return clustering_tendency
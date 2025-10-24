"""
Cognitive science connector for linking LBMD findings to human visual perception.
"""

from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from scipy.stats import pearsonr, spearmanr, kendalltau
from scipy.spatial.distance import cdist
from sklearn.metrics import mutual_info_score, adjusted_rand_score
from sklearn.preprocessing import StandardScaler
from ..core.interfaces import BaseAnalyzer
from ..core.data_models import AlignmentMetrics


class HumanPerceptionModel:
    """Models human visual perception principles for comparison with neural networks."""
    
    def __init__(self):
        self.gestalt_principles = {
            'proximity': self._proximity_grouping,
            'similarity': self._similarity_grouping,
            'closure': self._closure_detection,
            'continuity': self._continuity_detection,
            'common_fate': self._common_fate_grouping
        }
    
    def simulate_human_boundary_perception(self, image_features: np.ndarray, 
                                         spatial_coords: np.ndarray) -> Dict[str, Any]:
        """
        Simulate human boundary perception using Gestalt principles.
        
        Args:
            image_features: Feature representations (n_points, n_features)
            spatial_coords: Spatial coordinates (n_points, 2)
            
        Returns:
            Dictionary with simulated human perception results
        """
        results = {}
        
        # Apply Gestalt principles
        for principle_name, principle_func in self.gestalt_principles.items():
            results[principle_name] = principle_func(image_features, spatial_coords)
        
        # Combine principles for overall boundary perception
        results['combined_boundaries'] = self._combine_gestalt_principles(results)
        
        # Simulate attention and saliency
        results['attention_map'] = self._simulate_attention(image_features, spatial_coords)
        
        # Simulate perceptual grouping
        results['perceptual_groups'] = self._simulate_perceptual_grouping(
            image_features, spatial_coords, results['combined_boundaries']
        )
        
        return results
    
    def _proximity_grouping(self, features: np.ndarray, coords: np.ndarray) -> np.ndarray:
        """Simulate proximity-based grouping (Gestalt principle)."""
        # Compute spatial distances
        spatial_distances = cdist(coords, coords)
        
        # Create proximity-based boundaries where distance changes rapidly
        proximity_boundaries = np.zeros(len(coords))
        
        for i in range(len(coords)):
            # Find k nearest neighbors
            k = min(8, len(coords) - 1)
            nearest_indices = np.argsort(spatial_distances[i])[1:k+1]
            
            # Compute variance in distances to nearest neighbors
            nearest_distances = spatial_distances[i, nearest_indices]
            distance_variance = np.var(nearest_distances)
            
            # High variance indicates boundary region
            proximity_boundaries[i] = distance_variance
        
        # Normalize to [0, 1]
        proximity_boundaries = (proximity_boundaries - np.min(proximity_boundaries)) / \
                              (np.max(proximity_boundaries) - np.min(proximity_boundaries) + 1e-10)
        
        return proximity_boundaries
    
    def _similarity_grouping(self, features: np.ndarray, coords: np.ndarray) -> np.ndarray:
        """Simulate similarity-based grouping (Gestalt principle)."""
        # Compute feature similarities
        feature_distances = cdist(features, features)
        
        similarity_boundaries = np.zeros(len(features))
        
        for i in range(len(features)):
            # Find spatially nearby points
            spatial_distances = cdist([coords[i]], coords)[0]
            nearby_mask = spatial_distances < np.percentile(spatial_distances, 25)
            
            if np.sum(nearby_mask) > 1:
                # Compute feature similarity variance among nearby points
                nearby_feature_distances = feature_distances[i, nearby_mask]
                similarity_variance = np.var(nearby_feature_distances)
                similarity_boundaries[i] = similarity_variance
        
        # Normalize
        similarity_boundaries = (similarity_boundaries - np.min(similarity_boundaries)) / \
                               (np.max(similarity_boundaries) - np.min(similarity_boundaries) + 1e-10)
        
        return similarity_boundaries
    
    def _closure_detection(self, features: np.ndarray, coords: np.ndarray) -> np.ndarray:
        """Simulate closure detection (Gestalt principle)."""
        # Detect closed contours using spatial arrangement
        closure_strength = np.zeros(len(coords))
        
        for i in range(len(coords)):
            # Find nearby points
            distances = cdist([coords[i]], coords)[0]
            nearby_indices = np.where(distances < np.percentile(distances, 20))[0]
            
            if len(nearby_indices) >= 3:
                # Check if nearby points form closed shapes
                nearby_coords = coords[nearby_indices]
                
                # Compute convex hull and check closure
                try:
                    from scipy.spatial import ConvexHull
                    hull = ConvexHull(nearby_coords)
                    
                    # Closure strength based on hull area vs perimeter ratio
                    if hasattr(hull, 'volume') and hasattr(hull, 'area'):
                        closure_strength[i] = hull.volume / (hull.area + 1e-10)
                    else:
                        # 2D case: use area/perimeter ratio approximation
                        area_approx = len(hull.vertices)
                        perimeter_approx = np.sum([np.linalg.norm(nearby_coords[hull.vertices[j]] - 
                                                                 nearby_coords[hull.vertices[(j+1) % len(hull.vertices)]])
                                                  for j in range(len(hull.vertices))])
                        closure_strength[i] = area_approx / (perimeter_approx + 1e-10)
                except:
                    closure_strength[i] = 0.0
        
        # Normalize
        if np.max(closure_strength) > np.min(closure_strength):
            closure_strength = (closure_strength - np.min(closure_strength)) / \
                              (np.max(closure_strength) - np.min(closure_strength))
        
        return closure_strength
    
    def _continuity_detection(self, features: np.ndarray, coords: np.ndarray) -> np.ndarray:
        """Simulate good continuation detection (Gestalt principle)."""
        continuity_strength = np.zeros(len(coords))
        
        for i in range(len(coords)):
            # Find nearest neighbors
            distances = cdist([coords[i]], coords)[0]
            k = min(6, len(coords) - 1)
            nearest_indices = np.argsort(distances)[1:k+1]
            
            if len(nearest_indices) >= 2:
                # Compute angles between consecutive neighbors
                center = coords[i]
                neighbor_coords = coords[nearest_indices]
                
                # Compute vectors from center to neighbors
                vectors = neighbor_coords - center
                
                # Compute angles between consecutive vectors
                angles = []
                for j in range(len(vectors)):
                    for k in range(j+1, len(vectors)):
                        v1, v2 = vectors[j], vectors[k]
                        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-10)
                        angle = np.arccos(np.clip(cos_angle, -1, 1))
                        angles.append(angle)
                
                # Continuity is high when angles are close to 0 or π (straight lines)
                if angles:
                    angle_deviations = [min(abs(angle), abs(angle - np.pi)) for angle in angles]
                    continuity_strength[i] = 1.0 - np.mean(angle_deviations) / (np.pi / 2)
        
        return np.clip(continuity_strength, 0, 1)
    
    def _common_fate_grouping(self, features: np.ndarray, coords: np.ndarray) -> np.ndarray:
        """Simulate common fate grouping (Gestalt principle)."""
        # For static images, simulate using feature similarity gradients
        common_fate = np.zeros(len(features))
        
        for i in range(len(features)):
            # Find nearby points
            spatial_distances = cdist([coords[i]], coords)[0]
            nearby_mask = spatial_distances < np.percentile(spatial_distances, 30)
            nearby_indices = np.where(nearby_mask)[0]
            
            if len(nearby_indices) > 2:
                # Compute feature gradients
                center_features = features[i]
                nearby_features = features[nearby_indices]
                
                # Compute feature differences
                feature_diffs = nearby_features - center_features
                
                # Common fate when feature changes are consistent
                if len(feature_diffs) > 1:
                    # Compute consistency of feature changes
                    diff_correlations = []
                    for j in range(len(feature_diffs)):
                        for k in range(j+1, len(feature_diffs)):
                            corr = np.corrcoef(feature_diffs[j], feature_diffs[k])[0, 1]
                            if not np.isnan(corr):
                                diff_correlations.append(abs(corr))
                    
                    if diff_correlations:
                        common_fate[i] = np.mean(diff_correlations)
        
        return common_fate
    
    def _combine_gestalt_principles(self, principle_results: Dict[str, np.ndarray]) -> np.ndarray:
        """Combine Gestalt principles for overall boundary perception."""
        # Weight different principles
        weights = {
            'proximity': 0.25,
            'similarity': 0.30,
            'closure': 0.20,
            'continuity': 0.15,
            'common_fate': 0.10
        }
        
        combined = np.zeros_like(principle_results['proximity'])
        
        for principle, weight in weights.items():
            if principle in principle_results:
                combined += weight * principle_results[principle]
        
        return combined
    
    def _simulate_attention(self, features: np.ndarray, coords: np.ndarray) -> np.ndarray:
        """Simulate human attention mechanisms."""
        attention_map = np.zeros(len(features))
        
        # Bottom-up attention (saliency)
        for i in range(len(features)):
            # Compute feature uniqueness
            feature_distances = cdist([features[i]], features)[0]
            uniqueness = np.mean(feature_distances)
            
            # Compute spatial centrality
            spatial_distances = cdist([coords[i]], coords)[0]
            centrality = 1.0 / (np.mean(spatial_distances) + 1e-10)
            
            # Combine for attention
            attention_map[i] = 0.7 * uniqueness + 0.3 * centrality
        
        # Normalize
        attention_map = (attention_map - np.min(attention_map)) / \
                       (np.max(attention_map) - np.min(attention_map) + 1e-10)
        
        return attention_map
    
    def _simulate_perceptual_grouping(self, features: np.ndarray, coords: np.ndarray, 
                                    boundaries: np.ndarray) -> np.ndarray:
        """Simulate perceptual grouping based on boundaries."""
        from sklearn.cluster import DBSCAN
        
        # Use boundaries to guide clustering
        # Points with low boundary strength should be grouped together
        boundary_weights = 1.0 - boundaries  # Invert: low boundary = high grouping
        
        # Weight features by boundary strength for clustering
        weighted_features = features * boundary_weights.reshape(-1, 1)
        
        # Perform clustering
        clustering = DBSCAN(eps=0.5, min_samples=3)
        groups = clustering.fit_predict(weighted_features)
        
        return groups


class PerceptualGroupingAnalyzer:
    """Analyzes perceptual grouping patterns in neural networks vs humans."""
    
    def __init__(self):
        self.human_model = HumanPerceptionModel()
    
    def compare_grouping_patterns(self, neural_boundaries: np.ndarray, 
                                neural_features: np.ndarray,
                                spatial_coords: np.ndarray,
                                human_annotations: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Compare neural network grouping patterns with human perception.
        
        Args:
            neural_boundaries: Neural network boundary predictions
            neural_features: Neural network features
            spatial_coords: Spatial coordinates of features
            human_annotations: Optional human boundary annotations
            
        Returns:
            Dictionary with comparison results
        """
        results = {}
        
        # Simulate human perception if no annotations provided
        if human_annotations is None:
            human_perception = self.human_model.simulate_human_boundary_perception(
                neural_features, spatial_coords
            )
            human_boundaries = human_perception['combined_boundaries']
        else:
            human_boundaries = human_annotations
        
        # Compute alignment metrics
        results['boundary_correlation'] = self._compute_boundary_correlation(
            neural_boundaries, human_boundaries
        )
        
        # Analyze grouping consistency
        results['grouping_consistency'] = self._analyze_grouping_consistency(
            neural_boundaries, human_boundaries, spatial_coords
        )
        
        # Compute perceptual plausibility
        results['perceptual_plausibility'] = self._compute_perceptual_plausibility(
            neural_boundaries, neural_features, spatial_coords
        )
        
        # Analyze attention alignment
        if human_annotations is None:
            attention_map = human_perception['attention_map']
        else:
            attention_map = self._estimate_attention_from_annotations(human_annotations, spatial_coords)
        
        results['attention_alignment'] = self._analyze_attention_alignment(
            neural_boundaries, attention_map
        )
        
        return results
    
    def _compute_boundary_correlation(self, neural_boundaries: np.ndarray, 
                                    human_boundaries: np.ndarray) -> Dict[str, float]:
        """Compute correlation between neural and human boundaries."""
        # Ensure same length
        min_len = min(len(neural_boundaries), len(human_boundaries))
        neural_b = neural_boundaries[:min_len]
        human_b = human_boundaries[:min_len]
        
        # Compute various correlation measures
        pearson_corr, pearson_p = pearsonr(neural_b, human_b)
        spearman_corr, spearman_p = spearmanr(neural_b, human_b)
        kendall_corr, kendall_p = kendalltau(neural_b, human_b)
        
        return {
            'pearson_correlation': pearson_corr,
            'pearson_p_value': pearson_p,
            'spearman_correlation': spearman_corr,
            'spearman_p_value': spearman_p,
            'kendall_correlation': kendall_corr,
            'kendall_p_value': kendall_p
        }
    
    def _analyze_grouping_consistency(self, neural_boundaries: np.ndarray,
                                    human_boundaries: np.ndarray,
                                    spatial_coords: np.ndarray) -> Dict[str, float]:
        """Analyze consistency of grouping patterns."""
        # Convert boundaries to binary masks
        neural_mask = neural_boundaries > np.percentile(neural_boundaries, 75)
        human_mask = human_boundaries > np.percentile(human_boundaries, 75)
        
        # Compute spatial consistency
        spatial_consistency = self._compute_spatial_consistency(
            neural_mask, human_mask, spatial_coords
        )
        
        # Compute clustering agreement
        clustering_agreement = self._compute_clustering_agreement(
            neural_boundaries, human_boundaries
        )
        
        return {
            'spatial_consistency': spatial_consistency,
            'clustering_agreement': clustering_agreement,
            'boundary_overlap': np.mean(neural_mask == human_mask)
        }
    
    def _compute_perceptual_plausibility(self, neural_boundaries: np.ndarray,
                                       neural_features: np.ndarray,
                                       spatial_coords: np.ndarray) -> Dict[str, float]:
        """Compute perceptual plausibility of neural boundaries."""
        # Simulate human perception
        human_perception = self.human_model.simulate_human_boundary_perception(
            neural_features, spatial_coords
        )
        
        plausibility_scores = {}
        
        # Compare with each Gestalt principle
        for principle, human_result in human_perception.items():
            if isinstance(human_result, np.ndarray) and len(human_result) == len(neural_boundaries):
                corr, _ = pearsonr(neural_boundaries, human_result)
                plausibility_scores[f'{principle}_alignment'] = corr
        
        # Overall plausibility
        plausibility_scores['overall_plausibility'] = np.mean([
            score for score in plausibility_scores.values() if not np.isnan(score)
        ])
        
        return plausibility_scores
    
    def _analyze_attention_alignment(self, neural_boundaries: np.ndarray,
                                   attention_map: np.ndarray) -> Dict[str, float]:
        """Analyze alignment between neural boundaries and human attention."""
        # Ensure same length
        min_len = min(len(neural_boundaries), len(attention_map))
        neural_b = neural_boundaries[:min_len]
        attention = attention_map[:min_len]
        
        # Compute correlation
        corr, p_value = pearsonr(neural_b, attention)
        
        # Compute mutual information
        # Discretize for mutual information calculation
        neural_discrete = np.digitize(neural_b, np.percentile(neural_b, [25, 50, 75]))
        attention_discrete = np.digitize(attention, np.percentile(attention, [25, 50, 75]))
        
        mi_score = mutual_info_score(neural_discrete, attention_discrete)
        
        return {
            'attention_correlation': corr,
            'attention_p_value': p_value,
            'mutual_information': mi_score
        }
    
    def _compute_spatial_consistency(self, neural_mask: np.ndarray, 
                                   human_mask: np.ndarray,
                                   spatial_coords: np.ndarray) -> float:
        """Compute spatial consistency of boundary predictions."""
        # Find connected components in both masks
        from scipy.spatial.distance import cdist
        
        # For each boundary point, check if nearby predictions are consistent
        consistency_scores = []
        
        for i in range(len(neural_mask)):
            if neural_mask[i] or human_mask[i]:  # Only check boundary regions
                # Find nearby points
                distances = cdist([spatial_coords[i]], spatial_coords)[0]
                nearby_mask = distances < np.percentile(distances, 10)
                
                # Check consistency in neighborhood
                nearby_neural = neural_mask[nearby_mask]
                nearby_human = human_mask[nearby_mask]
                
                if len(nearby_neural) > 0:
                    consistency = np.mean(nearby_neural == nearby_human)
                    consistency_scores.append(consistency)
        
        return np.mean(consistency_scores) if consistency_scores else 0.0
    
    def _compute_clustering_agreement(self, neural_boundaries: np.ndarray,
                                    human_boundaries: np.ndarray) -> float:
        """Compute agreement in clustering patterns."""
        # Convert to cluster labels based on boundary strength
        neural_clusters = np.digitize(neural_boundaries, 
                                    np.percentile(neural_boundaries, [33, 66]))
        human_clusters = np.digitize(human_boundaries,
                                   np.percentile(human_boundaries, [33, 66]))
        
        # Compute adjusted rand index
        return adjusted_rand_score(neural_clusters, human_clusters)
    
    def _estimate_attention_from_annotations(self, annotations: np.ndarray,
                                           spatial_coords: np.ndarray) -> np.ndarray:
        """Estimate attention map from human annotations."""
        # Simple heuristic: attention is higher near annotated boundaries
        attention_map = np.zeros(len(annotations))
        
        boundary_points = np.where(annotations > np.percentile(annotations, 75))[0]
        
        for i in range(len(annotations)):
            if len(boundary_points) > 0:
                # Distance to nearest boundary
                distances = [np.linalg.norm(spatial_coords[i] - spatial_coords[bp]) 
                           for bp in boundary_points]
                min_distance = min(distances)
                
                # Attention inversely related to distance
                attention_map[i] = 1.0 / (1.0 + min_distance)
        
        # Normalize
        if np.max(attention_map) > np.min(attention_map):
            attention_map = (attention_map - np.min(attention_map)) / \
                           (np.max(attention_map) - np.min(attention_map))
        
        return attention_map


class CognitivePlausibilityEvaluator:
    """Evaluates cognitive plausibility of LBMD insights."""
    
    def __init__(self):
        self.grouping_analyzer = PerceptualGroupingAnalyzer()
    
    def evaluate_cognitive_plausibility(self, lbmd_results: Dict[str, Any],
                                      image_data: np.ndarray,
                                      spatial_coords: np.ndarray) -> Dict[str, Any]:
        """
        Evaluate cognitive plausibility of LBMD insights.
        
        Args:
            lbmd_results: Results from LBMD analysis
            image_data: Original image data or features
            spatial_coords: Spatial coordinates
            
        Returns:
            Dictionary with plausibility evaluation results
        """
        evaluation = {}
        
        # Extract boundary information from LBMD results
        if 'boundary_scores' in lbmd_results:
            neural_boundaries = lbmd_results['boundary_scores']
        else:
            neural_boundaries = np.random.random(len(spatial_coords))  # Fallback
        
        # Evaluate perceptual grouping alignment
        evaluation['perceptual_grouping'] = self.grouping_analyzer.compare_grouping_patterns(
            neural_boundaries, image_data, spatial_coords
        )
        
        # Evaluate biological plausibility
        evaluation['biological_plausibility'] = self._evaluate_biological_plausibility(
            lbmd_results, neural_boundaries
        )
        
        # Evaluate developmental plausibility
        evaluation['developmental_plausibility'] = self._evaluate_developmental_plausibility(
            lbmd_results
        )
        
        # Overall cognitive plausibility score
        evaluation['overall_plausibility'] = self._compute_overall_plausibility(evaluation)
        
        return evaluation
    
    def _evaluate_biological_plausibility(self, lbmd_results: Dict[str, Any],
                                        neural_boundaries: np.ndarray) -> Dict[str, float]:
        """Evaluate biological plausibility based on neuroscience principles."""
        plausibility = {}
        
        # Hierarchical processing (boundaries should be more refined in deeper layers)
        if 'layer_name' in lbmd_results:
            layer_depth = self._estimate_layer_depth(lbmd_results['layer_name'])
            boundary_complexity = np.std(neural_boundaries)
            
            # Deeper layers should have more complex boundaries
            expected_complexity = layer_depth * 0.1  # Simple heuristic
            plausibility['hierarchical_processing'] = 1.0 - abs(boundary_complexity - expected_complexity)
        else:
            plausibility['hierarchical_processing'] = 0.5  # Neutral
        
        # Lateral inhibition (boundaries should be sparse and well-separated)
        boundary_sparsity = np.mean(neural_boundaries < np.percentile(neural_boundaries, 80))
        plausibility['lateral_inhibition'] = boundary_sparsity
        
        # Center-surround organization
        center_surround_score = self._evaluate_center_surround(neural_boundaries)
        plausibility['center_surround'] = center_surround_score
        
        return plausibility
    
    def _evaluate_developmental_plausibility(self, lbmd_results: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate plausibility from developmental perspective."""
        plausibility = {}
        
        # Simple-to-complex progression
        if 'topological_properties' in lbmd_results:
            topo_props = lbmd_results['topological_properties']
            
            # Simple boundaries should emerge before complex ones
            if hasattr(topo_props, 'betti_numbers'):
                complexity = sum(topo_props.betti_numbers.values()) if isinstance(topo_props.betti_numbers, dict) else 0
                plausibility['complexity_progression'] = 1.0 / (1.0 + complexity)  # Simpler is more plausible early
            else:
                plausibility['complexity_progression'] = 0.5
        else:
            plausibility['complexity_progression'] = 0.5
        
        # Stability over development
        plausibility['developmental_stability'] = 0.7  # Placeholder - would need longitudinal data
        
        return plausibility
    
    def _compute_overall_plausibility(self, evaluation: Dict[str, Any]) -> float:
        """Compute overall cognitive plausibility score."""
        scores = []
        
        # Perceptual grouping scores
        if 'perceptual_grouping' in evaluation:
            pg_scores = evaluation['perceptual_grouping']
            if 'perceptual_plausibility' in pg_scores:
                pp_scores = pg_scores['perceptual_plausibility']
                if 'overall_plausibility' in pp_scores:
                    scores.append(pp_scores['overall_plausibility'])
        
        # Biological plausibility scores
        if 'biological_plausibility' in evaluation:
            bio_scores = list(evaluation['biological_plausibility'].values())
            scores.extend([s for s in bio_scores if not np.isnan(s)])
        
        # Developmental plausibility scores
        if 'developmental_plausibility' in evaluation:
            dev_scores = list(evaluation['developmental_plausibility'].values())
            scores.extend([s for s in dev_scores if not np.isnan(s)])
        
        return np.mean(scores) if scores else 0.0
    
    def _estimate_layer_depth(self, layer_name: str) -> float:
        """Estimate layer depth from layer name."""
        # Simple heuristic based on common layer naming conventions
        if 'layer1' in layer_name or 'conv1' in layer_name:
            return 1.0
        elif 'layer2' in layer_name or 'conv2' in layer_name:
            return 2.0
        elif 'layer3' in layer_name or 'conv3' in layer_name:
            return 3.0
        elif 'layer4' in layer_name or 'conv4' in layer_name:
            return 4.0
        elif 'fc' in layer_name or 'classifier' in layer_name:
            return 5.0
        else:
            return 3.0  # Default middle layer
    
    def _evaluate_center_surround(self, boundaries: np.ndarray) -> float:
        """Evaluate center-surround organization in boundaries."""
        # Simple evaluation: boundaries should have local maxima surrounded by lower values
        center_surround_score = 0.0
        
        for i in range(1, len(boundaries) - 1):
            # Check if current point is local maximum
            if boundaries[i] > boundaries[i-1] and boundaries[i] > boundaries[i+1]:
                # Check surround suppression
                surround_avg = (boundaries[i-1] + boundaries[i+1]) / 2
                center_strength = boundaries[i]
                
                if center_strength > surround_avg:
                    center_surround_score += (center_strength - surround_avg) / center_strength
        
        # Normalize by number of potential centers
        return center_surround_score / max(1, len(boundaries) - 2)


class CognitiveScienceConnector(BaseAnalyzer):
    """Links LBMD findings to human visual perception research."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.human_model = HumanPerceptionModel()
        self.grouping_analyzer = PerceptualGroupingAnalyzer()
        self.plausibility_evaluator = CognitivePlausibilityEvaluator()
    
    def initialize(self) -> None:
        """Initialize the cognitive science connector."""
        self._initialized = True
    
    def analyze(self, data: Any) -> Dict[str, Any]:
        """Analyze cognitive alignment of LBMD insights."""
        if not self._initialized:
            self.initialize()
        
        results = {}
        
        # Extract required data
        if isinstance(data, dict):
            lbmd_results = data.get('lbmd_results', {})
            image_features = data.get('image_features', np.array([]))
            spatial_coords = data.get('spatial_coords', np.array([]))
            human_annotations = data.get('human_annotations', None)
        else:
            raise ValueError("Data must be a dictionary with required fields")
        
        # Analyze cognitive alignment
        results['cognitive_alignment'] = self.analyze_cognitive_alignment(
            lbmd_results, {'image_features': image_features, 'spatial_coords': spatial_coords}
        )
        
        # Evaluate cognitive plausibility
        results['cognitive_plausibility'] = self.plausibility_evaluator.evaluate_cognitive_plausibility(
            lbmd_results, image_features, spatial_coords
        )
        
        # Compare with human perception
        if len(image_features) > 0 and len(spatial_coords) > 0:
            boundary_scores = lbmd_results.get('boundary_scores', np.random.random(len(spatial_coords)))
            results['human_comparison'] = self.grouping_analyzer.compare_grouping_patterns(
                boundary_scores, image_features, spatial_coords, human_annotations
            )
        
        return results
    
    def analyze_cognitive_alignment(self, neural_boundaries: Any, human_data: Any) -> AlignmentMetrics:
        """Analyze alignment between neural and human boundary perception."""
        if not self._initialized:
            self.initialize()
        
        # Extract boundary data
        if isinstance(neural_boundaries, dict) and 'boundary_scores' in neural_boundaries:
            boundary_scores = neural_boundaries['boundary_scores']
        elif isinstance(neural_boundaries, np.ndarray):
            boundary_scores = neural_boundaries
        else:
            boundary_scores = np.array([])
        
        # Extract human data
        image_features = human_data.get('image_features', np.array([]))
        spatial_coords = human_data.get('spatial_coords', np.array([]))
        
        if len(boundary_scores) == 0 or len(image_features) == 0 or len(spatial_coords) == 0:
            # Return default metrics if data is insufficient
            return AlignmentMetrics(
                correlation_coefficient=0.0,
                mutual_information=0.0,
                rank_correlation=0.0,
                classification_agreement=0.0,
                boundary_agreement=0.0
            )
        
        # Simulate human perception
        human_perception = self.human_model.simulate_human_boundary_perception(
            image_features, spatial_coords
        )
        human_boundaries = human_perception['combined_boundaries']
        
        # Ensure same length
        min_len = min(len(boundary_scores), len(human_boundaries))
        neural_b = boundary_scores[:min_len]
        human_b = human_boundaries[:min_len]
        
        # Compute alignment metrics
        correlation_coeff, _ = pearsonr(neural_b, human_b)
        rank_correlation, _ = spearmanr(neural_b, human_b)
        
        # Mutual information
        neural_discrete = np.digitize(neural_b, np.percentile(neural_b, [25, 50, 75]))
        human_discrete = np.digitize(human_b, np.percentile(human_b, [25, 50, 75]))
        mutual_info = mutual_info_score(neural_discrete, human_discrete)
        
        # Classification agreement (binary boundary detection)
        neural_binary = neural_b > np.percentile(neural_b, 75)
        human_binary = human_b > np.percentile(human_b, 75)
        classification_agreement = np.mean(neural_binary == human_binary)
        
        # Boundary agreement (continuous)
        boundary_agreement = 1.0 - np.mean(np.abs(neural_b - human_b))
        
        return AlignmentMetrics(
            correlation_coefficient=correlation_coeff,
            mutual_information=mutual_info,
            rank_correlation=rank_correlation,
            classification_agreement=classification_agreement,
            boundary_agreement=boundary_agreement
        )
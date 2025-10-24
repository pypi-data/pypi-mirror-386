"""
Topological analyzer for topological data analysis methods.
"""

from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.spatial import ConvexHull
from sklearn.neighbors import NearestNeighbors
from sklearn.decomposition import PCA
import warnings
from ..core.interfaces import BaseAnalyzer
from ..core.data_models import TopologicalProperties


class PersistentHomologyAnalyzer:
    """Implements persistent homology analysis for boundary manifolds."""
    
    def __init__(self, max_dimension: int = 2, max_edge_length: float = None):
        self.max_dimension = max_dimension
        self.max_edge_length = max_edge_length
    
    def compute_persistence_diagram(self, points: np.ndarray) -> Dict[str, List[Tuple[float, float]]]:
        """
        Compute persistence diagram using Vietoris-Rips complex.
        
        Args:
            points: Point cloud data (n_points, n_dimensions)
            
        Returns:
            Dictionary with persistence pairs for each dimension
        """
        # Compute pairwise distances
        distances = pdist(points)
        distance_matrix = squareform(distances)
        
        # Set maximum edge length if not provided
        if self.max_edge_length is None:
            self.max_edge_length = np.percentile(distances, 95)
        
        # Compute persistence for different dimensions
        persistence_pairs = {}
        
        # 0-dimensional persistence (connected components)
        persistence_pairs[0] = self._compute_0d_persistence(distance_matrix)
        
        # 1-dimensional persistence (loops)
        if self.max_dimension >= 1:
            persistence_pairs[1] = self._compute_1d_persistence(distance_matrix, points)
        
        # 2-dimensional persistence (voids)
        if self.max_dimension >= 2:
            persistence_pairs[2] = self._compute_2d_persistence(distance_matrix, points)
        
        return persistence_pairs
    
    def _compute_0d_persistence(self, distance_matrix: np.ndarray) -> List[Tuple[float, float]]:
        """Compute 0-dimensional persistence (connected components)."""
        n_points = distance_matrix.shape[0]
        
        # Union-Find data structure for tracking connected components
        parent = list(range(n_points))
        birth_times = [0.0] * n_points
        death_times = []
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y, time):
            root_x, root_y = find(x), find(y)
            if root_x != root_y:
                # Merge components, record death of one
                if birth_times[root_x] > birth_times[root_y]:
                    root_x, root_y = root_y, root_x
                death_times.append((birth_times[root_y], time))
                parent[root_y] = root_x
        
        # Sort edges by distance
        edges = []
        for i in range(n_points):
            for j in range(i + 1, n_points):
                if distance_matrix[i, j] <= self.max_edge_length:
                    edges.append((distance_matrix[i, j], i, j))
        edges.sort()
        
        # Process edges in order
        for dist, i, j in edges:
            union(i, j, dist)
        
        # Add infinite persistence for remaining components
        components = set(find(i) for i in range(n_points))
        for comp in components:
            death_times.append((birth_times[comp], float('inf')))
        
        return death_times
    
    def _compute_1d_persistence(self, distance_matrix: np.ndarray, points: np.ndarray) -> List[Tuple[float, float]]:
        """Compute 1-dimensional persistence (loops) using simplified approach."""
        # Simplified 1D persistence computation
        # In practice, would use more sophisticated algorithms like Dionysus or GUDHI
        
        n_points = points.shape[0]
        if n_points < 3:
            return []
        
        # Find triangles and compute their circumradius
        persistence_pairs = []
        
        # Use Delaunay-like approach for triangle detection
        from scipy.spatial import Delaunay
        
        try:
            tri = Delaunay(points)
            for simplex in tri.simplices:
                if len(simplex) == 3:  # Triangle
                    # Compute circumradius as birth time
                    p1, p2, p3 = points[simplex]
                    circumradius = self._compute_circumradius(p1, p2, p3)
                    
                    # Estimate death time (simplified)
                    edge_lengths = [
                        np.linalg.norm(p1 - p2),
                        np.linalg.norm(p2 - p3),
                        np.linalg.norm(p3 - p1)
                    ]
                    death_time = max(edge_lengths) * 1.5
                    
                    if circumradius < death_time:
                        persistence_pairs.append((circumradius, death_time))
        except Exception:
            # Fallback: use distance-based heuristic
            distances = pdist(points)
            mean_dist = np.mean(distances)
            std_dist = np.std(distances)
            persistence_pairs.append((mean_dist - std_dist, mean_dist + std_dist))
        
        return persistence_pairs
    
    def _compute_2d_persistence(self, distance_matrix: np.ndarray, points: np.ndarray) -> List[Tuple[float, float]]:
        """Compute 2-dimensional persistence (voids) using simplified approach."""
        # Simplified 2D persistence computation
        n_points = points.shape[0]
        if n_points < 4:
            return []
        
        # Use convex hull as approximation for void detection
        try:
            if points.shape[1] >= 3:
                hull = ConvexHull(points)
                volume = hull.volume
                
                # Estimate persistence based on hull properties
                distances = pdist(points)
                max_dist = np.max(distances)
                mean_dist = np.mean(distances)
                
                birth_time = mean_dist
                death_time = max_dist * 0.8
                
                return [(birth_time, death_time)]
        except Exception:
            pass
        
        return []
    
    def _compute_circumradius(self, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> float:
        """Compute circumradius of triangle formed by three points."""
        a = np.linalg.norm(p2 - p3)
        b = np.linalg.norm(p1 - p3)
        c = np.linalg.norm(p1 - p2)
        
        # Use formula: R = (abc) / (4 * Area)
        s = (a + b + c) / 2  # semi-perimeter
        area = np.sqrt(max(0, s * (s - a) * (s - b) * (s - c)))
        
        if area < 1e-10:
            return float('inf')
        
        return (a * b * c) / (4 * area)
    
    def compute_betti_numbers(self, persistence_pairs: Dict[str, List[Tuple[float, float]]], 
                            threshold: float) -> Dict[int, int]:
        """Compute Betti numbers at given threshold."""
        betti_numbers = {}
        
        for dim, pairs in persistence_pairs.items():
            count = 0
            for birth, death in pairs:
                if birth <= threshold < death:
                    count += 1
            betti_numbers[dim] = count
        
        return betti_numbers


class TopologicalFeatureExtractor:
    """Extracts topological features from boundary manifolds."""
    
    def __init__(self):
        self.ph_analyzer = PersistentHomologyAnalyzer()
    
    def extract_topological_features(self, manifold_points: np.ndarray) -> Dict[str, Any]:
        """
        Extract comprehensive topological features from manifold.
        
        Args:
            manifold_points: Points on the manifold (n_points, n_dimensions)
            
        Returns:
            Dictionary of topological features
        """
        features = {}
        
        # Persistent homology features
        persistence_diagram = self.ph_analyzer.compute_persistence_diagram(manifold_points)
        features['persistence_diagram'] = persistence_diagram
        
        # Betti numbers at different scales
        distances = pdist(manifold_points)
        thresholds = np.percentile(distances, [25, 50, 75, 90])
        
        betti_curves = {}
        for threshold in thresholds:
            betti_numbers = self.ph_analyzer.compute_betti_numbers(persistence_diagram, threshold)
            betti_curves[threshold] = betti_numbers
        
        features['betti_curves'] = betti_curves
        
        # Persistence landscapes
        features['persistence_landscapes'] = self._compute_persistence_landscapes(persistence_diagram)
        
        # Topological entropy
        features['topological_entropy'] = self._compute_topological_entropy(persistence_diagram)
        
        # Persistent entropy
        features['persistent_entropy'] = self._compute_persistent_entropy(persistence_diagram)
        
        return features
    
    def _compute_persistence_landscapes(self, persistence_diagram: Dict[str, List[Tuple[float, float]]]) -> Dict[str, np.ndarray]:
        """Compute persistence landscapes for each dimension."""
        landscapes = {}
        
        for dim, pairs in persistence_diagram.items():
            if not pairs:
                landscapes[dim] = np.array([])
                continue
            
            # Create landscape function
            birth_death = np.array(pairs)
            if len(birth_death) == 0:
                landscapes[dim] = np.array([])
                continue
            
            # Compute landscape values at regular intervals
            min_val = np.min(birth_death[:, 0])
            max_val = np.max(birth_death[:, 1])
            if np.isinf(max_val):
                max_val = np.max(birth_death[birth_death[:, 1] != np.inf, 1])
            
            if min_val >= max_val:
                landscapes[dim] = np.array([])
                continue
            
            x_vals = np.linspace(min_val, max_val, 100)
            landscape_vals = np.zeros(len(x_vals))
            
            for birth, death in pairs:
                if np.isinf(death):
                    death = max_val
                
                for i, x in enumerate(x_vals):
                    if birth <= x <= death:
                        landscape_vals[i] = max(landscape_vals[i], 
                                              min(x - birth, death - x))
            
            landscapes[dim] = landscape_vals
        
        return landscapes
    
    def _compute_topological_entropy(self, persistence_diagram: Dict[str, List[Tuple[float, float]]]) -> float:
        """Compute topological entropy based on persistence diagram."""
        total_entropy = 0.0
        
        for dim, pairs in persistence_diagram.items():
            if not pairs:
                continue
            
            # Compute lifetimes
            lifetimes = []
            for birth, death in pairs:
                if not np.isinf(death):
                    lifetimes.append(death - birth)
            
            if not lifetimes:
                continue
            
            # Normalize lifetimes to probabilities
            lifetimes = np.array(lifetimes)
            total_lifetime = np.sum(lifetimes)
            
            if total_lifetime > 0:
                probabilities = lifetimes / total_lifetime
                # Compute entropy
                entropy = -np.sum(probabilities * np.log(probabilities + 1e-10))
                total_entropy += entropy
        
        return total_entropy
    
    def _compute_persistent_entropy(self, persistence_diagram: Dict[str, List[Tuple[float, float]]]) -> Dict[str, float]:
        """Compute persistent entropy for each dimension."""
        entropies = {}
        
        for dim, pairs in persistence_diagram.items():
            if not pairs:
                entropies[dim] = 0.0
                continue
            
            # Compute persistence values
            persistences = []
            for birth, death in pairs:
                if not np.isinf(death):
                    persistences.append(death - birth)
            
            if not persistences:
                entropies[dim] = 0.0
                continue
            
            # Normalize and compute entropy
            persistences = np.array(persistences)
            total_persistence = np.sum(persistences)
            
            if total_persistence > 0:
                probabilities = persistences / total_persistence
                entropy = -np.sum(probabilities * np.log(probabilities + 1e-10))
                entropies[dim] = entropy
            else:
                entropies[dim] = 0.0
        
        return entropies


class ManifoldCurvatureAnalyzer:
    """Analyzes curvature and geometric properties of manifolds."""
    
    def __init__(self, k_neighbors: int = 10):
        self.k_neighbors = k_neighbors
    
    def compute_curvature_metrics(self, manifold_points: np.ndarray) -> Dict[str, Any]:
        """
        Compute various curvature metrics for the manifold.
        
        Args:
            manifold_points: Points on the manifold (n_points, n_dimensions)
            
        Returns:
            Dictionary of curvature metrics
        """
        metrics = {}
        
        # Gaussian curvature approximation
        metrics['gaussian_curvature'] = self._compute_gaussian_curvature(manifold_points)
        
        # Mean curvature approximation
        metrics['mean_curvature'] = self._compute_mean_curvature(manifold_points)
        
        # Principal curvatures
        metrics['principal_curvatures'] = self._compute_principal_curvatures(manifold_points)
        
        # Curvature statistics
        metrics['curvature_statistics'] = self._compute_curvature_statistics(metrics)
        
        # Local dimensionality
        metrics['local_dimensionality'] = self._compute_local_dimensionality(manifold_points)
        
        return metrics
    
    def _compute_gaussian_curvature(self, points: np.ndarray) -> np.ndarray:
        """Compute Gaussian curvature approximation using local neighborhoods."""
        n_points = points.shape[0]
        gaussian_curvatures = np.zeros(n_points)
        
        # Fit nearest neighbors
        nbrs = NearestNeighbors(n_neighbors=min(self.k_neighbors, n_points)).fit(points)
        
        for i in range(n_points):
            # Get local neighborhood
            distances, indices = nbrs.kneighbors([points[i]])
            local_points = points[indices[0]]
            
            # Center the points
            centered_points = local_points - np.mean(local_points, axis=0)
            
            # Compute local curvature using PCA
            if len(centered_points) > 2:
                pca = PCA()
                pca.fit(centered_points)
                
                # Gaussian curvature approximation using eigenvalue ratios
                eigenvals = pca.explained_variance_
                if len(eigenvals) >= 2 and eigenvals[0] > 1e-10:
                    gaussian_curvatures[i] = eigenvals[-1] / eigenvals[0]
                else:
                    gaussian_curvatures[i] = 0.0
        
        return gaussian_curvatures
    
    def _compute_mean_curvature(self, points: np.ndarray) -> np.ndarray:
        """Compute mean curvature approximation."""
        n_points = points.shape[0]
        mean_curvatures = np.zeros(n_points)
        
        nbrs = NearestNeighbors(n_neighbors=min(self.k_neighbors, n_points)).fit(points)
        
        for i in range(n_points):
            distances, indices = nbrs.kneighbors([points[i]])
            local_points = points[indices[0]]
            
            # Compute mean curvature using discrete Laplace-Beltrami operator
            center = points[i]
            neighbors = local_points[1:]  # Exclude the center point itself
            
            if len(neighbors) > 0:
                # Discrete mean curvature
                laplacian = np.mean(neighbors, axis=0) - center
                mean_curvatures[i] = np.linalg.norm(laplacian)
        
        return mean_curvatures
    
    def _compute_principal_curvatures(self, points: np.ndarray) -> Dict[str, np.ndarray]:
        """Compute principal curvatures."""
        n_points = points.shape[0]
        k1 = np.zeros(n_points)  # Maximum curvature
        k2 = np.zeros(n_points)  # Minimum curvature
        
        nbrs = NearestNeighbors(n_neighbors=min(self.k_neighbors, n_points)).fit(points)
        
        for i in range(n_points):
            distances, indices = nbrs.kneighbors([points[i]])
            local_points = points[indices[0]]
            
            # Center the points
            centered_points = local_points - np.mean(local_points, axis=0)
            
            if len(centered_points) > 2:
                # Compute local surface using PCA
                pca = PCA()
                pca.fit(centered_points)
                
                # Principal curvatures from eigenvalues
                eigenvals = pca.explained_variance_
                if len(eigenvals) >= 2:
                    k1[i] = eigenvals[0]
                    k2[i] = eigenvals[-1]
        
        return {'k1': k1, 'k2': k2}
    
    def _compute_curvature_statistics(self, curvature_metrics: Dict[str, Any]) -> Dict[str, float]:
        """Compute statistical summaries of curvature metrics."""
        stats = {}
        
        # Gaussian curvature statistics
        gaussian_curv = curvature_metrics['gaussian_curvature']
        stats['gaussian_curvature_mean'] = np.mean(gaussian_curv)
        stats['gaussian_curvature_std'] = np.std(gaussian_curv)
        stats['gaussian_curvature_max'] = np.max(gaussian_curv)
        stats['gaussian_curvature_min'] = np.min(gaussian_curv)
        
        # Mean curvature statistics
        mean_curv = curvature_metrics['mean_curvature']
        stats['mean_curvature_mean'] = np.mean(mean_curv)
        stats['mean_curvature_std'] = np.std(mean_curv)
        stats['mean_curvature_max'] = np.max(mean_curv)
        stats['mean_curvature_min'] = np.min(mean_curv)
        
        # Principal curvature statistics
        principal_curv = curvature_metrics['principal_curvatures']
        stats['k1_mean'] = np.mean(principal_curv['k1'])
        stats['k2_mean'] = np.mean(principal_curv['k2'])
        
        return stats
    
    def _compute_local_dimensionality(self, points: np.ndarray) -> np.ndarray:
        """Compute local intrinsic dimensionality."""
        n_points = points.shape[0]
        local_dims = np.zeros(n_points)
        
        nbrs = NearestNeighbors(n_neighbors=min(self.k_neighbors, n_points)).fit(points)
        
        for i in range(n_points):
            distances, indices = nbrs.kneighbors([points[i]])
            local_points = points[indices[0]]
            
            # Estimate local dimensionality using PCA
            centered_points = local_points - np.mean(local_points, axis=0)
            
            if len(centered_points) > 1:
                pca = PCA()
                pca.fit(centered_points)
                
                # Count significant dimensions (explained variance > threshold)
                explained_var_ratio = pca.explained_variance_ratio_
                threshold = 0.01  # 1% variance threshold
                local_dims[i] = np.sum(explained_var_ratio > threshold)
        
        return local_dims


class TopologicalAnalyzer(BaseAnalyzer):
    """Implements topological data analysis methods for boundary manifolds."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.ph_analyzer = PersistentHomologyAnalyzer(
            max_dimension=config.get('max_dimension', 2),
            max_edge_length=config.get('max_edge_length', None)
        )
        self.feature_extractor = TopologicalFeatureExtractor()
        self.curvature_analyzer = ManifoldCurvatureAnalyzer(
            k_neighbors=config.get('k_neighbors', 10)
        )
    
    def initialize(self) -> None:
        """Initialize the topological analyzer."""
        self._initialized = True
    
    def analyze(self, data: Any) -> Dict[str, Any]:
        """Analyze topological properties of boundary manifolds."""
        if not self._initialized:
            self.initialize()
        
        # Extract manifold points from data
        if isinstance(data, dict) and 'manifold_coords' in data:
            manifold_points = data['manifold_coords']
        elif isinstance(data, np.ndarray):
            manifold_points = data
        else:
            raise ValueError("Data must contain 'manifold_coords' or be a numpy array")
        
        results = {}
        
        # Persistent homology analysis
        results['persistent_homology'] = self.ph_analyzer.compute_persistence_diagram(manifold_points)
        
        # Topological feature extraction
        results['topological_features'] = self.feature_extractor.extract_topological_features(manifold_points)
        
        # Curvature analysis
        results['curvature_metrics'] = self.curvature_analyzer.compute_curvature_metrics(manifold_points)
        
        # Compute comprehensive topological properties
        results['topological_properties'] = self.compute_topological_properties(manifold_points)
        
        return results
    
    def compute_topological_properties(self, manifold: np.ndarray) -> TopologicalProperties:
        """Compute comprehensive topological properties of manifold."""
        # Get persistent homology
        persistence_diagram = self.ph_analyzer.compute_persistence_diagram(manifold)
        
        # Compute Betti numbers at median distance threshold
        distances = pdist(manifold)
        median_threshold = np.median(distances)
        betti_numbers = self.ph_analyzer.compute_betti_numbers(persistence_diagram, median_threshold)
        
        # Get topological features
        topo_features = self.feature_extractor.extract_topological_features(manifold)
        
        # Get curvature metrics
        curvature_metrics = self.curvature_analyzer.compute_curvature_metrics(manifold)
        
        # Create TopologicalProperties object
        return TopologicalProperties(
            betti_numbers=betti_numbers,
            persistence_diagram=persistence_diagram,
            topological_entropy=topo_features['topological_entropy'],
            persistent_entropy=topo_features['persistent_entropy'],
            curvature_statistics=curvature_metrics['curvature_statistics'],
            local_dimensionality=curvature_metrics['local_dimensionality'],
            persistence_landscapes=topo_features['persistence_landscapes']
        )
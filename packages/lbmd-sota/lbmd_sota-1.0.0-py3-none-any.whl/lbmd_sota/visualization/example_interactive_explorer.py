"""
Example usage of the Interactive Manifold Explorer.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from lbmd_sota.visualization.interactive_manifold_explorer import InteractiveManifoldExplorer
from lbmd_sota.core.data_models import ManifoldData, LBMDResults, StatisticalMetrics, TopologicalProperties


def create_sample_manifold_data() -> ManifoldData:
    """Create sample manifold data for demonstration."""
    # Generate sample 3D manifold coordinates
    n_points = 500
    
    # Create a spiral manifold
    t = np.linspace(0, 4*np.pi, n_points)
    x = np.cos(t) * (1 + 0.1 * t)
    y = np.sin(t) * (1 + 0.1 * t)
    z = 0.1 * t
    
    coordinates = np.column_stack([x, y, z])
    
    # Create cluster labels
    labels = (t / (2*np.pi)).astype(int)
    
    # Create distance matrix (simplified)
    distances = np.random.rand(n_points, n_points)
    distances = (distances + distances.T) / 2  # Make symmetric
    np.fill_diagonal(distances, 0)
    
    # Create neighborhoods (k-nearest neighbors)
    neighborhoods = {}
    k = 5
    for i in range(n_points):
        neighbors = np.argsort(distances[i])[:k+1]  # +1 to exclude self
        neighborhoods[i] = neighbors[neighbors != i].tolist()
    
    return ManifoldData(
        coordinates=coordinates,
        labels=labels,
        distances=distances,
        neighborhoods=neighborhoods,
        embedding_method="UMAP",
        parameters={"n_neighbors": k, "min_dist": 0.1}
    )


def create_sample_lbmd_results() -> LBMDResults:
    """Create sample LBMD results for demonstration."""
    n_neurons = 1000
    
    # Generate sample data
    boundary_scores = np.random.beta(2, 5, n_neurons)  # Skewed towards lower values
    boundary_mask = boundary_scores > np.percentile(boundary_scores, 75)
    
    # Create 3D manifold coordinates
    manifold_coords = np.random.randn(n_neurons, 3)
    
    # Create pixel coordinates (2D)
    pixel_coords = np.random.randint(0, 224, (n_neurons, 2))
    
    # Create boundary indicators
    is_boundary = boundary_mask
    
    # Create clusters
    from sklearn.cluster import KMeans
    kmeans = KMeans(n_clusters=5, random_state=42)
    clusters = kmeans.fit_predict(manifold_coords)
    
    # Create transition strengths between clusters
    transition_strengths = {}
    for i in range(5):
        for j in range(i+1, 5):
            strength = np.random.uniform(0.1, 0.9)
            transition_strengths[(i, j)] = strength
            transition_strengths[(j, i)] = strength
    
    # Create cluster hulls (simplified)
    from scipy.spatial import ConvexHull
    cluster_hulls = {}
    for cluster_id in range(5):
        cluster_points = manifold_coords[clusters == cluster_id]
        if len(cluster_points) >= 4:  # Minimum points for 3D hull
            try:
                hull = ConvexHull(cluster_points)
                cluster_hulls[cluster_id] = hull
            except:
                pass
    
    # Create statistical metrics
    statistical_metrics = StatisticalMetrics(
        correlation=0.78,
        p_value=0.001,
        confidence_interval=(0.72, 0.84),
        effect_size=0.65,
        sample_size=n_neurons
    )
    
    # Create topological properties
    topological_properties = TopologicalProperties(
        betti_numbers=[1, 2, 0],
        persistence_diagram=np.random.rand(10, 2),
        euler_characteristic=1,
        genus=0,
        curvature_metrics={"mean_curvature": 0.15, "gaussian_curvature": 0.08}
    )
    
    return LBMDResults(
        layer_name="backbone.layer4.2.conv3",
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


def demonstrate_interactive_manifold_explorer():
    """Demonstrate the interactive manifold explorer functionality."""
    print("Creating Interactive Manifold Explorer...")
    
    # Initialize explorer
    config = {
        'output_dir': './visualizations',
        'default_colorscale': 'Viridis',
        'figure_size': (800, 600)
    }
    
    explorer = InteractiveManifoldExplorer(config)
    explorer.initialize()
    
    print("✓ Explorer initialized")
    
    # Create sample data
    print("\nCreating sample manifold data...")
    manifold_data = create_sample_manifold_data()
    print(f"✓ Created manifold with {len(manifold_data.coordinates)} points")
    
    # Create interactive manifold visualization
    print("\nCreating interactive manifold visualization...")
    manifold_viz = explorer.create_interactive_manifold(manifold_data)
    print("✓ Interactive manifold visualization created")
    
    # Export the visualization
    print("\nExporting manifold visualization...")
    filename = explorer.export_visualization(manifold_viz, "sample_manifold", "html")
    print(f"✓ Exported to {filename}")
    
    # Create sample LBMD results
    print("\nCreating sample LBMD results...")
    lbmd_results = create_sample_lbmd_results()
    print(f"✓ Created LBMD results for layer: {lbmd_results.layer_name}")
    
    # Create LBMD visualization
    print("\nCreating LBMD visualization...")
    lbmd_viz = explorer.create_lbmd_visualization(lbmd_results)
    print("✓ LBMD visualization created")
    
    # Export LBMD visualization
    print("\nExporting LBMD visualization...")
    filename = explorer.export_visualization(lbmd_viz, "sample_lbmd_analysis", "html")
    print(f"✓ Exported to {filename}")
    
    # Create cross-layer comparison
    print("\nCreating cross-layer comparison...")
    layer_results = {
        "layer1.conv1": create_sample_lbmd_results(),
        "layer2.conv2": create_sample_lbmd_results(),
        "layer3.conv3": create_sample_lbmd_results()
    }
    
    comparison_viz = explorer.create_cross_layer_comparison(layer_results)
    print("✓ Cross-layer comparison created")
    
    # Export comparison visualization
    print("\nExporting cross-layer comparison...")
    filename = explorer.export_visualization(comparison_viz, "cross_layer_comparison", "html")
    print(f"✓ Exported to {filename}")
    
    print("\n" + "="*50)
    print("Interactive Manifold Explorer Demo Complete!")
    print("="*50)
    print("\nGenerated visualizations:")
    print("- sample_manifold.html: Basic manifold exploration")
    print("- sample_lbmd_analysis.html: Comprehensive LBMD analysis")
    print("- cross_layer_comparison.html: Multi-layer comparison")
    print("\nOpen these HTML files in a web browser to interact with the visualizations.")


def demonstrate_parameter_controls():
    """Demonstrate the parameter control interface."""
    print("\nDemonstrating parameter controls...")
    
    config = {'output_dir': './visualizations'}
    explorer = InteractiveManifoldExplorer(config)
    explorer.initialize()
    
    # Create sample data
    manifold_data = create_sample_manifold_data()
    lbmd_results = create_sample_lbmd_results()
    
    # Create visualizations with controls
    manifold_viz = explorer.create_interactive_manifold(manifold_data)
    lbmd_viz = explorer.create_lbmd_visualization(lbmd_results)
    
    print("✓ Created visualizations with interactive controls")
    
    # Demonstrate control creation
    if hasattr(explorer, '_create_parameter_controls'):
        manifold_controls = explorer._create_parameter_controls(manifold_data)
        lbmd_controls = explorer._create_lbmd_controls(lbmd_results)
        
        print(f"✓ Manifold controls: {list(manifold_controls.keys())}")
        print(f"✓ LBMD controls: {list(lbmd_controls.keys())}")
    
    # Create parameter adjustment interface
    try:
        interface = explorer.create_parameter_adjustment_interface(manifold_viz)
        print("✓ Parameter adjustment interface created")
    except Exception as e:
        print(f"Note: Parameter interface requires Jupyter environment: {e}")


if __name__ == "__main__":
    demonstrate_interactive_manifold_explorer()
    demonstrate_parameter_controls()
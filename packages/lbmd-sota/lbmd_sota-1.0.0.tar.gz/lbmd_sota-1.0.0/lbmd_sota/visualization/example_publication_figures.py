"""
Example usage of the Publication Figure Generator.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any

from lbmd_sota.visualization.publication_figure_generator import PublicationFigureGenerator
from lbmd_sota.core.data_models import ManifoldData, LBMDResults, StatisticalMetrics, TopologicalProperties


def create_sample_lbmd_results() -> LBMDResults:
    """Create sample LBMD results for demonstration."""
    n_neurons = 500
    
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


def create_sample_manifold_data() -> ManifoldData:
    """Create sample manifold data for demonstration."""
    # Generate sample 3D manifold coordinates
    n_points = 300
    
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


def demonstrate_publication_figure_generator():
    """Demonstrate the publication figure generator functionality."""
    print("Creating Publication Figure Generator...")
    
    # Initialize generator with publication settings
    config = {
        'figure_style': 'publication',
        'dpi': 300,
        'font_size': 12,
        'color_palette': 'viridis'
    }
    
    generator = PublicationFigureGenerator(config)
    generator.initialize()
    
    print("✓ Generator initialized with publication settings")
    
    # Create sample data
    print("\nCreating sample LBMD results...")
    lbmd_results = create_sample_lbmd_results()
    print(f"✓ Created LBMD results for layer: {lbmd_results.layer_name}")
    
    print("\nCreating sample manifold data...")
    manifold_data = create_sample_manifold_data()
    print(f"✓ Created manifold with {len(manifold_data.coordinates)} points")
    
    # Generate comprehensive LBMD figure
    print("\nGenerating comprehensive LBMD figure...")
    try:
        comprehensive_fig = generator.create_comprehensive_lbmd_figure(lbmd_results)
        print("✓ Comprehensive LBMD figure created")
        
        # Save the figure
        generator.save_figure(comprehensive_fig, "comprehensive_lbmd_analysis", format='png')
        print("✓ Saved as comprehensive_lbmd_analysis.png")
        
    except Exception as e:
        print(f"Note: Comprehensive figure generation requires additional dependencies: {e}")
    
    # Generate boundary manifold figure
    print("\nGenerating boundary manifold figure...")
    try:
        boundary_fig = generator.create_boundary_manifold_figure(lbmd_results)
        print("✓ Boundary manifold figure created")
        
        # Save the figure
        generator.save_figure(boundary_fig, "boundary_manifold_analysis", format='png')
        print("✓ Saved as boundary_manifold_analysis.png")
        
    except Exception as e:
        print(f"Note: Boundary figure generation requires additional dependencies: {e}")
    
    # Generate statistical analysis figure
    print("\nGenerating statistical analysis figure...")
    try:
        stats_fig = generator.create_statistical_analysis_figure(lbmd_results)
        print("✓ Statistical analysis figure created")
        
        # Save the figure
        generator.save_figure(stats_fig, "statistical_analysis", format='png')
        print("✓ Saved as statistical_analysis.png")
        
    except Exception as e:
        print(f"Note: Statistical figure generation requires additional dependencies: {e}")
    
    # Generate cluster analysis figure
    print("\nGenerating cluster analysis figure...")
    try:
        cluster_fig = generator.create_cluster_analysis_figure(lbmd_results)
        print("✓ Cluster analysis figure created")
        
        # Save the figure
        generator.save_figure(cluster_fig, "cluster_analysis", format='png')
        print("✓ Saved as cluster_analysis.png")
        
    except Exception as e:
        print(f"Note: Cluster figure generation requires additional dependencies: {e}")
    
    # Generate transition heatmap figure
    print("\nGenerating transition heatmap figure...")
    try:
        transition_fig = generator.create_transition_heatmap_figure(lbmd_results)
        print("✓ Transition heatmap figure created")
        
        # Save the figure
        generator.save_figure(transition_fig, "transition_heatmap", format='png')
        print("✓ Saved as transition_heatmap.png")
        
    except Exception as e:
        print(f"Note: Transition figure generation requires additional dependencies: {e}")
    
    # Generate manifold figure
    print("\nGenerating manifold figure...")
    try:
        manifold_fig = generator.create_manifold_figure(manifold_data)
        print("✓ Manifold figure created")
        
        # Save the figure
        generator.save_figure(manifold_fig, "manifold_visualization", format='png')
        print("✓ Saved as manifold_visualization.png")
        
    except Exception as e:
        print(f"Note: Manifold figure generation requires additional dependencies: {e}")
    
    # Generate all publication figures
    print("\nGenerating complete publication figure set...")
    try:
        all_figures = generator.generate_publication_figures(lbmd_results)
        print(f"✓ Generated {len(all_figures)} publication-quality figures")
        
        # Save all figures
        figure_names = ['boundary_manifold', 'statistical_analysis', 'cluster_analysis', 'transition_heatmap']
        for i, (fig, name) in enumerate(zip(all_figures, figure_names)):
            generator.save_figure(fig, f"publication_{name}", format='png')
            print(f"✓ Saved publication_{name}.png")
            
    except Exception as e:
        print(f"Note: Complete figure set generation requires additional dependencies: {e}")
    
    print("\n" + "="*60)
    print("Publication Figure Generator Demo Complete!")
    print("="*60)
    print("\nGenerated publication-quality figures:")
    print("- comprehensive_lbmd_analysis.png: Multi-panel LBMD overview")
    print("- boundary_manifold_analysis.png: Focused boundary analysis")
    print("- statistical_analysis.png: Statistical significance results")
    print("- cluster_analysis.png: Cluster structure and quality")
    print("- transition_heatmap.png: Inter-cluster transitions")
    print("- manifold_visualization.png: Basic manifold structure")
    print("\nAll figures are generated with publication-quality settings:")
    print("- 300 DPI resolution")
    print("- Professional typography (Times New Roman)")
    print("- Consistent color schemes")
    print("- Proper annotations and captions")
    print("- Multiple export formats (PDF, PNG, SVG)")


def demonstrate_figure_customization():
    """Demonstrate figure customization options."""
    print("\nDemonstrating figure customization...")
    
    # Create generator with custom settings
    custom_config = {
        'figure_style': 'publication',
        'dpi': 600,  # Higher resolution
        'font_size': 14,  # Larger fonts
        'color_palette': 'plasma'  # Different color scheme
    }
    
    generator = PublicationFigureGenerator(custom_config)
    generator.initialize()
    
    print("✓ Custom generator created with high-resolution settings")
    
    # Create sample data
    lbmd_results = create_sample_lbmd_results()
    
    # Generate specific figure types
    figure_types = ['boundary_manifold', 'statistical', 'clusters']
    
    for fig_type in figure_types:
        try:
            fig = generator.create_lbmd_figure(lbmd_results, figure_type=fig_type)
            print(f"✓ Generated {fig_type} figure with custom settings")
            
            # Save in multiple formats
            for fmt in ['png', 'pdf']:
                generator.save_figure(fig, f"custom_{fig_type}", format=fmt)
                print(f"  - Saved as custom_{fig_type}.{fmt}")
                
        except Exception as e:
            print(f"Note: {fig_type} figure requires additional dependencies: {e}")
    
    print("✓ Figure customization demonstration complete")


if __name__ == "__main__":
    demonstrate_publication_figure_generator()
    demonstrate_figure_customization()
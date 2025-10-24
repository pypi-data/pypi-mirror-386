"""
Example usage of the Real-time Analysis Dashboard.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import time
import threading
import numpy as np
from typing import Dict, Any

from lbmd_sota.visualization.realtime_dashboard import RealtimeDashboard
from lbmd_sota.core.data_models import LBMDResults, StatisticalMetrics, TopologicalProperties


def create_sample_lbmd_results(layer_name: str) -> LBMDResults:
    """Create sample LBMD results for demonstration."""
    n_neurons = 200
    
    # Generate sample data
    boundary_scores = np.random.beta(2, 5, n_neurons)
    boundary_mask = boundary_scores > np.percentile(boundary_scores, 75)
    
    # Create 3D manifold coordinates
    manifold_coords = np.random.randn(n_neurons, 3)
    
    # Create pixel coordinates (2D)
    pixel_coords = np.random.randint(0, 224, (n_neurons, 2))
    
    # Create boundary indicators
    is_boundary = boundary_mask
    
    # Create clusters
    from sklearn.cluster import KMeans
    kmeans = KMeans(n_clusters=3, random_state=42)
    clusters = kmeans.fit_predict(manifold_coords)
    
    # Create transition strengths between clusters
    transition_strengths = {}
    for i in range(3):
        for j in range(i+1, 3):
            strength = np.random.uniform(0.2, 0.8)
            transition_strengths[(i, j)] = strength
            transition_strengths[(j, i)] = strength
    
    # Create statistical metrics
    statistical_metrics = StatisticalMetrics(
        correlation=0.65 + 0.2 * np.random.randn(),
        p_value=0.001 + 0.01 * np.random.rand(),
        confidence_interval=(0.6, 0.8),
        effect_size=0.5 + 0.2 * np.random.randn(),
        sample_size=n_neurons
    )
    
    # Create topological properties
    topological_properties = TopologicalProperties(
        betti_numbers=[1, 1, 0],
        persistence_diagram=np.random.rand(5, 2),
        euler_characteristic=1,
        genus=0,
        curvature_metrics={"mean_curvature": 0.1, "gaussian_curvature": 0.05}
    )
    
    return LBMDResults(
        layer_name=layer_name,
        boundary_scores=boundary_scores,
        boundary_mask=boundary_mask,
        manifold_coords=manifold_coords,
        pixel_coords=pixel_coords,
        is_boundary=is_boundary,
        clusters=clusters,
        transition_strengths=transition_strengths,
        cluster_hulls={},
        statistical_metrics=statistical_metrics,
        topological_properties=topological_properties
    )


def simulate_live_experiment(dashboard: RealtimeDashboard, experiment_id: str):
    """Simulate a live experiment with streaming data."""
    print(f"Starting simulation for experiment {experiment_id}")
    
    layers = [
        "backbone.layer1.conv1",
        "backbone.layer2.conv2", 
        "backbone.layer3.conv3",
        "backbone.layer4.conv4",
        "fpn.inner_blocks.0",
        "fpn.inner_blocks.1"
    ]
    
    for i, layer in enumerate(layers):
        print(f"Processing layer {layer}...")
        
        # Update progress
        progress = (i + 1) / len(layers) * 100
        dashboard.update_experiment_progress(experiment_id, progress, "processing")
        
        # Generate LBMD results for this layer
        lbmd_results = create_sample_lbmd_results(layer)
        
        # Add to dashboard
        dashboard.add_experiment_data(experiment_id, lbmd_results)
        
        # Simulate processing time
        time.sleep(2)
    
    # Mark experiment as complete
    dashboard.update_experiment_progress(experiment_id, 100, "completed")
    print(f"Experiment {experiment_id} completed!")


def demonstrate_dashboard_basic():
    """Demonstrate basic dashboard functionality."""
    print("Creating Real-time Analysis Dashboard...")
    
    # Check if Dash is available
    try:
        import dash
        print("✓ Dash is available")
    except ImportError:
        print("✗ Dash is not available. Install with: pip install dash dash-bootstrap-components")
        print("Skipping dashboard demonstration.")
        return
    
    # Initialize dashboard
    config = {
        'port': 8050,
        'host': '127.0.0.1',
        'debug': False,
        'update_interval': 2000  # 2 seconds
    }
    
    dashboard = RealtimeDashboard(config)
    
    try:
        # Launch dashboard
        dashboard_info = dashboard.launch_analysis_dashboard(config)
        print("✓ Dashboard launched successfully")
        print(f"  - Components: {dashboard_info.components}")
        print(f"  - Update frequency: {dashboard_info.update_frequency}s")
        print(f"  - Access at: http://127.0.0.1:8050")
        
        # Simulate some experiments
        print("\nSimulating live experiments...")
        
        # Start first experiment
        exp1_id = "exp_coco_maskrcnn_001"
        exp1_thread = threading.Thread(
            target=simulate_live_experiment,
            args=(dashboard, exp1_id),
            daemon=True
        )
        exp1_thread.start()
        
        # Wait a bit, then start second experiment
        time.sleep(5)
        exp2_id = "exp_cityscapes_solo_002"
        exp2_thread = threading.Thread(
            target=simulate_live_experiment,
            args=(dashboard, exp2_id),
            daemon=True
        )
        exp2_thread.start()
        
        # Keep dashboard running for demonstration
        print("\nDashboard is running with live experiments...")
        print("Open http://127.0.0.1:8050 in your browser to view the dashboard")
        print("Press Ctrl+C to stop the dashboard")
        
        try:
            # Wait for experiments to complete
            exp1_thread.join()
            exp2_thread.join()
            
            # Keep dashboard running for a bit longer
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\nStopping dashboard...")
        
        # Export experiment data
        print("\nExporting experiment data...")
        try:
            dashboard.export_experiment_data(exp1_id, f"{exp1_id}_results.json")
            print(f"✓ Exported {exp1_id} results")
        except Exception as e:
            print(f"Note: Export failed: {e}")
        
        try:
            dashboard.export_experiment_data(exp2_id, f"{exp2_id}_results.json")
            print(f"✓ Exported {exp2_id} results")
        except Exception as e:
            print(f"Note: Export failed: {e}")
        
        # Get experiment summaries
        print("\nExperiment Summaries:")
        for exp_id in [exp1_id, exp2_id]:
            summary = dashboard.get_experiment_summary(exp_id)
            if summary:
                print(f"\n{exp_id}:")
                print(f"  - Layers analyzed: {summary.get('n_layers', 0)}")
                print(f"  - Mean correlation: {summary.get('mean_correlation', 0):.3f}")
                print(f"  - Total neurons: {summary.get('total_neurons', 0)}")
        
        # Stop dashboard
        dashboard.stop_dashboard()
        print("✓ Dashboard stopped")
        
    except Exception as e:
        print(f"✗ Dashboard error: {e}")
        print("This might be due to missing dependencies or port conflicts.")


def demonstrate_dashboard_features():
    """Demonstrate advanced dashboard features."""
    print("\nDemonstrating advanced dashboard features...")
    
    try:
        import dash
    except ImportError:
        print("Dash not available - skipping advanced features demo")
        return
    
    # Create dashboard with custom configuration
    config = {
        'port': 8051,  # Different port
        'host': '127.0.0.1',
        'debug': True,  # Enable debug mode
        'update_interval': 1000  # Faster updates (1 second)
    }
    
    dashboard = RealtimeDashboard(config)
    
    print("✓ Dashboard created with custom configuration")
    print(f"  - Port: {config['port']}")
    print(f"  - Debug mode: {config['debug']}")
    print(f"  - Update interval: {config['update_interval']}ms")
    
    # Test data management features
    print("\nTesting data management features...")
    
    # Add some test data
    test_exp_id = "test_experiment_001"
    for i in range(3):
        layer_name = f"test_layer_{i}"
        lbmd_results = create_sample_lbmd_results(layer_name)
        dashboard.add_experiment_data(test_exp_id, lbmd_results)
        print(f"✓ Added data for {layer_name}")
    
    # Get experiment summary
    summary = dashboard.get_experiment_summary(test_exp_id)
    print(f"\nExperiment Summary:")
    print(f"  - Experiment ID: {summary['experiment_id']}")
    print(f"  - Layers: {summary['n_layers']}")
    print(f"  - Mean correlation: {summary['mean_correlation']:.3f}")
    print(f"  - Total neurons: {summary['total_neurons']}")
    
    # Test export functionality
    try:
        dashboard.export_experiment_data(test_exp_id, "test_experiment_export.json")
        print("✓ Data export successful")
        
        # Check if file was created
        if os.path.exists("test_experiment_export.json"):
            print("✓ Export file created successfully")
            
            # Read and display file size
            file_size = os.path.getsize("test_experiment_export.json")
            print(f"  - File size: {file_size} bytes")
        
    except Exception as e:
        print(f"✗ Export failed: {e}")
    
    print("✓ Advanced features demonstration complete")


def demonstrate_collaborative_features():
    """Demonstrate collaborative research features."""
    print("\nDemonstrating collaborative research features...")
    
    # Simulate multiple researchers working on different aspects
    researchers = {
        'researcher_a': {'focus': 'boundary_analysis', 'experiments': []},
        'researcher_b': {'focus': 'manifold_structure', 'experiments': []},
        'researcher_c': {'focus': 'statistical_validation', 'experiments': []}
    }
    
    print("✓ Simulated multi-researcher environment")
    
    # Each researcher would have their own experiment tracking
    for researcher, info in researchers.items():
        exp_id = f"{researcher}_experiment_{int(time.time())}"
        info['experiments'].append(exp_id)
        print(f"  - {researcher}: {info['focus']} -> {exp_id}")
    
    print("✓ Collaborative workflow simulation complete")
    print("\nIn a real deployment, the dashboard would support:")
    print("  - User authentication and permissions")
    print("  - Experiment sharing and collaboration")
    print("  - Real-time notifications")
    print("  - Experiment comparison tools")
    print("  - Team workspace management")


if __name__ == "__main__":
    print("LBMD Real-time Dashboard Demonstration")
    print("=" * 50)
    
    demonstrate_dashboard_basic()
    demonstrate_dashboard_features()
    demonstrate_collaborative_features()
    
    print("\n" + "=" * 50)
    print("Dashboard Demonstration Complete!")
    print("=" * 50)
    print("\nKey Features Demonstrated:")
    print("✓ Real-time experiment monitoring")
    print("✓ Live metrics visualization")
    print("✓ Interactive boundary analysis")
    print("✓ 3D manifold exploration")
    print("✓ Experiment progress tracking")
    print("✓ Data export and sharing")
    print("✓ Multi-experiment comparison")
    print("✓ Collaborative research support")
    
    print("\nTo use the dashboard in your research:")
    print("1. Install dependencies: pip install dash dash-bootstrap-components")
    print("2. Initialize dashboard with your configuration")
    print("3. Launch dashboard and open in browser")
    print("4. Start experiments and monitor in real-time")
    print("5. Export results for publication and sharing")
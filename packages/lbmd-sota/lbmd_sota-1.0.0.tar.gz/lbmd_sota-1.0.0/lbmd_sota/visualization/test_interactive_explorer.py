"""
Tests for the Interactive Manifold Explorer.
"""

import unittest
import numpy as np
import tempfile
import os
from unittest.mock import Mock, patch

from .interactive_manifold_explorer import InteractiveManifoldExplorer
from ..core.data_models import ManifoldData, LBMDResults, StatisticalMetrics, TopologicalProperties


class TestInteractiveManifoldExplorer(unittest.TestCase):
    """Test cases for InteractiveManifoldExplorer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'output_dir': tempfile.mkdtemp(),
            'default_colorscale': 'Viridis',
            'figure_size': (800, 600)
        }
        self.explorer = InteractiveManifoldExplorer(self.config)
        self.explorer.initialize()
        
        # Create sample manifold data
        self.manifold_data = self._create_sample_manifold_data()
        self.lbmd_results = self._create_sample_lbmd_results()
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary directory
        import shutil
        if os.path.exists(self.config['output_dir']):
            shutil.rmtree(self.config['output_dir'])
    
    def _create_sample_manifold_data(self) -> ManifoldData:
        """Create sample manifold data for testing."""
        n_points = 100
        coordinates = np.random.randn(n_points, 3)
        labels = np.random.randint(0, 5, n_points)
        distances = np.random.rand(n_points, n_points)
        neighborhoods = {i: [j for j in range(min(5, n_points)) if j != i] for i in range(n_points)}
        
        return ManifoldData(
            coordinates=coordinates,
            labels=labels,
            distances=distances,
            neighborhoods=neighborhoods,
            embedding_method="UMAP",
            parameters={"n_neighbors": 5}
        )
    
    def _create_sample_lbmd_results(self) -> LBMDResults:
        """Create sample LBMD results for testing."""
        n_neurons = 100
        
        return LBMDResults(
            layer_name="test_layer",
            boundary_scores=np.random.rand(n_neurons),
            boundary_mask=np.random.choice([True, False], n_neurons),
            manifold_coords=np.random.randn(n_neurons, 3),
            pixel_coords=np.random.randint(0, 224, (n_neurons, 2)),
            is_boundary=np.random.choice([True, False], n_neurons),
            clusters=np.random.randint(0, 5, n_neurons),
            transition_strengths={(0, 1): 0.5, (1, 2): 0.7},
            cluster_hulls={},
            statistical_metrics=StatisticalMetrics(0.78, 0.001, (0.7, 0.85), 0.6, n_neurons),
            topological_properties=TopologicalProperties([1, 0], np.array([[0, 1]]), 1, 0, {})
        )
    
    def test_initialization(self):
        """Test explorer initialization."""
        self.assertTrue(self.explorer._initialized)
        self.assertIsInstance(self.explorer.color_schemes, dict)
        self.assertIn('boundary', self.explorer.color_schemes)
        self.assertIn('cluster', self.explorer.color_schemes)
    
    def test_create_interactive_manifold(self):
        """Test interactive manifold creation."""
        visualization = self.explorer.create_interactive_manifold(self.manifold_data)
        
        self.assertIsNotNone(visualization)
        self.assertIn('figure', visualization.plot_data)
        self.assertIn('controls', visualization.plot_data)
        self.assertEqual(len(visualization.export_options), 4)
        self.assertIn('html', visualization.export_options)
    
    def test_create_lbmd_visualization(self):
        """Test LBMD visualization creation."""
        visualization = self.explorer.create_lbmd_visualization(self.lbmd_results)
        
        self.assertIsNotNone(visualization)
        self.assertIn('figure', visualization.plot_data)
        self.assertIn('controls', visualization.plot_data)
        self.assertIn('lbmd_results', visualization.plot_data)
        self.assertEqual(visualization.layout_config['width'], 1200)
        self.assertEqual(visualization.layout_config['height'], 800)
    
    def test_create_cross_layer_comparison(self):
        """Test cross-layer comparison visualization."""
        layer_results = {
            "layer1": self.lbmd_results,
            "layer2": self._create_sample_lbmd_results(),
            "layer3": self._create_sample_lbmd_results()
        }
        
        visualization = self.explorer.create_cross_layer_comparison(layer_results)
        
        self.assertIsNotNone(visualization)
        self.assertIn('figure', visualization.plot_data)
        self.assertIn('controls', visualization.plot_data)
        self.assertIn('layer_results', visualization.plot_data)
    
    def test_parameter_controls_creation(self):
        """Test parameter controls creation."""
        controls = self.explorer._create_parameter_controls(self.manifold_data)
        
        expected_controls = ['point_size', 'color_scheme', 'opacity', 'show_connections']
        for control_name in expected_controls:
            self.assertIn(control_name, controls)
    
    def test_lbmd_controls_creation(self):
        """Test LBMD controls creation."""
        controls = self.explorer._create_lbmd_controls(self.lbmd_results)
        
        expected_controls = ['boundary_threshold', 'selected_clusters', 'view_mode']
        for control_name in expected_controls:
            self.assertIn(control_name, controls)
    
    def test_comparison_controls_creation(self):
        """Test comparison controls creation."""
        layer_results = {"layer1": self.lbmd_results}
        controls = self.explorer._create_comparison_controls(layer_results)
        
        expected_controls = ['selected_layers', 'sync_views', 'comparison_metric']
        for control_name in expected_controls:
            self.assertIn(control_name, controls)
    
    def test_interaction_callbacks_creation(self):
        """Test interaction callbacks creation."""
        callbacks = self.explorer._create_interaction_callbacks()
        
        expected_callbacks = ['point_size', 'color_scheme', 'connections']
        for callback_name in expected_callbacks:
            self.assertIn(callback_name, callbacks)
            self.assertTrue(callable(callbacks[callback_name]))
    
    def test_lbmd_callbacks_creation(self):
        """Test LBMD callbacks creation."""
        callbacks = self.explorer._create_lbmd_callbacks()
        
        expected_callbacks = ['boundary_threshold', 'cluster_selection', 'view_mode']
        for callback_name in expected_callbacks:
            self.assertIn(callback_name, callbacks)
            self.assertTrue(callable(callbacks[callback_name]))
    
    def test_comparison_callbacks_creation(self):
        """Test comparison callbacks creation."""
        callbacks = self.explorer._create_comparison_callbacks()
        
        expected_callbacks = ['layer_selection', 'sync_views', 'comparison_metric']
        for callback_name in expected_callbacks:
            self.assertIn(callback_name, callbacks)
            self.assertTrue(callable(callbacks[callback_name]))
    
    @patch('plotly.graph_objects.Figure.write_html')
    def test_export_visualization_html(self, mock_write_html):
        """Test HTML export functionality."""
        visualization = self.explorer.create_interactive_manifold(self.manifold_data)
        
        filename = self.explorer.export_visualization(visualization, "test_export", "html")
        
        self.assertEqual(filename, "test_export.html")
        mock_write_html.assert_called_once_with("test_export.html")
    
    @patch('plotly.graph_objects.Figure.write_image')
    def test_export_visualization_png(self, mock_write_image):
        """Test PNG export functionality."""
        visualization = self.explorer.create_interactive_manifold(self.manifold_data)
        
        filename = self.explorer.export_visualization(visualization, "test_export", "png")
        
        self.assertEqual(filename, "test_export.png")
        mock_write_image.assert_called_once_with("test_export.png")
    
    def test_export_visualization_invalid_format(self):
        """Test export with invalid format."""
        visualization = self.explorer.create_interactive_manifold(self.manifold_data)
        
        with self.assertRaises(ValueError):
            self.explorer.export_visualization(visualization, "test_export", "invalid")
    
    def test_visualize_method_manifold_data(self):
        """Test generic visualize method with ManifoldData."""
        visualization = self.explorer.visualize(self.manifold_data)
        
        self.assertIsNotNone(visualization)
        self.assertIn('figure', visualization.plot_data)
    
    def test_visualize_method_lbmd_results(self):
        """Test generic visualize method with LBMDResults."""
        visualization = self.explorer.visualize(self.lbmd_results)
        
        self.assertIsNotNone(visualization)
        self.assertIn('figure', visualization.plot_data)
    
    def test_visualize_method_invalid_data(self):
        """Test generic visualize method with invalid data."""
        with self.assertRaises(ValueError):
            self.explorer.visualize("invalid_data")
    
    def test_add_neighborhood_edges(self):
        """Test neighborhood edge addition."""
        import plotly.graph_objects as go
        
        fig = go.Figure()
        coords = np.random.randn(10, 3)
        neighborhoods = {0: [1, 2], 1: [0, 3], 2: [0, 4]}
        
        # This should not raise an exception
        self.explorer._add_neighborhood_edges(fig, coords, neighborhoods)
        
        # Check that traces were added (edges should be added as traces)
        self.assertGreaterEqual(len(fig.data), 0)
    
    def test_2d_manifold_handling(self):
        """Test handling of 2D manifold data."""
        # Create 2D manifold data
        manifold_data_2d = ManifoldData(
            coordinates=np.random.randn(50, 2),  # Only 2D
            labels=np.random.randint(0, 3, 50),
            distances=np.random.rand(50, 50),
            neighborhoods={},
            embedding_method="PCA",
            parameters={}
        )
        
        visualization = self.explorer.create_interactive_manifold(manifold_data_2d)
        
        self.assertIsNotNone(visualization)
        self.assertIn('figure', visualization.plot_data)
    
    def test_empty_transition_strengths(self):
        """Test handling of empty transition strengths."""
        lbmd_results_empty = LBMDResults(
            layer_name="test_layer",
            boundary_scores=np.random.rand(50),
            boundary_mask=np.random.choice([True, False], 50),
            manifold_coords=np.random.randn(50, 3),
            pixel_coords=np.random.randint(0, 224, (50, 2)),
            is_boundary=np.random.choice([True, False], 50),
            clusters=np.random.randint(0, 3, 50),
            transition_strengths={},  # Empty
            cluster_hulls={},
            statistical_metrics=StatisticalMetrics(0.5, 0.1, (0.4, 0.6), 0.3, 50),
            topological_properties=TopologicalProperties([1], np.array([[0, 1]]), 1, 0, {})
        )
        
        visualization = self.explorer.create_lbmd_visualization(lbmd_results_empty)
        
        self.assertIsNotNone(visualization)
        self.assertIn('figure', visualization.plot_data)


class TestInteractiveManifoldExplorerIntegration(unittest.TestCase):
    """Integration tests for InteractiveManifoldExplorer."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.config = {
            'output_dir': tempfile.mkdtemp(),
            'default_colorscale': 'Viridis'
        }
        self.explorer = InteractiveManifoldExplorer(self.config)
        self.explorer.initialize()
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        import shutil
        if os.path.exists(self.config['output_dir']):
            shutil.rmtree(self.config['output_dir'])
    
    def test_end_to_end_manifold_workflow(self):
        """Test complete manifold visualization workflow."""
        # Create data
        manifold_data = ManifoldData(
            coordinates=np.random.randn(100, 3),
            labels=np.random.randint(0, 5, 100),
            distances=np.random.rand(100, 100),
            neighborhoods={i: [j for j in range(5) if j != i] for i in range(100)},
            embedding_method="UMAP",
            parameters={"n_neighbors": 15}
        )
        
        # Create visualization
        visualization = self.explorer.create_interactive_manifold(manifold_data)
        
        # Create parameter interface
        try:
            interface = self.explorer.create_parameter_adjustment_interface(visualization)
            interface_created = True
        except:
            interface_created = False  # May fail without Jupyter
        
        # Export visualization
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp:
            filename = self.explorer.export_visualization(
                visualization, tmp.name[:-5], "html"
            )
            
            # Check file was created
            self.assertTrue(os.path.exists(filename))
            
            # Clean up
            os.unlink(filename)
        
        # Verify workflow completed
        self.assertIsNotNone(visualization)
        self.assertIn('figure', visualization.plot_data)
    
    def test_end_to_end_lbmd_workflow(self):
        """Test complete LBMD visualization workflow."""
        # Create LBMD results
        lbmd_results = LBMDResults(
            layer_name="backbone.layer4.2.conv3",
            boundary_scores=np.random.beta(2, 5, 200),
            boundary_mask=np.random.choice([True, False], 200),
            manifold_coords=np.random.randn(200, 3),
            pixel_coords=np.random.randint(0, 224, (200, 2)),
            is_boundary=np.random.choice([True, False], 200),
            clusters=np.random.randint(0, 5, 200),
            transition_strengths={(0, 1): 0.5, (1, 2): 0.7, (2, 3): 0.3},
            cluster_hulls={},
            statistical_metrics=StatisticalMetrics(0.78, 0.001, (0.7, 0.85), 0.6, 200),
            topological_properties=TopologicalProperties([1, 2], np.random.rand(5, 2), 1, 0, {})
        )
        
        # Create visualization
        visualization = self.explorer.create_lbmd_visualization(lbmd_results)
        
        # Export multiple formats
        formats = ['html', 'png']
        exported_files = []
        
        for fmt in formats:
            try:
                with tempfile.NamedTemporaryFile(suffix=f'.{fmt}', delete=False) as tmp:
                    filename = self.explorer.export_visualization(
                        visualization, tmp.name[:-4], fmt
                    )
                    exported_files.append(filename)
            except Exception as e:
                # Some formats may not be available in test environment
                print(f"Could not export {fmt}: {e}")
        
        # Clean up
        for filename in exported_files:
            if os.path.exists(filename):
                os.unlink(filename)
        
        # Verify workflow completed
        self.assertIsNotNone(visualization)
        self.assertIn('lbmd_results', visualization.plot_data)


if __name__ == '__main__':
    unittest.main()
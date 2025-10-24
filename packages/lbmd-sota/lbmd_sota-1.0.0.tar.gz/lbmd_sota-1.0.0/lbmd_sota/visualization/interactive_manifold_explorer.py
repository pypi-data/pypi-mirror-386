"""
Interactive manifold explorer for 3D visualizations.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

try:
    import ipywidgets as widgets
    from IPython.display import display
    WIDGETS_AVAILABLE = True
except ImportError:
    WIDGETS_AVAILABLE = False
    widgets = None

import pandas as pd

from ..core.interfaces import BaseVisualizer
from ..core.data_models import InteractiveVisualization, ManifoldData, LBMDResults


class InteractiveManifoldExplorer(BaseVisualizer):
    """Creates interactive 3D visualizations of boundary manifolds."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.color_schemes = {
            'boundary': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'],
            'cluster': px.colors.qualitative.Set3,
            'strength': px.colors.sequential.Viridis
        }
        self.plot_cache = {}
        
    def initialize(self) -> None:
        """Initialize the interactive manifold explorer."""
        try:
            import plotly
            if not WIDGETS_AVAILABLE:
                print("Warning: ipywidgets not available. Interactive controls will be limited.")
            self._initialized = True
        except ImportError as e:
            raise ImportError(f"Required packages not available: {e}")
    
    def visualize(self, data: Any, **kwargs) -> InteractiveVisualization:
        """Create interactive manifold visualization."""
        if isinstance(data, ManifoldData):
            return self.create_interactive_manifold(data, **kwargs)
        elif isinstance(data, LBMDResults):
            return self.create_lbmd_visualization(data, **kwargs)
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")
    
    def create_interactive_manifold(self, manifold_data: ManifoldData) -> InteractiveVisualization:
        """Create interactive manifold visualization from manifold data."""
        # Create 3D scatter plot
        fig = go.Figure()
        
        # Add manifold points
        coords = manifold_data.coordinates
        if coords.shape[1] >= 3:
            x, y, z = coords[:, 0], coords[:, 1], coords[:, 2]
        else:
            # Pad with zeros if less than 3D
            x, y = coords[:, 0], coords[:, 1]
            z = np.zeros_like(x)
        
        # Color by labels if available
        colors = manifold_data.labels if manifold_data.labels is not None else np.arange(len(x))
        
        scatter = go.Scatter3d(
            x=x, y=y, z=z,
            mode='markers',
            marker=dict(
                size=5,
                color=colors,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Cluster ID")
            ),
            text=[f"Point {i}<br>Label: {label}" for i, label in enumerate(colors)],
            hovertemplate="<b>Point %{text}</b><br>" +
                         "X: %{x:.3f}<br>" +
                         "Y: %{y:.3f}<br>" +
                         "Z: %{z:.3f}<extra></extra>"
        )
        
        fig.add_trace(scatter)
        
        # Add neighborhood connections if available
        if hasattr(manifold_data, 'neighborhoods') and manifold_data.neighborhoods:
            self._add_neighborhood_edges(fig, coords, manifold_data.neighborhoods)
        
        # Configure layout
        fig.update_layout(
            title=f"Interactive Manifold Visualization ({manifold_data.embedding_method})",
            scene=dict(
                xaxis_title="Dimension 1",
                yaxis_title="Dimension 2",
                zaxis_title="Dimension 3",
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
            ),
            width=800,
            height=600,
            showlegend=True
        )
        
        # Create interactive controls
        controls = self._create_parameter_controls(manifold_data)
        
        return InteractiveVisualization(
            plot_data={'figure': fig, 'controls': controls},
            interaction_callbacks=self._create_interaction_callbacks(),
            layout_config={'width': 800, 'height': 600},
            export_options=['html', 'png', 'pdf', 'svg']
        )

    def create_lbmd_visualization(self, lbmd_results: LBMDResults) -> InteractiveVisualization:
        """Create interactive visualization from LBMD results."""
        # Create subplot with multiple views
        fig = make_subplots(
            rows=2, cols=2,
            specs=[[{'type': 'scatter3d'}, {'type': 'scatter'}],
                   [{'type': 'heatmap'}, {'type': 'scatter'}]],
            subplot_titles=('3D Manifold', 'Boundary Scores', 'Transition Strengths', 'Cluster Analysis'),
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )
        
        # 3D manifold visualization
        coords = lbmd_results.manifold_coords
        if coords.shape[1] >= 3:
            x, y, z = coords[:, 0], coords[:, 1], coords[:, 2]
        else:
            x, y = coords[:, 0], coords[:, 1]
            z = np.zeros_like(x)
        
        # Color by boundary strength
        colors = lbmd_results.boundary_scores
        
        scatter3d = go.Scatter3d(
            x=x, y=y, z=z,
            mode='markers',
            marker=dict(
                size=4,
                color=colors,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Boundary Strength", x=0.45)
            ),
            text=[f"Neuron {i}<br>Boundary: {score:.3f}" for i, score in enumerate(colors)],
            hovertemplate="<b>Neuron %{text}</b><br>" +
                         "X: %{x:.3f}<br>" +
                         "Y: %{y:.3f}<br>" +
                         "Z: %{z:.3f}<extra></extra>",
            name="Manifold Points"
        )
        
        fig.add_trace(scatter3d, row=1, col=1)
        
        # Boundary scores histogram
        boundary_hist = go.Histogram(
            x=lbmd_results.boundary_scores,
            nbinsx=50,
            name="Boundary Scores",
            marker_color='rgba(55, 128, 191, 0.7)'
        )
        fig.add_trace(boundary_hist, row=1, col=2)
        
        # Update layout
        fig.update_layout(
            title=f"LBMD Analysis: {lbmd_results.layer_name}",
            height=800,
            width=1200,
            showlegend=False
        )
        
        # Create parameter controls for LBMD
        controls = self._create_lbmd_controls(lbmd_results)
        
        return InteractiveVisualization(
            plot_data={'figure': fig, 'controls': controls, 'lbmd_results': lbmd_results},
            interaction_callbacks=self._create_lbmd_callbacks(),
            layout_config={'width': 1200, 'height': 800},
            export_options=['html', 'png', 'pdf', 'svg']
        )
    
    def create_cross_layer_comparison(self, layer_results: Dict[str, LBMDResults]) -> InteractiveVisualization:
        """Create cross-layer manifold comparison visualization."""
        n_layers = len(layer_results)
        cols = min(3, n_layers)
        rows = (n_layers + cols - 1) // cols
        
        fig = make_subplots(
            rows=rows, cols=cols,
            specs=[[{'type': 'scatter3d'} for _ in range(cols)] for _ in range(rows)],
            subplot_titles=list(layer_results.keys()),
            vertical_spacing=0.05,
            horizontal_spacing=0.05
        )
        
        for idx, (layer_name, results) in enumerate(layer_results.items()):
            row = idx // cols + 1
            col = idx % cols + 1
            
            coords = results.manifold_coords
            if coords.shape[1] >= 3:
                x, y, z = coords[:, 0], coords[:, 1], coords[:, 2]
            else:
                x, y = coords[:, 0], coords[:, 1]
                z = np.zeros_like(x)
            
            scatter = go.Scatter3d(
                x=x, y=y, z=z,
                mode='markers',
                marker=dict(
                    size=3,
                    color=results.boundary_scores,
                    colorscale='Viridis',
                    showscale=(idx == 0),
                    colorbar=dict(title="Boundary Strength", x=1.02) if idx == 0 else None
                ),
                name=layer_name,
                showlegend=False
            )
            
            fig.add_trace(scatter, row=row, col=col)
        
        fig.update_layout(
            title="Cross-Layer Manifold Comparison",
            height=300 * rows,
            width=400 * cols,
            showlegend=False
        )
        
        # Create layer comparison controls
        controls = self._create_comparison_controls(layer_results)
        
        return InteractiveVisualization(
            plot_data={'figure': fig, 'controls': controls, 'layer_results': layer_results},
            interaction_callbacks=self._create_comparison_callbacks(),
            layout_config={'width': 400 * cols, 'height': 300 * rows},
            export_options=['html', 'png', 'pdf', 'svg']
        )
    
    def _add_neighborhood_edges(self, fig: go.Figure, coords: np.ndarray, neighborhoods: Dict[int, List[int]]):
        """Add neighborhood connection edges to the plot."""
        edge_x, edge_y, edge_z = [], [], []
        
        for node, neighbors in neighborhoods.items():
            if node < len(coords):
                for neighbor in neighbors:
                    if neighbor < len(coords):
                        edge_x.extend([coords[node, 0], coords[neighbor, 0], None])
                        edge_y.extend([coords[node, 1], coords[neighbor, 1], None])
                        if coords.shape[1] >= 3:
                            edge_z.extend([coords[node, 2], coords[neighbor, 2], None])
                        else:
                            edge_z.extend([0, 0, None])
        
        if edge_x:
            edge_trace = go.Scatter3d(
                x=edge_x, y=edge_y, z=edge_z,
                mode='lines',
                line=dict(color='rgba(125, 125, 125, 0.3)', width=1),
                hoverinfo='none',
                showlegend=False,
                name="Connections"
            )
            fig.add_trace(edge_trace)
    
    def _create_parameter_controls(self, manifold_data: ManifoldData) -> Dict[str, Any]:
        """Create interactive parameter controls for manifold exploration."""
        if not WIDGETS_AVAILABLE:
            return {
                'point_size': 5,
                'color_scheme': 'Viridis',
                'opacity': 0.8,
                'show_connections': True
            }
        
        controls = {}
        controls['point_size'] = widgets.IntSlider(
            value=5, min=1, max=20, step=1, description='Point Size:'
        )
        controls['color_scheme'] = widgets.Dropdown(
            options=['Viridis', 'Plasma', 'Inferno'], value='Viridis', description='Color Scheme:'
        )
        controls['opacity'] = widgets.FloatSlider(
            value=0.8, min=0.1, max=1.0, step=0.1, description='Opacity:'
        )
        controls['show_connections'] = widgets.Checkbox(
            value=True, description='Show Connections'
        )
        return controls
    
    def _create_lbmd_controls(self, lbmd_results: LBMDResults) -> Dict[str, Any]:
        """Create interactive controls for LBMD visualization."""
        if not WIDGETS_AVAILABLE:
            unique_clusters = np.unique(lbmd_results.clusters)
            return {
                'boundary_threshold': np.percentile(lbmd_results.boundary_scores, 75),
                'selected_clusters': list(unique_clusters),
                'view_mode': '3D Manifold'
            }
        
        controls = {}
        controls['boundary_threshold'] = widgets.FloatSlider(
            value=np.percentile(lbmd_results.boundary_scores, 75),
            min=np.min(lbmd_results.boundary_scores),
            max=np.max(lbmd_results.boundary_scores),
            step=0.01, description='Boundary Threshold:'
        )
        unique_clusters = np.unique(lbmd_results.clusters)
        controls['selected_clusters'] = widgets.SelectMultiple(
            options=[(f'Cluster {c}', c) for c in unique_clusters],
            value=list(unique_clusters), description='Show Clusters:'
        )
        controls['view_mode'] = widgets.RadioButtons(
            options=['3D Manifold', 'Boundary Analysis', 'Cluster View'],
            value='3D Manifold', description='View Mode:'
        )
        return controls
    
    def _create_comparison_controls(self, layer_results: Dict[str, LBMDResults]) -> Dict[str, Any]:
        """Create controls for cross-layer comparison."""
        if not WIDGETS_AVAILABLE:
            return {
                'selected_layers': list(layer_results.keys()),
                'sync_views': True,
                'comparison_metric': 'Boundary Strength'
            }
        
        controls = {}
        controls['selected_layers'] = widgets.SelectMultiple(
            options=list(layer_results.keys()),
            value=list(layer_results.keys()), description='Show Layers:'
        )
        controls['sync_views'] = widgets.Checkbox(
            value=True, description='Synchronize Camera Views'
        )
        controls['comparison_metric'] = widgets.Dropdown(
            options=['Boundary Strength', 'Cluster Similarity'],
            value='Boundary Strength', description='Comparison Metric:'
        )
        return controls
    
    def _create_interaction_callbacks(self) -> Dict[str, callable]:
        """Create interaction callbacks for manifold exploration."""
        return {
            'point_size': lambda change: None,
            'color_scheme': lambda change: None,
            'connections': lambda change: None
        }
    
    def _create_lbmd_callbacks(self) -> Dict[str, callable]:
        """Create callbacks for LBMD visualization interactions."""
        return {
            'boundary_threshold': lambda change: None,
            'cluster_selection': lambda change: None,
            'view_mode': lambda change: None
        }
    
    def _create_comparison_callbacks(self) -> Dict[str, callable]:
        """Create callbacks for cross-layer comparison interactions."""
        return {
            'layer_selection': lambda change: None,
            'sync_views': lambda change: None,
            'comparison_metric': lambda change: None
        }
    
    def export_visualization(self, visualization: InteractiveVisualization, 
                           filename: str, format: str = 'html') -> str:
        """Export visualization to specified format."""
        fig = visualization.plot_data['figure']
        
        if format.lower() == 'html':
            fig.write_html(f"{filename}.html")
        elif format.lower() == 'png':
            fig.write_image(f"{filename}.png")
        elif format.lower() == 'pdf':
            fig.write_image(f"{filename}.pdf")
        elif format.lower() == 'svg':
            fig.write_image(f"{filename}.svg")
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        return f"{filename}.{format.lower()}"
    
    def create_parameter_adjustment_interface(self, visualization: InteractiveVisualization) -> Any:
        """Create real-time parameter adjustment interface."""
        if not WIDGETS_AVAILABLE:
            controls = visualization.plot_data.get('controls', {})
            return {
                'controls': controls,
                'export_options': ['html', 'png', 'pdf', 'svg'],
                'default_filename': 'lbmd_visualization'
            }
        
        controls = visualization.plot_data.get('controls', {})
        control_widgets = [widget for widget in controls.values() if hasattr(widget, 'description')]
        
        export_button = widgets.Button(description='Export Visualization', button_style='success')
        format_dropdown = widgets.Dropdown(options=['html', 'png', 'pdf', 'svg'], value='html')
        filename_text = widgets.Text(value='lbmd_visualization', description='Filename:')
        
        export_box = widgets.HBox([filename_text, format_dropdown, export_button])
        all_controls = control_widgets + [export_box]
        
        return widgets.VBox(all_controls)
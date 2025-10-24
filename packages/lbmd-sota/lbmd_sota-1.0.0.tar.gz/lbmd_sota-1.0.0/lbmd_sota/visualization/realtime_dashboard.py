"""
Real-time dashboard for live analysis interface.
"""

from typing import Dict, List, Any, Optional, Callable
import numpy as np
import pandas as pd
import threading
import time
import json
from datetime import datetime
import queue

try:
    import dash
    from dash import dcc, html, Input, Output, State, callback_context
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import dash_bootstrap_components as dbc
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False
    dash = None
    dcc = html = Input = Output = State = None
    go = px = make_subplots = None
    dbc = None

from ..core.interfaces import BaseComponent
from ..core.data_models import Dashboard, LBMDResults, ExperimentConfig


class RealtimeDashboard(BaseComponent):
    """Provides live analysis interface for researchers."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.port = config.get('port', 8050)
        self.host = config.get('host', '127.0.0.1')
        self.debug = config.get('debug', False)
        self.update_interval = config.get('update_interval', 2000)  # milliseconds
        
        # Data storage
        self.experiment_data = {}
        self.live_metrics = queue.Queue()
        self.experiment_history = []
        
        # Dashboard components
        self.app = None
        self.server_thread = None
        
    def initialize(self) -> None:
        """Initialize the real-time dashboard."""
        if not DASH_AVAILABLE:
            raise ImportError("Dash is required for the real-time dashboard. Install with: pip install dash dash-bootstrap-components")
        
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self._setup_layout()
        self._setup_callbacks()
        self._initialized = True
    
    def launch_analysis_dashboard(self, config: Dict[str, Any]) -> Dashboard:
        """Launch real-time analysis dashboard."""
        if not self._initialized:
            self.initialize()
        
        # Start the dashboard server in a separate thread
        self.server_thread = threading.Thread(
            target=self._run_server,
            daemon=True
        )
        self.server_thread.start()
        
        # Wait a moment for server to start
        time.sleep(2)
        
        dashboard_url = f"http://{self.host}:{self.port}"
        print(f"Dashboard launched at: {dashboard_url}")
        
        return Dashboard(
            components=['experiment_monitor', 'live_metrics', 'visualization_panel', 'control_panel'],
            layout={'type': 'grid', 'rows': 2, 'cols': 2},
            data_sources={'experiments': 'live', 'metrics': 'streaming'},
            update_frequency=self.update_interval / 1000.0,
            user_permissions={'admin': ['read', 'write', 'execute']}
        )
    
    def _setup_layout(self):
        """Set up the dashboard layout."""
        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("LBMD Real-Time Analysis Dashboard", className="text-center mb-4"),
                    html.Hr()
                ])
            ]),
            
            # Control Panel
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Experiment Control"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Dataset:"),
                                    dcc.Dropdown(
                                        id='dataset-dropdown',
                                        options=[
                                            {'label': 'COCO', 'value': 'coco'},
                                            {'label': 'Cityscapes', 'value': 'cityscapes'},
                                            {'label': 'Pascal VOC', 'value': 'pascal_voc'},
                                            {'label': 'ADE20K', 'value': 'ade20k'}
                                        ],
                                        value='coco'
                                    )
                                ], width=6),
                                dbc.Col([
                                    dbc.Label("Model:"),
                                    dcc.Dropdown(
                                        id='model-dropdown',
                                        options=[
                                            {'label': 'Mask R-CNN', 'value': 'mask_rcnn'},
                                            {'label': 'SOLO', 'value': 'solo'},
                                            {'label': 'YOLACT', 'value': 'yolact'},
                                            {'label': 'Mask2Former', 'value': 'mask2former'}
                                        ],
                                        value='mask_rcnn'
                                    )
                                ], width=6)
                            ]),
                            html.Br(),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button("Start Experiment", id="start-btn", color="success", className="me-2"),
                                    dbc.Button("Stop Experiment", id="stop-btn", color="danger", className="me-2"),
                                    dbc.Button("Reset", id="reset-btn", color="warning")
                                ])
                            ])
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            # Status and Metrics Row
            dbc.Row([
                # Live Metrics
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Live Metrics"),
                        dbc.CardBody([
                            dcc.Graph(id='live-metrics-graph'),
                            dcc.Interval(
                                id='metrics-interval',
                                interval=self.update_interval,
                                n_intervals=0
                            )
                        ])
                    ])
                ], width=6),
                
                # Experiment Status
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Experiment Status"),
                        dbc.CardBody([
                            html.Div(id='status-display'),
                            html.Br(),
                            dbc.Progress(id="progress-bar", value=0, striped=True, animated=True),
                            html.Br(),
                            html.Div(id='experiment-info')
                        ])
                    ])
                ], width=6)
            ], className="mb-4"),
            
            # Visualization Row
            dbc.Row([
                # Boundary Analysis
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Boundary Analysis"),
                        dbc.CardBody([
                            dcc.Graph(id='boundary-analysis-graph')
                        ])
                    ])
                ], width=6),
                
                # Manifold Visualization
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Manifold Structure"),
                        dbc.CardBody([
                            dcc.Graph(id='manifold-graph')
                        ])
                    ])
                ], width=6)
            ], className="mb-4"),
            
            # Results Table
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Experiment Results"),
                        dbc.CardBody([
                            html.Div(id='results-table')
                        ])
                    ])
                ], width=12)
            ]),
            
            # Hidden div to store experiment state
            html.Div(id='experiment-state', style={'display': 'none'}),
            
        ], fluid=True)
    
    def _setup_callbacks(self):
        """Set up dashboard callbacks."""
        
        @self.app.callback(
            [Output('experiment-state', 'children'),
             Output('status-display', 'children'),
             Output('progress-bar', 'value')],
            [Input('start-btn', 'n_clicks'),
             Input('stop-btn', 'n_clicks'),
             Input('reset-btn', 'n_clicks')],
            [State('dataset-dropdown', 'value'),
             State('model-dropdown', 'value'),
             State('experiment-state', 'children')]
        )
        def control_experiment(start_clicks, stop_clicks, reset_clicks, dataset, model, current_state):
            ctx = callback_context
            if not ctx.triggered:
                return '{"status": "idle", "progress": 0}', self._create_status_display("idle"), 0
            
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if button_id == 'start-btn' and start_clicks:
                # Start new experiment
                experiment_id = f"exp_{int(time.time())}"
                state = {
                    "status": "running",
                    "experiment_id": experiment_id,
                    "dataset": dataset,
                    "model": model,
                    "start_time": datetime.now().isoformat(),
                    "progress": 10
                }
                
                # Start background experiment simulation
                self._start_experiment_simulation(experiment_id, dataset, model)
                
                return json.dumps(state), self._create_status_display("running", experiment_id), 10
            
            elif button_id == 'stop-btn' and stop_clicks:
                state = {"status": "stopped", "progress": 0}
                return json.dumps(state), self._create_status_display("stopped"), 0
            
            elif button_id == 'reset-btn' and reset_clicks:
                state = {"status": "idle", "progress": 0}
                self.experiment_data.clear()
                return json.dumps(state), self._create_status_display("idle"), 0
            
            return current_state or '{"status": "idle", "progress": 0}', self._create_status_display("idle"), 0
        
        @self.app.callback(
            Output('live-metrics-graph', 'figure'),
            [Input('metrics-interval', 'n_intervals')],
            [State('experiment-state', 'children')]
        )
        def update_live_metrics(n_intervals, experiment_state):
            if not experiment_state:
                return self._create_empty_metrics_figure()
            
            state = json.loads(experiment_state)
            if state.get('status') != 'running':
                return self._create_empty_metrics_figure()
            
            # Generate live metrics data
            metrics_data = self._get_live_metrics_data()
            
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Boundary Strength', 'Correlation', 'Processing Speed', 'Memory Usage'),
                specs=[[{'secondary_y': False}, {'secondary_y': False}],
                       [{'secondary_y': False}, {'secondary_y': False}]]
            )
            
            # Boundary strength over time
            fig.add_trace(
                go.Scatter(
                    x=metrics_data['timestamps'],
                    y=metrics_data['boundary_strength'],
                    mode='lines+markers',
                    name='Boundary Strength',
                    line=dict(color='blue')
                ),
                row=1, col=1
            )
            
            # Correlation over time
            fig.add_trace(
                go.Scatter(
                    x=metrics_data['timestamps'],
                    y=metrics_data['correlation'],
                    mode='lines+markers',
                    name='Correlation',
                    line=dict(color='red')
                ),
                row=1, col=2
            )
            
            # Processing speed
            fig.add_trace(
                go.Scatter(
                    x=metrics_data['timestamps'],
                    y=metrics_data['processing_speed'],
                    mode='lines+markers',
                    name='Speed (samples/sec)',
                    line=dict(color='green')
                ),
                row=2, col=1
            )
            
            # Memory usage
            fig.add_trace(
                go.Scatter(
                    x=metrics_data['timestamps'],
                    y=metrics_data['memory_usage'],
                    mode='lines+markers',
                    name='Memory (MB)',
                    line=dict(color='orange')
                ),
                row=2, col=2
            )
            
            fig.update_layout(
                height=400,
                showlegend=False,
                title_text="Live Experiment Metrics"
            )
            
            return fig
        
        @self.app.callback(
            Output('boundary-analysis-graph', 'figure'),
            [Input('metrics-interval', 'n_intervals')],
            [State('experiment-state', 'children')]
        )
        def update_boundary_analysis(n_intervals, experiment_state):
            if not experiment_state:
                return self._create_empty_boundary_figure()
            
            state = json.loads(experiment_state)
            if state.get('status') != 'running':
                return self._create_empty_boundary_figure()
            
            # Generate boundary analysis data
            boundary_data = self._get_boundary_analysis_data()
            
            fig = go.Figure()
            
            # Boundary score distribution
            fig.add_trace(go.Histogram(
                x=boundary_data['scores'],
                nbinsx=30,
                name='Boundary Scores',
                opacity=0.7
            ))
            
            # Add threshold line
            threshold = np.percentile(boundary_data['scores'], 75)
            fig.add_vline(
                x=threshold,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Threshold: {threshold:.3f}"
            )
            
            fig.update_layout(
                title="Boundary Score Distribution",
                xaxis_title="Boundary Strength",
                yaxis_title="Frequency",
                height=300
            )
            
            return fig
        
        @self.app.callback(
            Output('manifold-graph', 'figure'),
            [Input('metrics-interval', 'n_intervals')],
            [State('experiment-state', 'children')]
        )
        def update_manifold_visualization(n_intervals, experiment_state):
            if not experiment_state:
                return self._create_empty_manifold_figure()
            
            state = json.loads(experiment_state)
            if state.get('status') != 'running':
                return self._create_empty_manifold_figure()
            
            # Generate manifold data
            manifold_data = self._get_manifold_data()
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter3d(
                x=manifold_data['coords'][:, 0],
                y=manifold_data['coords'][:, 1],
                z=manifold_data['coords'][:, 2],
                mode='markers',
                marker=dict(
                    size=4,
                    color=manifold_data['boundary_scores'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Boundary Strength")
                ),
                name='Neurons'
            ))
            
            fig.update_layout(
                title="3D Manifold Structure",
                scene=dict(
                    xaxis_title="Dimension 1",
                    yaxis_title="Dimension 2",
                    zaxis_title="Dimension 3"
                ),
                height=300
            )
            
            return fig
        
        @self.app.callback(
            Output('results-table', 'children'),
            [Input('metrics-interval', 'n_intervals')],
            [State('experiment-state', 'children')]
        )
        def update_results_table(n_intervals, experiment_state):
            if not self.experiment_history:
                return html.P("No experiments completed yet.")
            
            # Create results table
            df = pd.DataFrame(self.experiment_history)
            
            table = dbc.Table.from_dataframe(
                df,
                striped=True,
                bordered=True,
                hover=True,
                responsive=True,
                size='sm'
            )
            
            return table
        
        @self.app.callback(
            Output('experiment-info', 'children'),
            [Input('metrics-interval', 'n_intervals')],
            [State('experiment-state', 'children')]
        )
        def update_experiment_info(n_intervals, experiment_state):
            if not experiment_state:
                return html.P("No active experiment")
            
            state = json.loads(experiment_state)
            
            if state.get('status') == 'running':
                experiment_id = state.get('experiment_id', 'Unknown')
                dataset = state.get('dataset', 'Unknown')
                model = state.get('model', 'Unknown')
                start_time = state.get('start_time', 'Unknown')
                
                return html.Div([
                    html.P(f"Experiment ID: {experiment_id}"),
                    html.P(f"Dataset: {dataset.upper()}"),
                    html.P(f"Model: {model.replace('_', ' ').title()}"),
                    html.P(f"Started: {start_time}")
                ])
            
            return html.P("No active experiment")
    
    def _create_status_display(self, status: str, experiment_id: str = None) -> html.Div:
        """Create status display component."""
        if status == "idle":
            return dbc.Alert("System ready. Select dataset and model to start experiment.", color="info")
        elif status == "running":
            return dbc.Alert(f"Experiment {experiment_id} is running...", color="success")
        elif status == "stopped":
            return dbc.Alert("Experiment stopped by user.", color="warning")
        else:
            return dbc.Alert("Unknown status.", color="secondary")
    
    def _start_experiment_simulation(self, experiment_id: str, dataset: str, model: str):
        """Start background experiment simulation."""
        def simulate_experiment():
            # Simulate experiment progress
            for i in range(100):
                if experiment_id not in self.experiment_data:
                    self.experiment_data[experiment_id] = {
                        'dataset': dataset,
                        'model': model,
                        'progress': 0,
                        'metrics': []
                    }
                
                # Update progress
                self.experiment_data[experiment_id]['progress'] = i + 1
                
                # Generate metrics
                metrics = {
                    'timestamp': time.time(),
                    'boundary_strength': 0.5 + 0.3 * np.sin(i * 0.1) + 0.1 * np.random.randn(),
                    'correlation': 0.7 + 0.2 * np.cos(i * 0.05) + 0.05 * np.random.randn(),
                    'processing_speed': 50 + 10 * np.random.randn(),
                    'memory_usage': 1000 + 200 * np.random.randn()
                }
                
                self.experiment_data[experiment_id]['metrics'].append(metrics)
                
                time.sleep(0.5)  # Simulate processing time
            
            # Add to experiment history
            self.experiment_history.append({
                'Experiment ID': experiment_id,
                'Dataset': dataset.upper(),
                'Model': model.replace('_', ' ').title(),
                'Status': 'Completed',
                'Final Correlation': f"{metrics['correlation']:.3f}",
                'Completion Time': datetime.now().strftime('%H:%M:%S')
            })
        
        thread = threading.Thread(target=simulate_experiment, daemon=True)
        thread.start()
    
    def _get_live_metrics_data(self) -> Dict[str, List]:
        """Get live metrics data for plotting."""
        # Get recent metrics from all active experiments
        all_metrics = []
        for exp_data in self.experiment_data.values():
            all_metrics.extend(exp_data.get('metrics', []))
        
        if not all_metrics:
            # Return empty data
            return {
                'timestamps': [],
                'boundary_strength': [],
                'correlation': [],
                'processing_speed': [],
                'memory_usage': []
            }
        
        # Sort by timestamp and take last 50 points
        all_metrics.sort(key=lambda x: x['timestamp'])
        recent_metrics = all_metrics[-50:]
        
        return {
            'timestamps': [datetime.fromtimestamp(m['timestamp']) for m in recent_metrics],
            'boundary_strength': [m['boundary_strength'] for m in recent_metrics],
            'correlation': [m['correlation'] for m in recent_metrics],
            'processing_speed': [m['processing_speed'] for m in recent_metrics],
            'memory_usage': [m['memory_usage'] for m in recent_metrics]
        }
    
    def _get_boundary_analysis_data(self) -> Dict[str, np.ndarray]:
        """Get boundary analysis data."""
        # Generate synthetic boundary scores
        n_neurons = 1000
        boundary_scores = np.random.beta(2, 5, n_neurons)
        
        return {
            'scores': boundary_scores,
            'threshold': np.percentile(boundary_scores, 75)
        }
    
    def _get_manifold_data(self) -> Dict[str, np.ndarray]:
        """Get manifold visualization data."""
        # Generate synthetic 3D manifold
        n_points = 500
        coords = np.random.randn(n_points, 3)
        boundary_scores = np.random.beta(2, 5, n_points)
        
        return {
            'coords': coords,
            'boundary_scores': boundary_scores
        }
    
    def _create_empty_metrics_figure(self) -> go.Figure:
        """Create empty metrics figure."""
        fig = go.Figure()
        fig.add_annotation(
            text="No active experiment",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        fig.update_layout(
            title="Live Experiment Metrics",
            height=400,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig
    
    def _create_empty_boundary_figure(self) -> go.Figure:
        """Create empty boundary analysis figure."""
        fig = go.Figure()
        fig.add_annotation(
            text="Start experiment to see boundary analysis",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=14)
        )
        fig.update_layout(
            title="Boundary Score Distribution",
            height=300,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig
    
    def _create_empty_manifold_figure(self) -> go.Figure:
        """Create empty manifold figure."""
        fig = go.Figure()
        fig.add_annotation(
            text="Start experiment to see manifold structure",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=14)
        )
        fig.update_layout(
            title="3D Manifold Structure",
            height=300,
            scene=dict(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                zaxis=dict(visible=False)
            )
        )
        return fig
    
    def _run_server(self):
        """Run the dashboard server."""
        self.app.run(
            host=self.host,
            port=self.port,
            debug=self.debug,
            use_reloader=False
        )
    
    def add_experiment_data(self, experiment_id: str, lbmd_results: LBMDResults):
        """Add experiment data to the dashboard."""
        if experiment_id not in self.experiment_data:
            self.experiment_data[experiment_id] = {
                'results': [],
                'metrics': []
            }
        
        self.experiment_data[experiment_id]['results'].append(lbmd_results)
        
        # Extract metrics for live display
        metrics = {
            'timestamp': time.time(),
            'boundary_strength': np.mean(lbmd_results.boundary_scores),
            'correlation': lbmd_results.statistical_metrics.correlation,
            'n_clusters': len(np.unique(lbmd_results.clusters)),
            'layer': lbmd_results.layer_name
        }
        
        self.experiment_data[experiment_id]['metrics'].append(metrics)
    
    def update_experiment_progress(self, experiment_id: str, progress: float, status: str = None):
        """Update experiment progress."""
        if experiment_id in self.experiment_data:
            self.experiment_data[experiment_id]['progress'] = progress
            if status:
                self.experiment_data[experiment_id]['status'] = status
    
    def get_experiment_summary(self, experiment_id: str) -> Dict[str, Any]:
        """Get experiment summary."""
        if experiment_id not in self.experiment_data:
            return {}
        
        exp_data = self.experiment_data[experiment_id]
        results = exp_data.get('results', [])
        
        if not results:
            return {'experiment_id': experiment_id, 'status': 'no_data'}
        
        # Compute summary statistics
        all_correlations = [r.statistical_metrics.correlation for r in results]
        all_boundary_scores = np.concatenate([r.boundary_scores for r in results])
        
        return {
            'experiment_id': experiment_id,
            'n_layers': len(results),
            'mean_correlation': np.mean(all_correlations),
            'std_correlation': np.std(all_correlations),
            'mean_boundary_strength': np.mean(all_boundary_scores),
            'total_neurons': len(all_boundary_scores),
            'layers_analyzed': [r.layer_name for r in results]
        }
    
    def export_experiment_data(self, experiment_id: str, filepath: str):
        """Export experiment data to file."""
        if experiment_id not in self.experiment_data:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        exp_data = self.experiment_data[experiment_id]
        
        # Convert to serializable format
        export_data = {
            'experiment_id': experiment_id,
            'timestamp': datetime.now().isoformat(),
            'summary': self.get_experiment_summary(experiment_id),
            'metrics': exp_data.get('metrics', []),
            'results_summary': []
        }
        
        # Add results summary (without large arrays)
        for result in exp_data.get('results', []):
            result_summary = {
                'layer_name': result.layer_name,
                'n_neurons': len(result.boundary_scores),
                'mean_boundary_score': float(np.mean(result.boundary_scores)),
                'correlation': result.statistical_metrics.correlation,
                'p_value': result.statistical_metrics.p_value,
                'n_clusters': len(np.unique(result.clusters))
            }
            export_data['results_summary'].append(result_summary)
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def stop_dashboard(self):
        """Stop the dashboard server."""
        if self.server_thread and self.server_thread.is_alive():
            # Note: Dash doesn't have a clean shutdown method
            # In production, you might want to use a more sophisticated approach
            print("Dashboard server stopping...")
            self._initialized = False
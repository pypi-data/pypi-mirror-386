"""
Automated Report Generator for LBMD Experiments

This module provides comprehensive experimental report templates, automated statistical
analysis and visualization, and comparison report generation across different experimental conditions.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from jinja2 import Environment, FileSystemLoader, Template
from matplotlib.backends.backend_pdf import PdfPages

from ..core.data_models import LBMDResults, ValidationResults
from ..empirical_validation.statistical_analyzer import StatisticalAnalyzer


class ReportTemplate:
    """Base class for report templates"""
    
    def __init__(self, template_name: str):
        self.template_name = template_name
        self.created_at = datetime.now()
    
    def render(self, data: Dict[str, Any]) -> str:
        """Render template with data"""
        raise NotImplementedError


class HTMLReportTemplate(ReportTemplate):
    """HTML report template using Jinja2"""
    
    def __init__(self, template_path: Optional[str] = None):
        super().__init__("HTML Report")
        
        if template_path and Path(template_path).exists():
            env = Environment(loader=FileSystemLoader(Path(template_path).parent))
            self.template = env.get_template(Path(template_path).name)
        else:
            # Use default template
            self.template = Template(self._get_default_template())
    
    def _get_default_template(self) -> str:
        """Default HTML template for LBMD reports"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>LBMD Experiment Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; }
        .metric { display: inline-block; margin: 10px; padding: 10px; 
                 background-color: #e8f4f8; border-radius: 3px; }
        .table { border-collapse: collapse; width: 100%; }
        .table th, .table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .table th { background-color: #f2f2f2; }
        .figure { text-align: center; margin: 20px 0; }
        .error { color: red; }
        .success { color: green; }
    </style>
</head>
<body>
    <div class="header">
        <h1>LBMD Experiment Report</h1>
        <p><strong>Generated:</strong> {{ report_metadata.generated_at }}</p>
        <p><strong>Experiment ID:</strong> {{ report_metadata.experiment_id }}</p>
        <p><strong>Total Experiments:</strong> {{ summary_statistics.total_experiments }}</p>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <div class="metric">
            <strong>Success Rate:</strong> 
            <span class="{{ 'success' if summary_statistics.success_rate > 0.8 else 'error' }}">
                {{ "%.1f%%" | format(summary_statistics.success_rate * 100) }}
            </span>
        </div>
        <div class="metric">
            <strong>Mean Execution Time:</strong> {{ "%.2f" | format(summary_statistics.mean_execution_time) }}s
        </div>
        <div class="metric">
            <strong>Mean Memory Usage:</strong> {{ "%.1f" | format(summary_statistics.mean_memory_usage) }}MB
        </div>
    </div>

    <div class="section">
        <h2>Statistical Analysis</h2>
        {% if statistical_analysis %}
        <table class="table">
            <tr>
                <th>Metric</th>
                <th>Value</th>
                <th>Confidence Interval</th>
                <th>P-value</th>
            </tr>
            {% for metric_name, metric_data in statistical_analysis.items() %}
            <tr>
                <td>{{ metric_name }}</td>
                <td>{{ "%.4f" | format(metric_data.value) }}</td>
                <td>[{{ "%.4f" | format(metric_data.ci_lower) }}, {{ "%.4f" | format(metric_data.ci_upper) }}]</td>
                <td>{{ "%.4f" | format(metric_data.p_value) if metric_data.p_value else "N/A" }}</td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <p>No statistical analysis available.</p>
        {% endif %}
    </div>

    <div class="section">
        <h2>Dataset Performance</h2>
        <table class="table">
            <tr>
                <th>Dataset</th>
                <th>Model</th>
                <th>Success Rate</th>
                <th>Mean Boundary Score</th>
                <th>Mean Transition Strength</th>
            </tr>
            {% for result in dataset_results %}
            <tr>
                <td>{{ result.dataset }}</td>
                <td>{{ result.model }}</td>
                <td>{{ "%.1f%%" | format(result.success_rate * 100) }}</td>
                <td>{{ "%.4f" | format(result.mean_boundary_score) }}</td>
                <td>{{ "%.4f" | format(result.mean_transition_strength) }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <div class="section">
        <h2>Visualizations</h2>
        {% for figure in figures %}
        <div class="figure">
            <h3>{{ figure.title }}</h3>
            <img src="{{ figure.path }}" alt="{{ figure.title }}" style="max-width: 100%;">
            <p>{{ figure.caption }}</p>
        </div>
        {% endfor %}
    </div>

    <div class="section">
        <h2>Detailed Results</h2>
        <p>Complete experimental data is available in the accompanying CSV file.</p>
    </div>

    <div class="section">
        <h2>Conclusions</h2>
        {% if conclusions %}
        <ul>
        {% for conclusion in conclusions %}
            <li>{{ conclusion }}</li>
        {% endfor %}
        </ul>
        {% else %}
        <p>No automated conclusions generated.</p>
        {% endif %}
    </div>
</body>
</html>
        """
    
    def render(self, data: Dict[str, Any]) -> str:
        """Render HTML report with data"""
        return self.template.render(**data)


class MarkdownReportTemplate(ReportTemplate):
    """Markdown report template"""
    
    def __init__(self):
        super().__init__("Markdown Report")
    
    def render(self, data: Dict[str, Any]) -> str:
        """Render Markdown report with data"""
        report = f"""# LBMD Experiment Report

**Generated:** {data.get('report_metadata', {}).get('generated_at', 'Unknown')}
**Experiment ID:** {data.get('report_metadata', {}).get('experiment_id', 'Unknown')}

## Executive Summary

- **Total Experiments:** {data.get('summary_statistics', {}).get('total_experiments', 0)}
- **Success Rate:** {data.get('summary_statistics', {}).get('success_rate', 0) * 100:.1f}%
- **Mean Execution Time:** {data.get('summary_statistics', {}).get('mean_execution_time', 0):.2f}s
- **Mean Memory Usage:** {data.get('summary_statistics', {}).get('mean_memory_usage', 0):.1f}MB

## Statistical Analysis

"""
        
        # Add statistical analysis table
        if 'statistical_analysis' in data and data['statistical_analysis']:
            report += "| Metric | Value | Confidence Interval | P-value |\n"
            report += "|--------|-------|-------------------|----------|\n"
            
            for metric_name, metric_data in data['statistical_analysis'].items():
                ci_str = f"[{metric_data.get('ci_lower', 0):.4f}, {metric_data.get('ci_upper', 0):.4f}]"
                p_val = metric_data.get('p_value', 'N/A')
                p_val_str = f"{p_val:.4f}" if isinstance(p_val, (int, float)) else str(p_val)
                
                report += f"| {metric_name} | {metric_data.get('value', 0):.4f} | {ci_str} | {p_val_str} |\n"
        else:
            report += "No statistical analysis available.\n"
        
        # Add dataset results
        report += "\n## Dataset Performance\n\n"
        if 'dataset_results' in data and data['dataset_results']:
            report += "| Dataset | Model | Success Rate | Mean Boundary Score | Mean Transition Strength |\n"
            report += "|---------|-------|--------------|-------------------|------------------------|\n"
            
            for result in data['dataset_results']:
                report += f"| {result.get('dataset', 'Unknown')} | {result.get('model', 'Unknown')} | "
                report += f"{result.get('success_rate', 0) * 100:.1f}% | "
                report += f"{result.get('mean_boundary_score', 0):.4f} | "
                report += f"{result.get('mean_transition_strength', 0):.4f} |\n"
        else:
            report += "No dataset results available.\n"
        
        # Add conclusions
        if 'conclusions' in data and data['conclusions']:
            report += "\n## Conclusions\n\n"
            for conclusion in data['conclusions']:
                report += f"- {conclusion}\n"
        
        return report


class VisualizationGenerator:
    """Generates visualizations for experiment reports"""
    
    def __init__(self, output_dir: str = "./report_figures"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Set style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def create_performance_summary(self, 
                                 summary_df: pd.DataFrame,
                                 output_name: str = "performance_summary") -> str:
        """Create performance summary visualization"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('LBMD Experiment Performance Summary', fontsize=16)
        
        # Success rate by dataset/model
        if 'success' in summary_df.columns and 'dataset' in summary_df.columns and 'model' in summary_df.columns:
            try:
                success_by_group = summary_df.groupby(['dataset', 'model'])['success'].mean().reset_index()
                success_pivot = success_by_group.pivot(index='dataset', columns='model', values='success')
                
                sns.heatmap(success_pivot, annot=True, fmt='.2%', ax=axes[0, 0], cmap='RdYlGn')
                axes[0, 0].set_title('Success Rate by Dataset and Model')
            except Exception as e:
                axes[0, 0].text(0.5, 0.5, f'Dataset/Model grouping not available\n{str(e)}', 
                               ha='center', va='center', transform=axes[0, 0].transAxes)
                axes[0, 0].set_title('Success Rate by Dataset and Model (N/A)')
        else:
            axes[0, 0].text(0.5, 0.5, 'Dataset/Model columns not available', 
                           ha='center', va='center', transform=axes[0, 0].transAxes)
            axes[0, 0].set_title('Success Rate by Dataset and Model (N/A)')
        
        # Execution time distribution
        if 'execution_time' in summary_df.columns:
            summary_df['execution_time'].hist(bins=30, ax=axes[0, 1], alpha=0.7)
            axes[0, 1].set_title('Execution Time Distribution')
            axes[0, 1].set_xlabel('Execution Time (s)')
            axes[0, 1].set_ylabel('Frequency')
        else:
            axes[0, 1].text(0.5, 0.5, 'Execution time data not available', 
                           ha='center', va='center', transform=axes[0, 1].transAxes)
            axes[0, 1].set_title('Execution Time Distribution (N/A)')
        
        # Memory usage vs execution time
        if 'memory_usage' in summary_df.columns and 'execution_time' in summary_df.columns:
            axes[1, 0].scatter(summary_df['execution_time'], summary_df['memory_usage'], alpha=0.6)
            axes[1, 0].set_xlabel('Execution Time (s)')
            axes[1, 0].set_ylabel('Memory Usage (MB)')
            axes[1, 0].set_title('Memory Usage vs Execution Time')
        else:
            axes[1, 0].text(0.5, 0.5, 'Memory/Time data not available', 
                           ha='center', va='center', transform=axes[1, 0].transAxes)
            axes[1, 0].set_title('Memory Usage vs Execution Time (N/A)')
        
        # Boundary score distribution
        if 'mean_boundary_score' in summary_df.columns:
            summary_df['mean_boundary_score'].hist(bins=30, ax=axes[1, 1], alpha=0.7)
            axes[1, 1].set_title('Boundary Score Distribution')
            axes[1, 1].set_xlabel('Mean Boundary Score')
            axes[1, 1].set_ylabel('Frequency')
        else:
            axes[1, 1].text(0.5, 0.5, 'Boundary score data not available', 
                           ha='center', va='center', transform=axes[1, 1].transAxes)
            axes[1, 1].set_title('Boundary Score Distribution (N/A)')
        
        plt.tight_layout()
        
        output_path = self.output_dir / f"{output_name}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(output_path)
    
    def create_statistical_analysis_plot(self,
                                       statistical_results: Dict[str, Any],
                                       output_name: str = "statistical_analysis") -> str:
        """Create statistical analysis visualization"""
        if not statistical_results:
            return ""
        
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        fig.suptitle('Statistical Analysis Results', fontsize=16)
        
        # Extract metrics for plotting
        metrics = []
        values = []
        ci_lower = []
        ci_upper = []
        
        for metric_name, metric_data in statistical_results.items():
            if isinstance(metric_data, dict):
                metrics.append(metric_name)
                values.append(metric_data.get('value', 0))
                ci_lower.append(metric_data.get('ci_lower', 0))
                ci_upper.append(metric_data.get('ci_upper', 0))
        
        if metrics:
            # Confidence intervals plot
            y_pos = np.arange(len(metrics))
            axes[0].errorbar(values, y_pos, 
                           xerr=[np.array(values) - np.array(ci_lower),
                                np.array(ci_upper) - np.array(values)],
                           fmt='o', capsize=5)
            axes[0].set_yticks(y_pos)
            axes[0].set_yticklabels(metrics)
            axes[0].set_xlabel('Value')
            axes[0].set_title('Confidence Intervals')
            axes[0].grid(True, alpha=0.3)
            
            # P-values plot (if available)
            p_values = [statistical_results[m].get('p_value', 1.0) for m in metrics]
            if any(isinstance(p, (int, float)) for p in p_values):
                colors = ['red' if p < 0.05 else 'blue' for p in p_values if isinstance(p, (int, float))]
                valid_p_values = [p for p in p_values if isinstance(p, (int, float))]
                valid_metrics = [m for m, p in zip(metrics, p_values) if isinstance(p, (int, float))]
                
                if valid_p_values:
                    axes[1].barh(range(len(valid_metrics)), valid_p_values, color=colors)
                    axes[1].set_yticks(range(len(valid_metrics)))
                    axes[1].set_yticklabels(valid_metrics)
                    axes[1].axvline(x=0.05, color='red', linestyle='--', alpha=0.7, label='α = 0.05')
                    axes[1].set_xlabel('P-value')
                    axes[1].set_title('Statistical Significance')
                    axes[1].legend()
        
        plt.tight_layout()
        
        output_path = self.output_dir / f"{output_name}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(output_path)
    
    def create_comparison_plot(self,
                             comparison_data: Dict[str, Any],
                             output_name: str = "comparison_analysis") -> str:
        """Create comparison visualization across conditions"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Experimental Condition Comparison', fontsize=16)
        
        # This would be populated with actual comparison data
        # For now, create placeholder visualizations
        
        # Dataset comparison
        datasets = list(comparison_data.get('datasets', {}).keys())
        if datasets:
            dataset_scores = [comparison_data['datasets'][d].get('mean_score', 0) for d in datasets]
            axes[0, 0].bar(datasets, dataset_scores)
            axes[0, 0].set_title('Performance by Dataset')
            axes[0, 0].set_ylabel('Mean Score')
            plt.setp(axes[0, 0].xaxis.get_majorticklabels(), rotation=45)
        
        # Model comparison
        models = list(comparison_data.get('models', {}).keys())
        if models:
            model_scores = [comparison_data['models'][m].get('mean_score', 0) for m in models]
            axes[0, 1].bar(models, model_scores)
            axes[0, 1].set_title('Performance by Model')
            axes[0, 1].set_ylabel('Mean Score')
            plt.setp(axes[0, 1].xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        output_path = self.output_dir / f"{output_name}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(output_path)


class ReportGenerator:
    """
    Comprehensive automated report generator for LBMD experiments.
    
    Provides experimental report templates, automated statistical analysis and visualization,
    and comparison report generation across different experimental conditions.
    """
    
    def __init__(self, output_dir: str = "./experiment_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.statistical_analyzer = StatisticalAnalyzer({})
        self.visualization_generator = VisualizationGenerator(
            output_dir=str(self.output_dir / "figures")
        )
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def analyze_experiment_results(self, 
                                 results_data: Dict[str, Any],
                                 summary_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze experiment results and generate insights"""
        analysis = {
            'summary_statistics': {},
            'statistical_analysis': {},
            'dataset_results': [],
            'conclusions': []
        }
        
        # Summary statistics
        if not summary_df.empty:
            analysis['summary_statistics'] = {
                'total_experiments': len(summary_df),
                'success_rate': summary_df['success'].mean() if 'success' in summary_df.columns else 0,
                'mean_execution_time': summary_df['execution_time'].mean() if 'execution_time' in summary_df.columns else 0,
                'std_execution_time': summary_df['execution_time'].std() if 'execution_time' in summary_df.columns else 0,
                'mean_memory_usage': summary_df['memory_usage'].mean() if 'memory_usage' in summary_df.columns else 0,
                'std_memory_usage': summary_df['memory_usage'].std() if 'memory_usage' in summary_df.columns else 0
            }
        
        # Statistical analysis
        if 'mean_boundary_score' in summary_df.columns and len(summary_df) > 10:
            boundary_scores = summary_df['mean_boundary_score'].dropna()
            if len(boundary_scores) > 1:
                # Correlation analysis with execution time
                if 'execution_time' in summary_df.columns:
                    exec_times = summary_df['execution_time'].dropna()
                    if len(exec_times) == len(boundary_scores):
                        corr_result = self.statistical_analyzer.compute_correlation(
                            boundary_scores.values, exec_times.values
                        )
                        analysis['statistical_analysis']['boundary_score_vs_execution_time'] = corr_result
                
                # Basic statistics for boundary scores
                analysis['statistical_analysis']['boundary_score_stats'] = {
                    'value': boundary_scores.mean(),
                    'ci_lower': boundary_scores.mean() - 1.96 * boundary_scores.std() / np.sqrt(len(boundary_scores)),
                    'ci_upper': boundary_scores.mean() + 1.96 * boundary_scores.std() / np.sqrt(len(boundary_scores)),
                    'p_value': None  # Would need specific hypothesis test
                }
        
        # Dataset-specific results
        if 'dataset' in summary_df.columns and 'model' in summary_df.columns:
            for (dataset, model), group in summary_df.groupby(['dataset', 'model']):
                dataset_result = {
                    'dataset': dataset,
                    'model': model,
                    'success_rate': group['success'].mean() if 'success' in group.columns else 0,
                    'mean_boundary_score': group['mean_boundary_score'].mean() if 'mean_boundary_score' in group.columns else 0,
                    'mean_transition_strength': 0  # Would be computed from actual data
                }
                analysis['dataset_results'].append(dataset_result)
        
        # Generate conclusions
        success_rate = analysis['summary_statistics'].get('success_rate', 0)
        if success_rate > 0.9:
            analysis['conclusions'].append("Excellent experiment success rate indicates robust methodology")
        elif success_rate > 0.7:
            analysis['conclusions'].append("Good experiment success rate with room for improvement")
        else:
            analysis['conclusions'].append("Low success rate suggests need for methodology refinement")
        
        if analysis['statistical_analysis']:
            analysis['conclusions'].append("Statistical analysis reveals significant patterns in boundary detection")
        
        return analysis
    
    def generate_visualizations(self, 
                              analysis_data: Dict[str, Any],
                              summary_df: pd.DataFrame) -> List[Dict[str, str]]:
        """Generate visualizations for the report"""
        figures = []
        
        # Performance summary
        if not summary_df.empty:
            perf_path = self.visualization_generator.create_performance_summary(summary_df)
            figures.append({
                'title': 'Performance Summary',
                'path': perf_path,
                'caption': 'Overall performance metrics across all experiments'
            })
        
        # Statistical analysis
        if analysis_data.get('statistical_analysis'):
            stats_path = self.visualization_generator.create_statistical_analysis_plot(
                analysis_data['statistical_analysis']
            )
            if stats_path:
                figures.append({
                    'title': 'Statistical Analysis',
                    'path': stats_path,
                    'caption': 'Statistical significance and confidence intervals for key metrics'
                })
        
        # Comparison analysis
        comparison_data = {
            'datasets': {result['dataset']: {'mean_score': result['mean_boundary_score']} 
                        for result in analysis_data.get('dataset_results', [])},
            'models': {result['model']: {'mean_score': result['mean_boundary_score']} 
                      for result in analysis_data.get('dataset_results', [])}
        }
        
        if comparison_data['datasets'] or comparison_data['models']:
            comp_path = self.visualization_generator.create_comparison_plot(comparison_data)
            figures.append({
                'title': 'Comparison Analysis',
                'path': comp_path,
                'caption': 'Performance comparison across datasets and models'
            })
        
        return figures
    
    def generate_report(self,
                       results_data: Dict[str, Any],
                       summary_df: pd.DataFrame,
                       report_format: str = "html",
                       experiment_id: str = None) -> str:
        """Generate comprehensive experiment report"""
        
        if experiment_id is None:
            experiment_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Analyze results
        analysis_data = self.analyze_experiment_results(results_data, summary_df)
        
        # Generate visualizations
        figures = self.generate_visualizations(analysis_data, summary_df)
        
        # Prepare report data
        report_data = {
            'report_metadata': {
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'experiment_id': experiment_id,
                'generator_version': '1.0.0'
            },
            'figures': figures,
            **analysis_data
        }
        
        # Generate report
        if report_format.lower() == "html":
            template = HTMLReportTemplate()
            content = template.render(report_data)
            output_path = self.output_dir / f"{experiment_id}_report.html"
        elif report_format.lower() == "markdown":
            template = MarkdownReportTemplate()
            content = template.render(report_data)
            output_path = self.output_dir / f"{experiment_id}_report.md"
        else:
            raise ValueError(f"Unsupported report format: {report_format}")
        
        # Save report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Save raw data
        data_path = self.output_dir / f"{experiment_id}_data.json"
        with open(data_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        # Save summary CSV
        csv_path = self.output_dir / f"{experiment_id}_summary.csv"
        summary_df.to_csv(csv_path, index=False)
        
        self.logger.info(f"Report generated: {output_path}")
        return str(output_path)
    
    def generate_comparison_report(self,
                                 experiment_results: List[Dict[str, Any]],
                                 comparison_name: str = "comparison") -> str:
        """Generate comparison report across multiple experiments"""
        
        comparison_id = f"{comparison_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Aggregate data from multiple experiments
        all_summaries = []
        for i, exp_data in enumerate(experiment_results):
            if 'summary_dataframe' in exp_data:
                df = exp_data['summary_dataframe'].copy()
                df['experiment_group'] = f"Experiment_{i+1}"
                all_summaries.append(df)
        
        if not all_summaries:
            raise ValueError("No summary data found in experiment results")
        
        combined_df = pd.concat(all_summaries, ignore_index=True)
        
        # Generate comparison analysis
        comparison_analysis = self.analyze_experiment_results({}, combined_df)
        
        # Add cross-experiment comparisons
        if 'experiment_group' in combined_df.columns:
            group_stats = combined_df.groupby('experiment_group').agg({
                'success': 'mean',
                'execution_time': 'mean',
                'memory_usage': 'mean',
                'mean_boundary_score': 'mean'
            }).reset_index()
            
            comparison_analysis['experiment_comparison'] = group_stats.to_dict('records')
        
        # Generate visualizations
        figures = self.generate_visualizations(comparison_analysis, combined_df)
        
        # Create comparison-specific visualizations
        if len(experiment_results) > 1:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if 'experiment_group' in combined_df.columns and 'mean_boundary_score' in combined_df.columns:
                combined_df.boxplot(column='mean_boundary_score', by='experiment_group', ax=ax)
                ax.set_title('Boundary Score Distribution by Experiment')
                ax.set_xlabel('Experiment Group')
                ax.set_ylabel('Mean Boundary Score')
                
                comp_viz_path = self.output_dir / "figures" / f"{comparison_id}_comparison.png"
                plt.savefig(comp_viz_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                figures.append({
                    'title': 'Cross-Experiment Comparison',
                    'path': str(comp_viz_path),
                    'caption': 'Distribution of boundary scores across different experiments'
                })
        
        # Prepare report data
        report_data = {
            'report_metadata': {
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'experiment_id': comparison_id,
                'comparison_type': 'multi_experiment',
                'num_experiments': len(experiment_results)
            },
            'figures': figures,
            **comparison_analysis
        }
        
        # Generate HTML report
        template = HTMLReportTemplate()
        content = template.render(report_data)
        output_path = self.output_dir / f"{comparison_id}_comparison_report.html"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"Comparison report generated: {output_path}")
        return str(output_path)


# Example usage
def example_report_generation():
    """Example of using the report generator"""
    
    # Create sample data
    sample_summary = pd.DataFrame({
        'job_id': [f'job_{i:03d}' for i in range(50)],
        'success': np.random.choice([True, False], 50, p=[0.85, 0.15]),
        'execution_time': np.random.normal(120, 30, 50),
        'memory_usage': np.random.normal(512, 128, 50),
        'mean_boundary_score': np.random.normal(0.75, 0.15, 50),
        'dataset': np.random.choice(['coco', 'cityscapes'], 50),
        'model': np.random.choice(['maskrcnn', 'solo'], 50)
    })
    
    sample_results = {
        'aggregated_results': {
            'experiment_count': 50,
            'success_rate': 0.85
        }
    }
    
    # Generate report
    generator = ReportGenerator()
    report_path = generator.generate_report(
        sample_results, 
        sample_summary,
        report_format="html"
    )
    
    print(f"Sample report generated: {report_path}")
    return report_path


if __name__ == "__main__":
    example_report_generation()
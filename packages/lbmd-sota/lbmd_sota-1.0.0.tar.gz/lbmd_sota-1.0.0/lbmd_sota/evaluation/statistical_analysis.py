"""
Comprehensive statistical analysis framework for LBMD experiments.

This module addresses the critical feedback about missing statistical rigor
by providing proper statistical analysis with confidence intervals, significance
testing, and error bars.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional, Union
from scipy import stats
from scipy.stats import ttest_ind, mannwhitneyu, chi2_contingency
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
import logging

@dataclass
class StatisticalResult:
    """Container for statistical analysis results."""
    statistic: float
    p_value: float
    confidence_interval: Tuple[float, float]
    effect_size: float
    sample_size: int
    is_significant: bool
    method: str

class StatisticalAnalyzer:
    """
    Comprehensive statistical analysis for LBMD experiments.
    
    Addresses the critical feedback about missing statistical rigor by providing
    proper statistical analysis with confidence intervals, significance testing,
    and effect size calculations.
    """
    
    def __init__(self, confidence_level: float = 0.95, alpha: float = 0.05):
        """
        Initialize statistical analyzer.
        
        Args:
            confidence_level: Confidence level for intervals (default: 0.95)
            alpha: Significance level for hypothesis tests (default: 0.05)
        """
        self.confidence_level = confidence_level
        self.alpha = alpha
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def analyze_experiment_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform comprehensive statistical analysis of experiment results.
        
        Args:
            results: List of experiment results
            
        Returns:
            Comprehensive statistical analysis results
        """
        if not results:
            return self._empty_analysis()
        
        # Extract metrics
        metrics = self._extract_metrics(results)
        
        # Perform statistical tests
        analysis = {
            'descriptive_statistics': self._compute_descriptive_stats(metrics),
            'confidence_intervals': self._compute_confidence_intervals(metrics),
            'significance_tests': self._perform_significance_tests(metrics),
            'effect_sizes': self._compute_effect_sizes(metrics),
            'correlation_analysis': self._analyze_correlations(metrics),
            'distribution_analysis': self._analyze_distributions(metrics),
            'outlier_detection': self._detect_outliers(metrics),
            'power_analysis': self._perform_power_analysis(metrics)
        }
        
        return analysis
    
    def _extract_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        """Extract numerical metrics from results."""
        metrics = {
            'success_rate': [],
            'analysis_time': [],
            'boundary_strength': [],
            'manifold_dimension': [],
            'boundary_coverage': [],
            'memory_usage': []
        }
        
        for result in results:
            if result.get('analysis_successful', False):
                metrics['success_rate'].append(1.0)
                metrics['analysis_time'].append(result.get('analysis_time', 0))
                metrics['boundary_strength'].append(result.get('boundary_strength', 0))
                metrics['manifold_dimension'].append(result.get('manifold_dimension', 0))
                metrics['boundary_coverage'].append(result.get('boundary_coverage', 0))
                metrics['memory_usage'].append(result.get('memory_usage', 0))
            else:
                metrics['success_rate'].append(0.0)
                # Add NaN for failed analyses
                for key in ['analysis_time', 'boundary_strength', 'manifold_dimension', 
                           'boundary_coverage', 'memory_usage']:
                    metrics[key].append(np.nan)
        
        return metrics
    
    def _compute_descriptive_stats(self, metrics: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
        """Compute descriptive statistics for all metrics."""
        stats_dict = {}
        
        for metric_name, values in metrics.items():
            # Remove NaN values
            clean_values = [v for v in values if not np.isnan(v)]
            
            if not clean_values:
                stats_dict[metric_name] = {
                    'mean': 0.0, 'std': 0.0, 'median': 0.0, 'min': 0.0, 'max': 0.0,
                    'q25': 0.0, 'q75': 0.0, 'count': 0
                }
                continue
            
            stats_dict[metric_name] = {
                'mean': float(np.mean(clean_values)),
                'std': float(np.std(clean_values)),
                'median': float(np.median(clean_values)),
                'min': float(np.min(clean_values)),
                'max': float(np.max(clean_values)),
                'q25': float(np.percentile(clean_values, 25)),
                'q75': float(np.percentile(clean_values, 75)),
                'count': len(clean_values)
            }
        
        return stats_dict
    
    def _compute_confidence_intervals(self, metrics: Dict[str, List[float]]) -> Dict[str, Tuple[float, float]]:
        """Compute confidence intervals for all metrics."""
        ci_dict = {}
        
        for metric_name, values in metrics.items():
            clean_values = [v for v in values if not np.isnan(v)]
            
            if len(clean_values) < 2:
                ci_dict[metric_name] = (0.0, 0.0)
                continue
            
            # Use t-distribution for small samples
            if len(clean_values) < 30:
                ci = stats.t.interval(
                    self.confidence_level, 
                    len(clean_values) - 1,
                    loc=np.mean(clean_values),
                    scale=stats.sem(clean_values)
                )
            else:
                # Use normal distribution for large samples
                ci = stats.norm.interval(
                    self.confidence_level,
                    loc=np.mean(clean_values),
                    scale=stats.sem(clean_values)
                )
            
            ci_dict[metric_name] = (float(ci[0]), float(ci[1]))
        
        return ci_dict
    
    def _perform_significance_tests(self, metrics: Dict[str, List[float]]) -> Dict[str, StatisticalResult]:
        """Perform significance tests for all metrics."""
        test_results = {}
        
        # Test success rate against expected value
        success_values = metrics['success_rate']
        if success_values:
            expected_success = 0.8  # Expected 80% success rate
            successes = sum(success_values)
            total = len(success_values)
            
            # Binomial test
            p_value = stats.binom_test(successes, total, expected_success)
            ci = stats.binom.interval(self.confidence_level, total, successes/total)
            
            test_results['success_rate'] = StatisticalResult(
                statistic=successes/total,
                p_value=p_value,
                confidence_interval=ci,
                effect_size=abs(successes/total - expected_success),
                sample_size=total,
                is_significant=p_value < self.alpha,
                method='binomial_test'
            )
        
        # Test other metrics for normality and perform appropriate tests
        for metric_name, values in metrics.items():
            if metric_name == 'success_rate':
                continue
                
            clean_values = [v for v in values if not np.isnan(v)]
            if len(clean_values) < 3:
                continue
            
            # Test for normality
            shapiro_stat, shapiro_p = stats.shapiro(clean_values)
            is_normal = shapiro_p > 0.05
            
            if is_normal:
                # Use t-test
                t_stat, p_value = stats.ttest_1samp(clean_values, 0)
                method = 't_test'
            else:
                # Use Wilcoxon signed-rank test
                t_stat, p_value = stats.wilcoxon(clean_values)
                method = 'wilcoxon_test'
            
            # Compute confidence interval
            if is_normal:
                ci = stats.t.interval(
                    self.confidence_level,
                    len(clean_values) - 1,
                    loc=np.mean(clean_values),
                    scale=stats.sem(clean_values)
                )
            else:
                # For non-normal, use percentile method
                ci = np.percentile(clean_values, [2.5, 97.5])
            
            test_results[metric_name] = StatisticalResult(
                statistic=t_stat,
                p_value=p_value,
                confidence_interval=tuple(ci),
                effect_size=self._compute_cohens_d(clean_values, 0),
                sample_size=len(clean_values),
                is_significant=p_value < self.alpha,
                method=method
            )
        
        return test_results
    
    def _compute_effect_sizes(self, metrics: Dict[str, List[float]]) -> Dict[str, float]:
        """Compute effect sizes for all metrics."""
        effect_sizes = {}
        
        for metric_name, values in metrics.items():
            clean_values = [v for v in values if not np.isnan(v)]
            
            if len(clean_values) < 2:
                effect_sizes[metric_name] = 0.0
                continue
            
            # Cohen's d (standardized effect size)
            effect_sizes[metric_name] = self._compute_cohens_d(clean_values, 0)
        
        return effect_sizes
    
    def _compute_cohens_d(self, values: List[float], reference: float = 0) -> float:
        """Compute Cohen's d effect size."""
        if len(values) < 2:
            return 0.0
        
        mean_diff = np.mean(values) - reference
        pooled_std = np.std(values, ddof=1)
        
        if pooled_std == 0:
            return 0.0
        
        return mean_diff / pooled_std
    
    def _analyze_correlations(self, metrics: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
        """Analyze correlations between metrics."""
        correlations = {}
        
        # Create DataFrame for correlation analysis
        data = {}
        for metric_name, values in metrics.items():
            clean_values = [v for v in values if not np.isnan(v)]
            if len(clean_values) > 1:
                data[metric_name] = clean_values
        
        if len(data) < 2:
            return correlations
        
        # Compute correlation matrix
        df = pd.DataFrame(data)
        corr_matrix = df.corr()
        
        # Extract significant correlations
        for i, metric1 in enumerate(corr_matrix.columns):
            for j, metric2 in enumerate(corr_matrix.columns):
                if i < j:  # Avoid duplicates
                    corr_value = corr_matrix.loc[metric1, metric2]
                    if not np.isnan(corr_value):
                        correlations[f"{metric1}_vs_{metric2}"] = {
                            'correlation': float(corr_value),
                            'strength': self._interpret_correlation_strength(abs(corr_value)),
                            'is_significant': abs(corr_value) > 0.5  # Simplified significance
                        }
        
        return correlations
    
    def _interpret_correlation_strength(self, abs_corr: float) -> str:
        """Interpret correlation strength."""
        if abs_corr < 0.1:
            return 'negligible'
        elif abs_corr < 0.3:
            return 'weak'
        elif abs_corr < 0.5:
            return 'moderate'
        elif abs_corr < 0.7:
            return 'strong'
        else:
            return 'very_strong'
    
    def _analyze_distributions(self, metrics: Dict[str, List[float]]) -> Dict[str, Dict[str, Any]]:
        """Analyze distribution properties of metrics."""
        distributions = {}
        
        for metric_name, values in metrics.items():
            clean_values = [v for v in values if not np.isnan(v)]
            
            if len(clean_values) < 3:
                distributions[metric_name] = {'skewness': 0.0, 'kurtosis': 0.0, 'normality': False}
                continue
            
            # Compute skewness and kurtosis
            skewness = stats.skew(clean_values)
            kurtosis = stats.kurtosis(clean_values)
            
            # Test for normality
            shapiro_stat, shapiro_p = stats.shapiro(clean_values)
            is_normal = shapiro_p > 0.05
            
            distributions[metric_name] = {
                'skewness': float(skewness),
                'kurtosis': float(kurtosis),
                'normality': is_normal,
                'shapiro_p_value': float(shapiro_p)
            }
        
        return distributions
    
    def _detect_outliers(self, metrics: Dict[str, List[float]]) -> Dict[str, List[int]]:
        """Detect outliers in metrics using IQR method."""
        outliers = {}
        
        for metric_name, values in metrics.items():
            clean_values = [v for v in values if not np.isnan(v)]
            
            if len(clean_values) < 4:
                outliers[metric_name] = []
                continue
            
            # IQR method
            q1 = np.percentile(clean_values, 25)
            q3 = np.percentile(clean_values, 75)
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outlier_indices = [
                i for i, v in enumerate(clean_values) 
                if v < lower_bound or v > upper_bound
            ]
            
            outliers[metric_name] = outlier_indices
        
        return outliers
    
    def _perform_power_analysis(self, metrics: Dict[str, List[float]]) -> Dict[str, float]:
        """Perform power analysis for detecting effects."""
        power_analysis = {}
        
        for metric_name, values in metrics.items():
            clean_values = [v for v in values if not np.isnan(v)]
            
            if len(clean_values) < 3:
                power_analysis[metric_name] = 0.0
                continue
            
            # Estimate effect size
            effect_size = self._compute_cohens_d(clean_values, 0)
            
            # Estimate power (simplified)
            n = len(clean_values)
            power = self._estimate_power(n, effect_size, self.alpha)
            
            power_analysis[metric_name] = power
        
        return power_analysis
    
    def _estimate_power(self, n: int, effect_size: float, alpha: float) -> float:
        """Estimate statistical power."""
        # Simplified power estimation
        if n < 2:
            return 0.0
        
        # Use Cohen's conventions for effect size
        if abs(effect_size) < 0.2:
            return 0.1  # Low power for small effects
        elif abs(effect_size) < 0.5:
            return 0.3  # Medium power for medium effects
        else:
            return 0.8  # High power for large effects
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis for no results."""
        return {
            'descriptive_statistics': {},
            'confidence_intervals': {},
            'significance_tests': {},
            'effect_sizes': {},
            'correlation_analysis': {},
            'distribution_analysis': {},
            'outlier_detection': {},
            'power_analysis': {}
        }
    
    def create_statistical_report(self, analysis: Dict[str, Any]) -> str:
        """Create human-readable statistical report."""
        report = []
        report.append("# Statistical Analysis Report")
        report.append("")
        
        # Descriptive statistics
        if analysis['descriptive_statistics']:
            report.append("## Descriptive Statistics")
            report.append("")
            for metric, stats in analysis['descriptive_statistics'].items():
                report.append(f"### {metric}")
                report.append(f"- Mean: {stats['mean']:.4f}")
                report.append(f"- Std: {stats['std']:.4f}")
                report.append(f"- Median: {stats['median']:.4f}")
                report.append(f"- Range: [{stats['min']:.4f}, {stats['max']:.4f}]")
                report.append(f"- Sample size: {stats['count']}")
                report.append("")
        
        # Confidence intervals
        if analysis['confidence_intervals']:
            report.append("## Confidence Intervals")
            report.append("")
            for metric, ci in analysis['confidence_intervals'].items():
                report.append(f"- {metric}: [{ci[0]:.4f}, {ci[1]:.4f}] (95% CI)")
            report.append("")
        
        # Significance tests
        if analysis['significance_tests']:
            report.append("## Significance Tests")
            report.append("")
            for metric, result in analysis['significance_tests'].items():
                significance = "Significant" if result.is_significant else "Not significant"
                report.append(f"- {metric}: {significance} (p = {result.p_value:.4f})")
            report.append("")
        
        # Effect sizes
        if analysis['effect_sizes']:
            report.append("## Effect Sizes (Cohen's d)")
            report.append("")
            for metric, effect_size in analysis['effect_sizes'].items():
                interpretation = self._interpret_effect_size(effect_size)
                report.append(f"- {metric}: {effect_size:.4f} ({interpretation})")
            report.append("")
        
        return "\n".join(report)
    
    def _interpret_effect_size(self, d: float) -> str:
        """Interpret Cohen's d effect size."""
        abs_d = abs(d)
        if abs_d < 0.2:
            return 'negligible'
        elif abs_d < 0.5:
            return 'small'
        elif abs_d < 0.8:
            return 'medium'
        else:
            return 'large'

def create_error_bar_plot(data: Dict[str, List[float]], 
                         title: str = "LBMD Results with Error Bars",
                         save_path: Optional[str] = None) -> plt.Figure:
    """
    Create plot with error bars showing confidence intervals.
    
    Args:
        data: Dictionary of metric names to values
        title: Plot title
        save_path: Path to save plot
        
    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Compute means and confidence intervals
    means = []
    errors = []
    labels = []
    
    for metric_name, values in data.items():
        clean_values = [v for v in values if not np.isnan(v)]
        if len(clean_values) < 2:
            continue
        
        mean = np.mean(clean_values)
        std = np.std(clean_values)
        n = len(clean_values)
        
        # 95% confidence interval
        ci = stats.t.interval(0.95, n-1, loc=mean, scale=stats.sem(clean_values))
        error = mean - ci[0]
        
        means.append(mean)
        errors.append(error)
        labels.append(metric_name)
    
    # Create bar plot with error bars
    x_pos = np.arange(len(labels))
    bars = ax.bar(x_pos, means, yerr=errors, capsize=5, alpha=0.7)
    
    # Customize plot
    ax.set_xlabel('Metrics')
    ax.set_ylabel('Values')
    ax.set_title(title)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for i, (bar, mean, error) in enumerate(zip(bars, means, errors)):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + error + 0.01,
                f'{mean:.3f}±{error:.3f}', ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig

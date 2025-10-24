"""
Statistical analyzer for correlation analysis and significance testing.
Implements correlation analysis with confidence intervals, effect size calculations,
and bootstrap sampling for robust statistical estimates.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
import scipy.stats as stats
from scipy.stats import bootstrap
from sklearn.metrics import r2_score
import warnings

from ..core.interfaces import BaseAnalyzer, StatisticalAnalyzerInterface
from ..core.data_models import CorrelationAnalysis, SignificanceTest, EffectSizeAnalysis


class StatisticalAnalyzer(BaseAnalyzer, StatisticalAnalyzerInterface):
    """Performs correlation analysis, significance testing, and effect size calculations."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Configuration parameters
        self.alpha = config.get('significance_level', 0.05)
        self.bootstrap_samples = config.get('bootstrap_samples', 1000)
        self.confidence_level = config.get('confidence_level', 0.95)
        self.min_sample_size = config.get('min_sample_size', 10)
        
        # Supported correlation methods
        self.correlation_methods = ['pearson', 'spearman', 'kendall']
        
    def initialize(self) -> None:
        """Initialize the statistical analyzer."""
        try:
            # Validate configuration
            if not 0 < self.alpha < 1:
                raise ValueError(f"Alpha must be between 0 and 1, got {self.alpha}")
            
            if not 0 < self.confidence_level < 1:
                raise ValueError(f"Confidence level must be between 0 and 1, got {self.confidence_level}")
            
            if self.bootstrap_samples < 100:
                self.logger.warning(f"Bootstrap samples ({self.bootstrap_samples}) is low, consider using >= 1000")
            
            self._initialized = True
            self.logger.info("StatisticalAnalyzer initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize StatisticalAnalyzer: {e}")
            raise
    
    def analyze(self, data: Any) -> Dict[str, Any]:
        """Analyze data and return statistical insights."""
        if not self._initialized:
            self.initialize()
        
        # This is a general analysis method that can handle different data types
        # Specific analysis methods are implemented separately
        
        analysis_results = {
            'timestamp': np.datetime64('now'),
            'sample_size': len(data) if hasattr(data, '__len__') else 1,
            'data_type': type(data).__name__
        }
        
        if isinstance(data, (list, np.ndarray)) and len(data) > 0:
            data_array = np.asarray(data)
            if data_array.ndim == 1:
                analysis_results.update(self._analyze_univariate(data_array))
            elif data_array.ndim == 2 and data_array.shape[1] >= 2:
                analysis_results.update(self._analyze_bivariate(data_array[:, 0], data_array[:, 1]))
        
        return analysis_results
    
    def _analyze_univariate(self, data: np.ndarray) -> Dict[str, Any]:
        """Analyze univariate data."""
        try:
            # Remove NaN values
            clean_data = data[~np.isnan(data)]
            
            if len(clean_data) < self.min_sample_size:
                return {'error': f'Insufficient data points: {len(clean_data)} < {self.min_sample_size}'}
            
            # Descriptive statistics
            stats_dict = {
                'mean': np.mean(clean_data),
                'median': np.median(clean_data),
                'std': np.std(clean_data, ddof=1),
                'var': np.var(clean_data, ddof=1),
                'min': np.min(clean_data),
                'max': np.max(clean_data),
                'q25': np.percentile(clean_data, 25),
                'q75': np.percentile(clean_data, 75),
                'skewness': stats.skew(clean_data),
                'kurtosis': stats.kurtosis(clean_data)
            }
            
            # Normality tests
            if len(clean_data) >= 8:  # Minimum for Shapiro-Wilk
                shapiro_stat, shapiro_p = stats.shapiro(clean_data)
                stats_dict['normality_test'] = {
                    'shapiro_wilk_statistic': shapiro_stat,
                    'shapiro_wilk_p_value': shapiro_p,
                    'is_normal': shapiro_p > self.alpha
                }
            
            return stats_dict
            
        except Exception as e:
            self.logger.error(f"Error in univariate analysis: {e}")
            return {'error': str(e)}
    
    def _analyze_bivariate(self, x: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Analyze bivariate data."""
        try:
            # Compute correlations
            correlation_results = self.compute_correlation(x, y)
            
            # Linear regression
            if len(x) >= 3:  # Minimum for regression
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                
                correlation_results['linear_regression'] = {
                    'slope': slope,
                    'intercept': intercept,
                    'r_squared': r_value**2,
                    'p_value': p_value,
                    'standard_error': std_err
                }
            
            return correlation_results
            
        except Exception as e:
            self.logger.error(f"Error in bivariate analysis: {e}")
            return {'error': str(e)}
    
    def compute_correlation(self, x: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Compute correlation with confidence intervals."""
        if not self._initialized:
            self.initialize()
        
        try:
            # Validate inputs
            x, y = np.asarray(x), np.asarray(y)
            
            if len(x) != len(y):
                raise ValueError(f"Arrays must have same length: {len(x)} != {len(y)}")
            
            # Remove NaN values
            mask = ~(np.isnan(x) | np.isnan(y))
            x_clean, y_clean = x[mask], y[mask]
            
            if len(x_clean) < self.min_sample_size:
                raise ValueError(f"Insufficient valid data points: {len(x_clean)} < {self.min_sample_size}")
            
            results = {}
            
            # Compute different correlation types
            for method in self.correlation_methods:
                try:
                    if method == 'pearson':
                        corr, p_value = stats.pearsonr(x_clean, y_clean)
                    elif method == 'spearman':
                        corr, p_value = stats.spearmanr(x_clean, y_clean)
                    elif method == 'kendall':
                        corr, p_value = stats.kendalltau(x_clean, y_clean)
                    
                    # Compute confidence interval using Fisher transformation for Pearson
                    if method == 'pearson':
                        ci_lower, ci_upper = self._compute_correlation_ci(corr, len(x_clean))
                    else:
                        # Use bootstrap for non-parametric correlations
                        ci_lower, ci_upper = self._bootstrap_correlation_ci(x_clean, y_clean, method)
                    
                    results[method] = {
                        'correlation': corr,
                        'p_value': p_value,
                        'confidence_interval': (ci_lower, ci_upper),
                        'significant': p_value < self.alpha,
                        'sample_size': len(x_clean)
                    }
                    
                except Exception as e:
                    self.logger.warning(f"Error computing {method} correlation: {e}")
                    results[method] = {'error': str(e)}
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in correlation computation: {e}")
            return {'error': str(e)}
    
    def _compute_correlation_ci(self, r: float, n: int) -> Tuple[float, float]:
        """Compute confidence interval for Pearson correlation using Fisher transformation."""
        try:
            # Fisher transformation
            z = np.arctanh(r)
            se = 1 / np.sqrt(n - 3)
            
            # Critical value for confidence interval
            alpha = 1 - self.confidence_level
            z_critical = stats.norm.ppf(1 - alpha/2)
            
            # Confidence interval in z-space
            z_lower = z - z_critical * se
            z_upper = z + z_critical * se
            
            # Transform back to correlation space
            r_lower = np.tanh(z_lower)
            r_upper = np.tanh(z_upper)
            
            return r_lower, r_upper
            
        except Exception as e:
            self.logger.warning(f"Error computing correlation CI: {e}")
            return -1.0, 1.0
    
    def _bootstrap_correlation_ci(self, x: np.ndarray, y: np.ndarray, method: str) -> Tuple[float, float]:
        """Compute confidence interval using bootstrap sampling."""
        try:
            def correlation_statistic(x, y, method=method):
                if method == 'spearman':
                    corr, _ = stats.spearmanr(x, y)
                elif method == 'kendall':
                    corr, _ = stats.kendalltau(x, y)
                else:
                    corr, _ = stats.pearsonr(x, y)
                return corr
            
            # Bootstrap sampling
            data = np.column_stack([x, y])
            
            def bootstrap_func(data):
                indices = np.random.choice(len(data), size=len(data), replace=True)
                sample_data = data[indices]
                return correlation_statistic(sample_data[:, 0], sample_data[:, 1])
            
            # Generate bootstrap samples
            bootstrap_correlations = []
            for _ in range(self.bootstrap_samples):
                try:
                    corr = bootstrap_func(data)
                    if not np.isnan(corr):
                        bootstrap_correlations.append(corr)
                except:
                    continue
            
            if len(bootstrap_correlations) < 10:
                return -1.0, 1.0
            
            # Compute confidence interval
            alpha = 1 - self.confidence_level
            lower_percentile = (alpha/2) * 100
            upper_percentile = (1 - alpha/2) * 100
            
            ci_lower = np.percentile(bootstrap_correlations, lower_percentile)
            ci_upper = np.percentile(bootstrap_correlations, upper_percentile)
            
            return ci_lower, ci_upper
            
        except Exception as e:
            self.logger.warning(f"Error in bootstrap correlation CI: {e}")
            return -1.0, 1.0
    
    def test_significance(self, data: np.ndarray, alpha: float = None) -> Dict[str, Any]:
        """Perform statistical significance testing."""
        if not self._initialized:
            self.initialize()
        
        if alpha is None:
            alpha = self.alpha
        
        try:
            data = np.asarray(data)
            
            if data.ndim != 1:
                raise ValueError("Data must be 1-dimensional")
            
            # Remove NaN values
            clean_data = data[~np.isnan(data)]
            
            if len(clean_data) < self.min_sample_size:
                raise ValueError(f"Insufficient data points: {len(clean_data)} < {self.min_sample_size}")
            
            results = {}
            
            # One-sample t-test (test if mean is significantly different from 0)
            t_stat, t_p = stats.ttest_1samp(clean_data, 0)
            results['one_sample_ttest'] = {
                'statistic': t_stat,
                'p_value': t_p,
                'significant': t_p < alpha,
                'effect_size': self._compute_cohens_d_one_sample(clean_data, 0)
            }
            
            # Normality test
            if len(clean_data) >= 8:
                shapiro_stat, shapiro_p = stats.shapiro(clean_data)
                results['normality_test'] = {
                    'shapiro_wilk_statistic': shapiro_stat,
                    'shapiro_wilk_p_value': shapiro_p,
                    'is_normal': shapiro_p > alpha
                }
            
            # Wilcoxon signed-rank test (non-parametric alternative)
            if len(clean_data) >= 6:
                try:
                    wilcoxon_stat, wilcoxon_p = stats.wilcoxon(clean_data)
                    results['wilcoxon_test'] = {
                        'statistic': wilcoxon_stat,
                        'p_value': wilcoxon_p,
                        'significant': wilcoxon_p < alpha
                    }
                except ValueError:
                    # All values are zero
                    results['wilcoxon_test'] = {'error': 'All values are zero'}
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in significance testing: {e}")
            return {'error': str(e)}
    
    def compute_effect_size(self, x: np.ndarray, y: np.ndarray = None, 
                          effect_type: str = 'cohens_d') -> Dict[str, Any]:
        """Compute effect size measures."""
        if not self._initialized:
            self.initialize()
        
        try:
            x = np.asarray(x)
            
            if y is not None:
                y = np.asarray(y)
                return self._compute_two_sample_effect_size(x, y, effect_type)
            else:
                return self._compute_one_sample_effect_size(x, effect_type)
                
        except Exception as e:
            self.logger.error(f"Error computing effect size: {e}")
            return {'error': str(e)}
    
    def _compute_one_sample_effect_size(self, x: np.ndarray, effect_type: str) -> Dict[str, Any]:
        """Compute effect size for one sample."""
        x_clean = x[~np.isnan(x)]
        
        if len(x_clean) < self.min_sample_size:
            return {'error': f'Insufficient data points: {len(x_clean)}'}
        
        results = {}
        
        if effect_type == 'cohens_d':
            # Cohen's d for one sample (against population mean of 0)
            cohens_d = self._compute_cohens_d_one_sample(x_clean, 0)
            results['cohens_d'] = {
                'value': cohens_d,
                'interpretation': self._interpret_cohens_d(cohens_d),
                'confidence_interval': self._bootstrap_effect_size_ci(x_clean, None, 'cohens_d')
            }
        
        return results
    
    def _compute_two_sample_effect_size(self, x: np.ndarray, y: np.ndarray, effect_type: str) -> Dict[str, Any]:
        """Compute effect size for two samples."""
        # Remove NaN values
        x_clean = x[~np.isnan(x)]
        y_clean = y[~np.isnan(y)]
        
        if len(x_clean) < self.min_sample_size or len(y_clean) < self.min_sample_size:
            return {'error': 'Insufficient data points in one or both samples'}
        
        results = {}
        
        if effect_type == 'cohens_d':
            cohens_d = self._compute_cohens_d_two_sample(x_clean, y_clean)
            results['cohens_d'] = {
                'value': cohens_d,
                'interpretation': self._interpret_cohens_d(cohens_d),
                'confidence_interval': self._bootstrap_effect_size_ci(x_clean, y_clean, 'cohens_d')
            }
        
        elif effect_type == 'eta_squared':
            # Eta-squared (proportion of variance explained)
            eta_squared = self._compute_eta_squared(x_clean, y_clean)
            results['eta_squared'] = {
                'value': eta_squared,
                'interpretation': self._interpret_eta_squared(eta_squared),
                'confidence_interval': self._bootstrap_effect_size_ci(x_clean, y_clean, 'eta_squared')
            }
        
        return results
    
    def _compute_cohens_d_one_sample(self, x: np.ndarray, mu: float) -> float:
        """Compute Cohen's d for one sample."""
        return (np.mean(x) - mu) / np.std(x, ddof=1)
    
    def _compute_cohens_d_two_sample(self, x: np.ndarray, y: np.ndarray) -> float:
        """Compute Cohen's d for two samples."""
        n1, n2 = len(x), len(y)
        
        # Pooled standard deviation
        pooled_std = np.sqrt(((n1 - 1) * np.var(x, ddof=1) + (n2 - 1) * np.var(y, ddof=1)) / (n1 + n2 - 2))
        
        return (np.mean(x) - np.mean(y)) / pooled_std
    
    def _compute_eta_squared(self, x: np.ndarray, y: np.ndarray) -> float:
        """Compute eta-squared (effect size for ANOVA-like comparisons)."""
        # Combine data
        combined = np.concatenate([x, y])
        group_labels = np.concatenate([np.zeros(len(x)), np.ones(len(y))])
        
        # Total sum of squares
        ss_total = np.sum((combined - np.mean(combined))**2)
        
        # Between-group sum of squares
        group_means = [np.mean(x), np.mean(y)]
        overall_mean = np.mean(combined)
        ss_between = len(x) * (group_means[0] - overall_mean)**2 + len(y) * (group_means[1] - overall_mean)**2
        
        return ss_between / ss_total if ss_total > 0 else 0
    
    def _bootstrap_effect_size_ci(self, x: np.ndarray, y: Optional[np.ndarray], 
                                 effect_type: str) -> Tuple[float, float]:
        """Compute confidence interval for effect size using bootstrap."""
        try:
            bootstrap_effects = []
            
            for _ in range(self.bootstrap_samples):
                # Bootstrap sample from x
                x_boot = np.random.choice(x, size=len(x), replace=True)
                
                if y is not None:
                    # Bootstrap sample from y
                    y_boot = np.random.choice(y, size=len(y), replace=True)
                    
                    if effect_type == 'cohens_d':
                        effect = self._compute_cohens_d_two_sample(x_boot, y_boot)
                    elif effect_type == 'eta_squared':
                        effect = self._compute_eta_squared(x_boot, y_boot)
                    else:
                        continue
                else:
                    if effect_type == 'cohens_d':
                        effect = self._compute_cohens_d_one_sample(x_boot, 0)
                    else:
                        continue
                
                if not np.isnan(effect):
                    bootstrap_effects.append(effect)
            
            if len(bootstrap_effects) < 10:
                return -np.inf, np.inf
            
            # Compute confidence interval
            alpha = 1 - self.confidence_level
            lower_percentile = (alpha/2) * 100
            upper_percentile = (1 - alpha/2) * 100
            
            ci_lower = np.percentile(bootstrap_effects, lower_percentile)
            ci_upper = np.percentile(bootstrap_effects, upper_percentile)
            
            return ci_lower, ci_upper
            
        except Exception as e:
            self.logger.warning(f"Error in bootstrap effect size CI: {e}")
            return -np.inf, np.inf
    
    def _interpret_cohens_d(self, d: float) -> str:
        """Interpret Cohen's d effect size."""
        abs_d = abs(d)
        if abs_d < 0.2:
            return "negligible"
        elif abs_d < 0.5:
            return "small"
        elif abs_d < 0.8:
            return "medium"
        else:
            return "large"
    
    def _interpret_eta_squared(self, eta_sq: float) -> str:
        """Interpret eta-squared effect size."""
        if eta_sq < 0.01:
            return "negligible"
        elif eta_sq < 0.06:
            return "small"
        elif eta_sq < 0.14:
            return "medium"
        else:
            return "large"
    
    def validate_correlation_claim(self, x: np.ndarray, y: np.ndarray, 
                                 expected_correlation: float = 0.78,
                                 tolerance: float = 0.1) -> Dict[str, Any]:
        """Validate a specific correlation claim (e.g., r=0.78 from requirements)."""
        if not self._initialized:
            self.initialize()
        
        try:
            # Compute correlation
            correlation_results = self.compute_correlation(x, y)
            
            if 'error' in correlation_results:
                return correlation_results
            
            # Focus on Pearson correlation for the claim validation
            pearson_results = correlation_results.get('pearson', {})
            
            if 'error' in pearson_results:
                return pearson_results
            
            observed_correlation = pearson_results['correlation']
            p_value = pearson_results['p_value']
            ci_lower, ci_upper = pearson_results['confidence_interval']
            
            # Check if observed correlation is within tolerance of expected
            within_tolerance = abs(observed_correlation - expected_correlation) <= tolerance
            
            # Check if expected correlation is within confidence interval
            within_ci = ci_lower <= expected_correlation <= ci_upper
            
            # Compute effect size
            effect_size_results = self.compute_effect_size(x, y, 'cohens_d')
            
            validation_results = {
                'expected_correlation': expected_correlation,
                'observed_correlation': observed_correlation,
                'difference': observed_correlation - expected_correlation,
                'within_tolerance': within_tolerance,
                'tolerance': tolerance,
                'within_confidence_interval': within_ci,
                'confidence_interval': (ci_lower, ci_upper),
                'p_value': p_value,
                'significant': p_value < self.alpha,
                'sample_size': pearson_results['sample_size'],
                'effect_size': effect_size_results,
                'validation_passed': within_tolerance and pearson_results['significant']
            }
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error validating correlation claim: {e}")
            return {'error': str(e)}
    
    def power_analysis(self, effect_size: float, sample_size: int, alpha: float = None) -> Dict[str, Any]:
        """Perform statistical power analysis."""
        if alpha is None:
            alpha = self.alpha
        
        try:
            # This is a simplified power analysis
            # For more comprehensive analysis, consider using statsmodels or other specialized libraries
            
            # Critical value for two-tailed test
            z_critical = stats.norm.ppf(1 - alpha/2)
            
            # Standard error
            se = 1 / np.sqrt(sample_size - 3)  # For correlation
            
            # Non-centrality parameter
            ncp = effect_size / se
            
            # Power calculation (simplified)
            power = 1 - stats.norm.cdf(z_critical - ncp) + stats.norm.cdf(-z_critical - ncp)
            
            return {
                'effect_size': effect_size,
                'sample_size': sample_size,
                'alpha': alpha,
                'power': power,
                'adequate_power': power >= 0.8  # Conventional threshold
            }
            
        except Exception as e:
            self.logger.error(f"Error in power analysis: {e}")
            return {'error': str(e)}
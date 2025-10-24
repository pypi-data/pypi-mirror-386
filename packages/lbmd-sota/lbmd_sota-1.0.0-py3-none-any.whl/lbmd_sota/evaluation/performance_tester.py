"""
Performance Tester for LBMD Evaluation System

This module provides comprehensive performance testing including end-to-end pipeline tests,
scalability analysis, and memory usage optimization tests.
"""

import asyncio
import gc
import logging
import psutil
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
try:
    from memory_profiler import profile
    HAS_MEMORY_PROFILER = True
except ImportError:
    HAS_MEMORY_PROFILER = False
    def profile(func):
        return func
from tqdm import tqdm

from ..core.data_models import ExperimentConfig, LBMDResults
from .experiment_orchestrator import ExperimentOrchestrator
from .report_generator import ReportGenerator


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single test"""
    test_name: str
    execution_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    gpu_memory_mb: Optional[float]
    throughput: float  # items per second
    success_rate: float
    error_count: int


@dataclass
class ScalabilityResult:
    """Results from scalability testing"""
    input_sizes: List[int]
    execution_times: List[float]
    memory_usage: List[float]
    throughput: List[float]
    scaling_factor: float  # Linear scaling coefficient
    efficiency_score: float  # 0-1 score for scaling efficiency


class MemoryProfiler:
    """Memory usage profiler for LBMD operations"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.baseline_memory = self.get_memory_usage()
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def get_gpu_memory_usage(self) -> Optional[float]:
        """Get GPU memory usage in MB"""
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated() / 1024 / 1024
        return None
    
    def memory_snapshot(self) -> Dict[str, float]:
        """Take a memory snapshot"""
        return {
            'ram_mb': self.get_memory_usage(),
            'gpu_mb': self.get_gpu_memory_usage(),
            'ram_delta_mb': self.get_memory_usage() - self.baseline_memory
        }


class PerformanceBenchmark:
    """Individual performance benchmark"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.profiler = MemoryProfiler()
    
    def setup(self):
        """Setup benchmark (override in subclasses)"""
        pass
    
    def run(self) -> Any:
        """Run benchmark (override in subclasses)"""
        raise NotImplementedError
    
    def teardown(self):
        """Cleanup after benchmark (override in subclasses)"""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    def execute(self) -> PerformanceMetrics:
        """Execute benchmark and collect metrics"""
        self.setup()
        
        # Initial measurements
        start_memory = self.profiler.memory_snapshot()
        start_time = time.time()
        
        # CPU usage monitoring
        cpu_percent_start = psutil.cpu_percent(interval=None)
        
        try:
            # Run benchmark
            result = self.run()
            success = True
            error_count = 0
        except Exception as e:
            logging.error(f"Benchmark {self.name} failed: {e}")
            result = None
            success = False
            error_count = 1
        
        # Final measurements
        end_time = time.time()
        end_memory = self.profiler.memory_snapshot()
        cpu_percent_end = psutil.cpu_percent(interval=None)
        
        execution_time = end_time - start_time
        memory_usage = end_memory['ram_mb'] - start_memory['ram_mb']
        cpu_usage = (cpu_percent_start + cpu_percent_end) / 2
        
        # Calculate throughput (items per second)
        throughput = 1.0 / execution_time if execution_time > 0 else 0
        
        self.teardown()
        
        return PerformanceMetrics(
            test_name=self.name,
            execution_time=execution_time,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            gpu_memory_mb=end_memory['gpu_mb'],
            throughput=throughput,
            success_rate=1.0 if success else 0.0,
            error_count=error_count
        )


class LBMDPipelineBenchmark(PerformanceBenchmark):
    """End-to-end LBMD pipeline benchmark"""
    
    def __init__(self, dataset_size: int = 10, model_name: str = "mockmodel"):
        super().__init__(f"LBMD_Pipeline_{dataset_size}_{model_name}")
        self.dataset_size = dataset_size
        self.model_name = model_name
        self.orchestrator = None
    
    def setup(self):
        """Setup LBMD pipeline"""
        self.orchestrator = ExperimentOrchestrator(max_workers=1, cache_results=False)
    
    def run(self) -> Dict[str, Any]:
        """Run LBMD pipeline"""
        # Create mock experiment configuration
        datasets = ['mock_dataset']
        models = [self.model_name]
        parameter_grid = {
            'k_neurons': [10],
            'epsilon': [0.1],
            'tau': [0.5],
            'batch_size': [min(8, self.dataset_size)]
        }
        
        # Run experiments
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(
                self.orchestrator.run_experiments(datasets, models, parameter_grid)
            )
            return results
        finally:
            loop.close()


class ScalabilityBenchmark(PerformanceBenchmark):
    """Scalability testing benchmark"""
    
    def __init__(self, input_sizes: List[int]):
        super().__init__("Scalability_Test")
        self.input_sizes = input_sizes
        self.results = []
    
    def run(self) -> ScalabilityResult:
        """Run scalability tests across different input sizes"""
        execution_times = []
        memory_usage = []
        throughput = []
        
        for size in self.input_sizes:
            # Create benchmark for this size
            benchmark = LBMDPipelineBenchmark(dataset_size=size)
            metrics = benchmark.execute()
            
            execution_times.append(metrics.execution_time)
            memory_usage.append(metrics.memory_usage_mb)
            throughput.append(metrics.throughput)
        
        # Calculate scaling metrics
        scaling_factor = self._calculate_scaling_factor(self.input_sizes, execution_times)
        efficiency_score = self._calculate_efficiency_score(self.input_sizes, execution_times)
        
        return ScalabilityResult(
            input_sizes=self.input_sizes,
            execution_times=execution_times,
            memory_usage=memory_usage,
            throughput=throughput,
            scaling_factor=scaling_factor,
            efficiency_score=efficiency_score
        )
    
    def _calculate_scaling_factor(self, sizes: List[int], times: List[float]) -> float:
        """Calculate linear scaling factor"""
        if len(sizes) < 2:
            return 1.0
        
        # Linear regression to find scaling factor
        sizes_array = np.array(sizes)
        times_array = np.array(times)
        
        # Fit y = ax + b
        A = np.vstack([sizes_array, np.ones(len(sizes_array))]).T
        scaling_factor, _ = np.linalg.lstsq(A, times_array, rcond=None)[0]
        
        return scaling_factor
    
    def _calculate_efficiency_score(self, sizes: List[int], times: List[float]) -> float:
        """Calculate efficiency score (0-1, higher is better)"""
        if len(sizes) < 2:
            return 1.0
        
        # Ideal linear scaling
        ideal_times = np.array(times[0]) * np.array(sizes) / sizes[0]
        actual_times = np.array(times)
        
        # Calculate efficiency as inverse of relative error
        relative_errors = np.abs(actual_times - ideal_times) / ideal_times
        mean_error = np.mean(relative_errors)
        
        # Convert to 0-1 score (1 = perfect linear scaling)
        efficiency = 1.0 / (1.0 + mean_error)
        return min(1.0, efficiency)


class ConcurrencyBenchmark(PerformanceBenchmark):
    """Concurrency and parallelization benchmark"""
    
    def __init__(self, worker_counts: List[int]):
        super().__init__("Concurrency_Test")
        self.worker_counts = worker_counts
    
    def run(self) -> Dict[str, Any]:
        """Test performance with different worker counts"""
        results = {}
        
        for worker_count in self.worker_counts:
            orchestrator = ExperimentOrchestrator(max_workers=worker_count, cache_results=False)
            
            start_time = time.time()
            
            # Run small experiment set
            datasets = ['mock_dataset']
            models = ['mockmodel']
            parameter_grid = {
                'k_neurons': [10, 20],
                'epsilon': [0.1, 0.2],
                'tau': [0.5],
                'batch_size': [8]
            }
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                experiment_results = loop.run_until_complete(
                    orchestrator.run_experiments(datasets, models, parameter_grid)
                )
                execution_time = time.time() - start_time
                
                results[worker_count] = {
                    'execution_time': execution_time,
                    'success_rate': experiment_results.get('aggregated_results', {}).get('success_rate', 0),
                    'total_jobs': experiment_results.get('total_jobs', 0)
                }
            finally:
                loop.close()
        
        return results


class MemoryOptimizationBenchmark(PerformanceBenchmark):
    """Memory optimization and leak detection benchmark"""
    
    def __init__(self, iterations: int = 10):
        super().__init__("Memory_Optimization")
        self.iterations = iterations
    
    def run(self) -> Dict[str, Any]:
        """Test for memory leaks and optimization"""
        memory_snapshots = []
        
        for i in range(self.iterations):
            # Take memory snapshot before
            snapshot_before = self.profiler.memory_snapshot()
            
            # Run a small LBMD operation
            benchmark = LBMDPipelineBenchmark(dataset_size=5)
            benchmark.execute()
            
            # Force garbage collection
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Take memory snapshot after
            snapshot_after = self.profiler.memory_snapshot()
            
            memory_snapshots.append({
                'iteration': i,
                'memory_before': snapshot_before['ram_mb'],
                'memory_after': snapshot_after['ram_mb'],
                'memory_delta': snapshot_after['ram_mb'] - snapshot_before['ram_mb'],
                'gpu_memory': snapshot_after['gpu_mb']
            })
        
        # Analyze memory trends
        memory_deltas = [s['memory_delta'] for s in memory_snapshots]
        memory_trend = np.polyfit(range(len(memory_deltas)), memory_deltas, 1)[0]
        
        return {
            'snapshots': memory_snapshots,
            'memory_trend': memory_trend,  # MB per iteration
            'total_memory_growth': sum(memory_deltas),
            'max_memory_delta': max(memory_deltas),
            'min_memory_delta': min(memory_deltas)
        }


class PerformanceTester:
    """
    Comprehensive performance testing system for LBMD evaluation framework.
    
    Provides end-to-end pipeline tests, scalability analysis, and memory usage optimization tests.
    """
    
    def __init__(self, output_dir: str = "./performance_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.benchmarks: List[PerformanceBenchmark] = []
        self.results: List[PerformanceMetrics] = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def add_benchmark(self, benchmark: PerformanceBenchmark):
        """Add a benchmark to the test suite"""
        self.benchmarks.append(benchmark)
    
    def run_all_benchmarks(self) -> List[PerformanceMetrics]:
        """Run all registered benchmarks"""
        self.results = []
        
        for benchmark in tqdm(self.benchmarks, desc="Running benchmarks"):
            self.logger.info(f"Running benchmark: {benchmark.name}")
            
            try:
                metrics = benchmark.execute()
                self.results.append(metrics)
                self.logger.info(f"Completed {benchmark.name}: {metrics.execution_time:.2f}s")
            except Exception as e:
                self.logger.error(f"Benchmark {benchmark.name} failed: {e}")
        
        return self.results
    
    def run_scalability_test(self, input_sizes: List[int] = None) -> ScalabilityResult:
        """Run scalability testing"""
        if input_sizes is None:
            input_sizes = [5, 10, 20, 50, 100]
        
        self.logger.info("Running scalability test")
        benchmark = ScalabilityBenchmark(input_sizes)
        return benchmark.run()
    
    def run_concurrency_test(self, worker_counts: List[int] = None) -> Dict[str, Any]:
        """Run concurrency testing"""
        if worker_counts is None:
            worker_counts = [1, 2, 4, 8]
        
        self.logger.info("Running concurrency test")
        benchmark = ConcurrencyBenchmark(worker_counts)
        return benchmark.run()
    
    def run_memory_optimization_test(self, iterations: int = 10) -> Dict[str, Any]:
        """Run memory optimization testing"""
        self.logger.info("Running memory optimization test")
        benchmark = MemoryOptimizationBenchmark(iterations)
        return benchmark.run()
    
    def generate_performance_report(self) -> str:
        """Generate comprehensive performance report"""
        if not self.results:
            self.logger.warning("No benchmark results available")
            return ""
        
        # Create performance summary
        df = pd.DataFrame([
            {
                'benchmark': r.test_name,
                'execution_time': r.execution_time,
                'memory_usage_mb': r.memory_usage_mb,
                'cpu_usage_percent': r.cpu_usage_percent,
                'throughput': r.throughput,
                'success_rate': r.success_rate
            }
            for r in self.results
        ])
        
        # Generate visualizations
        self._create_performance_visualizations(df)
        
        # Generate report
        report_generator = ReportGenerator(str(self.output_dir))
        
        # Prepare data for report
        results_data = {
            'performance_summary': {
                'total_benchmarks': len(self.results),
                'average_execution_time': df['execution_time'].mean(),
                'average_memory_usage': df['memory_usage_mb'].mean(),
                'overall_success_rate': df['success_rate'].mean()
            }
        }
        
        report_path = report_generator.generate_report(
            results_data,
            df,
            report_format="html",
            experiment_id="performance_test"
        )
        
        return report_path
    
    def _create_performance_visualizations(self, df: pd.DataFrame):
        """Create performance visualization plots"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('LBMD Performance Analysis', fontsize=16)
        
        # Execution time by benchmark
        df.plot(x='benchmark', y='execution_time', kind='bar', ax=axes[0, 0])
        axes[0, 0].set_title('Execution Time by Benchmark')
        axes[0, 0].set_ylabel('Time (seconds)')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Memory usage by benchmark
        df.plot(x='benchmark', y='memory_usage_mb', kind='bar', ax=axes[0, 1], color='orange')
        axes[0, 1].set_title('Memory Usage by Benchmark')
        axes[0, 1].set_ylabel('Memory (MB)')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Throughput comparison
        df.plot(x='benchmark', y='throughput', kind='bar', ax=axes[1, 0], color='green')
        axes[1, 0].set_title('Throughput by Benchmark')
        axes[1, 0].set_ylabel('Items/Second')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Success rate
        df.plot(x='benchmark', y='success_rate', kind='bar', ax=axes[1, 1], color='red')
        axes[1, 1].set_title('Success Rate by Benchmark')
        axes[1, 1].set_ylabel('Success Rate')
        axes[1, 1].set_ylim(0, 1.1)
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        output_path = self.output_dir / "performance_analysis.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Performance visualization saved: {output_path}")
    
    def create_scalability_visualization(self, scalability_result: ScalabilityResult):
        """Create scalability analysis visualization"""
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        fig.suptitle('LBMD Scalability Analysis', fontsize=16)
        
        # Execution time vs input size
        axes[0].plot(scalability_result.input_sizes, scalability_result.execution_times, 'bo-')
        axes[0].set_xlabel('Input Size')
        axes[0].set_ylabel('Execution Time (s)')
        axes[0].set_title('Execution Time Scaling')
        axes[0].grid(True, alpha=0.3)
        
        # Memory usage vs input size
        axes[1].plot(scalability_result.input_sizes, scalability_result.memory_usage, 'ro-')
        axes[1].set_xlabel('Input Size')
        axes[1].set_ylabel('Memory Usage (MB)')
        axes[1].set_title('Memory Usage Scaling')
        axes[1].grid(True, alpha=0.3)
        
        # Throughput vs input size
        axes[2].plot(scalability_result.input_sizes, scalability_result.throughput, 'go-')
        axes[2].set_xlabel('Input Size')
        axes[2].set_ylabel('Throughput (items/s)')
        axes[2].set_title('Throughput Scaling')
        axes[2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        output_path = self.output_dir / "scalability_analysis.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Scalability visualization saved: {output_path}")
    
    def run_comprehensive_performance_test(self) -> Dict[str, Any]:
        """Run comprehensive performance testing suite"""
        self.logger.info("Starting comprehensive performance testing")
        
        # Add standard benchmarks
        self.add_benchmark(LBMDPipelineBenchmark(dataset_size=10))
        self.add_benchmark(LBMDPipelineBenchmark(dataset_size=50))
        self.add_benchmark(LBMDPipelineBenchmark(dataset_size=100))
        
        # Run all benchmarks
        benchmark_results = self.run_all_benchmarks()
        
        # Run specialized tests
        scalability_result = self.run_scalability_test()
        concurrency_result = self.run_concurrency_test()
        memory_result = self.run_memory_optimization_test()
        
        # Create visualizations
        self.create_scalability_visualization(scalability_result)
        
        # Generate comprehensive report
        report_path = self.generate_performance_report()
        
        # Compile all results
        comprehensive_results = {
            'benchmark_results': benchmark_results,
            'scalability_result': scalability_result,
            'concurrency_result': concurrency_result,
            'memory_result': memory_result,
            'report_path': report_path
        }
        
        # Save comprehensive results
        results_path = self.output_dir / "comprehensive_performance_results.json"
        import json
        with open(results_path, 'w') as f:
            json.dump(comprehensive_results, f, indent=2, default=str)
        
        self.logger.info(f"Comprehensive performance test completed. Results: {results_path}")
        return comprehensive_results


# Example usage and testing
def example_performance_testing():
    """Example of using the performance tester"""
    tester = PerformanceTester()
    
    # Run comprehensive test
    results = tester.run_comprehensive_performance_test()
    
    print("Performance Testing Results:")
    print(f"- Benchmark Results: {len(results['benchmark_results'])} tests")
    print(f"- Scalability Efficiency: {results['scalability_result'].efficiency_score:.2f}")
    print(f"- Memory Trend: {results['memory_result']['memory_trend']:.2f} MB/iteration")
    print(f"- Report: {results['report_path']}")
    
    return results


if __name__ == "__main__":
    example_performance_testing()
"""
Experiment Orchestrator for Large-Scale LBMD Experiments

This module provides distributed experiment execution framework with result aggregation,
statistical analysis pipelines, and experiment reproducibility systems.
"""

import asyncio
import concurrent.futures
import hashlib
import json
import logging
import os
import pickle
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import torch
from tqdm import tqdm

from ..core.data_models import ExperimentConfig, LBMDResults, ValidationResults
from ..core.interfaces import DatasetInterface, ModelInterface
from ..empirical_validation.multi_dataset_evaluator import MultiDatasetEvaluator
from ..empirical_validation.statistical_analyzer import StatisticalAnalyzer


@dataclass
class ExperimentJob:
    """Individual experiment job configuration"""
    job_id: str
    config: ExperimentConfig
    dataset_name: str
    model_name: str
    parameters: Dict[str, Any]
    priority: int = 1
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class ExperimentResult:
    """Results from a single experiment job"""
    job_id: str
    success: bool
    results: Optional[LBMDResults]
    error_message: Optional[str]
    execution_time: float
    memory_usage: float
    timestamp: datetime
    reproducibility_hash: str


class ExperimentQueue:
    """Thread-safe experiment queue for job management"""
    
    def __init__(self):
        self._queue = asyncio.Queue()
        self._completed = []
        self._failed = []
        self._lock = asyncio.Lock()
    
    async def add_job(self, job: ExperimentJob):
        """Add experiment job to queue"""
        await self._queue.put(job)
    
    async def get_job(self) -> Optional[ExperimentJob]:
        """Get next job from queue"""
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None
    
    async def mark_completed(self, result: ExperimentResult):
        """Mark job as completed"""
        async with self._lock:
            self._completed.append(result)
    
    async def mark_failed(self, result: ExperimentResult):
        """Mark job as failed"""
        async with self._lock:
            self._failed.append(result)
    
    def get_status(self) -> Dict[str, int]:
        """Get queue status"""
        return {
            'pending': self._queue.qsize(),
            'completed': len(self._completed),
            'failed': len(self._failed)
        }


class ResultAggregator:
    """Aggregates and analyzes results from multiple experiments"""
    
    def __init__(self):
        self.results: List[ExperimentResult] = []
        self.statistical_analyzer = StatisticalAnalyzer({})
    
    def add_result(self, result: ExperimentResult):
        """Add experiment result"""
        self.results.append(result)
    
    def aggregate_results(self) -> Dict[str, Any]:
        """Aggregate results across all experiments"""
        if not self.results:
            return {}
        
        successful_results = [r for r in self.results if r.success and r.results]
        
        if not successful_results:
            return {'error': 'No successful experiments'}
        
        # Aggregate performance metrics
        execution_times = [r.execution_time for r in successful_results]
        memory_usage = [r.memory_usage for r in successful_results]
        
        # Aggregate LBMD metrics
        boundary_scores = []
        transition_strengths = []
        
        for result in successful_results:
            if result.results and hasattr(result.results, 'boundary_scores'):
                boundary_scores.extend(result.results.boundary_scores.flatten())
            if result.results and hasattr(result.results, 'transition_strengths'):
                transition_strengths.extend(result.results.transition_strengths.values())
        
        aggregated = {
            'experiment_count': len(self.results),
            'success_rate': len(successful_results) / len(self.results),
            'performance_metrics': {
                'mean_execution_time': np.mean(execution_times),
                'std_execution_time': np.std(execution_times),
                'mean_memory_usage': np.mean(memory_usage),
                'std_memory_usage': np.std(memory_usage)
            },
            'lbmd_metrics': {
                'mean_boundary_score': np.mean(boundary_scores) if boundary_scores else 0,
                'std_boundary_score': np.std(boundary_scores) if boundary_scores else 0,
                'mean_transition_strength': np.mean(transition_strengths) if transition_strengths else 0,
                'std_transition_strength': np.std(transition_strengths) if transition_strengths else 0
            }
        }
        
        # Statistical analysis
        if len(boundary_scores) > 10:  # Minimum sample size for statistical analysis
            statistical_results = self.statistical_analyzer.compute_correlation(
                np.array(boundary_scores), 
                np.array(transition_strengths[:len(boundary_scores)])
            )
            aggregated['statistical_analysis'] = statistical_results
        
        return aggregated
    
    def generate_summary_report(self) -> pd.DataFrame:
        """Generate summary report as DataFrame"""
        data = []
        for result in self.results:
            row = {
                'job_id': result.job_id,
                'success': result.success,
                'execution_time': result.execution_time,
                'memory_usage': result.memory_usage,
                'timestamp': result.timestamp,
                'error_message': result.error_message or ''
            }
            
            if result.results and hasattr(result.results, 'boundary_scores'):
                row['mean_boundary_score'] = np.mean(result.results.boundary_scores)
                row['boundary_score_std'] = np.std(result.results.boundary_scores)
            
            data.append(row)
        
        return pd.DataFrame(data)


class ReproducibilityManager:
    """Manages experiment reproducibility and version control"""
    
    def __init__(self, base_path: str = "./experiment_cache"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    def generate_experiment_hash(self, config: ExperimentConfig, parameters: Dict[str, Any]) -> str:
        """Generate reproducible hash for experiment configuration"""
        # Create deterministic string representation
        config_str = json.dumps(asdict(config), sort_keys=True)
        params_str = json.dumps(parameters, sort_keys=True)
        combined = f"{config_str}_{params_str}"
        
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def cache_result(self, experiment_hash: str, result: ExperimentResult):
        """Cache experiment result for reproducibility"""
        cache_file = self.base_path / f"{experiment_hash}.pkl"
        with open(cache_file, 'wb') as f:
            pickle.dump(result, f)
    
    def load_cached_result(self, experiment_hash: str) -> Optional[ExperimentResult]:
        """Load cached experiment result"""
        cache_file = self.base_path / f"{experiment_hash}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logging.warning(f"Failed to load cached result: {e}")
        return None
    
    def clear_cache(self):
        """Clear all cached results"""
        for cache_file in self.base_path.glob("*.pkl"):
            cache_file.unlink()


class ExperimentOrchestrator:
    """
    Orchestrates large-scale distributed LBMD experiments with result aggregation
    and reproducibility management.
    """
    
    def __init__(self, 
                 max_workers: int = 4,
                 use_gpu: bool = True,
                 cache_results: bool = True):
        self.max_workers = max_workers
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.cache_results = cache_results
        
        self.queue = ExperimentQueue()
        self.aggregator = ResultAggregator()
        self.reproducibility_manager = ReproducibilityManager()
        
        self.evaluator = MultiDatasetEvaluator({})
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def create_experiment_jobs(self, 
                             datasets: List[str],
                             models: List[str], 
                             parameter_grid: Dict[str, List[Any]]) -> List[ExperimentJob]:
        """Create experiment jobs from parameter grid"""
        jobs = []
        job_counter = 0
        
        for dataset in datasets:
            for model in models:
                # Generate parameter combinations
                param_names = list(parameter_grid.keys())
                param_values = list(parameter_grid.values())
                
                # Create cartesian product of parameters
                import itertools
                for param_combination in itertools.product(*param_values):
                    parameters = dict(zip(param_names, param_combination))
                    
                    config = ExperimentConfig(
                        experiment_name=f"{dataset}_{model}_{job_counter:06d}",
                        datasets=[dataset],
                        models=[model],
                        parameters=parameters,
                        output_directory="./experiment_results"
                    )
                    
                    job = ExperimentJob(
                        job_id=f"job_{job_counter:06d}",
                        config=config,
                        dataset_name=dataset,
                        model_name=model,
                        parameters=parameters
                    )
                    
                    jobs.append(job)
                    job_counter += 1
        
        return jobs
    
    async def execute_single_experiment(self, job: ExperimentJob) -> ExperimentResult:
        """Execute a single experiment job"""
        start_time = time.time()
        
        # Generate reproducibility hash
        experiment_hash = self.reproducibility_manager.generate_experiment_hash(
            job.config, job.parameters
        )
        
        # Check for cached result
        if self.cache_results:
            cached_result = self.reproducibility_manager.load_cached_result(experiment_hash)
            if cached_result:
                self.logger.info(f"Using cached result for job {job.job_id}")
                return cached_result
        
        try:
            # Monitor memory usage
            import psutil
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Execute experiment
            results = await asyncio.get_event_loop().run_in_executor(
                None, self._run_experiment_sync, job
            )
            
            execution_time = time.time() - start_time
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_usage = final_memory - initial_memory
            
            result = ExperimentResult(
                job_id=job.job_id,
                success=True,
                results=results,
                error_message=None,
                execution_time=execution_time,
                memory_usage=memory_usage,
                timestamp=datetime.now(),
                reproducibility_hash=experiment_hash
            )
            
            # Cache result
            if self.cache_results:
                self.reproducibility_manager.cache_result(experiment_hash, result)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Experiment {job.job_id} failed: {str(e)}")
            
            return ExperimentResult(
                job_id=job.job_id,
                success=False,
                results=None,
                error_message=str(e),
                execution_time=execution_time,
                memory_usage=0,
                timestamp=datetime.now(),
                reproducibility_hash=experiment_hash
            )
    
    def _run_experiment_sync(self, job: ExperimentJob) -> LBMDResults:
        """Synchronous experiment execution (for thread pool)"""
        # This would integrate with the actual LBMD evaluation pipeline
        # For now, return mock results
        return LBMDResults(
            layer_name="mock_layer",
            boundary_scores=np.random.rand(100),
            boundary_mask=np.random.randint(0, 2, (64, 64)),
            manifold_coords=np.random.rand(100, 2),
            pixel_coords=np.random.randint(0, 64, (100, 2)),
            is_boundary=np.random.randint(0, 2, 100).astype(bool),
            clusters=np.random.randint(0, 5, 100),
            transition_strengths={(0, 1): 0.5, (1, 2): 0.3},
            cluster_hulls={},
            statistical_metrics={},
            topological_properties={}
        )
    
    async def run_experiments(self, 
                            datasets: List[str],
                            models: List[str],
                            parameter_grid: Dict[str, List[Any]]) -> Dict[str, Any]:
        """Run distributed experiments across datasets and models"""
        
        # Create experiment jobs
        jobs = self.create_experiment_jobs(datasets, models, parameter_grid)
        self.logger.info(f"Created {len(jobs)} experiment jobs")
        
        # Add jobs to queue
        for job in jobs:
            await self.queue.add_job(job)
        
        # Execute jobs with progress tracking
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def execute_with_semaphore(job):
            async with semaphore:
                return await self.execute_single_experiment(job)
        
        # Process all jobs
        tasks = []
        with tqdm(total=len(jobs), desc="Executing experiments") as pbar:
            while True:
                job = await self.queue.get_job()
                if job is None:
                    break
                
                task = asyncio.create_task(execute_with_semaphore(job))
                tasks.append(task)
                
                # Update progress when task completes
                def update_progress(task):
                    pbar.update(1)
                    result = task.result()
                    if result.success:
                        asyncio.create_task(self.queue.mark_completed(result))
                    else:
                        asyncio.create_task(self.queue.mark_failed(result))
                    self.aggregator.add_result(result)
                
                task.add_done_callback(update_progress)
        
        # Wait for all tasks to complete
        if tasks:
            await asyncio.gather(*tasks)
        
        # Generate final results
        aggregated_results = self.aggregator.aggregate_results()
        summary_df = self.aggregator.generate_summary_report()
        
        return {
            'aggregated_results': aggregated_results,
            'summary_dataframe': summary_df,
            'queue_status': self.queue.get_status(),
            'total_jobs': len(jobs)
        }
    
    def save_results(self, results: Dict[str, Any], output_path: str):
        """Save experiment results to file"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save aggregated results as JSON
        json_results = {k: v for k, v in results.items() if k != 'summary_dataframe'}
        with open(output_path.with_suffix('.json'), 'w') as f:
            json.dump(json_results, f, indent=2, default=str)
        
        # Save summary DataFrame as CSV
        if 'summary_dataframe' in results:
            results['summary_dataframe'].to_csv(
                output_path.with_suffix('.csv'), 
                index=False
            )
        
        self.logger.info(f"Results saved to {output_path}")


# Example usage and testing functions
async def example_orchestration():
    """Example of using the experiment orchestrator"""
    orchestrator = ExperimentOrchestrator(max_workers=2)
    
    # Define experiment parameters
    datasets = ['coco', 'cityscapes']
    models = ['maskrcnn', 'solo']
    parameter_grid = {
        'k_neurons': [10, 20, 50],
        'epsilon': [0.1, 0.2],
        'tau': [0.5, 0.7],
        'batch_size': [8, 16]
    }
    
    # Run experiments
    results = await orchestrator.run_experiments(datasets, models, parameter_grid)
    
    # Save results
    orchestrator.save_results(results, './experiment_results/large_scale_evaluation')
    
    return results


if __name__ == "__main__":
    # Run example
    results = asyncio.run(example_orchestration())
    print(f"Completed {results['total_jobs']} experiments")
    print(f"Success rate: {results['aggregated_results'].get('success_rate', 0):.2%}")
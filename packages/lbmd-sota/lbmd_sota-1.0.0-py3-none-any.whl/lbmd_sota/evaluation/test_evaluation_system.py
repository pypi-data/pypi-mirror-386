"""
Integration and Performance Tests for LBMD Evaluation System

This module provides comprehensive integration tests for the complete LBMD evaluation
and benchmarking system, including end-to-end pipeline tests and performance validation.
"""

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import torch

from ..core.data_models import ExperimentConfig, LBMDResults
from .experiment_orchestrator import (
    ExperimentJob, ExperimentOrchestrator, ExperimentResult,
    ReproducibilityManager, ResultAggregator
)
from .performance_tester import (
    LBMDPipelineBenchmark, MemoryOptimizationBenchmark,
    PerformanceTester, ScalabilityBenchmark
)
from .report_generator import ReportGenerator, HTMLReportTemplate


class TestExperimentOrchestrator(unittest.TestCase):
    """Integration tests for experiment orchestrator"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.orchestrator = ExperimentOrchestrator(
            max_workers=2,
            use_gpu=False,
            cache_results=True
        )
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_experiment_jobs(self):
        """Test experiment job creation"""
        datasets = ['coco', 'cityscapes']
        models = ['maskrcnn', 'solo']
        parameter_grid = {
            'k_neurons': [10, 20],
            'epsilon': [0.1, 0.2]
        }
        
        jobs = self.orchestrator.create_experiment_jobs(datasets, models, parameter_grid)
        
        # Should create 2 datasets * 2 models * 2 k_neurons * 2 epsilon = 16 jobs
        self.assertEqual(len(jobs), 16)
        
        # Check job structure
        job = jobs[0]
        self.assertIsInstance(job, ExperimentJob)
        self.assertIn(job.dataset_name, datasets)
        self.assertIn(job.model_name, models)
        self.assertIn('k_neurons', job.parameters)
        self.assertIn('epsilon', job.parameters)
    
    def test_reproducibility_manager(self):
        """Test experiment reproducibility"""
        manager = ReproducibilityManager(base_path=self.temp_dir)
        
        # Create test configuration
        config = ExperimentConfig(
            dataset_name='test_dataset',
            model_name='test_model',
            batch_size=8,
            num_samples=100
        )
        parameters = {'k_neurons': 10, 'epsilon': 0.1}
        
        # Generate hash
        hash1 = manager.generate_experiment_hash(config, parameters)
        hash2 = manager.generate_experiment_hash(config, parameters)
        
        # Same config should produce same hash
        self.assertEqual(hash1, hash2)
        
        # Different config should produce different hash
        config2 = ExperimentConfig(
            dataset_name='test_dataset2',
            model_name='test_model',
            batch_size=8,
            num_samples=100
        )
        hash3 = manager.generate_experiment_hash(config2, parameters)
        self.assertNotEqual(hash1, hash3)
    
    def test_result_aggregator(self):
        """Test result aggregation"""
        aggregator = ResultAggregator()
        
        # Create mock results
        for i in range(5):
            result = ExperimentResult(
                job_id=f'job_{i}',
                success=True,
                results=LBMDResults(
                    layer_name=f'layer_{i}',
                    boundary_scores=np.random.rand(10),
                    boundary_mask=np.random.randint(0, 2, (8, 8)),
                    manifold_coords=np.random.rand(10, 2),
                    pixel_coords=np.random.randint(0, 8, (10, 2)),
                    is_boundary=np.random.randint(0, 2, 10).astype(bool),
                    clusters=np.random.randint(0, 3, 10),
                    transition_strengths={(0, 1): 0.5, (1, 2): 0.3},
                    cluster_hulls={},
                    statistical_metrics={},
                    topological_properties={}
                ),
                error_message=None,
                execution_time=1.0 + i * 0.1,
                memory_usage=100.0 + i * 10,
                timestamp=None,
                reproducibility_hash=f'hash_{i}'
            )
            aggregator.add_result(result)
        
        # Test aggregation
        aggregated = aggregator.aggregate_results()
        
        self.assertEqual(aggregated['experiment_count'], 5)
        self.assertEqual(aggregated['success_rate'], 1.0)
        self.assertIn('performance_metrics', aggregated)
        self.assertIn('lbmd_metrics', aggregated)
        
        # Test summary report
        summary_df = aggregator.generate_summary_report()
        self.assertEqual(len(summary_df), 5)
        self.assertIn('job_id', summary_df.columns)
        self.assertIn('success', summary_df.columns)
    
    @patch('lbmd_sota.evaluation.experiment_orchestrator.MultiDatasetEvaluator')
    def test_single_experiment_execution(self, mock_evaluator):
        """Test single experiment execution"""
        # Create test job
        config = ExperimentConfig(
            dataset_name='test_dataset',
            model_name='test_model',
            batch_size=8,
            num_samples=10
        )
        
        job = ExperimentJob(
            job_id='test_job',
            config=config,
            dataset_name='test_dataset',
            model_name='test_model',
            parameters={'k_neurons': 10}
        )
        
        # Run experiment
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                self.orchestrator.execute_single_experiment(job)
            )
        finally:
            loop.close()
        
        # Verify result
        self.assertIsInstance(result, ExperimentResult)
        self.assertEqual(result.job_id, 'test_job')
        self.assertTrue(result.success)  # Mock should succeed
        self.assertIsNotNone(result.results)


class TestReportGenerator(unittest.TestCase):
    """Integration tests for report generator"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = ReportGenerator(output_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_html_template_rendering(self):
        """Test HTML template rendering"""
        template = HTMLReportTemplate()
        
        test_data = {
            'report_metadata': {
                'generated_at': '2024-01-01 12:00:00',
                'experiment_id': 'test_exp'
            },
            'summary_statistics': {
                'total_experiments': 10,
                'success_rate': 0.9,
                'mean_execution_time': 120.5,
                'mean_memory_usage': 512.0
            },
            'statistical_analysis': {},
            'dataset_results': [],
            'figures': [],
            'conclusions': ['Test conclusion']
        }
        
        html_content = template.render(test_data)
        
        # Verify HTML structure
        self.assertIn('<html>', html_content)
        self.assertIn('LBMD Experiment Report', html_content)
        self.assertIn('test_exp', html_content)
        self.assertIn('90.0%', html_content)  # Success rate
        self.assertIn('Test conclusion', html_content)
    
    def test_report_generation(self):
        """Test complete report generation"""
        # Create sample data
        sample_summary = pd.DataFrame({
            'job_id': ['job_001', 'job_002', 'job_003'],
            'success': [True, True, False],
            'execution_time': [120.0, 130.0, 140.0],
            'memory_usage': [512.0, 520.0, 530.0],
            'mean_boundary_score': [0.75, 0.80, 0.70],
            'dataset': ['coco', 'coco', 'cityscapes'],
            'model': ['maskrcnn', 'solo', 'maskrcnn']
        })
        
        sample_results = {
            'aggregated_results': {
                'experiment_count': 3,
                'success_rate': 0.67
            }
        }
        
        # Generate report
        report_path = self.generator.generate_report(
            sample_results,
            sample_summary,
            report_format="html",
            experiment_id="test_report"
        )
        
        # Verify report was created
        self.assertTrue(Path(report_path).exists())
        
        # Verify content
        with open(report_path, 'r') as f:
            content = f.read()
            self.assertIn('LBMD Experiment Report', content)
            self.assertIn('test_report', content)
    
    def test_comparison_report_generation(self):
        """Test comparison report generation"""
        # Create sample experiment results
        exp1_summary = pd.DataFrame({
            'job_id': ['job_001', 'job_002'],
            'success': [True, True],
            'execution_time': [120.0, 130.0],
            'memory_usage': [512.0, 520.0],
            'mean_boundary_score': [0.75, 0.80],
            'dataset': ['coco', 'coco'],
            'model': ['maskrcnn', 'solo']
        })
        
        exp2_summary = pd.DataFrame({
            'job_id': ['job_003', 'job_004'],
            'success': [True, False],
            'execution_time': [140.0, 150.0],
            'memory_usage': [530.0, 540.0],
            'mean_boundary_score': [0.70, 0.65],
            'dataset': ['cityscapes', 'cityscapes'],
            'model': ['maskrcnn', 'solo']
        })
        
        experiment_results = [
            {'summary_dataframe': exp1_summary},
            {'summary_dataframe': exp2_summary}
        ]
        
        # Generate comparison report
        report_path = self.generator.generate_comparison_report(
            experiment_results,
            comparison_name="test_comparison"
        )
        
        # Verify report was created
        self.assertTrue(Path(report_path).exists())
        
        # Verify content
        with open(report_path, 'r') as f:
            content = f.read()
            self.assertIn('test_comparison', content)
            self.assertIn('multi_experiment', content)


class TestPerformanceTester(unittest.TestCase):
    """Integration tests for performance tester"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.tester = PerformanceTester(output_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_lbmd_pipeline_benchmark(self):
        """Test LBMD pipeline benchmark"""
        benchmark = LBMDPipelineBenchmark(dataset_size=5, model_name="test_model")
        
        # Execute benchmark
        metrics = benchmark.execute()
        
        # Verify metrics
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.test_name, "LBMD_Pipeline_5_test_model")
        self.assertGreater(metrics.execution_time, 0)
        self.assertGreaterEqual(metrics.success_rate, 0)
        self.assertLessEqual(metrics.success_rate, 1)
    
    def test_scalability_benchmark(self):
        """Test scalability benchmark"""
        input_sizes = [5, 10, 15]
        benchmark = ScalabilityBenchmark(input_sizes)
        
        # Execute benchmark
        result = benchmark.run()
        
        # Verify results
        self.assertEqual(len(result.input_sizes), 3)
        self.assertEqual(len(result.execution_times), 3)
        self.assertEqual(len(result.memory_usage), 3)
        self.assertGreaterEqual(result.efficiency_score, 0)
        self.assertLessEqual(result.efficiency_score, 1)
    
    def test_memory_optimization_benchmark(self):
        """Test memory optimization benchmark"""
        benchmark = MemoryOptimizationBenchmark(iterations=3)
        
        # Execute benchmark
        result = benchmark.run()
        
        # Verify results
        self.assertIn('snapshots', result)
        self.assertIn('memory_trend', result)
        self.assertEqual(len(result['snapshots']), 3)
        
        # Check snapshot structure
        snapshot = result['snapshots'][0]
        self.assertIn('iteration', snapshot)
        self.assertIn('memory_before', snapshot)
        self.assertIn('memory_after', snapshot)
        self.assertIn('memory_delta', snapshot)
    
    def test_performance_report_generation(self):
        """Test performance report generation"""
        # Add some benchmarks
        self.tester.add_benchmark(LBMDPipelineBenchmark(dataset_size=5))
        self.tester.add_benchmark(LBMDPipelineBenchmark(dataset_size=10))
        
        # Run benchmarks
        results = self.tester.run_all_benchmarks()
        
        # Generate report
        report_path = self.tester.generate_performance_report()
        
        # Verify report
        self.assertTrue(Path(report_path).exists())
        self.assertEqual(len(results), 2)


class TestEndToEndIntegration(unittest.TestCase):
    """End-to-end integration tests for the complete evaluation system"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_evaluation_pipeline(self):
        """Test complete evaluation pipeline from orchestration to reporting"""
        # Setup components
        orchestrator = ExperimentOrchestrator(max_workers=1, cache_results=False)
        report_generator = ReportGenerator(output_dir=self.temp_dir)
        
        # Define small experiment
        datasets = ['mock_dataset']
        models = ['mock_model']
        parameter_grid = {
            'k_neurons': [10, 20],
            'epsilon': [0.1]
        }
        
        # Run experiments
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(
                orchestrator.run_experiments(datasets, models, parameter_grid)
            )
        finally:
            loop.close()
        
        # Verify experiment results
        self.assertIn('aggregated_results', results)
        self.assertIn('summary_dataframe', results)
        self.assertEqual(results['total_jobs'], 2)  # 2 k_neurons values
        
        # Generate report
        report_path = report_generator.generate_report(
            results['aggregated_results'],
            results['summary_dataframe'],
            experiment_id="integration_test"
        )
        
        # Verify report
        self.assertTrue(Path(report_path).exists())
    
    def test_performance_and_reporting_integration(self):
        """Test integration between performance testing and reporting"""
        # Setup performance tester
        tester = PerformanceTester(output_dir=self.temp_dir)
        
        # Add benchmarks
        tester.add_benchmark(LBMDPipelineBenchmark(dataset_size=5))
        
        # Run performance tests
        benchmark_results = tester.run_all_benchmarks()
        scalability_result = tester.run_scalability_test([5, 10])
        
        # Generate performance report
        report_path = tester.generate_performance_report()
        
        # Verify integration
        self.assertTrue(len(benchmark_results) > 0)
        self.assertIsNotNone(scalability_result)
        self.assertTrue(Path(report_path).exists())
        
        # Verify scalability visualization
        viz_path = Path(self.temp_dir) / "scalability_analysis.png"
        self.assertTrue(viz_path.exists())
    
    def test_reproducibility_across_runs(self):
        """Test reproducibility of results across multiple runs"""
        orchestrator = ExperimentOrchestrator(max_workers=1, cache_results=True)
        
        # Define experiment
        datasets = ['mock_dataset']
        models = ['mock_model']
        parameter_grid = {'k_neurons': [10]}
        
        # Run experiment twice
        results1 = None
        results2 = None
        
        for i in range(2):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(
                    orchestrator.run_experiments(datasets, models, parameter_grid)
                )
                if i == 0:
                    results1 = results
                else:
                    results2 = results
            finally:
                loop.close()
        
        # Compare results (should be identical due to caching)
        self.assertEqual(results1['total_jobs'], results2['total_jobs'])
        self.assertEqual(
            results1['aggregated_results']['experiment_count'],
            results2['aggregated_results']['experiment_count']
        )


class TestSystemStressAndLimits(unittest.TestCase):
    """Stress tests and system limits testing"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_large_parameter_grid(self):
        """Test system behavior with large parameter grids"""
        orchestrator = ExperimentOrchestrator(max_workers=2, cache_results=False)
        
        # Create large parameter grid
        datasets = ['dataset1', 'dataset2']
        models = ['model1', 'model2']
        parameter_grid = {
            'k_neurons': [10, 20, 30, 40, 50],
            'epsilon': [0.1, 0.2, 0.3],
            'tau': [0.5, 0.7]
        }
        
        # Create jobs (should be 2*2*5*3*2 = 120 jobs)
        jobs = orchestrator.create_experiment_jobs(datasets, models, parameter_grid)
        
        # Verify job count
        expected_jobs = 2 * 2 * 5 * 3 * 2
        self.assertEqual(len(jobs), expected_jobs)
        
        # Test that jobs have unique IDs
        job_ids = [job.job_id for job in jobs]
        self.assertEqual(len(job_ids), len(set(job_ids)))
    
    def test_memory_usage_monitoring(self):
        """Test memory usage monitoring during intensive operations"""
        tester = PerformanceTester(output_dir=self.temp_dir)
        
        # Run memory optimization test
        memory_result = tester.run_memory_optimization_test(iterations=5)
        
        # Verify memory monitoring
        self.assertIn('snapshots', memory_result)
        self.assertIn('memory_trend', memory_result)
        
        # Check that memory trend is reasonable (not growing too fast)
        memory_trend = memory_result['memory_trend']
        self.assertLess(abs(memory_trend), 100)  # Less than 100MB per iteration growth
    
    def test_concurrent_execution_limits(self):
        """Test system behavior under high concurrency"""
        tester = PerformanceTester(output_dir=self.temp_dir)
        
        # Test with different worker counts
        concurrency_result = tester.run_concurrency_test([1, 2, 4])
        
        # Verify results structure
        self.assertIn(1, concurrency_result)
        self.assertIn(2, concurrency_result)
        self.assertIn(4, concurrency_result)
        
        # Check that execution times are reasonable
        for worker_count, result in concurrency_result.items():
            self.assertIn('execution_time', result)
            self.assertGreater(result['execution_time'], 0)
            self.assertLess(result['execution_time'], 300)  # Less than 5 minutes


def run_integration_tests():
    """Run all integration tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestExperimentOrchestrator,
        TestReportGenerator,
        TestPerformanceTester,
        TestEndToEndIntegration,
        TestSystemStressAndLimits
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    if success:
        print("\nAll integration tests passed!")
    else:
        print("\nSome integration tests failed!")
        exit(1)
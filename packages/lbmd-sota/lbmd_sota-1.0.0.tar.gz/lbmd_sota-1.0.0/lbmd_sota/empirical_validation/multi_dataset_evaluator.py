"""
Multi-dataset evaluator for comprehensive LBMD validation.
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from ..core.interfaces import BaseEvaluator, DatasetInterface
from ..core.data_models import ValidationResults, DatasetResults, ExperimentConfig
from .dataset_loaders import DatasetFactory, DataValidationPipeline, PreprocessingPipelines


class MultiDatasetEvaluator(BaseEvaluator):
    """Orchestrates evaluation across different datasets."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.datasets: Dict[str, DatasetInterface] = {}
        self.validation_pipeline = DataValidationPipeline(config.get('validation_config', {}))
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Dataset configuration
        self.dataset_configs = config.get('datasets', {})
        self.data_root = config.get('data_root', './data')
        
    def initialize(self) -> None:
        """Initialize the multi-dataset evaluator."""
        try:
            # Initialize datasets from configuration
            for dataset_name, dataset_config in self.dataset_configs.items():
                self._initialize_dataset(dataset_name, dataset_config)
            
            self._initialized = True
            self.logger.info(f"MultiDatasetEvaluator initialized with {len(self.datasets)} datasets")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MultiDatasetEvaluator: {e}")
            raise
    
    def _initialize_dataset(self, name: str, config: Dict[str, Any]) -> None:
        """Initialize a single dataset from configuration."""
        try:
            dataset_type = config['type']
            dataset_root = config.get('root', Path(self.data_root) / name)
            
            # Get appropriate preprocessing transform
            transform = self._get_dataset_transform(dataset_type, train=False)
            
            # Create dataset loader
            dataset_loader = DatasetFactory.create_dataset_loader(
                dataset_type=dataset_type,
                root=dataset_root,
                split='val',  # Use validation split for evaluation
                transform=transform,
                **config.get('loader_kwargs', {})
            )
            
            # Validate dataset
            if dataset_loader.validate_format():
                self.datasets[name] = dataset_loader
                self.logger.info(f"Successfully initialized dataset: {name}")
            else:
                self.logger.error(f"Dataset validation failed for: {name}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize dataset {name}: {e}")
            raise
    
    def _get_dataset_transform(self, dataset_type: str, train: bool = False):
        """Get appropriate preprocessing transform for dataset type."""
        if dataset_type == 'coco':
            return PreprocessingPipelines.get_coco_transform(train)
        elif dataset_type == 'cityscapes':
            return PreprocessingPipelines.get_cityscapes_transform(train)
        elif dataset_type == 'medical':
            return PreprocessingPipelines.get_medical_transform(train)
        else:
            # Default transform for other dataset types
            return PreprocessingPipelines.get_coco_transform(train)
    
    def evaluate(self, data: Any) -> ValidationResults:
        """Evaluate LBMD across multiple datasets."""
        if not self._initialized:
            self.initialize()
        
        # This will be implemented in subsequent tasks
        # For now, return empty validation results
        return ValidationResults(
            dataset_results={},
            model_results={},
            correlation_analysis=None,
            statistical_significance=None,
            effect_sizes=None,
            cross_validation_scores=[]
        )
    
    def register_dataset(self, name: str, dataset: DatasetInterface) -> None:
        """Register a dataset for evaluation."""
        self.datasets[name] = dataset
        self.logger.info(f"Registered dataset: {name}")
    
    def run_comprehensive_evaluation(self, datasets: List[str], models: List[str]) -> ValidationResults:
        """Run comprehensive evaluation across datasets and models."""
        if not self._initialized:
            self.initialize()
        
        # Validate requested datasets
        available_datasets = set(self.datasets.keys())
        requested_datasets = set(datasets)
        
        if not requested_datasets.issubset(available_datasets):
            missing = requested_datasets - available_datasets
            raise ValueError(f"Requested datasets not available: {missing}")
        
        self.logger.info(f"Starting comprehensive evaluation on {len(datasets)} datasets and {len(models)} models")
        
        # This will be implemented in subsequent tasks when model support is added
        # For now, return empty validation results
        return ValidationResults(
            dataset_results={},
            model_results={},
            correlation_analysis=None,
            statistical_significance=None,
            effect_sizes=None,
            cross_validation_scores=[]
        )
    
    def validate_datasets(self, dataset_names: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """Validate specified datasets and return validation reports."""
        if not self._initialized:
            self.initialize()
        
        if dataset_names is None:
            dataset_names = list(self.datasets.keys())
        
        validation_reports = {}
        
        for dataset_name in dataset_names:
            if dataset_name in self.datasets:
                self.logger.info(f"Validating dataset: {dataset_name}")
                validation_report = self.validation_pipeline.validate_dataset(self.datasets[dataset_name])
                validation_reports[dataset_name] = validation_report
            else:
                self.logger.warning(f"Dataset not found: {dataset_name}")
        
        return validation_reports
    
    def get_dataset_statistics(self, dataset_names: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """Get statistics for specified datasets."""
        if not self._initialized:
            self.initialize()
        
        if dataset_names is None:
            dataset_names = list(self.datasets.keys())
        
        statistics = {}
        
        for dataset_name in dataset_names:
            if dataset_name in self.datasets:
                try:
                    stats = self.datasets[dataset_name].get_statistics()
                    statistics[dataset_name] = stats
                except Exception as e:
                    self.logger.error(f"Error getting statistics for {dataset_name}: {e}")
                    statistics[dataset_name] = {'error': str(e)}
            else:
                self.logger.warning(f"Dataset not found: {dataset_name}")
        
        return statistics
    
    def get_available_datasets(self) -> List[str]:
        """Get list of available dataset names."""
        return list(self.datasets.keys())
    
    def get_supported_dataset_types(self) -> List[str]:
        """Get list of supported dataset types."""
        return DatasetFactory.get_supported_datasets()
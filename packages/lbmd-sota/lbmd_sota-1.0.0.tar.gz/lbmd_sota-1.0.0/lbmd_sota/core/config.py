"""
Configuration management system for LBMD SOTA framework.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
import logging


class LBMDConfig:
    """Main configuration class for LBMD SOTA framework."""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """Initialize configuration from dictionary or defaults."""
        # Set defaults
        self.experiment_name = "lbmd_sota_experiment"
        self.output_directory = "./results"
        self.random_seed = 42
        self.device = "cuda"
        self.data_root = "./data"
        self.batch_size = 16
        self.num_workers = 4
        self.checkpoint_directory = "./checkpoints"
        self.log_level = "INFO"
        self.log_file = None
        
        # Initialize default configurations
        self.datasets = self._get_default_dataset_config()
        self.models = self._get_default_model_config()
        self.lbmd_params = self._get_default_lbmd_params()
        self.validation_config = self._get_default_validation_config()
        self.comparison_config = self._get_default_comparison_config()
        self.visualization_config = self._get_default_visualization_config()
        
        # Override with provided config
        if config_dict:
            self._update_from_dict(config_dict)
    
    def _update_from_dict(self, config_dict: Dict[str, Any]):
        """Update configuration from dictionary."""
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                # Handle nested configs
                if key == 'lbmd_parameters':
                    self.lbmd_params = value
                elif key == 'comparative_analysis':
                    self.comparison_config = value
                elif key == 'visualization':
                    self.visualization_config = value
                elif key == 'computation':
                    if 'device' in value:
                        self.device = value['device']
                    if 'mixed_precision' in value:
                        self.mixed_precision = value.get('mixed_precision', False)
                else:
                    setattr(self, key, value)
    
    def __post_init__(self):
        """Initialize default configurations."""
        if self.datasets is None:
            self.datasets = self._get_default_dataset_config()
        
        if self.models is None:
            self.models = self._get_default_model_config()
        
        if self.lbmd_params is None:
            self.lbmd_params = self._get_default_lbmd_params()
        
        if self.validation_config is None:
            self.validation_config = self._get_default_validation_config()
        
        if self.comparison_config is None:
            self.comparison_config = self._get_default_comparison_config()
        
        if self.visualization_config is None:
            self.visualization_config = self._get_default_visualization_config()
    
    @property
    def lbmd_parameters(self):
        """Alias for lbmd_params for backward compatibility."""
        return self.lbmd_params
    
    @lbmd_parameters.setter
    def lbmd_parameters(self, value):
        """Setter for lbmd_parameters alias."""
        self.lbmd_params = value
    
    def _get_default_dataset_config(self) -> Dict[str, Dict[str, Any]]:
        """Get default dataset configuration."""
        return {
            "coco": {
                "type": "coco",
                "root": os.path.join(self.data_root, "coco"),
                "splits": ["train", "val"],
                "categories": "all"
            },
            "cityscapes": {
                "type": "cityscapes",
                "root": os.path.join(self.data_root, "cityscapes"),
                "splits": ["train", "val"],
                "categories": "all"
            },
            "pascal_voc": {
                "type": "pascal_voc",
                "root": os.path.join(self.data_root, "pascal_voc"),
                "splits": ["train", "val"],
                "categories": "all"
            }
        }
    
    def _get_default_model_config(self) -> Dict[str, Dict[str, Any]]:
        """Get default model configuration."""
        return {
            "mask_rcnn_r50": {
                "architecture": "mask_rcnn",
                "backbone": "resnet50",
                "checkpoint": "mask_rcnn_r50_fpn_1x_coco.pth",
                "config_file": "configs/mask_rcnn_r50_fpn_1x_coco.py"
            },
            "mask_rcnn_r101": {
                "architecture": "mask_rcnn",
                "backbone": "resnet101",
                "checkpoint": "mask_rcnn_r101_fpn_1x_coco.pth",
                "config_file": "configs/mask_rcnn_r101_fpn_1x_coco.py"
            },
            "solo_r50": {
                "architecture": "solo",
                "backbone": "resnet50",
                "checkpoint": "solo_r50_fpn_1x_coco.pth",
                "config_file": "configs/solo_r50_fpn_1x_coco.py"
            },
            "yolact_r50": {
                "architecture": "yolact",
                "backbone": "resnet50",
                "checkpoint": "yolact_r50_1x_coco.pth",
                "config_file": "configs/yolact_r50_1x_coco.py"
            },
            "mask2former": {
                "architecture": "mask2former",
                "backbone": "swin_large",
                "checkpoint": "mask2former_swin_large_coco.pth",
                "config_file": "configs/mask2former_swin_large_coco.py"
            }
        }
    
    def _get_default_lbmd_params(self) -> Dict[str, Any]:
        """Get default LBMD algorithm parameters."""
        return {
            "k_top_neurons": 100,
            "epsilon": 0.1,
            "tau": 0.5,
            "manifold_method": "umap",
            "clustering_method": "hdbscan",
            "boundary_detection_method": "gradient_based",
            "n_components": 2,
            "min_cluster_size": 10,
            "distance_metric": "euclidean"
        }
    
    def _get_default_validation_config(self) -> Dict[str, Any]:
        """Get default validation configuration."""
        return {
            "cross_validation_folds": 5,
            "bootstrap_samples": 1000,
            "significance_level": 0.05,
            "correlation_threshold": 0.78,
            "min_effect_size": 0.3,
            "statistical_tests": ["pearson", "spearman", "kendall"],
            "ablation_parameters": {
                "k_range": [50, 100, 200, 500],
                "epsilon_range": [0.05, 0.1, 0.2, 0.5],
                "tau_range": [0.3, 0.5, 0.7, 0.9]
            }
        }
    
    def _get_default_comparison_config(self) -> Dict[str, Any]:
        """Get default comparative analysis configuration."""
        return {
            "baseline_methods": ["grad_cam", "integrated_gradients", "lime", "shap"],
            "comparison_metrics": ["jaccard_similarity", "cosine_similarity", "rank_correlation"],
            "failure_analysis": {
                "failure_types": ["merging", "separation", "missed_boundaries"],
                "detection_threshold": 0.5,
                "min_failure_samples": 10
            },
            "human_evaluation": {
                "num_annotators": 3,
                "agreement_threshold": 0.7,
                "sample_size": 100
            }
        }
    
    def _get_default_visualization_config(self) -> Dict[str, Any]:
        """Get default visualization configuration."""
        return {
            "figure_format": "png",
            "figure_dpi": 300,
            "figure_size": [10, 8],
            "color_scheme": "viridis",
            "interactive_backend": "plotly",
            "dashboard_port": 8050,
            "save_intermediate_plots": True,
            "plot_types": {
                "manifold_2d": True,
                "manifold_3d": True,
                "boundary_heatmaps": True,
                "transition_graphs": True,
                "statistical_plots": True
            }
        }


class ConfigManager:
    """Configuration manager for loading, saving, and validating configurations."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager."""
        self.config_path = config_path
        self.config = None
        self.logger = logging.getLogger(__name__)
    
    def load_config(self, config_path: Optional[str] = None) -> LBMDConfig:
        """Load configuration from file."""
        if config_path is None:
            config_path = self.config_path
        
        if config_path is None:
            self.logger.info("No config path provided, using default configuration")
            self.config = LBMDConfig()
            return self.config
        
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            if config_path.suffix.lower() == '.json':
                with open(config_path, 'r') as f:
                    config_dict = json.load(f)
            elif config_path.suffix.lower() in ['.yml', '.yaml']:
                with open(config_path, 'r') as f:
                    config_dict = yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")
            
            self.config = self._dict_to_config(config_dict)
            self.logger.info(f"Configuration loaded from {config_path}")
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            raise
        
        return self.config
    
    def save_config(self, config: LBMDConfig, config_path: str, format: str = "yaml") -> None:
        """Save configuration to file."""
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = asdict(config)
        
        try:
            if format.lower() == 'json':
                with open(config_path, 'w') as f:
                    json.dump(config_dict, f, indent=2)
            elif format.lower() in ['yml', 'yaml']:
                with open(config_path, 'w') as f:
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Configuration saved to {config_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            raise
    
    def validate_config(self, config: LBMDConfig) -> bool:
        """Validate configuration parameters."""
        try:
            # Validate paths
            if not os.path.exists(config.data_root):
                self.logger.warning(f"Data root directory does not exist: {config.data_root}")
            
            # Validate LBMD parameters
            if config.lbmd_params["k_top_neurons"] <= 0:
                raise ValueError("k_top_neurons must be positive")
            
            if not 0 < config.lbmd_params["epsilon"] < 1:
                raise ValueError("epsilon must be between 0 and 1")
            
            if not 0 < config.lbmd_params["tau"] < 1:
                raise ValueError("tau must be between 0 and 1")
            
            # Validate device
            if config.device not in ["cpu", "cuda"]:
                self.logger.warning(f"Unknown device: {config.device}")
            
            self.logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> LBMDConfig:
        """Convert dictionary to LBMDConfig object."""
        # Filter out keys that are not in LBMDConfig
        valid_keys = set(LBMDConfig.__annotations__.keys())
        filtered_dict = {k: v for k, v in config_dict.items() if k in valid_keys}
        
        return LBMDConfig(**filtered_dict)
    
    def get_config(self) -> Optional[LBMDConfig]:
        """Get current configuration."""
        return self.config
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        if self.config is None:
            self.config = LBMDConfig()
        
        for key, value in updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                self.logger.warning(f"Unknown configuration key: {key}")


def setup_logging(config: LBMDConfig) -> None:
    """Setup logging based on configuration."""
    log_level = getattr(logging, config.log_level.upper())
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Setup file handler if specified
    if config.log_file:
        log_path = Path(config.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(config.log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


# Global configuration instance
_global_config_manager = ConfigManager()

def get_config() -> Optional[LBMDConfig]:
    """Get global configuration instance."""
    return _global_config_manager.get_config()

def set_config(config: LBMDConfig) -> None:
    """Set global configuration instance."""
    _global_config_manager.config = config

def load_global_config(config_path: str) -> LBMDConfig:
    """Load global configuration from file."""
    return _global_config_manager.load_config(config_path)
"""
Architecture manager for handling different model architectures.
Supports Mask R-CNN variants, SOLO, YOLACT, Mask2Former, and transformer-based models.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import torch
import torch.nn as nn
from collections import OrderedDict

from ..core.interfaces import BaseComponent, ModelInterface
from ..core.data_models import ModelResults


class BaseModelAdapter(ModelInterface):
    """Base adapter class for different model architectures."""
    
    def __init__(self, model_config: Dict[str, Any]):
        self.config = model_config
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.logger = logging.getLogger(self.__class__.__name__)
        self.feature_hooks = {}
        self.feature_maps = {}
        
    def load_model(self, checkpoint_path: str) -> torch.nn.Module:
        """Load model from checkpoint."""
        try:
            checkpoint_path = Path(checkpoint_path)
            if not checkpoint_path.exists():
                raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
            
            # Load checkpoint
            checkpoint = torch.load(checkpoint_path, map_location=self.device)
            
            # Create model architecture
            self.model = self._create_model_architecture()
            
            # Load state dict
            if 'state_dict' in checkpoint:
                state_dict = checkpoint['state_dict']
            elif 'model' in checkpoint:
                state_dict = checkpoint['model']
            else:
                state_dict = checkpoint
            
            # Handle different state dict formats
            state_dict = self._process_state_dict(state_dict)
            
            self.model.load_state_dict(state_dict, strict=False)
            self.model.to(self.device)
            self.model.eval()
            
            self.logger.info(f"Successfully loaded model from {checkpoint_path}")
            return self.model
            
        except Exception as e:
            self.logger.error(f"Error loading model from {checkpoint_path}: {e}")
            raise
    
    def _create_model_architecture(self) -> nn.Module:
        """Create model architecture. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement _create_model_architecture")
    
    def _process_state_dict(self, state_dict: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Process state dict to handle different naming conventions."""
        # Remove 'module.' prefix if present (from DataParallel)
        new_state_dict = OrderedDict()
        for key, value in state_dict.items():
            if key.startswith('module.'):
                new_key = key[7:]  # Remove 'module.' prefix
            else:
                new_key = key
            new_state_dict[new_key] = value
        
        return new_state_dict
    
    def extract_features(self, input_tensor: torch.Tensor, layer_names: List[str]) -> Dict[str, torch.Tensor]:
        """Extract features from specified layers."""
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Clear previous feature maps
        self.feature_maps.clear()
        
        # Register hooks for specified layers
        self._register_hooks(layer_names)
        
        try:
            # Forward pass
            with torch.no_grad():
                _ = self.model(input_tensor.to(self.device))
            
            # Collect feature maps
            features = {}
            for layer_name in layer_names:
                if layer_name in self.feature_maps:
                    features[layer_name] = self.feature_maps[layer_name].cpu()
                else:
                    self.logger.warning(f"Feature map not found for layer: {layer_name}")
            
            return features
            
        finally:
            # Remove hooks
            self._remove_hooks()
    
    def _register_hooks(self, layer_names: List[str]) -> None:
        """Register forward hooks for feature extraction."""
        def hook_fn(name):
            def hook(module, input, output):
                self.feature_maps[name] = output.detach()
            return hook
        
        # Find and register hooks for specified layers
        for layer_name in layer_names:
            module = self._get_module_by_name(layer_name)
            if module is not None:
                hook = module.register_forward_hook(hook_fn(layer_name))
                self.feature_hooks[layer_name] = hook
            else:
                self.logger.warning(f"Layer not found: {layer_name}")
    
    def _remove_hooks(self) -> None:
        """Remove all registered hooks."""
        for hook in self.feature_hooks.values():
            hook.remove()
        self.feature_hooks.clear()
    
    def _get_module_by_name(self, name: str) -> Optional[nn.Module]:
        """Get module by name from the model."""
        if self.model is None:
            return None
        
        # Handle nested module names (e.g., 'backbone.layer4.2.conv3')
        parts = name.split('.')
        module = self.model
        
        try:
            for part in parts:
                if hasattr(module, part):
                    module = getattr(module, part)
                elif part.isdigit() and hasattr(module, '__getitem__'):
                    module = module[int(part)]
                else:
                    return None
            return module
        except (AttributeError, IndexError, KeyError):
            return None
    
    def get_layer_names(self) -> List[str]:
        """Get available layer names for feature extraction."""
        if self.model is None:
            return []
        
        layer_names = []
        
        def add_layer_names(module, prefix=''):
            for name, child in module.named_children():
                full_name = f"{prefix}.{name}" if prefix else name
                layer_names.append(full_name)
                add_layer_names(child, full_name)
        
        add_layer_names(self.model)
        return layer_names


class MaskRCNNAdapter(BaseModelAdapter):
    """Adapter for Mask R-CNN variants."""
    
    def _create_model_architecture(self) -> nn.Module:
        """Create Mask R-CNN architecture."""
        try:
            # Try to import from detectron2 first
            try:
                from detectron2.model_zoo import model_zoo
                from detectron2.config import get_cfg
                from detectron2.modeling import build_model
                
                cfg = get_cfg()
                config_file = self.config.get('config_file', 'COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml')
                cfg.merge_from_file(model_zoo.get_config_file(config_file))
                cfg.MODEL.WEIGHTS = ""  # We'll load weights separately
                
                model = build_model(cfg)
                return model
                
            except ImportError:
                # Fallback to torchvision
                import torchvision.models as models
                from torchvision.models.detection import maskrcnn_resnet50_fpn
                
                backbone = self.config.get('backbone', 'resnet50')
                
                if backbone == 'resnet50':
                    model = maskrcnn_resnet50_fpn(pretrained=False)
                else:
                    # Create custom Mask R-CNN with different backbone
                    model = self._create_custom_maskrcnn(backbone)
                
                return model
                
        except Exception as e:
            self.logger.error(f"Error creating Mask R-CNN architecture: {e}")
            raise
    
    def _create_custom_maskrcnn(self, backbone: str) -> nn.Module:
        """Create custom Mask R-CNN with specified backbone."""
        # This would require more detailed implementation
        # For now, return ResNet50 version
        from torchvision.models.detection import maskrcnn_resnet50_fpn
        return maskrcnn_resnet50_fpn(pretrained=False)


class SOLOAdapter(BaseModelAdapter):
    """Adapter for SOLO (Segmenting Objects by Locations) models."""
    
    def _create_model_architecture(self) -> nn.Module:
        """Create SOLO architecture."""
        try:
            # SOLO implementation would require MMDetection
            # For now, create a placeholder that mimics SOLO structure
            
            class SOLOModel(nn.Module):
                def __init__(self):
                    super().__init__()
                    # Simplified SOLO-like architecture
                    self.backbone = self._create_backbone()
                    self.neck = self._create_fpn()
                    self.head = self._create_solo_head()
                
                def _create_backbone(self):
                    import torchvision.models as models
                    resnet = models.resnet50(pretrained=False)
                    # Remove final layers
                    return nn.Sequential(*list(resnet.children())[:-2])
                
                def _create_fpn(self):
                    # Simplified FPN
                    return nn.Identity()
                
                def _create_solo_head(self):
                    # Simplified SOLO head
                    return nn.Identity()
                
                def forward(self, x):
                    features = self.backbone(x)
                    fpn_features = self.neck(features)
                    output = self.head(fpn_features)
                    return output
            
            return SOLOModel()
            
        except Exception as e:
            self.logger.error(f"Error creating SOLO architecture: {e}")
            raise


class YOLACTAdapter(BaseModelAdapter):
    """Adapter for YOLACT (You Only Look At CoefficienTs) models."""
    
    def _create_model_architecture(self) -> nn.Module:
        """Create YOLACT architecture."""
        try:
            # YOLACT implementation placeholder
            
            class YOLACTModel(nn.Module):
                def __init__(self):
                    super().__init__()
                    self.backbone = self._create_backbone()
                    self.fpn = self._create_fpn()
                    self.prediction_head = self._create_prediction_head()
                    self.protonet = self._create_protonet()
                
                def _create_backbone(self):
                    import torchvision.models as models
                    resnet = models.resnet101(pretrained=False)
                    return nn.Sequential(*list(resnet.children())[:-2])
                
                def _create_fpn(self):
                    return nn.Identity()
                
                def _create_prediction_head(self):
                    return nn.Identity()
                
                def _create_protonet(self):
                    return nn.Identity()
                
                def forward(self, x):
                    backbone_features = self.backbone(x)
                    fpn_features = self.fpn(backbone_features)
                    predictions = self.prediction_head(fpn_features)
                    prototypes = self.protonet(fpn_features)
                    return predictions, prototypes
            
            return YOLACTModel()
            
        except Exception as e:
            self.logger.error(f"Error creating YOLACT architecture: {e}")
            raise


class Mask2FormerAdapter(BaseModelAdapter):
    """Adapter for Mask2Former transformer-based models."""
    
    def _create_model_architecture(self) -> nn.Module:
        """Create Mask2Former architecture."""
        try:
            # Mask2Former implementation placeholder
            
            class Mask2FormerModel(nn.Module):
                def __init__(self):
                    super().__init__()
                    self.backbone = self._create_backbone()
                    self.pixel_decoder = self._create_pixel_decoder()
                    self.transformer_decoder = self._create_transformer_decoder()
                
                def _create_backbone(self):
                    # Use Swin Transformer or ResNet backbone
                    backbone_type = self.config.get('backbone', 'swin_large')
                    if 'swin' in backbone_type:
                        return self._create_swin_backbone()
                    else:
                        return self._create_resnet_backbone()
                
                def _create_swin_backbone(self):
                    # Simplified Swin Transformer
                    return nn.Identity()
                
                def _create_resnet_backbone(self):
                    import torchvision.models as models
                    resnet = models.resnet50(pretrained=False)
                    return nn.Sequential(*list(resnet.children())[:-2])
                
                def _create_pixel_decoder(self):
                    return nn.Identity()
                
                def _create_transformer_decoder(self):
                    return nn.Identity()
                
                def forward(self, x):
                    backbone_features = self.backbone(x)
                    pixel_features = self.pixel_decoder(backbone_features)
                    mask_predictions = self.transformer_decoder(pixel_features)
                    return mask_predictions
            
            return Mask2FormerModel()
            
        except Exception as e:
            self.logger.error(f"Error creating Mask2Former architecture: {e}")
            raise


class DETRAdapter(BaseModelAdapter):
    """Adapter for DETR (Detection Transformer) models."""
    
    def _create_model_architecture(self) -> nn.Module:
        """Create DETR architecture."""
        try:
            # DETR implementation placeholder
            
            class DETRModel(nn.Module):
                def __init__(self):
                    super().__init__()
                    self.backbone = self._create_backbone()
                    self.transformer = self._create_transformer()
                    self.class_embed = nn.Linear(256, 91)  # COCO classes
                    self.bbox_embed = nn.Linear(256, 4)
                
                def _create_backbone(self):
                    import torchvision.models as models
                    resnet = models.resnet50(pretrained=False)
                    return nn.Sequential(*list(resnet.children())[:-2])
                
                def _create_transformer(self):
                    return nn.Transformer(d_model=256, nhead=8, num_encoder_layers=6, num_decoder_layers=6)
                
                def forward(self, x):
                    features = self.backbone(x)
                    # Simplified DETR forward pass
                    return features
            
            return DETRModel()
            
        except Exception as e:
            self.logger.error(f"Error creating DETR architecture: {e}")
            raise


class ModelFactory:
    """Factory for creating model adapters."""
    
    @staticmethod
    def create_model_adapter(architecture: str, config: Dict[str, Any]) -> BaseModelAdapter:
        """Create appropriate model adapter based on architecture type."""
        architecture = architecture.lower()
        
        if 'mask_rcnn' in architecture or 'maskrcnn' in architecture:
            return MaskRCNNAdapter(config)
        elif 'solo' in architecture:
            return SOLOAdapter(config)
        elif 'yolact' in architecture:
            return YOLACTAdapter(config)
        elif 'mask2former' in architecture:
            return Mask2FormerAdapter(config)
        elif 'detr' in architecture:
            return DETRAdapter(config)
        else:
            raise ValueError(f"Unsupported architecture: {architecture}")
    
    @staticmethod
    def get_supported_architectures() -> List[str]:
        """Get list of supported architectures."""
        return ['mask_rcnn', 'solo', 'yolact', 'mask2former', 'detr']


class ArchitectureManager(BaseComponent):
    """Handles loading and interfacing with different model architectures."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model_adapters: Dict[str, BaseModelAdapter] = {}
        self.model_configs = config.get('models', {})
        self.checkpoint_directory = config.get('checkpoint_directory', './checkpoints')
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def initialize(self) -> None:
        """Initialize the architecture manager."""
        try:
            # Initialize model adapters from configuration
            for model_name, model_config in self.model_configs.items():
                self._initialize_model_adapter(model_name, model_config)
            
            self._initialized = True
            self.logger.info(f"ArchitectureManager initialized with {len(self.model_adapters)} models")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ArchitectureManager: {e}")
            raise
    
    def _initialize_model_adapter(self, name: str, config: Dict[str, Any]) -> None:
        """Initialize a single model adapter."""
        try:
            architecture = config['architecture']
            adapter = ModelFactory.create_model_adapter(architecture, config)
            self.model_adapters[name] = adapter
            self.logger.info(f"Initialized model adapter: {name} ({architecture})")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize model adapter {name}: {e}")
            raise
    
    def register_model(self, name: str, model_adapter: BaseModelAdapter) -> None:
        """Register a model adapter."""
        self.model_adapters[name] = model_adapter
        self.logger.info(f"Registered model adapter: {name}")
    
    def load_model(self, model_name: str, checkpoint_path: Optional[str] = None) -> torch.nn.Module:
        """Load model from checkpoint."""
        if model_name not in self.model_adapters:
            raise ValueError(f"Model adapter not found: {model_name}")
        
        adapter = self.model_adapters[model_name]
        
        # Use configured checkpoint path if not provided
        if checkpoint_path is None:
            model_config = self.model_configs.get(model_name, {})
            checkpoint_name = model_config.get('checkpoint')
            if checkpoint_name:
                checkpoint_path = Path(self.checkpoint_directory) / checkpoint_name
            else:
                raise ValueError(f"No checkpoint path specified for model: {model_name}")
        
        return adapter.load_model(str(checkpoint_path))
    
    def extract_features(self, model_name: str, input_tensor: torch.Tensor, 
                        layer_names: List[str]) -> Dict[str, torch.Tensor]:
        """Extract features from specified layers."""
        if model_name not in self.model_adapters:
            raise ValueError(f"Model adapter not found: {model_name}")
        
        adapter = self.model_adapters[model_name]
        return adapter.extract_features(input_tensor, layer_names)
    
    def get_layer_names(self, model_name: str) -> List[str]:
        """Get available layer names for a model."""
        if model_name not in self.model_adapters:
            raise ValueError(f"Model adapter not found: {model_name}")
        
        adapter = self.model_adapters[model_name]
        return adapter.get_layer_names()
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names."""
        return list(self.model_adapters.keys())
    
    def get_supported_architectures(self) -> List[str]:
        """Get list of supported architectures."""
        return ModelFactory.get_supported_architectures()
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        if model_name not in self.model_adapters:
            raise ValueError(f"Model adapter not found: {model_name}")
        
        model_config = self.model_configs.get(model_name, {})
        adapter = self.model_adapters[model_name]
        
        return {
            'name': model_name,
            'architecture': model_config.get('architecture', 'unknown'),
            'backbone': model_config.get('backbone', 'unknown'),
            'config_file': model_config.get('config_file', 'unknown'),
            'checkpoint': model_config.get('checkpoint', 'unknown'),
            'available_layers': len(adapter.get_layer_names()) if adapter.model else 0,
            'loaded': adapter.model is not None
        }
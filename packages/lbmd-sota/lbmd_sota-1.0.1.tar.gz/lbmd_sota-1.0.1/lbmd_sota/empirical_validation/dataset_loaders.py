"""
Dataset abstraction layer and loaders for unified dataset interface.
Supports COCO, Cityscapes, Pascal VOC, medical imaging, and autonomous driving datasets.
"""

import os
import json
import torch
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from PIL import Image
import torchvision.transforms as transforms
from torch.utils.data import Dataset, DataLoader
import logging

from ..core.interfaces import DatasetInterface
from ..core.data_models import ExperimentConfig


class BaseDatasetLoader(DatasetInterface):
    """Base class for all dataset loaders with common functionality."""
    
    def __init__(self, root: str, split: str = "train", transform: Optional[transforms.Compose] = None):
        """Initialize base dataset loader.
        
        Args:
            root: Root directory of the dataset
            split: Dataset split (train/val/test)
            transform: Optional image transformations
        """
        self.root = Path(root)
        self.split = split
        self.transform = transform or self._get_default_transform()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Common attributes
        self.images = []
        self.annotations = []
        self.categories = {}
        self.metadata = {}
        
        # Validation flags
        self._validated = False
        self._loaded = False
    
    def _get_default_transform(self) -> transforms.Compose:
        """Get default image transformations."""
        return transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    
    def validate_format(self) -> bool:
        """Validate dataset format compatibility."""
        if self._validated:
            return True
            
        try:
            # Check if root directory exists
            if not self.root.exists():
                self.logger.error(f"Dataset root directory does not exist: {self.root}")
                return False
            
            # Perform dataset-specific validation
            self._validate_dataset_structure()
            self._validated = True
            self.logger.info(f"Dataset validation passed for {self.__class__.__name__}")
            return True
            
        except Exception as e:
            self.logger.error(f"Dataset validation failed: {e}")
            return False
    
    def _validate_dataset_structure(self) -> None:
        """Validate dataset-specific structure. Override in subclasses."""
        pass
    
    def _load_annotations(self) -> None:
        """Load annotations. Override in subclasses."""
        pass
    
    def _preprocess_image(self, image_path: str) -> torch.Tensor:
        """Preprocess image with validation and error handling."""
        try:
            image = Image.open(image_path).convert('RGB')
            if self.transform:
                image = self.transform(image)
            return image
        except Exception as e:
            self.logger.error(f"Error preprocessing image {image_path}: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics."""
        if not self._loaded:
            self.load_data(self.split)
        
        return {
            'num_images': len(self.images),
            'num_annotations': len(self.annotations),
            'num_categories': len(self.categories),
            'split': self.split,
            'root': str(self.root)
        }


class COCODatasetLoader(BaseDatasetLoader):
    """COCO dataset loader with instance segmentation support."""
    
    def __init__(self, root: str, split: str = "train", transform: Optional[transforms.Compose] = None):
        super().__init__(root, split, transform)
        self.annotation_file = None
        self.coco_data = None
    
    def _validate_dataset_structure(self) -> None:
        """Validate COCO dataset structure."""
        # Check for required directories
        images_dir = self.root / f"{self.split}2017"
        annotations_dir = self.root / "annotations"
        
        if not images_dir.exists():
            raise FileNotFoundError(f"COCO images directory not found: {images_dir}")
        
        if not annotations_dir.exists():
            raise FileNotFoundError(f"COCO annotations directory not found: {annotations_dir}")
        
        # Check for annotation file
        self.annotation_file = annotations_dir / f"instances_{self.split}2017.json"
        if not self.annotation_file.exists():
            raise FileNotFoundError(f"COCO annotation file not found: {self.annotation_file}")
    
    def load_data(self, split: str = "train") -> Dict[str, Any]:
        """Load COCO dataset split with standardized format."""
        self.split = split
        
        if not self.validate_format():
            raise ValueError("Dataset validation failed")
        
        try:
            # Load COCO annotations
            with open(self.annotation_file, 'r') as f:
                self.coco_data = json.load(f)
            
            # Process images
            self.images = []
            image_id_to_path = {}
            
            for img_info in self.coco_data['images']:
                img_path = self.root / f"{self.split}2017" / img_info['file_name']
                if img_path.exists():
                    self.images.append({
                        'id': img_info['id'],
                        'path': str(img_path),
                        'width': img_info['width'],
                        'height': img_info['height'],
                        'file_name': img_info['file_name']
                    })
                    image_id_to_path[img_info['id']] = len(self.images) - 1
            
            # Process annotations
            self.annotations = []
            for ann in self.coco_data['annotations']:
                if ann['image_id'] in image_id_to_path:
                    self.annotations.append({
                        'image_id': ann['image_id'],
                        'category_id': ann['category_id'],
                        'bbox': ann['bbox'],
                        'segmentation': ann['segmentation'],
                        'area': ann['area'],
                        'iscrowd': ann['iscrowd']
                    })
            
            # Process categories
            self.categories = {cat['id']: cat['name'] for cat in self.coco_data['categories']}
            
            self._loaded = True
            self.logger.info(f"Loaded COCO {split} split: {len(self.images)} images, {len(self.annotations)} annotations")
            
            return {
                'images': self.images,
                'annotations': self.annotations,
                'categories': self.categories,
                'metadata': self.metadata
            }
            
        except Exception as e:
            self.logger.error(f"Error loading COCO dataset: {e}")
            raise
    
    def get_sample(self, index: int) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """Get a single sample with image and annotations."""
        if not self._loaded:
            self.load_data(self.split)
        
        if index >= len(self.images):
            raise IndexError(f"Index {index} out of range for {len(self.images)} images")
        
        # Load image
        image_info = self.images[index]
        image = self._preprocess_image(image_info['path'])
        
        # Get annotations for this image
        image_annotations = [ann for ann in self.annotations if ann['image_id'] == image_info['id']]
        
        annotation_data = {
            'image_id': image_info['id'],
            'image_info': image_info,
            'annotations': image_annotations,
            'categories': self.categories
        }
        
        return image, annotation_data


class CityscapesDatasetLoader(BaseDatasetLoader):
    """Cityscapes dataset loader for urban scene segmentation."""
    
    def __init__(self, root: str, split: str = "train", transform: Optional[transforms.Compose] = None):
        super().__init__(root, split, transform)
        self.fine_annotations = True  # Use fine annotations by default
    
    def _validate_dataset_structure(self) -> None:
        """Validate Cityscapes dataset structure."""
        # Check for required directories
        images_dir = self.root / "leftImg8bit" / self.split
        annotations_dir = self.root / "gtFine" / self.split
        
        if not images_dir.exists():
            raise FileNotFoundError(f"Cityscapes images directory not found: {images_dir}")
        
        if not annotations_dir.exists():
            raise FileNotFoundError(f"Cityscapes annotations directory not found: {annotations_dir}")
    
    def load_data(self, split: str = "train") -> Dict[str, Any]:
        """Load Cityscapes dataset split with standardized format."""
        self.split = split
        
        if not self.validate_format():
            raise ValueError("Dataset validation failed")
        
        try:
            images_dir = self.root / "leftImg8bit" / self.split
            annotations_dir = self.root / "gtFine" / self.split
            
            self.images = []
            self.annotations = []
            
            # Process each city directory
            for city_dir in images_dir.iterdir():
                if not city_dir.is_dir():
                    continue
                
                city_name = city_dir.name
                city_ann_dir = annotations_dir / city_name
                
                if not city_ann_dir.exists():
                    continue
                
                # Process images in this city
                for img_path in city_dir.glob("*_leftImg8bit.png"):
                    # Find corresponding annotation files
                    base_name = img_path.stem.replace("_leftImg8bit", "")
                    
                    # Instance segmentation annotation
                    instance_ann_path = city_ann_dir / f"{base_name}_gtFine_instanceIds.png"
                    label_ann_path = city_ann_dir / f"{base_name}_gtFine_labelIds.png"
                    
                    if instance_ann_path.exists() and label_ann_path.exists():
                        img_id = len(self.images)
                        
                        self.images.append({
                            'id': img_id,
                            'path': str(img_path),
                            'city': city_name,
                            'file_name': img_path.name
                        })
                        
                        self.annotations.append({
                            'image_id': img_id,
                            'instance_path': str(instance_ann_path),
                            'label_path': str(label_ann_path),
                            'city': city_name
                        })
            
            # Load Cityscapes categories
            self.categories = self._get_cityscapes_categories()
            
            self._loaded = True
            self.logger.info(f"Loaded Cityscapes {split} split: {len(self.images)} images")
            
            return {
                'images': self.images,
                'annotations': self.annotations,
                'categories': self.categories,
                'metadata': self.metadata
            }
            
        except Exception as e:
            self.logger.error(f"Error loading Cityscapes dataset: {e}")
            raise
    
    def get_sample(self, index: int) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """Get a single sample with image and annotations."""
        if not self._loaded:
            self.load_data(self.split)
        
        if index >= len(self.images):
            raise IndexError(f"Index {index} out of range for {len(self.images)} images")
        
        # Load image
        image_info = self.images[index]
        image = self._preprocess_image(image_info['path'])
        
        # Load annotation masks
        annotation_info = self.annotations[index]
        instance_mask = np.array(Image.open(annotation_info['instance_path']))
        label_mask = np.array(Image.open(annotation_info['label_path']))
        
        annotation_data = {
            'image_id': image_info['id'],
            'image_info': image_info,
            'instance_mask': instance_mask,
            'label_mask': label_mask,
            'categories': self.categories
        }
        
        return image, annotation_data
    
    def _get_cityscapes_categories(self) -> Dict[int, str]:
        """Get Cityscapes category mapping."""
        return {
            0: 'unlabeled', 1: 'ego vehicle', 2: 'rectification border',
            3: 'out of roi', 4: 'static', 5: 'dynamic', 6: 'ground',
            7: 'road', 8: 'sidewalk', 9: 'parking', 10: 'rail track',
            11: 'building', 12: 'wall', 13: 'fence', 14: 'guard rail',
            15: 'bridge', 16: 'tunnel', 17: 'pole', 18: 'polegroup',
            19: 'traffic light', 20: 'traffic sign', 21: 'vegetation',
            22: 'terrain', 23: 'sky', 24: 'person', 25: 'rider',
            26: 'car', 27: 'truck', 28: 'bus', 29: 'caravan',
            30: 'trailer', 31: 'train', 32: 'motorcycle', 33: 'bicycle'
        }


class PascalVOCDatasetLoader(BaseDatasetLoader):
    """Pascal VOC dataset loader with segmentation support."""
    
    def __init__(self, root: str, split: str = "train", year: str = "2012", 
                 transform: Optional[transforms.Compose] = None):
        super().__init__(root, split, transform)
        self.year = year
    
    def _validate_dataset_structure(self) -> None:
        """Validate Pascal VOC dataset structure."""
        voc_dir = self.root / f"VOC{self.year}"
        
        # Check for required directories
        images_dir = voc_dir / "JPEGImages"
        annotations_dir = voc_dir / "Annotations"
        segmentation_dir = voc_dir / "SegmentationObject"
        imagesets_dir = voc_dir / "ImageSets" / "Segmentation"
        
        if not images_dir.exists():
            raise FileNotFoundError(f"Pascal VOC images directory not found: {images_dir}")
        
        if not segmentation_dir.exists():
            raise FileNotFoundError(f"Pascal VOC segmentation directory not found: {segmentation_dir}")
        
        if not imagesets_dir.exists():
            raise FileNotFoundError(f"Pascal VOC imagesets directory not found: {imagesets_dir}")
        
        # Check for split file
        split_file = imagesets_dir / f"{self.split}.txt"
        if not split_file.exists():
            raise FileNotFoundError(f"Pascal VOC split file not found: {split_file}")
    
    def load_data(self, split: str = "train") -> Dict[str, Any]:
        """Load Pascal VOC dataset split with standardized format."""
        self.split = split
        
        if not self.validate_format():
            raise ValueError("Dataset validation failed")
        
        try:
            voc_dir = self.root / f"VOC{self.year}"
            images_dir = voc_dir / "JPEGImages"
            segmentation_dir = voc_dir / "SegmentationObject"
            imagesets_dir = voc_dir / "ImageSets" / "Segmentation"
            
            # Load image IDs from split file
            split_file = imagesets_dir / f"{self.split}.txt"
            with open(split_file, 'r') as f:
                image_ids = [line.strip() for line in f.readlines()]
            
            self.images = []
            self.annotations = []
            
            for img_id in image_ids:
                img_path = images_dir / f"{img_id}.jpg"
                seg_path = segmentation_dir / f"{img_id}.png"
                
                if img_path.exists() and seg_path.exists():
                    self.images.append({
                        'id': len(self.images),
                        'path': str(img_path),
                        'file_name': f"{img_id}.jpg",
                        'image_id': img_id
                    })
                    
                    self.annotations.append({
                        'image_id': len(self.images) - 1,
                        'segmentation_path': str(seg_path),
                        'pascal_id': img_id
                    })
            
            # Load Pascal VOC categories
            self.categories = self._get_pascal_categories()
            
            self._loaded = True
            self.logger.info(f"Loaded Pascal VOC {split} split: {len(self.images)} images")
            
            return {
                'images': self.images,
                'annotations': self.annotations,
                'categories': self.categories,
                'metadata': self.metadata
            }
            
        except Exception as e:
            self.logger.error(f"Error loading Pascal VOC dataset: {e}")
            raise
    
    def get_sample(self, index: int) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """Get a single sample with image and annotations."""
        if not self._loaded:
            self.load_data(self.split)
        
        if index >= len(self.images):
            raise IndexError(f"Index {index} out of range for {len(self.images)} images")
        
        # Load image
        image_info = self.images[index]
        image = self._preprocess_image(image_info['path'])
        
        # Load segmentation mask
        annotation_info = self.annotations[index]
        segmentation_mask = np.array(Image.open(annotation_info['segmentation_path']))
        
        annotation_data = {
            'image_id': image_info['id'],
            'image_info': image_info,
            'segmentation_mask': segmentation_mask,
            'categories': self.categories
        }
        
        return image, annotation_data
    
    def _get_pascal_categories(self) -> Dict[int, str]:
        """Get Pascal VOC category mapping."""
        return {
            0: 'background', 1: 'aeroplane', 2: 'bicycle', 3: 'bird',
            4: 'boat', 5: 'bottle', 6: 'bus', 7: 'car', 8: 'cat',
            9: 'chair', 10: 'cow', 11: 'diningtable', 12: 'dog',
            13: 'horse', 14: 'motorbike', 15: 'person', 16: 'pottedplant',
            17: 'sheep', 18: 'sofa', 19: 'train', 20: 'tvmonitor'
        }


class MedicalImagingDatasetLoader(BaseDatasetLoader):
    """Medical imaging dataset loader for specialized medical datasets."""
    
    def __init__(self, root: str, split: str = "train", dataset_type: str = "generic",
                 transform: Optional[transforms.Compose] = None):
        super().__init__(root, split, transform)
        self.dataset_type = dataset_type
    
    def _validate_dataset_structure(self) -> None:
        """Validate medical imaging dataset structure."""
        # Check for images and masks directories
        images_dir = self.root / "images" / self.split
        masks_dir = self.root / "masks" / self.split
        
        if not images_dir.exists():
            raise FileNotFoundError(f"Medical imaging images directory not found: {images_dir}")
        
        if not masks_dir.exists():
            raise FileNotFoundError(f"Medical imaging masks directory not found: {masks_dir}")
    
    def load_data(self, split: str = "train") -> Dict[str, Any]:
        """Load medical imaging dataset split with standardized format."""
        self.split = split
        
        if not self.validate_format():
            raise ValueError("Dataset validation failed")
        
        try:
            images_dir = self.root / "images" / self.split
            masks_dir = self.root / "masks" / self.split
            
            self.images = []
            self.annotations = []
            
            # Process image files
            for img_path in images_dir.glob("*"):
                if img_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.tiff', '.dcm']:
                    # Find corresponding mask
                    mask_path = masks_dir / f"{img_path.stem}_mask{img_path.suffix}"
                    if not mask_path.exists():
                        mask_path = masks_dir / f"{img_path.stem}.png"
                    
                    if mask_path.exists():
                        self.images.append({
                            'id': len(self.images),
                            'path': str(img_path),
                            'file_name': img_path.name,
                            'modality': self._detect_modality(img_path.name)
                        })
                        
                        self.annotations.append({
                            'image_id': len(self.images) - 1,
                            'mask_path': str(mask_path),
                            'dataset_type': self.dataset_type
                        })
            
            # Load medical categories (generic for now)
            self.categories = self._get_medical_categories()
            
            self._loaded = True
            self.logger.info(f"Loaded medical imaging {split} split: {len(self.images)} images")
            
            return {
                'images': self.images,
                'annotations': self.annotations,
                'categories': self.categories,
                'metadata': self.metadata
            }
            
        except Exception as e:
            self.logger.error(f"Error loading medical imaging dataset: {e}")
            raise
    
    def get_sample(self, index: int) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """Get a single sample with image and annotations."""
        if not self._loaded:
            self.load_data(self.split)
        
        if index >= len(self.images):
            raise IndexError(f"Index {index} out of range for {len(self.images)} images")
        
        # Load image
        image_info = self.images[index]
        image = self._preprocess_medical_image(image_info['path'])
        
        # Load mask
        annotation_info = self.annotations[index]
        mask = np.array(Image.open(annotation_info['mask_path']))
        
        annotation_data = {
            'image_id': image_info['id'],
            'image_info': image_info,
            'mask': mask,
            'categories': self.categories,
            'modality': image_info['modality']
        }
        
        return image, annotation_data
    
    def _preprocess_medical_image(self, image_path: str) -> torch.Tensor:
        """Preprocess medical image with specialized handling."""
        try:
            # Handle different medical image formats
            if image_path.endswith('.dcm'):
                # DICOM handling would require pydicom
                # For now, treat as regular image
                pass
            
            image = Image.open(image_path)
            
            # Convert grayscale to RGB if needed
            if image.mode == 'L':
                image = image.convert('RGB')
            elif image.mode == 'RGBA':
                image = image.convert('RGB')
            
            if self.transform:
                image = self.transform(image)
            
            return image
            
        except Exception as e:
            self.logger.error(f"Error preprocessing medical image {image_path}: {e}")
            raise
    
    def _detect_modality(self, filename: str) -> str:
        """Detect medical imaging modality from filename."""
        filename_lower = filename.lower()
        
        if 'ct' in filename_lower:
            return 'CT'
        elif 'mri' in filename_lower or 'mr' in filename_lower:
            return 'MRI'
        elif 'xray' in filename_lower or 'x-ray' in filename_lower:
            return 'X-Ray'
        elif 'ultrasound' in filename_lower or 'us' in filename_lower:
            return 'Ultrasound'
        else:
            return 'Unknown'
    
    def _get_medical_categories(self) -> Dict[int, str]:
        """Get medical imaging category mapping."""
        return {
            0: 'background',
            1: 'organ',
            2: 'lesion',
            3: 'tumor',
            4: 'bone',
            5: 'tissue'
        }


class AutonomousDrivingDatasetLoader(BaseDatasetLoader):
    """Autonomous driving dataset loader for specialized driving datasets."""
    
    def __init__(self, root: str, split: str = "train", dataset_type: str = "generic",
                 transform: Optional[transforms.Compose] = None):
        super().__init__(root, split, transform)
        self.dataset_type = dataset_type
    
    def _validate_dataset_structure(self) -> None:
        """Validate autonomous driving dataset structure."""
        # Check for images and annotations directories
        images_dir = self.root / "images" / self.split
        annotations_dir = self.root / "annotations" / self.split
        
        if not images_dir.exists():
            raise FileNotFoundError(f"Autonomous driving images directory not found: {images_dir}")
        
        if not annotations_dir.exists():
            raise FileNotFoundError(f"Autonomous driving annotations directory not found: {annotations_dir}")
    
    def load_data(self, split: str = "train") -> Dict[str, Any]:
        """Load autonomous driving dataset split with standardized format."""
        self.split = split
        
        if not self.validate_format():
            raise ValueError("Dataset validation failed")
        
        try:
            images_dir = self.root / "images" / self.split
            annotations_dir = self.root / "annotations" / self.split
            
            self.images = []
            self.annotations = []
            
            # Process image files
            for img_path in images_dir.glob("*"):
                if img_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                    # Find corresponding annotation
                    ann_path = annotations_dir / f"{img_path.stem}.json"
                    
                    if ann_path.exists():
                        self.images.append({
                            'id': len(self.images),
                            'path': str(img_path),
                            'file_name': img_path.name,
                            'scene_type': self._detect_scene_type(img_path.name)
                        })
                        
                        # Load annotation data
                        with open(ann_path, 'r') as f:
                            ann_data = json.load(f)
                        
                        self.annotations.append({
                            'image_id': len(self.images) - 1,
                            'annotation_path': str(ann_path),
                            'annotation_data': ann_data,
                            'dataset_type': self.dataset_type
                        })
            
            # Load autonomous driving categories
            self.categories = self._get_driving_categories()
            
            self._loaded = True
            self.logger.info(f"Loaded autonomous driving {split} split: {len(self.images)} images")
            
            return {
                'images': self.images,
                'annotations': self.annotations,
                'categories': self.categories,
                'metadata': self.metadata
            }
            
        except Exception as e:
            self.logger.error(f"Error loading autonomous driving dataset: {e}")
            raise
    
    def get_sample(self, index: int) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """Get a single sample with image and annotations."""
        if not self._loaded:
            self.load_data(self.split)
        
        if index >= len(self.images):
            raise IndexError(f"Index {index} out of range for {len(self.images)} images")
        
        # Load image
        image_info = self.images[index]
        image = self._preprocess_image(image_info['path'])
        
        # Get annotation data
        annotation_info = self.annotations[index]
        
        annotation_data = {
            'image_id': image_info['id'],
            'image_info': image_info,
            'annotation_data': annotation_info['annotation_data'],
            'categories': self.categories,
            'scene_type': image_info['scene_type']
        }
        
        return image, annotation_data
    
    def _detect_scene_type(self, filename: str) -> str:
        """Detect scene type from filename."""
        filename_lower = filename.lower()
        
        if 'highway' in filename_lower:
            return 'highway'
        elif 'urban' in filename_lower or 'city' in filename_lower:
            return 'urban'
        elif 'rural' in filename_lower or 'country' in filename_lower:
            return 'rural'
        elif 'parking' in filename_lower:
            return 'parking'
        else:
            return 'unknown'
    
    def _get_driving_categories(self) -> Dict[int, str]:
        """Get autonomous driving category mapping."""
        return {
            0: 'background', 1: 'road', 2: 'sidewalk', 3: 'building',
            4: 'wall', 5: 'fence', 6: 'pole', 7: 'traffic_light',
            8: 'traffic_sign', 9: 'vegetation', 10: 'terrain',
            11: 'sky', 12: 'person', 13: 'rider', 14: 'car',
            15: 'truck', 16: 'bus', 17: 'train', 18: 'motorcycle',
            19: 'bicycle', 20: 'pedestrian', 21: 'vehicle'
        }


class DatasetFactory:
    """Factory class for creating dataset loaders."""
    
    @staticmethod
    def create_dataset_loader(dataset_type: str, root: str, split: str = "train", 
                            **kwargs) -> DatasetInterface:
        """Create appropriate dataset loader based on type.
        
        Args:
            dataset_type: Type of dataset (coco, cityscapes, pascal_voc, medical, autonomous_driving)
            root: Root directory of the dataset
            split: Dataset split
            **kwargs: Additional arguments for specific loaders
        
        Returns:
            DatasetInterface: Appropriate dataset loader instance
        """
        dataset_type = dataset_type.lower()
        
        if dataset_type == 'coco':
            return COCODatasetLoader(root, split, **kwargs)
        elif dataset_type == 'cityscapes':
            return CityscapesDatasetLoader(root, split, **kwargs)
        elif dataset_type == 'pascal_voc':
            return PascalVOCDatasetLoader(root, split, **kwargs)
        elif dataset_type == 'medical':
            return MedicalImagingDatasetLoader(root, split, **kwargs)
        elif dataset_type == 'autonomous_driving':
            return AutonomousDrivingDatasetLoader(root, split, **kwargs)
        else:
            raise ValueError(f"Unsupported dataset type: {dataset_type}")
    
    @staticmethod
    def get_supported_datasets() -> List[str]:
        """Get list of supported dataset types."""
        return ['coco', 'cityscapes', 'pascal_voc', 'medical', 'autonomous_driving']


class DataValidationPipeline:
    """Pipeline for validating and preprocessing data across different datasets."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize data validation pipeline."""
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Validation parameters
        self.min_image_size = self.config.get('min_image_size', (32, 32))
        self.max_image_size = self.config.get('max_image_size', (4096, 4096))
        self.supported_formats = self.config.get('supported_formats', ['.jpg', '.jpeg', '.png', '.tiff'])
        
    def validate_dataset(self, dataset_loader: DatasetInterface) -> Dict[str, Any]:
        """Validate entire dataset and return validation report."""
        validation_report = {
            'dataset_type': dataset_loader.__class__.__name__,
            'total_samples': 0,
            'valid_samples': 0,
            'invalid_samples': 0,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        try:
            # Load dataset
            data = dataset_loader.load_data()
            validation_report['total_samples'] = len(data['images'])
            
            # Validate each sample
            for i in range(len(data['images'])):
                try:
                    image, annotation = dataset_loader.get_sample(i)
                    
                    # Validate image
                    if self._validate_image(image):
                        validation_report['valid_samples'] += 1
                    else:
                        validation_report['invalid_samples'] += 1
                        validation_report['errors'].append(f"Invalid image at index {i}")
                        
                except Exception as e:
                    validation_report['invalid_samples'] += 1
                    validation_report['errors'].append(f"Error processing sample {i}: {str(e)}")
            
            # Compute statistics
            validation_report['statistics'] = self._compute_dataset_statistics(dataset_loader)
            
            self.logger.info(f"Dataset validation completed: {validation_report['valid_samples']}/{validation_report['total_samples']} valid samples")
            
        except Exception as e:
            validation_report['errors'].append(f"Dataset validation failed: {str(e)}")
            self.logger.error(f"Dataset validation failed: {e}")
        
        return validation_report
    
    def _validate_image(self, image: torch.Tensor) -> bool:
        """Validate individual image tensor."""
        try:
            # Check tensor properties
            if not isinstance(image, torch.Tensor):
                return False
            
            # Check dimensions
            if len(image.shape) != 3:  # Should be (C, H, W)
                return False
            
            c, h, w = image.shape
            
            # Check size constraints
            if h < self.min_image_size[0] or w < self.min_image_size[1]:
                return False
            
            if h > self.max_image_size[0] or w > self.max_image_size[1]:
                return False
            
            # Check for valid pixel values
            if torch.isnan(image).any() or torch.isinf(image).any():
                return False
            
            return True
            
        except Exception:
            return False
    
    def _compute_dataset_statistics(self, dataset_loader: DatasetInterface) -> Dict[str, Any]:
        """Compute dataset statistics."""
        try:
            stats = dataset_loader.get_statistics()
            
            # Add additional statistics
            stats['validation_timestamp'] = torch.utils.data.get_worker_info()
            stats['loader_type'] = dataset_loader.__class__.__name__
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error computing dataset statistics: {e}")
            return {}


# Preprocessing pipelines for different dataset types
class PreprocessingPipelines:
    """Collection of preprocessing pipelines for different dataset types."""
    
    @staticmethod
    def get_coco_transform(train: bool = True) -> transforms.Compose:
        """Get COCO preprocessing pipeline."""
        if train:
            return transforms.Compose([
                transforms.RandomHorizontalFlip(0.5),
                transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
        else:
            return transforms.Compose([
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
    
    @staticmethod
    def get_cityscapes_transform(train: bool = True) -> transforms.Compose:
        """Get Cityscapes preprocessing pipeline."""
        if train:
            return transforms.Compose([
                transforms.RandomHorizontalFlip(0.5),
                transforms.RandomCrop((512, 1024)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
        else:
            return transforms.Compose([
                transforms.Resize((512, 1024)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
    
    @staticmethod
    def get_medical_transform(train: bool = True) -> transforms.Compose:
        """Get medical imaging preprocessing pipeline."""
        if train:
            return transforms.Compose([
                transforms.RandomRotation(10),
                transforms.RandomHorizontalFlip(0.5),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.5], std=[0.5])  # Normalize to [-1, 1] for medical images
            ])
        else:
            return transforms.Compose([
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.5], std=[0.5])
            ])
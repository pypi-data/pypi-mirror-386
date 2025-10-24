"""
Multiple manifold learning methods for LBMD ablation studies.
"""

try:
    import numpy as np
    import torch
    from typing import Dict, Any, Optional, Tuple, List
    from abc import ABC, abstractmethod
    import logging

    # Manifold learning imports
    from sklearn.manifold import TSNE, Isomap, LocallyLinearEmbedding, SpectralEmbedding
    from sklearn.decomposition import PCA, KernelPCA
    from sklearn.preprocessing import StandardScaler
    import umap

    try:
        from ..core.interfaces import ManifoldLearnerInterface
        print("ManifoldLearnerInterface imported successfully")
    except Exception as e:
        print(f"Failed to import ManifoldLearnerInterface: {e}")
        # Fallback to absolute import
        from lbmd_sota.core.interfaces import ManifoldLearnerInterface
        print("ManifoldLearnerInterface imported with absolute path")
    
    print("All imports successful in manifold_learners.py")
    
except Exception as e:
    print(f"Import error in manifold_learners.py: {e}")
    import traceback
    traceback.print_exc()
    raise


class BaseManifoldLearner(ManifoldLearnerInterface):
    """Base class for manifold learning algorithms."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.embedding_model = None
    
    @abstractmethod
    def fit_transform(self, features: torch.Tensor) -> np.ndarray:
        """Fit the manifold learner and transform features."""
        pass
    
    @abstractmethod
    def transform(self, features: torch.Tensor) -> np.ndarray:
        """Transform features using fitted manifold learner."""
        pass
    
    def _prepare_features(self, features: torch.Tensor) -> np.ndarray:
        """Prepare features for manifold learning."""
        if features.dim() == 4:  # Batch dimension
            features = features.squeeze(0)
        
        # Convert to numpy
        if isinstance(features, torch.Tensor):
            features_np = features.detach().cpu().numpy()
        else:
            features_np = features
        
        # Flatten spatial dimensions, keep channel dimension
        # Shape: (channels, height, width) -> (height*width, channels)
        features_flat = features_np.transpose(1, 2, 0).reshape(-1, features_np.shape[0])
        
        return features_flat
    
    def _get_original_shape(self, features: torch.Tensor) -> Tuple[int, ...]:
        """Get original spatial shape for reshaping embeddings."""
        if features.dim() == 4:  # Batch dimension
            return features.shape[2:]
        else:
            return features.shape[1:]


class UMAPLearner(BaseManifoldLearner):
    """UMAP (Uniform Manifold Approximation and Projection) manifold learner."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.n_components = self.config.get('n_components', 2)
        self.n_neighbors = self.config.get('n_neighbors', 15)
        self.min_dist = self.config.get('min_dist', 0.1)
        self.metric = self.config.get('metric', 'euclidean')
        self.random_state = self.config.get('random_state', 42)
        self.n_jobs = self.config.get('n_jobs', -1)
    
    def fit_transform(self, features: torch.Tensor) -> np.ndarray:
        """Fit UMAP and transform features."""
        # Prepare features
        features_flat = self._prepare_features(features)
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features_flat)
        
        # Initialize and fit UMAP
        self.embedding_model = umap.UMAP(
            n_components=self.n_components,
            n_neighbors=self.n_neighbors,
            min_dist=self.min_dist,
            metric=self.metric,
            random_state=self.random_state,
            n_jobs=self.n_jobs
        )
        
        # Fit and transform
        embedding = self.embedding_model.fit_transform(features_scaled)
        self.is_fitted = True
        
        self.logger.info(f"UMAP embedding computed with shape: {embedding.shape}")
        return embedding
    
    def transform(self, features: torch.Tensor) -> np.ndarray:
        """Transform new features using fitted UMAP."""
        if not self.is_fitted:
            raise ValueError("UMAP model must be fitted before transform")
        
        # Prepare features
        features_flat = self._prepare_features(features)
        features_scaled = self.scaler.transform(features_flat)
        
        # Transform
        embedding = self.embedding_model.transform(features_scaled)
        return embedding


class PCALearner(BaseManifoldLearner):
    """PCA (Principal Component Analysis) manifold learner."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.n_components = self.config.get('n_components', 2)
        self.whiten = self.config.get('whiten', False)
        self.random_state = self.config.get('random_state', 42)
    
    def fit_transform(self, features: torch.Tensor) -> np.ndarray:
        """Fit PCA and transform features."""
        # Prepare features
        features_flat = self._prepare_features(features)
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features_flat)
        
        # Initialize and fit PCA
        self.embedding_model = PCA(
            n_components=self.n_components,
            whiten=self.whiten,
            random_state=self.random_state
        )
        
        # Fit and transform
        embedding = self.embedding_model.fit_transform(features_scaled)
        self.is_fitted = True
        
        self.logger.info(f"PCA embedding computed with shape: {embedding.shape}")
        self.logger.info(f"Explained variance ratio: {self.embedding_model.explained_variance_ratio_}")
        return embedding
    
    def transform(self, features: torch.Tensor) -> np.ndarray:
        """Transform new features using fitted PCA."""
        if not self.is_fitted:
            raise ValueError("PCA model must be fitted before transform")
        
        # Prepare features
        features_flat = self._prepare_features(features)
        features_scaled = self.scaler.transform(features_flat)
        
        # Transform
        embedding = self.embedding_model.transform(features_scaled)
        return embedding


class ManifoldLearnerFactory:
    """Factory for creating manifold learner instances."""
    
    _learners = {
        'umap': UMAPLearner,
        'pca': PCALearner
    }
    
    @classmethod
    def create_learner(cls, learner_type: str, config: Optional[Dict[str, Any]] = None) -> BaseManifoldLearner:
        """Create a manifold learner instance."""
        if learner_type not in cls._learners:
            raise ValueError(f"Unknown learner type: {learner_type}. "
                           f"Available types: {list(cls._learners.keys())}")
        
        learner_class = cls._learners[learner_type]
        return learner_class(config)
    
    @classmethod
    def get_available_learners(cls) -> List[str]:
        """Get list of available learner types."""
        return list(cls._learners.keys())
    
    @classmethod
    def register_learner(cls, name: str, learner_class: type) -> None:
        """Register a new learner type."""
        if not issubclass(learner_class, BaseManifoldLearner):
            raise ValueError("Learner class must inherit from BaseManifoldLearner")
        cls._learners[name] = learner_class


def compare_manifold_methods(features: torch.Tensor, 
                           methods: List[str],
                           configs: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Dict[str, Any]]:
    """Compare multiple manifold learning methods on the same features."""
    if configs is None:
        configs = {}
    
    results = {}
    
    # Prepare features once
    if features.dim() == 4:
        features = features.squeeze(0)
    
    if isinstance(features, torch.Tensor):
        features_np = features.detach().cpu().numpy()
    else:
        features_np = features
    
    features_flat = features_np.transpose(1, 2, 0).reshape(-1, features_np.shape[0])
    
    for method in methods:
        try:
            # Create learner
            config = configs.get(method, {})
            learner = ManifoldLearnerFactory.create_learner(method, config)
            
            # Fit and transform
            embedding = learner.fit_transform(features)
            
            # Simple quality metrics
            quality_metrics = {
                'embedding_variance': np.var(embedding),
                'embedding_range': np.max(embedding) - np.min(embedding)
            }
            
            results[method] = {
                'embedding': embedding,
                'quality_metrics': quality_metrics,
                'config': config,
                'success': True
            }
            
        except Exception as e:
            results[method] = {
                'embedding': None,
                'quality_metrics': None,
                'config': configs.get(method, {}),
                'success': False,
                'error': str(e)
            }
    
    return results
#!/usr/bin/env python3
"""
Simple Real Images Analysis for LBMD-SOTA

This module provides a simplified interface for analyzing real images
with the LBMD-SOTA framework.
"""

import torch
import numpy as np
from typing import List, Dict, Any
from lbmd_sota.core.analyzer import LBMDAnalyzer
from lbmd_sota.core.config import LBMDConfig


def simple_analyze(model, images: torch.Tensor, 
                  target_layers: List[str],
                  config: LBMDConfig = None) -> Dict[str, Any]:
    """
    Simple analysis function for real images.
    
    Args:
        model: PyTorch model to analyze
        images: Batch of images (B, C, H, W)
        target_layers: List of layer names to analyze
        config: Optional configuration
    
    Returns:
        Analysis results dictionary
    """
    if config is None:
        config = LBMDConfig()
    
    # Initialize analyzer
    analyzer = LBMDAnalyzer(
        model=model,
        target_layers=target_layers,
        k_neurons=config.lbmd_params.get('k_top_neurons', 100),
        epsilon=config.lbmd_params.get('epsilon', 0.1),
        tau=config.lbmd_params.get('tau', 0.5)
    )
    
    # Perform analysis
    results = analyzer.analyze(images)
    
    return results


def analyze_single_image(model, image: torch.Tensor, 
                        target_layers: List[str]) -> Dict[str, Any]:
    """
    Analyze a single image.
    
    Args:
        model: PyTorch model
        image: Single image tensor (C, H, W) or (1, C, H, W)
        target_layers: List of layer names
    
    Returns:
        Analysis results
    """
    # Ensure batch dimension
    if image.dim() == 3:
        image = image.unsqueeze(0)
    
    return simple_analyze(model, image, target_layers)


def batch_analyze(model, images: torch.Tensor, 
                 target_layers: List[str],
                 batch_size: int = 4) -> List[Dict[str, Any]]:
    """
    Analyze a batch of images.
    
    Args:
        model: PyTorch model
        images: Batch of images (N, C, H, W)
        target_layers: List of layer names
        batch_size: Batch size for processing
    
    Returns:
        List of analysis results
    """
    results = []
    num_images = images.shape[0]
    
    for i in range(0, num_images, batch_size):
        end_idx = min(i + batch_size, num_images)
        batch = images[i:end_idx]
        
        batch_results = simple_analyze(model, batch, target_layers)
        results.append(batch_results)
    
    return results


def main():
    """Example usage of simple real images analysis."""
    print("🖼️  Simple Real Images Analysis")
    print("=" * 40)
    
    print("📝 This module provides simplified functions for analyzing real images.")
    print("   Use these functions for quick analysis without complex setup.")
    
    # Example usage
    print(f"\n✅ Available functions:")
    print(f"   - simple_analyze(): Basic analysis function")
    print(f"   - analyze_single_image(): Analyze one image")
    print(f"   - batch_analyze(): Analyze multiple images")
    
    print(f"\n💡 Example usage:")
    print(f"   results = simple_analyze(model, images, ['layer1', 'layer2'])")
    print(f"   single_result = analyze_single_image(model, image, ['layer1'])")
    print(f"   batch_results = batch_analyze(model, images, ['layer1'], batch_size=8)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Real Images Demo for LBMD-SOTA

This module provides a demonstration of LBMD analysis on real images.
"""

import torch
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
from lbmd_sota.core.analyzer import LBMDAnalyzer
from lbmd_sota.core.config import LBMDConfig


class RealImagesDemo:
    """Demo class for real image analysis with LBMD."""
    
    def __init__(self, config: LBMDConfig = None):
        """Initialize the real images demo."""
        self.config = config or LBMDConfig()
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    
    def load_image(self, image_path: str) -> torch.Tensor:
        """Load and preprocess an image."""
        try:
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.transform(image).unsqueeze(0)
            return image_tensor
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return None
    
    def analyze_image(self, model, image_tensor: torch.Tensor, 
                     target_layers: list) -> dict:
        """Analyze a single image with LBMD."""
        analyzer = LBMDAnalyzer(
            model=model,
            target_layers=target_layers,
            k_neurons=self.config.lbmd_params.get('k_top_neurons', 100),
            epsilon=self.config.lbmd_params.get('epsilon', 0.1),
            tau=self.config.lbmd_params.get('tau', 0.5)
        )
        
        results = analyzer.analyze(image_tensor)
        return results
    
    def demo_with_sample_images(self, model, target_layers: list):
        """Run demo with sample images."""
        print("🖼️  Real Images Demo")
        print("=" * 40)
        
        # Create sample images (in practice, you would load real images)
        print("📝 Creating sample images for demonstration...")
        
        # Generate synthetic images for demo
        sample_images = []
        for i in range(3):
            # Create random image tensor
            image = torch.randn(1, 3, 224, 224)
            sample_images.append(image)
            print(f"  ✅ Sample image {i+1} created")
        
        # Analyze each image
        results = []
        for i, image in enumerate(sample_images):
            print(f"\n🔍 Analyzing sample image {i+1}...")
            result = self.analyze_image(model, image, target_layers)
            results.append(result)
            
            # Display results
            success_rate = result['summary_metrics']['success_rate']
            print(f"  📊 Success rate: {success_rate:.2%}")
            
            if success_rate > 0:
                avg_dim = result['summary_metrics'].get('avg_manifold_dimension', 0)
                avg_strength = result['summary_metrics'].get('avg_boundary_strength', 0)
                print(f"  📐 Average manifold dimension: {avg_dim:.2f}")
                print(f"  💪 Average boundary strength: {avg_strength:.2f}")
        
        return results


def main():
    """Main demo function."""
    print("🚀 LBMD-SOTA Real Images Demo")
    print("=" * 50)
    
    # Initialize demo
    config = LBMDConfig()
    demo = RealImagesDemo(config)
    
    print("📝 This demo shows how to analyze real images with LBMD.")
    print("   In practice, you would load actual images from files.")
    
    # Example usage
    print(f"\n✅ Real images demo initialized")
    print(f"   Configuration: {config.experiment_name}")
    print(f"   Target device: {config.device}")
    
    print(f"\n💡 To use with real images:")
    print(f"   1. Load your model")
    print(f"   2. Specify target layers")
    print(f"   3. Load images using demo.load_image()")
    print(f"   4. Analyze with demo.analyze_image()")


if __name__ == "__main__":
    main()

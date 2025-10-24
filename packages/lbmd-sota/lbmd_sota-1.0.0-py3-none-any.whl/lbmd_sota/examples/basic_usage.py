#!/usr/bin/env python3
"""
Basic Usage Example for LBMD-SOTA

This example demonstrates the basic usage of the LBMD-SOTA framework
for analyzing neural network models.
"""

import torch
import torchvision.models as models
from lbmd_sota.core.analyzer import LBMDAnalyzer
from lbmd_sota.visualization.interactive_manifold_explorer import InteractiveManifoldExplorer


def main():
    """Basic usage example."""
    print("🚀 LBMD-SOTA Basic Usage Example")
    print("=" * 50)
    
    # 1. Load a pre-trained model
    print("📦 Loading pre-trained ResNet-50...")
    model = models.resnet50(pretrained=True)
    model.eval()
    
    # 2. Create sample input data
    print("🖼️  Creating sample input data...")
    batch_size = 4
    input_data = torch.randn(batch_size, 3, 224, 224)
    
    # 3. Initialize LBMD analyzer
    print("🔍 Initializing LBMD analyzer...")
    target_layers = ['layer3.5.conv2', 'layer4.2.conv2']  # Deep layers
    analyzer = LBMDAnalyzer(
        model=model,
        target_layers=target_layers,
        k_neurons=50,
        epsilon=0.1,
        tau=0.5
    )
    
    # 4. Perform analysis
    print("🧠 Performing LBMD analysis...")
    results = analyzer.analyze(input_data)
    
    # 5. Display results
    print("\n📊 Analysis Results:")
    print(f"  - Layers analyzed: {len(results['manifold_analysis'])}")
    print(f"  - Success rate: {results['summary_metrics']['success_rate']:.2%}")
    
    if results['summary_metrics']['success_rate'] > 0:
        print(f"  - Average manifold dimension: {results['summary_metrics'].get('avg_manifold_dimension', 'N/A'):.2f}")
        print(f"  - Average boundary strength: {results['summary_metrics'].get('avg_boundary_strength', 'N/A'):.2f}")
    
    # 6. Layer-wise details
    print("\n🔬 Layer-wise Analysis:")
    for layer_name, layer_data in results['manifold_analysis'].items():
        if layer_data.get('analysis_successful', False):
            print(f"  - {layer_name}:")
            print(f"    * Manifold dimension: {layer_data.get('manifold_dimension', 'N/A'):.2f}")
            print(f"    * Boundary strength: {layer_data.get('boundary_strength', 'N/A'):.2f}")
            print(f"    * Number of boundaries: {layer_data.get('num_boundaries', 'N/A')}")
        else:
            print(f"  - {layer_name}: Analysis failed")
    
    print("\n✅ Basic analysis completed successfully!")
    print("\n💡 Next steps:")
    print("  - Try with different models (ViT, Swin, etc.)")
    print("  - Experiment with different target layers")
    print("  - Use the interactive visualization tools")
    print("  - Run comparative analysis with baseline methods")


if __name__ == "__main__":
    main()

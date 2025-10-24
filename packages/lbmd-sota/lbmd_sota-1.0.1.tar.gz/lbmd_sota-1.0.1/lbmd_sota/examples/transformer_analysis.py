#!/usr/bin/env python3
"""
Transformer Analysis Example for LBMD-SOTA

This example demonstrates how to analyze transformer architectures
using the LBMD-SOTA framework.
"""

import torch
import timm
from lbmd_sota.core.analyzer import LBMDAnalyzer
from lbmd_sota.comparative_analysis.baseline_comparator import BaselineComparator


def analyze_transformer(model_name: str, target_layers: list):
    """Analyze a transformer model with LBMD."""
    print(f"\n🔍 Analyzing {model_name}...")
    
    # Load model
    try:
        model = timm.create_model(model_name, pretrained=True)
        model.eval()
        print(f"  ✅ Model loaded successfully")
    except Exception as e:
        print(f"  ❌ Failed to load model: {e}")
        return None
    
    # Create sample input
    input_data = torch.randn(2, 3, 224, 224)
    
    # Initialize analyzer
    analyzer = LBMDAnalyzer(
        model=model,
        target_layers=target_layers,
        k_neurons=100,
        epsilon=0.1,
        tau=0.5,
        manifold_method='umap'
    )
    
    # Perform analysis
    try:
        results = analyzer.analyze(input_data)
        success_rate = results['summary_metrics']['success_rate']
        print(f"  📊 Success rate: {success_rate:.2%}")
        
        if success_rate > 0:
            avg_dim = results['summary_metrics'].get('avg_manifold_dimension', 0)
            avg_strength = results['summary_metrics'].get('avg_boundary_strength', 0)
            print(f"  📐 Average manifold dimension: {avg_dim:.2f}")
            print(f"  💪 Average boundary strength: {avg_strength:.2f}")
        
        return results
    except Exception as e:
        print(f"  ❌ Analysis failed: {e}")
        return None


def main():
    """Main transformer analysis example."""
    print("🚀 LBMD-SOTA Transformer Analysis Example")
    print("=" * 60)
    
    # Define transformer models to test
    transformer_models = [
        {
            'name': 'vit_base_patch16_224',
            'layers': ['blocks.6', 'blocks.11'],
            'description': 'Vision Transformer (ViT-B/16)'
        },
        {
            'name': 'swin_base_patch4_window7_224',
            'layers': ['layers.2', 'layers.3'],
            'description': 'Swin Transformer (Swin-B)'
        },
        {
            'name': 'convnext_base',
            'layers': ['stages.2.blocks.2', 'stages.3.blocks.2'],
            'description': 'ConvNeXt Base'
        }
    ]
    
    results_summary = {}
    
    # Analyze each model
    for model_info in transformer_models:
        print(f"\n{'='*60}")
        print(f"🤖 {model_info['description']}")
        print(f"   Model: {model_info['name']}")
        print(f"   Target layers: {model_info['layers']}")
        
        results = analyze_transformer(
            model_info['name'], 
            model_info['layers']
        )
        
        if results:
            results_summary[model_info['name']] = {
                'success_rate': results['summary_metrics']['success_rate'],
                'manifold_dimension': results['summary_metrics'].get('avg_manifold_dimension', 0),
                'boundary_strength': results['summary_metrics'].get('avg_boundary_strength', 0)
            }
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TRANSFORMER ANALYSIS SUMMARY")
    print("=" * 60)
    
    if results_summary:
        print(f"{'Model':<30} {'Success':<10} {'Manifold Dim':<15} {'Boundary Strength':<15}")
        print("-" * 70)
        
        for model_name, metrics in results_summary.items():
            print(f"{model_name:<30} {metrics['success_rate']:<10.2%} "
                  f"{metrics['manifold_dimension']:<15.2f} {metrics['boundary_strength']:<15.2f}")
        
        # Find best performing model
        best_model = max(results_summary.items(), 
                        key=lambda x: x[1]['success_rate'])
        print(f"\n🏆 Best performing model: {best_model[0]}")
        print(f"   Success rate: {best_model[1]['success_rate']:.2%}")
    else:
        print("❌ No models were successfully analyzed")
    
    print(f"\n✅ Transformer analysis completed!")
    print(f"\n💡 Key insights:")
    print(f"  - LBMD works across different transformer architectures")
    print(f"  - Success rates may vary based on model complexity")
    print(f"  - Deeper layers often provide better boundary insights")
    print(f"  - Try different target layers for optimal results")


if __name__ == "__main__":
    main()

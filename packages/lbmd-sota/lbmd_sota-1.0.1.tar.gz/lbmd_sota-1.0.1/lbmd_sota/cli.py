#!/usr/bin/env python3
"""
LBMD SOTA Framework Command Line Interface

This module provides command-line tools for running LBMD analysis, comparisons,
and demonstrations.
"""

import argparse
import sys
import logging
from pathlib import Path

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LBMD SOTA Framework - Latent Boundary Manifold Decomposition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  lbmd-demo                           # Run interactive demo
  lbmd-analyze --model maskrcnn       # Analyze model
  lbmd-compare --baseline gradcam     # Compare with baseline
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Demo command
    demo_parser = subparsers.add_parser('demo', help='Run interactive demonstration')
    demo_parser.add_argument('--jupyter', action='store_true', help='Run in Jupyter mode')
    demo_parser.add_argument('--output-dir', default='./demo_results', help='Output directory')
    
    # Analyze command  
    analyze_parser = subparsers.add_parser('analyze', help='Analyze model with LBMD')
    analyze_parser.add_argument('--model', required=True, help='Model architecture')
    analyze_parser.add_argument('--dataset', default='synthetic', help='Dataset to use')
    analyze_parser.add_argument('--config', help='Configuration file')
    analyze_parser.add_argument('--output-dir', default='./analysis_results', help='Output directory')
    
    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare LBMD with baselines')
    compare_parser.add_argument('--baseline', action='append', help='Baseline methods to compare')
    compare_parser.add_argument('--model', default='maskrcnn', help='Model architecture')
    compare_parser.add_argument('--output-dir', default='./comparison_results', help='Output directory')
    
    # Global arguments
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--version', action='version', version='lbmd-sota 1.0.0')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if not args.command:
        # Default to demo if no command specified
        args.command = 'demo'
        args.jupyter = False
        args.output_dir = './demo_results'
    
    try:
        if args.command == 'demo':
            run_demo(args)
        elif args.command == 'analyze':
            run_analyze(args)
        elif args.command == 'compare':
            run_compare(args)
        else:
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0

def run_demo(args):
    """Run the interactive demo."""
    print("🚀 Starting LBMD Interactive Demo")
    
    if args.jupyter:
        print("📓 Jupyter mode not yet implemented")
        print("   Running standalone demo instead...")
    
    # Import and run the working demo
    try:
        from . import examples
        examples.run_interactive_demo(args.output_dir)
    except ImportError:
        # Fallback to standalone demo
        print("📝 Running standalone demo...")
        import subprocess
        result = subprocess.run([sys.executable, 'standalone_interactive_demo.py'], 
                              capture_output=False)
        return result.returncode

def run_analyze(args):
    """Run LBMD analysis."""
    print(f"🔍 Analyzing model: {args.model}")
    print(f"📊 Dataset: {args.dataset}")
    print(f"📁 Output: {args.output_dir}")
    
    from lbmd_sota import LBMDConfig, MultiDatasetEvaluator, get_config_template
    
    # Load or create configuration
    if args.config:
        config = LBMDConfig.from_file(args.config)
    else:
        config_dict = get_config_template()
        config_dict['models']['architecture'] = args.model
        config_dict['visualization']['output_dir'] = args.output_dir
        config = LBMDConfig(config_dict)
    
    # Run analysis
    evaluator = MultiDatasetEvaluator(config)
    evaluator.initialize()
    
    print("✅ Analysis completed!")

def run_compare(args):
    """Run comparative analysis."""
    baselines = args.baseline or ['gradcam', 'integrated_gradients']
    print(f"⚖️  Comparing LBMD with: {', '.join(baselines)}")
    print(f"🤖 Model: {args.model}")
    print(f"📁 Output: {args.output_dir}")
    
    from lbmd_sota import BaselineComparator, LBMDConfig, get_config_template
    
    # Create configuration
    config_dict = get_config_template()
    config_dict['models']['architecture'] = args.model
    config_dict['visualization']['output_dir'] = args.output_dir
    config_dict['comparative_analysis'] = {
        'baseline_methods': baselines,
        'comparison_metrics': ['boundary_accuracy', 'computational_time', 'unique_insights']
    }
    config = LBMDConfig(config_dict)
    
    # Run comparison
    comparator = BaselineComparator(config.comparative_analysis)
    comparator.initialize()
    
    print("✅ Comparison completed!")

def analyze():
    """Entry point for lbmd-analyze command."""
    sys.argv = ['lbmd-sota', 'analyze'] + sys.argv[1:]
    return main()

def compare():
    """Entry point for lbmd-compare command.""" 
    sys.argv = ['lbmd-sota', 'compare'] + sys.argv[1:]
    return main()

if __name__ == '__main__':
    sys.exit(main())
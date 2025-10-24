"""
Test suite for theoretical framework components.
"""

import numpy as np
import pytest
from typing import Dict, Any

from .topological_analyzer import TopologicalAnalyzer, PersistentHomologyAnalyzer
from .mathematical_formalizer import MathematicalFormalizer
from .cognitive_science_connector import CognitiveScienceConnector
from ..core.data_models import AlignmentMetrics


class TestTopologicalAnalyzer:
    """Test topological analysis functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'max_dimension': 2,
            'k_neighbors': 5
        }
        self.analyzer = TopologicalAnalyzer(self.config)
        
        # Create test manifold data (circle-like structure)
        theta = np.linspace(0, 2*np.pi, 50)
        self.test_manifold = np.column_stack([
            np.cos(theta) + 0.1 * np.random.randn(50),
            np.sin(theta) + 0.1 * np.random.randn(50)
        ])
    
    def test_initialization(self):
        """Test analyzer initialization."""
        assert not self.analyzer._initialized
        self.analyzer.initialize()
        assert self.analyzer._initialized
    
    def test_persistent_homology_analysis(self):
        """Test persistent homology computation."""
        ph_analyzer = PersistentHomologyAnalyzer(max_dimension=1)
        persistence_diagram = ph_analyzer.compute_persistence_diagram(self.test_manifold)
        
        assert isinstance(persistence_diagram, dict)
        assert 0 in persistence_diagram  # Should have 0-dimensional features
        assert isinstance(persistence_diagram[0], list)
    
    def test_topological_properties_computation(self):
        """Test topological properties computation."""
        self.analyzer.initialize()
        properties = self.analyzer.compute_topological_properties(self.test_manifold)
        
        assert hasattr(properties, 'betti_numbers')
        assert hasattr(properties, 'persistence_diagram')
        assert hasattr(properties, 'topological_entropy')
    
    def test_analyze_method(self):
        """Test main analyze method."""
        data = {'manifold_coords': self.test_manifold}
        results = self.analyzer.analyze(data)
        
        assert 'persistent_homology' in results
        assert 'topological_features' in results
        assert 'curvature_metrics' in results
        assert 'topological_properties' in results


class TestMathematicalFormalizer:
    """Test mathematical formalization functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {}
        self.formalizer = MathematicalFormalizer(self.config)
        
        # Create test manifold data
        self.test_manifold = np.random.randn(30, 3)
    
    def test_initialization(self):
        """Test formalizer initialization."""
        assert not self.formalizer._initialized
        self.formalizer.initialize()
        assert self.formalizer._initialized
    
    def test_boundary_manifold_definition(self):
        """Test boundary manifold mathematical definition."""
        definition = self.formalizer.formalize_boundary_manifolds()
        
        assert definition.concept_name == "Boundary Manifold"
        assert len(definition.formal_definition) > 0
        assert len(definition.mathematical_notation) > 0
        assert len(definition.assumptions) > 0
    
    def test_boundary_responsiveness_definition(self):
        """Test boundary responsiveness definition."""
        definition = self.formalizer.formalize_boundary_responsiveness()
        
        assert definition.concept_name == "Boundary Responsiveness"
        assert "R_B(h_l)" in definition.mathematical_notation
    
    def test_manifold_decomposition_definition(self):
        """Test manifold decomposition definition."""
        definition = self.formalizer.formalize_manifold_decomposition()
        
        assert definition.concept_name == "Manifold Decomposition"
        assert "LBMD" in definition.formal_definition
    
    def test_theorem_proofs(self):
        """Test theorem proofs generation."""
        proofs = self.formalizer.prove_key_properties()
        
        assert 'boundary_preservation' in proofs
        assert 'responsiveness_monotonicity' in proofs
        assert 'manifold_stability' in proofs
        
        # Check proof structure
        for proof_name, proof_content in proofs.items():
            assert 'theorem' in proof_content
            assert 'proof' in proof_content
    
    def test_theoretical_validation(self):
        """Test theoretical property validation."""
        expected_properties = {'dimension': 2}
        validation_results = self.formalizer.validate_theoretical_properties(
            self.test_manifold, expected_properties
        )
        
        assert 'dimension_validation' in validation_results
        assert 'smoothness_validation' in validation_results
        assert 'topology_validation' in validation_results
        assert 'boundary_validation' in validation_results


class TestCognitiveScienceConnector:
    """Test cognitive science connection functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {}
        self.connector = CognitiveScienceConnector(self.config)
        
        # Create test data
        self.test_features = np.random.randn(40, 10)
        self.test_coords = np.random.randn(40, 2)
        self.test_boundaries = np.random.rand(40)
        
        self.test_data = {
            'lbmd_results': {'boundary_scores': self.test_boundaries},
            'image_features': self.test_features,
            'spatial_coords': self.test_coords
        }
    
    def test_initialization(self):
        """Test connector initialization."""
        assert not self.connector._initialized
        self.connector.initialize()
        assert self.connector._initialized
    
    def test_human_perception_simulation(self):
        """Test human perception model."""
        human_perception = self.connector.human_model.simulate_human_boundary_perception(
            self.test_features, self.test_coords
        )
        
        assert 'proximity' in human_perception
        assert 'similarity' in human_perception
        assert 'closure' in human_perception
        assert 'continuity' in human_perception
        assert 'common_fate' in human_perception
        assert 'combined_boundaries' in human_perception
        assert 'attention_map' in human_perception
    
    def test_cognitive_alignment_analysis(self):
        """Test cognitive alignment analysis."""
        human_data = {
            'image_features': self.test_features,
            'spatial_coords': self.test_coords
        }
        
        alignment = self.connector.analyze_cognitive_alignment(
            self.test_boundaries, human_data
        )
        
        assert isinstance(alignment, AlignmentMetrics)
        assert hasattr(alignment, 'correlation_coefficient')
        assert hasattr(alignment, 'mutual_information')
        assert hasattr(alignment, 'rank_correlation')
        assert hasattr(alignment, 'classification_agreement')
        assert hasattr(alignment, 'boundary_agreement')
    
    def test_cognitive_plausibility_evaluation(self):
        """Test cognitive plausibility evaluation."""
        plausibility = self.connector.plausibility_evaluator.evaluate_cognitive_plausibility(
            self.test_data['lbmd_results'], self.test_features, self.test_coords
        )
        
        assert 'perceptual_grouping' in plausibility
        assert 'biological_plausibility' in plausibility
        assert 'developmental_plausibility' in plausibility
        assert 'overall_plausibility' in plausibility
    
    def test_analyze_method(self):
        """Test main analyze method."""
        results = self.connector.analyze(self.test_data)
        
        assert 'cognitive_alignment' in results
        assert 'cognitive_plausibility' in results
        assert 'human_comparison' in results


def test_integration():
    """Test integration between theoretical framework components."""
    # Create test data
    manifold_data = np.random.randn(30, 3)
    
    # Test topological analysis
    topo_config = {'max_dimension': 2, 'k_neighbors': 5}
    topo_analyzer = TopologicalAnalyzer(topo_config)
    topo_results = topo_analyzer.analyze({'manifold_coords': manifold_data})
    
    # Test mathematical formalization
    math_config = {}
    math_formalizer = MathematicalFormalizer(math_config)
    math_framework = math_formalizer.generate_mathematical_framework()
    
    # Test cognitive science connection
    cognitive_config = {}
    cognitive_connector = CognitiveScienceConnector(cognitive_config)
    
    test_data = {
        'lbmd_results': {'boundary_scores': np.random.rand(20)},
        'image_features': np.random.randn(20, 5),
        'spatial_coords': np.random.randn(20, 2)
    }
    
    cognitive_results = cognitive_connector.analyze(test_data)
    
    # Verify all components work together
    assert topo_results is not None
    assert math_framework is not None
    assert cognitive_results is not None
    
    # Check that results have expected structure
    assert 'definitions' in math_framework
    assert 'proofs' in math_framework
    assert 'validation_methods' in math_framework
    
    assert 'cognitive_alignment' in cognitive_results
    assert 'cognitive_plausibility' in cognitive_results


if __name__ == "__main__":
    # Run basic tests
    print("Testing Theoretical Framework Components...")
    
    # Test topological analyzer
    print("Testing TopologicalAnalyzer...")
    test_topo = TestTopologicalAnalyzer()
    test_topo.setup_method()
    test_topo.test_initialization()
    test_topo.test_persistent_homology_analysis()
    test_topo.test_topological_properties_computation()
    test_topo.test_analyze_method()
    print("✓ TopologicalAnalyzer tests passed")
    
    # Test mathematical formalizer
    print("Testing MathematicalFormalizer...")
    test_math = TestMathematicalFormalizer()
    test_math.setup_method()
    test_math.test_initialization()
    test_math.test_boundary_manifold_definition()
    test_math.test_boundary_responsiveness_definition()
    test_math.test_manifold_decomposition_definition()
    test_math.test_theorem_proofs()
    test_math.test_theoretical_validation()
    print("✓ MathematicalFormalizer tests passed")
    
    # Test cognitive science connector
    print("Testing CognitiveScienceConnector...")
    test_cognitive = TestCognitiveScienceConnector()
    test_cognitive.setup_method()
    test_cognitive.test_initialization()
    test_cognitive.test_human_perception_simulation()
    test_cognitive.test_cognitive_alignment_analysis()
    test_cognitive.test_cognitive_plausibility_evaluation()
    test_cognitive.test_analyze_method()
    print("✓ CognitiveScienceConnector tests passed")
    
    # Test integration
    print("Testing integration...")
    test_integration()
    print("✓ Integration tests passed")
    
    print("\nAll theoretical framework tests completed successfully! ✓")
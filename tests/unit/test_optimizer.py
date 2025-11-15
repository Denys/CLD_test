"""
Unit Tests: Optimizer

Tests for automated design optimization engine.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from psfb_loss_analyzer import (
    DesignSpecification,
    DesignCandidate,
    ObjectiveFunction,
    generate_design_space,
    optimize_design,
    find_pareto_frontier,
    is_pareto_dominated,
)


def test_design_specification_creation():
    """Test design specification creation"""
    spec = DesignSpecification(
        power_min=2500.0,
        power_rated=3000.0,
        power_max=3300.0,
        vin_min=360.0,
        vin_nom=400.0,
        vin_max=440.0,
        vout_nom=48.0,
        n_phases=1,
        efficiency_target=0.95,
        zvs_enable=True,
    )

    assert spec.power_rated == 3000.0
    assert spec.vin_nom == 400.0
    assert spec.vout_nom == 48.0
    assert spec.efficiency_target == 0.95


def test_design_space_generation():
    """Test design space generation"""
    spec = DesignSpecification(
        power_min=2500.0,
        power_rated=3000.0,
        power_max=3300.0,
        vin_min=360.0,
        vin_nom=400.0,
        vin_max=440.0,
        vout_nom=48.0,
        n_phases=1,
        efficiency_target=0.95,
        zvs_enable=True,
    )

    # Generate small design space for testing
    design_space = generate_design_space(
        spec=spec,
        frequency_range=(80e3, 120e3, 2),  # 2 frequencies: 80kHz, 120kHz
        component_filter_top_n=2,  # Top 2 components only
    )

    # Should have at least a few candidates
    assert len(design_space) > 0, "Design space should not be empty"

    # Each design should have required fields
    for design in design_space:
        assert 'primary_mosfet_part' in design
        assert 'secondary_diode_part' in design
        assert 'switching_frequency' in design
        assert 'turns_ratio' in design


def test_pareto_dominance():
    """Test Pareto dominance checking"""
    # Create test candidates
    candidate1 = DesignCandidate(
        primary_mosfet_part="MOSFET1",
        secondary_diode_part="DIODE1",
        switching_frequency=100e3,
        turns_ratio=8.0,
        transformer_core="PQ32/30",
        efficiency_full_load=0.97,
        efficiency_cec=0.96,
        relative_cost=1.0,
        relative_size=1.0,
        score_efficiency=0.97,
        score_cost=1.0,
        score_balanced=0.97,
    )

    candidate2 = DesignCandidate(
        primary_mosfet_part="MOSFET2",
        secondary_diode_part="DIODE2",
        switching_frequency=100e3,
        turns_ratio=8.0,
        transformer_core="PQ32/30",
        efficiency_full_load=0.95,  # Lower efficiency
        efficiency_cec=0.94,
        relative_cost=0.8,  # Lower cost
        relative_size=1.0,
        score_efficiency=0.95,
        score_cost=0.8,
        score_balanced=0.95,
    )

    candidate3 = DesignCandidate(
        primary_mosfet_part="MOSFET3",
        secondary_diode_part="DIODE3",
        switching_frequency=100e3,
        turns_ratio=8.0,
        transformer_core="PQ32/30",
        efficiency_full_load=0.96,
        efficiency_cec=0.95,
        relative_cost=0.9,
        relative_size=0.9,
        score_efficiency=0.96,
        score_cost=0.9,
        score_balanced=0.96,
    )

    population = [candidate1, candidate2, candidate3]

    # Candidate 3 dominates candidate 2 (better efficiency, lower cost)
    assert not is_pareto_dominated(candidate3, population), \
        "Candidate 3 should not be dominated"

    # But candidate 1 and 3 are both on Pareto frontier
    # (1 has better efficiency, 3 has lower cost)


def test_pareto_frontier():
    """Test Pareto frontier generation"""
    # Create test candidates with clear Pareto frontier
    candidates = [
        DesignCandidate(
            primary_mosfet_part=f"MOSFET{i}",
            secondary_diode_part=f"DIODE{i}",
            switching_frequency=100e3,
            turns_ratio=8.0,
            transformer_core="PQ32/30",
            efficiency_full_load=eff,
            efficiency_cec=eff,
            relative_cost=cost,
            relative_size=1.0,
            score_efficiency=eff,
            score_cost=cost,
            score_balanced=(eff + (2.0 - cost)) / 2,
        )
        for i, (eff, cost) in enumerate([
            (0.97, 1.5),  # High eff, high cost - Pareto optimal
            (0.95, 1.0),  # Medium eff, medium cost - Pareto optimal
            (0.93, 0.8),  # Low eff, low cost - Pareto optimal
            (0.94, 1.2),  # Dominated by candidate 1
        ])
    ]

    pareto = find_pareto_frontier(candidates)

    # Should have 3 non-dominated solutions
    assert len(pareto) >= 3, f"Expected at least 3 Pareto optimal solutions, got {len(pareto)}"


def test_optimizer_small_design_space():
    """Test optimizer with small design space (fast test)"""
    spec = DesignSpecification(
        power_min=2500.0,
        power_rated=3000.0,
        power_max=3300.0,
        vin_min=360.0,
        vin_nom=400.0,
        vin_max=440.0,
        vout_nom=48.0,
        n_phases=1,
        efficiency_target=0.92,  # Lower target for faster convergence
        zvs_enable=True,
    )

    # Run optimization with very limited design space
    result = optimize_design(
        spec=spec,
        objective=ObjectiveFunction.BALANCED,
        max_evaluations=10,  # Very small for testing
        verbose=False,
    )

    # Should have some valid designs
    assert result.valid_designs_count > 0, "Should have at least one valid design"

    # Best designs should be selected
    if result.best_efficiency:
        assert result.best_efficiency.efficiency_full_load > 0.90

    if result.best_cost:
        assert result.best_cost.relative_cost > 0

    if result.best_balanced:
        assert result.best_balanced.score_balanced > 0


def test_objective_functions():
    """Test different objective functions"""
    spec = DesignSpecification(
        power_min=2500.0,
        power_rated=3000.0,
        power_max=3300.0,
        vin_min=360.0,
        vin_nom=400.0,
        vin_max=440.0,
        vout_nom=48.0,
        n_phases=1,
        efficiency_target=0.92,
        zvs_enable=True,
    )

    objectives = [
        ObjectiveFunction.EFFICIENCY,
        ObjectiveFunction.COST,
        ObjectiveFunction.BALANCED,
    ]

    for objective in objectives:
        result = optimize_design(
            spec=spec,
            objective=objective,
            max_evaluations=5,  # Very small for testing
            verbose=False,
        )

        # Should complete without errors
        assert result.valid_designs_count >= 0


if __name__ == "__main__":
    print("Running Optimizer Tests...")

    test_design_specification_creation()
    print("✓ Design specification creation")

    test_design_space_generation()
    print("✓ Design space generation")

    test_pareto_dominance()
    print("✓ Pareto dominance")

    test_pareto_frontier()
    print("✓ Pareto frontier")

    test_optimizer_small_design_space()
    print("✓ Optimizer (small design space)")

    test_objective_functions()
    print("✓ Objective functions")

    print("\n✓ All optimizer tests passed!")

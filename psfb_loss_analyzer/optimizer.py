"""
Multi-Objective Optimization Engine for PSFB Converter Design

Automatically designs PSFB converters by optimizing multiple objectives:
- Maximize efficiency
- Minimize cost
- Minimize size/volume
- Minimize thermal stress

Features:
- Component selection from libraries (MOSFETs, diodes, cores)
- Design parameter optimization (frequency, turns ratio, etc.)
- Multi-objective Pareto frontier generation
- Constraint verification (voltage/current ratings, temperature limits)
- Sensitivity analysis
- Design space exploration

Optimization Methods:
- Grid search for discrete parameters
- Pareto dominance filtering for multi-objective
- Weighted sum method for single solution
- Design of Experiments (DOE) for sensitivity

Author: PSFB Loss Analysis Tool
Version: 0.5.0
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Callable
from enum import Enum
import numpy as np
import itertools

try:
    from .circuit_params import MOSFETParameters, DiodeParameters, CoreMaterial
    from .component_library import (
        get_all_mosfets,
        get_all_diodes,
        CAPACITOR_LIBRARY_INPUT,
        CAPACITOR_LIBRARY_OUTPUT,
        filter_mosfets_by_rating,
        filter_diodes_by_rating,
    )
    from .magnetics_design import MagneticDesignSpec
    from .resonant_inductor_design import ZVSRequirements, design_resonant_inductor
    from .transformer_design import TransformerSpec, design_transformer
    from .output_inductor_design import OutputInductorSpec, design_output_inductor
    from .system_analyzer import MagneticComponents, analyze_psfb_system
    from .core_database import list_available_cores, get_core_geometry
except ImportError:
    from circuit_params import MOSFETParameters, DiodeParameters, CoreMaterial
    from component_library import (
        get_all_mosfets,
        get_all_diodes,
        CAPACITOR_LIBRARY_INPUT,
        CAPACITOR_LIBRARY_OUTPUT,
        filter_mosfets_by_rating,
        filter_diodes_by_rating,
    )
    from magnetics_design import MagneticDesignSpec
    from resonant_inductor_design import ZVSRequirements, design_resonant_inductor
    from transformer_design import TransformerSpec, design_transformer
    from output_inductor_design import OutputInductorSpec, design_output_inductor
    from system_analyzer import MagneticComponents, analyze_psfb_system
    from core_database import list_available_cores, get_core_geometry


@dataclass
class DesignSpecification:
    """Input specification for PSFB converter design"""
    # Power requirements
    power_min: float  # Minimum power (W)
    power_rated: float  # Rated power (W)
    power_max: float  # Maximum/peak power (W)

    # Voltage requirements
    vin_min: float  # Minimum input voltage (V)
    vin_nom: float  # Nominal input voltage (V)
    vin_max: float  # Maximum input voltage (V)
    vout_nom: float  # Nominal output voltage (V)
    vout_regulation: float = 0.05  # Output regulation (5%)

    # Multi-phase configuration
    n_phases: int = 1  # Number of phases (1-4)
    phase_shift_deg: float = 0.0  # Phase shift (degrees)

    # Performance targets
    efficiency_target: float = 0.95  # Minimum efficiency (95%)
    zvs_enable: bool = True  # Enable ZVS operation

    # Thermal constraints
    temp_ambient_max: float = 50.0  # Maximum ambient (°C)
    temp_junction_max_mosfet: float = 125.0  # Max MOSFET junction (°C)
    temp_junction_max_diode: float = 150.0  # Max diode junction (°C)


@dataclass
class DesignCandidate:
    """Single design candidate with all parameters"""
    # Component selections
    primary_mosfet_part: str
    secondary_diode_part: str
    input_capacitor_part: str
    output_capacitor_part: str

    # Design parameters
    switching_frequency: float  # Hz
    turns_ratio: float  # N_pri / N_sec
    transformer_core: str  # Core designation

    # Component objects (filled after selection)
    primary_mosfet: Optional[MOSFETParameters] = None
    secondary_diode: Optional[DiodeParameters] = None
    magnetics: Optional[MagneticComponents] = None

    # Performance metrics (filled after evaluation)
    efficiency_full_load: float = 0.0
    efficiency_half_load: float = 0.0
    efficiency_cec: float = 0.0
    total_loss: float = 0.0
    relative_cost: float = 0.0
    relative_size: float = 0.0
    temp_rise_max: float = 0.0

    # Constraint violations
    constraints_satisfied: bool = False
    constraint_violations: List[str] = field(default_factory=list)


@dataclass
class OptimizationResult:
    """Result of optimization run"""
    design_candidates: List[DesignCandidate] = field(default_factory=list)
    pareto_optimal: List[DesignCandidate] = field(default_factory=list)
    best_efficiency: Optional[DesignCandidate] = None
    best_cost: Optional[DesignCandidate] = None
    best_balanced: Optional[DesignCandidate] = None


class ObjectiveFunction(Enum):
    """Optimization objective functions"""
    MAXIMIZE_EFFICIENCY = "max_efficiency"
    MINIMIZE_COST = "min_cost"
    MINIMIZE_SIZE = "min_size"
    MINIMIZE_LOSS = "min_loss"
    BALANCED = "balanced"


# ============================================================================
# Design Space Definition
# ============================================================================

def generate_design_space(
    spec: DesignSpecification,
    frequency_range: Tuple[float, float, int] = (80e3, 150e3, 4),
    component_filter_top_n: int = 3,
) -> List[Dict]:
    """
    Generate design space (all possible combinations).

    Args:
        spec: Design specification
        frequency_range: (min_freq, max_freq, n_points)
        component_filter_top_n: Select top N components from library

    Returns:
        List of design parameter dictionaries
    """
    # Switching frequency candidates
    f_min, f_max, n_freq = frequency_range
    frequencies = np.linspace(f_min, f_max, n_freq).tolist()

    # Calculate per-phase power
    power_per_phase = spec.power_rated / spec.n_phases

    # Filter MOSFETs - primary side (high voltage)
    mosfet_lib = get_all_mosfets()
    mosfet_candidates = filter_mosfets_by_rating(
        mosfet_lib,
        min_voltage=spec.vin_max,
        min_current=power_per_phase / spec.vin_min * 2.0,  # Estimate with margin
    )
    primary_mosfets = [part for part, _, _ in mosfet_candidates[:component_filter_top_n]]

    # Filter diodes - secondary side
    diode_lib = get_all_diodes()
    diode_candidates = filter_diodes_by_rating(
        diode_lib,
        min_voltage=spec.vout_nom * 2.0,  # Full-bridge sees 2× Vout
        min_current=power_per_phase / spec.vout_nom,
        prefer_sic=True,
    )
    secondary_diodes = [part for part, _, _ in diode_candidates[:component_filter_top_n]]

    # Capacitor selections (simple - just pick first)
    input_caps = list(CAPACITOR_LIBRARY_INPUT.keys())[:2]
    output_caps = list(CAPACITOR_LIBRARY_OUTPUT.keys())[:2]

    # Turns ratio candidates (based on voltage transformation)
    base_ratio = (spec.vin_nom * 0.45) / spec.vout_nom  # Nominal at 45% duty
    turns_ratios = [base_ratio * f for f in [0.8, 1.0, 1.2]]

    # Transformer core candidates (filter by power level)
    all_cores = list_available_cores()
    # Simple heuristic: larger cores for higher power
    if power_per_phase < 1500:
        core_candidates = [c for c in all_cores if "PQ60" in c or "PQ65" in c or "ETD39" in c or "ETD44" in c]
    elif power_per_phase < 3000:
        core_candidates = [c for c in all_cores if "PQ65" in c or "PQ80" in c or "ETD49" in c or "ETD54" in c]
    else:
        core_candidates = [c for c in all_cores if "PQ80" in c or "PQ107" in c or "ETD54" in c or "ETD59" in c]

    # Limit combinations to avoid explosion
    if not core_candidates:
        core_candidates = ["PQ80/60"]  # Fallback

    # Generate all combinations
    design_space = []
    for freq in frequencies:
        for mosfet in primary_mosfets:
            for diode in secondary_diodes:
                for turns in turns_ratios:
                    for core in core_candidates[:2]:  # Limit to 2 cores
                        for input_cap in input_caps:
                            for output_cap in output_caps:
                                design_space.append({
                                    'frequency': freq,
                                    'mosfet': mosfet,
                                    'diode': diode,
                                    'turns_ratio': turns,
                                    'core': core,
                                    'input_cap': input_cap,
                                    'output_cap': output_cap,
                                })

    return design_space


# ============================================================================
# Design Evaluation
# ============================================================================

def evaluate_design(
    params: Dict,
    spec: DesignSpecification,
    verbose: bool = False,
) -> Optional[DesignCandidate]:
    """
    Evaluate a single design candidate.

    Args:
        params: Design parameters dictionary
        spec: Design specification
        verbose: Print evaluation details

    Returns:
        DesignCandidate with evaluated metrics, or None if failed
    """
    try:
        # Create design candidate
        candidate = DesignCandidate(
            primary_mosfet_part=params['mosfet'],
            secondary_diode_part=params['diode'],
            input_capacitor_part=params['input_cap'],
            output_capacitor_part=params['output_cap'],
            switching_frequency=params['frequency'],
            turns_ratio=params['turns_ratio'],
            transformer_core=params['core'],
        )

        # Get component objects
        mosfet_lib = get_all_mosfets()
        diode_lib = get_all_diodes()

        candidate.primary_mosfet = mosfet_lib[params['mosfet']]['device']
        candidate.secondary_diode = diode_lib[params['diode']]['device']

        input_cap_data = CAPACITOR_LIBRARY_INPUT[params['input_cap']]
        output_cap_data = CAPACITOR_LIBRARY_OUTPUT[params['output_cap']]

        # Calculate cost (relative)
        cost = (mosfet_lib[params['mosfet']]['metrics'].relative_cost * 4 +  # 4 MOSFETs
                diode_lib[params['diode']]['metrics'].relative_cost * 4 +  # 4 diodes
                input_cap_data['metrics'].relative_cost +
                output_cap_data['metrics'].relative_cost)
        candidate.relative_cost = cost

        # Design magnetic components (quick, suppress output)
        power_per_phase = spec.power_rated / spec.n_phases

        import io
        import contextlib

        with contextlib.redirect_stdout(io.StringIO()):
            # Magnetic design spec
            mag_spec = MagneticDesignSpec(
                power=power_per_phase,
                frequency=params['frequency'],
                temp_ambient=spec.temp_ambient_max,
                temp_rise_max=60.0,
                current_density_max=5.0,
                window_utilization=0.5,
                flux_density_max=0.25,
                core_material=CoreMaterial.FERRITE_3C95,
            )

            # Resonant inductor
            zvs_req = ZVSRequirements(
                mosfet_coss=candidate.primary_mosfet.capacitances.get_coss(spec.vin_nom),
                mosfet_vds_max=candidate.primary_mosfet.v_dss,
                n_mosfets_parallel=2,
                vin_nom=spec.vin_nom,
                vin_max=spec.vin_max,
                load_full=power_per_phase,
                load_min_zvs=power_per_phase * 0.1,
                frequency=params['frequency'],
                turns_ratio=params['turns_ratio'],
                magnetizing_inductance=200e-6,
            )
            lr_design, _ = design_resonant_inductor(zvs_req, mag_spec, "PQ", "ETD")

            # Transformer
            xfmr_spec = TransformerSpec(
                vin_min=spec.vin_min,
                vin_nom=spec.vin_nom,
                vin_max=spec.vin_max,
                vout_nom=spec.vout_nom,
                power_output=power_per_phase,
                frequency=params['frequency'],
                duty_cycle_nom=0.45,
            )
            xfmr_design, _ = design_transformer(xfmr_spec, mag_spec, "PQ", "ETD")

            # Output inductor
            lo_spec = OutputInductorSpec(
                vout_nom=spec.vout_nom,
                iout_nom=power_per_phase / spec.vout_nom,
                iout_max=power_per_phase / spec.vout_nom * 1.2,
                frequency=params['frequency'],
                n_phases=spec.n_phases,
                phase_shift_deg=spec.phase_shift_deg,
            )
            lo_design, _ = design_output_inductor(lo_spec, mag_spec, "PQ", "E")

        candidate.magnetics = MagneticComponents(
            resonant_inductor=lr_design,
            transformer=xfmr_design,
            output_inductor=lo_design,
        )

        # Estimate size (volume)
        core_geom = get_core_geometry(params['core'])
        if core_geom:
            candidate.relative_size = core_geom.effective_volume * 1e6  # cm³
        else:
            candidate.relative_size = 100.0  # Default

        # Evaluate system performance at key operating points
        duty_cycle = spec.vout_nom / (spec.vin_nom * params['turns_ratio'] * 2.0)
        duty_cycle = min(max(duty_cycle, 0.1), 0.48)

        # Full load
        system_full = analyze_psfb_system(
            input_voltage=spec.vin_nom,
            output_voltage=spec.vout_nom,
            output_power=spec.power_rated,
            frequency=params['frequency'],
            duty_cycle=duty_cycle,
            turns_ratio=xfmr_design.turns_ratio,
            n_phases=spec.n_phases,
            phase_shift_deg=spec.phase_shift_deg,
            primary_mosfet=candidate.primary_mosfet,
            secondary_diode=candidate.secondary_diode,
            magnetics=candidate.magnetics,
            input_capacitor=input_cap_data['device'],
            output_capacitor=output_cap_data['device'],
            zvs_operation=spec.zvs_enable,
        )

        candidate.efficiency_full_load = system_full.efficiency
        candidate.total_loss = system_full.total_loss

        # Half load
        system_half = analyze_psfb_system(
            input_voltage=spec.vin_nom,
            output_voltage=spec.vout_nom,
            output_power=spec.power_rated * 0.5,
            frequency=params['frequency'],
            duty_cycle=duty_cycle,
            turns_ratio=xfmr_design.turns_ratio,
            n_phases=spec.n_phases,
            phase_shift_deg=spec.phase_shift_deg,
            primary_mosfet=candidate.primary_mosfet,
            secondary_diode=candidate.secondary_diode,
            magnetics=candidate.magnetics,
            input_capacitor=input_cap_data['device'],
            output_capacitor=output_cap_data['device'],
            zvs_operation=spec.zvs_enable,
        )

        candidate.efficiency_half_load = system_half.efficiency

        # Simple CEC estimate (weighted)
        candidate.efficiency_cec = 0.53 * system_half.efficiency + 0.47 * system_full.efficiency

        # Temperature estimate (simplified)
        candidate.temp_rise_max = candidate.total_loss * 0.5  # Rough estimate

        # Check constraints
        violations = []

        if candidate.efficiency_full_load < spec.efficiency_target * 100:
            violations.append(f"Efficiency {candidate.efficiency_full_load:.1f}% < target {spec.efficiency_target*100:.1f}%")

        if candidate.primary_mosfet.v_dss < spec.vin_max * 1.2:
            violations.append(f"MOSFET voltage rating insufficient")

        if candidate.temp_rise_max > 80:
            violations.append(f"Excessive temperature rise")

        candidate.constraint_violations = violations
        candidate.constraints_satisfied = (len(violations) == 0)

        if verbose:
            print(f"  Evaluated: {params['mosfet']}, {params['diode']}, {params['frequency']/1000:.0f}kHz")
            print(f"    Efficiency: {candidate.efficiency_full_load:.2f}%, Cost: {candidate.relative_cost:.1f}")

        return candidate

    except Exception as e:
        if verbose:
            print(f"  Failed to evaluate design: {e}")
        return None


# ============================================================================
# Multi-Objective Optimization
# ============================================================================

def is_pareto_dominated(candidate: DesignCandidate, population: List[DesignCandidate]) -> bool:
    """
    Check if a candidate is Pareto dominated by any member of population.

    Objectives (to maximize):
    - Efficiency
    - Negative cost (minimize cost = maximize -cost)
    - Negative size

    Args:
        candidate: Design to check
        population: Population to compare against

    Returns:
        True if dominated, False otherwise
    """
    for other in population:
        if other == candidate:
            continue

        # Check if 'other' dominates 'candidate'
        # Domination: other is better or equal in all objectives, and strictly better in at least one

        better_efficiency = other.efficiency_cec >= candidate.efficiency_cec
        better_cost = other.relative_cost <= candidate.relative_cost
        better_size = other.relative_size <= candidate.relative_size

        strictly_better_efficiency = other.efficiency_cec > candidate.efficiency_cec
        strictly_better_cost = other.relative_cost < candidate.relative_cost
        strictly_better_size = other.relative_size < candidate.relative_size

        # Dominated if other is better/equal in all and strictly better in at least one
        if better_efficiency and better_cost and better_size:
            if strictly_better_efficiency or strictly_better_cost or strictly_better_size:
                return True  # Candidate is dominated

    return False  # Not dominated


def find_pareto_frontier(candidates: List[DesignCandidate]) -> List[DesignCandidate]:
    """
    Find Pareto-optimal designs from candidate list.

    Args:
        candidates: List of design candidates

    Returns:
        List of Pareto-optimal candidates
    """
    # Filter to valid designs only
    valid_candidates = [c for c in candidates if c.constraints_satisfied]

    if not valid_candidates:
        print("Warning: No valid candidates found for Pareto frontier")
        return []

    pareto_optimal = []

    for candidate in valid_candidates:
        if not is_pareto_dominated(candidate, valid_candidates):
            pareto_optimal.append(candidate)

    return pareto_optimal


# ============================================================================
# Optimization Engine
# ============================================================================

def optimize_design(
    spec: DesignSpecification,
    objective: ObjectiveFunction = ObjectiveFunction.BALANCED,
    max_evaluations: int = 100,
    verbose: bool = True,
) -> OptimizationResult:
    """
    Optimize PSFB converter design for given specifications.

    Args:
        spec: Design specification
        objective: Optimization objective
        max_evaluations: Maximum design evaluations
        verbose: Print progress

    Returns:
        OptimizationResult with candidates and Pareto frontier
    """
    if verbose:
        print("=" * 80)
        print("PSFB CONVERTER OPTIMIZATION")
        print("=" * 80)
        print()
        print(f"Specification:")
        print(f"  Power:       {spec.power_rated:.0f} W")
        print(f"  Input:       {spec.vin_nom:.0f} V ({spec.vin_min:.0f}-{spec.vin_max:.0f}V)")
        print(f"  Output:      {spec.vout_nom:.0f} V")
        print(f"  Phases:      {spec.n_phases}")
        print(f"  Objective:   {objective.value}")
        print()

    # Generate design space
    design_space = generate_design_space(spec)

    if verbose:
        print(f"Design Space: {len(design_space)} candidates")
        print()

    # Limit evaluations
    if len(design_space) > max_evaluations:
        # Sample randomly
        import random
        design_space = random.sample(design_space, max_evaluations)
        if verbose:
            print(f"Sampling {max_evaluations} designs randomly...")
            print()

    # Evaluate all candidates
    candidates = []
    if verbose:
        print("Evaluating designs...")

    for i, params in enumerate(design_space):
        if verbose and (i % 10 == 0):
            print(f"  Progress: {i}/{len(design_space)}")

        candidate = evaluate_design(params, spec, verbose=False)
        if candidate:
            candidates.append(candidate)

    if verbose:
        print(f"  Completed: {len(candidates)} valid designs")
        print()

    # Find Pareto frontier
    pareto_optimal = find_pareto_frontier(candidates)

    if verbose:
        print(f"Pareto Frontier: {len(pareto_optimal)} designs")
        print()

    # Find best designs by specific criteria
    valid_candidates = [c for c in candidates if c.constraints_satisfied]

    best_efficiency = None
    best_cost = None
    best_balanced = None

    if valid_candidates:
        best_efficiency = max(valid_candidates, key=lambda c: c.efficiency_cec)
        best_cost = min(valid_candidates, key=lambda c: c.relative_cost)

        # Balanced: normalize and weight
        for c in valid_candidates:
            c.score_balanced = (
                0.6 * (c.efficiency_cec / 100.0) +
                0.2 * (1.0 / (1.0 + c.relative_cost / 10.0)) +
                0.2 * (1.0 / (1.0 + c.relative_size / 100.0))
            )
        best_balanced = max(valid_candidates, key=lambda c: c.score_balanced)

    result = OptimizationResult(
        design_candidates=candidates,
        pareto_optimal=pareto_optimal,
        best_efficiency=best_efficiency,
        best_cost=best_cost,
        best_balanced=best_balanced,
    )

    return result


def print_optimization_summary(result: OptimizationResult):
    """Print formatted optimization results."""
    print("=" * 80)
    print("OPTIMIZATION RESULTS")
    print("=" * 80)
    print()

    print(f"Total Candidates:    {len(result.design_candidates)}")
    print(f"Valid Designs:       {sum(1 for c in result.design_candidates if c.constraints_satisfied)}")
    print(f"Pareto Optimal:      {len(result.pareto_optimal)}")
    print()

    if result.best_efficiency:
        print("BEST EFFICIENCY DESIGN:")
        print(f"  Primary MOSFET:    {result.best_efficiency.primary_mosfet_part}")
        print(f"  Secondary Diode:   {result.best_efficiency.secondary_diode_part}")
        print(f"  Switching Freq:    {result.best_efficiency.switching_frequency / 1000:.0f} kHz")
        print(f"  Efficiency:        {result.best_efficiency.efficiency_cec:.2f}%")
        print(f"  Relative Cost:     {result.best_efficiency.relative_cost:.1f}")
        print()

    if result.best_cost:
        print("LOWEST COST DESIGN:")
        print(f"  Primary MOSFET:    {result.best_cost.primary_mosfet_part}")
        print(f"  Secondary Diode:   {result.best_cost.secondary_diode_part}")
        print(f"  Switching Freq:    {result.best_cost.switching_frequency / 1000:.0f} kHz")
        print(f"  Efficiency:        {result.best_cost.efficiency_cec:.2f}%")
        print(f"  Relative Cost:     {result.best_cost.relative_cost:.1f}")
        print()

    if result.best_balanced:
        print("BEST BALANCED DESIGN:")
        print(f"  Primary MOSFET:    {result.best_balanced.primary_mosfet_part}")
        print(f"  Secondary Diode:   {result.best_balanced.secondary_diode_part}")
        print(f"  Switching Freq:    {result.best_balanced.switching_frequency / 1000:.0f} kHz")
        print(f"  Efficiency:        {result.best_balanced.efficiency_cec:.2f}%")
        print(f"  Relative Cost:     {result.best_balanced.relative_cost:.1f}")
        print()

    print("=" * 80)


# ============================================================================
# Module Information
# ============================================================================

if __name__ == "__main__":
    print("PSFB Loss Analyzer - Multi-Objective Optimization Engine")
    print("=" * 80)
    print()
    print("This module provides automated PSFB converter design:")
    print("  - Component selection from libraries")
    print("  - Multi-objective optimization (efficiency, cost, size)")
    print("  - Pareto frontier generation")
    print("  - Constraint verification")
    print()
    print("Use optimize_design() for automated design")
    print()

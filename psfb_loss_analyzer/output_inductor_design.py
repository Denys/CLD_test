"""
Output Inductor Design for PSFB Converters

Designs output filter inductors for Phase-Shifted Full-Bridge DC-DC converters with:
- Optimal inductance value for current ripple control
- Air gap design for DC bias current
- Multi-phase interleaving support (ripple cancellation)
- Minimized core and winding losses
- Thermal management

The output inductor:
1. Filters rectified output current to smooth DC
2. Works with output capacitor to minimize output voltage ripple
3. Must handle full DC load current plus AC ripple
4. Requires air gap to prevent core saturation from DC bias

For 3-phase interleaved PSFB (120° phase shift):
- Each phase has its own output inductor
- Inductors may share a common output node
- Ripple cancellation at output significantly reduces capacitor size
- Effective ripple frequency: 3× or 6× switching frequency

Key Design References:
- McLyman "Transformer and Inductor Design Handbook" 4th Ed., Chapter 4
- Erickson & Maksimovic "Fundamentals of Power Electronics" 3rd Ed., Ch. 2, 8
- Colonel McLyman's Area Product (Kg) method for gapped inductors

Design Methodology:
1. Calculate required inductance based on ripple specification
2. Account for multi-phase interleaving effects
3. Calculate DC and RMS currents
4. Use Kg method to select core
5. Calculate air gap for DC bias (avoid saturation)
6. Design winding with minimal AC resistance
7. Calculate losses (core loss with DC bias + copper loss)
8. Perform thermal analysis

Author: PSFB Loss Analysis Tool
Version: 0.3.0
"""

from dataclasses import dataclass
from typing import Optional, Tuple, List
import numpy as np

try:
    from .magnetics_design import (
        MagneticDesignSpec,
        MagneticDesignResult,
        WindingDesign,
        calculate_required_kg,
        select_core_by_kg,
        design_winding,
        calculate_core_loss_steinmetz,
        estimate_temperature_rise,
        calculate_window_utilization,
        B_MAX_FERRITE_100KHZ,
        J_MAX_FORCED_AIR,
        KU_CAREFUL_LAYERED,
    )
    from .core_database import get_core_loss_coefficients
    from .circuit_params import CoreMaterial
except ImportError:
    from magnetics_design import (
        MagneticDesignSpec,
        MagneticDesignResult,
        WindingDesign,
        calculate_required_kg,
        select_core_by_kg,
        design_winding,
        calculate_core_loss_steinmetz,
        estimate_temperature_rise,
        calculate_window_utilization,
        B_MAX_FERRITE_100KHZ,
        J_MAX_FORCED_AIR,
        KU_CAREFUL_LAYERED,
    )
    from core_database import get_core_loss_coefficients
    from circuit_params import CoreMaterial


@dataclass
class OutputInductorSpec:
    """Output inductor design specification"""
    # Required parameters
    vout_nom: float  # Nominal output voltage (V)
    iout_nom: float  # Nominal output current (A)
    iout_max: float  # Maximum output current (A)
    frequency: float  # Switching frequency (Hz)

    # Optional ripple requirements
    current_ripple_percent: float = 30.0  # Current ripple as % of nominal (20-40% typical)
    current_ripple_pp_max: Optional[float] = None  # Maximum peak-to-peak ripple (A)

    # Optional operating conditions
    duty_cycle_nom: float = 0.45  # Nominal duty cycle

    # Multi-phase interleaving
    n_phases: int = 1  # Number of interleaved phases (1, 2, 3, 4)
    phase_shift_deg: float = 0.0  # Phase shift between channels (degrees)
    # For 3-phase: phase_shift_deg = 120°

    # Inductance specification
    inductance_target: Optional[float] = None  # Target inductance (H), if specified


def calculate_output_inductance(
    vout: float,
    iout_nom: float,
    frequency: float,
    duty_cycle: float,
    ripple_percent: float,
    n_phases: int = 1,
) -> Tuple[float, float]:
    """
    Calculate required output inductance for desired ripple.

    For buck-derived converters (including PSFB):
    ΔI_L = (Vout × (1 - D)) / (L × f)

    Solving for L:
    L = (Vout × (1 - D)) / (ΔI_L × f)

    For multi-phase interleaving:
    - Each phase inductor sees switching frequency ripple
    - But output node sees higher effective frequency
    - Inductor design is per-phase (individual inductors)

    Args:
        vout: Output voltage (V)
        iout_nom: Nominal output current per phase (A)
        frequency: Switching frequency (Hz)
        duty_cycle: Duty cycle (0-1)
        ripple_percent: Desired current ripple (% of nominal current)
        n_phases: Number of interleaved phases

    Returns:
        Tuple of (inductance_per_phase, ripple_current_pp)
    """
    # Calculate ripple current
    ripple_current_pp = (ripple_percent / 100.0) * iout_nom

    # Required inductance per phase
    # L = Vout × (1 - D) / (ΔI × f)
    inductance = (vout * (1.0 - duty_cycle)) / (ripple_current_pp * frequency)

    return inductance, ripple_current_pp


def calculate_air_gap_length(
    inductance: float,
    n_turns: int,
    core_area: float,
    core_permeability: float = 2000,
    fringing_factor: float = 1.1,
) -> float:
    """
    Calculate required air gap length for specified inductance with DC bias.

    For gapped inductor with DC bias, air gap dominates reluctance:
    L = (μ₀ × N² × Ac) / (lg_eff)

    Where lg_eff includes fringing flux:
    lg_eff = lg × F
    F = fringing factor (typically 1.1 - 1.2 for small gaps)

    Solving for lg:
    lg = (μ₀ × N² × Ac) / (L × F)

    Args:
        inductance: Target inductance (H)
        n_turns: Number of turns
        core_area: Core cross-sectional area (m²)
        core_permeability: Relative permeability of core (not critical for large gaps)
        fringing_factor: Fringing flux factor (1.1 typical)

    Returns:
        Air gap length (m)
    """
    mu_0 = 4 * np.pi * 1e-7  # H/m

    # Air gap length (physical)
    lg = (mu_0 * n_turns**2 * core_area) / (inductance * fringing_factor)

    return lg


def calculate_inductor_current_stress(
    iout_dc: float,
    ripple_current_pp: float,
) -> Tuple[float, float, float]:
    """
    Calculate current stress parameters for inductor.

    For inductor with DC bias and triangular AC ripple:
    I_peak = I_dc + ΔI/2
    I_rms² = I_dc² + (ΔI²/12)

    Args:
        iout_dc: DC output current (A)
        ripple_current_pp: Peak-to-peak ripple current (A)

    Returns:
        Tuple of (I_peak, I_rms, I_valley)
    """
    i_peak = iout_dc + ripple_current_pp / 2.0
    i_valley = iout_dc - ripple_current_pp / 2.0
    i_rms = np.sqrt(iout_dc**2 + (ripple_current_pp**2 / 12.0))

    return i_peak, i_rms, i_valley


def calculate_core_loss_with_dc_bias(
    core_geometry,
    coefficients,
    frequency: float,
    flux_density_dc: float,
    flux_density_ac: float,
    dc_bias_factor: float = 0.5,
) -> float:
    """
    Calculate core loss for inductor with DC bias.

    With DC bias, core loss is reduced because:
    1. Core operates on minor B-H loop
    2. Effective permeability is reduced
    3. AC flux swing is smaller portion of total flux

    Empirical correction:
    P_core_biased ≈ P_core_ac_only × (1 - k_dc × B_dc/B_sat)

    Where k_dc ≈ 0.3-0.5 (empirical factor)

    Args:
        core_geometry: Core geometry
        coefficients: Steinmetz coefficients
        frequency: Operating frequency (Hz)
        flux_density_dc: DC flux density (T)
        flux_density_ac: AC flux density swing (T)
        dc_bias_factor: DC bias correction factor (0-1)

    Returns:
        Core loss with DC bias (W)
    """
    # Calculate AC-only core loss using Steinmetz
    p_core_ac = calculate_core_loss_steinmetz(
        core_geometry,
        coefficients,
        frequency,
        flux_density_ac
    )

    # DC bias correction (reduces loss)
    b_sat = 0.5  # Ferrite saturation (T)
    dc_bias_ratio = min(flux_density_dc / b_sat, 0.9)
    reduction_factor = 1.0 - dc_bias_factor * dc_bias_ratio

    # Corrected core loss
    p_core = p_core_ac * reduction_factor

    return p_core


def design_output_inductor(
    inductor_spec: OutputInductorSpec,
    mag_spec: MagneticDesignSpec,
    core_family: str = "PQ",
    alternative_family: str = "E",
) -> Tuple[MagneticDesignResult, MagneticDesignResult]:
    """
    Complete output inductor design for PSFB converter.

    Optimizes for low loss, minimal ripple, and thermal performance.

    Args:
        inductor_spec: Output inductor specifications
        mag_spec: Magnetic design specifications
        core_family: Primary core family ("PQ")
        alternative_family: Alternative core family ("E", "ETD")

    Returns:
        Tuple of (primary_design, alternative_design)
    """
    print("=" * 80)
    print("PSFB OUTPUT INDUCTOR DESIGN")
    print("=" * 80)
    print()

    # ========================================================================
    # Step 1: Calculate Required Inductance
    # ========================================================================
    print("Step 1: Inductance Calculation")
    print("-" * 80)

    if inductor_spec.inductance_target:
        inductance = inductor_spec.inductance_target
        # Back-calculate ripple
        ripple_current_pp = (inductor_spec.vout_nom * (1.0 - inductor_spec.duty_cycle_nom)) / (
            inductance * inductor_spec.frequency
        )
        ripple_percent = 100.0 * ripple_current_pp / inductor_spec.iout_nom
    else:
        inductance, ripple_current_pp = calculate_output_inductance(
            inductor_spec.vout_nom,
            inductor_spec.iout_nom,
            inductor_spec.frequency,
            inductor_spec.duty_cycle_nom,
            inductor_spec.current_ripple_percent,
            inductor_spec.n_phases,
        )
        ripple_percent = inductor_spec.current_ripple_percent

    print(f"Output Voltage:        {inductor_spec.vout_nom:.1f} V")
    print(f"Output Current:        {inductor_spec.iout_nom:.2f} A (nominal)")
    print(f"                       {inductor_spec.iout_max:.2f} A (maximum)")
    print(f"Switching Frequency:   {inductor_spec.frequency / 1000:.0f} kHz")
    print()
    print(f"Required Inductance:   {inductance * 1e6:.1f} µH")
    print(f"Current Ripple:        {ripple_current_pp:.2f} A p-p ({ripple_percent:.1f}%)")
    print()

    if inductor_spec.n_phases > 1:
        print(f"Multi-Phase Configuration:")
        print(f"  Number of phases:    {inductor_spec.n_phases}")
        print(f"  Phase shift:         {inductor_spec.phase_shift_deg:.0f}°")
        print(f"  Note: Each phase has separate inductor")
        print(f"  Output ripple frequency: {inductor_spec.frequency * inductor_spec.n_phases / 1000:.0f} kHz")
        print()

    # ========================================================================
    # Step 2: Calculate Current Stress
    # ========================================================================
    print("Step 2: Current Stress Analysis")
    print("-" * 80)

    # Current per phase (for interleaved design)
    iout_per_phase = inductor_spec.iout_nom / inductor_spec.n_phases

    i_peak, i_rms, i_valley = calculate_inductor_current_stress(
        iout_per_phase,
        ripple_current_pp
    )

    print(f"Per-Phase Current (for {inductor_spec.n_phases} phases):")
    print(f"  I_dc:                {iout_per_phase:.2f} A")
    print(f"  I_peak:              {i_peak:.2f} A")
    print(f"  I_valley:            {i_valley:.2f} A")
    print(f"  I_rms:               {i_rms:.2f} A")
    print()

    # ========================================================================
    # Step 3: Core Selection Using Kg Method
    # ========================================================================
    print("Step 3: Core Selection (Kg Method)")
    print("-" * 80)

    # Energy storage in inductor: E = ½ L I²
    energy_stored = 0.5 * inductance * i_peak**2

    # For gapped inductor, use energy-based Kg calculation
    # Approximate power as energy × frequency
    power_equivalent = energy_stored * inductor_spec.frequency * 2.0

    kg_required = calculate_required_kg(
        power=power_equivalent,
        frequency=inductor_spec.frequency,
        flux_density_max=mag_spec.flux_density_max,
        current_density_max=mag_spec.current_density_max,
        window_utilization=mag_spec.window_utilization,
        topology_factor=4.0,  # Inductor topology factor
    )

    print(f"Energy Stored:         {energy_stored:.2f} J")
    print(f"Required Kg:           {kg_required:.2e} m⁵")
    print()

    # Select core from primary family
    core_name_1, core_geom_1, kg_actual_1 = select_core_by_kg(
        kg_required,
        core_family=core_family,
        material=mag_spec.core_material,
        margin=1.2,
    )

    print(f"Selected Core ({core_family} family): {core_name_1}")
    print(f"  Kg actual:           {kg_actual_1:.2e} m⁵")
    print(f"  Core area:           {core_geom_1.core_area * 1e6:.1f} mm²")
    print(f"  Window area:         {core_geom_1.window_area * 1e6:.1f} mm²")
    print(f"  MLT:                 {core_geom_1.mean_length_turn * 1000:.1f} mm")
    print()

    # Select alternative core
    core_name_2, core_geom_2, kg_actual_2 = select_core_by_kg(
        kg_required,
        core_family=alternative_family,
        material=mag_spec.core_material,
        margin=1.2,
    )

    print(f"Alternative Core ({alternative_family} family): {core_name_2}")
    print(f"  Kg actual:           {kg_actual_2:.2e} m⁵")
    print(f"  Core area:           {core_geom_2.core_area * 1e6:.1f} mm²")
    print(f"  Window area:         {core_geom_2.window_area * 1e6:.1f} mm²")
    print()

    # Complete design for both cores
    designs = []

    for core_name, core_geom in [(core_name_1, core_geom_1), (core_name_2, core_geom_2)]:
        print("=" * 80)
        print(f"Detailed Design: {core_name}")
        print("=" * 80)
        print()

        # ====================================================================
        # Step 4: Calculate Number of Turns and Air Gap
        # ====================================================================
        print("Step 4: Turn Count and Air Gap Design")
        print("-" * 80)

        # Start with turns to achieve desired flux density
        # B_peak = L × I_peak / (N × Ac)
        # N = L × I_peak / (B_peak × Ac)

        b_target = mag_spec.flux_density_max * 0.8  # Use 80% of max for margin

        n_turns = int(np.ceil(
            (inductance * i_peak) / (b_target * core_geom.core_area)
        ))
        n_turns = max(n_turns, 10)  # Minimum 10 turns for practical construction

        # Calculate air gap for this inductance and turns
        air_gap = calculate_air_gap_length(
            inductance,
            n_turns,
            core_geom.core_area,
            core_permeability=2000,
            fringing_factor=1.1,
        )

        # Recalculate actual flux densities
        b_dc = (inductance * iout_per_phase) / (n_turns * core_geom.core_area)
        b_ac = (inductance * ripple_current_pp) / (n_turns * core_geom.core_area)
        b_peak = b_dc + b_ac / 2.0

        print(f"Number of Turns:       {n_turns}")
        print(f"Air Gap Length:        {air_gap * 1000:.2f} mm")
        print()
        print(f"Flux Density:")
        print(f"  B_dc:                {b_dc * 1000:.1f} mT")
        print(f"  B_ac (ripple):       {b_ac * 1000:.1f} mT")
        print(f"  B_peak:              {b_peak * 1000:.1f} mT")
        print()

        if b_peak > 0.4:
            print(f"  WARNING: B_peak = {b_peak:.3f}T is high! Risk of saturation.")
            print()

        # Verify inductance
        mu_0 = 4 * np.pi * 1e-7
        l_verify = (mu_0 * n_turns**2 * core_geom.core_area) / (air_gap * 1.1)
        print(f"Inductance Verification: {l_verify * 1e6:.1f} µH (target: {inductance * 1e6:.1f} µH)")
        print()

        # ====================================================================
        # Step 5: Winding Design
        # ====================================================================
        print("Step 5: Winding Design")
        print("-" * 80)

        winding = design_winding(
            current_rms=i_rms,
            n_turns=n_turns,
            mlt=core_geom.mean_length_turn,
            frequency=inductor_spec.frequency,
            current_density_max=mag_spec.current_density_max,
            n_layers_target=2,  # Multi-layer for better window utilization
            use_litz=False,  # Solid wire typically sufficient for output inductor
            temp=mag_spec.temp_ambient + mag_spec.temp_rise_max / 2,
        )

        print(f"Wire Diameter:         {winding.wire_diameter:.2f} mm (insulated)")
        print(f"                       {winding.wire_diameter_bare:.2f} mm (bare)")
        print(f"Number of Layers:      {winding.n_layers}")
        print(f"Wire Type:             {winding.wire_type.value}")
        print(f"R_dc:                  {winding.resistance_dc * 1000:.1f} mΩ")
        print(f"R_ac:                  {winding.resistance_ac * 1000:.1f} mΩ  (AC/DC: {winding.resistance_ac/winding.resistance_dc:.2f})")
        print(f"Copper Loss:           {winding.copper_loss:.2f} W")
        print(f"Current Density:       {winding.current_density:.2f} A/mm²")
        print()

        # ====================================================================
        # Step 6: Core Loss
        # ====================================================================
        print("Step 6: Core Loss Calculation (with DC Bias)")
        print("-" * 80)

        coefficients = get_core_loss_coefficients(
            mag_spec.core_material,
            mag_spec.temp_ambient + 40
        )

        # Core loss with DC bias correction
        core_loss = calculate_core_loss_with_dc_bias(
            core_geom,
            coefficients,
            inductor_spec.frequency,
            b_dc,
            b_ac,
            dc_bias_factor=0.5,
        )

        print(f"Steinmetz Coefficients ({mag_spec.core_material.value}):")
        print(f"  k = {coefficients.k:.2e}, α = {coefficients.alpha:.3f}, β = {coefficients.beta:.3f}")
        print(f"Core Loss (DC biased): {core_loss:.2f} W")
        print()

        # ====================================================================
        # Step 7: Total Loss and Efficiency
        # ====================================================================
        print("Step 7: Loss Summary")
        print("-" * 80)

        total_loss = winding.copper_loss + core_loss

        # Calculate efficiency based on power throughput per phase
        power_per_phase = inductor_spec.vout_nom * iout_per_phase
        efficiency = 100.0 * (1.0 - total_loss / power_per_phase) if power_per_phase > 0 else 0.0

        print(f"Copper Loss:           {winding.copper_loss:.2f} W")
        print(f"Core Loss:             {core_loss:.2f} W")
        print(f"Total Loss:            {total_loss:.2f} W")
        print(f"Efficiency:            {efficiency:.2f}%")
        print()

        # ====================================================================
        # Step 8: Thermal Analysis
        # ====================================================================
        print("Step 8: Thermal Analysis")
        print("-" * 80)

        temp_rise = estimate_temperature_rise(
            total_loss,
            core_geom.surface_area,
            cooling_coefficient=20.0,  # Forced air
        )

        ku_actual = calculate_window_utilization(
            winding,
            core_geom.window_area
        )

        print(f"Temperature Rise:      {temp_rise:.1f} °C")
        print(f"Hotspot Temperature:   {mag_spec.temp_ambient + temp_rise:.1f} °C")
        print(f"Window Utilization:    {ku_actual * 100:.1f}%")
        print()

        if temp_rise > mag_spec.temp_rise_max:
            print(f"  WARNING: Temperature rise exceeds {mag_spec.temp_rise_max}°C limit!")
            print()

        # ====================================================================
        # Create Result
        # ====================================================================

        result = MagneticDesignResult(
            core_name=core_name,
            core_geometry=core_geom,
            core_material=mag_spec.core_material,
            core_loss_coefficients=coefficients,
            n_primary=n_turns,
            flux_density_peak=b_peak,
            flux_density_ac=b_ac,
            inductance_magnetizing=inductance,
            primary_winding=winding,
            core_loss=core_loss,
            copper_loss_primary=winding.copper_loss,
            total_loss=total_loss,
            efficiency=efficiency,
            temp_rise_estimate=temp_rise,
            kg_value=kg_actual_1 if core_name == core_name_1 else kg_actual_2,
            area_product=core_geom.core_area * core_geom.window_area,
            window_utilization_actual=ku_actual,
        )

        designs.append(result)

    print("=" * 80)
    print("OUTPUT INDUCTOR DESIGN COMPLETE")
    print("=" * 80)
    print()

    return designs[0], designs[1]


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("PSFB Output Inductor Design Tool")
    print("=" * 80)
    print()

    # Example: 6.6kW Marine PSFB (3× 2.2kW phases @ 250V output)
    # Each phase: 2200W / 250V = 8.8A
    # 3-phase interleaved with 120° phase shift

    inductor_spec = OutputInductorSpec(
        vout_nom=250.0,
        iout_nom=8.8,  # Per phase
        iout_max=10.0,  # Per phase (with margin)
        current_ripple_percent=30.0,  # 30% ripple
        frequency=100e3,
        duty_cycle_nom=0.45,
        n_phases=3,
        phase_shift_deg=120.0,
    )

    mag_spec = MagneticDesignSpec(
        power=2200.0,
        frequency=100e3,
        temp_ambient=40.0,
        temp_rise_max=60.0,
        current_density_max=5.0,
        window_utilization=0.5,
        flux_density_max=0.3,
        core_material=CoreMaterial.FERRITE_3C95,
    )

    # Perform design
    pq_design, e_design = design_output_inductor(
        inductor_spec=inductor_spec,
        mag_spec=mag_spec,
        core_family="PQ",
        alternative_family="E",
    )

    print("\nRecommended Design:")
    print(f"  Core: {pq_design.core_name}")
    print(f"  Inductance: {pq_design.inductance_magnetizing * 1e6:.1f} µH")
    print(f"  Turns: {pq_design.n_primary}")
    print(f"  Total Loss: {pq_design.total_loss:.2f} W per phase")
    print(f"  Efficiency: {pq_design.efficiency:.2f}%")

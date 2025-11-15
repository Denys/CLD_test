"""
Transformer Design for Phase-Shifted Full-Bridge Converters

Designs high-frequency isolation transformers for PSFB converters with:
- Optimal turns ratio for voltage transformation
- Controlled leakage inductance for ZVS operation
- Minimized core and winding losses
- Thermal management for 2.2kW per phase operation

The PSFB transformer must:
1. Provide galvanic isolation between primary (400V) and secondary (250V)
2. Handle full power transfer with minimal losses
3. Have sufficient leakage inductance to work with resonant inductor for ZVS
4. Maintain good coupling to minimize duty cycle loss
5. Operate efficiently across the full load range

Key Design References:
- McLyman "Transformer and Inductor Design Handbook" 4th Ed., Chapter 3
- Erickson & Maksimovic "Fundamentals of Power Electronics" 3rd Ed., Ch. 13-14
- Infineon "Design Guide for Phase-Shifted Full-Bridge Converters"
- Colonel McLyman's Area Product (Kg) method for core selection

Design Methodology:
1. Calculate turns ratio from voltage requirements
2. Determine apparent power and operating flux density
3. Use Kg method to select appropriate core
4. Design primary winding (minimize AC resistance)
5. Design secondary winding (high current capability)
6. Optimize winding interleaving to control leakage inductance
7. Calculate all losses (core, primary copper, secondary copper)
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
        calculate_kg_fe,
        select_core_by_kg,
        calculate_number_of_turns,
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
        calculate_kg_fe,
        select_core_by_kg,
        calculate_number_of_turns,
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
class TransformerSpec:
    """Transformer design specification"""
    # Voltage requirements
    vin_min: float  # Minimum input voltage (V)
    vin_nom: float  # Nominal input voltage (V)
    vin_max: float  # Maximum input voltage (V)
    vout_nom: float  # Nominal output voltage (V)
    vout_regulation: float = 0.05  # Output voltage regulation (5%)

    # Power requirements
    power_output: float  # Output power per phase (W)
    efficiency_target: float = 0.96  # Target efficiency (96%)

    # Operating conditions
    frequency: float  # Switching frequency (Hz)
    duty_cycle_nom: float = 0.45  # Nominal duty cycle (0.45 max for PSFB)
    duty_cycle_min: float = 0.1  # Minimum duty cycle
    duty_cycle_max: float = 0.48  # Maximum duty cycle (leave margin for dead time)

    # Magnetic requirements
    leakage_inductance_target: Optional[float] = None  # Target leakage (H)
    leakage_inductance_max: float = 10e-6  # Maximum acceptable leakage (H)
    magnetizing_inductance_min: float = 100e-6  # Minimum magnetizing inductance (H)

    # Rectifier configuration
    secondary_rectifier: str = "full_bridge"  # "full_bridge" or "center_tap"


def calculate_turns_ratio(
    vin_nom: float,
    vout_nom: float,
    duty_cycle_nom: float = 0.45,
    rectifier_type: str = "full_bridge",
    voltage_drops: float = 2.0,
) -> Tuple[float, int, int]:
    """
    Calculate transformer turns ratio.

    For PSFB with full-bridge rectifier:
    Vout = Vin × D × n × η - V_drops

    Where:
        n = N_pri / N_sec (turns ratio)
        D = duty cycle
        η = rectifier efficiency
        V_drops = voltage drops in diodes/MOSFETs and wiring

    Args:
        vin_nom: Nominal input voltage (V)
        vout_nom: Nominal output voltage (V)
        duty_cycle_nom: Nominal duty cycle (typical 0.45)
        rectifier_type: "full_bridge" or "center_tap"
        voltage_drops: Estimated voltage drops (V)

    Returns:
        Tuple of (turns_ratio, n_primary_suggested, n_secondary_suggested)
    """
    # Account for voltage drops
    vout_transformer = vout_nom + voltage_drops

    # For full-bridge primary: V_pri_effective = Vin
    # For full-bridge secondary: V_sec_effective = V_pri × D / n
    # Therefore: n = (Vin × D) / Vout_transformer

    turns_ratio = (vin_nom * duty_cycle_nom) / vout_transformer

    # Suggest integer turn counts
    # Start with reasonable primary turns for 100kHz operation
    # For ferrite at 100kHz with B ≈ 0.2-0.3T:
    # Using Faraday: V = 4 × f × N × B × Ac
    # For typical PQ cores: Ac ≈ 200-500 mm² = 2-5 × 10⁻⁴ m²
    # Example: V = 400V, f = 100kHz, B = 0.25T, Ac = 300mm²
    # N_pri = V / (4 × f × B × Ac) = 400 / (4 × 100e3 × 0.25 × 3e-4) ≈ 13 turns

    # Start with a reasonable range: 12-20 turns primary
    for n_pri in range(12, 25):
        n_sec = round(n_pri / turns_ratio)
        actual_ratio = n_pri / n_sec
        error = abs(actual_ratio - turns_ratio) / turns_ratio

        if error < 0.05:  # Within 5% of target
            return turns_ratio, n_pri, n_sec

    # If no good match, use 16 primary as baseline (from example)
    n_pri = 16
    n_sec = round(n_pri / turns_ratio)
    actual_ratio = n_pri / n_sec

    return actual_ratio, n_pri, n_sec


def calculate_magnetizing_inductance(
    n_primary: int,
    core_area: float,
    core_path_length: float,
    core_permeability: float = 2000,
    air_gap: float = 0.0,
) -> float:
    """
    Calculate magnetizing inductance of transformer.

    For ungapped core:
    L_mag = (μ₀ × μᵣ × N² × Ac) / lc

    For gapped core:
    L_mag = (μ₀ × N² × Ac) / (lc/μᵣ + lg)
          ≈ (μ₀ × N² × Ac) / lg  (for lg >> lc/μᵣ)

    Args:
        n_primary: Number of primary turns
        core_area: Core cross-sectional area (m²)
        core_path_length: Magnetic path length (m)
        core_permeability: Relative permeability of core material
        air_gap: Air gap length (m), 0 for ungapped

    Returns:
        Magnetizing inductance (H)
    """
    mu_0 = 4 * np.pi * 1e-7  # H/m

    if air_gap > 0:
        # Gapped core (air gap dominates)
        reluctance_gap = air_gap / (mu_0 * core_area)
        reluctance_core = core_path_length / (mu_0 * core_permeability * core_area)
        reluctance_total = reluctance_gap + reluctance_core

        # For typical ferrite gap: reluctance_gap >> reluctance_core
        l_mag = (n_primary ** 2) / reluctance_total
    else:
        # Ungapped core
        l_mag = (mu_0 * core_permeability * n_primary ** 2 * core_area) / core_path_length

    return l_mag


def estimate_leakage_inductance(
    n_primary: int,
    core_area: float,
    window_height: float,
    window_width: float,
    winding_thickness_total: float,
    interleaving_factor: float = 1.0,
) -> float:
    """
    Estimate leakage inductance using empirical model.

    Leakage inductance depends on:
    - Winding geometry (spacing between primary and secondary)
    - Window dimensions
    - Number of turns
    - Interleaving (reduces leakage)

    Simplified formula:
    L_leak ≈ μ₀ × N² × MLT × (total_winding_thickness) / (3 × window_height)

    With interleaving: L_leak_actual = L_leak / interleaving_factor²

    Args:
        n_primary: Number of primary turns
        core_area: Core cross-sectional area (m²)
        window_height: Bobbin window height (m)
        window_width: Bobbin window width (m)
        winding_thickness_total: Total radial build (primary + secondary + insulation) (m)
        interleaving_factor: Interleaving factor (1.0 = no interleaving, 2.0 = full interleaving)

    Returns:
        Leakage inductance (H)
    """
    mu_0 = 4 * np.pi * 1e-7  # H/m

    # Mean length of turn (approximate from window dimensions)
    mlt = 2 * (window_height + window_width)

    # Leakage inductance (empirical formula)
    l_leak_base = mu_0 * (n_primary ** 2) * mlt * winding_thickness_total / (3 * window_height)

    # Reduce by interleaving
    l_leak = l_leak_base / (interleaving_factor ** 2)

    return l_leak


def design_transformer(
    xfmr_spec: TransformerSpec,
    mag_spec: MagneticDesignSpec,
    core_family: str = "PQ",
    alternative_family: str = "ETD",
) -> Tuple[MagneticDesignResult, MagneticDesignResult]:
    """
    Complete transformer design for PSFB converter.

    Optimizes for efficiency, thermal performance, and ZVS compatibility.

    Args:
        xfmr_spec: Transformer specifications
        mag_spec: Magnetic design specifications
        core_family: Primary core family ("PQ")
        alternative_family: Alternative core family ("ETD", "E")

    Returns:
        Tuple of (primary_design, alternative_design)
    """
    print("=" * 80)
    print("PSFB TRANSFORMER DESIGN")
    print("=" * 80)
    print()

    # ========================================================================
    # Step 1: Calculate Turns Ratio
    # ========================================================================
    print("Step 1: Turns Ratio Calculation")
    print("-" * 80)

    turns_ratio, n_pri_suggested, n_sec_suggested = calculate_turns_ratio(
        xfmr_spec.vin_nom,
        xfmr_spec.vout_nom,
        xfmr_spec.duty_cycle_nom,
        xfmr_spec.secondary_rectifier,
        voltage_drops=2.0,
    )

    print(f"Voltage Transformation: {xfmr_spec.vin_nom:.0f}V → {xfmr_spec.vout_nom:.0f}V")
    print(f"Turns Ratio (n):     {turns_ratio:.4f} (N_pri / N_sec)")
    print(f"Suggested Turns:     {n_pri_suggested}:{n_sec_suggested}")
    print(f"Actual Ratio:        {n_pri_suggested / n_sec_suggested:.4f}")
    print()

    # ========================================================================
    # Step 2: Calculate Apparent Power and Currents
    # ========================================================================
    print("Step 2: Power and Current Calculation")
    print("-" * 80)

    # Output current
    i_out = xfmr_spec.power_output / xfmr_spec.vout_nom

    # Secondary RMS current (for full-bridge rectifier, continuous conduction)
    # Each secondary winding conducts for half the period at full load
    # I_sec_rms = I_out / √2 for sinusoidal, but square wave for PSFB
    # For square wave: I_sec_rms ≈ I_out / √(2 × D)
    i_sec_rms = i_out / np.sqrt(2 * xfmr_spec.duty_cycle_nom)

    # Primary RMS current
    # Reflected from secondary: I_pri = I_sec × n
    # But primary conducts differently based on PSFB operation
    # For full-bridge: I_pri_rms ≈ I_sec_rms × (1/n) × √(2D)
    i_pri_rms = i_sec_rms / turns_ratio

    # Apparent power (VA)
    # For transformer: S = V_pri × I_pri = V_sec × I_sec
    power_apparent = xfmr_spec.vin_nom * i_pri_rms

    print(f"Output Power:        {xfmr_spec.power_output:.0f} W")
    print(f"Output Current:      {i_out:.2f} A")
    print(f"Apparent Power:      {power_apparent:.0f} VA")
    print()
    print(f"Primary RMS Current: {i_pri_rms:.2f} A")
    print(f"Secondary RMS Current: {i_sec_rms:.2f} A")
    print()

    # ========================================================================
    # Step 3: Core Selection Using Kg Method
    # ========================================================================
    print("Step 3: Core Selection (Kg Method)")
    print("-" * 80)

    # Calculate required Kg
    # Use apparent power for transformer design
    kg_required = calculate_required_kg(
        power=power_apparent,
        frequency=xfmr_spec.frequency,
        flux_density_max=mag_spec.flux_density_max,
        current_density_max=mag_spec.current_density_max,
        window_utilization=mag_spec.window_utilization,
        topology_factor=4.44,  # Transformer topology factor
    )

    print(f"Required Kg:         {kg_required:.2e} m⁵")
    print(f"Design Parameters:")
    print(f"  Flux density:      {mag_spec.flux_density_max:.2f} T")
    print(f"  Current density:   {mag_spec.current_density_max:.1f} A/mm²")
    print(f"  Window util:       {mag_spec.window_utilization:.2f}")
    print()

    # Select core from primary family
    core_name_1, core_geom_1, kg_actual_1 = select_core_by_kg(
        kg_required,
        core_family=core_family,
        material=mag_spec.core_material,
        margin=1.2,  # 20% margin for transformer
    )

    print(f"Selected Core ({core_family} family): {core_name_1}")
    print(f"  Kg actual:         {kg_actual_1:.2e} m⁵  (margin: {kg_actual_1/kg_required:.1f}x)")
    print(f"  Core area:         {core_geom_1.core_area * 1e6:.1f} mm²")
    print(f"  Window area:       {core_geom_1.window_area * 1e6:.1f} mm²")
    print(f"  Area product:      {core_geom_1.core_area * core_geom_1.window_area * 1e12:.1f} mm⁴")
    print(f"  MLT:               {core_geom_1.mean_length_turn * 1000:.1f} mm")
    print(f"  Volume:            {core_geom_1.volume * 1e6:.1f} cm³")
    print()

    # Select alternative core
    core_name_2, core_geom_2, kg_actual_2 = select_core_by_kg(
        kg_required,
        core_family=alternative_family,
        material=mag_spec.core_material,
        margin=1.2,
    )

    print(f"Alternative Core ({alternative_family} family): {core_name_2}")
    print(f"  Kg actual:         {kg_actual_2:.2e} m⁵  (margin: {kg_actual_2/kg_required:.1f}x)")
    print(f"  Core area:         {core_geom_2.core_area * 1e6:.1f} mm²")
    print(f"  Window area:       {core_geom_2.window_area * 1e6:.1f} mm²")
    print()

    # Complete design for both cores
    designs = []

    for core_name, core_geom in [(core_name_1, core_geom_1), (core_name_2, core_geom_2)]:
        print("=" * 80)
        print(f"Detailed Design: {core_name}")
        print("=" * 80)
        print()

        # ====================================================================
        # Step 4: Calculate Number of Turns
        # ====================================================================
        print("Step 4: Turn Count Verification")
        print("-" * 80)

        # Verify/recalculate primary turns using Faraday's law
        # V = 4 × f × N × B × Ac (for square wave)
        # N = V / (4 × f × B × Ac)

        n_pri_calculated = calculate_number_of_turns(
            voltage=xfmr_spec.vin_nom * xfmr_spec.duty_cycle_max,  # Max volt-seconds
            frequency=xfmr_spec.frequency,
            flux_density_ac=mag_spec.flux_density_max,
            core_area=core_geom.core_area,
            waveform_factor=4.0,  # Square wave
        )

        # Use suggested turns if close, otherwise use calculated
        if abs(n_pri_calculated - n_pri_suggested) <= 2:
            n_pri = n_pri_suggested
            n_sec = n_sec_suggested
        else:
            n_pri = n_pri_calculated
            n_sec = max(1, round(n_pri / turns_ratio))

        # Recalculate actual turns ratio
        turns_ratio_actual = n_pri / n_sec

        # Verify flux density at maximum duty cycle
        b_peak = (xfmr_spec.vin_nom * xfmr_spec.duty_cycle_max) / (
            4.0 * xfmr_spec.frequency * n_pri * core_geom.core_area
        )

        print(f"Primary Turns:       {n_pri}")
        print(f"Secondary Turns:     {n_sec}")
        print(f"Turns Ratio:         {turns_ratio_actual:.4f} (target: {turns_ratio:.4f})")
        print(f"Peak Flux Density:   {b_peak:.3f} T")
        print()

        if b_peak > 0.35:
            print(f"  WARNING: B_peak = {b_peak:.3f}T exceeds recommended limit!")
            print()

        # ====================================================================
        # Step 5: Primary Winding Design
        # ====================================================================
        print("Step 5: Primary Winding Design")
        print("-" * 80)

        primary_winding = design_winding(
            current_rms=i_pri_rms,
            n_turns=n_pri,
            mlt=core_geom.mean_length_turn,
            frequency=xfmr_spec.frequency,
            current_density_max=mag_spec.current_density_max,
            n_layers_target=1,  # Try single layer first
            use_litz=True if xfmr_spec.frequency > 100e3 else False,
            temp=mag_spec.temp_ambient + mag_spec.temp_rise_max / 2,
        )

        print(f"Wire Diameter:       {primary_winding.wire_diameter:.2f} mm (insulated)")
        print(f"                     {primary_winding.wire_diameter_bare:.2f} mm (bare)")
        if primary_winding.n_strands > 1:
            print(f"Litz Configuration:  {primary_winding.n_strands} strands × {primary_winding.strand_diameter:.2f} mm")
        print(f"Number of Layers:    {primary_winding.n_layers}")
        print(f"R_dc:                {primary_winding.resistance_dc * 1000:.1f} mΩ")
        print(f"R_ac:                {primary_winding.resistance_ac * 1000:.1f} mΩ  (AC/DC ratio: {primary_winding.resistance_ac/primary_winding.resistance_dc:.2f})")
        print(f"Copper Loss:         {primary_winding.copper_loss:.2f} W")
        print(f"Current Density:     {primary_winding.current_density:.2f} A/mm²")
        print()

        # ====================================================================
        # Step 6: Secondary Winding Design
        # ====================================================================
        print("Step 6: Secondary Winding Design")
        print("-" * 80)

        secondary_winding = design_winding(
            current_rms=i_sec_rms,
            n_turns=n_sec,
            mlt=core_geom.mean_length_turn,
            frequency=xfmr_spec.frequency,
            current_density_max=mag_spec.current_density_max * 0.8,  # Lower for secondary (more layers)
            n_layers_target=2,  # Secondary typically needs more layers
            use_litz=True if xfmr_spec.frequency > 100e3 else False,
            temp=mag_spec.temp_ambient + mag_spec.temp_rise_max / 2,
        )

        print(f"Wire Diameter:       {secondary_winding.wire_diameter:.2f} mm (insulated)")
        print(f"                     {secondary_winding.wire_diameter_bare:.2f} mm (bare)")
        if secondary_winding.n_strands > 1:
            print(f"Litz Configuration:  {secondary_winding.n_strands} strands × {secondary_winding.strand_diameter:.2f} mm")
        print(f"Number of Layers:    {secondary_winding.n_layers}")
        print(f"R_dc:                {secondary_winding.resistance_dc * 1000:.1f} mΩ")
        print(f"R_ac:                {secondary_winding.resistance_ac * 1000:.1f} mΩ  (AC/DC ratio: {secondary_winding.resistance_ac/secondary_winding.resistance_dc:.2f})")
        print(f"Copper Loss:         {secondary_winding.copper_loss:.2f} W")
        print(f"Current Density:     {secondary_winding.current_density:.2f} A/mm²")
        print()

        # ====================================================================
        # Step 7: Magnetic Properties
        # ====================================================================
        print("Step 7: Magnetic Properties")
        print("-" * 80)

        # Magnetizing inductance (ungapped transformer)
        l_mag = calculate_magnetizing_inductance(
            n_pri,
            core_geom.core_area,
            core_geom.path_length,
            core_permeability=2000,  # Typical for 3C95 ferrite
            air_gap=0.0,
        )

        # Estimate leakage inductance
        # Total winding thickness (simplified)
        winding_thickness = (
            primary_winding.n_layers * primary_winding.wire_diameter +
            secondary_winding.n_layers * secondary_winding.wire_diameter +
            2.0  # Insulation and spacing (mm)
        ) / 1000.0  # Convert to meters

        l_leak = estimate_leakage_inductance(
            n_pri,
            core_geom.core_area,
            np.sqrt(core_geom.window_area),  # Approximate window height
            np.sqrt(core_geom.window_area),  # Approximate window width
            winding_thickness,
            interleaving_factor=1.0,  # No interleaving for initial design
        )

        print(f"Magnetizing Inductance: {l_mag * 1e6:.0f} µH  (referred to primary)")
        print(f"Leakage Inductance:     {l_leak * 1e6:.2f} µH  (estimated)")
        print()

        if l_mag < xfmr_spec.magnetizing_inductance_min:
            print(f"  WARNING: L_mag too low! May need air gap or more turns.")
            print()

        if l_leak > xfmr_spec.leakage_inductance_max:
            print(f"  WARNING: L_leak too high! Consider winding interleaving.")
            print()

        # ====================================================================
        # Step 8: Core Loss
        # ====================================================================
        print("Step 8: Core Loss Calculation")
        print("-" * 80)

        # Get Steinmetz coefficients
        coefficients = get_core_loss_coefficients(
            mag_spec.core_material,
            mag_spec.temp_ambient + 40
        )

        # AC flux density (peak value for Steinmetz)
        b_ac = b_peak

        # Core loss
        core_loss = calculate_core_loss_steinmetz(
            core_geom,
            coefficients,
            xfmr_spec.frequency,
            b_ac
        )

        print(f"Steinmetz Coefficients ({mag_spec.core_material.value}):")
        print(f"  k = {coefficients.k:.2e}")
        print(f"  α = {coefficients.alpha:.3f}")
        print(f"  β = {coefficients.beta:.3f}")
        print(f"B_ac:                {b_ac * 1000:.1f} mT")
        print(f"Core Loss:           {core_loss:.2f} W")
        print()

        # ====================================================================
        # Step 9: Total Loss and Efficiency
        # ====================================================================
        print("Step 9: Loss Summary and Efficiency")
        print("-" * 80)

        total_copper_loss = primary_winding.copper_loss + secondary_winding.copper_loss
        total_loss = core_loss + total_copper_loss
        efficiency = 100.0 * (1.0 - total_loss / xfmr_spec.power_output)

        print(f"Primary Copper Loss:   {primary_winding.copper_loss:.2f} W")
        print(f"Secondary Copper Loss: {secondary_winding.copper_loss:.2f} W")
        print(f"Core Loss:             {core_loss:.2f} W")
        print(f"Total Loss:            {total_loss:.2f} W")
        print(f"Efficiency:            {efficiency:.2f}%")
        print()

        # ====================================================================
        # Step 10: Thermal Analysis
        # ====================================================================
        print("Step 10: Thermal Analysis")
        print("-" * 80)

        # Temperature rise estimate
        temp_rise = estimate_temperature_rise(
            total_loss,
            core_geom.surface_area,
            cooling_coefficient=20.0,  # Forced air cooling
        )

        # Window utilization
        ku_actual = calculate_window_utilization(
            primary_winding,
            core_geom.window_area,
            secondary_winding
        )

        print(f"Temperature Rise:      {temp_rise:.1f} °C")
        print(f"Hotspot Temperature:   {mag_spec.temp_ambient + temp_rise:.1f} °C")
        print(f"Window Utilization:    {ku_actual * 100:.1f}%")
        print()

        if temp_rise > mag_spec.temp_rise_max:
            print(f"  WARNING: Temperature rise exceeds limit!")
            print(f"  Consider: larger core, better cooling, or lower current density")
            print()

        if ku_actual > 0.6:
            print(f"  WARNING: Window utilization very high! May be difficult to wind.")
            print()
        elif ku_actual < 0.3:
            print(f"  NOTE: Low window utilization - could use smaller core.")
            print()

        # ====================================================================
        # Create Result
        # ====================================================================

        result = MagneticDesignResult(
            core_name=core_name,
            core_geometry=core_geom,
            core_material=mag_spec.core_material,
            core_loss_coefficients=coefficients,
            n_primary=n_pri,
            n_secondary=n_sec,
            turns_ratio=turns_ratio_actual,
            flux_density_peak=b_peak,
            flux_density_ac=b_ac,
            inductance_magnetizing=l_mag,
            inductance_leakage=l_leak,
            primary_winding=primary_winding,
            secondary_winding=secondary_winding,
            core_loss=core_loss,
            copper_loss_primary=primary_winding.copper_loss,
            copper_loss_secondary=secondary_winding.copper_loss,
            total_loss=total_loss,
            efficiency=efficiency,
            temp_rise_estimate=temp_rise,
            kg_value=kg_actual_1 if core_name == core_name_1 else kg_actual_2,
            area_product=core_geom.core_area * core_geom.window_area,
            window_utilization_actual=ku_actual,
        )

        designs.append(result)

    print("=" * 80)
    print("TRANSFORMER DESIGN COMPLETE")
    print("=" * 80)
    print()

    return designs[0], designs[1]


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("PSFB Transformer Design Tool")
    print("=" * 80)
    print()

    # Example: 6.6kW Marine PSFB (2.2kW per phase)
    # 400V → 250V transformation

    xfmr_spec = TransformerSpec(
        vin_min=360.0,
        vin_nom=400.0,
        vin_max=440.0,
        vout_nom=250.0,
        vout_regulation=0.05,
        power_output=2200.0,  # Per phase
        efficiency_target=0.96,
        frequency=100e3,
        duty_cycle_nom=0.45,
        duty_cycle_min=0.1,
        duty_cycle_max=0.48,
        leakage_inductance_max=8e-6,
        magnetizing_inductance_min=150e-6,
        secondary_rectifier="full_bridge",
    )

    mag_spec = MagneticDesignSpec(
        power=2200.0,
        frequency=100e3,
        temp_ambient=40.0,
        temp_rise_max=60.0,
        current_density_max=5.0,
        window_utilization=0.5,
        flux_density_max=0.25,
        core_material=CoreMaterial.FERRITE_3C95,
    )

    # Perform design
    pq_design, etd_design = design_transformer(
        xfmr_spec=xfmr_spec,
        mag_spec=mag_spec,
        core_family="PQ",
        alternative_family="ETD",
    )

    print("\nRecommended Design:")
    print(f"  Core: {pq_design.core_name}")
    print(f"  Turns: {pq_design.n_primary}:{pq_design.n_secondary}")
    print(f"  Total Loss: {pq_design.total_loss:.2f} W")
    print(f"  Efficiency: {pq_design.efficiency:.2f}%")

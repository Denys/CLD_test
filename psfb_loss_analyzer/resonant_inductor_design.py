"""
Resonant Inductor Design for PSFB ZVS Operation

Designs the resonant inductors (Lr) for Phase-Shifted Full-Bridge converters
to achieve Zero-Voltage Switching (ZVS) from full load down to light loads (10-30%).

The resonant inductor works with MOSFET output capacitance to create ZVS conditions:
- At turn-off: Lr and Coss resonate to discharge/charge MOSFET drain-source voltage
- Dead time must be sufficient for complete voltage transition
- At light load: Magnetizing current must supplement load current for ZVS

Key Design References:
- UCC28951 Phase-Shifted Full-Bridge Controller Datasheet (TI)
- Infineon "Design Guide for Phase-Shifted Full-Bridge Converters"
- Erickson & Maksimovic "Fundamentals of Power Electronics" 3rd Ed.
- McLyman "Transformer and Inductor Design Handbook" 4th Ed.

Design Methodology:
1. Calculate minimum resonant current for ZVS at full and light loads
2. Select Lr value that ensures ZVS down to minimum load percentage
3. Use Kg method to size inductor core
4. Design winding with minimal AC resistance
5. Validate thermal performance

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
    from .circuit_params import CoreMaterial, MOSFETParameters
except ImportError:
    from magnetics_design import (
        MagneticDesignSpec,
        MagneticDesignResult,
        WindingDesign,
        calculate_required_kg,
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
    from circuit_params import CoreMaterial, MOSFETParameters


@dataclass
class ZVSRequirements:
    """ZVS operating requirements for resonant inductor design"""
    # MOSFET parameters
    mosfet_coss: float  # Output capacitance at switching voltage (F)
    mosfet_vds_max: float  # Maximum drain-source voltage (V)
    n_mosfets_parallel: int = 2  # Number of parallel MOSFETs per leg (2 for half-bridge)

    # Operating conditions
    vin_min: float = 360.0  # Minimum input voltage (V)
    vin_nom: float = 400.0  # Nominal input voltage (V)
    vin_max: float = 440.0  # Maximum input voltage (V)

    # Load range for ZVS
    load_full: float = 2200.0  # Full load power per phase (W)
    load_min_zvs: float = 220.0  # Minimum load for ZVS (W) - 10% of full load
    load_min_percent: float = 10.0  # Minimum load percentage (%)

    # Transformer parameters
    turns_ratio: float = 0.533  # n = N_pri / N_sec (16:30 for 400V→250V)
    magnetizing_inductance: float = 200e-6  # Transformer magnetizing inductance (H)

    # Timing
    frequency: float = 100e3  # Switching frequency (Hz)
    dead_time_target: float = 500e-9  # Target dead time (s)

    # Safety margins
    zvs_energy_margin: float = 1.5  # ZVS energy margin (1.5 = 50% extra)


def calculate_zvs_inductor_value(
    zvs_req: ZVSRequirements,
    design_point: str = "light_load",
) -> Tuple[float, float, float]:
    """
    Calculate required resonant inductance for ZVS operation.

    ZVS Energy Balance:
    ½ × Lr × I_res² ≥ ½ × Coss_total × Vin²

    Minimum resonant current:
    I_res_min = Vin × √(Coss_total / Lr) × margin

    At light load, resonant current consists of:
    - Reflected load current: I_load_reflected = P_out / (Vin × n × duty)
    - Magnetizing current: I_mag = Vin × t_on / (2 × Lm)
    - Resonant inductor contributes: I_lr

    For ZVS at minimum load:
    I_total = I_load_reflected + I_mag ≥ I_res_min

    Args:
        zvs_req: ZVS requirements and operating conditions
        design_point: "light_load" or "full_load" optimization

    Returns:
        Tuple of (Lr_required, I_resonant_min, dead_time_required)
    """
    # Total output capacitance (2 MOSFETs in series per leg, 2 legs switch)
    # When Q1-Q2 leg switches: Q1_Coss and Q2_Coss in series
    # Effective: Coss_eff = Coss / 2 (series) × 2 (both legs) = Coss
    coss_total = zvs_req.mosfet_coss * zvs_req.n_mosfets_parallel

    if design_point == "light_load":
        # Design for light load ZVS (most challenging condition)
        v_in = zvs_req.vin_max  # Worst case: highest voltage to discharge
        p_out = zvs_req.load_min_zvs

        # Period and on-time at 50% duty (typical PSFB at light load)
        t_period = 1.0 / zvs_req.frequency
        duty_typical = 0.5
        t_on = duty_typical * t_period / 2  # Half-bridge leg on-time

        # Magnetizing current contribution (half-period average)
        i_mag = v_in * t_on / (2 * zvs_req.magnetizing_inductance)

        # Reflected load current (primary side, average)
        # For PSFB: I_pri_avg ≈ P_out / (Vin × η) / duty
        efficiency_est = 0.95
        i_load_reflected = p_out / (v_in * efficiency_est * duty_typical)

        # Available current for ZVS transition
        i_available = i_load_reflected + i_mag

        # Required resonant current for ZVS (with margin)
        # From energy balance: I_res = Vin × √(Coss / Lr)
        # We want: I_available ≥ I_res_min
        # Therefore: Lr ≤ Coss × (Vin / I_available)²

        lr_max = coss_total * (v_in / (i_available * zvs_req.zvs_energy_margin))**2

        # Choose Lr with some margin (use 70% of maximum)
        lr_design = lr_max * 0.7

    else:  # full_load
        # Design for full load (easier ZVS condition)
        v_in = zvs_req.vin_nom
        p_out = zvs_req.load_full

        # At full load, plenty of current available
        # Design for reasonable dead time and low conduction loss

        # Target dead time for resonant transition
        t_dead = zvs_req.dead_time_target

        # Resonant half-period: t_res = π × √(Lr × Coss)
        # We want: t_dead ≈ t_res
        # Therefore: Lr = (t_dead / π)² / Coss

        lr_design = (t_dead / np.pi)**2 / coss_total

    # Calculate resulting resonant parameters
    i_resonant_min = v_in * np.sqrt(coss_total / lr_design)

    # Dead time required for complete transition
    t_dead_required = np.pi * np.sqrt(lr_design * coss_total)

    return lr_design, i_resonant_min, t_dead_required


def calculate_inductor_current_waveform(
    lr_value: float,
    vin: float,
    vout: float,
    power: float,
    frequency: float,
    turns_ratio: float,
    duty_cycle: float = 0.5,
) -> Tuple[float, float, float, float]:
    """
    Calculate resonant inductor current waveform parameters.

    In PSFB, the resonant inductor current consists of:
    1. DC component (load current reflected to primary)
    2. AC component (magnetizing + resonant)

    Args:
        lr_value: Resonant inductance (H)
        vin: Input voltage (V)
        vout: Output voltage (V)
        power: Output power (W)
        frequency: Switching frequency (Hz)
        turns_ratio: Transformer turns ratio n = Npri/Nsec
        duty_cycle: Duty cycle (0-1)

    Returns:
        Tuple of (I_dc, I_peak, I_rms, I_ripple_pp)
    """
    # Output current
    i_out = power / vout

    # Primary side DC current (reflected through transformer)
    # For full-bridge: I_pri = I_sec / (n × 2) for 50% duty
    i_dc = i_out / (turns_ratio * 2.0)

    # Current ripple from resonant inductance
    # During on-time, voltage across Lr ≈ Vin - Vout/n
    v_lr_on = vin - vout / turns_ratio

    # During off-time (freewheeling), voltage across Lr ≈ -Vout/n
    v_lr_off = -vout / turns_ratio

    # On-time
    t_on = duty_cycle / frequency

    # Current ripple (triangular approximation)
    di_on = v_lr_on * t_on / lr_value
    i_ripple_pp = abs(di_on)

    # Peak current
    i_peak = i_dc + i_ripple_pp / 2

    # RMS current (DC + triangular ripple)
    # I_rms² = I_dc² + (I_ripple_pp² / 12)
    i_rms = np.sqrt(i_dc**2 + (i_ripple_pp**2 / 12))

    return i_dc, i_peak, i_rms, i_ripple_pp


def design_resonant_inductor(
    zvs_req: ZVSRequirements,
    spec: MagneticDesignSpec,
    core_family: str = "PQ",
    alternative_family: str = "ETD",
) -> Tuple[MagneticDesignResult, MagneticDesignResult]:
    """
    Complete resonant inductor design for PSFB ZVS operation.

    Optimizes for ZVS operation from full load down to light load (10-30%).

    Args:
        zvs_req: ZVS requirements
        spec: Magnetic design specification
        core_family: Primary core family ("PQ")
        alternative_family: Alternative core family ("ETD", "E")

    Returns:
        Tuple of (primary_design, alternative_design)
    """
    print("=" * 80)
    print("PSFB RESONANT INDUCTOR DESIGN FOR ZVS OPERATION")
    print("=" * 80)
    print()

    # ========================================================================
    # Step 1: Calculate Required Inductance Value
    # ========================================================================
    print("Step 1: ZVS Inductance Calculation")
    print("-" * 80)

    lr_light, i_res_light, t_dead_light = calculate_zvs_inductor_value(
        zvs_req, design_point="light_load"
    )

    lr_full, i_res_full, t_dead_full = calculate_zvs_inductor_value(
        zvs_req, design_point="full_load"
    )

    print(f"Light Load ZVS Design (@ {zvs_req.load_min_percent}% load):")
    print(f"  Lr (max):        {lr_light * 1e6:.2f} µH")
    print(f"  I_res (min):     {i_res_light:.2f} A")
    print(f"  Dead time:       {t_dead_light * 1e9:.0f} ns")
    print()
    print(f"Full Load Design:")
    print(f"  Lr (target):     {lr_full * 1e6:.2f} µH")
    print(f"  I_res (min):     {i_res_full:.2f} A")
    print(f"  Dead time:       {t_dead_full * 1e9:.0f} ns")
    print()

    # Choose the design point (light load is more restrictive)
    if zvs_req.load_min_zvs < zvs_req.load_full * 0.3:
        lr_value = lr_light
        print(f"Selected Lr = {lr_value * 1e6:.2f} µH (optimized for light load ZVS)")
    else:
        lr_value = lr_full
        print(f"Selected Lr = {lr_value * 1e6:.2f} µH (optimized for full load)")
    print()

    # ========================================================================
    # Step 2: Calculate Current Waveform
    # ========================================================================
    print("Step 2: Current Waveform Analysis")
    print("-" * 80)

    # Full load current
    i_dc_full, i_peak_full, i_rms_full, i_ripple_full = calculate_inductor_current_waveform(
        lr_value,
        zvs_req.vin_nom,
        zvs_req.vin_nom * zvs_req.turns_ratio,  # Approximate Vout
        zvs_req.load_full,
        zvs_req.frequency,
        zvs_req.turns_ratio,
        duty_cycle=0.5,
    )

    # Light load current
    i_dc_light, i_peak_light, i_rms_light, i_ripple_light = calculate_inductor_current_waveform(
        lr_value,
        zvs_req.vin_max,
        zvs_req.vin_max * zvs_req.turns_ratio,
        zvs_req.load_min_zvs,
        zvs_req.frequency,
        zvs_req.turns_ratio,
        duty_cycle=0.5,
    )

    print(f"Full Load Current ({zvs_req.load_full:.0f}W):")
    print(f"  I_dc:            {i_dc_full:.2f} A")
    print(f"  I_peak:          {i_peak_full:.2f} A")
    print(f"  I_rms:           {i_rms_full:.2f} A")
    print(f"  I_ripple (p-p):  {i_ripple_full:.2f} A")
    print()
    print(f"Light Load Current ({zvs_req.load_min_zvs:.0f}W, {zvs_req.load_min_percent}%):")
    print(f"  I_dc:            {i_dc_light:.2f} A")
    print(f"  I_peak:          {i_peak_light:.2f} A")
    print(f"  I_rms:           {i_rms_light:.2f} A")
    print(f"  I_ripple (p-p):  {i_ripple_light:.2f} A")
    print()

    # Use full load RMS for thermal design
    i_rms_design = i_rms_full

    # ========================================================================
    # Step 3: Calculate Number of Turns
    # ========================================================================
    print("Step 3: Turn Count Calculation")
    print("-" * 80)

    # For inductor: L = (μ₀ × μᵣ × N² × Ac) / lc
    # Or using energy: L = N² / Reluctance
    # We'll use the volt-second approach with DC bias

    # Core selection will be done via Kg, but we need initial turns estimate
    # Use a typical core to start (PQ60/42)
    from .core_database import get_core_geometry
    core_initial = get_core_geometry("PQ60/42")

    # AL value (inductance per turn²) approximation for gapped core
    # For air gap: AL ≈ (μ₀ × Ac) / lg
    # Target gap for Lr and peak current
    # Peak flux: B_peak = (L × I_peak) / (N × Ac)
    # Choose B_peak < B_sat (avoid saturation)

    b_peak_target = 0.3  # Tesla (conservative for ferrite with gap)

    # Required turns: N = (L × I_peak) / (B_peak × Ac)
    n_turns_initial = int(np.ceil(
        (lr_value * i_peak_full) / (b_peak_target * core_initial.core_area)
    ))
    n_turns_initial = max(n_turns_initial, 5)  # Minimum 5 turns

    print(f"Initial turn count estimate: {n_turns_initial} turns")
    print(f"  (Based on B_peak = {b_peak_target} T, PQ60/42 core)")
    print()

    # ========================================================================
    # Step 4: Core Selection Using Kg Method
    # ========================================================================
    print("Step 4: Core Selection (Kg Method)")
    print("-" * 80)

    # For inductors, use Kg with topology factor = 4.0
    kg_required = calculate_required_kg(
        power=zvs_req.load_full,  # Use full load power
        frequency=zvs_req.frequency,
        flux_density_max=spec.flux_density_max,
        current_density_max=spec.current_density_max,
        window_utilization=spec.window_utilization,
        topology_factor=4.0,  # Inductor topology factor
    )

    print(f"Required Kg:     {kg_required:.2e} m⁵")
    print()

    # Select core from primary family
    core_name_1, core_geom_1, kg_actual_1 = select_core_by_kg(
        kg_required,
        core_family=core_family,
        material=spec.core_material,
        margin=1.1,
    )

    print(f"Selected Core ({core_family} family): {core_name_1}")
    print(f"  Kg actual:       {kg_actual_1:.2e} m⁵")
    print(f"  Core area:       {core_geom_1.core_area * 1e6:.1f} mm²")
    print(f"  Window area:     {core_geom_1.window_area * 1e6:.1f} mm²")
    print(f"  MLT:             {core_geom_1.mean_length_turn * 1000:.1f} mm")
    print(f"  Volume:          {core_geom_1.volume * 1e6:.1f} cm³")
    print()

    # Select alternative core
    core_name_2, core_geom_2, kg_actual_2 = select_core_by_kg(
        kg_required,
        core_family=alternative_family,
        material=spec.core_material,
        margin=1.1,
    )

    print(f"Alternative Core ({alternative_family} family): {core_name_2}")
    print(f"  Kg actual:       {kg_actual_2:.2e} m⁵")
    print(f"  Core area:       {core_geom_2.core_area * 1e6:.1f} mm²")
    print(f"  Window area:     {core_geom_2.window_area * 1e6:.1f} mm²")
    print()

    # Complete design for both cores
    designs = []

    for core_name, core_geom in [(core_name_1, core_geom_1), (core_name_2, core_geom_2)]:
        print("-" * 80)
        print(f"Detailed Design: {core_name}")
        print("-" * 80)

        # Recalculate turns for selected core
        n_turns = int(np.ceil(
            (lr_value * i_peak_full) / (b_peak_target * core_geom.core_area)
        ))
        n_turns = max(n_turns, 5)

        # Verify inductance with air gap
        # L = (μ₀ × N² × Ac) / lg
        # lg = (μ₀ × N² × Ac) / L
        mu_0 = 4 * np.pi * 1e-7
        air_gap_length = (mu_0 * n_turns**2 * core_geom.core_area) / lr_value

        print(f"Turns:           {n_turns}")
        print(f"Air gap:         {air_gap_length * 1000:.2f} mm")
        print()

        # Winding design
        winding = design_winding(
            current_rms=i_rms_design,
            n_turns=n_turns,
            mlt=core_geom.mean_length_turn,
            frequency=zvs_req.frequency,
            current_density_max=spec.current_density_max,
            n_layers_target=1,  # Single layer for inductor
            use_litz=False,  # Solid wire for inductor (lower frequency harmonics)
            temp=spec.temp_ambient + spec.temp_rise_max / 2,
        )

        print(f"Wire diameter:   {winding.wire_diameter:.2f} mm (insulated)")
        print(f"                 {winding.wire_diameter_bare:.2f} mm (bare)")
        print(f"R_dc:            {winding.resistance_dc * 1000:.1f} mΩ")
        print(f"R_ac:            {winding.resistance_ac * 1000:.1f} mΩ")
        print(f"Copper loss:     {winding.copper_loss:.2f} W")
        print(f"Current density: {winding.current_density:.2f} A/mm²")
        print()

        # Core loss calculation
        coefficients = get_core_loss_coefficients(spec.core_material, spec.temp_ambient + 40)

        # AC flux density (peak-to-peak ripple current creates flux swing)
        b_ac = (lr_value * i_ripple_full) / (n_turns * core_geom.core_area)

        core_loss = calculate_core_loss_steinmetz(
            core_geom, coefficients, zvs_req.frequency, b_ac
        )

        print(f"Core Loss Calculation:")
        print(f"  B_ac:            {b_ac * 1000:.1f} mT")
        print(f"  Core loss:       {core_loss:.2f} W")
        print()

        # Total loss and efficiency
        total_loss = winding.copper_loss + core_loss
        efficiency = 100.0 * (1.0 - total_loss / zvs_req.load_full)

        # Temperature rise estimate
        temp_rise = estimate_temperature_rise(
            total_loss,
            core_geom.surface_area,
            cooling_coefficient=20.0,  # Forced air
        )

        # Window utilization
        ku_actual = calculate_window_utilization(winding, core_geom.window_area)

        print(f"Performance Summary:")
        print(f"  Total loss:      {total_loss:.2f} W")
        print(f"  Efficiency:      {efficiency:.2f}%")
        print(f"  Temp rise:       {temp_rise:.1f} °C")
        print(f"  Window util:     {ku_actual * 100:.1f}%")
        print()

        # Create result
        result = MagneticDesignResult(
            core_name=core_name,
            core_geometry=core_geom,
            core_material=spec.core_material,
            core_loss_coefficients=coefficients,
            n_primary=n_turns,
            flux_density_peak=b_peak_target,
            flux_density_ac=b_ac,
            inductance_magnetizing=lr_value,
            primary_winding=winding,
            core_loss=core_loss,
            copper_loss_primary=winding.copper_loss,
            total_loss=total_loss,
            efficiency=efficiency,
            temp_rise_estimate=temp_rise,
            area_product=core_geom.window_area * core_geom.core_area,
            window_utilization_actual=ku_actual,
        )

        designs.append(result)

    print("=" * 80)
    print("RESONANT INDUCTOR DESIGN COMPLETE")
    print("=" * 80)
    print()

    return designs[0], designs[1]


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("PSFB Resonant Inductor Design Tool")
    print("=" * 80)
    print()

    # Example: 6.6kW Marine PSFB (2.2kW per phase)
    # Using Infineon IMZA65R020M2H MOSFETs

    from .circuit_params import MOSFETParameters, CapacitanceVsVoltage

    # MOSFET parameters (IMZA65R020M2H)
    mosfet = MOSFETParameters(
        part_number="IMZA65R020M2H",
        v_dss=650.0,
        i_d_continuous=90.0,
        r_dson_25c=16e-3,
        r_dson_25c_max=20e-3,
        r_dson_150c=22e-3,
        r_dson_150c_max=28e-3,
        capacitances=CapacitanceVsVoltage(
            c_iss=7200e-12,
            c_oss=520e-12,  # At 400V
            c_rss=15e-12,
        ),
        q_g=142e-9,
        q_gs=38e-9,
        q_gd=52e-9,
        v_gs_max=23.0,
        v_threshold=4.5,
    )

    # ZVS requirements
    zvs_req = ZVSRequirements(
        mosfet_coss=mosfet.capacitances.c_oss,
        mosfet_vds_max=mosfet.v_dss,
        n_mosfets_parallel=2,
        vin_min=360.0,
        vin_nom=400.0,
        vin_max=440.0,
        load_full=2200.0,  # Per phase
        load_min_zvs=220.0,  # 10% load
        load_min_percent=10.0,
        turns_ratio=16.0 / 30.0,
        magnetizing_inductance=200e-6,
        frequency=100e3,
        dead_time_target=500e-9,
        zvs_energy_margin=1.5,
    )

    # Design specification
    spec = MagneticDesignSpec(
        power=2200.0,
        frequency=100e3,
        temp_ambient=40.0,
        temp_rise_max=60.0,
        current_density_max=5.0,
        window_utilization=0.5,
        flux_density_max=0.3,
        core_material=CoreMaterial.FERRITE_3C95,
        enable_light_load_zvs=True,
        min_load_percentage=10.0,
    )

    # Perform design
    pq_design, etd_design = design_resonant_inductor(
        zvs_req=zvs_req,
        spec=spec,
        core_family="PQ",
        alternative_family="ETD",
    )

    print("\nRecommended Design:")
    print(f"  Core: {pq_design.core_name}")
    print(f"  Inductance: {pq_design.inductance_magnetizing * 1e6:.2f} µH")
    print(f"  Turns: {pq_design.n_primary}")
    print(f"  Total Loss: {pq_design.total_loss:.2f} W")
    print(f"  Efficiency: {pq_design.efficiency:.2f}%")

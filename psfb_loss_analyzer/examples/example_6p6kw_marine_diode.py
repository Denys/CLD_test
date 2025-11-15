"""
Example Configuration: 6.6kW Marine PSFB with Diode Rectification

This example demonstrates a high-power Phase-Shifted Full-Bridge converter
for marine applications using SiC Schottky diode rectification on the
secondary side.

Specifications:
- Input: 400V DC (marine high-voltage bus)
- Output: 250V DC (multi-output capable)
- Power: 1700W (Load 1), 2200W (Load 2), up to 6600W total (3×2200W)
- Switching frequency: 100 kHz
- Primary: SiC MOSFETs (Infineon IMZA65R020M2H, 650V 20mΩ)
- Secondary: SiC Schottky diodes (full-bridge rectifier)
- Controller: UCC28951 (Phase-Shift Full-Bridge with ZVS optimization)

Target Application:
- Marine DC power distribution systems
- Ship electrical systems (400V DC bus to 250V loads)
- Multi-output power supplies for marine electronics
- Ruggedized industrial power systems

Component Selection Rationale:
- Primary: IMZA65R020M2H (650V, 20mΩ SiC) - Low loss, ZVS capable
- Secondary: SiC Schottky diodes - Low forward drop, negligible reverse recovery
- Diode rectification chosen for:
  * Simplicity and reliability
  * Reduced control complexity (no SR drive)
  * Lower cost than SR MOSFETs
  * Acceptable efficiency at moderate power levels
- Transformer: Large PQ core for multi-kW power handling

Author: PSFB Loss Analysis Tool
Reference: UCC28951 datasheet, Infineon IMZA65R020M2H datasheet
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from circuit_params import *
from core_database import get_core_geometry, get_core_loss_coefficients


def create_6p6kw_marine_diode_config() -> PSFBConfiguration:
    """
    Create a 6.6kW marine PSFB converter with diode rectification

    Returns:
        Complete PSFBConfiguration object
    """

    # =========================================================================
    # CIRCUIT TOPOLOGY
    # =========================================================================
    # Turns ratio calculation for 400V→250V:
    # V_out = V_in × D_eff / (2n), where D_eff = φ/180
    # At φ = 120°: D_eff = 0.667
    # 250 = 400 × 0.667 / (2n) → n = 0.53 ≈ 8:15 ratio
    topology = CircuitTopology(
        v_in=VoltageRange(min=360.0, nominal=400.0, max=440.0),  # ±10% tolerance
        v_out=250.0,  # 250V DC output
        p_out=6600.0,  # Maximum combined power (3 × 2200W)
        f_sw=100e3,  # 100 kHz switching frequency
        phase_shift_min=20.0,  # Minimum phase shift (light load)
        phase_shift_max=160.0,  # Maximum phase shift (full load)
        n_phases=1,  # Single phase (3 outputs share same transformer)
        dead_time_primary=300e-9,  # 300ns dead time for ZVS
        dead_time_secondary=0.0,  # Not applicable for diode rectification
        transformer_turns_ratio=0.533  # 8:15 ratio (400V → 250V nominal)
    )

    # =========================================================================
    # PRIMARY SIDE MOSFETs (Q1-Q4)
    # Infineon IMZA65R020M2H - 650V 20mΩ CoolSiC™ MOSFET
    # Same device as 5kW telecom example
    # =========================================================================

    # Capacitance vs VDS curve for IMZA65R020M2H
    primary_caps_curve = [
        (25.0, 4500e-12, 180e-12, 45e-12),
        (100.0, 4200e-12, 95e-12, 22e-12),
        (200.0, 4000e-12, 60e-12, 14e-12),
        (400.0, 3900e-12, 40e-12, 9e-12),
        (600.0, 3850e-12, 30e-12, 7e-12),
    ]

    primary_mosfet = MOSFETParameters(
        part_number="IMZA65R020M2H",  # Infineon 650V 20mΩ CoolSiC™
        v_dss=650.0,  # 650V rating (good margin for 440V max)
        i_d_continuous=90.0,  # 90A @ 25°C (TC)

        # RDS(on) characteristics
        r_dson_25c=16e-3,  # 16mΩ typical @ 25°C, VGS=18V
        r_dson_25c_max=20e-3,  # 20mΩ max @ 25°C
        r_dson_150c=22e-3,  # 22mΩ typical @ 150°C
        r_dson_150c_max=28e-3,  # 28mΩ max @ 150°C

        # Gate charge (VGS=18V, VDS=400V)
        q_g=85e-9,  # 85nC total gate charge
        q_gs=25e-9,  # 25nC gate-source charge
        q_gd=28e-9,  # 28nC gate-drain (Miller) charge
        v_gs_plateau=4.8,  # 4.8V Miller plateau

        # Capacitances
        capacitances=CapacitanceVsVoltage(capacitance_curve=primary_caps_curve),

        # Switching times (VGS=18V, RG=5Ω, ID=45A, VDS=400V)
        t_r=18e-9,  # 18ns rise time
        t_f=14e-9,  # 14ns fall time

        # Body diode (SiC Schottky body diode)
        v_sd=2.2,  # 2.2V forward voltage @ 45A
        q_rr=15e-9,  # 15nC reverse recovery (very low for SiC)
        t_rr=12e-9,  # 12ns reverse recovery time

        # Thermal
        r_th_jc=0.50,  # 0.50°C/W junction-to-case
        t_j_max=175.0,  # 175°C for SiC

        # Gate drive
        v_gs_drive=18.0,  # 18V gate drive
        r_g_internal=1.5,  # 1.5Ω internal gate resistance
        r_g_external=5.0,  # 5Ω external gate resistor
    )

    # =========================================================================
    # SECONDARY SIDE RECTIFIER DIODES
    # Using SiC Schottky diodes for full-bridge rectification
    # Example: Wolfspeed C4D30120A (1200V, 31A SiC Schottky)
    # =========================================================================

    secondary_diode = DiodeParameters(
        part_number="C4D30120A",  # Wolfspeed 1200V 31A SiC Schottky
        v_rrm=1200.0,  # 1200V reverse voltage (over-rated for reliability)
        i_f_avg=31.0,  # 31A average forward current @ TC=127°C

        # Forward characteristics (SiC Schottky - no threshold voltage)
        v_f0=0.0,  # SiC Schottky has no V_F0 (different from Si PN)
        r_d=35e-3,  # 35mΩ dynamic resistance (from V_F curve slope)
        # At 15A: V_F ≈ 1.5V → R_D ≈ 1.5/15 + some slope ≈ 35mΩ effective

        # Reverse recovery (SiC Schottky - essentially zero)
        q_rr=0.0,  # Negligible for SiC Schottky
        t_rr=0.0,  # No reverse recovery

        # Thermal
        r_th_jc=1.2,  # 1.2°C/W junction-to-case
        t_j_max=175.0,  # 175°C for SiC
    )

    # =========================================================================
    # TRANSFORMER
    # Using TDK PQ107/87 core - largest PQ for high power
    # Reference: TDK Large PQ series datasheet
    # =========================================================================

    # Get core geometry from database
    core_geometry = get_core_geometry("PQ107/87")

    # Get core loss coefficients for 3C95 @ 100°C
    core_loss_coeffs = get_core_loss_coefficients(CoreMaterial.FERRITE_3C95, 100.0)

    # Primary winding (Np = 16 turns for 400V input, heavy Litz wire)
    # Voltage per turn: 400V / (2 × 16) = 12.5V/turn (good for 100kHz)
    primary_winding = WindingParameters(
        n_turns=16,
        wire_diameter=1.5e-3,  # 1.5mm Litz strand diameter
        wire_conductors=120,  # 120 strands for low AC resistance @ 100kHz
        dc_resistance=3.2e-3,  # 3.2mΩ DC resistance
        layers=2,  # 2 layers to fit in window
        foil_winding=False
    )

    # Secondary winding (Ns = 30 turns for 250V output, 16/30 = 0.533 ratio)
    # Output current: 6600W / 250V = 26.4A average
    # Use multiple parallel windings or heavy wire
    secondary_winding = WindingParameters(
        n_turns=30,  # 16:30 ratio = 0.533
        wire_diameter=2.0e-3,  # 2.0mm wire diameter (or equivalent Litz)
        wire_conductors=60,  # 60 strands in parallel for current capacity
        dc_resistance=6.5e-3,  # 6.5mΩ DC resistance (more turns than primary)
        layers=3,  # 3 layers for 30 turns
        foil_winding=False
    )

    transformer = TransformerParameters(
        core_geometry=core_geometry,
        core_material=CoreMaterial.FERRITE_3C95,
        core_loss_coefficients=core_loss_coeffs,
        primary_winding=primary_winding,
        secondary_winding=secondary_winding,
        leakage_inductance=4.5e-6,  # 4.5µH leakage (important for PSFB operation)
        magnetizing_inductance=650e-6,  # 650µH magnetizing inductance
        isolation_capacitance=200e-12  # 200pF primary-secondary
    )

    # =========================================================================
    # OUTPUT FILTER INDUCTOR
    # =========================================================================
    # Output current: 26.4A average at full load
    # Inductor for 100kHz, 250V output
    output_inductor = InductorParameters(
        inductance=40e-6,  # 40µH for 100kHz switching, higher voltage
        dc_resistance=1.8e-3,  # 1.8mΩ DCR
        ac_resistance_100khz=3.5e-3,  # 3.5mΩ @ 100kHz
        core_loss_density=200e3,  # 200 kW/m³
        core_volume=35e-6,  # 35 cm³ core volume (large inductor)
        current_rating=35.0,  # 35A RMS rating
        saturation_current=45.0  # 45A saturation current
    )

    # =========================================================================
    # FILTER CAPACITORS
    # =========================================================================

    # Input capacitor bank (high voltage film capacitors)
    input_capacitor = CapacitorParameters(
        capacitance=200e-6,  # 200µF total (multiple caps in parallel)
        voltage_rating=500.0,  # 500V rating for 440V max input
        esr=6e-3,  # 6mΩ ESR (parallel film caps)
        esl=10e-9,  # 10nH ESL
        ripple_current_rating=50.0  # 50A RMS ripple current
    )

    # Output capacitor bank (high voltage, high capacitance)
    output_capacitor = CapacitorParameters(
        capacitance=500e-6,  # 500µF total for 250V output
        voltage_rating=350.0,  # 350V rating for 250V output
        esr=8e-3,  # 8mΩ ESR
        esl=12e-9,  # 12nH ESL
        ripple_current_rating=40.0  # 40A RMS ripple current
    )

    # =========================================================================
    # COMPONENT SET
    # =========================================================================
    components = ComponentSet(
        primary_mosfets=primary_mosfet,
        secondary_rectifier_type=RectifierType.DIODE,  # DIODE RECTIFICATION
        secondary_diodes=secondary_diode,  # SiC Schottky diodes
        transformer=transformer,
        output_inductor=output_inductor,
        input_capacitor=input_capacitor,
        output_capacitor=output_capacitor
    )

    # =========================================================================
    # THERMAL MANAGEMENT
    # =========================================================================
    thermal = ThermalParameters(
        t_ambient=50.0,  # 50°C ambient (marine environment, hot)
        cooling_method=CoolingMethod.FORCED_AIR,
        forced_air_cfm=30.0,  # 30 CFM forced air (significant cooling for 6.6kW)
        heatsink_r_th_ca=1.5,  # 1.5°C/W case-to-ambient (primary MOSFETs)
        thermal_interface_r_th=0.10,  # 0.10°C/W thermal interface
        target_t_j_max=125.0  # Target 125°C max (50°C margin)
    )

    # =========================================================================
    # OPERATING POINT
    # Analysis at maximum combined power (6600W)
    # =========================================================================
    operating_point = OperatingConditions(
        load_percentage=100.0,  # Full load analysis (6600W)
        input_voltage=400.0,  # Nominal input voltage
        output_current=26.4,  # 6600W / 250V = 26.4A
        phase_shift_angle=140.0,  # 140° phase shift at full load (estimated)
        zvs_achieved_primary=True  # Assume ZVS achieved with proper design
    )

    # =========================================================================
    # CREATE COMPLETE CONFIGURATION
    # =========================================================================
    config = PSFBConfiguration(
        project_name="6.6kW Marine PSFB with SiC Diode Rectification (400V→250V)",
        topology=topology,
        components=components,
        thermal=thermal,
        operating_point=operating_point
    )

    return config


def main():
    """
    Demonstrate configuration creation and validation
    """
    print("="*70)
    print("PSFB Loss Analyzer - 6.6kW Marine PSFB with Diode Rectification")
    print("="*70)

    # Create configuration
    config = create_6p6kw_marine_diode_config()

    # Display summary
    print(config)

    # Validate configuration
    print("\nValidation Results:")
    print("-"*70)
    validate_configuration(config)

    # Export to JSON
    output_path = os.path.join(
        os.path.dirname(__file__),
        "6p6kw_marine_diode_config.json"
    )
    config.to_json(output_path, indent=2)
    print(f"\n✓ Configuration exported to: {output_path}")

    # Display key parameters
    print("\n" + "="*70)
    print("KEY DESIGN PARAMETERS - DIODE RECTIFICATION")
    print("="*70)

    print(f"\nPrimary MOSFETs (Infineon CoolSiC™):")
    print(f"  Part:              {config.components.primary_mosfets.part_number}")
    print(f"  Technology:        SiC (Silicon Carbide)")
    print(f"  Voltage rating:    {config.components.primary_mosfets.v_dss} V")
    print(f"  RDS(on) @ 25°C:    {config.components.primary_mosfets.r_dson_25c*1e3:.1f} mΩ")
    print(f"  RDS(on) @ 150°C:   {config.components.primary_mosfets.r_dson_150c*1e3:.1f} mΩ")
    print(f"  Alpha coefficient: {config.components.primary_mosfets.alpha_rdson:.2f} %/°C")

    print(f"\nSecondary Rectifier Diodes (SiC Schottky):")
    print(f"  Part:              {config.components.secondary_diodes.part_number}")
    print(f"  Technology:        SiC Schottky (zero reverse recovery)")
    print(f"  Voltage rating:    {config.components.secondary_diodes.v_rrm} V")
    print(f"  Avg current:       {config.components.secondary_diodes.i_f_avg} A")
    print(f"  Dynamic R:         {config.components.secondary_diodes.r_d*1e3:.1f} mΩ")
    print(f"  Reverse recovery:  {config.components.secondary_diodes.q_rr*1e9:.1f} nC (SiC: zero)")
    print(f"  Rectifier type:    {config.components.secondary_rectifier_type.value.upper()}")

    print(f"\nTransformer (TDK PQ107/87 - Largest PQ Core):")
    print(f"  Core:              {config.components.transformer.core_geometry.core_type}")
    print(f"  Material:          {config.components.transformer.core_material.value}")
    print(f"  Turns ratio:       {config.components.transformer.primary_winding.n_turns}:{config.components.transformer.secondary_winding.n_turns} (n={config.topology.transformer_turns_ratio:.3f})")
    print(f"  Ae:                {config.components.transformer.core_geometry.effective_area*1e6:.0f} mm²")
    print(f"  Ve:                {config.components.transformer.core_geometry.effective_volume*1e6:.0f} cm³")
    print(f"  Leakage L:         {config.components.transformer.leakage_inductance*1e6:.2f} µH")

    print(f"\nPower Distribution:")
    print(f"  Load 1:            1700 W (single output)")
    print(f"  Load 2:            2200 W (single output)")
    print(f"  Maximum combined:  {config.topology.p_out:.0f} W (3 × 2200W outputs)")
    print(f"  Output voltage:    {config.topology.v_out} V")
    print(f"  Output current:    {config.operating_point.output_current:.1f} A @ max power")

    print(f"\nExpected Currents @ 6600W:")
    i_in_avg = config.topology.p_out / config.topology.v_in.nominal / 0.94  # Assume 94% eff
    i_out = config.topology.p_out / config.topology.v_out
    print(f"  Input current:     {i_in_avg:.1f} A (avg @ 400V)")
    print(f"  Output current:    {i_out:.1f} A")
    print(f"  Primary RMS:       ~{i_in_avg*0.65:.1f} A (estimated)")
    print(f"  Secondary RMS:     ~{i_out*0.55:.1f} A (estimated)")
    print(f"  Diode avg current: ~{i_out/4:.1f} A per diode (4 diodes)")

    print(f"\nEstimated Primary Conduction Loss (worst-case):")
    i_rms_per_mosfet = i_in_avg * 0.65 / 2
    r_ds_125c = config.components.primary_mosfets.r_dson_25c_max * (1 + config.components.primary_mosfets.alpha_rdson/100 * (125-25))
    p_cond_primary = 4 * r_ds_125c * i_rms_per_mosfet**2
    print(f"  I_RMS per MOSFET:  ~{i_rms_per_mosfet:.1f} A")
    print(f"  RDS(on) @ 125°C:   {r_ds_125c*1e3:.1f} mΩ (max)")
    print(f"  Total P_cond:      ~{p_cond_primary:.1f} W (4 MOSFETs)")

    print(f"\nEstimated Diode Conduction Loss (approximate):")
    i_diode_avg = i_out / 4  # Full-bridge: each diode conducts 1/4 of cycle
    i_diode_rms = i_out / 2  # RMS current in each diode
    v_f_est = config.components.secondary_diodes.r_d * i_diode_avg * 1.5  # Rough estimate
    p_diode_single = v_f_est * i_diode_avg
    p_diode_total = p_diode_single * 4
    print(f"  I_avg per diode:   ~{i_diode_avg:.1f} A")
    print(f"  V_F estimated:     ~{v_f_est:.2f} V @ {i_diode_avg:.1f}A")
    print(f"  Total P_diode:     ~{p_diode_total:.1f} W (4 diodes)")

    print(f"\nController:")
    print(f"  IC:                UCC28951 (Phase-Shift FB Controller)")
    print(f"  Features:          ZVS optimization, adaptive dead-time")
    print(f"  Phase shift range: {config.topology.phase_shift_min:.0f}° - {config.topology.phase_shift_max:.0f}°")
    print(f"  Dead time:         {config.topology.dead_time_primary*1e9:.0f} ns")

    print("\n" + "="*70)


if __name__ == "__main__":
    main()

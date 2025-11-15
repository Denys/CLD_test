"""
Example Configuration: 5kW High-Power PSFB with Infineon IMZA65R020M2H

This example demonstrates a 5kW Phase-Shifted Full-Bridge converter design
using Infineon CoolSiC™ IMZA65R020M2H MOSFETs (650V, 20mΩ).

Specifications:
- Input: 200-400V DC (300V nominal, high-voltage DC link)
- Output: 48V DC @ 104A (5000W)
- Switching frequency: 150 kHz
- Synchronous rectification with low RDS(on) MOSFETs
- SiC MOSFETs for high efficiency and high temperature operation
- Forced air cooling with heatsinks

Target Application:
- Telecom/Datacom power supplies
- Industrial 48V power systems
- EV charging infrastructure
- High-density server PSUs

Component Selection Rationale:
- Primary: IMZA65R020M2H (650V, 20mΩ) - Low RDS(on) for high voltage, high current
- Secondary: IMZA120R007M2H (1200V, 7mΩ SiC) used as low-side SR (over-rated for reliability)
- Transformer: TDK PQ80/60 with PC95 ferrite (1230mm² Ae, suitable for 5kW)
- High frequency (150kHz) enabled by low switching loss of SiC

Author: PSFB Loss Analysis Tool
Reference: Infineon IMZA65R020M2H datasheet
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from circuit_params import *
from core_database import get_core_geometry, get_core_loss_coefficients


def create_5kw_infineon_config() -> PSFBConfiguration:
    """
    Create a 5kW PSFB converter configuration with Infineon IMZA65R020M2H

    Returns:
        Complete PSFBConfiguration object
    """

    # =========================================================================
    # CIRCUIT TOPOLOGY
    # =========================================================================
    topology = CircuitTopology(
        v_in=VoltageRange(min=200.0, nominal=300.0, max=400.0),  # High voltage DC link
        v_out=48.0,  # 48V telecom standard
        p_out=5000.0,  # 5kW rated power
        f_sw=150e3,  # 150 kHz (high frequency for SiC)
        phase_shift_min=15.0,  # Minimum phase shift (light load)
        phase_shift_max=165.0,  # Maximum phase shift (full load)
        n_phases=1,  # Single phase
        dead_time_primary=250e-9,  # 250ns dead time for ZVS
        dead_time_secondary=150e-9,  # 150ns for SR MOSFETs
        transformer_turns_ratio=3.125  # 300V / (2*48V) ≈ 3.125:1
    )

    # =========================================================================
    # PRIMARY SIDE MOSFETs (Q1-Q4)
    # Infineon IMZA65R020M2H - 650V 20mΩ CoolSiC™ MOSFET
    # Reference: infineon-imza65r020m2h-datasheet-en.pdf
    # =========================================================================

    # Capacitance vs VDS curve for IMZA65R020M2H (typical values from CoolSiC family)
    # Format: (V_DS, C_iss, C_oss, C_rss) in Farads
    primary_caps_curve = [
        (25.0, 4500e-12, 180e-12, 45e-12),    # Low voltage
        (100.0, 4200e-12, 95e-12, 22e-12),    # Medium voltage
        (200.0, 4000e-12, 60e-12, 14e-12),    # Operating point
        (400.0, 3900e-12, 40e-12, 9e-12),     # High voltage
        (600.0, 3850e-12, 30e-12, 7e-12),     # Near rated
    ]

    primary_mosfet = MOSFETParameters(
        part_number="IMZA65R020M2H",  # Infineon 650V 20mΩ CoolSiC™
        v_dss=650.0,  # 650V rating
        i_d_continuous=90.0,  # 90A @ 25°C (TC), 36A @ 100°C

        # RDS(on) characteristics from datasheet
        # VGS=18V, note: SiC has better temp stability than Si
        r_dson_25c=16e-3,  # 16mΩ typical @ 25°C, VGS=18V
        r_dson_25c_max=20e-3,  # 20mΩ max @ 25°C
        r_dson_150c=22e-3,  # 22mΩ typical @ 150°C
        r_dson_150c_max=28e-3,  # 28mΩ max @ 150°C (SiC: only 40% increase vs 80% for Si)

        # Gate charge (VGS=18V, VDS=400V per datasheet)
        q_g=85e-9,  # 85nC total gate charge
        q_gs=25e-9,  # 25nC gate-source charge
        q_gd=28e-9,  # 28nC gate-drain (Miller) charge
        v_gs_plateau=4.8,  # 4.8V Miller plateau (typical for SiC)

        # Capacitances
        capacitances=CapacitanceVsVoltage(capacitance_curve=primary_caps_curve),

        # Switching times (from datasheet @ VGS=18V, RG=5Ω, ID=45A, VDS=400V)
        t_r=18e-9,  # 18ns rise time
        t_f=14e-9,  # 14ns fall time

        # Body diode (SiC Schottky body diode - excellent characteristics)
        v_sd=2.2,  # 2.2V forward voltage @ 45A (SiC body diode)
        q_rr=15e-9,  # 15nC reverse recovery (very low for SiC)
        t_rr=12e-9,  # 12ns reverse recovery time

        # Thermal (excellent for SiC)
        r_th_jc=0.50,  # 0.50°C/W junction-to-case (large die)
        t_j_max=175.0,  # 175°C for SiC (vs 150°C for Si)

        # Gate drive (SiC requires higher VGS for low RDS(on))
        v_gs_drive=18.0,  # 18V gate drive (optimal for SiC)
        r_g_internal=1.5,  # 1.5Ω internal gate resistance
        r_g_external=5.0,  # 5Ω external gate resistor
    )

    # =========================================================================
    # SECONDARY SIDE SYNCHRONOUS RECTIFIER MOSFETs (SR1-SR2)
    # Using ultra-low RDS(on) devices for secondary (high current, low voltage)
    # Option: IMZA120R007M2H or similar ultra-low RDS(on) device
    # =========================================================================

    # For 48V output with 3.125:1 turns ratio, secondary sees ~96V reflected
    # Use over-rated device for reliability and paralleling capability
    secondary_caps_curve = [
        (10.0, 3200e-12, 450e-12, 95e-12),
        (25.0, 3000e-12, 280e-12, 58e-12),
        (50.0, 2850e-12, 180e-12, 38e-12),
        (80.0, 2750e-12, 130e-12, 28e-12),
    ]

    secondary_mosfet = MOSFETParameters(
        part_number="IMZA120R007M2H",  # Infineon 1200V 7mΩ CoolSiC™ (over-spec for reliability)
        v_dss=1200.0,  # 1200V rating (over-rated for 96V secondary)
        i_d_continuous=142.0,  # 142A @ 25°C

        # RDS(on) - ultra-low for high current secondary
        r_dson_25c=5.5e-3,  # 5.5mΩ typical @ 25°C
        r_dson_25c_max=7.0e-3,  # 7.0mΩ max @ 25°C
        r_dson_150c=7.5e-3,  # 7.5mΩ typical @ 150°C
        r_dson_150c_max=9.5e-3,  # 9.5mΩ max @ 150°C

        # Gate charge (VGS=18V, VDS=800V)
        q_g=180e-9,  # 180nC total (larger device)
        q_gs=48e-9,  # 48nC
        q_gd=62e-9,  # 62nC Miller charge
        v_gs_plateau=4.5,  # 4.5V plateau

        # Capacitances
        capacitances=CapacitanceVsVoltage(capacitance_curve=secondary_caps_curve),

        # Switching times
        t_r=22e-9,  # 22ns
        t_f=18e-9,  # 18ns

        # Body diode (SiC)
        v_sd=2.0,  # 2.0V forward voltage
        q_rr=18e-9,  # 18nC (SiC, very low)
        t_rr=15e-9,  # 15ns

        # Thermal
        r_th_jc=0.35,  # 0.35°C/W (large die for high current)
        t_j_max=175.0,  # 175°C

        # Gate drive
        v_gs_drive=18.0,  # 18V gate drive
        r_g_internal=1.2,  # 1.2Ω
        r_g_external=3.0,  # 3Ω for fast SR switching
    )

    # =========================================================================
    # TRANSFORMER
    # Using TDK PQ80/60 core with PC95 ferrite material
    # Reference: TDK Large PQ series datasheet
    # =========================================================================

    # Get core geometry from database
    core_geometry = get_core_geometry("PQ80/60")

    # Get core loss coefficients for PC95 @ 100°C
    core_loss_coeffs = get_core_loss_coefficients(CoreMaterial.FERRITE_3C95, 100.0)

    # Primary winding (Np = 25 turns for 300V input, Litz wire for AC loss reduction)
    primary_winding = WindingParameters(
        n_turns=25,
        wire_diameter=1.2e-3,  # 1.2mm Litz strand diameter
        wire_conductors=80,  # 80 strands for 150kHz
        dc_resistance=8.5e-3,  # 8.5mΩ DC resistance
        layers=3,  # 3 layers
        foil_winding=False
    )

    # Secondary winding (Ns = 8 turns for 48V output, copper foil for very high current)
    # 104A output requires very low DCR
    secondary_winding = WindingParameters(
        n_turns=8,  # 25/8 ≈ 3.125 turns ratio
        wire_diameter=0.4e-3,  # 0.4mm foil thickness
        wire_conductors=1,  # Single foil conductor
        dc_resistance=0.35e-3,  # 0.35mΩ DC resistance (critical for 104A!)
        layers=2,  # 2 layers for current capacity
        foil_winding=True  # Foil winding essential for 100A+ current
    )

    transformer = TransformerParameters(
        core_geometry=core_geometry,
        core_material=CoreMaterial.FERRITE_3C95,
        core_loss_coefficients=core_loss_coeffs,
        primary_winding=primary_winding,
        secondary_winding=secondary_winding,
        leakage_inductance=3.5e-6,  # 3.5µH leakage inductance (critical for PSFB operation)
        magnetizing_inductance=450e-6,  # 450µH magnetizing inductance
        isolation_capacitance=180e-12  # 180pF primary-secondary
    )

    # =========================================================================
    # OUTPUT FILTER INDUCTOR
    # =========================================================================
    output_inductor = InductorParameters(
        inductance=8e-6,  # 8µH for 150kHz switching, 48V output
        dc_resistance=0.25e-3,  # 0.25mΩ DCR (must be very low for 104A)
        ac_resistance_100khz=0.7e-3,  # 0.7mΩ @ 150kHz (includes AC effects)
        core_loss_density=250e3,  # 250 kW/m³ core loss density
        core_volume=22e-6,  # 22 cm³ core volume
        current_rating=120.0,  # 120A RMS rating
        saturation_current=150.0  # 150A saturation current
    )

    # =========================================================================
    # FILTER CAPACITORS
    # =========================================================================

    # Input capacitor bank (film capacitors for high voltage, high ripple)
    input_capacitor = CapacitorParameters(
        capacitance=150e-6,  # 150µF total (multiple caps in parallel)
        voltage_rating=500.0,  # 500V rating for 400V max input
        esr=8e-3,  # 8mΩ ESR (parallel film caps)
        esl=12e-9,  # 12nH ESL
        ripple_current_rating=40.0  # 40A RMS ripple current
    )

    # Output capacitor bank (polymer/electrolytic for 48V)
    output_capacitor = CapacitorParameters(
        capacitance=2200e-6,  # 2200µF total (2.2mF for low ripple)
        voltage_rating=63.0,  # 63V rating for 48V output
        esr=2e-3,  # 2mΩ ESR (polymer caps)
        esl=6e-9,  # 6nH ESL
        ripple_current_rating=70.0  # 70A RMS ripple current
    )

    # =========================================================================
    # COMPONENT SET
    # =========================================================================
    components = ComponentSet(
        primary_mosfets=primary_mosfet,
        secondary_rectifier_type=RectifierType.SYNCHRONOUS_MOSFET,
        secondary_mosfets=secondary_mosfet,
        transformer=transformer,
        output_inductor=output_inductor,
        input_capacitor=input_capacitor,
        output_capacitor=output_capacitor
    )

    # =========================================================================
    # THERMAL MANAGEMENT
    # =========================================================================
    thermal = ThermalParameters(
        t_ambient=40.0,  # 40°C ambient (telecom environment)
        cooling_method=CoolingMethod.FORCED_AIR,
        forced_air_cfm=25.0,  # 25 CFM forced air (significant cooling)
        heatsink_r_th_ca=1.8,  # 1.8°C/W case-to-ambient (primary MOSFETs with heatsink)
        thermal_interface_r_th=0.12,  # 0.12°C/W thermal pad
        target_t_j_max=125.0  # Target 125°C max (50°C margin from 175°C SiC limit)
    )

    # =========================================================================
    # OPERATING POINT
    # =========================================================================
    operating_point = OperatingConditions(
        load_percentage=100.0,  # Full load analysis
        input_voltage=300.0,  # Nominal input voltage
        output_current=104.2,  # 5000W / 48V = 104.2A
        phase_shift_angle=135.0,  # 135° phase shift at full load (estimated)
        zvs_achieved_primary=True  # Assume ZVS achieved (SiC excels at ZVS)
    )

    # =========================================================================
    # CREATE COMPLETE CONFIGURATION
    # =========================================================================
    config = PSFBConfiguration(
        project_name="5kW High-Voltage PSFB with Infineon IMZA65R020M2H (300V→48V)",
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
    print("PSFB Loss Analyzer - 5kW Infineon IMZA65R020M2H Example")
    print("="*70)

    # Create configuration
    config = create_5kw_infineon_config()

    # Display summary
    print(config)

    # Validate configuration
    print("\nValidation Results:")
    print("-"*70)
    validate_configuration(config)

    # Export to JSON
    output_path = os.path.join(
        os.path.dirname(__file__),
        "5kw_infineon_20mohm_config.json"
    )
    config.to_json(output_path, indent=2)
    print(f"\n✓ Configuration exported to: {output_path}")

    # Display key parameters
    print("\n" + "="*70)
    print("KEY DESIGN PARAMETERS")
    print("="*70)

    print(f"\nPrimary MOSFETs (Infineon CoolSiC™):")
    print(f"  Part:              {config.components.primary_mosfets.part_number}")
    print(f"  Technology:        SiC (Silicon Carbide)")
    print(f"  Voltage rating:    {config.components.primary_mosfets.v_dss} V")
    print(f"  RDS(on) @ 25°C:    {config.components.primary_mosfets.r_dson_25c*1e3:.1f} mΩ")
    print(f"  RDS(on) @ 150°C:   {config.components.primary_mosfets.r_dson_150c*1e3:.1f} mΩ")
    print(f"  Temp increase:     {(config.components.primary_mosfets.r_dson_150c/config.components.primary_mosfets.r_dson_25c - 1)*100:.0f}% (SiC advantage)")
    print(f"  Alpha coefficient: {config.components.primary_mosfets.alpha_rdson:.2f} %/°C")
    print(f"  Body diode Qrr:    {config.components.primary_mosfets.q_rr*1e9:.1f} nC (SiC: very low)")

    print(f"\nSecondary SR MOSFETs:")
    print(f"  Part:              {config.components.secondary_mosfets.part_number}")
    print(f"  RDS(on) @ 25°C:    {config.components.secondary_mosfets.r_dson_25c*1e3:.2f} mΩ")
    print(f"  RDS(on) @ 150°C:   {config.components.secondary_mosfets.r_dson_150c*1e3:.2f} mΩ")

    print(f"\nTransformer (TDK PQ80/60):")
    print(f"  Core:              {config.components.transformer.core_geometry.core_type}")
    print(f"  Material:          {config.components.transformer.core_material.value}")
    print(f"  Turns ratio:       {config.components.transformer.primary_winding.n_turns}:{config.components.transformer.secondary_winding.n_turns}")
    print(f"  Ae:                {config.components.transformer.core_geometry.effective_area*1e6:.0f} mm²")
    print(f"  Leakage L:         {config.components.transformer.leakage_inductance*1e6:.2f} µH")

    print(f"\nExpected Currents:")
    i_in_avg = config.topology.p_out / config.topology.v_in.nominal / 0.96  # Assume 96% eff (SiC)
    i_out = config.topology.p_out / config.topology.v_out
    print(f"  Input current:     {i_in_avg:.1f} A (avg @ 300V)")
    print(f"  Output current:    {i_out:.1f} A")
    print(f"  Primary RMS:       ~{i_in_avg*0.65:.1f} A (estimated)")
    print(f"  Secondary RMS:     ~{i_out*0.55:.1f} A (estimated)")

    print(f"\nEstimated Primary Conduction Loss (worst-case):")
    # Quick estimate: 4 MOSFETs, I_rms ≈ 11A per device, RDS(on)_max @ 125°C
    i_rms_per_mosfet = i_in_avg * 0.65 / 2  # Two MOSFETs conduct simultaneously
    r_ds_125c = config.components.primary_mosfets.r_dson_25c_max * (1 + config.components.primary_mosfets.alpha_rdson/100 * (125-25))
    p_cond_primary = 4 * r_ds_125c * i_rms_per_mosfet**2
    print(f"  I_RMS per MOSFET:  ~{i_rms_per_mosfet:.1f} A")
    print(f"  RDS(on) @ 125°C:   {r_ds_125c*1e3:.1f} mΩ (max)")
    print(f"  Total P_cond:      ~{p_cond_primary:.1f} W (4 MOSFETs)")

    print("\n" + "="*70)


if __name__ == "__main__":
    main()

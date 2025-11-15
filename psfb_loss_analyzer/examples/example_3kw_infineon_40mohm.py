"""
Example Configuration: 3kW Mid-Power PSFB with Infineon IMZA65R040M2H

This example demonstrates a 3kW Phase-Shifted Full-Bridge converter design
using Infineon CoolSiC™ IMZA65R040M2H MOSFETs (650V, 40mΩ).

Specifications:
- Input: 300-450V DC (380V nominal, high-voltage DC bus)
- Output: 48V DC @ 62.5A (3000W)
- Switching frequency: 120 kHz
- Synchronous rectification
- SiC MOSFETs for efficiency and compact design
- Natural convection with heatsinks (fanless operation)

Target Application:
- Industrial equipment power supplies
- Renewable energy inverters (PV, energy storage)
- Electric vehicle auxiliary power
- Compact 48V telecom rectifiers

Component Selection Rationale:
- Primary: IMZA65R040M2H (650V, 40mΩ) - Cost-optimized SiC for mid-power
- Secondary: CSD19536KTT (100V, 3.9mΩ) - Standard Si SR MOSFET for 48V
- Transformer: Ferroxcube ETD59 with 3C95 ferrite
- Lower frequency (120kHz) allows natural convection cooling

Author: PSFB Loss Analysis Tool
Reference: Infineon IMZA65R040M2H datasheet
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from circuit_params import *
from core_database import get_core_geometry, get_core_loss_coefficients


def create_3kw_infineon_40mohm_config() -> PSFBConfiguration:
    """
    Create a 3kW PSFB converter configuration with Infineon IMZA65R040M2H

    Returns:
        Complete PSFBConfiguration object
    """

    # =========================================================================
    # CIRCUIT TOPOLOGY
    # =========================================================================
    topology = CircuitTopology(
        v_in=VoltageRange(min=300.0, nominal=380.0, max=450.0),  # High voltage DC bus
        v_out=48.0,  # 48V standard output
        p_out=3000.0,  # 3kW rated power
        f_sw=120e3,  # 120 kHz (moderate frequency for natural convection)
        phase_shift_min=12.0,  # Minimum phase shift (light load)
        phase_shift_max=168.0,  # Maximum phase shift (full load)
        n_phases=1,  # Single phase
        dead_time_primary=300e-9,  # 300ns dead time for ZVS
        dead_time_secondary=120e-9,  # 120ns for SR MOSFETs
        transformer_turns_ratio=3.958  # 380V / (2*48V) ≈ 3.958:1
    )

    # =========================================================================
    # PRIMARY SIDE MOSFETs (Q1-Q4)
    # Infineon IMZA65R040M2H - 650V 40mΩ CoolSiC™ MOSFET
    # Reference: infineon-imza65r040m2h-datasheet-en.pdf
    # =========================================================================

    # Capacitance vs VDS curve for IMZA65R040M2H (typical values from CoolSiC family)
    # Format: (V_DS, C_iss, C_oss, C_rss) in Farads
    primary_caps_curve = [
        (25.0, 2800e-12, 120e-12, 28e-12),    # Low voltage
        (100.0, 2650e-12, 65e-12, 16e-12),    # Medium voltage
        (200.0, 2550e-12, 42e-12, 11e-12),    # Typical operating point
        (400.0, 2500e-12, 28e-12, 7e-12),     # High voltage
        (600.0, 2480e-12, 22e-12, 5e-12),     # Near rated
    ]

    primary_mosfet = MOSFETParameters(
        part_number="IMZA65R040M2H",  # Infineon 650V 40mΩ CoolSiC™
        v_dss=650.0,  # 650V rating
        i_d_continuous=56.0,  # 56A @ 25°C (TC), 22A @ 100°C

        # RDS(on) characteristics from datasheet
        # VGS=18V, SiC technology
        r_dson_25c=32e-3,  # 32mΩ typical @ 25°C, VGS=18V
        r_dson_25c_max=40e-3,  # 40mΩ max @ 25°C
        r_dson_150c=44e-3,  # 44mΩ typical @ 150°C
        r_dson_150c_max=55e-3,  # 55mΩ max @ 150°C

        # Gate charge (VGS=18V, VDS=400V per datasheet)
        q_g=58e-9,  # 58nC total gate charge
        q_gs=18e-9,  # 18nC gate-source charge
        q_gd=20e-9,  # 20nC gate-drain (Miller) charge
        v_gs_plateau=4.7,  # 4.7V Miller plateau

        # Capacitances
        capacitances=CapacitanceVsVoltage(capacitance_curve=primary_caps_curve),

        # Switching times (from datasheet @ VGS=18V, RG=5Ω, ID=28A, VDS=400V)
        t_r=16e-9,  # 16ns rise time
        t_f=13e-9,  # 13ns fall time

        # Body diode (SiC Schottky body diode)
        v_sd=2.1,  # 2.1V forward voltage @ 28A
        q_rr=12e-9,  # 12nC reverse recovery (very low for SiC)
        t_rr=10e-9,  # 10ns reverse recovery time

        # Thermal
        r_th_jc=0.95,  # 0.95°C/W junction-to-case
        t_j_max=175.0,  # 175°C for SiC

        # Gate drive
        v_gs_drive=18.0,  # 18V gate drive (optimal for SiC)
        r_g_internal=2.0,  # 2.0Ω internal gate resistance
        r_g_external=5.0,  # 5Ω external gate resistor
    )

    # =========================================================================
    # SECONDARY SIDE SYNCHRONOUS RECTIFIER MOSFETs (SR1-SR2)
    # Using standard Si MOSFETs for cost optimization at 48V
    # TI CSD19536KTT (100V, 3.9mΩ) - good balance of cost and performance
    # =========================================================================

    secondary_caps_curve = [
        (10.0, 3100e-12, 650e-12, 120e-12),
        (25.0, 2950e-12, 420e-12, 75e-12),
        (50.0, 2800e-12, 280e-12, 52e-12),
        (80.0, 2700e-12, 210e-12, 40e-12),
    ]

    secondary_mosfet = MOSFETParameters(
        part_number="CSD19536KTT",  # TI 100V 3.9mΩ NexFET (Si technology)
        v_dss=100.0,  # 100V rating
        i_d_continuous=200.0,  # 200A @ 25°C

        # RDS(on) - low for secondary SR
        r_dson_25c=3.2e-3,  # 3.2mΩ typical @ 25°C
        r_dson_25c_max=3.9e-3,  # 3.9mΩ max @ 25°C
        r_dson_150c=5.8e-3,  # 5.8mΩ typical @ 150°C (Si: larger temp coefficient)
        r_dson_150c_max=7.0e-3,  # 7.0mΩ max @ 150°C

        # Gate charge (VGS=10V, VDS=50V)
        q_g=72e-9,  # 72nC total
        q_gs=20e-9,  # 20nC
        q_gd=18e-9,  # 18nC Miller charge
        v_gs_plateau=3.8,  # 3.8V plateau

        # Capacitances
        capacitances=CapacitanceVsVoltage(capacitance_curve=secondary_caps_curve),

        # Switching times
        t_r=18e-9,  # 18ns
        t_f=15e-9,  # 15ns

        # Body diode (Si technology)
        v_sd=1.0,  # 1.0V forward voltage
        q_rr=95e-9,  # 95nC (Si: higher than SiC)
        t_rr=35e-9,  # 35ns

        # Thermal
        r_th_jc=0.5,  # 0.5°C/W
        t_j_max=175.0,  # 175°C

        # Gate drive
        v_gs_drive=10.0,  # 10V gate drive (Si optimum)
        r_g_internal=0.9,  # 0.9Ω
        r_g_external=2.5,  # 2.5Ω
    )

    # =========================================================================
    # TRANSFORMER
    # Using Ferroxcube ETD59 core with 3C95 ferrite material
    # Reference: Ferroxcube ETD core catalog
    # =========================================================================

    # Get core geometry from database
    core_geometry = get_core_geometry("ETD59")

    # Get core loss coefficients for 3C95 @ 100°C
    core_loss_coeffs = get_core_loss_coefficients(CoreMaterial.FERRITE_3C95, 100.0)

    # Primary winding (Np = 24 turns, Litz wire)
    primary_winding = WindingParameters(
        n_turns=24,
        wire_diameter=1.0e-3,  # 1.0mm Litz strand diameter
        wire_conductors=70,  # 70 strands for 120kHz
        dc_resistance=5.5e-3,  # 5.5mΩ DC resistance
        layers=3,  # 3 layers
        foil_winding=False
    )

    # Secondary winding (Ns = 6 turns, heavy copper or foil)
    # 62.5A output requires low DCR
    secondary_winding = WindingParameters(
        n_turns=6,  # 24/6 = 4:1 turns ratio (close to 3.958 effective)
        wire_diameter=0.35e-3,  # 0.35mm foil thickness
        wire_conductors=1,  # Single foil conductor
        dc_resistance=0.6e-3,  # 0.6mΩ DC resistance
        layers=2,  # 2 layers
        foil_winding=True  # Foil winding for high current
    )

    transformer = TransformerParameters(
        core_geometry=core_geometry,
        core_material=CoreMaterial.FERRITE_3C95,
        core_loss_coefficients=core_loss_coeffs,
        primary_winding=primary_winding,
        secondary_winding=secondary_winding,
        leakage_inductance=2.8e-6,  # 2.8µH leakage inductance
        magnetizing_inductance=320e-6,  # 320µH magnetizing inductance
        isolation_capacitance=140e-12  # 140pF primary-secondary
    )

    # =========================================================================
    # OUTPUT FILTER INDUCTOR
    # =========================================================================
    output_inductor = InductorParameters(
        inductance=12e-6,  # 12µH for 120kHz switching
        dc_resistance=0.4e-3,  # 0.4mΩ DCR
        ac_resistance_100khz=1.0e-3,  # 1.0mΩ @ 120kHz
        core_loss_density=180e3,  # 180 kW/m³ core loss density
        core_volume=18e-6,  # 18 cm³ core volume
        current_rating=80.0,  # 80A RMS rating
        saturation_current=100.0  # 100A saturation current
    )

    # =========================================================================
    # FILTER CAPACITORS
    # =========================================================================

    # Input capacitor bank (film capacitors for high voltage)
    input_capacitor = CapacitorParameters(
        capacitance=100e-6,  # 100µF total
        voltage_rating=550.0,  # 550V rating for 450V max input
        esr=10e-3,  # 10mΩ ESR
        esl=15e-9,  # 15nH ESL
        ripple_current_rating=25.0  # 25A RMS ripple current
    )

    # Output capacitor bank (polymer caps for 48V)
    output_capacitor = CapacitorParameters(
        capacitance=1500e-6,  # 1500µF total (1.5mF)
        voltage_rating=63.0,  # 63V rating
        esr=2.5e-3,  # 2.5mΩ ESR
        esl=8e-9,  # 8nH ESL
        ripple_current_rating=50.0  # 50A RMS ripple current
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
    # THERMAL MANAGEMENT (Natural Convection - Fanless)
    # =========================================================================
    thermal = ThermalParameters(
        t_ambient=45.0,  # 45°C ambient (industrial environment)
        cooling_method=CoolingMethod.NATURAL_CONVECTION,
        forced_air_cfm=0.0,  # No forced air (fanless)
        heatsink_r_th_ca=4.5,  # 4.5°C/W case-to-ambient (larger heatsinks for natural convection)
        thermal_interface_r_th=0.18,  # 0.18°C/W thermal pad
        target_t_j_max=135.0  # Target 135°C max (40°C margin for reliability)
    )

    # =========================================================================
    # OPERATING POINT
    # =========================================================================
    operating_point = OperatingConditions(
        load_percentage=100.0,  # Full load analysis
        input_voltage=380.0,  # Nominal input voltage
        output_current=62.5,  # 3000W / 48V = 62.5A
        phase_shift_angle=125.0,  # 125° phase shift at full load (estimated)
        zvs_achieved_primary=True  # Assume ZVS achieved
    )

    # =========================================================================
    # CREATE COMPLETE CONFIGURATION
    # =========================================================================
    config = PSFBConfiguration(
        project_name="3kW Fanless PSFB with Infineon IMZA65R040M2H (380V→48V)",
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
    print("PSFB Loss Analyzer - 3kW Infineon IMZA65R040M2H Example (Fanless)")
    print("="*70)

    # Create configuration
    config = create_3kw_infineon_40mohm_config()

    # Display summary
    print(config)

    # Validate configuration
    print("\nValidation Results:")
    print("-"*70)
    validate_configuration(config)

    # Export to JSON
    output_path = os.path.join(
        os.path.dirname(__file__),
        "3kw_infineon_40mohm_config.json"
    )
    config.to_json(output_path, indent=2)
    print(f"\n✓ Configuration exported to: {output_path}")

    # Display key parameters
    print("\n" + "="*70)
    print("KEY DESIGN PARAMETERS - FANLESS NATURAL CONVECTION")
    print("="*70)

    print(f"\nPrimary MOSFETs (Infineon CoolSiC™):")
    print(f"  Part:              {config.components.primary_mosfets.part_number}")
    print(f"  Technology:        SiC (Silicon Carbide)")
    print(f"  Voltage rating:    {config.components.primary_mosfets.v_dss} V")
    print(f"  RDS(on) @ 25°C:    {config.components.primary_mosfets.r_dson_25c*1e3:.1f} mΩ")
    print(f"  RDS(on) @ 150°C:   {config.components.primary_mosfets.r_dson_150c*1e3:.1f} mΩ")
    print(f"  Alpha coefficient: {config.components.primary_mosfets.alpha_rdson:.2f} %/°C")

    print(f"\nSecondary SR MOSFETs (Silicon):")
    print(f"  Part:              {config.components.secondary_mosfets.part_number}")
    print(f"  Technology:        Si (Standard Silicon)")
    print(f"  RDS(on) @ 25°C:    {config.components.secondary_mosfets.r_dson_25c*1e3:.2f} mΩ")
    print(f"  RDS(on) @ 150°C:   {config.components.secondary_mosfets.r_dson_150c*1e3:.2f} mΩ")
    print(f"  Temp increase:     {(config.components.secondary_mosfets.r_dson_150c/config.components.secondary_mosfets.r_dson_25c - 1)*100:.0f}% (Si characteristic)")

    print(f"\nTransformer (Ferroxcube ETD59):")
    print(f"  Core:              {config.components.transformer.core_geometry.core_type}")
    print(f"  Material:          {config.components.transformer.core_material.value}")
    print(f"  Turns ratio:       {config.components.transformer.primary_winding.n_turns}:{config.components.transformer.secondary_winding.n_turns}")
    print(f"  Ae:                {config.components.transformer.core_geometry.effective_area*1e6:.0f} mm²")
    print(f"  Leakage L:         {config.components.transformer.leakage_inductance*1e6:.2f} µH")

    print(f"\nThermal Design (Natural Convection):")
    print(f"  Cooling method:    {config.thermal.cooling_method.value}")
    print(f"  Heatsink Rth(c-a): {config.thermal.heatsink_r_th_ca}°C/W (large heatsink)")
    print(f"  Ambient temp:      {config.thermal.t_ambient}°C")
    print(f"  Target Tj max:     {config.thermal.target_t_j_max}°C")

    print(f"\nExpected Currents:")
    i_in_avg = config.topology.p_out / config.topology.v_in.nominal / 0.94  # Assume 94% eff
    i_out = config.topology.p_out / config.topology.v_out
    print(f"  Input current:     {i_in_avg:.1f} A (avg @ 380V)")
    print(f"  Output current:    {i_out:.1f} A")
    print(f"  Primary RMS:       ~{i_in_avg*0.65:.1f} A (estimated)")
    print(f"  Secondary RMS:     ~{i_out*0.55:.1f} A (estimated)")

    print(f"\nEstimated Primary Conduction Loss (worst-case):")
    i_rms_per_mosfet = i_in_avg * 0.65 / 2
    r_ds_135c = config.components.primary_mosfets.r_dson_25c_max * (1 + config.components.primary_mosfets.alpha_rdson/100 * (135-25))
    p_cond_primary = 4 * r_ds_135c * i_rms_per_mosfet**2
    print(f"  I_RMS per MOSFET:  ~{i_rms_per_mosfet:.1f} A")
    print(f"  RDS(on) @ 135°C:   {r_ds_135c*1e3:.1f} mΩ (max)")
    print(f"  Total P_cond:      ~{p_cond_primary:.1f} W (4 MOSFETs)")

    print("\n" + "="*70)


if __name__ == "__main__":
    main()

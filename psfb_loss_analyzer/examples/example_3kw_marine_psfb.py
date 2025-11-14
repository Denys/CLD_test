"""
Example Configuration: 3kW Marine PSFB Converter

This example demonstrates a complete parameter definition for a
3kW Phase-Shifted Full-Bridge converter designed for marine applications.

Specifications:
- Input: 36-60V DC (48V nominal, marine power system)
- Output: 24V DC @ 125A
- Switching frequency: 100 kHz
- Synchronous rectification
- SiC MOSFETs for high efficiency
- Forced air cooling

Author: PSFB Loss Analysis Tool
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from circuit_params import (
    PSFBConfiguration,
    CircuitTopology,
    VoltageRange,
    ComponentSet,
    MOSFETParameters,
    CapacitanceVsVoltage,
    TransformerParameters,
    CoreGeometry,
    CoreLossCoefficients,
    CoreMaterial,
    WindingParameters,
    InductorParameters,
    CapacitorParameters,
    ThermalParameters,
    CoolingMethod,
    OperatingConditions,
    RectifierType,
    validate_configuration
)


def create_3kw_marine_config() -> PSFBConfiguration:
    """
    Create a 3kW marine PSFB converter configuration

    Returns:
        Complete PSFBConfiguration object
    """

    # =========================================================================
    # CIRCUIT TOPOLOGY
    # =========================================================================
    topology = CircuitTopology(
        v_in=VoltageRange(min=36.0, nominal=48.0, max=60.0),  # 48V marine system
        v_out=24.0,  # 24V output
        p_out=3000.0,  # 3kW rated power
        f_sw=100e3,  # 100 kHz switching frequency
        phase_shift_min=10.0,  # Minimum phase shift (light load)
        phase_shift_max=170.0,  # Maximum phase shift (full load)
        n_phases=1,  # Single phase (can extend to 2-4 for higher power)
        dead_time_primary=200e-9,  # 200ns dead time for ZVS
        dead_time_secondary=100e-9,  # 100ns for SR MOSFETs
        transformer_turns_ratio=1.0  # 48V / (2*24V) = 1:1 turns ratio
    )

    # =========================================================================
    # PRIMARY SIDE MOSFETs (Q1-Q4)
    # Using C3M0065090J (650V SiC MOSFET from Wolfspeed/Cree)
    # =========================================================================

    # Capacitance vs VDS curve for C3M0065090J (extracted from datasheet)
    # Format: (V_DS, C_iss, C_oss, C_rss) in Farads
    primary_caps_curve = [
        (25.0, 1350e-12, 95e-12, 25e-12),
        (100.0, 1300e-12, 45e-12, 12e-12),
        (200.0, 1270e-12, 30e-12, 8e-12),
        (400.0, 1250e-12, 20e-12, 5e-12),
    ]

    primary_mosfet = MOSFETParameters(
        part_number="C3M0065090J",  # Wolfspeed 650V 65mΩ SiC MOSFET
        v_dss=650.0,  # 650V rating (good margin for 60V input)
        i_d_continuous=90.0,  # 90A @ 25°C

        # RDS(on) characteristics from datasheet
        r_dson_25c=52e-3,  # 52mΩ typical @ 25°C
        r_dson_25c_max=65e-3,  # 65mΩ max @ 25°C
        r_dson_150c=72e-3,  # 72mΩ typical @ 150°C
        r_dson_150c_max=91e-3,  # 91mΩ max @ 150°C

        # Gate charge (VGS=18V, VDS=400V per datasheet)
        q_g=36e-9,  # 36nC total gate charge
        q_gs=12e-9,  # 12nC gate-source charge
        q_gd=12e-9,  # 12nC gate-drain (Miller) charge
        v_gs_plateau=4.5,  # 4.5V Miller plateau

        # Capacitances
        capacitances=CapacitanceVsVoltage(capacitance_curve=primary_caps_curve),

        # Switching times (from datasheet @ VGS=18V, RG=5Ω, ID=25A)
        t_r=15e-9,  # 15ns rise time
        t_f=12e-9,  # 12ns fall time

        # Body diode (SiC diode, very low Qrr)
        v_sd=2.5,  # 2.5V forward voltage @ 25A
        q_rr=42e-9,  # 42nC reverse recovery (very low for SiC)
        t_rr=20e-9,  # 20ns reverse recovery time

        # Thermal
        r_th_jc=0.85,  # 0.85°C/W junction-to-case
        t_j_max=175.0,  # 175°C for SiC

        # Gate drive
        v_gs_drive=18.0,  # 18V gate drive (optimal for SiC)
        r_g_internal=2.4,  # 2.4Ω internal gate resistance
        r_g_external=5.0,  # 5Ω external gate resistor
    )

    # =========================================================================
    # SECONDARY SIDE SYNCHRONOUS RECTIFIER MOSFETs (SR1-SR2)
    # Using CSD19538Q3A (100V 1.8mΩ MOSFET from Texas Instruments)
    # =========================================================================

    # Capacitance for CSD19538Q3A
    secondary_caps_curve = [
        (10.0, 5400e-12, 1200e-12, 180e-12),
        (25.0, 5200e-12, 800e-12, 120e-12),
        (50.0, 5000e-12, 500e-12, 80e-12),
        (80.0, 4900e-12, 350e-12, 60e-12),
    ]

    secondary_mosfet = MOSFETParameters(
        part_number="CSD19538Q3A",  # TI 100V 1.8mΩ NexFET
        v_dss=100.0,  # 100V rating
        i_d_continuous=300.0,  # 300A @ 25°C (very high current device)

        # RDS(on) - ultra-low for high-current secondary
        r_dson_25c=1.5e-3,  # 1.5mΩ typical @ 25°C
        r_dson_25c_max=1.8e-3,  # 1.8mΩ max @ 25°C
        r_dson_150c=2.7e-3,  # 2.7mΩ typical @ 150°C
        r_dson_150c_max=3.2e-3,  # 3.2mΩ max @ 150°C

        # Gate charge (VGS=10V, VDS=50V)
        q_g=110e-9,  # 110nC total (large device)
        q_gs=28e-9,  # 28nC
        q_gd=25e-9,  # 25nC Miller charge
        v_gs_plateau=3.5,  # 3.5V plateau

        # Capacitances
        capacitances=CapacitanceVsVoltage(capacitance_curve=secondary_caps_curve),

        # Switching times
        t_r=20e-9,  # 20ns
        t_f=18e-9,  # 18ns

        # Body diode
        v_sd=1.0,  # 1.0V forward voltage
        q_rr=180e-9,  # 180nC (Si MOSFET, higher than SiC)
        t_rr=45e-9,  # 45ns

        # Thermal
        r_th_jc=0.3,  # 0.3°C/W (large die)
        t_j_max=175.0,  # 175°C

        # Gate drive
        v_gs_drive=10.0,  # 10V gate drive
        r_g_internal=0.8,  # 0.8Ω
        r_g_external=2.0,  # 2Ω for fast SR switching
    )

    # =========================================================================
    # TRANSFORMER
    # Using ETD59 ferrite core with 3C95 material
    # =========================================================================

    # Core geometry for ETD59
    core_geometry = CoreGeometry(
        core_type="ETD59",
        effective_area=368e-6,  # 368 mm² = 368e-6 m²
        effective_length=139e-3,  # 139 mm
        effective_volume=51.2e-6,  # 51.2 cm³ = 51.2e-6 m³
        window_area=511e-6,  # 511 mm²
        b_sat=0.39  # 0.39T @ 100°C for 3C95
    )

    # Core loss coefficients for 3C95 ferrite @ 100°C
    # Extracted from Ferroxcube datasheet
    core_loss_coeffs = CoreLossCoefficients(
        k=38.8,  # Material constant
        alpha=1.63,  # Frequency exponent
        beta=2.62,  # Flux density exponent
        temperature=100.0  # Valid at 100°C
    )

    # Primary winding (Np = 12 turns, Litz wire)
    primary_winding = WindingParameters(
        n_turns=12,
        wire_diameter=1.5e-3,  # 1.5mm Litz strand diameter
        wire_conductors=60,  # 60 strands for low AC resistance
        dc_resistance=2.5e-3,  # 2.5mΩ DC resistance
        layers=2,  # 2 layers
        foil_winding=False
    )

    # Secondary winding (Ns = 12 turns, copper foil for high current)
    secondary_winding = WindingParameters(
        n_turns=12,
        wire_diameter=0.3e-3,  # 0.3mm foil thickness
        wire_conductors=1,  # Single foil conductor
        dc_resistance=0.5e-3,  # 0.5mΩ DC resistance (very low)
        layers=2,
        foil_winding=True  # Foil winding for 125A current
    )

    transformer = TransformerParameters(
        core_geometry=core_geometry,
        core_material=CoreMaterial.FERRITE_3C95,
        core_loss_coefficients=core_loss_coeffs,
        primary_winding=primary_winding,
        secondary_winding=secondary_winding,
        leakage_inductance=2.5e-6,  # 2.5µH leakage inductance
        magnetizing_inductance=250e-6,  # 250µH magnetizing inductance
        isolation_capacitance=150e-12  # 150pF primary-secondary
    )

    # =========================================================================
    # OUTPUT FILTER INDUCTOR
    # =========================================================================
    output_inductor = InductorParameters(
        inductance=10e-6,  # 10µH for 100kHz switching
        dc_resistance=0.3e-3,  # 0.3mΩ DCR
        ac_resistance_100khz=0.8e-3,  # 0.8mΩ @ 100kHz (includes AC effects)
        core_loss_density=200e3,  # 200 kW/m³ core loss density (estimated)
        core_volume=15e-6,  # 15 cm³ core volume
        current_rating=150.0,  # 150A RMS rating
        saturation_current=180.0  # 180A saturation current
    )

    # =========================================================================
    # FILTER CAPACITORS
    # =========================================================================

    # Input capacitor bank (film + ceramic for high ripple current)
    input_capacitor = CapacitorParameters(
        capacitance=100e-6,  # 100µF total (multiple caps in parallel)
        voltage_rating=100.0,  # 100V rating for 60V max input
        esr=5e-3,  # 5mΩ ESR (parallel caps)
        esl=5e-9,  # 5nH ESL
        ripple_current_rating=30.0  # 30A RMS ripple current
    )

    # Output capacitor bank (electrolytic + ceramic)
    output_capacitor = CapacitorParameters(
        capacitance=1000e-6,  # 1000µF total (1mF)
        voltage_rating=50.0,  # 50V rating for 24V output
        esr=3e-3,  # 3mΩ ESR
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
    # THERMAL MANAGEMENT
    # =========================================================================
    thermal = ThermalParameters(
        t_ambient=50.0,  # 50°C ambient (hot marine environment)
        cooling_method=CoolingMethod.FORCED_AIR,
        forced_air_cfm=15.0,  # 15 CFM forced air
        heatsink_r_th_ca=2.5,  # 2.5°C/W case-to-ambient (primary MOSFETs)
        thermal_interface_r_th=0.15,  # 0.15°C/W thermal pad
        target_t_j_max=125.0  # Target 125°C max (50°C margin from 175°C)
    )

    # =========================================================================
    # OPERATING POINT
    # =========================================================================
    operating_point = OperatingConditions(
        load_percentage=100.0,  # Full load analysis
        input_voltage=48.0,  # Nominal input voltage
        output_current=125.0,  # 3000W / 24V = 125A
        phase_shift_angle=120.0,  # 120° phase shift at full load (estimated)
        zvs_achieved_primary=True  # Assume ZVS achieved (will be verified)
    )

    # =========================================================================
    # CREATE COMPLETE CONFIGURATION
    # =========================================================================
    config = PSFBConfiguration(
        project_name="3kW Marine PSFB Converter (48V→24V)",
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
    print("PSFB Loss Analyzer - 3kW Marine Converter Example")
    print("="*70)

    # Create configuration
    config = create_3kw_marine_config()

    # Display summary
    print(config)

    # Validate configuration
    print("\nValidation Results:")
    print("-"*70)
    validate_configuration(config)

    # Export to JSON
    output_path = os.path.join(
        os.path.dirname(__file__),
        "3kw_marine_psfb_config.json"
    )
    config.to_json(output_path, indent=2)
    print(f"\n✓ Configuration exported to: {output_path}")

    # Display key parameters
    print("\n" + "="*70)
    print("KEY DESIGN PARAMETERS")
    print("="*70)

    print(f"\nPrimary MOSFETs:")
    print(f"  Part:              {config.components.primary_mosfets.part_number}")
    print(f"  RDS(on) @ 25°C:    {config.components.primary_mosfets.r_dson_25c*1e3:.1f} mΩ")
    print(f"  RDS(on) @ 150°C:   {config.components.primary_mosfets.r_dson_150c*1e3:.1f} mΩ")
    print(f"  Alpha coefficient: {config.components.primary_mosfets.alpha_rdson:.2f} %/°C")

    print(f"\nSecondary MOSFETs:")
    print(f"  Part:              {config.components.secondary_mosfets.part_number}")
    print(f"  RDS(on) @ 25°C:    {config.components.secondary_mosfets.r_dson_25c*1e3:.2f} mΩ")
    print(f"  RDS(on) @ 150°C:   {config.components.secondary_mosfets.r_dson_150c*1e3:.2f} mΩ")

    print(f"\nTransformer:")
    print(f"  Core:              {config.components.transformer.core_geometry.core_type}")
    print(f"  Material:          {config.components.transformer.core_material.value}")
    print(f"  Primary turns:     {config.components.transformer.primary_winding.n_turns}")
    print(f"  Secondary turns:   {config.components.transformer.secondary_winding.n_turns}")
    print(f"  Leakage L:         {config.components.transformer.leakage_inductance*1e6:.2f} µH")

    print(f"\nExpected Currents:")
    i_in_avg = config.topology.p_out / config.topology.v_in.nominal / 0.95  # Assume 95% eff
    i_out = config.topology.p_out / config.topology.v_out
    print(f"  Input current:     {i_in_avg:.1f} A (avg @ 48V)")
    print(f"  Output current:    {i_out:.1f} A")
    print(f"  Primary RMS:       ~{i_in_avg*0.7:.1f} A (estimated)")
    print(f"  Secondary RMS:     ~{i_out*0.6:.1f} A (estimated)")

    print("\n" + "="*70)


if __name__ == "__main__":
    main()

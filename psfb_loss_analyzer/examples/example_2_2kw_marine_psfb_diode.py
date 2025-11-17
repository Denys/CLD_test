"""
Example Configuration: 2.2kW Marine PSFB Converter with SiC Diode Rectification

This example demonstrates a complete parameter definition for a
2.2kW Phase-Shifted Full-Bridge converter with SiC Schottky diode rectification
designed for marine/industrial applications.

Specifications:
- Input: 360-440V DC (400V nominal, high-voltage DC bus)
- Output: 250V DC @ 8.8A
- Switching frequency: 100 kHz
- Diode rectification (SiC Schottky, full-bridge, no center-tap)
- Primary: SiC MOSFETs
- Secondary: SiC Schottky diodes
- Transformer turns ratio: Np/Ns = 1.6 (step-down)
- Target ZVS < 30%
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
    DiodeParameters,
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


def create_2_2kw_marine_diode_config() -> PSFBConfiguration:
    """
    Create a 2.2kW marine PSFB converter configuration with SiC diode rectification

    Returns:
        Complete PSFBConfiguration object
    """

    # =========================================================================
    # CIRCUIT TOPOLOGY
    # =========================================================================
    topology = CircuitTopology(
        v_in=VoltageRange(min=360.0, nominal=400.0, max=440.0),  # 400V DC bus
        v_out=250.0,  # 250V output
        p_out=2200.0,  # 2.2kW rated power
        f_sw=100e3,  # 100 kHz switching frequency
        phase_shift_min=10.0,  # Minimum phase shift (light load)
        phase_shift_max=170.0,  # Maximum phase shift (full load)
        n_phases=1,  # Single phase
        dead_time_primary=200e-9,  # 200ns dead time for ZVS
        dead_time_secondary=100e-9,  # 100ns (not critical for diodes)
        transformer_turns_ratio=1.6  # Np/Ns = 1.6 (16:10 turns ratio)
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
        v_dss=650.0,  # 650V rating (good margin for 440V max input)
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
    # SECONDARY SIDE DIODE RECTIFIERS (D1-D4)
    # Using IDH16G65C5 (650V 16A SiC Schottky Diode from Infineon)
    # Full-bridge configuration, no center-tap
    # =========================================================================

    secondary_diode = DiodeParameters(
        part_number="IDH16G65C5",  # Infineon 650V 16A SiC Schottky
        v_rrm=650.0,  # 650V reverse voltage rating
        i_f_avg=16.0,  # 16A average forward current
        i_fsm=115.0,  # 115A surge current (non-repetitive)

        # Forward voltage characteristics
        v_f_typ=1.5,  # 1.5V typical @ 16A, 25°C
        v_f_max=2.0,  # 2.0V max @ 16A, 175°C

        # Thermal
        r_th_jc=1.2,  # 1.2°C/W junction-to-case
        t_j_max=175.0,  # 175°C max junction temperature

        # Capacitance (SiC Schottky has very low junction capacitance)
        c_j=120e-12,  # 120pF @ 400V (typical for SiC Schottky)

        # Reverse recovery (SiC Schottky has negligible reverse recovery)
        t_rr=0.0,  # Essentially zero for Schottky
        q_rr=0.0,  # Essentially zero for Schottky
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

    # Primary winding (Np = 16 turns, Litz wire)
    primary_winding = WindingParameters(
        n_turns=16,
        wire_diameter=1.2e-3,  # 1.2mm Litz strand diameter
        wire_conductors=40,  # 40 strands for low AC resistance
        dc_resistance=35e-3,  # 35mΩ DC resistance
        layers=2,  # 2 layers
        foil_winding=False
    )

    # Secondary winding (Ns = 10 turns, Litz wire for medium current)
    secondary_winding = WindingParameters(
        n_turns=10,
        wire_diameter=0.8e-3,  # 0.8mm Litz strand diameter
        wire_conductors=20,  # 20 strands
        dc_resistance=15e-3,  # 15mΩ DC resistance
        layers=2,
        foil_winding=False
    )

    transformer = TransformerParameters(
        core_geometry=core_geometry,
        core_material=CoreMaterial.FERRITE_3C95,
        core_loss_coefficients=core_loss_coeffs,
        primary_winding=primary_winding,
        secondary_winding=secondary_winding,
        leakage_inductance=3.5e-6,  # 3.5µH leakage inductance
        magnetizing_inductance=350e-6,  # 350µH magnetizing inductance
        isolation_capacitance=120e-12  # 120pF primary-secondary
    )

    # =========================================================================
    # OUTPUT FILTER INDUCTOR
    # =========================================================================
    output_inductor = InductorParameters(
        inductance=15e-6,  # 15µH for 100kHz switching
        dc_resistance=1.2e-3,  # 1.2mΩ DCR
        ac_resistance_100khz=2.5e-3,  # 2.5mΩ @ 100kHz (includes AC effects)
        core_loss_density=250e3,  # 250 kW/m³ core loss density (estimated)
        core_volume=20e-6,  # 20 cm³ core volume
        current_rating=12.0,  # 12A RMS rating
        saturation_current=15.0  # 15A saturation current
    )

    # =========================================================================
    # FILTER CAPACITORS
    # =========================================================================

    # Input capacitor bank (film capacitors for high voltage)
    input_capacitor = CapacitorParameters(
        capacitance=100e-6,  # 100µF total (multiple caps in parallel)
        voltage_rating=500.0,  # 500V rating for 440V max input
        esr=8e-3,  # 8mΩ ESR (parallel film caps)
        esl=10e-9,  # 10nH ESL
        ripple_current_rating=25.0  # 25A RMS ripple current
    )

    # Output capacitor bank (film + electrolytic)
    output_capacitor = CapacitorParameters(
        capacitance=150e-6,  # 150µF total
        voltage_rating=350.0,  # 350V rating for 250V output
        esr=5e-3,  # 5mΩ ESR
        esl=12e-9,  # 12nH ESL
        ripple_current_rating=35.0  # 35A RMS ripple current
    )

    # =========================================================================
    # COMPONENT SET
    # =========================================================================
    components = ComponentSet(
        primary_mosfets=primary_mosfet,
        secondary_rectifier_type=RectifierType.DIODE,
        secondary_diodes=secondary_diode,
        transformer=transformer,
        output_inductor=output_inductor,
        input_capacitor=input_capacitor,
        output_capacitor=output_capacitor
    )

    # =========================================================================
    # THERMAL MANAGEMENT
    # =========================================================================
    thermal = ThermalParameters(
        t_ambient=50.0,  # 50°C ambient (hot marine/industrial environment)
        cooling_method=CoolingMethod.FORCED_AIR,
        forced_air_cfm=20.0,  # 20 CFM forced air
        heatsink_r_th_ca=2.0,  # 2.0°C/W case-to-ambient (primary MOSFETs)
        thermal_interface_r_th=0.15,  # 0.15°C/W thermal pad
        target_t_j_max=125.0  # Target 125°C max (50°C margin from 175°C)
    )

    # =========================================================================
    # OPERATING POINT
    # =========================================================================
    operating_point = OperatingConditions(
        load_percentage=100.0,  # Full load analysis
        input_voltage=400.0,  # Nominal input voltage
        output_current=8.8,  # 2200W / 250V = 8.8A
        phase_shift_angle=140.0,  # 140° phase shift at full load (estimated)
        zvs_achieved_primary=False  # Target ZVS < 30% (limited ZVS with diodes)
    )

    # =========================================================================
    # CREATE COMPLETE CONFIGURATION
    # =========================================================================
    config = PSFBConfiguration(
        project_name="2.2kW Marine PSFB with SiC Diode Rectification (400V→250V)",
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
    print("PSFB Loss Analyzer - 2.2kW Marine Converter with SiC Diode Rectification")
    print("="*70)

    # Create configuration
    config = create_2_2kw_marine_diode_config()

    # Display summary
    print(config)

    # Validate configuration
    print("\nValidation Results:")
    print("-"*70)
    validate_configuration(config)

    # Export to JSON
    output_path = os.path.join(
        os.path.dirname(__file__),
        "2_2kw_marine_psfb_diode_config.json"
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

    print(f"\nSecondary Diodes (SiC Schottky):")
    print(f"  Part:              {config.components.secondary_diodes.part_number}")
    print(f"  Vf typical:        {config.components.secondary_diodes.v_f_typ:.2f} V @ 16A")
    print(f"  Vf max:            {config.components.secondary_diodes.v_f_max:.2f} V @ 16A, 175°C")
    print(f"  Reverse recovery:  {config.components.secondary_diodes.q_rr*1e9:.1f} nC (negligible)")

    print(f"\nTransformer:")
    print(f"  Core:              {config.components.transformer.core_geometry.core_type}")
    print(f"  Material:          {config.components.transformer.core_material.value}")
    print(f"  Primary turns:     {config.components.transformer.primary_winding.n_turns}")
    print(f"  Secondary turns:   {config.components.transformer.secondary_winding.n_turns}")
    print(f"  Turns ratio Np/Ns: {config.topology.transformer_turns_ratio:.2f}")
    print(f"  Leakage L:         {config.components.transformer.leakage_inductance*1e6:.2f} µH")

    print(f"\nExpected Currents:")
    i_in_avg = config.topology.p_out / config.topology.v_in.nominal / 0.93  # Assume 93% eff (diodes have higher loss)
    i_out = config.topology.p_out / config.topology.v_out
    print(f"  Input current:     {i_in_avg:.2f} A (avg @ 400V)")
    print(f"  Output current:    {i_out:.2f} A")
    print(f"  Primary RMS:       ~{i_in_avg*0.7:.2f} A (estimated)")
    print(f"  Secondary RMS:     ~{i_out*0.6:.2f} A (estimated)")

    print(f"\nRectification:")
    print(f"  Type:              Full-bridge SiC Schottky diodes (no center-tap)")
    print(f"  Number of diodes:  4 (full-bridge)")
    print(f"  ZVS target:        < 30% (limited ZVS with diode rectification)")

    print("\n" + "="*70)


if __name__ == "__main__":
    main()

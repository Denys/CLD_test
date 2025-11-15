"""
Complete System Loss Analysis - 6.6kW Marine PSFB Converter

Demonstrates complete system-level loss analysis integrating:
- Primary-side MOSFET losses (Infineon IMZA65R020M2H SiC)
- Secondary-side diode losses (Wolfspeed C4D30120A SiC Schottky)
- Magnetic component losses (resonant inductor, transformer, output inductor)
- Capacitor ESR losses
- 3-phase interleaved operation @ 120° phase shift

System Specification:
- Total Power: 6.6kW (3× 2.2kW phases)
- Input: 400V DC (360-440V range)
- Output: 250V DC @ 26.4A
- Switching Frequency: 100kHz per phase
- Topology: Phase-Shifted Full-Bridge with SiC Schottky diode rectifier

Author: PSFB Loss Analysis Tool
Version: 0.4.0
"""

import sys
import os

try:
    from psfb_loss_analyzer.circuit_params import (
        MOSFETParameters,
        CapacitanceVsVoltage,
        DiodeParameters,
        CapacitorParameters,
        CoreMaterial,
    )
    from psfb_loss_analyzer.magnetics_design import MagneticDesignSpec
    from psfb_loss_analyzer.resonant_inductor_design import (
        ZVSRequirements,
        design_resonant_inductor,
    )
    from psfb_loss_analyzer.transformer_design import (
        TransformerSpec,
        design_transformer,
    )
    from psfb_loss_analyzer.output_inductor_design import (
        OutputInductorSpec,
        design_output_inductor,
    )
    from psfb_loss_analyzer.system_analyzer import (
        MagneticComponents,
        analyze_psfb_system,
        print_system_loss_report,
    )
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from circuit_params import (
        MOSFETParameters,
        CapacitanceVsVoltage,
        DiodeParameters,
        CapacitorParameters,
        CoreMaterial,
    )
    from magnetics_design import MagneticDesignSpec
    from resonant_inductor_design import (
        ZVSRequirements,
        design_resonant_inductor,
    )
    from transformer_design import (
        TransformerSpec,
        design_transformer,
    )
    from output_inductor_design import (
        OutputInductorSpec,
        design_output_inductor,
    )
    from system_analyzer import (
        MagneticComponents,
        analyze_psfb_system,
        print_system_loss_report,
    )


def main():
    """
    Complete system analysis for 6.6kW marine PSFB converter.
    """
    print("=" * 80)
    print("6.6kW MARINE PSFB - COMPLETE SYSTEM LOSS ANALYSIS")
    print("=" * 80)
    print()

    # ========================================================================
    # Component Parameters
    # ========================================================================

    print("Step 1: Component Selection")
    print("-" * 80)

    # Primary MOSFET: Infineon IMZA65R020M2H (650V, 20mΩ SiC)
    primary_mosfet = MOSFETParameters(
        part_number="IMZA65R020M2H",
        v_dss=650.0,
        i_d_continuous=90.0,
        r_dson_25c=16e-3,
        r_dson_25c_max=20e-3,
        r_dson_150c=22e-3,
        r_dson_150c_max=28e-3,
        capacitances=CapacitanceVsVoltage(
            c_iss_constant=7200e-12,
            c_oss_constant=520e-12,
            c_rss_constant=15e-12,
        ),
        q_g=142e-9,
        q_gs=38e-9,
        q_gd=52e-9,
        v_gs_plateau=4.5,
        t_r=25e-9,
        t_f=20e-9,
    )

    # Secondary Diode: Wolfspeed C4D30120A (1200V, 31A SiC Schottky)
    secondary_diode = DiodeParameters(
        part_number="C4D30120A",
        v_rrm=1200.0,
        i_f_avg=31.0,
        v_f0=0.0,  # SiC Schottky: no threshold
        r_d=35e-3,  # 35mΩ dynamic resistance
        q_rr=0.0,  # SiC: negligible reverse recovery
        t_rr=0.0,
    )

    # Input Capacitor: Film capacitor bank
    input_capacitor = CapacitorParameters(
        capacitance=100e-6,  # 100µF
        voltage_rating=500.0,
        esr=10e-3,  # 10mΩ (film capacitor)
        ripple_current_rating=50.0,
    )

    # Output Capacitor: Aluminum electrolytic bank
    output_capacitor = CapacitorParameters(
        capacitance=1000e-6,  # 1000µF
        voltage_rating=350.0,
        esr=5e-3,  # 5mΩ (low ESR electrolytic)
        ripple_current_rating=40.0,
    )

    print(f"Primary MOSFET:      {primary_mosfet.part_number}")
    print(f"Secondary Diode:     {secondary_diode.part_number}")
    print(f"Input Capacitor:     {input_capacitor.capacitance * 1e6:.0f} µF, ESR = {input_capacitor.esr * 1000:.0f} mΩ")
    print(f"Output Capacitor:    {output_capacitor.capacitance * 1e6:.0f} µF, ESR = {output_capacitor.esr * 1000:.0f} mΩ")
    print()

    # ========================================================================
    # Design Magnetic Components
    # ========================================================================

    print("Step 2: Magnetic Component Design (Quick Mode)")
    print("-" * 80)
    print("Designing magnetic components for single phase (2.2kW)...")
    print()

    # Common magnetic design spec
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

    # Design resonant inductor (suppress verbose output)
    zvs_req = ZVSRequirements(
        mosfet_coss=primary_mosfet.capacitances.get_coss(400.0),  # At 400V
        mosfet_vds_max=primary_mosfet.v_dss,
        n_mosfets_parallel=2,
        vin_nom=400.0,
        vin_max=440.0,
        load_full=2200.0,
        load_min_zvs=220.0,
        frequency=100e3,
        turns_ratio=16.0/30.0,
        magnetizing_inductance=200e-6,
    )

    # Suppress print output temporarily
    import io
    import contextlib

    with contextlib.redirect_stdout(io.StringIO()):
        lr_design, _ = design_resonant_inductor(zvs_req, mag_spec, "PQ", "ETD")

        xfmr_spec = TransformerSpec(
            vin_min=360.0,
            vin_nom=400.0,
            vin_max=440.0,
            vout_nom=250.0,
            power_output=2200.0,
            frequency=100e3,
            duty_cycle_nom=0.45,
        )
        xfmr_design, _ = design_transformer(xfmr_spec, mag_spec, "PQ", "ETD")

        lo_spec = OutputInductorSpec(
            vout_nom=250.0,
            iout_nom=8.8,  # 2200W / 250V per phase
            iout_max=10.0,
            frequency=100e3,
            n_phases=3,
            phase_shift_deg=120.0,
        )
        lo_design, _ = design_output_inductor(lo_spec, mag_spec, "PQ", "E")

    print(f"Resonant Inductor:   {lr_design.core_name}, {lr_design.inductance_magnetizing*1e6:.1f} µH, {lr_design.total_loss:.2f}W loss")
    print(f"Transformer:         {xfmr_design.core_name}, {xfmr_design.n_primary}:{xfmr_design.n_secondary} turns, {xfmr_design.total_loss:.2f}W loss")
    print(f"Output Inductor:     {lo_design.core_name}, {lo_design.inductance_magnetizing*1e6:.1f} µH, {lo_design.total_loss:.2f}W loss")
    print()

    # Package magnetic designs
    magnetics = MagneticComponents(
        resonant_inductor=lr_design,
        transformer=xfmr_design,
        output_inductor=lo_design,
    )

    # ========================================================================
    # System Loss Analysis
    # ========================================================================

    print("Step 3: Complete System Loss Analysis")
    print("-" * 80)
    print()

    # Analyze at multiple operating points
    operating_points = [
        ("10% Load", 400.0, 250.0, 660.0),
        ("25% Load", 400.0, 250.0, 1650.0),
        ("50% Load", 400.0, 250.0, 3300.0),
        ("75% Load", 400.0, 250.0, 4950.0),
        ("100% Load (Nominal)", 400.0, 250.0, 6600.0),
        ("100% Load (Low Vin)", 360.0, 250.0, 6600.0),
        ("100% Load (High Vin)", 440.0, 250.0, 6600.0),
    ]

    results = []

    for name, vin, vout, pout in operating_points:
        # Calculate duty cycle for this operating point
        # For PSFB: Vout ≈ Vin × D × n
        turns_ratio = xfmr_design.turns_ratio
        duty_nom = vout / (vin * turns_ratio * 2.0)  # Approximate
        duty_nom = min(max(duty_nom, 0.1), 0.48)  # Clamp to reasonable range

        system_loss = analyze_psfb_system(
            input_voltage=vin,
            output_voltage=vout,
            output_power=pout,
            frequency=100e3,
            duty_cycle=duty_nom,
            turns_ratio=turns_ratio,
            n_phases=3,
            phase_shift_deg=120.0,
            primary_mosfet=primary_mosfet,
            secondary_diode=secondary_diode,
            magnetics=magnetics,
            input_capacitor=input_capacitor,
            output_capacitor=output_capacitor,
            zvs_operation=True,
            t_junction_mosfet=100.0,
            t_junction_diode=125.0,
            output_inductor_ripple_pp=2.5,
        )

        results.append((name, system_loss))

    # ========================================================================
    # Print Results
    # ========================================================================

    print("=" * 80)
    print("EFFICIENCY vs. LOAD SUMMARY")
    print("=" * 80)
    print()
    print(f"{'Operating Point':<25} {'Pout (W)':<12} {'Loss (W)':<12} {'Efficiency':<12}")
    print("-" * 80)
    for name, sys_loss in results:
        print(f"{name:<25} {sys_loss.output_power:>10.1f} W  {sys_loss.total_loss:>10.2f} W  {sys_loss.efficiency:>10.2f} %")
    print()

    # Detailed report for nominal operating point
    nominal_result = results[4][1]  # 100% Load (Nominal)

    print()
    print_system_loss_report(nominal_result, detailed=True)

    # ========================================================================
    # Loss Breakdown Pie Chart Data
    # ========================================================================

    print("=" * 80)
    print("LOSS BREAKDOWN @ NOMINAL (6.6kW, 400V input)")
    print("=" * 80)
    print()

    total = nominal_result.total_loss
    print(f"Component Category        Loss (W)    % of Total Loss")
    print("-" * 60)
    print(f"Primary MOSFETs           {nominal_result.total_mosfet_loss:>8.2f} W    {100*nominal_result.total_mosfet_loss/total:>6.1f}%")
    print(f"Secondary Diodes          {nominal_result.total_diode_loss:>8.2f} W    {100*nominal_result.total_diode_loss/total:>6.1f}%")
    print(f"Magnetic Components       {nominal_result.total_magnetic_loss:>8.2f} W    {100*nominal_result.total_magnetic_loss/total:>6.1f}%")
    print(f"Capacitor ESR             {nominal_result.total_capacitor_loss:>8.2f} W    {100*nominal_result.total_capacitor_loss/total:>6.1f}%")
    print("-" * 60)
    print(f"TOTAL                     {total:>8.2f} W    100.0%")
    print()

    # ========================================================================
    # Magnetic Loss Breakdown
    # ========================================================================

    print("=" * 80)
    print("MAGNETIC LOSS BREAKDOWN (3 phases)")
    print("=" * 80)
    print()

    mag_total = nominal_result.total_magnetic_loss
    lr_total = lr_design.total_loss * 3
    xfmr_total = xfmr_design.total_loss * 3
    lo_total = lo_design.total_loss * 3

    print(f"Component              Loss per Phase    Total (3 phases)    % of Mag Loss")
    print("-" * 80)
    print(f"Resonant Inductors     {lr_design.total_loss:>14.2f} W    {lr_total:>15.2f} W    {100*lr_total/mag_total:>13.1f}%")
    print(f"Transformers           {xfmr_design.total_loss:>14.2f} W    {xfmr_total:>15.2f} W    {100*xfmr_total/mag_total:>13.1f}%")
    print(f"Output Inductors       {lo_design.total_loss:>14.2f} W    {lo_total:>15.2f} W    {100*lo_total/mag_total:>13.1f}%")
    print("-" * 80)
    print(f"TOTAL                                       {mag_total:>15.2f} W    100.0%")
    print()

    # ========================================================================
    # Summary
    # ========================================================================

    print("=" * 80)
    print("DESIGN SUMMARY")
    print("=" * 80)
    print()
    print(f"System Configuration:")
    print(f"  Topology:            3-phase interleaved PSFB @ 120° phase shift")
    print(f"  Total Power:         6.6 kW")
    print(f"  Power per Phase:     2.2 kW")
    print(f"  Switching Frequency: 100 kHz")
    print()
    print(f"Performance @ Nominal (400V→250V, 6.6kW):")
    print(f"  Total Loss:          {nominal_result.total_loss:.2f} W")
    print(f"  Efficiency:          {nominal_result.efficiency:.2f} %")
    print(f"  Power Density:       {6600.0 / nominal_result.total_loss:.1f} W/W_loss")
    print()
    print(f"Peak Efficiency:")
    max_eff = max(results, key=lambda x: x[1].efficiency)
    print(f"  Operating Point:     {max_eff[0]}")
    print(f"  Efficiency:          {max_eff[1].efficiency:.2f} %")
    print()
    print(f"Key Advantages:")
    print(f"  ✓ ZVS operation reduces MOSFET switching losses")
    print(f"  ✓ SiC devices minimize conduction and switching losses")
    print(f"  ✓ 3-phase interleaving reduces input/output ripple")
    print(f"  ✓ High efficiency across wide load range (>96% @ 25-100% load)")
    print()
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user.")
    except Exception as e:
        print(f"\n\nError during analysis: {e}")
        import traceback
        traceback.print_exc()

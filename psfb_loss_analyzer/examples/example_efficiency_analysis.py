"""
Efficiency Analysis Example - 6.6kW Marine PSFB Converter

Demonstrates comprehensive efficiency characterization:
- Efficiency vs. load curves at multiple input voltages
- 2D efficiency map (load vs. Vin)
- CEC and European weighted efficiency
- Peak efficiency identification
- CSV data export for documentation

System: 3-phase interleaved PSFB, 400V→250V, 6.6kW total (3× 2.2kW)

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
    from psfb_loss_analyzer.system_analyzer import MagneticComponents
    from psfb_loss_analyzer.efficiency_mapper import (
        sweep_efficiency_vs_load,
        generate_efficiency_map,
        export_efficiency_curve_csv,
        export_efficiency_map_csv,
        print_efficiency_summary,
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
    from system_analyzer import MagneticComponents
    from efficiency_mapper import (
        sweep_efficiency_vs_load,
        generate_efficiency_map,
        export_efficiency_curve_csv,
        export_efficiency_map_csv,
        print_efficiency_summary,
    )


def main():
    """
    Complete efficiency analysis for 6.6kW marine PSFB.
    """
    print("=" * 80)
    print("6.6kW MARINE PSFB - EFFICIENCY ANALYSIS")
    print("=" * 80)
    print()

    # ========================================================================
    # Component Definitions (same as complete analysis example)
    # ========================================================================

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

    secondary_diode = DiodeParameters(
        part_number="C4D30120A",
        v_rrm=1200.0,
        i_f_avg=31.0,
        v_f0=0.0,
        r_d=35e-3,
        q_rr=0.0,
        t_rr=0.0,
    )

    input_capacitor = CapacitorParameters(
        capacitance=100e-6,
        voltage_rating=500.0,
        esr=10e-3,
        ripple_current_rating=50.0,
    )

    output_capacitor = CapacitorParameters(
        capacitance=1000e-6,
        voltage_rating=350.0,
        esr=5e-3,
        ripple_current_rating=40.0,
    )

    # ========================================================================
    # Quick Magnetic Design (suppress output)
    # ========================================================================

    print("Designing magnetic components...")

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

    import io
    import contextlib

    with contextlib.redirect_stdout(io.StringIO()):
        zvs_req = ZVSRequirements(
            mosfet_coss=primary_mosfet.capacitances.get_coss(400.0),
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
            iout_nom=8.8,
            iout_max=10.0,
            frequency=100e3,
            n_phases=3,
            phase_shift_deg=120.0,
        )
        lo_design, _ = design_output_inductor(lo_spec, mag_spec, "PQ", "E")

    magnetics = MagneticComponents(
        resonant_inductor=lr_design,
        transformer=xfmr_design,
        output_inductor=lo_design,
    )

    print(f"  Magnetic components designed")
    print(f"  Transformer: {xfmr_design.n_primary}:{xfmr_design.n_secondary} turns")
    print()

    # ========================================================================
    # Efficiency vs. Load at Multiple Input Voltages
    # ========================================================================

    print("=" * 80)
    print("EFFICIENCY vs. LOAD ANALYSIS")
    print("=" * 80)
    print()

    input_voltages = [360, 400, 440]  # Min, Nominal, Max

    for vin in input_voltages:
        print(f"Analyzing @ Vin = {vin}V...")

        curve = sweep_efficiency_vs_load(
            rated_power=6600.0,
            input_voltage=vin,
            output_voltage=250.0,
            frequency=100e3,
            turns_ratio=xfmr_design.turns_ratio,
            n_phases=3,
            phase_shift_deg=120.0,
            primary_mosfet=primary_mosfet,
            secondary_diode=secondary_diode,
            magnetics=magnetics,
            input_capacitor=input_capacitor,
            output_capacitor=output_capacitor,
            load_points=[10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 100],
            zvs_operation=True,
        )

        print(f"  Peak Efficiency:     {curve.peak_efficiency:.2f}% @ {curve.peak_efficiency_load:.0f}% load")
        print(f"  Efficiency @ 50%:    {curve.efficiency_50_percent:.2f}%")
        print(f"  Efficiency @ 100%:   {curve.efficiency_100_percent:.2f}%")
        print()

        # Export to CSV
        filename = f"efficiency_vs_load_{vin}V.csv"
        export_efficiency_curve_csv(curve, filename)

    # ========================================================================
    # 2D Efficiency Map
    # ========================================================================

    print("=" * 80)
    print("2D EFFICIENCY MAP GENERATION")
    print("=" * 80)
    print()
    print("Generating efficiency map (this may take a minute)...")

    eff_map = generate_efficiency_map(
        rated_power=6600.0,
        output_voltage=250.0,
        frequency=100e3,
        turns_ratio=xfmr_design.turns_ratio,
        n_phases=3,
        phase_shift_deg=120.0,
        primary_mosfet=primary_mosfet,
        secondary_diode=secondary_diode,
        magnetics=magnetics,
        input_capacitor=input_capacitor,
        output_capacitor=output_capacitor,
        voltage_range=(360, 440, 5),  # 5 voltage points
        load_points=[10, 20, 25, 50, 75, 100],  # Key load points
        zvs_operation=True,
    )

    print()
    print_efficiency_summary(eff_map, 6600.0)

    # Export map to CSV
    export_efficiency_map_csv(eff_map, "efficiency_map_2d.csv")

    # ========================================================================
    # Efficiency Table (formatted output)
    # ========================================================================

    print()
    print("=" * 80)
    print("EFFICIENCY TABLE")
    print("=" * 80)
    print()
    print(f"{'Vin (V)':<10}", end="")
    for load in eff_map.load_points:
        print(f"{load:>8}%", end="")
    print()
    print("-" * 80)

    for i, vin in enumerate(eff_map.voltage_points):
        print(f"{vin:<10.0f}", end="")
        for eff in eff_map.efficiency_grid[i]:
            print(f"{eff:>9.2f}", end="")
        print()

    print()

    # ========================================================================
    # Standard Efficiency Metrics
    # ========================================================================

    print("=" * 80)
    print("STANDARD EFFICIENCY METRICS")
    print("=" * 80)
    print()
    print(f"CEC Weighted Efficiency:      {eff_map.cec_efficiency:.2f}%")
    print(f"  (0.04×10% + 0.05×20% + 0.12×30% + 0.21×50% + 0.53×75% + 0.05×100%)")
    print()
    print(f"European Weighted Efficiency: {eff_map.european_efficiency:.2f}%")
    print(f"  (0.03×10% + 0.06×20% + 0.13×30% + 0.10×50% + 0.48×75% + 0.20×100%)")
    print()
    print(f"Average Efficiency:           {eff_map.average_efficiency:.2f}%")
    print()

    # ========================================================================
    # 80 PLUS Certification Check
    # ========================================================================

    print("=" * 80)
    print("80 PLUS CERTIFICATION CHECK")
    print("=" * 80)
    print()

    # 80 PLUS certification levels (at 115V AC input, but we adapt for DC-DC)
    cert_levels = {
        "80 PLUS": {"20%": 80, "50%": 80, "100%": 80},
        "80 PLUS Bronze": {"20%": 82, "50%": 85, "100%": 82},
        "80 PLUS Silver": {"20%": 85, "50%": 88, "100%": 85},
        "80 PLUS Gold": {"20%": 87, "50%": 90, "100%": 87},
        "80 PLUS Platinum": {"20%": 90, "50%": 92, "100%": 89},
        "80 PLUS Titanium": {"20%": 92, "50%": 94, "100%": 90},
    }

    # Find efficiency at 400V nominal for certification check
    nom_curve = None
    for vin in input_voltages:
        if vin == 400:
            curve = sweep_efficiency_vs_load(
                rated_power=6600.0,
                input_voltage=400,
                output_voltage=250.0,
                frequency=100e3,
                turns_ratio=xfmr_design.turns_ratio,
                n_phases=3,
                phase_shift_deg=120.0,
                primary_mosfet=primary_mosfet,
                secondary_diode=secondary_diode,
                magnetics=magnetics,
                input_capacitor=input_capacitor,
                output_capacitor=output_capacitor,
                load_points=[20, 50, 100],
                zvs_operation=True,
            )
            nom_curve = curve
            break

    if nom_curve:
        actual_20 = nom_curve.efficiency_20_percent
        actual_50 = nom_curve.efficiency_50_percent
        actual_100 = nom_curve.efficiency_100_percent

        print(f"Actual Efficiency (@ 400V):")
        print(f"  20% Load:  {actual_20:.2f}%")
        print(f"  50% Load:  {actual_50:.2f}%")
        print(f"  100% Load: {actual_100:.2f}%")
        print()

        highest_level = None
        for level, requirements in cert_levels.items():
            if (actual_20 >= requirements["20%"] and
                actual_50 >= requirements["50%"] and
                actual_100 >= requirements["100%"]):
                highest_level = level

        if highest_level:
            print(f"✓ Meets {highest_level} certification requirements!")
        else:
            print(f"✗ Does not meet 80 PLUS certification")

        print()

    # ========================================================================
    # Summary
    # ========================================================================

    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print()
    print("Generated Files:")
    print("  - efficiency_vs_load_360V.csv")
    print("  - efficiency_vs_load_400V.csv")
    print("  - efficiency_vs_load_440V.csv")
    print("  - efficiency_map_2d.csv")
    print()
    print("Key Findings:")
    print(f"  - Peak efficiency: {eff_map.peak_efficiency:.2f}% @ {eff_map.peak_efficiency_load:.0f}% load, {eff_map.peak_efficiency_vin:.0f}V")
    print(f"  - CEC efficiency:  {eff_map.cec_efficiency:.2f}%")
    print(f"  - EU efficiency:   {eff_map.european_efficiency:.2f}%")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user.")
    except Exception as e:
        print(f"\n\nError during analysis: {e}")
        import traceback
        traceback.print_exc()

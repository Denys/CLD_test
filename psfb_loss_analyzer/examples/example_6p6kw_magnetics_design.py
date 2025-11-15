"""
Complete Magnetic Component Design for 6.6kW Marine PSFB Converter

This example demonstrates the complete magnetic design process for a 3-phase
interleaved Phase-Shifted Full-Bridge DC-DC converter:

System Specification:
- Total Power: 6.6kW (3× 2.2kW phases, 120° phase shift)
- Input: 400V DC (360-440V range)
- Output: 250V DC
- Switching Frequency: 100kHz per phase
- Controller: UCC28951 (or equivalent PSFB controller)
- Primary MOSFETs: Infineon IMZA65R020M2H (650V, 20mΩ SiC)
- Secondary Rectifier: SiC Schottky diodes (full-bridge)

Magnetic Components (per phase):
1. Resonant Inductor (Lr): For ZVS operation from 10-100% load
2. Transformer: 400V → 250V isolation and voltage transformation
3. Output Inductor (Lo): Output current filtering with interleaving

Design Methodology:
- McLyman's Kg area product method for core selection
- Erickson & Maksimovic Kg_fe method verification
- TDK PQ series cores (primary) + alternative cores
- Light load ZVS optimization (10-30% load)

Author: PSFB Loss Analysis Tool
Version: 0.3.0
"""

import sys
import numpy as np

try:
    # When running as module
    from psfb_loss_analyzer.circuit_params import (
        MOSFETParameters,
        CapacitanceVsVoltage,
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
except ImportError:
    # When running directly
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from circuit_params import (
        MOSFETParameters,
        CapacitanceVsVoltage,
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


def print_section_header(title: str):
    """Print formatted section header"""
    print("\n")
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)
    print()


def print_subsection(title: str):
    """Print formatted subsection header"""
    print()
    print(f"--- {title} " + "-" * (76 - len(title)))
    print()


def main():
    """
    Complete magnetic design for 6.6kW marine PSFB converter.
    """
    print("=" * 80)
    print("6.6kW MARINE PSFB CONVERTER - COMPLETE MAGNETIC COMPONENT DESIGN")
    print("=" * 80)
    print()
    print("System Overview:")
    print("  Architecture:        3-phase interleaved PSFB (120° phase shift)")
    print("  Total Power:         6.6 kW (3× 2.2kW phases)")
    print("  Input Voltage:       400V DC (360-440V range)")
    print("  Output Voltage:      250V DC")
    print("  Switching Frequency: 100 kHz")
    print("  Topology:            Phase-Shifted Full-Bridge with diode rectifier")
    print()
    print("Design Approach:")
    print("  - Each phase is designed for 2.2kW")
    print("  - Resonant inductors optimized for light load ZVS (10-30%)")
    print("  - Transformer designed for 400V→250V transformation")
    print("  - Output inductors with ripple cancellation benefit")
    print("  - Core selection: TDK PQ series + alternatives")
    print()
    input("Press Enter to begin design process...")

    # ========================================================================
    # System Parameters
    # ========================================================================

    print_section_header("SYSTEM PARAMETERS")

    # MOSFET: Infineon IMZA65R020M2H (650V, 20mΩ SiC)
    primary_mosfet = MOSFETParameters(
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

    print("Primary MOSFET: Infineon IMZA65R020M2H (CoolSiC™)")
    print(f"  V_DSS:               {primary_mosfet.v_dss:.0f} V")
    print(f"  I_D:                 {primary_mosfet.i_d_continuous:.0f} A")
    print(f"  R_DS(on) @ 25°C:     {primary_mosfet.r_dson_25c * 1000:.1f} mΩ (typ)")
    print(f"  C_oss @ 400V:        {primary_mosfet.capacitances.c_oss * 1e12:.0f} pF")
    print()

    # Common magnetic design specification
    mag_spec = MagneticDesignSpec(
        power=2200.0,  # Per phase
        frequency=100e3,
        temp_ambient=40.0,
        temp_rise_max=60.0,
        current_density_max=5.0,  # A/mm² for forced air cooling
        window_utilization=0.5,
        flux_density_max=0.25,  # Conservative for 100kHz
        core_material=CoreMaterial.FERRITE_3C95,
        enable_light_load_zvs=True,
        min_load_percentage=10.0,
    )

    print("Magnetic Design Specification (per phase):")
    print(f"  Power:               {mag_spec.power:.0f} W")
    print(f"  Frequency:           {mag_spec.frequency / 1000:.0f} kHz")
    print(f"  Current Density:     {mag_spec.current_density_max:.1f} A/mm²")
    print(f"  Flux Density:        {mag_spec.flux_density_max:.2f} T")
    print(f"  Core Material:       {mag_spec.core_material.value}")
    print(f"  Cooling:             Forced air")
    print()

    # ========================================================================
    # PART 1: RESONANT INDUCTOR DESIGN
    # ========================================================================

    print_section_header("PART 1: RESONANT INDUCTOR DESIGN (Lr)")

    print("Purpose: Enable Zero-Voltage Switching (ZVS) from 10% to 100% load")
    print()
    input("Press Enter to design resonant inductor...")

    # ZVS requirements
    zvs_req = ZVSRequirements(
        mosfet_coss=primary_mosfet.capacitances.c_oss,
        mosfet_vds_max=primary_mosfet.v_dss,
        n_mosfets_parallel=2,  # Q1-Q2 in series, treat as 2 for Coss calc
        vin_min=360.0,
        vin_nom=400.0,
        vin_max=440.0,
        load_full=2200.0,  # Per phase
        load_min_zvs=220.0,  # 10% load
        load_min_percent=10.0,
        turns_ratio=16.0 / 30.0,  # Will be refined by transformer design
        magnetizing_inductance=200e-6,  # Estimated, will update
        frequency=100e3,
        dead_time_target=500e-9,
        zvs_energy_margin=1.5,
    )

    # Design resonant inductor
    lr_pq, lr_alt = design_resonant_inductor(
        zvs_req=zvs_req,
        spec=mag_spec,
        core_family="PQ",
        alternative_family="ETD",
    )

    print_subsection("Resonant Inductor Design Summary")
    print(f"Recommended Design (PQ core): {lr_pq.core_name}")
    print(f"  Inductance:          {lr_pq.inductance_magnetizing * 1e6:.2f} µH")
    print(f"  Turns:               {lr_pq.n_primary}")
    print(f"  Core Loss:           {lr_pq.core_loss:.2f} W")
    print(f"  Copper Loss:         {lr_pq.copper_loss_primary:.2f} W")
    print(f"  Total Loss:          {lr_pq.total_loss:.2f} W")
    print(f"  Efficiency:          {lr_pq.efficiency:.2f}%")
    print(f"  Temperature Rise:    {lr_pq.temp_rise_estimate:.1f} °C")
    print()
    print(f"Alternative Design ({lr_alt.core_name}):")
    print(f"  Total Loss:          {lr_alt.total_loss:.2f} W")
    print(f"  Temperature Rise:    {lr_alt.temp_rise_estimate:.1f} °C")
    print()

    # ========================================================================
    # PART 2: TRANSFORMER DESIGN
    # ========================================================================

    print_section_header("PART 2: TRANSFORMER DESIGN (T1)")

    print("Purpose: Galvanic isolation and 400V→250V voltage transformation")
    print()
    input("Press Enter to design transformer...")

    # Transformer specification
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

    # Design transformer
    xfmr_pq, xfmr_alt = design_transformer(
        xfmr_spec=xfmr_spec,
        mag_spec=mag_spec,
        core_family="PQ",
        alternative_family="ETD",
    )

    print_subsection("Transformer Design Summary")
    print(f"Recommended Design (PQ core): {xfmr_pq.core_name}")
    print(f"  Turns Ratio:         {xfmr_pq.n_primary}:{xfmr_pq.n_secondary} (n={xfmr_pq.turns_ratio:.4f})")
    print(f"  Magnetizing L:       {xfmr_pq.inductance_magnetizing * 1e6:.0f} µH")
    print(f"  Leakage L:           {xfmr_pq.inductance_leakage * 1e6:.2f} µH")
    print(f"  Peak Flux Density:   {xfmr_pq.flux_density_peak * 1000:.0f} mT")
    print(f"  Core Loss:           {xfmr_pq.core_loss:.2f} W")
    print(f"  Primary Cu Loss:     {xfmr_pq.copper_loss_primary:.2f} W")
    print(f"  Secondary Cu Loss:   {xfmr_pq.copper_loss_secondary:.2f} W")
    print(f"  Total Loss:          {xfmr_pq.total_loss:.2f} W")
    print(f"  Efficiency:          {xfmr_pq.efficiency:.2f}%")
    print(f"  Temperature Rise:    {xfmr_pq.temp_rise_estimate:.1f} °C")
    print()
    print(f"Alternative Design ({xfmr_alt.core_name}):")
    print(f"  Turns:               {xfmr_alt.n_primary}:{xfmr_alt.n_secondary}")
    print(f"  Total Loss:          {xfmr_alt.total_loss:.2f} W")
    print(f"  Temperature Rise:    {xfmr_alt.temp_rise_estimate:.1f} °C")
    print()

    # ========================================================================
    # PART 3: OUTPUT INDUCTOR DESIGN
    # ========================================================================

    print_section_header("PART 3: OUTPUT INDUCTOR DESIGN (Lo)")

    print("Purpose: Output current filtering with 3-phase interleaving")
    print("Note: Each phase has its own inductor, ripple cancellation at output node")
    print()
    input("Press Enter to design output inductor...")

    # Output inductor specification
    # Total output: 6.6kW @ 250V = 26.4A
    # Per phase: 2.2kW @ 250V = 8.8A
    inductor_spec = OutputInductorSpec(
        vout_nom=250.0,
        iout_nom=8.8,  # Per phase (26.4A / 3 phases)
        iout_max=10.0,  # Per phase with margin
        current_ripple_percent=30.0,  # 30% ripple per inductor
        frequency=100e3,
        duty_cycle_nom=0.45,
        n_phases=3,
        phase_shift_deg=120.0,
    )

    # Design output inductor
    lo_pq, lo_alt = design_output_inductor(
        inductor_spec=inductor_spec,
        mag_spec=mag_spec,
        core_family="PQ",
        alternative_family="E",
    )

    print_subsection("Output Inductor Design Summary")
    print(f"Recommended Design (PQ core): {lo_pq.core_name}")
    print(f"  Inductance:          {lo_pq.inductance_magnetizing * 1e6:.1f} µH")
    print(f"  Turns:               {lo_pq.n_primary}")
    print(f"  Peak Flux Density:   {lo_pq.flux_density_peak * 1000:.0f} mT")
    print(f"  Core Loss:           {lo_pq.core_loss:.2f} W")
    print(f"  Copper Loss:         {lo_pq.copper_loss_primary:.2f} W")
    print(f"  Total Loss:          {lo_pq.total_loss:.2f} W (per phase)")
    print(f"  Efficiency:          {lo_pq.efficiency:.2f}%")
    print(f"  Temperature Rise:    {lo_pq.temp_rise_estimate:.1f} °C")
    print()
    print(f"Alternative Design ({lo_alt.core_name}):")
    print(f"  Inductance:          {lo_alt.inductance_magnetizing * 1e6:.1f} µH")
    print(f"  Total Loss:          {lo_alt.total_loss:.2f} W")
    print(f"  Temperature Rise:    {lo_alt.temp_rise_estimate:.1f} °C")
    print()

    # ========================================================================
    # SYSTEM SUMMARY
    # ========================================================================

    print_section_header("COMPLETE SYSTEM SUMMARY - 6.6kW MARINE PSFB")

    print("3-Phase Interleaved Configuration (120° phase shift)")
    print()
    print("Per-Phase Magnetic Components (× 3 for complete system):")
    print("-" * 80)
    print()

    print("1. RESONANT INDUCTOR (Lr):")
    print(f"   Core:                {lr_pq.core_name}")
    print(f"   Inductance:          {lr_pq.inductance_magnetizing * 1e6:.2f} µH")
    print(f"   Turns:               {lr_pq.n_primary}")
    print(f"   Loss:                {lr_pq.total_loss:.2f} W per phase")
    print()

    print("2. TRANSFORMER (T1):")
    print(f"   Core:                {xfmr_pq.core_name}")
    print(f"   Turns Ratio:         {xfmr_pq.n_primary}:{xfmr_pq.n_secondary}")
    print(f"   Magnetizing L:       {xfmr_pq.inductance_magnetizing * 1e6:.0f} µH")
    print(f"   Leakage L:           {xfmr_pq.inductance_leakage * 1e6:.2f} µH")
    print(f"   Loss:                {xfmr_pq.total_loss:.2f} W per phase")
    print()

    print("3. OUTPUT INDUCTOR (Lo):")
    print(f"   Core:                {lo_pq.core_name}")
    print(f"   Inductance:          {lo_pq.inductance_magnetizing * 1e6:.1f} µH")
    print(f"   Turns:               {lo_pq.n_primary}")
    print(f"   Loss:                {lo_pq.total_loss:.2f} W per phase")
    print()

    print("-" * 80)
    print("TOTAL MAGNETIC LOSS BREAKDOWN (all 3 phases):")
    print("-" * 80)

    total_lr_loss = lr_pq.total_loss * 3
    total_xfmr_loss = xfmr_pq.total_loss * 3
    total_lo_loss = lo_pq.total_loss * 3
    total_magnetic_loss = total_lr_loss + total_xfmr_loss + total_lo_loss

    print(f"Resonant Inductors:    {total_lr_loss:.2f} W  (3× {lr_pq.total_loss:.2f}W)")
    print(f"Transformers:          {total_xfmr_loss:.2f} W  (3× {xfmr_pq.total_loss:.2f}W)")
    print(f"Output Inductors:      {total_lo_loss:.2f} W  (3× {lo_pq.total_loss:.2f}W)")
    print(f"{'':>24}{'─' * 20}")
    print(f"Total Magnetic Loss:   {total_magnetic_loss:.2f} W")
    print()
    print(f"System Output Power:   {6600.0:.0f} W")
    print(f"Magnetic Efficiency:   {100.0 * (1.0 - total_magnetic_loss / 6600.0):.2f}%")
    print(f"Loss Percentage:       {100.0 * total_magnetic_loss / 6600.0:.2f}% of output power")
    print()

    print("-" * 80)
    print("BILL OF MATERIALS - MAGNETIC COMPONENTS:")
    print("-" * 80)
    print()
    print(f"QTY  PART NUMBER              DESCRIPTION")
    print(f"─── ──────────────────────── ────────────────────────────────────")
    print(f" 3   {lr_pq.core_name:20s}     Resonant Inductor Core ({lr_pq.n_primary} turns)")
    print(f" 3   {xfmr_pq.core_name:20s}     Transformer Core ({xfmr_pq.n_primary}:{xfmr_pq.n_secondary} turns)")
    print(f" 3   {lo_pq.core_name:20s}     Output Inductor Core ({lo_pq.n_primary} turns)")
    print()

    print("=" * 80)
    print("DESIGN COMPLETE")
    print("=" * 80)
    print()
    print("Next Steps:")
    print("  1. Procure magnetic cores from TDK or equivalent")
    print("  2. Design PCB layout with proper spacing and creepage")
    print("  3. Calculate total converter losses (add semiconductor losses)")
    print("  4. Design thermal management (heatsinks, fans)")
    print("  5. Build and test prototype (verify ZVS operation)")
    print()
    print("For semiconductor loss analysis, use:")
    print("  - mosfet_losses.py for primary-side MOSFET analysis")
    print("  - diode_losses.py for secondary-side diode analysis")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDesign interrupted by user.")
    except Exception as e:
        print(f"\n\nError during design: {e}")
        import traceback
        traceback.print_exc()

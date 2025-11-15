#!/usr/bin/env python3
"""
PSFB Loss Analyzer - Main CLI Interface

Command-line interface for PSFB converter loss analysis and optimization.

Usage:
    python main.py --config <config_file.json>
    python main.py --example  # Run with example 3kW marine design

Author: PSFB Loss Analysis Tool
Reference: Infineon "MOSFET Power Losses Calculation Using DataSheet Parameters"
"""

import argparse
import sys
from pathlib import Path

from .circuit_params import PSFBConfiguration, validate_configuration
from .config_loader import ConfigurationLoader


def print_banner():
    """Print application banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║         PSFB LOSS ANALYZER & OPTIMIZATION SUITE                   ║
║                                                                   ║
║         Phase-Shifted Full-Bridge Converter Analysis              ║
║         Based on Infineon Application Note Methodology            ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def display_configuration_summary(config: PSFBConfiguration):
    """
    Display a detailed summary of the configuration

    Args:
        config: PSFB configuration to display
    """
    print("\n" + "="*70)
    print("CONFIGURATION SUMMARY")
    print("="*70)
    print(config)

    # Additional component details
    print("COMPONENT DETAILS")
    print("="*70)

    print("\nPrimary Side (Q1-Q4):")
    pm = config.components.primary_mosfets
    print(f"  Device:            {pm.part_number}")
    print(f"  Voltage rating:    {pm.v_dss} V")
    print(f"  Current rating:    {pm.i_d_continuous} A @ 25°C")
    print(f"  RDS(on) @ 25°C:    {pm.r_dson_25c*1e3:.2f} mΩ (typ), {pm.r_dson_25c_max*1e3:.2f} mΩ (max)")
    print(f"  RDS(on) @ 150°C:   {pm.r_dson_150c*1e3:.2f} mΩ (typ), {pm.r_dson_150c_max*1e3:.2f} mΩ (max)")
    print(f"  Temp coefficient:  α = {pm.alpha_rdson:.3f} %/°C")
    print(f"  Gate charge:       Qg = {pm.q_g*1e9:.1f} nC, Qgd = {pm.q_gd*1e9:.1f} nC")
    print(f"  Thermal:           Rth(j-c) = {pm.r_th_jc:.2f} °C/W")

    if config.components.secondary_mosfets:
        sm = config.components.secondary_mosfets
        print(f"\nSecondary Side SR MOSFETs:")
        print(f"  Device:            {sm.part_number}")
        print(f"  Voltage rating:    {sm.v_dss} V")
        print(f"  Current rating:    {sm.i_d_continuous} A @ 25°C")
        print(f"  RDS(on) @ 25°C:    {sm.r_dson_25c*1e3:.3f} mΩ (typ), {sm.r_dson_25c_max*1e3:.3f} mΩ (max)")
        print(f"  RDS(on) @ 150°C:   {sm.r_dson_150c*1e3:.3f} mΩ (typ), {sm.r_dson_150c_max*1e3:.3f} mΩ (max)")
        print(f"  Temp coefficient:  α = {sm.alpha_rdson:.3f} %/°C")

    elif config.components.secondary_diodes:
        sd = config.components.secondary_diodes
        print(f"\nSecondary Side Diodes:")
        print(f"  Device:            {sd.part_number}")
        print(f"  Voltage rating:    {sd.v_rrm} V")
        print(f"  Current rating:    {sd.i_f_avg} A")
        print(f"  Forward voltage:   VF0 = {sd.v_f0} V, RD = {sd.r_d*1e3:.2f} mΩ")
        print(f"  Reverse recovery:  Qrr = {sd.q_rr*1e9:.1f} nC")

    xfmr = config.components.transformer
    print(f"\nTransformer:")
    print(f"  Core:              {xfmr.core_geometry.core_type} ({xfmr.core_material.value})")
    print(f"  Turns ratio:       {xfmr.primary_winding.n_turns}:{xfmr.secondary_winding.n_turns}")
    print(f"  Ae:                {xfmr.core_geometry.effective_area*1e6:.1f} mm²")
    print(f"  Ve:                {xfmr.core_geometry.effective_volume*1e6:.1f} cm³")
    print(f"  Lleak:             {xfmr.leakage_inductance*1e6:.2f} µH")
    print(f"  Lmag:              {xfmr.magnetizing_inductance*1e6:.1f} µH")
    print(f"  Primary winding:   {xfmr.primary_winding.n_turns} turns, "
          f"{xfmr.primary_winding.dc_resistance*1e3:.2f} mΩ DCR")
    print(f"  Secondary winding: {xfmr.secondary_winding.n_turns} turns, "
          f"{xfmr.secondary_winding.dc_resistance*1e3:.2f} mΩ DCR")

    print(f"\nOutput Filter:")
    print(f"  Inductor:          {config.components.output_inductor.inductance*1e6:.1f} µH, "
          f"{config.components.output_inductor.dc_resistance*1e3:.2f} mΩ DCR")
    print(f"  Output cap:        {config.components.output_capacitor.capacitance*1e6:.0f} µF, "
          f"{config.components.output_capacitor.esr*1e3:.1f} mΩ ESR")

    print(f"\nThermal Environment:")
    print(f"  Ambient temp:      {config.thermal.t_ambient}°C")
    print(f"  Cooling:           {config.thermal.cooling_method.value}")
    if config.thermal.cooling_method.value == "forced_air":
        print(f"  Airflow:           {config.thermal.forced_air_cfm} CFM")
    print(f"  Heatsink Rth(c-a): {config.thermal.heatsink_r_th_ca}°C/W")
    print(f"  Target Tj max:     {config.thermal.target_t_j_max}°C")


def validate_config(config: PSFBConfiguration) -> bool:
    """
    Validate configuration and display results

    Args:
        config: Configuration to validate

    Returns:
        True if validation passed
    """
    print("\n" + "="*70)
    print("CONFIGURATION VALIDATION")
    print("="*70)

    issues = config.validate()

    if not issues:
        print("✓ All validation checks passed")
        print("\nThe configuration is ready for loss analysis.")
        return True
    else:
        print("⚠ Validation warnings detected:\n")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}\n")
        print("Please review these warnings before proceeding with analysis.")
        return False


def run_analysis_placeholder(config: PSFBConfiguration):
    """
    Placeholder for loss analysis (to be implemented)

    Args:
        config: PSFB configuration
    """
    print("\n" + "="*70)
    print("LOSS ANALYSIS")
    print("="*70)
    print("\n⚠ Loss analysis engine not yet implemented.")
    print("\nNext steps:")
    print("  1. Implement mosfet_losses.py - MOSFET conduction and switching losses")
    print("  2. Implement transformer_losses.py - Core and winding losses")
    print("  3. Implement diode_losses.py - Rectifier losses (if applicable)")
    print("  4. Implement thermal_solver.py - Junction temperature iteration")
    print("  5. Implement efficiency_mapper.py - Efficiency vs load/voltage curves")
    print("  6. Implement optimizer.py - Component and parameter optimization")
    print("  7. Implement report_generator.py - Results output and visualization")

    print(f"\nConfiguration loaded successfully: {config.project_name}")
    print(f"Ready for analysis implementation.")


def main():
    """Main entry point for CLI"""

    parser = argparse.ArgumentParser(
        description="PSFB Loss Analyzer - Comprehensive loss analysis for Phase-Shifted Full-Bridge converters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a configuration file
  python main.py --config my_design.json

  # Run with example 3kW marine design
  python main.py --example

  # Validate configuration only
  python main.py --config my_design.json --validate-only

  # Export configuration template
  python main.py --export-template my_template.json

For more information, see README.md
        """
    )

    parser.add_argument(
        '-c', '--config',
        type=str,
        help='Path to PSFB configuration JSON file'
    )

    parser.add_argument(
        '-e', '--example',
        action='store_true',
        help='Run analysis on example 3kW marine PSFB design'
    )

    parser.add_argument(
        '-v', '--validate-only',
        action='store_true',
        help='Only validate configuration, do not run analysis'
    )

    parser.add_argument(
        '--export-template',
        type=str,
        metavar='FILENAME',
        help='Export a configuration template JSON file'
    )

    parser.add_argument(
        '--show-params',
        action='store_true',
        help='Display detailed parameter information'
    )

    args = parser.parse_args()

    # Print banner
    print_banner()

    # Handle template export
    if args.export_template:
        print(f"Generating example configuration and exporting to {args.export_template}...")
        # Import the example configuration
        sys.path.append(str(Path(__file__).parent / 'examples'))
        from example_3kw_marine_psfb import create_3kw_marine_config

        example_config = create_3kw_marine_config()
        example_config.to_json(args.export_template, indent=2)
        print(f"✓ Template exported to: {args.export_template}")
        print("\nYou can now edit this file with your design parameters.")
        return 0

    # Determine which configuration to load
    config = None

    if args.example:
        print("Loading example 3kW marine PSFB configuration...\n")
        # Import the example configuration
        sys.path.append(str(Path(__file__).parent / 'examples'))
        from example_3kw_marine_psfb import create_3kw_marine_config
        config = create_3kw_marine_config()

    elif args.config:
        print(f"Loading configuration from: {args.config}\n")
        try:
            config = ConfigurationLoader.from_json_file(args.config)
        except FileNotFoundError:
            print(f"✗ Error: Configuration file not found: {args.config}")
            return 1
        except Exception as e:
            print(f"✗ Error loading configuration: {e}")
            return 1

    else:
        print("✗ Error: No configuration specified.")
        print("\nUse --config <file.json> to load a configuration")
        print("or --example to run with the example design.")
        print("Use --help for more options.")
        return 1

    # Display configuration summary if requested
    if args.show_params:
        display_configuration_summary(config)

    # Validate configuration
    validation_passed = validate_config(config)

    if args.validate_only:
        # Only validation requested
        if validation_passed:
            print("\n✓ Configuration validation complete.")
            return 0
        else:
            print("\n⚠ Configuration has warnings (see above).")
            return 1

    # Run analysis (placeholder for now)
    if validation_passed:
        run_analysis_placeholder(config)
    else:
        print("\n⚠ Proceeding with analysis despite validation warnings...")
        run_analysis_placeholder(config)

    return 0


if __name__ == "__main__":
    sys.exit(main())

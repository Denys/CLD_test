"""
Automated PSFB Converter Design Example

Demonstrates the automated design optimization capability:
- Input: Design specifications (power, voltage, efficiency targets)
- Output: Optimized component selection and design parameters

The optimizer automatically:
1. Selects MOSFETs and diodes from component library
2. Optimizes switching frequency and turns ratio
3. Designs magnetic components
4. Evaluates multiple objectives (efficiency, cost, size)
5. Generates Pareto frontier for trade-off analysis

Example: Design a 3kW, 400V→48V PSFB converter

Author: PSFB Loss Analysis Tool
Version: 0.5.0
"""

import sys
import os

try:
    from psfb_loss_analyzer.optimizer import (
        DesignSpecification,
        optimize_design,
        print_optimization_summary,
        ObjectiveFunction,
    )
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from optimizer import (
        DesignSpecification,
        optimize_design,
        print_optimization_summary,
        ObjectiveFunction,
    )


def main():
    """
    Automated design example: 3kW, 400V→48V PSFB converter
    """
    print("=" * 80)
    print("AUTOMATED PSFB CONVERTER DESIGN")
    print("=" * 80)
    print()
    print("Application: 3kW Telecom Power Supply")
    print("  Input:  300-420V DC (battery backup with wide range)")
    print("  Output: 48V DC @ 62.5A")
    print("  Target: >95% efficiency, cost-effective design")
    print()
    input("Press Enter to begin automated design...")
    print()

    # ========================================================================
    # Define Design Specification
    # ========================================================================

    spec = DesignSpecification(
        # Power requirements
        power_min=500.0,  # Light load
        power_rated=3000.0,  # Rated power
        power_max=3300.0,  # Peak capability

        # Voltage requirements
        vin_min=300.0,  # Minimum input
        vin_nom=380.0,  # Nominal input
        vin_max=420.0,  # Maximum input
        vout_nom=48.0,  # Output voltage
        vout_regulation=0.02,  # ±2% regulation

        # Configuration
        n_phases=1,  # Single phase
        phase_shift_deg=0.0,

        # Performance targets
        efficiency_target=0.95,  # 95% minimum
        zvs_enable=True,  # Enable ZVS

        # Thermal constraints
        temp_ambient_max=50.0,  # 50°C ambient
        temp_junction_max_mosfet=125.0,
        temp_junction_max_diode=150.0,
    )

    # ========================================================================
    # Run Optimization
    # ========================================================================

    result = optimize_design(
        spec=spec,
        objective=ObjectiveFunction.BALANCED,
        max_evaluations=50,  # Limit for faster demo (use 200+ for production)
        verbose=True,
    )

    # ========================================================================
    # Print Results
    # ========================================================================

    print_optimization_summary(result)

    # ========================================================================
    # Detailed Analysis of Best Design
    # ========================================================================

    if result.best_balanced:
        print("=" * 80)
        print("DETAILED ANALYSIS - RECOMMENDED DESIGN")
        print("=" * 80)
        print()

        design = result.best_balanced

        print("Component Selection:")
        print(f"  Primary MOSFETs:     4× {design.primary_mosfet_part}")
        print(f"    Voltage Rating:    {design.primary_mosfet.v_dss:.0f} V")
        print(f"    Current Rating:    {design.primary_mosfet.i_d_continuous:.0f} A")
        print(f"    R_DS(on) @ 25°C:   {design.primary_mosfet.r_dson_25c_max * 1000:.1f} mΩ")
        print()

        print(f"  Secondary Diodes:    4× {design.secondary_diode_part}")
        print(f"    Voltage Rating:    {design.secondary_diode.v_rrm:.0f} V")
        print(f"    Current Rating:    {design.secondary_diode.i_f_avg:.0f} A")
        if design.secondary_diode.v_f0 > 0:
            print(f"    Type:              Si PN Diode")
        else:
            print(f"    Type:              SiC Schottky (Zero Recovery)")
        print()

        print("Design Parameters:")
        print(f"  Switching Frequency: {design.switching_frequency / 1000:.0f} kHz")
        print(f"  Transformer Ratio:   {design.turns_ratio:.3f} (N_pri/N_sec)")
        print(f"  Input Capacitor:     {design.input_capacitor_part}")
        print(f"  Output Capacitor:    {design.output_capacitor_part}")
        print()

        print("Magnetic Components:")
        if design.magnetics:
            print(f"  Resonant Inductor:   {design.magnetics.resonant_inductor.inductance_magnetizing * 1e6:.1f} µH")
            print(f"    Core:              {design.magnetics.resonant_inductor.core_name}")
            print(f"    Loss:              {design.magnetics.resonant_inductor.total_loss:.2f} W")
            print()

            print(f"  Transformer:         {design.magnetics.transformer.n_primary}:{design.magnetics.transformer.n_secondary} turns")
            print(f"    Core:              {design.magnetics.transformer.core_name}")
            print(f"    Magnetizing L:     {design.magnetics.transformer.inductance_magnetizing * 1e6:.0f} µH")
            print(f"    Loss:              {design.magnetics.transformer.total_loss:.2f} W")
            print()

            print(f"  Output Inductor:     {design.magnetics.output_inductor.inductance_magnetizing * 1e6:.1f} µH")
            print(f"    Core:              {design.magnetics.output_inductor.core_name}")
            print(f"    Loss:              {design.magnetics.output_inductor.total_loss:.2f} W")
            print()

        print("Performance:")
        print(f"  Efficiency @ 100%:   {design.efficiency_full_load:.2f}%")
        print(f"  Efficiency @ 50%:    {design.efficiency_half_load:.2f}%")
        print(f"  CEC Efficiency:      {design.efficiency_cec:.2f}%")
        print(f"  Total Loss:          {design.total_loss:.2f} W")
        print(f"  Temperature Rise:    ~{design.temp_rise_max:.1f} °C")
        print()

        print("Economics:")
        print(f"  Relative Cost:       {design.relative_cost:.1f}")
        print(f"  Relative Size:       {design.relative_size:.1f} cm³")
        print()

        if design.constraint_violations:
            print("⚠ Constraint Violations:")
            for violation in design.constraint_violations:
                print(f"  - {violation}")
            print()
        else:
            print("✓ All constraints satisfied")
            print()

    # ========================================================================
    # Pareto Frontier Analysis
    # ========================================================================

    if len(result.pareto_optimal) > 1:
        print("=" * 80)
        print("PARETO FRONTIER TRADE-OFF ANALYSIS")
        print("=" * 80)
        print()
        print("Multiple optimal designs with different trade-offs:")
        print()
        print(f"{'Efficiency':<12} {'Cost':<10} {'Size':<10} {'Primary MOSFET':<20} {'Frequency':<12}")
        print("-" * 80)

        for design in sorted(result.pareto_optimal, key=lambda d: -d.efficiency_cec)[:10]:
            print(f"{design.efficiency_cec:>10.2f}%  {design.relative_cost:>8.1f}  "
                  f"{design.relative_size:>8.0f}  {design.primary_mosfet_part:<20} "
                  f"{design.switching_frequency/1000:>8.0f} kHz")
        print()

    # ========================================================================
    # Design Recommendations
    # ========================================================================

    print("=" * 80)
    print("DESIGN RECOMMENDATIONS")
    print("=" * 80)
    print()

    if result.best_efficiency and result.best_cost and result.best_balanced:
        print("Choose based on your priorities:")
        print()

        print("1. MAXIMUM EFFICIENCY:")
        print(f"   {result.best_efficiency.primary_mosfet_part} + {result.best_efficiency.secondary_diode_part}")
        print(f"   Efficiency: {result.best_efficiency.efficiency_cec:.2f}%, Cost: {result.best_efficiency.relative_cost:.1f}")
        print(f"   → Best for: High-efficiency applications, data centers")
        print()

        print("2. LOWEST COST:")
        print(f"   {result.best_cost.primary_mosfet_part} + {result.best_cost.secondary_diode_part}")
        print(f"   Efficiency: {result.best_cost.efficiency_cec:.2f}%, Cost: {result.best_cost.relative_cost:.1f}")
        print(f"   → Best for: Cost-sensitive applications, high-volume")
        print()

        print("3. BALANCED (RECOMMENDED):")
        print(f"   {result.best_balanced.primary_mosfet_part} + {result.best_balanced.secondary_diode_part}")
        print(f"   Efficiency: {result.best_balanced.efficiency_cec:.2f}%, Cost: {result.best_balanced.relative_cost:.1f}")
        print(f"   → Best for: General purpose, good efficiency/cost trade-off")
        print()

    print("=" * 80)
    print()


def example_multi_phase():
    """
    Example: Automated design for 6.6kW, 3-phase interleaved PSFB
    """
    print("=" * 80)
    print("AUTOMATED DESIGN - 6.6kW MARINE PSFB (3-PHASE)")
    print("=" * 80)
    print()

    spec = DesignSpecification(
        power_min=1700.0,
        power_rated=6600.0,
        power_max=7000.0,
        vin_min=360.0,
        vin_nom=400.0,
        vin_max=440.0,
        vout_nom=250.0,
        n_phases=3,
        phase_shift_deg=120.0,
        efficiency_target=0.96,
        zvs_enable=True,
    )

    result = optimize_design(
        spec=spec,
        objective=ObjectiveFunction.MAXIMIZE_EFFICIENCY,
        max_evaluations=30,  # Reduced for demo
        verbose=True,
    )

    print_optimization_summary(result)


if __name__ == "__main__":
    try:
        # Run single-phase example
        main()

        # Optionally run multi-phase example
        print()
        response = input("Run multi-phase (6.6kW) example? (y/n): ")
        if response.lower() == 'y':
            print()
            example_multi_phase()

    except KeyboardInterrupt:
        print("\n\nDesign interrupted by user.")
    except Exception as e:
        print(f"\n\nError during design: {e}")
        import traceback
        traceback.print_exc()

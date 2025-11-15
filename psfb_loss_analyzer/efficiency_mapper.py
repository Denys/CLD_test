"""
Efficiency Mapping and Characterization for PSFB Converters

Generates comprehensive efficiency data across operating range:
- Efficiency vs. load curves (light load to overload)
- Efficiency vs. input voltage curves
- 2D efficiency maps (load vs. Vin)
- California Energy Commission (CEC) weighted efficiency
- European efficiency (EU 2019/1782)
- Peak efficiency identification and operating point
- Data export for plotting and documentation

Key Features:
- Operating point sweep with configurable resolution
- Multiple efficiency metrics (CEC, EU, peak, average)
- CSV export for external plotting tools
- Matplotlib integration for immediate visualization
- Loss breakdown at key operating points

Design References:
- California Energy Commission Test Method for Determining Appliance Efficiency
- EU Regulation 2019/1782 on standby and networked standby power consumption
- 80 PLUS certification levels

Author: PSFB Loss Analysis Tool
Version: 0.4.0
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
import numpy as np
import csv
from pathlib import Path

try:
    from .system_analyzer import (
        analyze_psfb_system,
        MagneticComponents,
        SystemLosses,
    )
    from .circuit_params import (
        MOSFETParameters,
        DiodeParameters,
        CapacitorParameters,
    )
except ImportError:
    from system_analyzer import (
        analyze_psfb_system,
        MagneticComponents,
        SystemLosses,
    )
    from circuit_params import (
        MOSFETParameters,
        DiodeParameters,
        CapacitorParameters,
    )


@dataclass
class EfficiencyPoint:
    """Single efficiency measurement point"""
    input_voltage: float  # Input voltage (V)
    output_power: float  # Output power (W)
    load_percent: float  # Load percentage (%)
    efficiency: float  # Efficiency (%)
    total_loss: float  # Total loss (W)
    input_power: float  # Input power (W)

    # Loss breakdown
    mosfet_loss: float = 0.0
    diode_loss: float = 0.0
    magnetic_loss: float = 0.0
    capacitor_loss: float = 0.0


@dataclass
class EfficiencyCurve:
    """Efficiency vs. load curve at fixed input voltage"""
    input_voltage: float  # Fixed input voltage (V)
    points: List[EfficiencyPoint] = field(default_factory=list)

    # Summary statistics
    peak_efficiency: float = 0.0
    peak_efficiency_load: float = 0.0
    efficiency_10_percent: float = 0.0
    efficiency_20_percent: float = 0.0
    efficiency_50_percent: float = 0.0
    efficiency_100_percent: float = 0.0


@dataclass
class EfficiencyMap:
    """2D efficiency map (load vs. input voltage)"""
    load_points: List[float] = field(default_factory=list)  # Load percentages
    voltage_points: List[float] = field(default_factory=list)  # Input voltages
    efficiency_grid: List[List[float]] = field(default_factory=list)  # 2D efficiency array

    # Weighted efficiency metrics
    cec_efficiency: float = 0.0  # California Energy Commission
    european_efficiency: float = 0.0  # European Union
    average_efficiency: float = 0.0  # Simple average

    # Peak performance
    peak_efficiency: float = 0.0
    peak_efficiency_vin: float = 0.0
    peak_efficiency_load: float = 0.0


# ============================================================================
# Efficiency Sweep Functions
# ============================================================================

def sweep_efficiency_vs_load(
    rated_power: float,
    input_voltage: float,
    output_voltage: float,
    frequency: float,
    turns_ratio: float,
    n_phases: int,
    phase_shift_deg: float,
    primary_mosfet: MOSFETParameters,
    secondary_diode: DiodeParameters,
    magnetics: MagneticComponents,
    input_capacitor: Optional[CapacitorParameters] = None,
    output_capacitor: Optional[CapacitorParameters] = None,
    load_points: Optional[List[float]] = None,
    zvs_operation: bool = True,
    t_junction_mosfet: float = 100.0,
    t_junction_diode: float = 125.0,
) -> EfficiencyCurve:
    """
    Generate efficiency vs. load curve at fixed input voltage.

    Args:
        rated_power: Rated output power (W)
        input_voltage: Fixed input voltage (V)
        output_voltage: Output voltage (V)
        frequency: Switching frequency (Hz)
        turns_ratio: Transformer turns ratio
        n_phases: Number of phases
        phase_shift_deg: Phase shift (degrees)
        primary_mosfet: Primary MOSFET parameters
        secondary_diode: Secondary diode parameters
        magnetics: Magnetic component designs
        input_capacitor: Input capacitor (optional)
        output_capacitor: Output capacitor (optional)
        load_points: Load percentages to sweep (default: 5% to 110%)
        zvs_operation: ZVS flag
        t_junction_mosfet: MOSFET temperature (°C)
        t_junction_diode: Diode temperature (°C)

    Returns:
        EfficiencyCurve with efficiency data
    """
    # Default load points if not specified
    if load_points is None:
        load_points = [5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 100, 110]

    curve = EfficiencyCurve(input_voltage=input_voltage)

    for load_pct in load_points:
        output_power = rated_power * (load_pct / 100.0)

        # Calculate duty cycle for this operating point
        # For PSFB: Vout ≈ Vin × D × n
        duty_cycle = output_voltage / (input_voltage * turns_ratio * 2.0)
        duty_cycle = min(max(duty_cycle, 0.1), 0.48)

        # Analyze system at this operating point
        system_loss = analyze_psfb_system(
            input_voltage=input_voltage,
            output_voltage=output_voltage,
            output_power=output_power,
            frequency=frequency,
            duty_cycle=duty_cycle,
            turns_ratio=turns_ratio,
            n_phases=n_phases,
            phase_shift_deg=phase_shift_deg,
            primary_mosfet=primary_mosfet,
            secondary_diode=secondary_diode,
            magnetics=magnetics,
            input_capacitor=input_capacitor,
            output_capacitor=output_capacitor,
            zvs_operation=zvs_operation,
            t_junction_mosfet=t_junction_mosfet,
            t_junction_diode=t_junction_diode,
        )

        # Create efficiency point
        point = EfficiencyPoint(
            input_voltage=input_voltage,
            output_power=output_power,
            load_percent=load_pct,
            efficiency=system_loss.efficiency,
            total_loss=system_loss.total_loss,
            input_power=system_loss.input_power,
            mosfet_loss=system_loss.total_mosfet_loss,
            diode_loss=system_loss.total_diode_loss,
            magnetic_loss=system_loss.total_magnetic_loss,
            capacitor_loss=system_loss.total_capacitor_loss,
        )

        curve.points.append(point)

    # Calculate summary statistics
    if curve.points:
        # Peak efficiency
        peak_point = max(curve.points, key=lambda p: p.efficiency)
        curve.peak_efficiency = peak_point.efficiency
        curve.peak_efficiency_load = peak_point.load_percent

        # Efficiency at standard load points
        for point in curve.points:
            if abs(point.load_percent - 10) < 1:
                curve.efficiency_10_percent = point.efficiency
            elif abs(point.load_percent - 20) < 1:
                curve.efficiency_20_percent = point.efficiency
            elif abs(point.load_percent - 50) < 1:
                curve.efficiency_50_percent = point.efficiency
            elif abs(point.load_percent - 100) < 1:
                curve.efficiency_100_percent = point.efficiency

    return curve


def generate_efficiency_map(
    rated_power: float,
    output_voltage: float,
    frequency: float,
    turns_ratio: float,
    n_phases: int,
    phase_shift_deg: float,
    primary_mosfet: MOSFETParameters,
    secondary_diode: DiodeParameters,
    magnetics: MagneticComponents,
    input_capacitor: Optional[CapacitorParameters] = None,
    output_capacitor: Optional[CapacitorParameters] = None,
    voltage_range: Tuple[float, float, int] = (360, 440, 5),
    load_points: Optional[List[float]] = None,
    zvs_operation: bool = True,
) -> EfficiencyMap:
    """
    Generate 2D efficiency map (load vs. input voltage).

    Args:
        rated_power: Rated output power (W)
        output_voltage: Output voltage (V)
        frequency: Switching frequency (Hz)
        turns_ratio: Transformer turns ratio
        n_phases: Number of phases
        phase_shift_deg: Phase shift (degrees)
        primary_mosfet: Primary MOSFET parameters
        secondary_diode: Secondary diode parameters
        magnetics: Magnetic component designs
        input_capacitor: Input capacitor (optional)
        output_capacitor: Output capacitor (optional)
        voltage_range: (min_vin, max_vin, num_points)
        load_points: Load percentages (default: 10% to 100%)
        zvs_operation: ZVS flag

    Returns:
        EfficiencyMap with 2D efficiency data
    """
    # Default load points
    if load_points is None:
        load_points = [10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 100]

    # Voltage sweep points
    vin_min, vin_max, n_vin = voltage_range
    voltage_points = np.linspace(vin_min, vin_max, n_vin).tolist()

    # Initialize efficiency map
    eff_map = EfficiencyMap(
        load_points=load_points,
        voltage_points=voltage_points,
        efficiency_grid=[],
    )

    # Sweep both dimensions
    all_points = []

    for vin in voltage_points:
        eff_row = []

        for load_pct in load_points:
            output_power = rated_power * (load_pct / 100.0)

            # Calculate duty cycle
            duty_cycle = output_voltage / (vin * turns_ratio * 2.0)
            duty_cycle = min(max(duty_cycle, 0.1), 0.48)

            # Analyze system
            system_loss = analyze_psfb_system(
                input_voltage=vin,
                output_voltage=output_voltage,
                output_power=output_power,
                frequency=frequency,
                duty_cycle=duty_cycle,
                turns_ratio=turns_ratio,
                n_phases=n_phases,
                phase_shift_deg=phase_shift_deg,
                primary_mosfet=primary_mosfet,
                secondary_diode=secondary_diode,
                magnetics=magnetics,
                input_capacitor=input_capacitor,
                output_capacitor=output_capacitor,
                zvs_operation=zvs_operation,
            )

            eff_row.append(system_loss.efficiency)

            # Store for weighted efficiency calculations
            point = EfficiencyPoint(
                input_voltage=vin,
                output_power=output_power,
                load_percent=load_pct,
                efficiency=system_loss.efficiency,
                total_loss=system_loss.total_loss,
                input_power=system_loss.input_power,
            )
            all_points.append(point)

        eff_map.efficiency_grid.append(eff_row)

    # Find peak efficiency
    if all_points:
        peak_point = max(all_points, key=lambda p: p.efficiency)
        eff_map.peak_efficiency = peak_point.efficiency
        eff_map.peak_efficiency_vin = peak_point.input_voltage
        eff_map.peak_efficiency_load = peak_point.load_percent

        # Average efficiency
        eff_map.average_efficiency = np.mean([p.efficiency for p in all_points])

    # Calculate weighted efficiencies
    eff_map.cec_efficiency = calculate_cec_efficiency(all_points, rated_power)
    eff_map.european_efficiency = calculate_european_efficiency(all_points, rated_power)

    return eff_map


# ============================================================================
# Weighted Efficiency Calculations
# ============================================================================

def calculate_cec_efficiency(
    points: List[EfficiencyPoint],
    rated_power: float,
) -> float:
    """
    Calculate California Energy Commission (CEC) weighted efficiency.

    CEC Efficiency = 0.04×η_10% + 0.05×η_20% + 0.12×η_30% +
                     0.21×η_50% + 0.53×η_75% + 0.05×η_100%

    Args:
        points: List of efficiency points
        rated_power: Rated power (W)

    Returns:
        CEC weighted efficiency (%)
    """
    # CEC load points and weights
    cec_loads = {
        10: 0.04,
        20: 0.05,
        30: 0.12,
        50: 0.21,
        75: 0.53,
        100: 0.05,
    }

    # Find closest points to CEC load levels
    weighted_sum = 0.0
    total_weight = 0.0

    for load_pct, weight in cec_loads.items():
        # Find point closest to this load
        target_power = rated_power * (load_pct / 100.0)
        closest_point = min(points, key=lambda p: abs(p.output_power - target_power))

        weighted_sum += weight * closest_point.efficiency
        total_weight += weight

    cec_eff = weighted_sum / total_weight if total_weight > 0 else 0.0

    return cec_eff


def calculate_european_efficiency(
    points: List[EfficiencyPoint],
    rated_power: float,
) -> float:
    """
    Calculate European weighted efficiency (EU 2019/1782).

    EU Efficiency = 0.03×η_10% + 0.06×η_20% + 0.13×η_30% +
                    0.10×η_50% + 0.48×η_75% + 0.20×η_100%

    Args:
        points: List of efficiency points
        rated_power: Rated power (W)

    Returns:
        European weighted efficiency (%)
    """
    # EU load points and weights
    eu_loads = {
        10: 0.03,
        20: 0.06,
        30: 0.13,
        50: 0.10,
        75: 0.48,
        100: 0.20,
    }

    # Find closest points to EU load levels
    weighted_sum = 0.0
    total_weight = 0.0

    for load_pct, weight in eu_loads.items():
        target_power = rated_power * (load_pct / 100.0)
        closest_point = min(points, key=lambda p: abs(p.output_power - target_power))

        weighted_sum += weight * closest_point.efficiency
        total_weight += weight

    eu_eff = weighted_sum / total_weight if total_weight > 0 else 0.0

    return eu_eff


# ============================================================================
# Data Export Functions
# ============================================================================

def export_efficiency_curve_csv(
    curve: EfficiencyCurve,
    filename: str,
):
    """
    Export efficiency vs. load curve to CSV file.

    Args:
        curve: EfficiencyCurve to export
        filename: Output CSV filename
    """
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Header
        writer.writerow([
            'Load (%)',
            'Output Power (W)',
            'Efficiency (%)',
            'Total Loss (W)',
            'Input Power (W)',
            'MOSFET Loss (W)',
            'Diode Loss (W)',
            'Magnetic Loss (W)',
            'Capacitor Loss (W)',
        ])

        # Data rows
        for point in curve.points:
            writer.writerow([
                f"{point.load_percent:.1f}",
                f"{point.output_power:.2f}",
                f"{point.efficiency:.3f}",
                f"{point.total_loss:.2f}",
                f"{point.input_power:.2f}",
                f"{point.mosfet_loss:.2f}",
                f"{point.diode_loss:.2f}",
                f"{point.magnetic_loss:.2f}",
                f"{point.capacitor_loss:.2f}",
            ])

    print(f"Efficiency curve exported to: {filename}")


def export_efficiency_map_csv(
    eff_map: EfficiencyMap,
    filename: str,
):
    """
    Export 2D efficiency map to CSV file.

    Args:
        eff_map: EfficiencyMap to export
        filename: Output CSV filename
    """
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Header row (load percentages)
        header = ['Vin (V)'] + [f"{load}%" for load in eff_map.load_points]
        writer.writerow(header)

        # Data rows (one per input voltage)
        for i, vin in enumerate(eff_map.voltage_points):
            row = [f"{vin:.1f}"] + [f"{eff:.3f}" for eff in eff_map.efficiency_grid[i]]
            writer.writerow(row)

    print(f"Efficiency map exported to: {filename}")


def print_efficiency_summary(
    eff_map: EfficiencyMap,
    rated_power: float,
):
    """
    Print formatted efficiency summary.

    Args:
        eff_map: EfficiencyMap with results
        rated_power: Rated power (W)
    """
    print("=" * 80)
    print("EFFICIENCY SUMMARY")
    print("=" * 80)
    print()
    print(f"Rated Power:            {rated_power:.0f} W")
    print()
    print(f"Peak Efficiency:        {eff_map.peak_efficiency:.2f} %")
    print(f"  @ Vin:                {eff_map.peak_efficiency_vin:.0f} V")
    print(f"  @ Load:               {eff_map.peak_efficiency_load:.0f} %")
    print()
    print(f"Weighted Efficiency Metrics:")
    print(f"  CEC Efficiency:       {eff_map.cec_efficiency:.2f} %")
    print(f"  European Efficiency:  {eff_map.european_efficiency:.2f} %")
    print(f"  Average Efficiency:   {eff_map.average_efficiency:.2f} %")
    print()
    print("=" * 80)


# ============================================================================
# Matplotlib Plotting (Optional)
# ============================================================================

def plot_efficiency_curve(
    curve: EfficiencyCurve,
    show_loss_breakdown: bool = False,
    save_filename: Optional[str] = None,
):
    """
    Plot efficiency vs. load curve using matplotlib.

    Args:
        curve: EfficiencyCurve to plot
        show_loss_breakdown: Show loss breakdown subplot
        save_filename: Save plot to file (optional)
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Matplotlib not available. Install with: pip install matplotlib")
        return

    load = [p.load_percent for p in curve.points]
    efficiency = [p.efficiency for p in curve.points]

    if show_loss_breakdown:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

        # Efficiency plot
        ax1.plot(load, efficiency, 'b-o', linewidth=2, markersize=6)
        ax1.grid(True, alpha=0.3)
        ax1.set_xlabel('Load (%)', fontsize=12)
        ax1.set_ylabel('Efficiency (%)', fontsize=12)
        ax1.set_title(f'Efficiency vs. Load @ Vin = {curve.input_voltage:.0f}V', fontsize=14)
        ax1.set_ylim([min(efficiency) - 1, max(efficiency) + 1])

        # Loss breakdown plot
        mosfet_loss = [p.mosfet_loss for p in curve.points]
        diode_loss = [p.diode_loss for p in curve.points]
        magnetic_loss = [p.magnetic_loss for p in curve.points]
        capacitor_loss = [p.capacitor_loss for p in curve.points]

        ax2.plot(load, mosfet_loss, 'r-o', label='MOSFET', linewidth=2)
        ax2.plot(load, diode_loss, 'g-o', label='Diode', linewidth=2)
        ax2.plot(load, magnetic_loss, 'm-o', label='Magnetic', linewidth=2)
        ax2.plot(load, capacitor_loss, 'c-o', label='Capacitor', linewidth=2)
        ax2.grid(True, alpha=0.3)
        ax2.set_xlabel('Load (%)', fontsize=12)
        ax2.set_ylabel('Loss (W)', fontsize=12)
        ax2.set_title('Loss Breakdown vs. Load', fontsize=14)
        ax2.legend(loc='best')

        plt.tight_layout()
    else:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(load, efficiency, 'b-o', linewidth=2, markersize=6)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Load (%)', fontsize=12)
        ax.set_ylabel('Efficiency (%)', fontsize=12)
        ax.set_title(f'Efficiency vs. Load @ Vin = {curve.input_voltage:.0f}V', fontsize=14)
        ax.set_ylim([min(efficiency) - 1, max(efficiency) + 1])

    if save_filename:
        plt.savefig(save_filename, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {save_filename}")
    else:
        plt.show()


# ============================================================================
# Module Information
# ============================================================================

if __name__ == "__main__":
    print("PSFB Loss Analyzer - Efficiency Mapping Module")
    print("=" * 80)
    print()
    print("This module provides efficiency characterization:")
    print("  - Efficiency vs. load curves")
    print("  - Efficiency vs. input voltage")
    print("  - 2D efficiency maps")
    print("  - CEC weighted efficiency")
    print("  - European weighted efficiency")
    print("  - CSV export and matplotlib plotting")
    print()
    print("Use sweep_efficiency_vs_load() and generate_efficiency_map()")
    print()

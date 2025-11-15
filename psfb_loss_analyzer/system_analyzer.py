"""
System-Level Loss Analysis for PSFB Converters

Integrates all loss sources to calculate total converter efficiency:
- Primary-side MOSFET losses (4 switches per phase)
- Secondary-side rectifier losses (diodes or synchronous MOSFETs)
- Magnetic component losses (resonant inductor, transformer, output inductor)
- Capacitor ESR losses (input and output filter capacitors)
- Multi-phase interleaved operation support

Provides comprehensive loss breakdown, efficiency calculation, and system-level
analysis for Phase-Shifted Full-Bridge DC-DC converters.

Key Features:
- Complete system loss integration
- Multi-phase support (1-4 phases with arbitrary phase shift)
- Temperature-dependent loss calculations
- Detailed loss breakdown by component and loss mechanism
- Efficiency calculation across operating range
- Power loss density analysis

Design References:
- Infineon "MOSFET Power Losses Calculation Using the DataSheet Parameters"
- Erickson & Maksimovic "Fundamentals of Power Electronics" 3rd Ed.
- Various application notes on PSFB converter design

Author: PSFB Loss Analysis Tool
Version: 0.4.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict
from enum import Enum
import numpy as np

try:
    from .circuit_params import (
        PSFBConfiguration,
        MOSFETParameters,
        DiodeParameters,
        CapacitorParameters,
        RectifierType,
    )
    from .mosfet_losses import (
        MOSFETLosses,
        calculate_mosfet_losses,
        estimate_psfb_primary_waveform,
    )
    from .diode_losses import (
        DiodeLosses,
        calculate_diode_losses,
        estimate_fullbridge_diode_waveform,
    )
    from .magnetics_design import (
        MagneticDesignResult,
    )
except ImportError:
    from circuit_params import (
        PSFBConfiguration,
        MOSFETParameters,
        DiodeParameters,
        CapacitorParameters,
        RectifierType,
    )
    from mosfet_losses import (
        MOSFETLosses,
        calculate_mosfet_losses,
        estimate_psfb_primary_waveform,
    )
    from diode_losses import (
        DiodeLosses,
        calculate_diode_losses,
        estimate_fullbridge_diode_waveform,
    )
    from magnetics_design import (
        MagneticDesignResult,
    )


@dataclass
class CapacitorLosses:
    """Capacitor ESR losses"""
    capacitor_id: str
    esr: float  # ESR (Ω)
    current_rms: float  # RMS current (A)
    loss_total: float  # Total loss (W)
    temperature_rise: float = 0.0  # Temperature rise (°C)


@dataclass
class PhaseLosses:
    """Losses for a single phase of multi-phase converter"""
    phase_id: int  # Phase number (0, 1, 2, ...)

    # Primary side MOSFETs (4 switches in full-bridge)
    mosfet_q1: MOSFETLosses  # Leading leg, high-side
    mosfet_q2: MOSFETLosses  # Leading leg, low-side
    mosfet_q3: MOSFETLosses  # Lagging leg, high-side
    mosfet_q4: MOSFETLosses  # Lagging leg, low-side

    # Secondary side rectifier (4 diodes in full-bridge)
    diode_d1: DiodeLosses  # Positive rail, primary-side winding
    diode_d2: DiodeLosses  # Negative rail, primary-side winding
    diode_d3: DiodeLosses  # Positive rail, secondary-side winding
    diode_d4: DiodeLosses  # Negative rail, secondary-side winding

    # Magnetic components
    resonant_inductor_loss: float = 0.0  # Lr loss (W)
    transformer_loss: float = 0.0  # Transformer total loss (W)
    transformer_core_loss: float = 0.0  # Transformer core loss (W)
    transformer_copper_loss_pri: float = 0.0  # Transformer primary copper (W)
    transformer_copper_loss_sec: float = 0.0  # Transformer secondary copper (W)
    output_inductor_loss: float = 0.0  # Lo loss (W)

    # Total losses by category
    total_mosfet_loss: float = 0.0
    total_diode_loss: float = 0.0
    total_magnetic_loss: float = 0.0
    total_phase_loss: float = 0.0


@dataclass
class SystemLosses:
    """Complete system losses for multi-phase PSFB converter"""
    # Operating point
    input_voltage: float  # Input voltage (V)
    output_voltage: float  # Output voltage (V)
    output_current: float  # Total output current (A)
    output_power: float  # Output power (W)

    # Multi-phase configuration
    n_phases: int  # Number of phases
    phase_shift_deg: float  # Phase shift between channels (degrees)

    # Per-phase losses
    phase_losses: List[PhaseLosses] = field(default_factory=list)

    # Capacitor losses
    input_cap_losses: List[CapacitorLosses] = field(default_factory=list)
    output_cap_losses: List[CapacitorLosses] = field(default_factory=list)

    # Total losses by category (sum of all phases)
    total_mosfet_loss: float = 0.0
    total_diode_loss: float = 0.0
    total_magnetic_loss: float = 0.0
    total_capacitor_loss: float = 0.0
    total_loss: float = 0.0

    # Power flow
    input_power: float = 0.0
    efficiency: float = 0.0  # Efficiency (%)

    # Loss breakdown percentages
    mosfet_loss_percent: float = 0.0
    diode_loss_percent: float = 0.0
    magnetic_loss_percent: float = 0.0
    capacitor_loss_percent: float = 0.0


@dataclass
class MagneticComponents:
    """Magnetic component design results for system analysis"""
    resonant_inductor: Optional[MagneticDesignResult] = None
    transformer: Optional[MagneticDesignResult] = None
    output_inductor: Optional[MagneticDesignResult] = None


# ============================================================================
# Capacitor Loss Calculation
# ============================================================================

def calculate_capacitor_esr_loss(
    esr: float,
    current_rms: float,
    capacitor_id: str = "C_unknown",
) -> CapacitorLosses:
    """
    Calculate capacitor ESR loss.

    P_esr = I_rms² × ESR

    Args:
        esr: Equivalent series resistance (Ω)
        current_rms: RMS current through capacitor (A)
        capacitor_id: Capacitor identifier

    Returns:
        CapacitorLosses with calculated values
    """
    loss = current_rms**2 * esr

    # Estimate temperature rise (very approximate)
    # Assume ~5°C per watt for typical aluminum electrolytic
    temp_rise = loss * 5.0

    return CapacitorLosses(
        capacitor_id=capacitor_id,
        esr=esr,
        current_rms=current_rms,
        loss_total=loss,
        temperature_rise=temp_rise,
    )


def estimate_input_capacitor_current(
    input_current_avg: float,
    output_current: float,
    turns_ratio: float,
    duty_cycle: float,
    n_phases: int = 1,
) -> float:
    """
    Estimate RMS current in input capacitor for PSFB.

    Input capacitor supplies pulsed current during on-time.
    For multi-phase, current pulses are interleaved.

    Args:
        input_current_avg: Average input current (A)
        output_current: Total output current (A)
        turns_ratio: Transformer turns ratio n = Npri/Nsec
        duty_cycle: Duty cycle (0-1)
        n_phases: Number of interleaved phases

    Returns:
        Input capacitor RMS current (A)
    """
    # Reflected output current to primary
    i_pri_reflected = output_current / (turns_ratio * 2.0)

    # Input capacitor supplies difference between average and peak
    # For single phase: large ripple
    # For multi-phase: ripple cancellation reduces RMS

    if n_phases == 1:
        # Single phase: high ripple current
        i_cap_rms = i_pri_reflected * np.sqrt(duty_cycle * (1.0 - duty_cycle))
    elif n_phases == 2:
        # 2-phase: 50% ripple reduction
        i_cap_rms = i_pri_reflected * np.sqrt(duty_cycle * (1.0 - duty_cycle)) * 0.5
    elif n_phases >= 3:
        # 3+ phase: significant ripple cancellation
        i_cap_rms = i_pri_reflected * np.sqrt(duty_cycle * (1.0 - duty_cycle)) * 0.3
    else:
        i_cap_rms = input_current_avg * 0.5

    return i_cap_rms


def estimate_output_capacitor_current(
    output_current: float,
    current_ripple_pp: float,
    n_phases: int = 1,
    phase_shift_deg: float = 120.0,
) -> float:
    """
    Estimate RMS current in output capacitor.

    Output capacitor absorbs inductor ripple current.
    For multi-phase interleaving, ripple cancellation significantly
    reduces capacitor RMS current.

    Args:
        output_current: Total output current (A)
        current_ripple_pp: Peak-to-peak ripple per inductor (A)
        n_phases: Number of interleaved phases
        phase_shift_deg: Phase shift between channels (degrees)

    Returns:
        Output capacitor RMS current (A)
    """
    # Per-inductor ripple current RMS (triangular wave)
    i_ripple_rms_single = current_ripple_pp / np.sqrt(12)

    if n_phases == 1:
        # Single phase: capacitor sees full ripple
        i_cap_rms = i_ripple_rms_single
    elif n_phases == 2 and abs(phase_shift_deg - 180.0) < 10:
        # 2-phase @ 180°: excellent cancellation
        i_cap_rms = i_ripple_rms_single * 0.2
    elif n_phases == 3 and abs(phase_shift_deg - 120.0) < 10:
        # 3-phase @ 120°: very good cancellation
        i_cap_rms = i_ripple_rms_single * 0.15
    elif n_phases == 4 and abs(phase_shift_deg - 90.0) < 10:
        # 4-phase @ 90°: excellent cancellation
        i_cap_rms = i_ripple_rms_single * 0.1
    else:
        # Generic reduction
        i_cap_rms = i_ripple_rms_single / np.sqrt(n_phases)

    return i_cap_rms


# ============================================================================
# System-Level Loss Analysis
# ============================================================================

def analyze_psfb_phase(
    input_voltage: float,
    output_voltage: float,
    output_power_per_phase: float,
    frequency: float,
    duty_cycle: float,
    turns_ratio: float,
    primary_mosfet: MOSFETParameters,
    secondary_diode: DiodeParameters,
    magnetics: MagneticComponents,
    phase_id: int = 0,
    zvs_operation: bool = True,
    t_junction_mosfet: float = 100.0,
    t_junction_diode: float = 125.0,
) -> PhaseLosses:
    """
    Analyze losses for a single phase of PSFB converter.

    Args:
        input_voltage: Input voltage (V)
        output_voltage: Output voltage (V)
        output_power_per_phase: Output power for this phase (W)
        frequency: Switching frequency (Hz)
        duty_cycle: Duty cycle (0-1)
        turns_ratio: Transformer turns ratio n = Npri/Nsec
        primary_mosfet: Primary MOSFET parameters
        secondary_diode: Secondary diode parameters
        magnetics: Magnetic component designs
        phase_id: Phase identifier (0, 1, 2, ...)
        zvs_operation: True if ZVS operation, False for hard switching
        t_junction_mosfet: MOSFET junction temperature (°C)
        t_junction_diode: Diode junction temperature (°C)

    Returns:
        PhaseLosses with complete loss breakdown
    """
    # ========================================================================
    # Calculate Primary-Side MOSFET Losses
    # ========================================================================

    # Output current
    i_out = output_power_per_phase / output_voltage

    # Estimate primary-side current waveform
    from .mosfet_losses import estimate_psfb_primary_waveform

    primary_waveform = estimate_psfb_primary_waveform(
        v_in=input_voltage,
        p_out=output_power_per_phase,
        efficiency=0.96,  # Estimate
        duty_cycle=duty_cycle,
    )

    # Q1 and Q2 (leading leg) - see full conduction current
    # Q3 and Q4 (lagging leg) - see reduced conduction due to phase shift

    # For simplicity, assume all MOSFETs see similar current
    # (More detailed analysis would account for phase shift effects)

    mosfet_q1 = calculate_mosfet_losses(
        mosfet=primary_mosfet,
        waveform=primary_waveform,
        v_ds_off=input_voltage,
        frequency=frequency,
        zvs_operation=zvs_operation,
        t_junction=t_junction_mosfet,
        gate_drive_voltage=15.0,
    )

    # Q2 shares similar losses with Q1 (same leg)
    mosfet_q2 = mosfet_q1

    # Q3 and Q4 (lagging leg) have similar losses
    # In real design, lagging leg may have slightly different switching losses
    mosfet_q3 = mosfet_q1
    mosfet_q4 = mosfet_q1

    # ========================================================================
    # Calculate Secondary-Side Diode Losses
    # ========================================================================

    # Estimate secondary diode current waveform
    from .diode_losses import estimate_fullbridge_diode_waveform

    diode_waveform = estimate_fullbridge_diode_waveform(
        iout=i_out,
        duty_cycle=duty_cycle,
    )

    # All four diodes see similar currents in full-bridge rectifier
    diode_d1 = calculate_diode_losses(
        diode=secondary_diode,
        waveform=diode_waveform,
        v_reverse=output_voltage * 1.5,  # Reverse voltage stress
        frequency=frequency,
        t_junction=t_junction_diode,
    )

    diode_d2 = diode_d1
    diode_d3 = diode_d1
    diode_d4 = diode_d1

    # ========================================================================
    # Magnetic Component Losses
    # ========================================================================

    lr_loss = magnetics.resonant_inductor.total_loss if magnetics.resonant_inductor else 0.0
    xfmr_loss = magnetics.transformer.total_loss if magnetics.transformer else 0.0
    xfmr_core = magnetics.transformer.core_loss if magnetics.transformer else 0.0
    xfmr_cu_pri = magnetics.transformer.copper_loss_primary if magnetics.transformer else 0.0
    xfmr_cu_sec = magnetics.transformer.copper_loss_secondary if magnetics.transformer else 0.0
    lo_loss = magnetics.output_inductor.total_loss if magnetics.output_inductor else 0.0

    # ========================================================================
    # Totals
    # ========================================================================

    total_mosfet = (mosfet_q1.total_loss + mosfet_q2.total_loss +
                    mosfet_q3.total_loss + mosfet_q4.total_loss)
    total_diode = (diode_d1.total_loss + diode_d2.total_loss +
                   diode_d3.total_loss + diode_d4.total_loss)
    total_magnetic = lr_loss + xfmr_loss + lo_loss
    total_phase = total_mosfet + total_diode + total_magnetic

    return PhaseLosses(
        phase_id=phase_id,
        mosfet_q1=mosfet_q1,
        mosfet_q2=mosfet_q2,
        mosfet_q3=mosfet_q3,
        mosfet_q4=mosfet_q4,
        diode_d1=diode_d1,
        diode_d2=diode_d2,
        diode_d3=diode_d3,
        diode_d4=diode_d4,
        resonant_inductor_loss=lr_loss,
        transformer_loss=xfmr_loss,
        transformer_core_loss=xfmr_core,
        transformer_copper_loss_pri=xfmr_cu_pri,
        transformer_copper_loss_sec=xfmr_cu_sec,
        output_inductor_loss=lo_loss,
        total_mosfet_loss=total_mosfet,
        total_diode_loss=total_diode,
        total_magnetic_loss=total_magnetic,
        total_phase_loss=total_phase,
    )


def analyze_psfb_system(
    input_voltage: float,
    output_voltage: float,
    output_power: float,
    frequency: float,
    duty_cycle: float,
    turns_ratio: float,
    n_phases: int,
    phase_shift_deg: float,
    primary_mosfet: MOSFETParameters,
    secondary_diode: DiodeParameters,
    magnetics: MagneticComponents,
    input_capacitor: Optional[CapacitorParameters] = None,
    output_capacitor: Optional[CapacitorParameters] = None,
    zvs_operation: bool = True,
    t_junction_mosfet: float = 100.0,
    t_junction_diode: float = 125.0,
    output_inductor_ripple_pp: float = 2.5,  # A, per phase
) -> SystemLosses:
    """
    Complete system-level loss analysis for multi-phase PSFB converter.

    Args:
        input_voltage: Input voltage (V)
        output_voltage: Output voltage (V)
        output_power: Total output power (W)
        frequency: Switching frequency (Hz)
        duty_cycle: Duty cycle (0-1)
        turns_ratio: Transformer turns ratio n = Npri/Nsec
        n_phases: Number of interleaved phases
        phase_shift_deg: Phase shift between consecutive phases (degrees)
        primary_mosfet: Primary MOSFET parameters
        secondary_diode: Secondary diode parameters
        magnetics: Magnetic component designs (per phase)
        input_capacitor: Input capacitor parameters (optional)
        output_capacitor: Output capacitor parameters (optional)
        zvs_operation: ZVS operation flag
        t_junction_mosfet: MOSFET junction temperature (°C)
        t_junction_diode: Diode junction temperature (°C)
        output_inductor_ripple_pp: Output inductor ripple current per phase (A)

    Returns:
        SystemLosses with complete breakdown
    """
    # Output current
    i_out_total = output_power / output_voltage

    # Power per phase
    power_per_phase = output_power / n_phases

    # ========================================================================
    # Analyze Each Phase
    # ========================================================================

    phase_losses_list = []

    for phase_id in range(n_phases):
        phase_loss = analyze_psfb_phase(
            input_voltage=input_voltage,
            output_voltage=output_voltage,
            output_power_per_phase=power_per_phase,
            frequency=frequency,
            duty_cycle=duty_cycle,
            turns_ratio=turns_ratio,
            primary_mosfet=primary_mosfet,
            secondary_diode=secondary_diode,
            magnetics=magnetics,
            phase_id=phase_id,
            zvs_operation=zvs_operation,
            t_junction_mosfet=t_junction_mosfet,
            t_junction_diode=t_junction_diode,
        )
        phase_losses_list.append(phase_loss)

    # ========================================================================
    # Calculate Capacitor Losses
    # ========================================================================

    input_cap_losses_list = []
    output_cap_losses_list = []
    total_cap_loss = 0.0

    if input_capacitor:
        i_avg_input = output_power / input_voltage  # Average input current
        i_cap_in_rms = estimate_input_capacitor_current(
            i_avg_input,
            i_out_total,
            turns_ratio,
            duty_cycle,
            n_phases,
        )

        cap_loss_in = calculate_capacitor_esr_loss(
            input_capacitor.esr,
            i_cap_in_rms,
            "C_input",
        )
        input_cap_losses_list.append(cap_loss_in)
        total_cap_loss += cap_loss_in.loss_total

    if output_capacitor:
        i_cap_out_rms = estimate_output_capacitor_current(
            i_out_total,
            output_inductor_ripple_pp,
            n_phases,
            phase_shift_deg,
        )

        cap_loss_out = calculate_capacitor_esr_loss(
            output_capacitor.esr,
            i_cap_out_rms,
            "C_output",
        )
        output_cap_losses_list.append(cap_loss_out)
        total_cap_loss += cap_loss_out.loss_total

    # ========================================================================
    # Calculate System Totals
    # ========================================================================

    total_mosfet = sum(p.total_mosfet_loss for p in phase_losses_list)
    total_diode = sum(p.total_diode_loss for p in phase_losses_list)
    total_magnetic = sum(p.total_magnetic_loss for p in phase_losses_list)
    total_loss = total_mosfet + total_diode + total_magnetic + total_cap_loss

    input_power = output_power + total_loss
    efficiency = 100.0 * output_power / input_power if input_power > 0 else 0.0

    # Loss percentages (of output power)
    mosfet_pct = 100.0 * total_mosfet / output_power if output_power > 0 else 0.0
    diode_pct = 100.0 * total_diode / output_power if output_power > 0 else 0.0
    magnetic_pct = 100.0 * total_magnetic / output_power if output_power > 0 else 0.0
    cap_pct = 100.0 * total_cap_loss / output_power if output_power > 0 else 0.0

    return SystemLosses(
        input_voltage=input_voltage,
        output_voltage=output_voltage,
        output_current=i_out_total,
        output_power=output_power,
        n_phases=n_phases,
        phase_shift_deg=phase_shift_deg,
        phase_losses=phase_losses_list,
        input_cap_losses=input_cap_losses_list,
        output_cap_losses=output_cap_losses_list,
        total_mosfet_loss=total_mosfet,
        total_diode_loss=total_diode,
        total_magnetic_loss=total_magnetic,
        total_capacitor_loss=total_cap_loss,
        total_loss=total_loss,
        input_power=input_power,
        efficiency=efficiency,
        mosfet_loss_percent=mosfet_pct,
        diode_loss_percent=diode_pct,
        magnetic_loss_percent=magnetic_pct,
        capacitor_loss_percent=cap_pct,
    )


def print_system_loss_report(system: SystemLosses, detailed: bool = True):
    """
    Print formatted system loss report.

    Args:
        system: SystemLosses object
        detailed: Include detailed per-phase breakdown
    """
    print("=" * 80)
    print("PSFB CONVERTER SYSTEM LOSS ANALYSIS")
    print("=" * 80)
    print()
    print(f"Operating Point:")
    print(f"  Input Voltage:       {system.input_voltage:.1f} V")
    print(f"  Output Voltage:      {system.output_voltage:.1f} V")
    print(f"  Output Current:      {system.output_current:.2f} A")
    print(f"  Output Power:        {system.output_power:.1f} W")
    print()
    print(f"Configuration:")
    print(f"  Number of Phases:    {system.n_phases}")
    print(f"  Phase Shift:         {system.phase_shift_deg:.0f}°")
    print(f"  Power per Phase:     {system.output_power / system.n_phases:.1f} W")
    print()

    print("=" * 80)
    print("TOTAL SYSTEM LOSSES")
    print("=" * 80)
    print()
    print(f"{'Loss Category':<30} {'Total (W)':<12} {'% of Pout':<12} {'Per Phase (W)':<12}")
    print("-" * 80)
    print(f"{'Primary MOSFETs':<30} {system.total_mosfet_loss:>10.2f} W  {system.mosfet_loss_percent:>10.2f} %  {system.total_mosfet_loss/system.n_phases:>10.2f} W")
    print(f"{'Secondary Diodes':<30} {system.total_diode_loss:>10.2f} W  {system.diode_loss_percent:>10.2f} %  {system.total_diode_loss/system.n_phases:>10.2f} W")
    print(f"{'Magnetic Components':<30} {system.total_magnetic_loss:>10.2f} W  {system.magnetic_loss_percent:>10.2f} %  {system.total_magnetic_loss/system.n_phases:>10.2f} W")
    print(f"{'Capacitor ESR':<30} {system.total_capacitor_loss:>10.2f} W  {system.capacitor_loss_percent:>10.2f} %  {system.total_capacitor_loss:>10.2f} W")
    print("-" * 80)
    print(f"{'TOTAL LOSS':<30} {system.total_loss:>10.2f} W  {100.0 * system.total_loss / system.output_power:>10.2f} %")
    print()
    print(f"{'Input Power':<30} {system.input_power:>10.2f} W")
    print(f"{'Output Power':<30} {system.output_power:>10.2f} W")
    print(f"{'EFFICIENCY':<30} {system.efficiency:>10.2f} %")
    print()

    if detailed and system.n_phases > 1:
        print("=" * 80)
        print("PER-PHASE LOSS BREAKDOWN")
        print("=" * 80)

        for phase in system.phase_losses:
            print()
            print(f"Phase {phase.phase_id}:")
            print(f"  MOSFETs (Q1-Q4):     {phase.total_mosfet_loss:.2f} W")
            print(f"  Diodes (D1-D4):      {phase.total_diode_loss:.2f} W")
            print(f"  Resonant Inductor:   {phase.resonant_inductor_loss:.2f} W")
            print(f"  Transformer:         {phase.transformer_loss:.2f} W")
            print(f"    - Core loss:       {phase.transformer_core_loss:.2f} W")
            print(f"    - Primary Cu:      {phase.transformer_copper_loss_pri:.2f} W")
            print(f"    - Secondary Cu:    {phase.transformer_copper_loss_sec:.2f} W")
            print(f"  Output Inductor:     {phase.output_inductor_loss:.2f} W")
            print(f"  Phase Total:         {phase.total_phase_loss:.2f} W")

    print()
    print("=" * 80)


# ============================================================================
# Module Information
# ============================================================================

if __name__ == "__main__":
    print("PSFB Loss Analyzer - System Integration Module")
    print("=" * 80)
    print()
    print("This module integrates all loss sources for complete system analysis:")
    print("  - Primary-side MOSFET losses")
    print("  - Secondary-side rectifier losses")
    print("  - Magnetic component losses")
    print("  - Capacitor ESR losses")
    print("  - Multi-phase interleaved operation")
    print()
    print("Use analyze_psfb_system() for complete loss analysis.")
    print()

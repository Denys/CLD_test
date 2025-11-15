"""
Diode Loss Calculation Module

Implements rectifier diode power loss calculations for PSFB secondary side.
Supports both Si PN diodes and SiC Schottky diodes.

Loss Components:
- Forward conduction loss (dominant)
- Reverse recovery loss (Si PN diodes only)
- Temperature-dependent forward voltage

Reference Equations:
- Conduction loss: P_F = V_F0 × I_F_avg + R_D × I²_F_rms  [Standard diode model]
- Recovery energy:  E_rr = ¼ × Q_rr × U_Drr  [Infineon AN, Page 4]
- Recovery power:   P_rr = E_rr × f_sw

Diode Types:
- Si PN Diode: V_F = V_F0 + R_D × I_F (with threshold voltage V_F0)
- SiC Schottky:  V_F = R_D × I_F (no threshold, purely resistive)

Author: PSFB Loss Analysis Tool
Reference: Infineon AN "MOSFET Power Losses..." + Standard Diode Equations
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional
from .circuit_params import DiodeParameters


@dataclass
class DiodeCurrentWaveform:
    """
    Diode current waveform characteristics

    Attributes:
        i_avg: Average forward current (A)
        i_rms: RMS forward current (A)
        i_peak: Peak forward current (A)
        duty_cycle: Conduction duty cycle (0-1)
    """
    i_avg: float
    i_rms: float
    i_peak: float
    duty_cycle: float


@dataclass
class DiodeLosses:
    """
    Complete diode loss breakdown

    Attributes:
        p_forward: Forward conduction loss (W)
        p_recovery: Reverse recovery loss (W)
        p_total: Total diode loss (W)
        v_f_avg: Average forward voltage drop (V)
        t_junction: Calculated junction temperature (°C) - optional
    """
    p_forward: float
    p_recovery: float
    p_total: float
    v_f_avg: float
    t_junction: Optional[float] = None


# =============================================================================
# FORWARD VOLTAGE DROP CALCULATION
# =============================================================================

def calculate_forward_voltage(
    diode: DiodeParameters,
    i_forward: float,
    t_junction: float = 125.0
) -> float:
    """
    Calculate diode forward voltage drop at specified current and temperature

    Two models supported:
    1. Si PN Diode:    V_F = V_F0 + R_D × I_F
    2. SiC Schottky:   V_F = R_D × I_F  (V_F0 = 0)

    Temperature dependence (simplified):
    - Si PN:      V_F0 decreases ~2mV/°C
    - SiC Schottky: R_D increases slightly with temperature

    Args:
        diode: Diode parameters
        i_forward: Forward current (A)
        t_junction: Junction temperature (°C)

    Returns:
        Forward voltage drop in Volts

    Note:
        For accurate temperature compensation, use datasheet V_F curves.
        This implementation uses simplified linear model.
    """
    # Base forward voltage at 25°C
    v_f0_base = diode.v_f0  # Threshold voltage (0 for SiC Schottky)
    r_d = diode.r_d  # Dynamic resistance

    # Temperature compensation (simplified)
    # Si PN: V_F0 decreases with temperature (~-2mV/°C)
    # SiC Schottky: Minimal temperature dependence
    if v_f0_base > 0:  # Si PN diode
        temp_coeff = -2e-3  # -2 mV/°C for Si PN junction
        v_f0_tj = v_f0_base + temp_coeff * (t_junction - 25)
    else:  # SiC Schottky
        v_f0_tj = 0.0

    # Forward voltage: V_F = V_F0(Tj) + R_D × I_F
    v_f = v_f0_tj + r_d * i_forward

    return v_f


# =============================================================================
# FORWARD CONDUCTION LOSS CALCULATION
# =============================================================================

def calculate_forward_conduction_loss(
    diode: DiodeParameters,
    i_avg: float,
    i_rms: float,
    t_junction: float = 125.0
) -> tuple[float, float]:
    """
    Calculate diode forward conduction loss

    Two-component model:
    P_F = V_F0 × I_F_avg + R_D × I²_F_rms

    This separates:
    - Constant voltage drop loss: V_F0 × I_avg
    - Resistive loss: R_D × I²_rms

    Args:
        diode: Diode parameters
        i_avg: Average forward current (A)
        i_rms: RMS forward current (A)
        t_junction: Junction temperature (°C)

    Returns:
        Tuple of (P_forward, V_F_avg) in Watts and Volts

    Reference:
        Standard diode conduction loss equation
    """
    # Get temperature-compensated V_F0
    v_f0_tj = diode.v_f0
    if v_f0_tj > 0:  # Si PN diode temperature compensation
        temp_coeff = -2e-3  # -2 mV/°C
        v_f0_tj = v_f0_tj + temp_coeff * (t_junction - 25)

    # Forward conduction loss components
    # P_F = V_F0 × I_avg + R_D × I²_rms
    p_threshold = v_f0_tj * i_avg  # Constant voltage drop component
    p_resistive = diode.r_d * i_rms**2  # Resistive component

    p_forward = p_threshold + p_resistive

    # Calculate average forward voltage for reference
    # V_F_avg ≈ V_F0 + R_D × I_avg
    v_f_avg = v_f0_tj + diode.r_d * i_avg

    return p_forward, v_f_avg


# =============================================================================
# REVERSE RECOVERY LOSS CALCULATION
# Reference: Infineon AN Equation (Page 4, Diode section)
# =============================================================================

def calculate_reverse_recovery_loss(
    diode: DiodeParameters,
    v_reverse: float,
    f_sw: float
) -> float:
    """
    Calculate diode reverse recovery loss

    Reverse recovery occurs when diode turns off and must remove
    stored charge before blocking voltage.

    Energy per recovery event:
    E_rr = ¼ × Q_rr × U_Drr

    Power loss:
    P_rr = E_rr × f_sw

    Args:
        diode: Diode parameters
        v_reverse: Reverse voltage during recovery (V)
        f_sw: Switching frequency (Hz)

    Returns:
        Reverse recovery power loss in Watts

    Note:
        - Si PN diodes: Q_rr typically 50-500 nC (significant loss)
        - SiC Schottky: Q_rr ≈ 0 (negligible loss)

    Reference:
        Infineon AN "MOSFET Power Losses...", Page 4
    """
    # Recovery energy per event: E_rr = ¼ × Q_rr × V_reverse
    e_rr = 0.25 * diode.q_rr * v_reverse

    # Power loss: P_rr = E_rr × f_sw
    p_recovery = e_rr * f_sw

    return p_recovery


# =============================================================================
# COMPLETE DIODE LOSS CALCULATION
# =============================================================================

def calculate_diode_losses(
    diode: DiodeParameters,
    waveform: DiodeCurrentWaveform,
    v_reverse: float,
    f_sw: float,
    t_junction: float = 125.0
) -> DiodeLosses:
    """
    Calculate complete diode loss breakdown

    Combines:
    - Forward conduction loss (dominant for most diodes)
    - Reverse recovery loss (significant for Si PN, negligible for SiC)

    Args:
        diode: Diode parameters
        waveform: Current waveform characteristics
        v_reverse: Reverse blocking voltage (V)
        f_sw: Switching frequency (Hz)
        t_junction: Junction temperature for V_F calculation (°C)

    Returns:
        DiodeLosses object with complete loss breakdown

    Example:
        >>> diode = DiodeParameters(...)
        >>> waveform = DiodeCurrentWaveform(i_avg=10.0, i_rms=12.0, i_peak=25.0, duty_cycle=0.5)
        >>> losses = calculate_diode_losses(diode, waveform, v_reverse=400.0, f_sw=100e3)
        >>> print(f"Total loss: {losses.p_total:.2f} W")
    """
    # 1. Forward conduction loss
    p_forward, v_f_avg = calculate_forward_conduction_loss(
        diode=diode,
        i_avg=waveform.i_avg,
        i_rms=waveform.i_rms,
        t_junction=t_junction
    )

    # 2. Reverse recovery loss
    p_recovery = calculate_reverse_recovery_loss(
        diode=diode,
        v_reverse=v_reverse,
        f_sw=f_sw
    )

    # 3. Total loss
    p_total = p_forward + p_recovery

    return DiodeLosses(
        p_forward=p_forward,
        p_recovery=p_recovery,
        p_total=p_total,
        v_f_avg=v_f_avg,
        t_junction=t_junction
    )


# =============================================================================
# FULL-BRIDGE RECTIFIER CURRENT WAVEFORM ESTIMATION
# =============================================================================

def estimate_fullbridge_diode_waveform(
    i_out_dc: float,
    duty_cycle: float = 0.5
) -> DiodeCurrentWaveform:
    """
    Estimate diode current waveform for full-bridge rectifier

    In a full-bridge rectifier:
    - Each diode conducts for half the output cycle
    - Two diodes conduct simultaneously (one from each leg)
    - Current waveform depends on output filter inductance

    Args:
        i_out_dc: DC output current (A)
        duty_cycle: Effective conduction duty cycle (default 0.5)

    Returns:
        DiodeCurrentWaveform with estimated values

    Note:
        For continuous conduction mode (CCM) with large output inductor:
        - Each diode average current ≈ I_out / 2
        - Each diode RMS current ≈ I_out / √2
        - Peak current depends on ripple (assumed 20% ripple)
    """
    # Full-bridge: each diode conducts for duty_cycle of period
    # Two diodes in series conduct simultaneously

    # Average current per diode (duty-cycle weighted)
    i_avg = i_out_dc * duty_cycle / 2  # Divided by 2 (two legs)

    # RMS current (assuming continuous conduction)
    # For square wave: I_rms = I_avg / √duty_cycle
    i_rms = i_out_dc * np.sqrt(duty_cycle) / 2

    # Peak current (assume 20% current ripple)
    ripple_factor = 1.2
    i_peak = i_out_dc * ripple_factor

    return DiodeCurrentWaveform(
        i_avg=i_avg,
        i_rms=i_rms,
        i_peak=i_peak,
        duty_cycle=duty_cycle
    )


def estimate_centertap_diode_waveform(
    i_out_dc: float,
    duty_cycle: float = 0.5
) -> DiodeCurrentWaveform:
    """
    Estimate diode current waveform for center-tap rectifier

    In a center-tap rectifier:
    - Each diode conducts for half the switching period
    - Only one diode conducts at a time (alternating)
    - Full output current flows through one diode

    Args:
        i_out_dc: DC output current (A)
        duty_cycle: Effective conduction duty cycle (default 0.5)

    Returns:
        DiodeCurrentWaveform with estimated values

    Note:
        For center-tap:
        - Each diode average current ≈ I_out / 2
        - Each diode RMS current ≈ I_out / √2
        - Higher current stress than full-bridge
    """
    # Center-tap: each diode conducts for half period
    # Full current flows through one diode at a time

    # Average current per diode
    i_avg = i_out_dc * duty_cycle

    # RMS current
    i_rms = i_out_dc * np.sqrt(duty_cycle)

    # Peak current (assume 20% ripple)
    ripple_factor = 1.2
    i_peak = i_out_dc * ripple_factor

    return DiodeCurrentWaveform(
        i_avg=i_avg,
        i_rms=i_rms,
        i_peak=i_peak,
        duty_cycle=duty_cycle
    )


# =============================================================================
# DIODE SELECTION VERIFICATION
# =============================================================================

def verify_diode_ratings(
    diode: DiodeParameters,
    waveform: DiodeCurrentWaveform,
    v_reverse_max: float,
    t_junction_max: float = 125.0
) -> list[str]:
    """
    Verify diode is properly rated for application

    Checks:
    - Reverse voltage rating vs maximum blocking voltage
    - Average current rating vs actual average current
    - Junction temperature vs rating

    Args:
        diode: Diode parameters
        waveform: Actual current waveform
        v_reverse_max: Maximum reverse voltage (V)
        t_junction_max: Maximum expected junction temperature (°C)

    Returns:
        List of warning messages (empty if all checks pass)
    """
    warnings = []

    # Voltage rating check (20% margin recommended)
    if v_reverse_max > 0.8 * diode.v_rrm:
        warnings.append(
            f"Reverse voltage ({v_reverse_max:.0f}V) exceeds 80% of "
            f"diode rating ({diode.v_rrm:.0f}V). Recommend 20% margin."
        )

    # Average current rating check
    if waveform.i_avg > diode.i_f_avg:
        warnings.append(
            f"Average current ({waveform.i_avg:.1f}A) exceeds "
            f"diode rating ({diode.i_f_avg:.1f}A)."
        )

    # Junction temperature check
    if t_junction_max > diode.t_j_max:
        warnings.append(
            f"Junction temperature ({t_junction_max:.0f}°C) exceeds "
            f"diode rating ({diode.t_j_max:.0f}°C)."
        )

    return warnings


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    try:
        from circuit_params import DiodeParameters
    except ImportError:
        from .circuit_params import DiodeParameters

    print("="*70)
    print("DIODE LOSS CALCULATION - EXAMPLES")
    print("="*70)

    # =============================================================================
    # Example 1: SiC Schottky Diode (from 6.6kW marine example)
    # Wolfspeed C4D30120A (1200V, 31A SiC Schottky)
    # =============================================================================
    print("\n" + "="*70)
    print("EXAMPLE 1: SiC SCHOTTKY DIODE (Wolfspeed C4D30120A)")
    print("="*70)

    sic_diode = DiodeParameters(
        part_number="C4D30120A",
        v_rrm=1200.0,
        i_f_avg=31.0,
        v_f0=0.0,  # SiC Schottky: no threshold voltage
        r_d=35e-3,  # 35mΩ dynamic resistance
        q_rr=0.0,  # SiC Schottky: negligible reverse recovery
        t_rr=0.0,
        r_th_jc=1.2,
        t_j_max=175.0
    )

    # Full-bridge rectifier, 6600W @ 250V output
    i_out = 6600 / 250  # 26.4A output current
    waveform_sic = estimate_fullbridge_diode_waveform(i_out, duty_cycle=0.5)

    print(f"\nDiode: {sic_diode.part_number}")
    print(f"  Type:              SiC Schottky (no threshold voltage)")
    print(f"  V_RRM:             {sic_diode.v_rrm} V")
    print(f"  I_F(avg) rating:   {sic_diode.i_f_avg} A")
    print(f"  R_D:               {sic_diode.r_d*1e3:.1f} mΩ")
    print(f"  Q_rr:              {sic_diode.q_rr*1e9:.1f} nC (zero for SiC)")

    print(f"\nCurrent Waveform (Full-Bridge, {i_out:.1f}A output):")
    print(f"  I_avg per diode:   {waveform_sic.i_avg:.2f} A")
    print(f"  I_RMS per diode:   {waveform_sic.i_rms:.2f} A")
    print(f"  I_peak:            {waveform_sic.i_peak:.2f} A")
    print(f"  Duty cycle:        {waveform_sic.duty_cycle:.2f}")

    # Calculate losses
    losses_sic = calculate_diode_losses(
        diode=sic_diode,
        waveform=waveform_sic,
        v_reverse=400.0,  # Reflected primary voltage
        f_sw=100e3,
        t_junction=125.0
    )

    print(f"\nLoss Breakdown @ Tj=125°C:")
    print(f"  Forward conduction:  {losses_sic.p_forward:.3f} W")
    print(f"  Reverse recovery:    {losses_sic.p_recovery:.3f} W (SiC: zero)")
    print(f"  TOTAL per diode:     {losses_sic.p_total:.3f} W")
    print(f"  Average V_F:         {losses_sic.v_f_avg:.3f} V")

    # Total for 4 diodes in full-bridge
    print(f"\nFull-Bridge Total (4 diodes): {losses_sic.p_total * 4:.2f} W")

    # Verify ratings
    warnings = verify_diode_ratings(sic_diode, waveform_sic, v_reverse_max=400.0)
    if warnings:
        print("\n⚠ Warnings:")
        for w in warnings:
            print(f"  - {w}")
    else:
        print("\n✓ All ratings verified OK")

    # =============================================================================
    # Example 2: Si PN Diode (for comparison)
    # Typical fast recovery diode
    # =============================================================================
    print("\n" + "="*70)
    print("EXAMPLE 2: Si PN FAST RECOVERY DIODE (for comparison)")
    print("="*70)

    si_diode = DiodeParameters(
        part_number="VS-30EPS16-N3",  # Example Si fast recovery
        v_rrm=1600.0,
        i_f_avg=30.0,
        v_f0=0.9,  # Si PN: has threshold voltage
        r_d=18e-3,  # 18mΩ dynamic resistance
        q_rr=250e-9,  # 250nC reverse recovery (significant!)
        t_rr=50e-9,
        r_th_jc=1.5,
        t_j_max=175.0
    )

    # Same operating conditions
    waveform_si = estimate_fullbridge_diode_waveform(i_out, duty_cycle=0.5)

    print(f"\nDiode: {si_diode.part_number}")
    print(f"  Type:              Si PN Fast Recovery")
    print(f"  V_F0:              {si_diode.v_f0} V (threshold)")
    print(f"  R_D:               {si_diode.r_d*1e3:.1f} mΩ")
    print(f"  Q_rr:              {si_diode.q_rr*1e9:.0f} nC (significant!)")

    # Calculate losses
    losses_si = calculate_diode_losses(
        diode=si_diode,
        waveform=waveform_si,
        v_reverse=400.0,
        f_sw=100e3,
        t_junction=125.0
    )

    print(f"\nLoss Breakdown @ Tj=125°C:")
    print(f"  Forward conduction:  {losses_si.p_forward:.3f} W")
    print(f"  Reverse recovery:    {losses_si.p_recovery:.3f} W (Si: significant)")
    print(f"  TOTAL per diode:     {losses_si.p_total:.3f} W")
    print(f"  Average V_F:         {losses_si.v_f_avg:.3f} V")

    print(f"\nFull-Bridge Total (4 diodes): {losses_si.p_total * 4:.2f} W")

    # =============================================================================
    # Comparison
    # =============================================================================
    print("\n" + "="*70)
    print("SiC SCHOTTKY vs Si PN DIODE COMPARISON")
    print("="*70)

    print(f"\nPer-diode losses:")
    print(f"  SiC Schottky:      {losses_sic.p_total:.3f} W")
    print(f"  Si PN:             {losses_si.p_total:.3f} W")
    print(f"  Difference:        {losses_si.p_total - losses_sic.p_total:.3f} W")
    print(f"  SiC advantage:     {(1 - losses_sic.p_total/losses_si.p_total)*100:.1f}% lower loss")

    print(f"\nFull-bridge (4 diodes):")
    print(f"  SiC Schottky:      {losses_sic.p_total * 4:.2f} W")
    print(f"  Si PN:             {losses_si.p_total * 4:.2f} W")
    print(f"  Power savings:     {(losses_si.p_total - losses_sic.p_total) * 4:.2f} W")

    print(f"\nKey benefits of SiC Schottky:")
    print(f"  ✓ No threshold voltage (V_F0 = 0)")
    print(f"  ✓ Zero reverse recovery (Q_rr ≈ 0)")
    print(f"  ✓ Lower forward voltage at high current")
    print(f"  ✓ Higher temperature capability (175°C)")

    print("\n" + "="*70)

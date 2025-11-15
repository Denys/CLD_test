"""
MOSFET Loss Calculation Module

Implements MOSFET power loss calculations based on Infineon Application Note:
"MOSFET Power Losses Calculation Using the DataSheet Parameters" (2006)

This module calculates:
- Conduction losses with temperature-dependent RDS(on)
- Switching losses (turn-on and turn-off)
- Gate drive losses
- ZVS capacitive losses
- Miller time calculations

Reference Equations:
- Conduction loss: P_cond = R_DS(on)(Tj) × I²_rms  [Infineon AN Eq. 1]
- RDS(on) temp:    R_DS(on)(Tj) = R_DS(on)_max(25°C) × [1 + α/100 × (Tj - 25)]  [Eq. 3]
- Turn-on energy:  E_on = V_DS × I_D × (t_ri + t_fu)/2 + Q_rr × V_DS  [Eq. 7]
- Turn-off energy: E_off = V_DS × I_D × (t_ru + t_fi)/2  [Eq. 8]
- Gate drive loss: P_gate = Q_g × V_GS × f_sw  [Eq. 14]

Author: PSFB Loss Analysis Tool
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple
from circuit_params import MOSFETParameters


@dataclass
class MOSFETCurrentWaveform:
    """
    MOSFET current waveform characteristics

    Attributes:
        i_rms: RMS current through MOSFET (A)
        i_avg: Average current through MOSFET (A)
        i_peak: Peak current through MOSFET (A)
        duty_cycle: Effective duty cycle (0-1)
    """
    i_rms: float
    i_avg: float
    i_peak: float
    duty_cycle: float


@dataclass
class MOSFETLosses:
    """
    Complete MOSFET loss breakdown

    Attributes:
        p_cond: Conduction loss (W)
        p_sw_on: Turn-on switching loss (W)
        p_sw_off: Turn-off switching loss (W)
        p_sw_total: Total switching loss (W)
        p_gate: Gate drive loss (W)
        p_total: Total MOSFET loss (W)
        t_junction: Calculated junction temperature (°C) - optional
    """
    p_cond: float
    p_sw_on: float
    p_sw_off: float
    p_sw_total: float
    p_gate: float
    p_total: float
    t_junction: Optional[float] = None


# =============================================================================
# TEMPERATURE-DEPENDENT RDS(ON) CALCULATION
# Reference: Infineon AN Equation 3, Page 5
# =============================================================================

def calculate_rdson_at_temp(
    mosfet: MOSFETParameters,
    t_junction: float,
    use_max: bool = True
) -> float:
    """
    Calculate RDS(on) at specified junction temperature

    Implements Infineon AN Equation 3:
    R_DS(on)(Tj) = R_DS(on)_max(25°C) × [1 + α/100 × (Tj - 25)]

    Args:
        mosfet: MOSFET parameters
        t_junction: Junction temperature in °C
        use_max: If True, use maximum RDS(on) values; if False, use typical

    Returns:
        RDS(on) at specified junction temperature (Ω)

    Reference:
        Infineon AN "MOSFET Power Losses...", Equation 3, Page 5
    """
    # Get base RDS(on) at 25°C
    if use_max:
        r_dson_25c = mosfet.r_dson_25c_max
    else:
        r_dson_25c = mosfet.r_dson_25c

    # Calculate using temperature coefficient
    alpha = mosfet.alpha_rdson  # Temperature coefficient in %/°C

    # Equation 3: R_DS(on)(Tj) = R_DS(on)(25°C) × [1 + α/100 × (Tj - 25)]
    r_dson_tj = r_dson_25c * (1 + alpha / 100 * (t_junction - 25))

    return r_dson_tj


# =============================================================================
# CONDUCTION LOSS CALCULATION
# Reference: Infineon AN Equation 1, Page 4
# =============================================================================

def calculate_conduction_loss(
    mosfet: MOSFETParameters,
    i_rms: float,
    t_junction: float,
    use_max: bool = True
) -> float:
    """
    Calculate MOSFET conduction loss

    Implements Infineon AN Equation 1:
    P_cond = R_DS(on)(Tj) × I²_rms

    Args:
        mosfet: MOSFET parameters
        i_rms: RMS current through MOSFET (A)
        t_junction: Junction temperature (°C)
        use_max: If True, use maximum RDS(on); if False, use typical

    Returns:
        Conduction loss in Watts

    Reference:
        Infineon AN "MOSFET Power Losses...", Equation 1, Page 4
    """
    # Get temperature-dependent RDS(on)
    r_dson = calculate_rdson_at_temp(mosfet, t_junction, use_max)

    # Equation 1: P_cond = R_DS(on) × I²_rms
    p_cond = r_dson * i_rms**2

    return p_cond


# =============================================================================
# MILLER TIME CALCULATION
# Reference: Infineon AN Pages 8-9, Two-Point Capacitance Method
# =============================================================================

def calculate_miller_time(
    mosfet: MOSFETParameters,
    v_ds: float,
    v_gs_drive: float,
    i_load: float,
    r_g_total: float
) -> Tuple[float, float]:
    """
    Calculate Miller plateau times for turn-on and turn-off

    Uses two-point capacitance approximation from Infineon AN Pages 8-9.
    The Miller plateau time is when V_DS changes while V_GS is approximately constant.

    For turn-on (voltage fall time):
    t_fu = (C_gd1 + C_gd2)/2 × ΔV_DS / I_gate

    For turn-off (voltage rise time):
    t_ru = (C_gd1 + C_gd2)/2 × ΔV_DS / I_gate

    Args:
        mosfet: MOSFET parameters
        v_ds: Drain-source voltage (V)
        v_gs_drive: Gate drive voltage (V)
        i_load: Load current during switching (A)
        r_g_total: Total gate resistance (Ω)

    Returns:
        Tuple of (t_fu, t_ru) - fall and rise times in seconds

    Reference:
        Infineon AN "MOSFET Power Losses...", Pages 8-9
    """
    # Get Miller capacitance at two voltage points
    # Point 1: V_DS ≈ 0V (fully on)
    c_gd1 = mosfet.capacitances.get_crss(vds=25.0)  # Use low VDS point

    # Point 2: V_DS = rated voltage
    c_gd2 = mosfet.capacitances.get_crss(vds=v_ds)

    # Average Miller capacitance
    c_gd_avg = (c_gd1 + c_gd2) / 2

    # Gate current during Miller plateau
    # I_gate = (V_GS_drive - V_plateau) / R_G_total
    v_plateau = mosfet.v_gs_plateau
    i_gate = (v_gs_drive - v_plateau) / r_g_total

    # Miller time (voltage transition time)
    # t_miller = C_gd × ΔV_DS / I_gate
    if i_gate > 0:
        t_miller = c_gd_avg * v_ds / i_gate
    else:
        t_miller = 0.0  # Avoid division by zero

    # For PSFB, turn-on and turn-off Miller times are similar
    t_fu = t_miller  # Fall time (turn-on)
    t_ru = t_miller  # Rise time (turn-off)

    return t_fu, t_ru


# =============================================================================
# SWITCHING ENERGY CALCULATION - HARD SWITCHING
# Reference: Infineon AN Equations 7-8, Page 10
# =============================================================================

def calculate_switching_energy_hard(
    v_ds: float,
    i_d: float,
    t_ri: float,
    t_fi: float,
    t_fu: float,
    t_ru: float,
    q_rr: float = 0.0
) -> Tuple[float, float]:
    """
    Calculate switching energies for hard-switching operation

    Implements Infineon AN Equations 7-8:
    E_on = V_DS × I_D × (t_ri + t_fu)/2 + Q_rr × V_DS
    E_off = V_DS × I_D × (t_ru + t_fi)/2

    Args:
        v_ds: Drain-source voltage during switching (V)
        i_d: Drain current during switching (A)
        t_ri: Current rise time (s)
        t_fi: Current fall time (s)
        t_fu: Voltage fall time (Miller plateau) (s)
        t_ru: Voltage rise time (Miller plateau) (s)
        q_rr: Reverse recovery charge of body diode or opposite device (C)

    Returns:
        Tuple of (E_on, E_off) - turn-on and turn-off energies in Joules

    Reference:
        Infineon AN "MOSFET Power Losses...", Equations 7-8, Page 10
    """
    # Equation 7: Turn-on energy
    # E_on = V_DS × I_D × (t_ri + t_fu)/2 + Q_rr × V_DS
    e_on_switching = v_ds * i_d * (t_ri + t_fu) / 2
    e_on_recovery = q_rr * v_ds
    e_on = e_on_switching + e_on_recovery

    # Equation 8: Turn-off energy
    # E_off = V_DS × I_D × (t_ru + t_fi)/2
    e_off = v_ds * i_d * (t_ru + t_fi) / 2

    return e_on, e_off


# =============================================================================
# SWITCHING ENERGY CALCULATION - ZVS OPERATION
# Reference: Soft-switching principles, capacitive charging
# =============================================================================

def calculate_switching_energy_zvs(
    mosfet: MOSFETParameters,
    v_ds: float,
    i_d_off: float
) -> Tuple[float, float]:
    """
    Calculate switching energies for Zero-Voltage Switching (ZVS) operation

    In ZVS operation:
    - Turn-on loss is nearly zero (capacitive discharge by resonant current)
    - Turn-off loss includes charging the output capacitance
    - E_cap = ½ × C_oss × V²_DS

    Args:
        mosfet: MOSFET parameters
        v_ds: Drain-source voltage (V)
        i_d_off: Turn-off current (A)

    Returns:
        Tuple of (E_on, E_off) - turn-on and turn-off energies in Joules

    Note:
        For true ZVS, E_on ≈ 0. This function calculates capacitive losses only.
    """
    # Get output capacitance at operating voltage
    c_oss = mosfet.capacitances.get_coss(vds=v_ds)

    # Turn-on energy (ZVS): essentially zero
    # Coss is discharged by resonant current before gate drive
    e_on = 0.0

    # Turn-off energy: Charging C_oss from 0 to V_DS
    # E_cap = ½ × C_oss × V²_DS
    e_off_capacitive = 0.5 * c_oss * v_ds**2

    # In practice, there may be some additional loss if ZVS is not perfect
    # But for ideal ZVS, this is the dominant loss mechanism
    e_off = e_off_capacitive

    return e_on, e_off


# =============================================================================
# SWITCHING POWER LOSS CALCULATION
# =============================================================================

def calculate_switching_loss(
    e_on: float,
    e_off: float,
    f_sw: float
) -> Tuple[float, float, float]:
    """
    Calculate switching power loss from energy per cycle

    P_sw = E_sw × f_sw

    Args:
        e_on: Turn-on energy per switching cycle (J)
        e_off: Turn-off energy per switching cycle (J)
        f_sw: Switching frequency (Hz)

    Returns:
        Tuple of (P_sw_on, P_sw_off, P_sw_total) in Watts
    """
    p_sw_on = e_on * f_sw
    p_sw_off = e_off * f_sw
    p_sw_total = p_sw_on + p_sw_off

    return p_sw_on, p_sw_off, p_sw_total


# =============================================================================
# GATE DRIVE LOSS CALCULATION
# Reference: Infineon AN Equation 14, Page 13
# =============================================================================

def calculate_gate_drive_loss(
    mosfet: MOSFETParameters,
    v_gs_drive: float,
    f_sw: float,
    n_parallel: int = 1
) -> float:
    """
    Calculate gate drive power loss

    Implements Infineon AN Equation 14:
    P_gate = Q_g × V_GS × f_sw × N_parallel

    Args:
        mosfet: MOSFET parameters
        v_gs_drive: Gate drive voltage (V)
        f_sw: Switching frequency (Hz)
        n_parallel: Number of MOSFETs in parallel (default: 1)

    Returns:
        Gate drive loss in Watts

    Reference:
        Infineon AN "MOSFET Power Losses...", Equation 14, Page 13
    """
    # Equation 14: P_gate = Q_g × V_GS × f_sw × N_parallel
    p_gate = mosfet.q_g * v_gs_drive * f_sw * n_parallel

    return p_gate


# =============================================================================
# COMPLETE MOSFET LOSS CALCULATION
# =============================================================================

def calculate_mosfet_losses(
    mosfet: MOSFETParameters,
    waveform: MOSFETCurrentWaveform,
    v_ds: float,
    f_sw: float,
    t_junction: float = 125.0,
    zvs_operation: bool = False,
    q_rr_external: float = 0.0,
    use_max_rdson: bool = True
) -> MOSFETLosses:
    """
    Calculate complete MOSFET loss breakdown

    Combines all loss mechanisms:
    - Conduction loss (temperature-dependent)
    - Switching loss (hard-switching or ZVS)
    - Gate drive loss

    Args:
        mosfet: MOSFET parameters
        waveform: Current waveform characteristics
        v_ds: Drain-source voltage during off-state (V)
        f_sw: Switching frequency (Hz)
        t_junction: Junction temperature for RDS(on) calculation (°C)
        zvs_operation: True for ZVS, False for hard-switching
        q_rr_external: External reverse recovery charge (e.g., from body diode) (C)
        use_max_rdson: If True, use maximum RDS(on); if False, use typical

    Returns:
        MOSFETLosses object with complete loss breakdown

    Example:
        >>> mosfet = MOSFETParameters(...)
        >>> waveform = MOSFETCurrentWaveform(i_rms=10.0, i_avg=5.0, i_peak=20.0, duty_cycle=0.5)
        >>> losses = calculate_mosfet_losses(mosfet, waveform, v_ds=400.0, f_sw=100e3)
        >>> print(f"Total loss: {losses.p_total:.2f} W")
    """
    # 1. Conduction loss
    p_cond = calculate_conduction_loss(
        mosfet=mosfet,
        i_rms=waveform.i_rms,
        t_junction=t_junction,
        use_max=use_max_rdson
    )

    # 2. Switching loss
    if zvs_operation:
        # ZVS operation - minimal switching loss
        e_on, e_off = calculate_switching_energy_zvs(
            mosfet=mosfet,
            v_ds=v_ds,
            i_d_off=waveform.i_peak
        )
    else:
        # Hard switching - calculate Miller times
        t_fu, t_ru = calculate_miller_time(
            mosfet=mosfet,
            v_ds=v_ds,
            v_gs_drive=mosfet.v_gs_drive,
            i_load=waveform.i_peak,
            r_g_total=mosfet.r_g_total
        )

        # Calculate switching energies
        e_on, e_off = calculate_switching_energy_hard(
            v_ds=v_ds,
            i_d=waveform.i_peak,
            t_ri=mosfet.t_r,
            t_fi=mosfet.t_f,
            t_fu=t_fu,
            t_ru=t_ru,
            q_rr=q_rr_external  # External recovery charge (if any)
        )

    # Convert energy to power
    p_sw_on, p_sw_off, p_sw_total = calculate_switching_loss(e_on, e_off, f_sw)

    # 3. Gate drive loss
    p_gate = calculate_gate_drive_loss(
        mosfet=mosfet,
        v_gs_drive=mosfet.v_gs_drive,
        f_sw=f_sw,
        n_parallel=1  # Per device
    )

    # 4. Total loss
    p_total = p_cond + p_sw_total + p_gate

    return MOSFETLosses(
        p_cond=p_cond,
        p_sw_on=p_sw_on,
        p_sw_off=p_sw_off,
        p_sw_total=p_sw_total,
        p_gate=p_gate,
        p_total=p_total,
        t_junction=t_junction
    )


# =============================================================================
# PSFB-SPECIFIC CURRENT WAVEFORM ESTIMATION
# =============================================================================

def estimate_psfb_primary_waveform(
    v_in: float,
    p_out: float,
    efficiency: float,
    duty_cycle: float
) -> MOSFETCurrentWaveform:
    """
    Estimate primary side MOSFET current waveform for PSFB converter

    For PSFB, each primary MOSFET conducts for approximately half the switching period.
    Current waveform is approximately trapezoidal.

    Args:
        v_in: Input voltage (V)
        p_out: Output power (W)
        efficiency: Converter efficiency (0-1)
        duty_cycle: Effective duty cycle related to phase shift (0-1)

    Returns:
        MOSFETCurrentWaveform with estimated values

    Note:
        This is a simplified estimation. Actual waveforms depend on:
        - Leakage inductance
        - Phase shift angle
        - ZVS timing
        - Transformer magnetizing current
    """
    # Input power
    p_in = p_out / efficiency

    # Average input current
    i_in_avg = p_in / v_in

    # For PSFB, each leg conducts for half period, but with 2 devices in series
    # RMS current per MOSFET (simplified):
    # Assuming trapezoidal waveform with duty ≈ 0.5
    i_rms = i_in_avg * np.sqrt(duty_cycle) / np.sqrt(2)  # Divided by 2 legs

    # Average current per MOSFET
    i_avg = i_in_avg * duty_cycle / 2

    # Peak current (depends on load and leakage inductance)
    # Rough estimate: 1.5× average for trapezoidal waveform
    i_peak = i_avg * 1.8

    return MOSFETCurrentWaveform(
        i_rms=i_rms,
        i_avg=i_avg,
        i_peak=i_peak,
        duty_cycle=duty_cycle
    )


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    from circuit_params import MOSFETParameters, CapacitanceVsVoltage

    print("="*70)
    print("MOSFET LOSS CALCULATION - EXAMPLE")
    print("="*70)

    # Example: Infineon IMZA65R020M2H (from 6.6kW marine example)
    caps_curve = [
        (25.0, 4500e-12, 180e-12, 45e-12),
        (100.0, 4200e-12, 95e-12, 22e-12),
        (400.0, 3900e-12, 40e-12, 9e-12),
    ]

    mosfet = MOSFETParameters(
        part_number="IMZA65R020M2H",
        v_dss=650.0,
        i_d_continuous=90.0,
        r_dson_25c=16e-3,
        r_dson_25c_max=20e-3,
        r_dson_150c=22e-3,
        r_dson_150c_max=28e-3,
        q_g=85e-9,
        q_gs=25e-9,
        q_gd=28e-9,
        v_gs_plateau=4.8,
        capacitances=CapacitanceVsVoltage(capacitance_curve=caps_curve),
        t_r=18e-9,
        t_f=14e-9,
        v_sd=2.2,
        q_rr=15e-9,
        t_rr=12e-9,
        r_th_jc=0.50,
        t_j_max=175.0,
        v_gs_drive=18.0,
        r_g_internal=1.5,
        r_g_external=5.0
    )

    # Example waveform (from 6.6kW marine PSFB @ 400V input)
    waveform = estimate_psfb_primary_waveform(
        v_in=400.0,
        p_out=6600.0,
        efficiency=0.94,
        duty_cycle=0.5
    )

    print(f"\nMOSFET: {mosfet.part_number}")
    print(f"  RDS(on) @ 25°C:  {mosfet.r_dson_25c*1e3:.1f} mΩ (typ), {mosfet.r_dson_25c_max*1e3:.1f} mΩ (max)")
    print(f"  Alpha coeff:     {mosfet.alpha_rdson:.3f} %/°C")

    print(f"\nEstimated Current Waveform:")
    print(f"  I_RMS:           {waveform.i_rms:.2f} A")
    print(f"  I_avg:           {waveform.i_avg:.2f} A")
    print(f"  I_peak:          {waveform.i_peak:.2f} A")
    print(f"  Duty cycle:      {waveform.duty_cycle:.2f}")

    # Calculate losses at 125°C junction temperature
    print(f"\n" + "-"*70)
    print("HARD-SWITCHING OPERATION @ Tj=125°C")
    print("-"*70)

    losses_hard = calculate_mosfet_losses(
        mosfet=mosfet,
        waveform=waveform,
        v_ds=400.0,
        f_sw=100e3,
        t_junction=125.0,
        zvs_operation=False,
        use_max_rdson=True
    )

    print(f"\nConduction Loss:     {losses_hard.p_cond:.3f} W")
    print(f"Turn-on Loss:        {losses_hard.p_sw_on:.3f} W")
    print(f"Turn-off Loss:       {losses_hard.p_sw_off:.3f} W")
    print(f"Switching Loss:      {losses_hard.p_sw_total:.3f} W")
    print(f"Gate Drive Loss:     {losses_hard.p_gate:.3f} W")
    print(f"TOTAL LOSS:          {losses_hard.p_total:.3f} W")

    # Calculate losses with ZVS
    print(f"\n" + "-"*70)
    print("ZVS OPERATION @ Tj=125°C")
    print("-"*70)

    losses_zvs = calculate_mosfet_losses(
        mosfet=mosfet,
        waveform=waveform,
        v_ds=400.0,
        f_sw=100e3,
        t_junction=125.0,
        zvs_operation=True,
        use_max_rdson=True
    )

    print(f"\nConduction Loss:     {losses_zvs.p_cond:.3f} W")
    print(f"Turn-on Loss:        {losses_zvs.p_sw_on:.3f} W (ZVS ≈ 0)")
    print(f"Turn-off Loss:       {losses_zvs.p_sw_off:.3f} W (capacitive)")
    print(f"Switching Loss:      {losses_zvs.p_sw_total:.3f} W")
    print(f"Gate Drive Loss:     {losses_zvs.p_gate:.3f} W")
    print(f"TOTAL LOSS:          {losses_zvs.p_total:.3f} W")

    # Comparison
    print(f"\n" + "="*70)
    print("ZVS BENEFIT")
    print("="*70)
    reduction = (losses_hard.p_total - losses_zvs.p_total) / losses_hard.p_total * 100
    print(f"Hard-switching loss: {losses_hard.p_total:.3f} W")
    print(f"ZVS loss:            {losses_zvs.p_total:.3f} W")
    print(f"Reduction:           {reduction:.1f}%")

    # Show RDS(on) at different temperatures
    print(f"\n" + "="*70)
    print("RDS(ON) vs TEMPERATURE")
    print("="*70)
    for tj in [25, 75, 125, 150]:
        rdson = calculate_rdson_at_temp(mosfet, tj, use_max=True)
        print(f"  Tj = {tj:3d}°C:  RDS(on) = {rdson*1e3:.2f} mΩ (max)")

    print("\n" + "="*70)

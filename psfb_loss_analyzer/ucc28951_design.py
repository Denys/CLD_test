#!/usr/bin/env python3
"""
UCC28951 Phase-Shifted Full-Bridge Controller Component Calculation

This module calculates all external components for the TI UCC28951/UCC28950
phase-shifted full-bridge controller and designs the compensation loop for
optimal control performance.

Design Goals:
- Gain Crossover Frequency: > 1 kHz
- Phase Margin: > 45°
- Stable operation across full load range

References:
- TI UCC28951 Datasheet (SLUS842)
- TI UCC28950 Design Calculator (SLUC222)
- Erickson & Maksimovic: "Fundamentals of Power Electronics" Ch 9

Author: PSFB Loss Analysis Tool
Version: 1.0.0
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np
from enum import Enum

# ============================================================================
# Data Structures
# ============================================================================

class CompensationType(Enum):
    """Compensation network type"""
    TYPE_II = "Type II"  # One pole, one zero
    TYPE_III = "Type III"  # Two poles, two zeros

@dataclass
class UCC28951Specification:
    """Input specification for UCC28951 design"""
    # Power stage parameters (from other modules)
    vin_min: float  # Minimum input voltage (V)
    vin_nom: float  # Nominal input voltage (V)
    vin_max: float  # Maximum input voltage (V)
    vout: float  # Output voltage (V)
    iout_max: float  # Maximum output current (A)

    # Transformer parameters (from transformer_design module)
    turns_ratio: float  # N_pri:N_sec
    leakage_inductance: float  # Primary-referred leakage inductance (H)

    # Output filter (from inductor_design module)
    output_inductance: float  # Output inductor (H)
    output_capacitance: float  # Output capacitor (F)
    output_cap_esr: float  # Output capacitor ESR (Ω)

    # Switching parameters
    switching_frequency: float  # Switching frequency (Hz)
    deadtime: float = 200e-9  # Deadtime between switches (s)

    # Current sensing
    current_sense_resistor: float = 0.010  # Current sense resistor (Ω)
    current_limit: float = 1.2  # Overcurrent limit as ratio of max current

    # Design targets
    target_crossover_freq: float = 3000.0  # Target gain crossover (Hz)
    target_phase_margin: float = 60.0  # Target phase margin (degrees)
    compensation_type: CompensationType = CompensationType.TYPE_III

@dataclass
class UCC28951ComponentValues:
    """Calculated component values for UCC28951"""
    # Timing components
    rt: float  # Timing resistor (Ω)
    ct: float  # Timing capacitor (F)

    # Voltage sensing and reference
    r_ref_top: float  # Reference divider top resistor (Ω)
    r_ref_bot: float  # Reference divider bottom resistor (Ω)
    r_fb_top: float  # Feedback divider top resistor (Ω)
    r_fb_bot: float  # Feedback divider bottom resistor (Ω)

    # Current sensing
    r_cs: float  # Current sense resistor (Ω)
    r_cs_filter: float  # CS pin filter resistor (Ω)
    c_cs_filter: float  # CS pin filter capacitor (F)

    # Compensation network (Type III)
    r_comp_upper: float  # Upper compensation resistor (Ω)
    r_comp_lower: float  # Lower compensation resistor (Ω)
    c_comp_hf: float  # High frequency compensation capacitor (F)
    c_comp_lf: float  # Low frequency compensation capacitor (F)
    c_comp_pole: float  # High frequency pole capacitor (F)

    # Soft-start
    c_ss: float  # Soft-start capacitor (F)

    # Additional calculated values
    actual_switching_freq: float  # Actual switching frequency (Hz)
    gain_crossover_freq: float  # Actual gain crossover frequency (Hz)
    phase_margin: float  # Actual phase margin (degrees)
    gain_margin: float  # Gain margin (dB)

@dataclass
class PowerStageTransferFunction:
    """Power stage small-signal transfer function parameters"""
    dc_gain: float  # DC gain (V/V or dB)
    esr_zero_freq: float  # ESR zero frequency (Hz)
    lc_resonant_freq: float  # LC double pole frequency (Hz)
    q_factor: float  # Quality factor at LC resonance
    rhp_zero_freq: Optional[float] = None  # Right-half-plane zero (Hz), if present

# ============================================================================
# Power Stage Analysis
# ============================================================================

def calculate_power_stage_tf(spec: UCC28951Specification) -> PowerStageTransferFunction:
    """
    Calculate power stage small-signal transfer function.

    For voltage-mode control, the control-to-output transfer function is:

    Gvd(s) = Gdc · (1 + s/ωz_esr) / [(1 + s/ωp_rhpz) · (1 + s/(Q·ω0) + s²/ω0²)]

    where:
    - Gdc = Vin / (n · D) for PSFB
    - ωz_esr = 1 / (ESR · Co)
    - ω0 = 1 / sqrt(Lo · Co)
    - Q = Ro / sqrt(Lo/Co)
    """
    # DC gain (small-signal, duty cycle to output)
    # For PSFB: Vo = Vin * D / n, so dVo/dD = Vin/n
    duty_cycle = spec.vout * spec.turns_ratio / (2 * spec.vin_nom)
    dc_gain = spec.vin_nom / spec.turns_ratio  # V/V
    dc_gain_db = 20 * np.log10(dc_gain)

    # ESR zero frequency
    esr_zero_freq = 1.0 / (2 * np.pi * spec.output_cap_esr * spec.output_capacitance)

    # LC resonant frequency (double pole)
    lc_resonant_freq = 1.0 / (2 * np.pi * np.sqrt(spec.output_inductance * spec.output_capacitance))

    # Quality factor
    # Load resistance
    r_load = spec.vout / spec.iout_max
    # Characteristic impedance
    z0 = np.sqrt(spec.output_inductance / spec.output_capacitance)
    # Q factor (includes ESR damping)
    r_total = r_load + spec.output_cap_esr
    q_factor = r_total / z0 if z0 > 0 else 10.0

    # Right-half-plane zero (for current-fed converters, typically not dominant in PSFB)
    # For PSFB, RHP zero is typically at very high frequency or not present
    rhp_zero_freq = None

    return PowerStageTransferFunction(
        dc_gain=dc_gain_db,
        esr_zero_freq=esr_zero_freq,
        lc_resonant_freq=lc_resonant_freq,
        q_factor=q_factor,
        rhp_zero_freq=rhp_zero_freq
    )

# ============================================================================
# Timing Components
# ============================================================================

def calculate_timing_components(switching_frequency: float) -> Tuple[float, float]:
    """
    Calculate RT and CT for UCC28951.

    Switching frequency relationship:
    fsw = 1 / (RT · CT · 0.97e-6)  (from datasheet)

    Typical values:
    - RT: 10kΩ to 100kΩ
    - CT: 1nF to 100nF

    Returns:
        (rt, ct): RT in Ω, CT in F
    """
    # Choose CT first (standard value)
    ct_options = [1e-9, 2.2e-9, 4.7e-9, 10e-9, 22e-9, 47e-9, 100e-9]  # nF

    # Try each CT and find RT
    for ct in ct_options:
        rt = 1.0 / (switching_frequency * ct * 0.97e-6)

        # Check if RT is in reasonable range (10k to 100k)
        if 10e3 <= rt <= 100e3:
            # Round to nearest E96 resistor value
            rt = round_to_standard_resistor(rt)
            # Recalculate actual frequency
            actual_freq = 1.0 / (rt * ct * 0.97e-6)

            # Check if within 5% of target
            if abs(actual_freq - switching_frequency) / switching_frequency < 0.05:
                return rt, ct

    # If no good match, use middle CT value and calculate RT
    ct = 10e-9
    rt = 1.0 / (switching_frequency * ct * 0.97e-6)
    rt = round_to_standard_resistor(rt)

    return rt, ct

# ============================================================================
# Voltage Sensing
# ============================================================================

def calculate_voltage_sensing(vout: float) -> Tuple[float, float, float, float]:
    """
    Calculate voltage sensing resistors.

    UCC28951 has:
    - VREF pin: 5V reference
    - FB pin: Feedback input (compare to VREF/2 = 2.5V)

    Design approach:
    - REF pin voltage divider: Sets internal reference (typically 5V)
    - FB pin voltage divider: Scales Vout to 2.5V nominal

    Returns:
        (r_ref_top, r_ref_bot, r_fb_top, r_fb_bot) in Ω
    """
    # REF pin divider (typically just a bypass, or set to 5V)
    # For simplicity, we'll use standard values for 5V reference
    r_ref_top = 10e3  # 10kΩ
    r_ref_bot = 10e3  # 10kΩ (creates 2.5V from 5V, but VREF is internally regulated)

    # FB pin divider (scales Vout to 2.5V)
    # Vout · R_bot / (R_top + R_bot) = 2.5V
    # Choose R_bot, calculate R_top

    # Use ~10kΩ total for reasonable current (~250µA)
    r_fb_bot = 10e3  # 10kΩ
    r_fb_top = r_fb_bot * (vout - 2.5) / 2.5
    r_fb_top = round_to_standard_resistor(r_fb_top)

    return r_ref_top, r_ref_bot, r_fb_top, r_fb_bot

# ============================================================================
# Current Sensing
# ============================================================================

def calculate_current_sensing(
    iout_max: float,
    turns_ratio: float,
    r_sense: float,
    current_limit_ratio: float = 1.2
) -> Tuple[float, float, float]:
    """
    Calculate current sense components.

    UCC28951 CS pin:
    - Cycle-by-cycle current limit at ~1V
    - Filter to reject switching noise

    Returns:
        (r_cs, r_cs_filter, c_cs_filter)
    """
    # Primary current (max)
    i_pri_max = iout_max / turns_ratio

    # Sense resistor voltage at max current (with margin)
    v_sense_max = i_pri_max * current_limit_ratio * r_sense

    # UCC28951 CS threshold is ~1V (check datasheet for exact value)
    # Ensure we don't exceed this
    if v_sense_max > 0.9:
        print(f"Warning: CS voltage ({v_sense_max:.2f}V) near limit. Consider reducing R_sense.")

    # CS pin filter (to reject switching noise)
    # RC filter with cutoff ~100kHz (much less than switching freq)
    r_cs_filter = 1e3  # 1kΩ
    c_cs_filter = 1.0 / (2 * np.pi * r_cs_filter * 100e3)
    c_cs_filter = round_to_standard_capacitor(c_cs_filter)

    return r_sense, r_cs_filter, c_cs_filter

# ============================================================================
# Compensation Network Design (Type III)
# ============================================================================

def design_type3_compensation(
    spec: UCC28951Specification,
    power_stage: PowerStageTransferFunction
) -> Tuple[float, float, float, float, float, float, float]:
    """
    Design Type III compensation network for voltage-mode control.

    Type III compensator:
    - Two zeros: Cancel LC double pole
    - Two poles: One at origin (integrator), one at high freq (filter switching noise)
    - Mid-frequency gain: Set crossover frequency

    Network topology (around error amplifier):
          C_hf
           |
    R_upper--+--C_lf--+
             |        |
    FB ------+        +------ COMP (to PWM)
                      |
                   R_lower
                      |
                   C_pole
                      |
                     GND

    Returns:
        (r_upper, r_lower, c_hf, c_lf, c_pole, fc, pm)
    """
    # Target crossover frequency
    fc_target = spec.target_crossover_freq

    # Power stage parameters
    f0 = power_stage.lc_resonant_freq  # LC resonance
    fz_esr = power_stage.esr_zero_freq  # ESR zero
    Q = power_stage.q_factor

    # Type III compensator design
    # Place zeros BELOW LC resonant frequency to provide phase boost
    # Rule of thumb: place zeros at f0/3 to f0/4 for PM > 45°
    # Target crossover between f0 and fz_esr for maximum phase margin
    fz1 = f0 / 4.0  # First zero well below f0
    fz2 = f0 / 4.0  # Second zero (same location)

    # High frequency pole (to filter switching noise)
    # Place at ~fsw/10 to avoid reducing phase margin
    fp2 = spec.switching_frequency / 10  # 1/10 of switching frequency

    # Calculate required mid-band gain to achieve crossover
    # At crossover: |Gc(fc)| · |Gp(fc)| = 1 (0 dB)
    # where Gc = compensator, Gp = power stage

    # Power stage gain at crossover (approximate)
    # Below f0: gain is flat at Gdc
    # At f0: gain drops by Q (if underdamped)
    # Above f0: gain rolls off at -40dB/dec

    if fc_target < f0:
        # Crossover below resonance
        gp_at_fc_db = power_stage.dc_gain
    else:
        # Crossover above resonance (typical for good phase margin)
        gp_at_fc_db = power_stage.dc_gain - 40 * np.log10(fc_target / f0)

    # Compensator must provide negative of this gain
    gc_required_db = -gp_at_fc_db

    # Type III mid-band gain (between fz and fp2):
    # Gc_mid = (2π · fz · R_upper · C_lf)
    # In dB: 20·log10(2π · fz · R_upper · C_lf)

    # Choose R_upper (start with reasonable value)
    r_upper = 100e3  # 100kΩ

    # Choose C_lf to set zero frequency
    c_lf = 1.0 / (2 * np.pi * fz1 * r_upper)
    c_lf = round_to_standard_capacitor(c_lf)

    # C_hf = C_lf / 10 (typical ratio for Type III)
    c_hf = c_lf / 10
    c_hf = round_to_standard_capacitor(c_hf)

    # Calculate actual zero frequencies
    fz1_actual = 1.0 / (2 * np.pi * r_upper * c_lf)
    fz2_actual = 1.0 / (2 * np.pi * r_upper * c_hf)

    # R_lower sets DC gain and low-frequency pole
    # Low frequency pole at fp1 = 1/(2π · R_lower · C_lf)
    # Set fp1 << fc for good low-frequency gain
    # Also, R_upper/R_lower sets the mid-band gain boost

    # Calculate required mid-band gain to achieve crossover
    # At crossover, we need |Gc(fc)| · |Gp(fc)| = 1
    # Power stage gain at fc (assume fc > f0, so -40dB/dec rolloff)
    if fc_target > f0:
        gp_at_fc_linear = 10 ** (power_stage.dc_gain / 20) * (f0 / fc_target) ** 2
    else:
        gp_at_fc_linear = 10 ** (power_stage.dc_gain / 20)

    # Compensator needs gain of 1/Gp at crossover
    gc_required_linear = 1.0 / gp_at_fc_linear

    # Mid-band gain of Type III: Gc_mid ≈ (R_upper/R_lower) · (fc / fz)
    # Solve for R_lower
    r_lower = r_upper / (gc_required_linear * fc_target / fz1)
    r_lower = round_to_standard_resistor(r_lower)

    # Ensure R_lower gives reasonable low-freq pole
    fp1 = 1.0 / (2 * np.pi * r_lower * c_lf)
    if fp1 > fc_target / 10:
        # Pole too high, increase R_lower
        fp1_target = fc_target / 20
        r_lower = 1.0 / (2 * np.pi * fp1_target * c_lf)
        r_lower = round_to_standard_resistor(r_lower)

    # C_pole sets high frequency pole
    # fp2 = 1/(2π · R_upper · C_pole)
    c_pole = 1.0 / (2 * np.pi * r_upper * fp2)
    c_pole = round_to_standard_capacitor(c_pole)

    # Calculate actual crossover frequency and phase margin
    # This requires loop gain analysis
    fc_actual, pm_actual = calculate_loop_response(
        spec, power_stage, r_upper, r_lower, c_hf, c_lf, c_pole
    )

    return r_upper, r_lower, c_hf, c_lf, c_pole, fc_actual, pm_actual

def calculate_loop_response(
    spec: UCC28951Specification,
    power_stage: PowerStageTransferFunction,
    r_upper: float,
    r_lower: float,
    c_hf: float,
    c_lf: float,
    c_pole: float
) -> Tuple[float, float]:
    """
    Calculate actual crossover frequency and phase margin.

    This function evaluates the loop gain magnitude and phase over frequency
    to find the actual crossover frequency and phase margin.

    Returns:
        (crossover_freq, phase_margin)
    """
    # Frequency sweep (10 Hz to 1 MHz)
    freqs = np.logspace(1, 6, 1000)
    s = 2j * np.pi * freqs

    # Power stage transfer function
    # Gp(s) = Gdc · (1 + s/ωz_esr) / [(1 + s/(Q·ω0) + s²/ω0²)]
    gdc_linear = 10 ** (power_stage.dc_gain / 20)
    wz_esr = 2 * np.pi * power_stage.esr_zero_freq
    w0 = 2 * np.pi * power_stage.lc_resonant_freq
    Q = power_stage.q_factor

    gp = gdc_linear * (1 + s / wz_esr) / (1 + s / (Q * w0) + s**2 / w0**2)

    # Compensator transfer function (Type III)
    # Gc(s) = (R_upper/R_lower) · (1 + s·R_upper·C_lf) · (1 + s·R_upper·C_hf) /
    #         [s·C_lf · (1 + s·R_upper·C_pole)]

    fz1 = 1.0 / (2 * np.pi * r_upper * c_lf)
    fz2 = 1.0 / (2 * np.pi * r_upper * c_hf)
    fp1 = 1.0 / (2 * np.pi * r_lower * c_lf)
    fp2 = 1.0 / (2 * np.pi * r_upper * c_pole)

    wz1 = 2 * np.pi * fz1
    wz2 = 2 * np.pi * fz2
    wp1 = 2 * np.pi * fp1
    wp2 = 2 * np.pi * fp2

    # Avoid division by zero at DC
    s_safe = s + 1e-10

    gc = (r_upper / r_lower) * (1 + s / wz1) * (1 + s / wz2) / (s_safe / wp1 * (1 + s / wp2))

    # Loop gain
    loop_gain = gp * gc
    loop_gain_mag = np.abs(loop_gain)
    loop_gain_mag_db = 20 * np.log10(loop_gain_mag + 1e-12)
    loop_gain_phase = np.angle(loop_gain, deg=True)

    # Find crossover frequency (where magnitude = 0 dB)
    # Find the index where magnitude crosses 0 dB
    crossover_idx = np.argmin(np.abs(loop_gain_mag_db))
    crossover_freq = freqs[crossover_idx]

    # Phase margin at crossover
    phase_at_crossover = loop_gain_phase[crossover_idx]
    phase_margin = 180 + phase_at_crossover

    # Ensure we found actual crossover (not just minimum)
    if abs(loop_gain_mag_db[crossover_idx]) > 3:  # More than 3dB from 0dB
        # Try to find where it actually crosses
        for i in range(len(loop_gain_mag_db) - 1):
            if loop_gain_mag_db[i] > 0 and loop_gain_mag_db[i + 1] < 0:
                # Interpolate
                crossover_freq = freqs[i]
                phase_at_crossover = loop_gain_phase[i]
                phase_margin = 180 + phase_at_crossover
                break

    return crossover_freq, phase_margin

# ============================================================================
# Soft-Start Capacitor
# ============================================================================

def calculate_soft_start_capacitor(
    vout: float,
    iout_max: float,
    startup_time: float = 0.010  # 10ms typical
) -> float:
    """
    Calculate soft-start capacitor.

    UCC28951 soft-start:
    - SS pin charges through internal 10µA current source
    - Output voltage ramps proportionally to SS voltage
    - tss = Css · Vss / Iss

    where Vss ~= 5V, Iss = 10µA

    Returns:
        c_ss in F
    """
    i_ss = 10e-6  # 10µA internal current source
    v_ss = 5.0  # SS voltage range

    # C_ss = I_ss · t_ss / V_ss
    c_ss = i_ss * startup_time / v_ss

    # Round to standard value
    c_ss = round_to_standard_capacitor(c_ss)

    return c_ss

# ============================================================================
# Helper Functions
# ============================================================================

def round_to_standard_resistor(value: float, series: str = "E96") -> float:
    """Round to nearest standard resistor value"""
    if series == "E96":
        # E96 series (1% tolerance)
        e96 = [1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24,
               1.27, 1.30, 1.33, 1.37, 1.40, 1.43, 1.47, 1.50, 1.54, 1.58,
               1.62, 1.65, 1.69, 1.74, 1.78, 1.82, 1.87, 1.91, 1.96, 2.00,
               2.05, 2.10, 2.15, 2.21, 2.26, 2.32, 2.37, 2.43, 2.49, 2.55,
               2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09, 3.16, 3.24,
               3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12,
               4.22, 4.32, 4.42, 4.53, 4.64, 4.75, 4.87, 4.99, 5.11, 5.23,
               5.36, 5.49, 5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65,
               6.81, 6.98, 7.15, 7.32, 7.50, 7.68, 7.87, 8.06, 8.25, 8.45,
               8.66, 8.87, 9.09, 9.31, 9.53, 9.76]
    else:
        # E24 series (5% tolerance)
        e96 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4,
               2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2,
               6.8, 7.5, 8.2, 9.1]

    # Find decade
    decade = 10 ** np.floor(np.log10(value))
    normalized = value / decade

    # Find closest standard value
    closest = min(e96, key=lambda x: abs(x - normalized))

    return closest * decade

def round_to_standard_capacitor(value: float) -> float:
    """Round to nearest standard capacitor value"""
    # E12 series for capacitors
    e12 = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]

    # Find decade
    decade = 10 ** np.floor(np.log10(value))
    normalized = value / decade

    # Find closest standard value
    closest = min(e12, key=lambda x: abs(x - normalized))

    return closest * decade

# ============================================================================
# Main Design Function
# ============================================================================

def design_ucc28951_components(spec: UCC28951Specification) -> UCC28951ComponentValues:
    """
    Complete UCC28951 component calculation.

    This function integrates all component calculations and compensation
    design to produce a complete set of component values.

    Args:
        spec: UCC28951Specification with power stage parameters

    Returns:
        UCC28951ComponentValues with all calculated components
    """
    # 1. Analyze power stage transfer function
    power_stage = calculate_power_stage_tf(spec)

    print("Power Stage Analysis:")
    print(f"  DC Gain: {power_stage.dc_gain:.1f} dB")
    print(f"  ESR Zero: {power_stage.esr_zero_freq:.1f} Hz")
    print(f"  LC Resonance: {power_stage.lc_resonant_freq:.1f} Hz")
    print(f"  Q Factor: {power_stage.q_factor:.2f}")
    print()

    # 2. Calculate timing components
    rt, ct = calculate_timing_components(spec.switching_frequency)
    actual_fsw = 1.0 / (rt * ct * 0.97e-6)

    print("Timing Components:")
    print(f"  RT = {rt/1e3:.1f} kΩ")
    print(f"  CT = {ct*1e9:.1f} nF")
    print(f"  Actual fsw = {actual_fsw/1e3:.2f} kHz")
    print()

    # 3. Calculate voltage sensing
    r_ref_top, r_ref_bot, r_fb_top, r_fb_bot = calculate_voltage_sensing(spec.vout)

    print("Voltage Sensing:")
    print(f"  R_FB_TOP = {r_fb_top/1e3:.1f} kΩ")
    print(f"  R_FB_BOT = {r_fb_bot/1e3:.1f} kΩ")
    print()

    # 4. Calculate current sensing
    r_cs, r_cs_filter, c_cs_filter = calculate_current_sensing(
        spec.iout_max, spec.turns_ratio, spec.current_sense_resistor, spec.current_limit
    )

    print("Current Sensing:")
    print(f"  R_CS = {r_cs*1e3:.1f} mΩ")
    print(f"  R_CS_FILTER = {r_cs_filter/1e3:.1f} kΩ")
    print(f"  C_CS_FILTER = {c_cs_filter*1e9:.1f} nF")
    print()

    # 5. Design compensation network
    r_upper, r_lower, c_hf, c_lf, c_pole, fc, pm = design_type3_compensation(spec, power_stage)

    print("Compensation Network (Type III):")
    print(f"  R_UPPER = {r_upper/1e3:.1f} kΩ")
    print(f"  R_LOWER = {r_lower/1e3:.1f} kΩ")
    print(f"  C_HF = {c_hf*1e12:.1f} pF")
    print(f"  C_LF = {c_lf*1e9:.1f} nF")
    print(f"  C_POLE = {c_pole*1e12:.1f} pF")
    print()
    print("Loop Performance:")
    print(f"  Crossover Frequency: {fc:.1f} Hz")
    print(f"  Phase Margin: {pm:.1f}°")
    print()

    # 6. Calculate soft-start capacitor
    c_ss = calculate_soft_start_capacitor(spec.vout, spec.iout_max)

    print("Soft-Start:")
    print(f"  C_SS = {c_ss*1e6:.2f} µF")
    print()

    # Check design targets
    if fc >= spec.target_crossover_freq:
        print(f"✓ Crossover frequency target met ({fc:.1f} Hz >= {spec.target_crossover_freq:.1f} Hz)")
    else:
        print(f"✗ Crossover frequency below target ({fc:.1f} Hz < {spec.target_crossover_freq:.1f} Hz)")

    if pm >= spec.target_phase_margin:
        print(f"✓ Phase margin target met ({pm:.1f}° >= {spec.target_phase_margin:.1f}°)")
    else:
        print(f"✗ Phase margin below target ({pm:.1f}° < {spec.target_phase_margin:.1f}°)")

    # Estimate gain margin (at 180° phase)
    # For now, use simplified estimate
    gain_margin = 12.0  # dB (typical for well-designed Type III)

    return UCC28951ComponentValues(
        rt=rt,
        ct=ct,
        r_ref_top=r_ref_top,
        r_ref_bot=r_ref_bot,
        r_fb_top=r_fb_top,
        r_fb_bot=r_fb_bot,
        r_cs=r_cs,
        r_cs_filter=r_cs_filter,
        c_cs_filter=c_cs_filter,
        r_comp_upper=r_upper,
        r_comp_lower=r_lower,
        c_comp_hf=c_hf,
        c_comp_lf=c_lf,
        c_comp_pole=c_pole,
        c_ss=c_ss,
        actual_switching_freq=actual_fsw,
        gain_crossover_freq=fc,
        phase_margin=pm,
        gain_margin=gain_margin
    )

# ============================================================================
# Integration with Existing Modules
# ============================================================================

def create_spec_from_transformer_design(
    transformer_result,  # TransformerDesignResult
    output_inductor_result,  # InductorDesignResult
    output_capacitance: float,  # F
    output_cap_esr: float,  # Ω
    vin_min: float,
    vin_nom: float,
    vin_max: float,
    vout: float,
    iout_max: float,
    switching_frequency: float
) -> UCC28951Specification:
    """
    Create UCC28951Specification from existing design results.

    This function bridges the gap between transformer/inductor design
    and UCC28951 component calculation.
    """
    # Extract transformer parameters
    turns_ratio = transformer_result.n_primary / transformer_result.n_secondary

    # Estimate leakage inductance (typically 1-5% of magnetizing inductance)
    # For now, use simplified estimate or user-provided value
    leakage_inductance = 10e-6  # 10µH typical for kW-range PSFB

    # Extract output inductor parameters
    output_inductance = output_inductor_result.inductance_actual

    return UCC28951Specification(
        vin_min=vin_min,
        vin_nom=vin_nom,
        vin_max=vin_max,
        vout=vout,
        iout_max=iout_max,
        turns_ratio=turns_ratio,
        leakage_inductance=leakage_inductance,
        output_inductance=output_inductance,
        output_capacitance=output_capacitance,
        output_cap_esr=output_cap_esr,
        switching_frequency=switching_frequency
    )

# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example: 3kW PSFB with UCC28951
    spec = UCC28951Specification(
        vin_min=360.0,
        vin_nom=400.0,
        vin_max=440.0,
        vout=48.0,
        iout_max=62.5,  # 3kW / 48V
        turns_ratio=8.0,  # 16:2
        leakage_inductance=10e-6,  # 10µH
        output_inductance=10e-6,  # 10µH
        output_capacitance=1000e-6,  # 1000µF
        output_cap_esr=0.010,  # 10mΩ
        switching_frequency=100e3,  # 100kHz
        target_crossover_freq=3000.0,  # 3kHz
        target_phase_margin=60.0,  # 60°
    )

    print("=" * 80)
    print("UCC28951 COMPONENT CALCULATION")
    print("=" * 80)
    print()

    result = design_ucc28951_components(spec)

    print()
    print("=" * 80)
    print("DESIGN COMPLETE")
    print("=" * 80)

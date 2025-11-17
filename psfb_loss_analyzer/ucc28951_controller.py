"""
UCC28951 Phase-Shifted Full-Bridge Controller Calculation Module

This module provides calculations for the UCC28951/UCC28950 controller
from Texas Instruments for phase-shifted full-bridge (PSFB) DC-DC converters.

Features:
- Component value calculations (timing, soft-start, compensation)
- Loop compensation design
- Protection threshold calculations
- Bode plot generation
- BOM generation

Reference: Texas Instruments UCC28950/UCC28951 Datasheet and Application Notes

Author: PSFB Loss Analysis Tool
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from enum import Enum


class ControlMode(Enum):
    """UCC28951 control modes"""
    VOLTAGE_MODE = "voltage_mode"
    PEAK_CURRENT_MODE = "peak_current_mode"


@dataclass
class UCC28951PowerStage:
    """Power stage parameters for UCC28951 design"""
    # Input/Output specifications
    v_in_min: float  # Minimum input voltage (V)
    v_in_nom: float  # Nominal input voltage (V)
    v_in_max: float  # Maximum input voltage (V)
    v_out: float  # Output voltage (V)
    i_out_max: float  # Maximum output current (A)
    p_out: float  # Output power (W)

    # Switching specifications
    f_sw: float  # Switching frequency (Hz)
    dead_time: float = 200e-9  # Dead time (s), default 200ns
    max_duty_cycle: float = 0.45  # Maximum duty cycle (per leg), default 45%

    # Transformer
    n_primary: int = 1  # Primary turns (for full-bridge, typically 1:1:1:1 per switch)
    n_secondary: int = 1  # Secondary turns
    n_ratio: float = field(init=False)  # Calculated turns ratio Np:Ns
    leakage_inductance: float = 2.5e-6  # Transformer leakage inductance (H)
    magnetizing_inductance: float = 250e-6  # Magnetizing inductance (H)

    # Secondary rectifier
    v_f_rectifier: float = 0.5  # Rectifier forward voltage drop (V)

    # Control mode
    control_mode: ControlMode = ControlMode.VOLTAGE_MODE

    def __post_init__(self):
        """Calculate derived parameters"""
        self.n_ratio = self.n_primary / self.n_secondary


@dataclass
class UCC28951Components:
    """Calculated component values for UCC28951"""
    # Timing components
    r_t: float = 0.0  # Oscillator timing resistor (Ω)
    c_t: float = 0.0  # Oscillator timing capacitor (F)

    # Soft-start
    c_ss: float = 0.0  # Soft-start capacitor (F)
    t_ss: float = 0.0  # Soft-start time (s)

    # Adaptive delay set
    r_ads: float = 0.0  # Adaptive delay set resistor (Ω)
    t_delay: float = 0.0  # Adaptive delay time (s)

    # Compensation (Type II or Type III)
    r_comp: float = 0.0  # Compensation resistor (Ω)
    c_comp1: float = 0.0  # Compensation capacitor 1 (F)
    c_comp2: float = 0.0  # Compensation capacitor 2 (F)
    r_comp2: float = 0.0  # Compensation resistor 2 (Ω)

    # Current sense (for peak current mode)
    r_cs: float = 0.0  # Current sense resistor (Ω)
    v_cs_max: float = 1.0  # Maximum current sense voltage (V)

    # Output voltage divider
    r_upper: float = 0.0  # Upper feedback resistor (Ω)
    r_lower: float = 0.0  # Lower feedback resistor (Ω)

    # Input voltage compensation
    r_eao: float = 0.0  # Error amplifier output resistor (Ω)

    # Input UVLO
    r_uvlo_upper: float = 0.0  # UVLO upper resistor (Ω)
    r_uvlo_lower: float = 0.0  # UVLO lower resistor (Ω)


@dataclass
class UCC28951LoopResponse:
    """Frequency response data for compensation design"""
    frequencies: np.ndarray = field(default_factory=lambda: np.array([]))  # Frequency array (Hz)
    gain_db: np.ndarray = field(default_factory=lambda: np.array([]))  # Gain (dB)
    phase_deg: np.ndarray = field(default_factory=lambda: np.array([]))  # Phase (degrees)
    f_crossover: float = 0.0  # Crossover frequency (Hz)
    phase_margin: float = 0.0  # Phase margin (degrees)
    gain_margin: float = 0.0  # Gain margin (dB)


class UCC28951Designer:
    """UCC28951 controller design and calculation engine"""

    # UCC28951 internal constants
    V_REF = 2.5  # Internal reference voltage (V)
    I_SS = 10e-6  # Soft-start charging current (A)
    V_SS_MAX = 5.0  # Maximum soft-start voltage (V)
    R_T_NOMINAL = 10e3  # Nominal timing resistor (10kΩ)
    V_CS_TH = 1.0  # Current sense threshold (V)
    V_UVLO = 12.0  # UVLO threshold (V)
    I_EAOUT = 2.5e-3  # Error amplifier output current (mA)

    def __init__(self, power_stage: UCC28951PowerStage):
        """
        Initialize UCC28951 designer

        Args:
            power_stage: Power stage parameters
        """
        self.power_stage = power_stage
        self.components = UCC28951Components()

    def calculate_timing_components(self) -> Tuple[float, float]:
        """
        Calculate oscillator timing components RT and CT

        The UCC28951 oscillator frequency is set by:
        f_sw = 1 / (R_T * C_T * 1.4)  (approximately)

        Returns:
            (R_T, C_T): Timing resistor and capacitor
        """
        # Use standard value for RT (typically 10k to 100k)
        r_t = 47e3  # 47kΩ (standard value)

        # Calculate CT from desired frequency
        # f_sw = 1 / (1.4 * R_T * C_T)
        c_t = 1.0 / (1.4 * r_t * self.power_stage.f_sw)

        self.components.r_t = r_t
        self.components.c_t = c_t

        return r_t, c_t

    def calculate_soft_start(self, t_ss_desired: float = 10e-3) -> float:
        """
        Calculate soft-start capacitor

        The soft-start time is determined by:
        t_ss = C_SS * V_SS_MAX / I_SS

        Args:
            t_ss_desired: Desired soft-start time (s), default 10ms

        Returns:
            C_SS: Soft-start capacitor (F)
        """
        # Calculate CSS
        c_ss = (t_ss_desired * self.I_SS) / self.V_SS_MAX

        self.components.c_ss = c_ss
        self.components.t_ss = t_ss_desired

        return c_ss

    def calculate_adaptive_delay(self) -> Tuple[float, float]:
        """
        Calculate adaptive delay set resistor

        The adaptive delay is used for ZVS optimization.
        R_ADS sets the delay time between primary and secondary transitions.

        Returns:
            (R_ADS, t_delay): Adaptive delay resistor and time
        """
        # Adaptive delay should be roughly equal to transformer + rectifier delay
        # Typically 100-300ns
        t_delay = self.power_stage.dead_time * 0.5  # Half of dead time

        # R_ADS calculation (from datasheet)
        # t_delay = R_ADS * 100pF (approximately)
        r_ads = t_delay / 100e-12

        self.components.r_ads = r_ads
        self.components.t_delay = t_delay

        return r_ads, t_delay

    def calculate_output_divider(self, r_lower: float = 10e3) -> Tuple[float, float]:
        """
        Calculate output voltage feedback divider

        The divider sets V_FB = 2.5V when V_OUT = V_out (nominal)
        R_upper / R_lower = (V_out - V_REF) / V_REF

        Args:
            r_lower: Lower resistor value (Ω), typically 10kΩ

        Returns:
            (R_upper, R_lower): Upper and lower feedback resistors
        """
        # Calculate R_upper
        r_upper = r_lower * (self.power_stage.v_out - self.V_REF) / self.V_REF

        self.components.r_upper = r_upper
        self.components.r_lower = r_lower

        return r_upper, r_lower

    def calculate_current_sense_resistor(self, i_pri_peak: Optional[float] = None) -> float:
        """
        Calculate current sense resistor for peak current mode control

        Args:
            i_pri_peak: Peak primary current (A), calculated if not provided

        Returns:
            R_CS: Current sense resistor (Ω)
        """
        if i_pri_peak is None:
            # Estimate peak primary current
            # P_in = P_out / efficiency (assume 93%)
            p_in = self.power_stage.p_out / 0.93
            i_in_avg = p_in / self.power_stage.v_in_nom

            # Peak current is approximately 1.5-2x average for phase-shifted operation
            i_pri_peak = i_in_avg * 1.8

        # R_CS = V_CS_TH / I_pri_peak
        r_cs = self.V_CS_TH / i_pri_peak

        self.components.r_cs = r_cs
        self.components.v_cs_max = self.V_CS_TH

        return r_cs

    def calculate_uvlo_divider(self, v_uvlo_on: float, v_uvlo_off: float,
                               r_lower: float = 10e3) -> Tuple[float, float]:
        """
        Calculate UVLO voltage divider

        Args:
            v_uvlo_on: UVLO turn-on voltage (V)
            v_uvlo_off: UVLO turn-off voltage (V)
            r_lower: Lower resistor value (Ω)

        Returns:
            (R_upper, R_lower): UVLO resistor divider
        """
        # At UVLO threshold, V_UVLO = 12V (typical)
        # R_upper / R_lower = (V_uvlo_on - V_UVLO) / V_UVLO
        r_upper = r_lower * (v_uvlo_on - self.V_UVLO) / self.V_UVLO

        self.components.r_uvlo_upper = r_upper
        self.components.r_uvlo_lower = r_lower

        return r_upper, r_lower

    def design_type2_compensation(self, f_crossover: float = None,
                                  phase_boost: float = 60.0) -> Dict[str, float]:
        """
        Design Type II compensation network

        Type II compensation provides one pole and one zero for voltage mode control.

        Args:
            f_crossover: Desired crossover frequency (Hz), default f_sw/10
            phase_boost: Desired phase boost (degrees)

        Returns:
            Dictionary with compensation component values
        """
        if f_crossover is None:
            f_crossover = self.power_stage.f_sw / 10.0

        # Output filter parameters
        # Assume typical output LC filter
        l_out = 10e-6  # 10µH (typical)
        c_out = 500e-6  # 500µF (typical)

        # LC filter corner frequency
        f_lc = 1.0 / (2 * np.pi * np.sqrt(l_out * c_out))

        # Zero placement: typically at LC filter resonance
        f_z = f_lc

        # Pole placement: for phase boost
        f_p = f_crossover * 10  # High frequency pole for noise rejection

        # Component calculations
        # Assume C_COMP1 = 10nF (reasonable starting point)
        c_comp1 = 10e-9

        # R_COMP = 1 / (2π * f_z * C_COMP1)
        r_comp = 1.0 / (2 * np.pi * f_z * c_comp1)

        # C_COMP2 = 1 / (2π * f_p * R_COMP)
        c_comp2 = 1.0 / (2 * np.pi * f_p * r_comp)

        self.components.r_comp = r_comp
        self.components.c_comp1 = c_comp1
        self.components.c_comp2 = c_comp2

        return {
            'r_comp': r_comp,
            'c_comp1': c_comp1,
            'c_comp2': c_comp2,
            'f_zero': f_z,
            'f_pole': f_p,
            'f_crossover': f_crossover
        }

    def calculate_all_components(self, t_ss: float = 10e-3,
                                 f_crossover: float = None) -> UCC28951Components:
        """
        Calculate all component values for UCC28951 design

        Args:
            t_ss: Soft-start time (s)
            f_crossover: Loop crossover frequency (Hz)

        Returns:
            UCC28951Components with all calculated values
        """
        # Timing components
        self.calculate_timing_components()

        # Soft-start
        self.calculate_soft_start(t_ss)

        # Adaptive delay
        self.calculate_adaptive_delay()

        # Output voltage divider
        self.calculate_output_divider()

        # Current sense (if peak current mode)
        if self.power_stage.control_mode == ControlMode.PEAK_CURRENT_MODE:
            self.calculate_current_sense_resistor()

        # UVLO divider (with 10% hysteresis)
        v_uvlo_on = self.power_stage.v_in_min * 0.9
        v_uvlo_off = v_uvlo_on * 0.9
        self.calculate_uvlo_divider(v_uvlo_on, v_uvlo_off)

        # Compensation
        self.design_type2_compensation(f_crossover)

        return self.components

    def generate_bode_plot(self, f_min: float = 10.0, f_max: float = 1e6,
                           points: int = 1000) -> UCC28951LoopResponse:
        """
        Generate Bode plot for loop compensation

        Args:
            f_min: Minimum frequency (Hz)
            f_max: Maximum frequency (Hz)
            points: Number of frequency points

        Returns:
            UCC28951LoopResponse with frequency response data
        """
        # Generate frequency array (log scale)
        frequencies = np.logspace(np.log10(f_min), np.log10(f_max), points)
        omega = 2 * np.pi * frequencies

        # Power stage transfer function (simplified LC output filter model)
        l_out = 10e-6  # 10µH
        c_out = 500e-6  # 500µF
        r_load = self.power_stage.v_out / self.power_stage.i_out_max
        esr = 5e-3  # 5mΩ ESR

        # LC filter with ESR zero
        s = 1j * omega

        # Output filter transfer function
        z_esr = 1.0 / (s * c_out) + esr
        z_l = s * l_out
        h_power = z_esr / (z_esr + z_l + r_load)

        # PWM gain (simplified)
        k_pwm = self.power_stage.v_out / self.V_REF

        # Compensation network transfer function (Type II)
        # H_comp(s) = (1 + s*R_COMP*C_COMP1) / (s*C_COMP1 * (1 + s*R_COMP*C_COMP2))
        if self.components.c_comp1 > 0:
            z_comp = 1.0 / (2 * np.pi * self.components.r_comp * self.components.c_comp1)
            p_comp = 1.0 / (2 * np.pi * self.components.r_comp * self.components.c_comp2) if self.components.c_comp2 > 0 else 1e6

            h_comp = (1 + s / (2*np.pi*z_comp)) / (s / (2*np.pi*1e3) * (1 + s / (2*np.pi*p_comp)))
        else:
            h_comp = np.ones_like(s)

        # Total loop gain
        h_loop = k_pwm * h_power * h_comp

        # Convert to dB and degrees
        gain_db = 20 * np.log10(np.abs(h_loop))
        phase_deg = np.angle(h_loop) * 180 / np.pi

        # Find crossover frequency and margins
        # Crossover: where gain = 0 dB
        crossover_idx = np.argmin(np.abs(gain_db))
        f_crossover = frequencies[crossover_idx]
        phase_margin = 180 + phase_deg[crossover_idx]

        # Gain margin: gain at -180° phase
        phase_180_idx = np.argmin(np.abs(phase_deg + 180))
        gain_margin = -gain_db[phase_180_idx]

        response = UCC28951LoopResponse(
            frequencies=frequencies,
            gain_db=gain_db,
            phase_deg=phase_deg,
            f_crossover=f_crossover,
            phase_margin=phase_margin,
            gain_margin=gain_margin
        )

        return response

    def generate_bom(self) -> List[Dict[str, str]]:
        """
        Generate Bill of Materials (BOM) for UCC28951 design

        Returns:
            List of dictionaries with component information
        """
        bom = [
            {
                'Designator': 'U1',
                'Part Number': 'UCC28951',
                'Description': 'Phase-Shifted Full-Bridge Controller',
                'Manufacturer': 'Texas Instruments',
                'Value': '',
                'Package': 'TSSOP-20',
                'Quantity': '1'
            },
            {
                'Designator': 'RT',
                'Part Number': '',
                'Description': 'Timing Resistor',
                'Manufacturer': '',
                'Value': f'{self.components.r_t/1e3:.1f}k',
                'Package': '0603',
                'Quantity': '1'
            },
            {
                'Designator': 'CT',
                'Part Number': '',
                'Description': 'Timing Capacitor',
                'Manufacturer': '',
                'Value': f'{self.components.c_t*1e12:.0f}pF',
                'Package': '0603',
                'Quantity': '1'
            },
            {
                'Designator': 'CSS',
                'Part Number': '',
                'Description': 'Soft-Start Capacitor',
                'Manufacturer': '',
                'Value': f'{self.components.c_ss*1e9:.1f}nF',
                'Package': '0603',
                'Quantity': '1'
            },
            {
                'Designator': 'RADS',
                'Part Number': '',
                'Description': 'Adaptive Delay Set Resistor',
                'Manufacturer': '',
                'Value': f'{self.components.r_ads/1e3:.1f}k',
                'Package': '0603',
                'Quantity': '1'
            },
            {
                'Designator': 'RCOMP',
                'Part Number': '',
                'Description': 'Compensation Resistor',
                'Manufacturer': '',
                'Value': f'{self.components.r_comp/1e3:.1f}k',
                'Package': '0603',
                'Quantity': '1'
            },
            {
                'Designator': 'CCOMP1',
                'Part Number': '',
                'Description': 'Compensation Capacitor 1',
                'Manufacturer': '',
                'Value': f'{self.components.c_comp1*1e9:.1f}nF',
                'Package': '0603',
                'Quantity': '1'
            },
            {
                'Designator': 'CCOMP2',
                'Part Number': '',
                'Description': 'Compensation Capacitor 2',
                'Manufacturer': '',
                'Value': f'{self.components.c_comp2*1e12:.0f}pF',
                'Package': '0603',
                'Quantity': '1'
            },
            {
                'Designator': 'R_FB_UPPER',
                'Part Number': '',
                'Description': 'Feedback Upper Resistor',
                'Manufacturer': '',
                'Value': f'{self.components.r_upper/1e3:.1f}k',
                'Package': '0603',
                'Quantity': '1'
            },
            {
                'Designator': 'R_FB_LOWER',
                'Part Number': '',
                'Description': 'Feedback Lower Resistor',
                'Manufacturer': '',
                'Value': f'{self.components.r_lower/1e3:.1f}k',
                'Package': '0603',
                'Quantity': '1'
            },
            {
                'Designator': 'R_UVLO_UPPER',
                'Part Number': '',
                'Description': 'UVLO Upper Resistor',
                'Manufacturer': '',
                'Value': f'{self.components.r_uvlo_upper/1e3:.1f}k',
                'Package': '0603',
                'Quantity': '1'
            },
            {
                'Designator': 'R_UVLO_LOWER',
                'Part Number': '',
                'Description': 'UVLO Lower Resistor',
                'Manufacturer': '',
                'Value': f'{self.components.r_uvlo_lower/1e3:.1f}k',
                'Package': '0603',
                'Quantity': '1'
            }
        ]

        # Add current sense resistor if peak current mode
        if self.power_stage.control_mode == ControlMode.PEAK_CURRENT_MODE and self.components.r_cs > 0:
            bom.append({
                'Designator': 'RCS',
                'Part Number': '',
                'Description': 'Current Sense Resistor',
                'Manufacturer': '',
                'Value': f'{self.components.r_cs*1e3:.2f}mΩ',
                'Package': '2512',
                'Quantity': '1'
            })

        return bom


def format_component_value(value: float, unit: str = '') -> str:
    """
    Format component value with appropriate SI prefix

    Args:
        value: Component value
        unit: Unit string (Ω, F, H, etc.)

    Returns:
        Formatted string (e.g., "10kΩ", "100nF")
    """
    if value >= 1e6:
        return f'{value/1e6:.2f}M{unit}'
    elif value >= 1e3:
        return f'{value/1e3:.2f}k{unit}'
    elif value >= 1.0:
        return f'{value:.2f}{unit}'
    elif value >= 1e-3:
        return f'{value*1e3:.2f}m{unit}'
    elif value >= 1e-6:
        return f'{value*1e6:.2f}µ{unit}'
    elif value >= 1e-9:
        return f'{value*1e9:.2f}n{unit}'
    elif value >= 1e-12:
        return f'{value*1e12:.2f}p{unit}'
    else:
        return f'{value:.2e}{unit}'

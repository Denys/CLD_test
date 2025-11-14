"""
Circuit Parameters Data Classes for PSFB Loss Analysis

This module defines the input parameter interface for the PSFB loss analyzer.
All parameters are structured using dataclasses with type hints and validation.

Author: PSFB Loss Analysis Tool
Reference: Infineon "MOSFET Power Losses Calculation Using DataSheet Parameters"
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from enum import Enum
import json


class RectifierType(Enum):
    """Type of rectifier used on secondary side"""
    DIODE = "diode"
    SYNCHRONOUS_MOSFET = "synchronous_mosfet"


class CoolingMethod(Enum):
    """Cooling method for thermal analysis"""
    NATURAL_CONVECTION = "natural_convection"
    FORCED_AIR = "forced_air"
    LIQUID_COOLING = "liquid_cooling"


class CoreMaterial(Enum):
    """Transformer core material types"""
    FERRITE_3C95 = "3C95"
    FERRITE_3F3 = "3F3"
    FERRITE_N87 = "N87"
    FERRITE_N97 = "N97"
    NANOCRYSTALLINE = "nanocrystalline"


@dataclass
class VoltageRange:
    """Input or output voltage specification"""
    min: float  # Volts
    nominal: float  # Volts
    max: float  # Volts

    def __post_init__(self):
        if not (self.min <= self.nominal <= self.max):
            raise ValueError(f"Voltage range invalid: min={self.min}, nom={self.nominal}, max={self.max}")


@dataclass
class CircuitTopology:
    """
    PSFB converter circuit topology parameters

    Attributes:
        v_in: Input voltage range (V)
        v_out: Output voltage (V)
        p_out: Output power (W)
        f_sw: Switching frequency (Hz)
        phase_shift_min: Minimum phase shift angle (degrees, 0-180)
        phase_shift_max: Maximum phase shift angle (degrees, 0-180)
        n_phases: Number of interleaved phases (1-4)
        dead_time_primary: Dead time between primary MOSFETs (seconds)
        dead_time_secondary: Dead time for synchronous rectifiers (seconds, if applicable)
        transformer_turns_ratio: Primary:Secondary turns ratio (Np:Ns)
    """
    v_in: VoltageRange
    v_out: float
    p_out: float
    f_sw: float
    phase_shift_min: float = 0.0
    phase_shift_max: float = 180.0
    n_phases: int = 1
    dead_time_primary: float = 100e-9  # 100ns default
    dead_time_secondary: float = 50e-9  # 50ns default
    transformer_turns_ratio: float = 1.0  # Np/Ns

    def __post_init__(self):
        if not (1 <= self.n_phases <= 4):
            raise ValueError(f"Number of phases must be 1-4, got {self.n_phases}")
        if not (0 <= self.phase_shift_min <= self.phase_shift_max <= 180):
            raise ValueError(f"Phase shift range invalid: {self.phase_shift_min}-{self.phase_shift_max}")
        if self.f_sw <= 0:
            raise ValueError(f"Switching frequency must be positive, got {self.f_sw}")


@dataclass
class CapacitanceVsVoltage:
    """
    MOSFET capacitance vs drain-source voltage characteristic

    For accurate switching loss calculation, capacitances vary with VDS.
    Can be defined as discrete points or use simplified constant values.
    """
    # Option 1: Constant values (simplified)
    c_iss_constant: Optional[float] = None  # Input capacitance (F)
    c_oss_constant: Optional[float] = None  # Output capacitance (F)
    c_rss_constant: Optional[float] = None  # Reverse transfer capacitance (F)

    # Option 2: Voltage-dependent curves (more accurate)
    # Format: List of (V_DS, C_iss, C_oss, C_rss) tuples
    capacitance_curve: Optional[List[Tuple[float, float, float, float]]] = None

    def get_ciss(self, vds: float = 25.0) -> float:
        """Get input capacitance at specified VDS"""
        if self.c_iss_constant is not None:
            return self.c_iss_constant
        elif self.capacitance_curve:
            return self._interpolate_capacitance(vds, index=1)
        else:
            raise ValueError("No capacitance data provided")

    def get_coss(self, vds: float = 25.0) -> float:
        """Get output capacitance at specified VDS"""
        if self.c_oss_constant is not None:
            return self.c_oss_constant
        elif self.capacitance_curve:
            return self._interpolate_capacitance(vds, index=2)
        else:
            raise ValueError("No capacitance data provided")

    def get_crss(self, vds: float = 25.0) -> float:
        """Get reverse transfer capacitance at specified VDS"""
        if self.c_rss_constant is not None:
            return self.c_rss_constant
        elif self.capacitance_curve:
            return self._interpolate_capacitance(vds, index=3)
        else:
            raise ValueError("No capacitance data provided")

    def _interpolate_capacitance(self, vds: float, index: int) -> float:
        """Linear interpolation of capacitance from curve data"""
        if not self.capacitance_curve or len(self.capacitance_curve) < 2:
            raise ValueError("Insufficient capacitance curve data")

        # Find bracketing points
        for i in range(len(self.capacitance_curve) - 1):
            v1, *caps1 = self.capacitance_curve[i]
            v2, *caps2 = self.capacitance_curve[i + 1]

            if v1 <= vds <= v2:
                # Linear interpolation
                ratio = (vds - v1) / (v2 - v1) if v2 != v1 else 0
                return caps1[index - 1] + ratio * (caps2[index - 1] - caps1[index - 1])

        # Extrapolate if outside range
        if vds < self.capacitance_curve[0][0]:
            return self.capacitance_curve[0][index]
        else:
            return self.capacitance_curve[-1][index]


@dataclass
class MOSFETParameters:
    """
    MOSFET datasheet parameters for loss calculation

    Based on Infineon application note methodology.
    All parameters should be extracted from manufacturer datasheets.

    Attributes:
        part_number: MOSFET part number for reference
        v_dss: Drain-source voltage rating (V)
        i_d_continuous: Continuous drain current rating @ 25°C (A)

        # Conduction loss parameters (Section 2.1.1 of Infineon PDF)
        r_dson_25c: On-resistance @ VGS=10V, 25°C, typical (Ω)
        r_dson_25c_max: On-resistance @ VGS=10V, 25°C, maximum (Ω)
        r_dson_150c: On-resistance @ VGS=10V, 150°C, typical (Ω)
        r_dson_150c_max: On-resistance @ VGS=10V, 150°C, maximum (Ω)

        # Gate charge parameters (Section 2.2 of Infineon PDF)
        q_g: Total gate charge @ VDS=rated, VGS=10V (C)
        q_gs: Gate-source charge (C)
        q_gd: Gate-drain (Miller) charge (C)
        v_gs_plateau: Miller plateau voltage (V)

        # Capacitances
        capacitances: CapacitanceVsVoltage

        # Switching time parameters
        t_r: Rise time (s) - from datasheet test conditions
        t_f: Fall time (s) - from datasheet test conditions

        # Body diode parameters
        v_sd: Source-drain diode forward voltage @ I_SD (V)
        q_rr: Reverse recovery charge (C)
        t_rr: Reverse recovery time (s)

        # Thermal parameters
        r_th_jc: Junction-to-case thermal resistance (°C/W)
        t_j_max: Maximum junction temperature (°C)

        # Gate driver parameters
        v_gs_drive: Gate drive voltage (V, typically 10V or 12V)
        r_g_internal: Internal gate resistance (Ω)
        r_g_external: External gate resistance (Ω)
    """
    part_number: str
    v_dss: float
    i_d_continuous: float

    # RDS(on) temperature characteristics
    r_dson_25c: float
    r_dson_25c_max: float
    r_dson_150c: float
    r_dson_150c_max: float

    # Gate charge
    q_g: float
    q_gs: float
    q_gd: float
    v_gs_plateau: float = 5.0  # Typical value

    # Capacitances
    capacitances: CapacitanceVsVoltage = field(default_factory=lambda: CapacitanceVsVoltage())

    # Switching times
    t_r: float = 10e-9  # 10ns default
    t_f: float = 10e-9  # 10ns default

    # Body diode
    v_sd: float = 1.0  # Typical SiC or Si body diode
    q_rr: float = 0.0  # SiC has negligible Qrr
    t_rr: float = 0.0

    # Thermal
    r_th_jc: float = 1.0  # °C/W
    t_j_max: float = 175.0  # °C (SiC), 150°C (Si)

    # Gate drive
    v_gs_drive: float = 12.0  # V
    r_g_internal: float = 1.0  # Ω
    r_g_external: float = 5.0  # Ω

    @property
    def r_g_total(self) -> float:
        """Total gate resistance"""
        return self.r_g_internal + self.r_g_external

    @property
    def alpha_rdson(self) -> float:
        """
        Temperature coefficient α for RDS(on)

        Calculated from two-point data per Infineon PDF Section 2.1.1:
        R_DS(on)(Tj) = R_DS(on)_max(25°C) × [1 + α/100 × (Tj - 25)]

        Returns: Temperature coefficient in %/°C
        """
        if self.r_dson_25c_max == 0:
            return 0.0

        # Solve for alpha using two-point data
        # r_dson_150c_max / r_dson_25c_max = 1 + α/100 × (150 - 25)
        ratio = self.r_dson_150c_max / self.r_dson_25c_max
        alpha = 100 * (ratio - 1) / (150 - 25)
        return alpha


@dataclass
class DiodeParameters:
    """
    Rectifier diode parameters (for diode rectification option)

    Attributes:
        part_number: Diode part number
        v_rrm: Reverse repetitive maximum voltage (V)
        i_f_avg: Average forward current rating (A)
        v_f0: Forward voltage threshold (V)
        r_d: Dynamic forward resistance (Ω)
        q_rr: Reverse recovery charge (C)
        t_rr: Reverse recovery time (s)
        r_th_jc: Junction-to-case thermal resistance (°C/W)
        t_j_max: Maximum junction temperature (°C)
    """
    part_number: str
    v_rrm: float
    i_f_avg: float
    v_f0: float = 0.7  # Schottky ~0.4V, PN ~0.7V
    r_d: float = 0.01  # Ω
    q_rr: float = 0.0  # Schottky has negligible Qrr
    t_rr: float = 0.0
    r_th_jc: float = 2.0  # °C/W
    t_j_max: float = 150.0  # °C


@dataclass
class CoreGeometry:
    """
    Transformer core physical geometry

    Attributes:
        core_type: Core designation (e.g., "ETD39", "PQ40/40")
        effective_area: Core effective cross-sectional area (m²)
        effective_length: Core effective magnetic path length (m)
        effective_volume: Core effective volume (m³)
        window_area: Core window area for windings (m²)
        b_sat: Saturation flux density at operating temperature (T)
    """
    core_type: str
    effective_area: float  # A_e (m²)
    effective_length: float  # l_e (m)
    effective_volume: float  # V_e (m³)
    window_area: float  # W_a (m²)
    b_sat: float = 0.4  # Tesla (typical for ferrite at 100°C)


@dataclass
class CoreLossCoefficients:
    """
    Steinmetz equation coefficients for core loss calculation

    Core loss: P_v = k × f^α × B^β  (W/m³)

    These coefficients are material and temperature dependent.
    Should be extracted from manufacturer's core loss curves.

    Attributes:
        k: Steinmetz coefficient
        alpha: Frequency exponent
        beta: Flux density exponent
        temperature: Temperature at which coefficients are valid (°C)
    """
    k: float
    alpha: float
    beta: float
    temperature: float = 100.0  # °C


@dataclass
class WindingParameters:
    """
    Transformer winding specifications

    Attributes:
        n_turns: Number of turns
        wire_diameter: Wire diameter including insulation (m)
        wire_conductors: Number of parallel conductors (for Litz or multi-strand)
        dc_resistance: DC resistance @ 20°C (Ω)
        layers: Number of winding layers
        foil_winding: True if foil winding, False if round wire
    """
    n_turns: int
    wire_diameter: float  # meters
    wire_conductors: int = 1
    dc_resistance: float = 0.001  # Ω
    layers: int = 1
    foil_winding: bool = False

    @property
    def effective_diameter(self) -> float:
        """Effective diameter for skin effect calculation"""
        if self.wire_conductors > 1:
            # Litz wire approximation
            return self.wire_diameter / (self.wire_conductors ** 0.5)
        return self.wire_diameter


@dataclass
class TransformerParameters:
    """
    Complete transformer specification

    Attributes:
        core_geometry: Physical core dimensions
        core_material: Magnetic core material type
        core_loss_coefficients: Steinmetz equation parameters
        primary_winding: Primary winding specifications
        secondary_winding: Secondary winding specifications
        leakage_inductance: Leakage inductance referred to primary (H)
        magnetizing_inductance: Magnetizing inductance (H)
        isolation_capacitance: Primary-secondary capacitance (F)
    """
    core_geometry: CoreGeometry
    core_material: CoreMaterial
    core_loss_coefficients: CoreLossCoefficients
    primary_winding: WindingParameters
    secondary_winding: WindingParameters
    leakage_inductance: float  # H
    magnetizing_inductance: float  # H
    isolation_capacitance: float = 100e-12  # 100pF typical


@dataclass
class InductorParameters:
    """
    Output filter inductor parameters

    Attributes:
        inductance: Inductance value (H)
        dc_resistance: DC winding resistance (Ω)
        ac_resistance_100khz: AC resistance @ 100kHz (Ω) - optional
        core_loss_density: Core loss per unit volume (W/m³) - optional
        core_volume: Core volume (m³) - if core loss is specified
        current_rating: RMS current rating (A)
        saturation_current: DC current at which L drops 10% (A)
    """
    inductance: float  # H
    dc_resistance: float  # Ω
    ac_resistance_100khz: Optional[float] = None
    core_loss_density: Optional[float] = None
    core_volume: Optional[float] = None
    current_rating: float = 10.0  # A
    saturation_current: float = 15.0  # A


@dataclass
class CapacitorParameters:
    """
    Input/Output filter capacitor parameters

    Attributes:
        capacitance: Capacitance value (F)
        voltage_rating: Voltage rating (V)
        esr: Equivalent series resistance @ switching frequency (Ω)
        esl: Equivalent series inductance (H) - for high-frequency analysis
        ripple_current_rating: RMS ripple current rating @ 100kHz (A)
    """
    capacitance: float  # F
    voltage_rating: float  # V
    esr: float = 0.01  # Ω
    esl: float = 10e-9  # 10nH typical
    ripple_current_rating: float = 5.0  # A


@dataclass
class ThermalParameters:
    """
    Thermal management and ambient conditions

    Attributes:
        t_ambient: Ambient temperature (°C)
        cooling_method: Type of cooling employed
        forced_air_cfm: Air flow rate if forced air cooling (CFM)
        heatsink_r_th_ca: Heatsink case-to-ambient thermal resistance (°C/W)
        thermal_interface_r_th: Thermal interface material resistance (°C/W)
        target_t_j_max: Target maximum junction temperature for design (°C)
    """
    t_ambient: float = 50.0  # °C (marine environment can be hot)
    cooling_method: CoolingMethod = CoolingMethod.FORCED_AIR
    forced_air_cfm: float = 10.0  # CFM
    heatsink_r_th_ca: float = 5.0  # °C/W
    thermal_interface_r_th: float = 0.2  # °C/W
    target_t_j_max: float = 125.0  # °C (with safety margin)


@dataclass
class OperatingConditions:
    """
    Operating point and analysis conditions

    Attributes:
        load_percentage: Load as percentage of rated power (10-100%)
        input_voltage: Actual input voltage for this operating point (V)
        output_current: Output current (A)
        phase_shift_angle: Phase shift angle for this operating point (degrees)
        zvs_achieved_primary: True if ZVS is achieved on primary side
    """
    load_percentage: float = 100.0
    input_voltage: Optional[float] = None  # If None, use nominal
    output_current: Optional[float] = None  # If None, calculated from P_out
    phase_shift_angle: float = 90.0  # degrees
    zvs_achieved_primary: bool = True  # Assume ZVS unless proven otherwise


@dataclass
class ComponentSet:
    """
    Complete component selection for PSFB converter

    Defines all active and passive components in the power stage.

    Attributes:
        primary_mosfets: Primary side MOSFETs (Q1-Q4 typically identical)
        secondary_rectifier_type: Diode or synchronous MOSFET rectification
        secondary_mosfets: Secondary side SR MOSFETs (if SR used)
        secondary_diodes: Secondary side diodes (if diode rectification)
        transformer: Main power transformer
        output_inductor: Output filter inductor
        input_capacitor: Input filter capacitor
        output_capacitor: Output filter capacitor
    """
    primary_mosfets: MOSFETParameters
    secondary_rectifier_type: RectifierType
    transformer: TransformerParameters
    output_inductor: InductorParameters
    input_capacitor: CapacitorParameters
    output_capacitor: CapacitorParameters

    # Optional components depending on rectifier type
    secondary_mosfets: Optional[MOSFETParameters] = None
    secondary_diodes: Optional[DiodeParameters] = None

    def __post_init__(self):
        """Validate component selection consistency"""
        if self.secondary_rectifier_type == RectifierType.SYNCHRONOUS_MOSFET:
            if self.secondary_mosfets is None:
                raise ValueError("Secondary MOSFETs must be specified for SR rectification")
        elif self.secondary_rectifier_type == RectifierType.DIODE:
            if self.secondary_diodes is None:
                raise ValueError("Secondary diodes must be specified for diode rectification")


@dataclass
class PSFBConfiguration:
    """
    Complete PSFB converter configuration

    This is the top-level container for all analysis inputs.

    Attributes:
        project_name: Name/description of this design
        topology: Circuit topology parameters
        components: Component selection
        thermal: Thermal management parameters
        operating_point: Operating conditions for analysis
    """
    project_name: str
    topology: CircuitTopology
    components: ComponentSet
    thermal: ThermalParameters
    operating_point: OperatingConditions

    def to_dict(self) -> dict:
        """Convert configuration to dictionary for JSON export"""
        def convert(obj):
            if isinstance(obj, Enum):
                return obj.value
            elif hasattr(obj, '__dataclass_fields__'):
                return {k: convert(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert(item) for item in obj]
            else:
                return obj

        return convert(self)

    def to_json(self, filepath: str, indent: int = 2):
        """Export configuration to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> 'PSFBConfiguration':
        """Load configuration from dictionary"""
        # This would need custom deserialization logic
        # Implementation depends on whether we use JSON or YAML
        raise NotImplementedError("Use from_json() or from_yaml() methods")

    @classmethod
    def from_json(cls, filepath: str) -> 'PSFBConfiguration':
        """Load configuration from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def validate(self) -> List[str]:
        """
        Validate configuration for physical consistency

        Returns:
            List of validation warnings/errors (empty if all OK)
        """
        issues = []

        # Check voltage relationships
        v_in_max = self.topology.v_in.max
        primary_vdss = self.components.primary_mosfets.v_dss
        if v_in_max > 0.8 * primary_vdss:
            issues.append(f"Primary MOSFET voltage rating ({primary_vdss}V) "
                         f"insufficient for V_in_max ({v_in_max}V). "
                         f"Recommend 20% derating minimum.")

        # Check current ratings
        i_out_max = self.topology.p_out / self.topology.v_out
        if i_out_max > self.components.output_inductor.saturation_current:
            issues.append(f"Output inductor saturation current "
                         f"({self.components.output_inductor.saturation_current}A) "
                         f"insufficient for max output current ({i_out_max}A)")

        # Check transformer turns ratio vs voltage
        n = self.topology.transformer_turns_ratio
        v_in_nom = self.topology.v_in.nominal
        v_out = self.topology.v_out
        expected_n = v_in_nom / (2 * v_out)  # PSFB volt-second balance
        if abs(n - expected_n) / expected_n > 0.2:  # 20% tolerance
            issues.append(f"Transformer turns ratio ({n:.2f}) deviates >20% "
                         f"from expected value ({expected_n:.2f})")

        # Check thermal margins
        if self.thermal.target_t_j_max > self.components.primary_mosfets.t_j_max:
            issues.append(f"Target Tj ({self.thermal.target_t_j_max}°C) exceeds "
                         f"MOSFET rating ({self.components.primary_mosfets.t_j_max}°C)")

        return issues

    def __str__(self) -> str:
        """Human-readable summary of configuration"""
        return f"""
PSFB Configuration: {self.project_name}
{'='*60}
Power:      {self.topology.p_out/1000:.2f} kW
Input:      {self.topology.v_in.min}-{self.topology.v_in.max}V (nom: {self.topology.v_in.nominal}V)
Output:     {self.topology.v_out}V
Frequency:  {self.topology.f_sw/1000:.1f} kHz
Phases:     {self.topology.n_phases}

Primary MOSFET:     {self.components.primary_mosfets.part_number}
Secondary Rectifier: {self.components.secondary_rectifier_type.value}
Transformer Core:   {self.components.transformer.core_geometry.core_type} ({self.components.transformer.core_material.value})

Operating Point:    {self.operating_point.load_percentage}% load, {self.operating_point.phase_shift_angle}° phase shift
Ambient Temp:       {self.thermal.t_ambient}°C
"""


# Validation helper function
def validate_configuration(config: PSFBConfiguration) -> bool:
    """
    Validate a PSFB configuration and print issues

    Args:
        config: PSFB configuration to validate

    Returns:
        True if no critical issues found
    """
    issues = config.validate()

    if not issues:
        print("✓ Configuration validation passed")
        return True
    else:
        print("⚠ Configuration validation warnings:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        return False

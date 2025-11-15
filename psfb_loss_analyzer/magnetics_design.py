"""
Magnetic Component Design Module for PSFB Converters

Implements industry-standard magnetic design methods:
- Kg (Area Product) method from McLyman's Transformer and Inductor Design Handbook
- Kg_fe method from Erickson & Maksimovic "Fundamentals of Power Electronics 3ed"
- Steinmetz core loss calculation with temperature compensation
- Dowell method for AC winding resistance
- Optimization for ZVS operation at light loads (10-50%)

Design References:
- McLyman, "Transformer and Inductor Design Handbook" 4th Ed.
- Erickson & Maksimovic, "Fundamentals of Power Electronics" 3rd Ed., Appendix B
- Infineon "MOSFET Power Losses Calculation Using the DataSheet Parameters"
- UCC28951 Phase-Shifted Full-Bridge Controller Datasheet

Author: PSFB Loss Analysis Tool
Version: 0.3.0
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict
from enum import Enum
import numpy as np

try:
    from .circuit_params import (
        CoreGeometry,
        CoreLossCoefficients,
        CoreMaterial,
        WindingParameters,
        TransformerParameters,
        InductorParameters,
    )
    from .core_database import (
        get_core_geometry,
        get_core_loss_coefficients,
        list_available_cores,
    )
except ImportError:
    from circuit_params import (
        CoreGeometry,
        CoreLossCoefficients,
        CoreMaterial,
        WindingParameters,
        TransformerParameters,
        InductorParameters,
    )
    from core_database import (
        get_core_geometry,
        get_core_loss_coefficients,
        list_available_cores,
    )


# ============================================================================
# Physical Constants and Material Properties
# ============================================================================

# Copper resistivity at different temperatures (Ω⋅m)
RHO_COPPER_20C = 1.68e-8  # 20°C
RHO_COPPER_100C = 2.14e-8  # 100°C
COPPER_TEMP_COEFF = 0.00393  # Temperature coefficient (1/°C)

# Current density limits (A/mm²)
J_MAX_NATURAL_CONVECTION = 2.5  # Natural convection
J_MAX_FORCED_AIR = 5.0  # Forced air cooling
J_MAX_LIQUID = 10.0  # Liquid cooling

# Window utilization factor (Ku)
KU_SIMPLE_BOBBIN = 0.4  # Simple bobbin winding
KU_CAREFUL_LAYERED = 0.5  # Careful layered winding
KU_PROFESSIONAL = 0.6  # Professional manufacturing

# Flux density limits (Tesla)
B_SAT_FERRITE = 0.5  # Ferrite saturation (conservative)
B_MAX_FERRITE_100KHZ = 0.3  # Maximum for low loss at 100kHz
B_MAX_FERRITE_150KHZ = 0.25  # Maximum for low loss at 150kHz


class WindingType(Enum):
    """Winding configuration type"""
    SINGLE_LAYER = "single_layer"
    MULTI_LAYER = "multi_layer"
    FOIL = "foil"
    LITZ = "litz"


@dataclass
class MagneticDesignSpec:
    """Specification for magnetic component design"""
    # Power and operating conditions
    power: float  # Power rating (W)
    frequency: float  # Switching frequency (Hz)
    temp_ambient: float = 40.0  # Ambient temperature (°C)
    temp_rise_max: float = 60.0  # Maximum temperature rise (°C)

    # Electrical specifications
    voltage_primary: Optional[float] = None  # Primary voltage (V) - for transformers
    voltage_secondary: Optional[float] = None  # Secondary voltage (V) - for transformers
    current_primary_rms: Optional[float] = None  # Primary RMS current (A)
    current_secondary_rms: Optional[float] = None  # Secondary RMS current (A)
    inductance_target: Optional[float] = None  # Target inductance (H) - for inductors
    current_dc: Optional[float] = None  # DC current (A) - for inductors
    current_ripple_pp: Optional[float] = None  # Peak-to-peak ripple current (A)

    # Design constraints
    current_density_max: float = J_MAX_FORCED_AIR  # Maximum current density (A/mm²)
    window_utilization: float = KU_CAREFUL_LAYERED  # Window utilization factor
    flux_density_max: float = B_MAX_FERRITE_100KHZ  # Maximum flux density (T)
    core_material: CoreMaterial = CoreMaterial.FERRITE_3C95  # Core material

    # ZVS requirements (for resonant inductors)
    enable_light_load_zvs: bool = False  # Enable light load ZVS optimization
    min_load_percentage: float = 10.0  # Minimum load for ZVS (%)


@dataclass
class WindingDesign:
    """Complete winding design result"""
    n_turns: int  # Number of turns
    wire_diameter: float  # Wire diameter including insulation (mm)
    wire_diameter_bare: float  # Bare wire diameter (mm)
    n_strands: int  # Number of parallel strands (for Litz or parallel)
    strand_diameter: float  # Individual strand diameter (mm) for Litz
    n_layers: int  # Number of winding layers
    mlT: float  # Mean length per turn (m)
    resistance_dc: float  # DC resistance (Ω)
    resistance_ac: float  # AC resistance including skin/proximity effects (Ω)
    copper_loss: float  # Copper loss at rated current (W)
    wire_type: WindingType  # Winding type
    current_density: float  # Actual current density (A/mm²)


@dataclass
class MagneticDesignResult:
    """Complete magnetic component design result"""
    # Core selection
    core_name: str
    core_geometry: CoreGeometry
    core_material: CoreMaterial
    core_loss_coefficients: CoreLossCoefficients

    # Magnetic design
    n_primary: int  # Primary turns (or total turns for inductor)
    n_secondary: Optional[int] = None  # Secondary turns (transformers only)
    turns_ratio: Optional[float] = None  # n = N_pri / N_sec

    # Flux and inductance
    flux_density_peak: float = 0.0  # Peak flux density (T)
    flux_density_ac: float = 0.0  # AC flux density for core loss (T)
    inductance_magnetizing: Optional[float] = None  # Magnetizing inductance (H)
    inductance_leakage: Optional[float] = None  # Leakage inductance (H)

    # Winding designs
    primary_winding: WindingDesign
    secondary_winding: Optional[WindingDesign] = None

    # Loss breakdown
    core_loss: float = 0.0  # Core loss (W)
    copper_loss_primary: float = 0.0  # Primary copper loss (W)
    copper_loss_secondary: float = 0.0  # Secondary copper loss (W)
    total_loss: float = 0.0  # Total loss (W)
    efficiency: float = 0.0  # Efficiency (%)

    # Thermal
    temp_rise_estimate: float = 0.0  # Estimated temperature rise (°C)

    # Design metrics
    kg_value: float = 0.0  # Kg geometrical constant
    area_product: float = 0.0  # Wa × Ac (m⁴)
    window_utilization_actual: float = 0.0  # Actual Ku achieved


# ============================================================================
# Kg Method (McLyman) - Area Product Approach
# ============================================================================

def calculate_kg_geometrical_constant(core: CoreGeometry) -> float:
    """
    Calculate Kg geometrical constant for a given core.

    From McLyman: Kg = (Wa × Ac)² / MLT
    Where:
        Wa = window area (m²)
        Ac = core cross-sectional area (m²)
        MLT = mean length per turn (m)

    Args:
        core: Core geometry parameters

    Returns:
        Kg geometrical constant (m⁵)
    """
    wa = core.window_area  # m²
    ac = core.core_area  # m²
    mlt = core.mean_length_turn  # m

    kg = (wa * ac) ** 2 / mlt

    return kg


def calculate_required_kg(
    power: float,
    frequency: float,
    flux_density_max: float,
    current_density_max: float,
    window_utilization: float = KU_CAREFUL_LAYERED,
    topology_factor: float = 4.44,  # 4.44 for transformer, 4.0 for inductor
) -> float:
    """
    Calculate required Kg based on power and operating conditions.

    From McLyman Chapter 3:
    Kg = (P_t × 10⁴) / (K_u × K_t × f × B_max × J)

    Where:
        P_t = apparent power (VA)
        K_u = window utilization factor (typically 0.4-0.6)
        K_t = topology factor (4.44 for transformer, 4.0 for inductor)
        f = frequency (Hz)
        B_max = maximum flux density (T)
        J = current density (A/m² = A/mm² × 10⁶)

    Args:
        power: Power rating (W)
        frequency: Switching frequency (Hz)
        flux_density_max: Maximum flux density (T)
        current_density_max: Maximum current density (A/mm²)
        window_utilization: Window utilization factor Ku (0-1)
        topology_factor: 4.44 for transformer, 4.0 for inductor

    Returns:
        Required Kg (m⁵)
    """
    # Convert current density from A/mm² to A/m²
    j_si = current_density_max * 1e6  # A/m²

    # McLyman formula (with 10⁴ factor for unit conversion)
    kg_required = (power * 1e4) / (
        window_utilization * topology_factor * frequency * flux_density_max * j_si
    )

    return kg_required


def calculate_kg_fe(
    power: float,
    frequency: float,
    flux_density_ac: float,
    current_density: float,
    core_loss_density: float,
    copper_fill_factor: float = KU_CAREFUL_LAYERED,
) -> float:
    """
    Calculate required Kg using the Kg_fe method from Erickson & Maksimovic.

    From "Fundamentals of Power Electronics" 3rd Ed., Appendix B:
    This method accounts for both core and copper losses more explicitly.

    Kg_fe ≈ (2 × P_out) / (f × ΔB × J × K_u × (P_fe/V_e)^(1/2))

    Where:
        P_out = output power (W)
        f = frequency (Hz)
        ΔB = AC flux density swing (T)
        J = current density (A/m²)
        K_u = copper fill factor
        P_fe/V_e = core loss per unit volume (W/m³)

    Args:
        power: Output power (W)
        frequency: Operating frequency (Hz)
        flux_density_ac: AC flux density swing (T)
        current_density: Current density (A/mm²)
        core_loss_density: Core loss per unit volume (W/m³)
        copper_fill_factor: Copper fill factor (0-1)

    Returns:
        Required Kg_fe (m⁵)
    """
    j_si = current_density * 1e6  # Convert A/mm² to A/m²

    # Erickson & Maksimovic Kg_fe formula
    kg_fe = (2.0 * power) / (
        frequency * flux_density_ac * j_si * copper_fill_factor * np.sqrt(core_loss_density)
    )

    return kg_fe


def select_core_by_kg(
    kg_required: float,
    core_family: str = "PQ",
    material: CoreMaterial = CoreMaterial.FERRITE_3C95,
    margin: float = 1.2,
) -> Tuple[str, CoreGeometry, float]:
    """
    Select appropriate core based on required Kg value.

    Args:
        kg_required: Required Kg geometrical constant (m⁵)
        core_family: Core family ("PQ", "ETD", "E")
        material: Core material
        margin: Safety margin (1.2 = 20% margin)

    Returns:
        Tuple of (core_name, core_geometry, kg_actual)
    """
    kg_target = kg_required * margin

    # Get all available cores of the specified family
    all_cores = list_available_cores()
    family_cores = [c for c in all_cores if c.upper().startswith(core_family.upper())]

    if not family_cores:
        raise ValueError(f"No cores found in family '{core_family}'")

    # Calculate Kg for each core and find best match
    best_core = None
    best_kg = 0
    min_excess = float('inf')

    for core_name in family_cores:
        core_geom = get_core_geometry(core_name)
        kg = calculate_kg_geometrical_constant(core_geom)

        # Find smallest core that meets requirement
        if kg >= kg_target:
            excess = kg - kg_target
            if excess < min_excess:
                min_excess = excess
                best_core = core_name
                best_kg = kg

    # If no core is large enough, select the largest available
    if best_core is None:
        for core_name in family_cores:
            core_geom = get_core_geometry(core_name)
            kg = calculate_kg_geometrical_constant(core_geom)
            if kg > best_kg:
                best_kg = kg
                best_core = core_name

        print(f"Warning: No core in '{core_family}' family meets Kg requirement.")
        print(f"  Required: {kg_target:.2e} m⁵, Largest available: {best_kg:.2e} m⁵")

    core_geometry = get_core_geometry(best_core)

    return best_core, core_geometry, best_kg


# ============================================================================
# Winding Design
# ============================================================================

def calculate_number_of_turns(
    voltage: float,
    frequency: float,
    flux_density_ac: float,
    core_area: float,
    waveform_factor: float = 4.0,
) -> int:
    """
    Calculate required number of turns using Faraday's law.

    For inductors (buck/boost):
        V = L × di/dt  →  N = (V × Δt) / (B × Ac)
        For square wave: N = V / (4 × f × B × Ac)

    For transformers:
        V = N × dΦ/dt  →  N = V / (4.44 × f × B × Ac)  [sinusoidal]
        For square wave: N = V / (4 × f × B × Ac)

    Args:
        voltage: Applied voltage (V)
        frequency: Operating frequency (Hz)
        flux_density_ac: AC flux density swing (T)
        core_area: Core cross-sectional area (m²)
        waveform_factor: 4.44 for sinusoidal, 4.0 for square wave

    Returns:
        Number of turns (integer)
    """
    # Faraday's law: V = K × N × f × B × Ac
    n_turns_float = voltage / (waveform_factor * frequency * flux_density_ac * core_area)

    # Round up to nearest integer
    n_turns = int(np.ceil(n_turns_float))

    # Minimum 2 turns for practical construction
    n_turns = max(n_turns, 2)

    return n_turns


def calculate_wire_diameter(
    current_rms: float,
    current_density: float,
    n_parallel: int = 1,
) -> Tuple[float, float, float]:
    """
    Calculate wire diameter based on current and current density.

    Args:
        current_rms: RMS current (A)
        current_density: Maximum current density (A/mm²)
        n_parallel: Number of parallel strands

    Returns:
        Tuple of (total_area_mm2, bare_diameter_mm, insulated_diameter_mm)
    """
    # Total copper area required
    area_total = current_rms / current_density  # mm²

    # Area per strand
    area_per_strand = area_total / n_parallel  # mm²

    # Bare wire diameter
    d_bare = 2.0 * np.sqrt(area_per_strand / np.pi)  # mm

    # Insulated diameter (typical insulation adds 0.05-0.1mm)
    insulation_thickness = min(0.05 + 0.02 * d_bare, 0.15)  # mm
    d_insulated = d_bare + 2 * insulation_thickness  # mm

    return area_total, d_bare, d_insulated


def calculate_dc_resistance(
    n_turns: int,
    mlt: float,
    wire_area: float,
    temp: float = 100.0,
) -> float:
    """
    Calculate DC resistance of winding.

    R_dc = ρ × l / A = ρ × (N × MLT) / A

    Args:
        n_turns: Number of turns
        mlt: Mean length per turn (m)
        wire_area: Wire cross-sectional area (mm²)
        temp: Operating temperature (°C)

    Returns:
        DC resistance (Ω)
    """
    # Copper resistivity at temperature
    rho_20 = RHO_COPPER_20C  # Ω⋅m at 20°C
    rho_temp = rho_20 * (1 + COPPER_TEMP_COEFF * (temp - 20))

    # Total wire length
    length = n_turns * mlt  # m

    # Convert area to m²
    area_m2 = wire_area * 1e-6  # m²

    # Calculate resistance
    r_dc = rho_temp * length / area_m2  # Ω

    return r_dc


def calculate_skin_depth(frequency: float, temp: float = 100.0) -> float:
    """
    Calculate skin depth for copper at given frequency.

    δ = √(ρ / (π × μ₀ × μᵣ × f))

    For copper: μᵣ ≈ 1

    Args:
        frequency: Operating frequency (Hz)
        temp: Operating temperature (°C)

    Returns:
        Skin depth (mm)
    """
    mu_0 = 4 * np.pi * 1e-7  # Permeability of free space (H/m)
    mu_r = 1.0  # Relative permeability of copper

    # Copper resistivity at temperature
    rho_20 = RHO_COPPER_20C
    rho_temp = rho_20 * (1 + COPPER_TEMP_COEFF * (temp - 20))

    # Skin depth
    delta = np.sqrt(rho_temp / (np.pi * mu_0 * mu_r * frequency))

    # Convert to mm
    delta_mm = delta * 1000

    return delta_mm


def calculate_ac_resistance_dowell(
    r_dc: float,
    frequency: float,
    wire_diameter: float,
    n_layers: int,
    temp: float = 100.0,
) -> float:
    """
    Calculate AC resistance using Dowell's method.

    Accounts for skin effect and proximity effect in multi-layer windings.

    From Dowell's equation:
    R_ac / R_dc = Δ × [sinh(2Δ) + sin(2Δ)] / [cosh(2Δ) - cos(2Δ)]
                  + (2/3) × (m² - 1) × Δ × [sinh(Δ) - sin(Δ)] / [cosh(Δ) + cos(Δ)]

    Where:
        Δ = d / (2 × δ)  (wire diameter / (2 × skin depth))
        m = number of layers

    Args:
        r_dc: DC resistance (Ω)
        frequency: Operating frequency (Hz)
        wire_diameter: Bare wire diameter (mm)
        n_layers: Number of winding layers
        temp: Operating temperature (°C)

    Returns:
        AC resistance (Ω)
    """
    # Calculate skin depth
    delta = calculate_skin_depth(frequency, temp)  # mm

    # Dowell parameter
    Delta = wire_diameter / (2 * delta)

    # Avoid numerical issues for very small Delta
    if Delta < 0.01:
        return r_dc  # Negligible skin/proximity effects

    # Skin effect term (applies to all windings)
    sinh_2d = np.sinh(2 * Delta)
    sin_2d = np.sin(2 * Delta)
    cosh_2d = np.cosh(2 * Delta)
    cos_2d = np.cos(2 * Delta)

    if abs(cosh_2d - cos_2d) < 1e-10:
        F_r_skin = 1.0  # Avoid division by zero
    else:
        F_r_skin = Delta * (sinh_2d + sin_2d) / (cosh_2d - cos_2d)

    # Proximity effect term (multi-layer windings)
    if n_layers > 1:
        sinh_d = np.sinh(Delta)
        sin_d = np.sin(Delta)
        cosh_d = np.cosh(Delta)
        cos_d = np.cos(Delta)

        if abs(cosh_d + cos_d) < 1e-10:
            F_r_prox = 0.0
        else:
            F_r_prox = (2.0 / 3.0) * (n_layers**2 - 1) * Delta * (sinh_d - sin_d) / (cosh_d + cos_d)
    else:
        F_r_prox = 0.0

    # Total AC resistance factor
    F_r = F_r_skin + F_r_prox

    # Ensure reasonable bounds (1.0 to 100)
    F_r = max(1.0, min(F_r, 100.0))

    r_ac = r_dc * F_r

    return r_ac


def design_winding(
    current_rms: float,
    n_turns: int,
    mlt: float,
    frequency: float,
    current_density_max: float = J_MAX_FORCED_AIR,
    n_layers_target: int = 1,
    use_litz: bool = False,
    temp: float = 100.0,
) -> WindingDesign:
    """
    Complete winding design with wire selection and loss calculation.

    Args:
        current_rms: RMS current through winding (A)
        n_turns: Number of turns
        mlt: Mean length per turn (m)
        frequency: Operating frequency (Hz)
        current_density_max: Maximum current density (A/mm²)
        n_layers_target: Target number of layers (1 for single-layer)
        use_litz: Use Litz wire for high-frequency applications
        temp: Operating temperature (°C)

    Returns:
        WindingDesign with complete specifications
    """
    # Calculate wire diameter
    area_total, d_bare, d_insulated = calculate_wire_diameter(
        current_rms, current_density_max, n_parallel=1
    )

    # Check if Litz wire should be used (skin depth criterion)
    skin_depth = calculate_skin_depth(frequency, temp)

    if use_litz or (d_bare > 2 * skin_depth and frequency > 50e3):
        # Use Litz wire: multiple small strands
        strand_diameter = min(skin_depth * 1.5, 0.2)  # mm, max 0.2mm
        n_strands = int(np.ceil(area_total / (np.pi * (strand_diameter / 2)**2)))
        n_strands = max(n_strands, 10)  # Minimum 10 strands for Litz

        # Recalculate actual area
        area_actual = n_strands * np.pi * (strand_diameter / 2)**2
        d_insulated_bundle = np.sqrt(4 * area_actual / np.pi) * 1.5  # Bundle diameter with spacing

        wire_type = WindingType.LITZ
        d_bare_actual = np.sqrt(4 * area_actual / np.pi)
    else:
        # Use solid wire
        n_strands = 1
        strand_diameter = d_bare
        d_bare_actual = d_bare
        area_actual = area_total
        d_insulated_bundle = d_insulated
        wire_type = WindingType.SINGLE_LAYER if n_layers_target == 1 else WindingType.MULTI_LAYER

    # Calculate DC resistance
    r_dc = calculate_dc_resistance(n_turns, mlt, area_actual, temp)

    # Calculate AC resistance (Dowell method)
    if wire_type == WindingType.LITZ:
        # Litz wire: reduced proximity effect
        r_ac = r_dc * (1.0 + 0.1 * (d_bare_actual / skin_depth)**2)
    else:
        r_ac = calculate_ac_resistance_dowell(r_dc, frequency, d_bare_actual, n_layers_target, temp)

    # Copper loss
    copper_loss = r_ac * current_rms**2

    # Actual current density
    current_density_actual = current_rms / area_actual

    return WindingDesign(
        n_turns=n_turns,
        wire_diameter=d_insulated_bundle,
        wire_diameter_bare=d_bare_actual,
        n_strands=n_strands,
        strand_diameter=strand_diameter,
        n_layers=n_layers_target,
        mlT=mlt,
        resistance_dc=r_dc,
        resistance_ac=r_ac,
        copper_loss=copper_loss,
        wire_type=wire_type,
        current_density=current_density_actual,
    )


# ============================================================================
# Core Loss Calculation
# ============================================================================

def calculate_core_loss_steinmetz(
    core: CoreGeometry,
    coefficients: CoreLossCoefficients,
    frequency: float,
    flux_density_ac: float,
) -> float:
    """
    Calculate core loss using Steinmetz equation.

    P_v = k × f^α × B^β  (W/m³)
    P_core = P_v × V_e

    Args:
        core: Core geometry
        coefficients: Steinmetz coefficients (k, α, β)
        frequency: Operating frequency (Hz)
        flux_density_ac: AC flux density (T)

    Returns:
        Core loss (W)
    """
    # Steinmetz equation: P_v = k × f^α × B^β
    p_v = coefficients.k * (frequency ** coefficients.alpha) * (flux_density_ac ** coefficients.beta)

    # Total core loss
    p_core = p_v * core.volume  # W

    return p_core


# ============================================================================
# Helper Functions
# ============================================================================

def estimate_temperature_rise(
    total_loss: float,
    surface_area: float,
    cooling_coefficient: float = 10.0,
) -> float:
    """
    Estimate temperature rise using simple thermal resistance model.

    ΔT = P / (h × A)

    Where:
        h = heat transfer coefficient (W/m²⋅K)
            Natural convection: ~5-10 W/m²⋅K
            Forced air: ~20-50 W/m²⋅K
        A = surface area (m²)

    Args:
        total_loss: Total power dissipation (W)
        surface_area: Surface area for heat transfer (m²)
        cooling_coefficient: Heat transfer coefficient (W/m²⋅K)

    Returns:
        Temperature rise (°C)
    """
    temp_rise = total_loss / (cooling_coefficient * surface_area)
    return temp_rise


def calculate_window_utilization(
    primary_winding: WindingDesign,
    window_area: float,
    secondary_winding: Optional[WindingDesign] = None,
) -> float:
    """
    Calculate actual window utilization factor.

    Ku = (Area of copper) / (Window area)

    Args:
        primary_winding: Primary winding design
        window_area: Available window area (m²)
        secondary_winding: Secondary winding design (optional)

    Returns:
        Window utilization factor (0-1)
    """
    # Primary copper area
    area_primary = (np.pi * (primary_winding.wire_diameter / 2000)**2 *
                   primary_winding.n_turns * primary_winding.n_strands)

    # Secondary copper area
    if secondary_winding:
        area_secondary = (np.pi * (secondary_winding.wire_diameter / 2000)**2 *
                         secondary_winding.n_turns * secondary_winding.n_strands)
    else:
        area_secondary = 0.0

    # Total copper area
    area_copper_total = area_primary + area_secondary

    # Window utilization
    ku = area_copper_total / window_area

    return ku


# ============================================================================
# Module Information
# ============================================================================

if __name__ == "__main__":
    print("PSFB Loss Analyzer - Magnetic Component Design Module")
    print("=" * 70)
    print()
    print("This module provides magnetic design functions based on:")
    print("  - McLyman's Kg (Area Product) method")
    print("  - Erickson & Maksimovic Kg_fe method")
    print("  - Steinmetz core loss calculation")
    print("  - Dowell AC resistance calculation")
    print()
    print("Example usage:")
    print()
    print("  # Design a transformer")
    print("  spec = MagneticDesignSpec(")
    print("      power=2200.0,")
    print("      frequency=100e3,")
    print("      voltage_primary=400.0,")
    print("      voltage_secondary=250.0,")
    print("  )")
    print()
    print("Use the specific design functions:")
    print("  - resonant_inductor_design.py")
    print("  - transformer_design.py")
    print("  - output_inductor_design.py")
    print()

"""
Magnetic Core Database

Pre-defined core geometries and loss coefficients for common transformer cores
used in PSFB converters.

References:
- TDK "Large PQ series TDK PQ60x42 to PQ107x87x70" datasheet
- Ferroxcube soft ferrite catalog
- EPCOS/TDK ferrite materials data

Author: PSFB Loss Analysis Tool
"""

from circuit_params import CoreGeometry, CoreLossCoefficients, CoreMaterial
from typing import Dict, Optional


# =============================================================================
# TDK PQ CORES (Large Power Cores)
# Reference: TDK "Large PQ series" datasheet
# =============================================================================

TDK_PQ_CORES: Dict[str, CoreGeometry] = {
    # PQ 60/42 - Suitable for 3-5kW PSFB
    "PQ60/42": CoreGeometry(
        core_type="PQ60/42",
        effective_area=630e-6,      # 630 mm² = 630e-6 m²
        effective_length=147e-3,     # 147 mm = 0.147 m
        effective_volume=92.6e-6,    # 92.6 cm³ = 92.6e-6 m³
        window_area=585e-6,          # 585 mm² window area
        b_sat=0.39                   # 0.39T @ 100°C for PC95 ferrite
    ),

    # PQ 65/50 - Suitable for 4-6kW PSFB
    "PQ65/50": CoreGeometry(
        core_type="PQ65/50",
        effective_area=842e-6,       # 842 mm²
        effective_length=156e-3,     # 156 mm
        effective_volume=131e-6,     # 131 cm³
        window_area=708e-6,          # 708 mm²
        b_sat=0.39
    ),

    # PQ 80/60 - Suitable for 5-8kW PSFB
    "PQ80/60": CoreGeometry(
        core_type="PQ80/60",
        effective_area=1230e-6,      # 1230 mm²
        effective_length=188e-3,     # 188 mm
        effective_volume=231e-6,     # 231 cm³
        window_area=1100e-6,         # 1100 mm²
        b_sat=0.39
    ),

    # PQ 107/87 - Suitable for 8-12kW PSFB
    "PQ107/87": CoreGeometry(
        core_type="PQ107/87",
        effective_area=2210e-6,      # 2210 mm²
        effective_length=258e-3,     # 258 mm
        effective_volume=570e-6,     # 570 cm³
        window_area=2480e-6,         # 2480 mm²
        b_sat=0.39
    ),
}


# =============================================================================
# FERROXCUBE ETD CORES
# Reference: Ferroxcube soft ferrite catalog
# =============================================================================

FERROXCUBE_ETD_CORES: Dict[str, CoreGeometry] = {
    # ETD 39 - Suitable for 1-2kW PSFB
    "ETD39": CoreGeometry(
        core_type="ETD39",
        effective_area=125e-6,       # 125 mm²
        effective_length=92.7e-3,    # 92.7 mm
        effective_volume=11.6e-6,    # 11.6 cm³
        window_area=117e-6,          # 117 mm²
        b_sat=0.39                   # 3C95 @ 100°C
    ),

    # ETD 44 - Suitable for 2-3kW PSFB
    "ETD44": CoreGeometry(
        core_type="ETD44",
        effective_area=173e-6,       # 173 mm²
        effective_length=103e-3,     # 103 mm
        effective_volume=17.8e-6,    # 17.8 cm³
        window_area=174e-6,          # 174 mm²
        b_sat=0.39
    ),

    # ETD 49 - Suitable for 3-4kW PSFB
    "ETD49": CoreGeometry(
        core_type="ETD49",
        effective_area=211e-6,       # 211 mm²
        effective_length=114e-3,     # 114 mm
        effective_volume=24.1e-6,    # 24.1 cm³
        window_area=231e-6,          # 231 mm²
        b_sat=0.39
    ),

    # ETD 54 - Suitable for 4-5kW PSFB
    "ETD54": CoreGeometry(
        core_type="ETD54",
        effective_area=280e-6,       # 280 mm²
        effective_length=127e-3,     # 127 mm
        effective_volume=35.5e-6,    # 35.5 cm³
        window_area=314e-6,          # 314 mm²
        b_sat=0.39
    ),

    # ETD 59 - Suitable for 5-7kW PSFB (used in example)
    "ETD59": CoreGeometry(
        core_type="ETD59",
        effective_area=368e-6,       # 368 mm²
        effective_length=139e-3,     # 139 mm
        effective_volume=51.2e-6,    # 51.2 cm³
        window_area=511e-6,          # 511 mm²
        b_sat=0.39
    ),
}


# =============================================================================
# EPCOS/TDK E CORES
# Reference: EPCOS ferrite catalog
# =============================================================================

EPCOS_E_CORES: Dict[str, CoreGeometry] = {
    # E 42/21/20 - Suitable for 1-2kW PSFB
    "E42/21/20": CoreGeometry(
        core_type="E42/21/20",
        effective_area=181e-6,       # 181 mm²
        effective_length=96e-3,      # 96 mm
        effective_volume=17.4e-6,    # 17.4 cm³
        window_area=196e-6,          # 196 mm²
        b_sat=0.39
    ),

    # E 55/28/25 - Suitable for 3-5kW PSFB
    "E55/28/25": CoreGeometry(
        core_type="E55/28/25",
        effective_area=353e-6,       # 353 mm²
        effective_length=124e-3,     # 124 mm
        effective_volume=43.8e-6,    # 43.8 cm³
        window_area=412e-6,          # 412 mm²
        b_sat=0.39
    ),

    # E 65/32/27 - Suitable for 5-8kW PSFB
    "E65/32/27": CoreGeometry(
        core_type="E65/32/27",
        effective_area=530e-6,       # 530 mm²
        effective_length=148e-3,     # 148 mm
        effective_volume=78.5e-6,    # 78.5 cm³
        window_area=678e-6,          # 678 mm²
        b_sat=0.39
    ),
}


# =============================================================================
# CORE LOSS COEFFICIENTS (Steinmetz Equation)
# P_v [W/m³] = k × f^α × B^β
#
# Temperature-dependent coefficients for common ferrite materials
# Reference: Manufacturer datasheets with curve fitting
# =============================================================================

FERRITE_LOSS_COEFFICIENTS: Dict[str, Dict[float, CoreLossCoefficients]] = {
    # Ferroxcube 3C95 (MnZn ferrite, 25-200kHz optimal)
    CoreMaterial.FERRITE_3C95.value: {
        # At 25°C
        25.0: CoreLossCoefficients(
            k=28.3,
            alpha=1.61,
            beta=2.55,
            temperature=25.0
        ),
        # At 60°C
        60.0: CoreLossCoefficients(
            k=32.1,
            alpha=1.63,
            beta=2.60,
            temperature=60.0
        ),
        # At 100°C (recommended for design)
        100.0: CoreLossCoefficients(
            k=38.8,
            alpha=1.63,
            beta=2.62,
            temperature=100.0
        ),
        # At 120°C
        120.0: CoreLossCoefficients(
            k=43.2,
            alpha=1.64,
            beta=2.64,
            temperature=120.0
        ),
    },

    # Ferroxcube 3F3 (MnZn ferrite, 100-500kHz optimal)
    CoreMaterial.FERRITE_3F3.value: {
        25.0: CoreLossCoefficients(
            k=18.5,
            alpha=1.58,
            beta=2.48,
            temperature=25.0
        ),
        100.0: CoreLossCoefficients(
            k=26.7,
            alpha=1.60,
            beta=2.53,
            temperature=100.0
        ),
    },

    # EPCOS N87 (MnZn ferrite, 25-200kHz optimal)
    CoreMaterial.FERRITE_N87.value: {
        25.0: CoreLossCoefficients(
            k=24.1,
            alpha=1.57,
            beta=2.51,
            temperature=25.0
        ),
        100.0: CoreLossCoefficients(
            k=34.5,
            alpha=1.59,
            beta=2.58,
            temperature=100.0
        ),
    },

    # EPCOS N97 (MnZn ferrite, 100-500kHz optimal, lower loss)
    CoreMaterial.FERRITE_N97.value: {
        25.0: CoreLossCoefficients(
            k=16.2,
            alpha=1.54,
            beta=2.45,
            temperature=25.0
        ),
        100.0: CoreLossCoefficients(
            k=23.8,
            alpha=1.56,
            beta=2.50,
            temperature=100.0
        ),
    },

    # Nanocrystalline (Finemet, Vitroperm) - very low loss
    # Excellent for high frequency (>200kHz) and high flux density
    CoreMaterial.NANOCRYSTALLINE.value: {
        25.0: CoreLossCoefficients(
            k=8.5,
            alpha=1.51,
            beta=2.20,
            temperature=25.0
        ),
        100.0: CoreLossCoefficients(
            k=12.3,
            alpha=1.52,
            beta=2.24,
            temperature=100.0
        ),
    },
}


# =============================================================================
# DATABASE ACCESS FUNCTIONS
# =============================================================================

def get_core_geometry(core_type: str) -> Optional[CoreGeometry]:
    """
    Retrieve core geometry by core type designation

    Args:
        core_type: Core designation (e.g., "PQ80/60", "ETD59", "E65/32/27")

    Returns:
        CoreGeometry object if found, None otherwise
    """
    # Search all core databases
    all_cores = {
        **TDK_PQ_CORES,
        **FERROXCUBE_ETD_CORES,
        **EPCOS_E_CORES,
    }

    return all_cores.get(core_type)


def get_core_loss_coefficients(
    material: CoreMaterial,
    temperature: float
) -> CoreLossCoefficients:
    """
    Retrieve core loss coefficients for a material at specific temperature

    If exact temperature match not found, interpolates between available points.

    Args:
        material: Core material type
        temperature: Operating temperature in °C

    Returns:
        CoreLossCoefficients object

    Raises:
        ValueError: If material not in database
    """
    material_key = material.value

    if material_key not in FERRITE_LOSS_COEFFICIENTS:
        raise ValueError(f"Core material {material_key} not in database")

    temp_coeffs = FERRITE_LOSS_COEFFICIENTS[material_key]

    # Exact match
    if temperature in temp_coeffs:
        return temp_coeffs[temperature]

    # Interpolation needed
    temps = sorted(temp_coeffs.keys())

    if temperature < temps[0]:
        # Extrapolate using lowest temperature
        print(f"Warning: Temperature {temperature}°C below database range, "
              f"using {temps[0]}°C coefficients")
        return temp_coeffs[temps[0]]

    if temperature > temps[-1]:
        # Extrapolate using highest temperature
        print(f"Warning: Temperature {temperature}°C above database range, "
              f"using {temps[-1]}°C coefficients")
        return temp_coeffs[temps[-1]]

    # Linear interpolation between bracketing temperatures
    for i in range(len(temps) - 1):
        t1, t2 = temps[i], temps[i + 1]
        if t1 <= temperature <= t2:
            coeffs1 = temp_coeffs[t1]
            coeffs2 = temp_coeffs[t2]

            # Interpolation factor
            factor = (temperature - t1) / (t2 - t1)

            # Interpolate each coefficient
            k_interp = coeffs1.k + factor * (coeffs2.k - coeffs1.k)
            alpha_interp = coeffs1.alpha + factor * (coeffs2.alpha - coeffs1.alpha)
            beta_interp = coeffs1.beta + factor * (coeffs2.beta - coeffs1.beta)

            return CoreLossCoefficients(
                k=k_interp,
                alpha=alpha_interp,
                beta=beta_interp,
                temperature=temperature
            )

    raise ValueError(f"Temperature interpolation failed for {temperature}°C")


def list_available_cores(min_power_kw: Optional[float] = None,
                         max_power_kw: Optional[float] = None) -> Dict[str, str]:
    """
    List all available cores in database, optionally filtered by power range

    Args:
        min_power_kw: Minimum power in kW (optional)
        max_power_kw: Maximum power in kW (optional)

    Returns:
        Dictionary of {core_type: description}
    """
    all_cores = {
        **TDK_PQ_CORES,
        **FERROXCUBE_ETD_CORES,
        **EPCOS_E_CORES,
    }

    # Simple power estimation based on core volume
    # Rough rule: P ≈ 5-10 W/cm³ for PSFB @ 100kHz
    core_list = {}

    for core_type, geometry in all_cores.items():
        vol_cm3 = geometry.effective_volume * 1e6  # Convert m³ to cm³
        est_power_kw = (vol_cm3 * 7.5) / 1000  # Assume 7.5 W/cm³ average

        # Filter by power if specified
        if min_power_kw is not None and est_power_kw < min_power_kw:
            continue
        if max_power_kw is not None and est_power_kw > max_power_kw:
            continue

        description = (f"Ae={geometry.effective_area*1e6:.0f}mm², "
                      f"Ve={geometry.effective_volume*1e6:.1f}cm³, "
                      f"~{est_power_kw:.1f}kW")

        core_list[core_type] = description

    return core_list


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("="*70)
    print("MAGNETIC CORE DATABASE")
    print("="*70)

    # List all TDK PQ cores
    print("\n📦 TDK PQ Cores (Large Power):")
    print("-"*70)
    for core_type, description in list_available_cores().items():
        if core_type.startswith("PQ"):
            print(f"  {core_type:15s} - {description}")

    # List all Ferroxcube ETD cores
    print("\n📦 Ferroxcube ETD Cores:")
    print("-"*70)
    for core_type, description in list_available_cores().items():
        if core_type.startswith("ETD"):
            print(f"  {core_type:15s} - {description}")

    # List cores suitable for 3-5kW
    print("\n📦 Cores Suitable for 3-5kW PSFB:")
    print("-"*70)
    for core_type, description in list_available_cores(min_power_kw=3.0, max_power_kw=5.0).items():
        print(f"  {core_type:15s} - {description}")

    # Get specific core geometry
    print("\n📏 PQ80/60 Core Details:")
    print("-"*70)
    core = get_core_geometry("PQ80/60")
    if core:
        print(f"  Core type:     {core.core_type}")
        print(f"  Ae:            {core.effective_area*1e6:.1f} mm²")
        print(f"  le:            {core.effective_length*1e3:.1f} mm")
        print(f"  Ve:            {core.effective_volume*1e6:.1f} cm³")
        print(f"  Window area:   {core.window_area*1e6:.1f} mm²")
        print(f"  B_sat:         {core.b_sat:.2f} T @ 100°C")

    # Get core loss coefficients
    print("\n📊 3C95 Ferrite Loss Coefficients @ 100°C:")
    print("-"*70)
    coeffs = get_core_loss_coefficients(CoreMaterial.FERRITE_3C95, 100.0)
    print(f"  k:             {coeffs.k:.2f}")
    print(f"  α (alpha):     {coeffs.alpha:.2f}")
    print(f"  β (beta):      {coeffs.beta:.2f}")
    print(f"  Temperature:   {coeffs.temperature:.0f}°C")

    # Test interpolation
    print("\n📊 3C95 Ferrite Loss Coefficients @ 85°C (interpolated):")
    print("-"*70)
    coeffs = get_core_loss_coefficients(CoreMaterial.FERRITE_3C95, 85.0)
    print(f"  k:             {coeffs.k:.2f}")
    print(f"  α (alpha):     {coeffs.alpha:.2f}")
    print(f"  β (beta):      {coeffs.beta:.2f}")
    print(f"  Temperature:   {coeffs.temperature:.0f}°C")

    print("\n" + "="*70)

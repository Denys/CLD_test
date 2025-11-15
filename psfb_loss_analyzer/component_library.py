"""
Component Library Database for PSFB Converter Design

Database of commercially available components for automated design:
- SiC and Si MOSFETs (600V-1200V class)
- SiC Schottky and Si PN diodes
- Magnetic cores (TDK PQ, Ferroxcube ETD, EPCOS E)
- Input and output capacitors

Used by optimizer for automatic component selection based on:
- Voltage and current ratings
- On-resistance and forward voltage drop
- Cost metrics (relative)
- Availability and package types

Author: PSFB Loss Analysis Tool
Version: 0.5.0
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

try:
    from .circuit_params import (
        MOSFETParameters,
        CapacitanceVsVoltage,
        DiodeParameters,
        CapacitorParameters,
        CoreGeometry,
        CoreMaterial,
    )
except ImportError:
    from circuit_params import (
        MOSFETParameters,
        CapacitanceVsVoltage,
        DiodeParameters,
        CapacitorParameters,
        CoreGeometry,
        CoreMaterial,
    )


class DeviceType(Enum):
    """Semiconductor device type"""
    SIC_MOSFET = "SiC MOSFET"
    SI_MOSFET = "Si MOSFET"
    SIC_SCHOTTKY = "SiC Schottky"
    SI_PN_DIODE = "Si PN Diode"


@dataclass
class ComponentMetrics:
    """Component selection metrics"""
    relative_cost: float = 1.0  # Relative cost (1.0 = baseline)
    availability: str = "Standard"  # "Standard", "Limited", "EOL"
    package: str = "TO-247"  # Package type
    manufacturer: str = "Generic"  # Manufacturer


# ============================================================================
# MOSFET Library - SiC Devices
# ============================================================================

MOSFET_LIBRARY_SIC = {
    # Infineon CoolSiC™ 650V Series
    "IMZA65R020M2H": {
        "device": MOSFETParameters(
            part_number="IMZA65R020M2H",
            v_dss=650.0,
            i_d_continuous=90.0,
            r_dson_25c=16e-3,
            r_dson_25c_max=20e-3,
            r_dson_150c=22e-3,
            r_dson_150c_max=28e-3,
            capacitances=CapacitanceVsVoltage(c_iss_constant=7200e-12, c_oss_constant=520e-12, c_rss_constant=15e-12),
            q_g=142e-9,
            q_gs=38e-9,
            q_gd=52e-9,
            v_gs_plateau=4.5,
            t_r=25e-9,
            t_f=20e-9,
        ),
        "metrics": ComponentMetrics(relative_cost=2.8, availability="Standard", package="TO-247-4", manufacturer="Infineon"),
        "description": "650V 90A 20mΩ SiC MOSFET, Excellent for 2-5kW PSFB primary",
    },

    "IMZA65R040M2H": {
        "device": MOSFETParameters(
            part_number="IMZA65R040M2H",
            v_dss=650.0,
            i_d_continuous=58.0,
            r_dson_25c=32e-3,
            r_dson_25c_max=40e-3,
            r_dson_150c=44e-3,
            r_dson_150c_max=55e-3,
            capacitances=CapacitanceVsVoltage(c_iss_constant=4800e-12, c_oss_constant=340e-12, c_rss_constant=10e-12),
            q_g=98e-9,
            q_gs=26e-9,
            q_gd=36e-9,
            v_gs_plateau=4.2,
            t_r=20e-9,
            t_f=18e-9,
        ),
        "metrics": ComponentMetrics(relative_cost=2.2, availability="Standard", package="TO-247-4", manufacturer="Infineon"),
        "description": "650V 58A 40mΩ SiC MOSFET, Good for 1-3kW PSFB primary",
    },

    # Wolfspeed C3M™ 650V Series
    "C3M0065090J": {
        "device": MOSFETParameters(
            part_number="C3M0065090J",
            v_dss=900.0,
            i_d_continuous=36.0,
            r_dson_25c=50e-3,
            r_dson_25c_max=65e-3,
            r_dson_150c=70e-3,
            r_dson_150c_max=90e-3,
            capacitances=CapacitanceVsVoltage(c_iss_constant=1350e-12, c_oss_constant=120e-12, c_rss_constant=8e-12),
            q_g=55e-9,
            q_gs=18e-9,
            q_gd=20e-9,
            v_gs_plateau=4.8,
            t_r=18e-9,
            t_f=15e-9,
        ),
        "metrics": ComponentMetrics(relative_cost=2.5, availability="Standard", package="TO-247-3", manufacturer="Wolfspeed"),
        "description": "900V 36A 65mΩ SiC MOSFET, High voltage applications",
    },

    "C3M0021120K": {
        "device": MOSFETParameters(
            part_number="C3M0021120K",
            v_dss=1200.0,
            i_d_continuous=90.0,
            r_dson_25c=16e-3,
            r_dson_25c_max=21e-3,
            r_dson_150c=22e-3,
            r_dson_150c_max=29e-3,
            capacitances=CapacitanceVsVoltage(c_iss_constant=5800e-12, c_oss_constant=410e-12, c_rss_constant=12e-12),
            q_g=130e-9,
            q_gs=35e-9,
            q_gd=48e-9,
            v_gs_plateau=5.0,
            t_r=22e-9,
            t_f=20e-9,
        ),
        "metrics": ComponentMetrics(relative_cost=3.5, availability="Standard", package="TO-247-4", manufacturer="Wolfspeed"),
        "description": "1200V 90A 21mΩ SiC MOSFET, High power applications",
    },
}


# ============================================================================
# MOSFET Library - Si Devices (for cost comparison / SR applications)
# ============================================================================

MOSFET_LIBRARY_SI = {
    # Texas Instruments Si MOSFETs for Synchronous Rectification
    "CSD19538Q3A": {
        "device": MOSFETParameters(
            part_number="CSD19538Q3A",
            v_dss=100.0,
            i_d_continuous=300.0,
            r_dson_25c=1.1e-3,
            r_dson_25c_max=1.38e-3,
            r_dson_150c=2.0e-3,
            r_dson_150c_max=2.5e-3,
            capacitances=CapacitanceVsVoltage(c_iss_constant=18000e-12, c_oss_constant=3800e-12, c_rss_constant=450e-12),
            q_g=198e-9,
            q_gs=58e-9,
            q_gd=45e-9,
            v_gs_plateau=3.5,
            t_r=12e-9,
            t_f=10e-9,
        ),
        "metrics": ComponentMetrics(relative_cost=0.8, availability="Standard", package="SON 5x6", manufacturer="TI"),
        "description": "100V 300A 1.38mΩ Si MOSFET, Excellent for SR",
    },

    "CSD19536KTT": {
        "device": MOSFETParameters(
            part_number="CSD19536KTT",
            v_dss=100.0,
            i_d_continuous=200.0,
            r_dson_25c=1.4e-3,
            r_dson_25c_max=1.7e-3,
            r_dson_150c=2.5e-3,
            r_dson_150c_max=3.0e-3,
            capacitances=CapacitanceVsVoltage(c_iss_constant=12500e-12, c_oss_constant=2600e-12, c_rss_constant=350e-12),
            q_g=145e-9,
            q_gs=42e-9,
            q_gd=35e-9,
            v_gs_plateau=3.8,
            t_r=10e-9,
            t_f=8e-9,
        ),
        "metrics": ComponentMetrics(relative_cost=0.6, availability="Standard", package="D2PAK-7", manufacturer="TI"),
        "description": "100V 200A 1.7mΩ Si MOSFET, Good for SR",
    },
}


# ============================================================================
# Diode Library - SiC Schottky
# ============================================================================

DIODE_LIBRARY_SIC = {
    # Wolfspeed SiC Schottky Diodes
    "C4D30120A": {
        "device": DiodeParameters(
            part_number="C4D30120A",
            v_rrm=1200.0,
            i_f_avg=31.0,
            v_f0=0.0,  # SiC Schottky
            r_d=35e-3,
            q_rr=0.0,
            t_rr=0.0,
        ),
        "metrics": ComponentMetrics(relative_cost=2.0, availability="Standard", package="TO-247-2", manufacturer="Wolfspeed"),
        "description": "1200V 31A SiC Schottky, Zero recovery",
    },

    "C4D20120D": {
        "device": DiodeParameters(
            part_number="C4D20120D",
            v_rrm=1200.0,
            i_f_avg=20.0,
            v_f0=0.0,
            r_d=45e-3,
            q_rr=0.0,
            t_rr=0.0,
        ),
        "metrics": ComponentMetrics(relative_cost=1.5, availability="Standard", package="TO-220-2", manufacturer="Wolfspeed"),
        "description": "1200V 20A SiC Schottky, Lower current",
    },

    "C3D16065D": {
        "device": DiodeParameters(
            part_number="C3D16065D",
            v_rrm=650.0,
            i_f_avg=16.0,
            v_f0=0.0,
            r_d=50e-3,
            q_rr=0.0,
            t_rr=0.0,
        ),
        "metrics": ComponentMetrics(relative_cost=1.2, availability="Standard", package="TO-220-2", manufacturer="Wolfspeed"),
        "description": "650V 16A SiC Schottky, Mid-range",
    },
}


# ============================================================================
# Diode Library - Si PN (for comparison)
# ============================================================================

DIODE_LIBRARY_SI = {
    # Generic Si Fast Recovery Diodes
    "MUR3020WT": {
        "device": DiodeParameters(
            part_number="MUR3020WT",
            v_rrm=200.0,
            i_f_avg=30.0,
            v_f0=0.85,  # Si PN
            r_d=12e-3,
            q_rr=180e-9,
            t_rr=45e-9,
        ),
        "metrics": ComponentMetrics(relative_cost=0.3, availability="Standard", package="TO-247-2", manufacturer="On Semi"),
        "description": "200V 30A Si Fast Recovery",
    },

    "DSEI60-06A": {
        "device": DiodeParameters(
            part_number="DSEI60-06A",
            v_rrm=600.0,
            i_f_avg=60.0,
            v_f0=1.0,
            r_d=8e-3,
            q_rr=380e-9,
            t_rr=55e-9,
        ),
        "metrics": ComponentMetrics(relative_cost=0.5, availability="Standard", package="TO-247-2", manufacturer="IXYS"),
        "description": "600V 60A Si Ultrafast",
    },
}


# ============================================================================
# Capacitor Library
# ============================================================================

CAPACITOR_LIBRARY_INPUT = {
    # Film capacitors for input (low ESR, high ripple current)
    "MKP_100uF_500V": {
        "device": CapacitorParameters(
            capacitance=100e-6,
            voltage_rating=500.0,
            esr=10e-3,
            ripple_current_rating=50.0,
        ),
        "metrics": ComponentMetrics(relative_cost=1.5, availability="Standard", package="Radial", manufacturer="Generic"),
        "description": "100µF 500V Film, Low ESR",
    },

    "MKP_47uF_600V": {
        "device": CapacitorParameters(
            capacitance=47e-6,
            voltage_rating=600.0,
            esr=12e-3,
            ripple_current_rating=35.0,
        ),
        "metrics": ComponentMetrics(relative_cost=1.2, availability="Standard", package="Radial", manufacturer="Generic"),
        "description": "47µF 600V Film, Compact",
    },
}

CAPACITOR_LIBRARY_OUTPUT = {
    # Aluminum electrolytic for output (high capacitance)
    "Elec_1000uF_350V": {
        "device": CapacitorParameters(
            capacitance=1000e-6,
            voltage_rating=350.0,
            esr=5e-3,
            ripple_current_rating=40.0,
        ),
        "metrics": ComponentMetrics(relative_cost=0.8, availability="Standard", package="Snap-in", manufacturer="Generic"),
        "description": "1000µF 350V Electrolytic",
    },

    "Elec_470uF_450V": {
        "device": CapacitorParameters(
            capacitance=470e-6,
            voltage_rating=450.0,
            esr=8e-3,
            ripple_current_rating=30.0,
        ),
        "metrics": ComponentMetrics(relative_cost=0.6, availability="Standard", package="Snap-in", manufacturer="Generic"),
        "description": "470µF 450V Electrolytic",
    },
}


# ============================================================================
# Helper Functions for Component Selection
# ============================================================================

def filter_mosfets_by_rating(
    library: Dict,
    min_voltage: float,
    min_current: float,
    max_rdson: Optional[float] = None,
    device_type: Optional[DeviceType] = None,
) -> List[tuple]:
    """
    Filter MOSFET library by electrical ratings.

    Args:
        library: MOSFET library dictionary
        min_voltage: Minimum V_DSS requirement (V)
        min_current: Minimum I_D requirement (A)
        max_rdson: Maximum R_DS(on) (Ω, optional)
        device_type: Filter by device type (optional)

    Returns:
        List of (part_number, device, metrics) tuples
    """
    results = []

    for part_num, data in library.items():
        device = data["device"]
        metrics = data["metrics"]

        # Voltage rating check (with margin)
        if device.v_dss < min_voltage * 1.2:
            continue

        # Current rating check (with margin)
        if device.i_d_continuous < min_current * 1.2:
            continue

        # RDS(on) check
        if max_rdson and device.r_dson_25c_max > max_rdson:
            continue

        results.append((part_num, device, metrics))

    # Sort by RDS(on) (lower is better)
    results.sort(key=lambda x: x[1].r_dson_25c_max)

    return results


def filter_diodes_by_rating(
    library: Dict,
    min_voltage: float,
    min_current: float,
    prefer_sic: bool = True,
) -> List[tuple]:
    """
    Filter diode library by electrical ratings.

    Args:
        library: Diode library dictionary
        min_voltage: Minimum V_RRM requirement (V)
        min_current: Minimum I_F requirement (A)
        prefer_sic: Prefer SiC Schottky over Si PN

    Returns:
        List of (part_number, device, metrics) tuples
    """
    results = []

    for part_num, data in library.items():
        device = data["device"]
        metrics = data["metrics"]

        # Voltage rating check
        if device.v_rrm < min_voltage * 1.2:
            continue

        # Current rating check
        if device.i_f_avg < min_current * 1.2:
            continue

        results.append((part_num, device, metrics))

    # Sort: SiC first (if preferred), then by current rating
    if prefer_sic:
        results.sort(key=lambda x: (x[1].v_f0, -x[1].i_f_avg))
    else:
        results.sort(key=lambda x: -x[1].i_f_avg)

    return results


def get_all_mosfets() -> Dict:
    """Get complete MOSFET library (SiC + Si)"""
    return {**MOSFET_LIBRARY_SIC, **MOSFET_LIBRARY_SI}


def get_all_diodes() -> Dict:
    """Get complete diode library (SiC + Si)"""
    return {**DIODE_LIBRARY_SIC, **DIODE_LIBRARY_SI}


# ============================================================================
# Module Information
# ============================================================================

if __name__ == "__main__":
    print("PSFB Loss Analyzer - Component Library")
    print("=" * 80)
    print()
    print(f"Available MOSFETs (SiC): {len(MOSFET_LIBRARY_SIC)}")
    print(f"Available MOSFETs (Si):  {len(MOSFET_LIBRARY_SI)}")
    print(f"Available Diodes (SiC):  {len(DIODE_LIBRARY_SIC)}")
    print(f"Available Diodes (Si):   {len(DIODE_LIBRARY_SI)}")
    print(f"Input Capacitors:        {len(CAPACITOR_LIBRARY_INPUT)}")
    print(f"Output Capacitors:       {len(CAPACITOR_LIBRARY_OUTPUT)}")
    print()
    print("Example: Filter 650V MOSFETs for 20A application:")
    results = filter_mosfets_by_rating(MOSFET_LIBRARY_SIC, min_voltage=400, min_current=20)
    for part, device, metrics in results[:3]:
        print(f"  {part}: {device.v_dss}V {device.i_d_continuous}A {device.r_dson_25c_max*1000:.1f}mΩ")
    print()

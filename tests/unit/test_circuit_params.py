"""
Unit Tests: Circuit Parameters

Tests for MOSFETParameters, DiodeParameters, and related dataclasses.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from psfb_loss_analyzer import (
    MOSFETParameters,
    DiodeParameters,
    CapacitanceVsVoltage,
    CoreGeometry,
    CoreMaterial,
)


def test_mosfet_parameters_creation():
    """Test MOSFET parameter creation"""
    mosfet = MOSFETParameters(
        part_number="TEST_MOSFET",
        v_dss=650.0,
        i_d_continuous=90.0,
        r_dson_25c=20e-3,
        r_dson_25c_max=25e-3,
        r_dson_150c=28e-3,
        r_dson_150c_max=35e-3,
        capacitances=CapacitanceVsVoltage(
            c_iss_constant=7200e-12,
            c_oss_constant=520e-12,
            c_rss_constant=15e-12,
        ),
        q_g=142e-9,
        q_gs=38e-9,
        q_gd=52e-9,
        v_gs_plateau=4.5,
        t_r=25e-9,
        t_f=20e-9,
    )

    assert mosfet.part_number == "TEST_MOSFET"
    assert mosfet.v_dss == 650.0
    assert mosfet.i_d_continuous == 90.0
    assert mosfet.r_dson_25c == 20e-3
    assert mosfet.r_dson_150c > mosfet.r_dson_25c  # Should increase with temp


def test_diode_parameters_creation():
    """Test diode parameter creation"""
    diode = DiodeParameters(
        part_number="TEST_DIODE",
        v_rrm=1200.0,
        i_f_avg=30.0,
        v_f0=0.8,
        r_f=0.015,
        v_f_25c=1.5,
        v_f_125c=1.3,
        t_rr=35e-9,
        q_rr=50e-9,
        c_j0=500e-12,
        m_j=0.5,
        v_j=4.0,
    )

    assert diode.part_number == "TEST_DIODE"
    assert diode.v_rrm == 1200.0
    assert diode.i_f_avg == 30.0
    assert diode.v_f_125c < diode.v_f_25c  # Should decrease with temp for SiC


def test_capacitance_vs_voltage():
    """Test capacitance voltage dependence"""
    cap = CapacitanceVsVoltage(
        c_iss_constant=7200e-12,
        c_oss_constant=520e-12,
        c_rss_constant=15e-12,
    )

    # Test at 400V
    c_oss_400v = cap.get_c_oss(400.0)
    assert c_oss_400v > 0
    assert c_oss_400v == cap.c_oss_constant  # Constant model

    # Test with voltage-dependent model
    cap_vd = CapacitanceVsVoltage(
        c_iss_constant=7200e-12,
        c_oss_v0=1500e-12,
        c_oss_vj=3.5,
        c_oss_mj=0.4,
        c_rss_constant=15e-12,
    )

    c_oss_100v = cap_vd.get_c_oss(100.0)
    c_oss_400v = cap_vd.get_c_oss(400.0)
    assert c_oss_100v > c_oss_400v  # Should decrease with voltage


def test_core_geometry():
    """Test core geometry calculations"""
    core = CoreGeometry(
        effective_area=1.0e-4,  # 100 mm²
        effective_length=50e-3,  # 50 mm
        effective_volume=5.0e-6,  # 5000 mm³
        window_area=1.5e-4,  # 150 mm²
    )

    # Test properties
    assert core.core_area == core.effective_area
    assert core.path_length == core.effective_length
    assert core.volume == core.effective_volume

    # Test computed properties
    mlt = core.mean_length_turn
    assert mlt > 0
    assert mlt > 0.04  # Should be at least ~40mm

    surface_area = core.surface_area
    assert surface_area > 0


def test_core_material():
    """Test core material properties"""
    # N87 material (common ferrite)
    material = CoreMaterial(
        name="N87",
        k_core=1.0,
        alpha=1.3,
        beta=2.4,
        resistivity=3.0,
        density=4850.0,
    )

    assert material.name == "N87"
    assert material.k_core == 1.0
    assert material.alpha > 1.0  # Typical for ferrites
    assert material.beta > 2.0


def test_temperature_coefficient():
    """Test R_DS(on) temperature coefficient"""
    mosfet = MOSFETParameters(
        part_number="TEMP_TEST",
        v_dss=650.0,
        i_d_continuous=90.0,
        r_dson_25c=20e-3,
        r_dson_25c_max=25e-3,
        r_dson_150c=28e-3,
        r_dson_150c_max=35e-3,
        capacitances=CapacitanceVsVoltage(
            c_iss_constant=7200e-12,
            c_oss_constant=520e-12,
            c_rss_constant=15e-12,
        ),
        q_g=142e-9,
    )

    # Temperature coefficient should be positive
    temp_coeff = (mosfet.r_dson_150c - mosfet.r_dson_25c) / (150 - 25)
    assert temp_coeff > 0  # R_DS(on) increases with temperature

    # Typical increase: 30-50% from 25°C to 150°C
    ratio = mosfet.r_dson_150c / mosfet.r_dson_25c
    assert 1.3 < ratio < 1.6


if __name__ == "__main__":
    print("Running Circuit Parameters Tests...")
    test_mosfet_parameters_creation()
    print("✓ MOSFET parameters creation")

    test_diode_parameters_creation()
    print("✓ Diode parameters creation")

    test_capacitance_vs_voltage()
    print("✓ Capacitance vs voltage")

    test_core_geometry()
    print("✓ Core geometry")

    test_core_material()
    print("✓ Core material")

    test_temperature_coefficient()
    print("✓ Temperature coefficient")

    print("\n✓ All circuit parameter tests passed!")

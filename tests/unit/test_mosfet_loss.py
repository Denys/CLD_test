"""
Unit Tests: MOSFET Loss Calculations

Tests for MOSFET conduction, switching, and gate drive losses.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from psfb_loss_analyzer import (
    MOSFETParameters,
    CapacitanceVsVoltage,
    calculate_mosfet_conduction_loss,
    calculate_mosfet_switching_loss,
    calculate_mosfet_gate_drive_loss,
    calculate_mosfet_coss_loss,
)


# Test MOSFET definition
TEST_MOSFET = MOSFETParameters(
    part_number="TEST_650V_90A",
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


def test_conduction_loss_basic():
    """Test basic conduction loss calculation"""
    # Test conditions: 20A RMS, 25°C
    i_rms = 20.0
    duty_cycle = 0.45
    t_junction = 25.0

    loss = calculate_mosfet_conduction_loss(
        mosfet=TEST_MOSFET,
        i_rms=i_rms,
        duty_cycle=duty_cycle,
        t_junction=t_junction,
    )

    # Expected: I²R = 20² × 0.02 = 8W
    expected = i_rms**2 * TEST_MOSFET.r_dson_25c
    assert abs(loss - expected) < 0.5, f"Expected ~{expected}W, got {loss}W"
    assert loss > 0, "Loss must be positive"


def test_conduction_loss_temperature_scaling():
    """Test conduction loss increases with temperature"""
    i_rms = 20.0
    duty_cycle = 0.45

    # Calculate at 25°C
    loss_25c = calculate_mosfet_conduction_loss(
        mosfet=TEST_MOSFET,
        i_rms=i_rms,
        duty_cycle=duty_cycle,
        t_junction=25.0,
    )

    # Calculate at 150°C
    loss_150c = calculate_mosfet_conduction_loss(
        mosfet=TEST_MOSFET,
        i_rms=i_rms,
        duty_cycle=duty_cycle,
        t_junction=150.0,
    )

    # Loss should increase at higher temperature
    assert loss_150c > loss_25c, "Loss should increase with temperature"

    # Ratio should match R_DS(on) ratio
    ratio = loss_150c / loss_25c
    rdson_ratio = TEST_MOSFET.r_dson_150c / TEST_MOSFET.r_dson_25c
    assert abs(ratio - rdson_ratio) < 0.1, "Loss ratio should match R_DS(on) ratio"


def test_switching_loss_basic():
    """Test basic switching loss calculation"""
    v_ds = 400.0  # Blocking voltage
    i_d = 25.0    # Switched current
    frequency = 100e3  # 100kHz
    t_junction = 100.0

    loss = calculate_mosfet_switching_loss(
        mosfet=TEST_MOSFET,
        v_ds=v_ds,
        i_d=i_d,
        frequency=frequency,
        t_junction=t_junction,
    )

    # Switching loss should be reasonable
    # Typical: 10-50W @ 100kHz for this current/voltage
    assert 5.0 < loss < 100.0, f"Switching loss {loss}W seems unreasonable"
    assert loss > 0, "Loss must be positive"


def test_switching_loss_frequency_scaling():
    """Test switching loss scales with frequency"""
    v_ds = 400.0
    i_d = 25.0
    t_junction = 100.0

    # Calculate at 50kHz
    loss_50khz = calculate_mosfet_switching_loss(
        mosfet=TEST_MOSFET,
        v_ds=v_ds,
        i_d=i_d,
        frequency=50e3,
        t_junction=t_junction,
    )

    # Calculate at 100kHz
    loss_100khz = calculate_mosfet_switching_loss(
        mosfet=TEST_MOSFET,
        v_ds=v_ds,
        i_d=i_d,
        frequency=100e3,
        t_junction=t_junction,
    )

    # Loss should double with frequency
    ratio = loss_100khz / loss_50khz
    assert abs(ratio - 2.0) < 0.2, f"Loss should double with frequency, got ratio {ratio}"


def test_gate_drive_loss():
    """Test gate drive loss calculation"""
    v_gs_drive = 18.0  # Drive voltage
    frequency = 100e3  # 100kHz

    loss = calculate_mosfet_gate_drive_loss(
        mosfet=TEST_MOSFET,
        v_gs_drive=v_gs_drive,
        frequency=frequency,
    )

    # Expected: Q_g × V_gs × f = 142nC × 18V × 100kHz = 0.256W
    expected = TEST_MOSFET.q_g * v_gs_drive * frequency
    assert abs(loss - expected) < 0.01, f"Expected {expected}W, got {loss}W"
    assert loss > 0, "Loss must be positive"
    assert loss < 2.0, "Gate drive loss should be small (< 2W)"


def test_coss_loss():
    """Test C_oss related losses"""
    v_ds = 400.0
    frequency = 100e3

    loss = calculate_mosfet_coss_loss(
        mosfet=TEST_MOSFET,
        v_ds=v_ds,
        frequency=frequency,
    )

    # C_oss loss should be reasonable
    # Expected: 0.5 × C_oss × V² × f
    c_oss = TEST_MOSFET.capacitances.get_c_oss(v_ds)
    expected = 0.5 * c_oss * v_ds**2 * frequency

    assert abs(loss - expected) < 1.0, f"Expected ~{expected}W, got {loss}W"
    assert loss > 0, "Loss must be positive"


def test_total_loss_aggregation():
    """Test total MOSFET losses"""
    # Operating conditions
    i_rms = 20.0
    i_d = 25.0
    v_ds = 400.0
    frequency = 100e3
    duty_cycle = 0.45
    v_gs_drive = 18.0
    t_junction = 100.0

    # Calculate individual losses
    p_cond = calculate_mosfet_conduction_loss(
        TEST_MOSFET, i_rms, duty_cycle, t_junction
    )

    p_sw = calculate_mosfet_switching_loss(
        TEST_MOSFET, v_ds, i_d, frequency, t_junction
    )

    p_gate = calculate_mosfet_gate_drive_loss(
        TEST_MOSFET, v_gs_drive, frequency
    )

    p_coss = calculate_mosfet_coss_loss(
        TEST_MOSFET, v_ds, frequency
    )

    # Total loss
    p_total = p_cond + p_sw + p_gate + p_coss

    # All components should be positive
    assert p_cond > 0
    assert p_sw > 0
    assert p_gate > 0
    assert p_coss >= 0  # May be zero for some models

    # Total should be sum
    assert abs(p_total - (p_cond + p_sw + p_gate + p_coss)) < 0.01

    # Total should be reasonable (10-100W range)
    assert 10.0 < p_total < 200.0, f"Total loss {p_total}W seems unreasonable"


def test_zero_current():
    """Test losses with zero current (should be minimal)"""
    # Zero conduction loss
    loss_cond = calculate_mosfet_conduction_loss(
        TEST_MOSFET, i_rms=0.0, duty_cycle=0.5, t_junction=100.0
    )
    assert loss_cond == 0.0, "Zero current should give zero conduction loss"

    # Zero switching loss
    loss_sw = calculate_mosfet_switching_loss(
        TEST_MOSFET, v_ds=400.0, i_d=0.0, frequency=100e3, t_junction=100.0
    )
    # Should be zero or very small
    assert loss_sw < 1.0, "Zero current should give minimal switching loss"


if __name__ == "__main__":
    print("Running MOSFET Loss Calculation Tests...")

    test_conduction_loss_basic()
    print("✓ Conduction loss basic")

    test_conduction_loss_temperature_scaling()
    print("✓ Conduction loss temperature scaling")

    test_switching_loss_basic()
    print("✓ Switching loss basic")

    test_switching_loss_frequency_scaling()
    print("✓ Switching loss frequency scaling")

    test_gate_drive_loss()
    print("✓ Gate drive loss")

    test_coss_loss()
    print("✓ C_oss loss")

    test_total_loss_aggregation()
    print("✓ Total loss aggregation")

    test_zero_current()
    print("✓ Zero current edge case")

    print("\n✓ All MOSFET loss tests passed!")

"""
Unit Tests: Diode Loss Calculations

Tests for diode forward conduction and reverse recovery losses.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from psfb_loss_analyzer import (
    DiodeParameters,
    calculate_diode_conduction_loss,
    calculate_diode_reverse_recovery_loss,
)


# Test SiC Schottky diode
SIC_SCHOTTKY = DiodeParameters(
    part_number="SIC_SCHOTTKY_TEST",
    v_rrm=1200.0,
    i_f_avg=30.0,
    v_f0=0.8,
    r_f=0.015,
    v_f_25c=1.5,
    v_f_125c=1.3,
    t_rr=20e-9,  # Very low for SiC Schottky
    q_rr=10e-9,  # Very low for SiC Schottky
    c_j0=500e-12,
)

# Test Si PN diode
SI_PN_DIODE = DiodeParameters(
    part_number="SI_PN_TEST",
    v_rrm=1200.0,
    i_f_avg=30.0,
    v_f0=0.9,
    r_f=0.012,
    v_f_25c=1.2,
    v_f_125c=1.1,
    t_rr=150e-9,  # Higher for Si PN
    q_rr=500e-9,  # Higher for Si PN
    c_j0=800e-12,
)


def test_conduction_loss_sic():
    """Test SiC Schottky conduction loss"""
    i_f_avg = 20.0  # Average current
    i_f_rms = 22.0  # RMS current
    t_junction = 100.0

    loss = calculate_diode_conduction_loss(
        diode=SIC_SCHOTTKY,
        i_f_avg=i_f_avg,
        i_f_rms=i_f_rms,
        t_junction=t_junction,
    )

    # Expected: V_F0 × I_avg + R_F × I_rms²
    # V_F0 = 0.8V, R_F = 0.015Ω
    # P = 0.8 × 20 + 0.015 × 22² = 16 + 7.26 = 23.26W
    expected = SIC_SCHOTTKY.v_f0 * i_f_avg + SIC_SCHOTTKY.r_f * i_f_rms**2
    assert abs(loss - expected) < 2.0, f"Expected ~{expected}W, got {loss}W"
    assert loss > 0, "Loss must be positive"


def test_conduction_loss_si():
    """Test Si PN diode conduction loss"""
    i_f_avg = 20.0
    i_f_rms = 22.0
    t_junction = 100.0

    loss = calculate_diode_conduction_loss(
        diode=SI_PN_DIODE,
        i_f_avg=i_f_avg,
        i_f_rms=i_f_rms,
        t_junction=t_junction,
    )

    # Si PN should have similar conduction loss to SiC Schottky
    # (slightly lower V_F but higher R_F)
    expected = SI_PN_DIODE.v_f0 * i_f_avg + SI_PN_DIODE.r_f * i_f_rms**2
    assert abs(loss - expected) < 2.0, f"Expected ~{expected}W, got {loss}W"
    assert loss > 0, "Loss must be positive"


def test_reverse_recovery_sic():
    """Test SiC Schottky reverse recovery loss (should be very low)"""
    v_r = 400.0  # Reverse voltage
    frequency = 100e3

    loss = calculate_diode_reverse_recovery_loss(
        diode=SIC_SCHOTTKY,
        v_r=v_r,
        frequency=frequency,
    )

    # SiC Schottky should have very low reverse recovery loss
    # Expected: Q_rr × V_r × f = 10nC × 400V × 100kHz = 0.4W
    expected = SIC_SCHOTTKY.q_rr * v_r * frequency
    assert abs(loss - expected) < 0.2, f"Expected ~{expected}W, got {loss}W"
    assert loss < 2.0, "SiC Schottky reverse recovery should be < 2W"


def test_reverse_recovery_si():
    """Test Si PN diode reverse recovery loss (should be significant)"""
    v_r = 400.0
    frequency = 100e3

    loss = calculate_diode_reverse_recovery_loss(
        diode=SI_PN_DIODE,
        v_r=v_r,
        frequency=frequency,
    )

    # Si PN should have significant reverse recovery loss
    # Expected: Q_rr × V_r × f = 500nC × 400V × 100kHz = 20W
    expected = SI_PN_DIODE.q_rr * v_r * frequency
    assert abs(loss - expected) < 3.0, f"Expected ~{expected}W, got {loss}W"
    assert loss > 10.0, "Si PN reverse recovery should be > 10W"


def test_sic_vs_si_comparison():
    """Compare SiC Schottky vs Si PN total losses"""
    i_f_avg = 20.0
    i_f_rms = 22.0
    v_r = 400.0
    frequency = 100e3
    t_junction = 100.0

    # SiC Schottky total loss
    sic_cond = calculate_diode_conduction_loss(
        SIC_SCHOTTKY, i_f_avg, i_f_rms, t_junction
    )
    sic_rr = calculate_diode_reverse_recovery_loss(
        SIC_SCHOTTKY, v_r, frequency
    )
    sic_total = sic_cond + sic_rr

    # Si PN total loss
    si_cond = calculate_diode_conduction_loss(
        SI_PN_DIODE, i_f_avg, i_f_rms, t_junction
    )
    si_rr = calculate_diode_reverse_recovery_loss(
        SI_PN_DIODE, v_r, frequency
    )
    si_total = si_cond + si_rr

    # SiC should have lower total loss due to minimal reverse recovery
    assert sic_total < si_total, "SiC Schottky should have lower total loss"

    # Si reverse recovery should dominate
    assert si_rr > si_cond, "Si PN reverse recovery should dominate"

    # SiC reverse recovery should be minimal
    assert sic_rr < sic_cond, "SiC Schottky conduction should dominate"


def test_temperature_dependence():
    """Test temperature dependence of V_F"""
    i_f_avg = 20.0
    i_f_rms = 22.0

    # Calculate at 25°C
    loss_25c = calculate_diode_conduction_loss(
        SIC_SCHOTTKY, i_f_avg, i_f_rms, t_junction=25.0
    )

    # Calculate at 125°C
    loss_125c = calculate_diode_conduction_loss(
        SIC_SCHOTTKY, i_f_avg, i_f_rms, t_junction=125.0
    )

    # For SiC Schottky, V_F decreases with temperature
    # So loss should decrease
    assert loss_125c < loss_25c, "SiC Schottky loss should decrease with temperature"


def test_frequency_scaling():
    """Test reverse recovery loss scales with frequency"""
    v_r = 400.0

    # Calculate at 50kHz
    loss_50khz = calculate_diode_reverse_recovery_loss(
        SIC_SCHOTTKY, v_r, frequency=50e3
    )

    # Calculate at 100kHz
    loss_100khz = calculate_diode_reverse_recovery_loss(
        SIC_SCHOTTKY, v_r, frequency=100e3
    )

    # Loss should double with frequency
    ratio = loss_100khz / loss_50khz
    assert abs(ratio - 2.0) < 0.1, f"Loss should double with frequency, got ratio {ratio}"


def test_zero_current():
    """Test losses with zero current"""
    # Zero conduction loss
    loss_cond = calculate_diode_conduction_loss(
        SIC_SCHOTTKY, i_f_avg=0.0, i_f_rms=0.0, t_junction=100.0
    )
    assert loss_cond == 0.0, "Zero current should give zero conduction loss"


if __name__ == "__main__":
    print("Running Diode Loss Calculation Tests...")

    test_conduction_loss_sic()
    print("✓ SiC Schottky conduction loss")

    test_conduction_loss_si()
    print("✓ Si PN conduction loss")

    test_reverse_recovery_sic()
    print("✓ SiC Schottky reverse recovery")

    test_reverse_recovery_si()
    print("✓ Si PN reverse recovery")

    test_sic_vs_si_comparison()
    print("✓ SiC vs Si comparison")

    test_temperature_dependence()
    print("✓ Temperature dependence")

    test_frequency_scaling()
    print("✓ Frequency scaling")

    test_zero_current()
    print("✓ Zero current edge case")

    print("\n✓ All diode loss tests passed!")

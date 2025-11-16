"""
Unit Tests: System Analyzer

Tests for complete PSFB system loss analysis.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from psfb_loss_analyzer import (
    MOSFETParameters,
    DiodeParameters,
    CapacitanceVsVoltage,
    CapacitorParameters,
    MagneticComponents,
    MagneticDesignResult,
    CoreGeometry,
    WindingDesign,
    analyze_psfb_phase,
    analyze_psfb_system,
)


# Test components
TEST_MOSFET = MOSFETParameters(
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

TEST_DIODE = DiodeParameters(
    part_number="TEST_DIODE",
    v_rrm=1200.0,
    i_f_avg=30.0,
    v_f0=0.8,
    r_f=0.015,
    v_f_25c=1.5,
    v_f_125c=1.3,
    t_rr=20e-9,
    q_rr=10e-9,
    c_j0=500e-12,
)

# Test magnetic components
TEST_MAGNETICS = MagneticComponents(
    resonant_inductor=MagneticDesignResult(
        core_name="PQ20/16",
        core_geometry=CoreGeometry(
            effective_area=62e-6,
            effective_length=42e-3,
            effective_volume=2600e-9,
            window_area=45e-6,
        ),
        n_primary=25,
        primary_winding=WindingDesign(
            wire_diameter=1.0e-3,
            num_strands=5,
            layers=2,
        ),
        inductance=15e-6,
        core_loss=1.5,
        copper_loss=0.8,
    ),
    transformer=MagneticDesignResult(
        core_name="PQ32/30",
        core_geometry=CoreGeometry(
            effective_area=161e-6,
            effective_length=70e-3,
            effective_volume=11000e-9,
            window_area=150e-6,
        ),
        n_primary=40,
        n_secondary=5,
        primary_winding=WindingDesign(
            wire_diameter=0.8e-3,
            num_strands=10,
            layers=2,
        ),
        secondary_winding=WindingDesign(
            wire_diameter=1.5e-3,
            num_strands=20,
            layers=1,
        ),
        core_loss=8.5,
        copper_loss=12.0,
    ),
    output_inductor=MagneticDesignResult(
        core_name="PQ26/25",
        core_geometry=CoreGeometry(
            effective_area=133e-6,
            effective_length=60e-3,
            effective_volume=8000e-9,
            window_area=100e-6,
        ),
        n_primary=15,
        primary_winding=WindingDesign(
            wire_diameter=1.2e-3,
            num_strands=15,
            layers=1,
        ),
        inductance=10e-6,
        core_loss=3.2,
        copper_loss=4.5,
    ),
)

# Test capacitors
TEST_INPUT_CAP = CapacitorParameters(
    capacitance=100e-6,  # 100µF
    voltage_rating=450.0,
    esr=0.02,  # 20mΩ
    technology="Film",
)

TEST_OUTPUT_CAP = CapacitorParameters(
    capacitance=1000e-6,  # 1000µF
    voltage_rating=75.0,
    esr=0.005,  # 5mΩ
    technology="Electrolytic",
)


def test_single_phase_analysis():
    """Test single-phase PSFB analysis"""
    result = analyze_psfb_phase(
        input_voltage=400.0,
        output_voltage=48.0,
        output_power=3000.0,
        frequency=100e3,
        duty_cycle=0.45,
        turns_ratio=8.0,
        primary_mosfet=TEST_MOSFET,
        secondary_diode=TEST_DIODE,
        magnetics=TEST_MAGNETICS,
        zvs_operation=True,
        t_junction_mosfet=100.0,
        t_junction_diode=100.0,
    )

    # Total losses should be reasonable
    assert 50.0 < result.total_losses < 500.0, \
        f"Total loss {result.total_losses}W outside expected range"

    # Efficiency should be high (> 90%)
    assert result.efficiency > 0.90, \
        f"Efficiency {result.efficiency:.1%} too low"

    # Individual loss components should be positive
    assert result.mosfet_conduction_loss > 0
    assert result.mosfet_switching_loss >= 0  # May be zero if ZVS
    assert result.diode_conduction_loss > 0
    assert result.magnetic_losses > 0


def test_multiphase_system_analysis():
    """Test multi-phase system analysis"""
    result = analyze_psfb_system(
        input_voltage=400.0,
        output_voltage=48.0,
        output_power=6600.0,  # 6.6kW total
        frequency=100e3,
        duty_cycle=0.45,
        turns_ratio=8.0,
        n_phases=3,
        phase_shift_deg=120.0,  # 3-phase @ 120°
        primary_mosfet=TEST_MOSFET,
        secondary_diode=TEST_DIODE,
        magnetics=TEST_MAGNETICS,
        input_capacitor=TEST_INPUT_CAP,
        output_capacitor=TEST_OUTPUT_CAP,
        zvs_operation=True,
        t_junction_mosfet=100.0,
        t_junction_diode=100.0,
    )

    # Total losses should be reasonable for 6.6kW
    assert 100.0 < result.total_losses < 1000.0, \
        f"Total loss {result.total_losses}W outside expected range"

    # Efficiency should be high
    assert result.efficiency > 0.90, \
        f"Efficiency {result.efficiency:.1%} too low"

    # Number of phases should match
    assert len(result.per_phase_losses) == 3, "Should have 3 phases"

    # Each phase should carry ~1/3 of total power
    for phase_loss in result.per_phase_losses:
        # Each phase: 2.2kW, losses should be ~30-100W per phase
        assert 20.0 < phase_loss.total_losses < 200.0


def test_efficiency_vs_load():
    """Test efficiency at different load points"""
    load_points = [0.25, 0.50, 0.75, 1.00]  # 25%, 50%, 75%, 100% load
    efficiencies = []

    for load_fraction in load_points:
        power = 3000.0 * load_fraction

        result = analyze_psfb_phase(
            input_voltage=400.0,
            output_voltage=48.0,
            output_power=power,
            frequency=100e3,
            duty_cycle=0.45,
            turns_ratio=8.0,
            primary_mosfet=TEST_MOSFET,
            secondary_diode=TEST_DIODE,
            magnetics=TEST_MAGNETICS,
            zvs_operation=True,
            t_junction_mosfet=100.0,
            t_junction_diode=100.0,
        )

        efficiencies.append(result.efficiency)

    # Peak efficiency typically at 50-75% load
    peak_eff = max(efficiencies)
    peak_idx = efficiencies.index(peak_eff)

    # Peak should not be at 100% load (due to fixed losses)
    assert peak_idx < len(efficiencies) - 1, "Peak efficiency should not be at full load"

    # Efficiency should be reasonable at all load points
    for eff in efficiencies:
        assert eff > 0.85, f"Efficiency {eff:.1%} too low"


def test_capacitor_losses():
    """Test capacitor ESR losses"""
    result = analyze_psfb_system(
        input_voltage=400.0,
        output_voltage=48.0,
        output_power=3000.0,
        frequency=100e3,
        duty_cycle=0.45,
        turns_ratio=8.0,
        n_phases=1,
        phase_shift_deg=0.0,
        primary_mosfet=TEST_MOSFET,
        secondary_diode=TEST_DIODE,
        magnetics=TEST_MAGNETICS,
        input_capacitor=TEST_INPUT_CAP,
        output_capacitor=TEST_OUTPUT_CAP,
        zvs_operation=True,
        t_junction_mosfet=100.0,
        t_junction_diode=100.0,
    )

    # Capacitor losses should be present
    assert result.input_cap_loss >= 0
    assert result.output_cap_loss >= 0

    # Capacitor losses should be small compared to total
    total_cap_loss = result.input_cap_loss + result.output_cap_loss
    assert total_cap_loss < result.total_losses * 0.2, \
        "Capacitor losses should be < 20% of total"


def test_zvs_vs_non_zvs():
    """Compare ZVS vs non-ZVS operation"""
    # With ZVS
    result_zvs = analyze_psfb_phase(
        input_voltage=400.0,
        output_voltage=48.0,
        output_power=3000.0,
        frequency=100e3,
        duty_cycle=0.45,
        turns_ratio=8.0,
        primary_mosfet=TEST_MOSFET,
        secondary_diode=TEST_DIODE,
        magnetics=TEST_MAGNETICS,
        zvs_operation=True,
        t_junction_mosfet=100.0,
        t_junction_diode=100.0,
    )

    # Without ZVS
    result_no_zvs = analyze_psfb_phase(
        input_voltage=400.0,
        output_voltage=48.0,
        output_power=3000.0,
        frequency=100e3,
        duty_cycle=0.45,
        turns_ratio=8.0,
        primary_mosfet=TEST_MOSFET,
        secondary_diode=TEST_DIODE,
        magnetics=TEST_MAGNETICS,
        zvs_operation=False,
        t_junction_mosfet=100.0,
        t_junction_diode=100.0,
    )

    # ZVS should have lower switching losses
    assert result_zvs.mosfet_switching_loss < result_no_zvs.mosfet_switching_loss, \
        "ZVS should reduce switching losses"

    # ZVS should have higher efficiency
    assert result_zvs.efficiency > result_no_zvs.efficiency, \
        "ZVS should improve efficiency"


if __name__ == "__main__":
    print("Running System Analyzer Tests...")

    test_single_phase_analysis()
    print("✓ Single-phase analysis")

    test_multiphase_system_analysis()
    print("✓ Multi-phase system analysis")

    test_efficiency_vs_load()
    print("✓ Efficiency vs load")

    test_capacitor_losses()
    print("✓ Capacitor losses")

    test_zvs_vs_non_zvs()
    print("✓ ZVS vs non-ZVS comparison")

    print("\n✓ All system analyzer tests passed!")

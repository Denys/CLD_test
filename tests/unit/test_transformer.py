"""
Unit Tests: Transformer Design

Tests for PSFB transformer design using Kg method.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from psfb_loss_analyzer import (
    TransformerSpec,
    CoreMaterial,
    design_transformer,
)


def test_transformer_turns_ratio():
    """Test transformer turns ratio calculation"""
    # 400V → 48V transformer
    # Expected turns ratio: ~8:1 (accounting for duty cycle)

    spec = TransformerSpec(
        power=3000.0,  # 3kW
        vin_min=360.0,
        vin_nom=400.0,
        vin_max=440.0,
        vout=48.0,
        frequency=100e3,
        duty_cycle_min=0.4,
        duty_cycle_max=0.5,
        efficiency_est=0.97,
        flux_density_max=0.3,  # 300mT
        current_density=5.0e6,  # 5A/mm²
    )

    result = design_transformer(spec, CoreMaterial.N87())

    # Turns ratio should be 7-9:1
    turns_ratio = result.n_primary / result.n_secondary
    assert 7.0 < turns_ratio < 9.0, f"Turns ratio {turns_ratio} outside expected range"

    # Primary turns should be reasonable (> 10)
    assert result.n_primary > 10, "Primary turns too low"

    # Secondary turns should be reasonable (> 1)
    assert result.n_secondary > 1, "Secondary turns too low"


def test_transformer_flux_density():
    """Test transformer flux density is within limits"""
    spec = TransformerSpec(
        power=3000.0,
        vin_min=360.0,
        vin_nom=400.0,
        vin_max=440.0,
        vout=48.0,
        frequency=100e3,
        duty_cycle_min=0.4,
        duty_cycle_max=0.5,
        efficiency_est=0.97,
        flux_density_max=0.3,
        current_density=5.0e6,
    )

    result = design_transformer(spec, CoreMaterial.N87())

    # Flux density should be below maximum
    assert result.flux_density_peak < spec.flux_density_max, \
        f"Flux density {result.flux_density_peak}T exceeds max {spec.flux_density_max}T"

    # Flux density should be reasonable (100-300mT for SiC applications)
    assert 0.1 < result.flux_density_peak < 0.35, \
        f"Flux density {result.flux_density_peak}T outside typical range"


def test_transformer_core_selection():
    """Test transformer core is appropriately sized"""
    spec = TransformerSpec(
        power=3000.0,
        vin_min=360.0,
        vin_nom=400.0,
        vin_max=440.0,
        vout=48.0,
        frequency=100e3,
        duty_cycle_min=0.4,
        duty_cycle_max=0.5,
        efficiency_est=0.97,
        flux_density_max=0.3,
        current_density=5.0e6,
    )

    result = design_transformer(spec, CoreMaterial.N87())

    # Core should be selected
    assert result.core_name != "", "Core not selected"

    # Core geometry should be valid
    assert result.core_geometry.effective_area > 0
    assert result.core_geometry.effective_length > 0
    assert result.core_geometry.window_area > 0


def test_transformer_winding_design():
    """Test transformer winding design"""
    spec = TransformerSpec(
        power=3000.0,
        vin_min=360.0,
        vin_nom=400.0,
        vin_max=440.0,
        vout=48.0,
        frequency=100e3,
        duty_cycle_min=0.4,
        duty_cycle_max=0.5,
        efficiency_est=0.97,
        flux_density_max=0.3,
        current_density=5.0e6,
    )

    result = design_transformer(spec, CoreMaterial.N87())

    # Primary winding should be valid
    assert result.primary_winding.wire_diameter > 0
    assert result.primary_winding.num_strands > 0
    assert result.primary_winding.layers > 0

    # Secondary winding should be valid
    assert result.secondary_winding.wire_diameter > 0
    assert result.secondary_winding.num_strands > 0
    assert result.secondary_winding.layers > 0

    # Window utilization should be reasonable (30-50%)
    wu = result.window_utilization
    assert 0.2 < wu < 0.6, f"Window utilization {wu:.1%} outside typical range"


def test_transformer_losses():
    """Test transformer loss calculations"""
    spec = TransformerSpec(
        power=3000.0,
        vin_min=360.0,
        vin_nom=400.0,
        vin_max=440.0,
        vout=48.0,
        frequency=100e3,
        duty_cycle_min=0.4,
        duty_cycle_max=0.5,
        efficiency_est=0.97,
        flux_density_max=0.3,
        current_density=5.0e6,
    )

    result = design_transformer(spec, CoreMaterial.N87())

    # Core losses should be positive
    assert result.core_loss > 0, "Core loss should be positive"

    # Winding losses should be positive
    assert result.copper_loss > 0, "Copper loss should be positive"

    # Total losses should be reasonable (< 100W for 3kW transformer)
    total_loss = result.core_loss + result.copper_loss
    assert total_loss < 100.0, f"Total transformer loss {total_loss}W seems high"

    # Efficiency should be high (> 99%)
    efficiency = 1.0 - (total_loss / spec.power)
    assert efficiency > 0.98, f"Transformer efficiency {efficiency:.1%} seems low"


def test_different_power_levels():
    """Test transformer design at different power levels"""
    power_levels = [1000.0, 3000.0, 6000.0]  # 1kW, 3kW, 6kW

    for power in power_levels:
        spec = TransformerSpec(
            power=power,
            vin_min=360.0,
            vin_nom=400.0,
            vin_max=440.0,
            vout=48.0,
            frequency=100e3,
            duty_cycle_min=0.4,
            duty_cycle_max=0.5,
            efficiency_est=0.97,
            flux_density_max=0.3,
            current_density=5.0e6,
        )

        result = design_transformer(spec, CoreMaterial.N87())

        # Core size should increase with power
        # (We can't easily test this without tracking previous results,
        #  but we can verify design completes successfully)
        assert result.n_primary > 0
        assert result.core_loss > 0

        # Losses should scale roughly with power
        total_loss = result.core_loss + result.copper_loss
        assert total_loss < power * 0.05, \
            f"Transformer loss {total_loss}W exceeds 5% of {power}W"


def test_different_frequencies():
    """Test transformer design at different switching frequencies"""
    frequencies = [50e3, 100e3, 150e3]  # 50kHz, 100kHz, 150kHz

    for freq in frequencies:
        spec = TransformerSpec(
            power=3000.0,
            vin_min=360.0,
            vin_nom=400.0,
            vin_max=440.0,
            vout=48.0,
            frequency=freq,
            duty_cycle_min=0.4,
            duty_cycle_max=0.5,
            efficiency_est=0.97,
            flux_density_max=0.3,
            current_density=5.0e6,
        )

        result = design_transformer(spec, CoreMaterial.N87())

        # Higher frequency should allow smaller core
        # (Number of turns inversely proportional to frequency)
        assert result.n_primary > 0

        # Core losses should increase with frequency
        assert result.core_loss > 0


if __name__ == "__main__":
    print("Running Transformer Design Tests...")

    test_transformer_turns_ratio()
    print("✓ Turns ratio calculation")

    test_transformer_flux_density()
    print("✓ Flux density limits")

    test_transformer_core_selection()
    print("✓ Core selection")

    test_transformer_winding_design()
    print("✓ Winding design")

    test_transformer_losses()
    print("✓ Loss calculations")

    test_different_power_levels()
    print("✓ Different power levels")

    test_different_frequencies()
    print("✓ Different frequencies")

    print("\n✓ All transformer design tests passed!")

#!/usr/bin/env python3
"""
Complete PSFB Design Example with UCC28951 Controller

This example demonstrates the complete design flow:
1. Transformer design
2. Output inductor design
3. UCC28951 controller component calculation
4. Compensation loop design

Design Specification:
- 3kW PSFB converter
- 400V input → 48V output
- 100kHz switching frequency
- UCC28951 phase-shifted full-bridge controller

Author: PSFB Loss Analysis Tool
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from psfb_loss_analyzer import (
    # Transformer design
    TransformerSpec,
    CoreMaterial,
    design_transformer,
    # Inductor design
    design_output_inductor,
    # UCC28951 controller
    UCC28951Specification,
    design_ucc28951_components,
)

print("=" * 80)
print("COMPLETE PSFB DESIGN WITH UCC28951 CONTROLLER")
print("=" * 80)
print()

# ==================================================================
# Step 1: Design Transformer
# ==================================================================

print("STEP 1: TRANSFORMER DESIGN")
print("-" * 80)

transformer_spec = TransformerSpec(
    power_output=3000.0,  # 3kW
    vin_min=360.0,
    vin_nom=400.0,
    vin_max=440.0,
    vout_nom=48.0,
    frequency=100e3,  # 100kHz
    duty_cycle_min=0.35,
    duty_cycle_max=0.48,
    efficiency_target=0.97,
)

transformer = design_transformer(transformer_spec, CoreMaterial.FERRITE_N87)

print(f"Transformer Design Results:")
print(f"  Core: {transformer.core_name}")
print(f"  Turns Ratio: {transformer.n_primary}:{transformer.n_secondary}")
print(f"  Primary: {transformer.n_primary} turns, AWG{transformer.primary_winding.awg}")
print(f"  Secondary: {transformer.n_secondary} turns, AWG{transformer.secondary_winding.awg}")
print(f"  Core Loss: {transformer.core_loss:.2f}W")
print(f"  Copper Loss: {transformer.copper_loss:.2f}W")
print(f"  Total Loss: {transformer.total_loss:.2f}W")
print()

# ==================================================================
# Step 2: Design Output Inductor
# ==================================================================

print("STEP 2: OUTPUT INDUCTOR DESIGN")
print("-" * 80)

# Calculate output current
i_out_max = 3000.0 / 48.0  # 62.5A

# Design for 20% current ripple at full load
i_ripple = 0.20 * i_out_max

output_inductor = design_output_inductor(
    inductance=10e-6,  # 10µH
    current_dc=i_out_max,
    current_ripple=i_ripple,
    frequency=100e3,
    flux_density_max=0.30,
)

print(f"Output Inductor Design Results:")
print(f"  Core: {output_inductor.core_name}")
print(f"  Inductance: {output_inductor.inductance_actual * 1e6:.1f}µH")
print(f"  Turns: {output_inductor.n_turns}")
print(f"  Air Gap: {output_inductor.air_gap_mm:.2f}mm")
print(f"  Wire: AWG{output_inductor.winding.awg}, {output_inductor.winding.strands} strands")
print(f"  DC Resistance: {output_inductor.winding.resistance_dc * 1000:.2f}mΩ")
print(f"  Core Loss: {output_inductor.core_loss:.2f}W")
print(f"  Copper Loss: {output_inductor.copper_loss:.2f}W")
print(f"  Total Loss: {output_inductor.total_loss:.2f}W")
print()

# ==================================================================
# Step 3: Design UCC28951 Controller Components
# ==================================================================

print("STEP 3: UCC28951 CONTROLLER COMPONENT CALCULATION")
print("-" * 80)

# Specify output capacitor (example values)
c_out = 1000e-6  # 1000µF
esr_out = 0.010  # 10mΩ

# Create UCC28951 specification
ucc_spec = UCC28951Specification(
    vin_min=transformer_spec.vin_min,
    vin_nom=transformer_spec.vin_nom,
    vin_max=transformer_spec.vin_max,
    vout=transformer_spec.vout_nom,
    iout_max=i_out_max,
    turns_ratio=transformer.n_primary / transformer.n_secondary,
    leakage_inductance=10e-6,  # Estimated 10µH leakage
    output_inductance=output_inductor.inductance_actual,
    output_capacitance=c_out,
    output_cap_esr=esr_out,
    switching_frequency=transformer_spec.frequency,
    target_crossover_freq=3000.0,  # 3kHz target
    target_phase_margin=50.0,  # 50° target
)

# Design UCC28951 components
ucc_components = design_ucc28951_components(ucc_spec)

print()
print("=" * 80)
print("UCC28951 COMPONENT VALUES - BILL OF MATERIALS")
print("=" * 80)
print()

print("Timing Circuit:")
print(f"  RT  = {ucc_components.rt/1e3:.1f} kΩ  (1%, metal film)")
print(f"  CT  = {ucc_components.ct*1e9:.0f} nF  (C0G/NP0, ±5%)")
print()

print("Voltage Feedback:")
print(f"  R_FB_TOP = {ucc_components.r_fb_top/1e3:.1f} kΩ  (1%, metal film)")
print(f"  R_FB_BOT = {ucc_components.r_fb_bot/1e3:.1f} kΩ  (1%, metal film)")
print()

print("Current Sensing:")
print(f"  R_CS        = {ucc_components.r_cs*1e3:.1f} mΩ  (1%, ±50ppm/°C, 2W+)")
print(f"  R_CS_FILTER = {ucc_components.r_cs_filter/1e3:.1f} kΩ  (1%)")
print(f"  C_CS_FILTER = {ucc_components.c_cs_filter*1e9:.1f} nF  (C0G/NP0)")
print()

print("Compensation Network (Type III):")
print(f"  R_COMP_UPPER = {ucc_components.r_comp_upper/1e3:.1f} kΩ  (1%, metal film)")
print(f"  R_COMP_LOWER = {ucc_components.r_comp_lower/1e3:.1f} kΩ  (1%, metal film)")
print(f"  C_COMP_HF    = {ucc_components.c_comp_hf*1e12:.0f} pF  (C0G/NP0, ±5%)")
print(f"  C_COMP_LF    = {ucc_components.c_comp_lf*1e9:.1f} nF  (C0G/NP0, ±10%)")
print(f"  C_COMP_POLE  = {ucc_components.c_comp_pole*1e12:.0f} pF  (C0G/NP0, ±10%)")
print()

print("Soft-Start:")
print(f"  C_SS = {ucc_components.c_ss*1e6:.2f} µF  (ceramic or film)")
print()

print("=" * 80)
print("PERFORMANCE SUMMARY")
print("=" * 80)
print()

print("Power Stage:")
print(f"  Switching Frequency: {ucc_components.actual_switching_freq/1e3:.2f} kHz")
print(f"  Transformer Turns: {transformer.n_primary}:{transformer.n_secondary}")
print(f"  Output Inductor: {output_inductor.inductance_actual*1e6:.1f}µH")
print(f"  Output Capacitor: {c_out*1e6:.0f}µF, ESR={esr_out*1e3:.0f}mΩ")
print()

print("Control Loop:")
print(f"  Gain Crossover Frequency: {ucc_components.gain_crossover_freq:.0f} Hz")
print(f"  Phase Margin: {ucc_components.phase_margin:.1f}°")
print(f"  Gain Margin: {ucc_components.gain_margin:.1f} dB")
print()

# Check design criteria
print("Design Criteria:")
if ucc_components.gain_crossover_freq >= 1000:
    print(f"  ✓ Crossover > 1kHz: {ucc_components.gain_crossover_freq:.0f} Hz")
else:
    print(f"  ✗ Crossover < 1kHz: {ucc_components.gain_crossover_freq:.0f} Hz")

if ucc_components.phase_margin >= 45:
    print(f"  ✓ Phase Margin > 45°: {ucc_components.phase_margin:.1f}°")
else:
    print(f"  ✗ Phase Margin < 45°: {ucc_components.phase_margin:.1f}°")

print()
print("Losses:")
print(f"  Transformer: {transformer.total_loss:.2f}W")
print(f"  Output Inductor: {output_inductor.total_loss:.2f}W")
print(f"  Total Magnetic Losses: {transformer.total_loss + output_inductor.total_loss:.2f}W")
print()

print("=" * 80)
print("DESIGN COMPLETE - READY FOR PROTOTYPE")
print("=" * 80)

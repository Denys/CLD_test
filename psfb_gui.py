#!/usr/bin/env python3
"""
PSFB Loss Analyzer - Graphical User Interface

Web-based GUI using Gradio for interactive PSFB converter analysis.

Complete 8-tab interface:
    1. MOSFET Loss Analysis - Component library and loss calculations
    2. Diode Loss Analysis - SiC/Si diode loss calculations
    3. Datasheet Parser - Drag & drop PDF parameter extraction
    4. System Analysis - Multi-phase PSFB system analyzer
    5. Magnetic Design - Transformer and inductor design
    6. Optimizer - Automated design optimization with Pareto frontier
    7. UCC28951 Controller - TI controller component calculation with Bode plots
    8. About - Documentation and references

Usage:
    python psfb_gui.py

Then open browser to: http://localhost:7860

Author: PSFB Loss Analysis Tool
Version: 1.0.0 - Complete GUI Interface
"""

import sys
from pathlib import Path
import numpy as np
import warnings

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import gradio as gr
except ImportError:
    print("Gradio not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "gradio"])
    import gradio as gr

from psfb_loss_analyzer import (
    MOSFETParameters,
    DiodeParameters,
    CapacitanceVsVoltage,
    calculate_mosfet_conduction_loss,
    calculate_mosfet_switching_loss,
    calculate_mosfet_gate_drive_loss,
    calculate_diode_conduction_loss,
    calculate_diode_reverse_recovery_loss,
    MOSFET_LIBRARY_SIC,
    MOSFET_LIBRARY_SI,
    DIODE_LIBRARY_SIC,
    DIODE_LIBRARY_SI,
    get_all_mosfets,
    get_all_diodes,
    # System analysis
    analyze_psfb_phase,
    analyze_psfb_system,
    # Magnetic design
    TransformerSpec,
    CoreMaterial,
    design_transformer,
    design_resonant_inductor,
    design_output_inductor,
    # Optimizer
    DesignSpecification,
    optimize_design,
    ObjectiveFunction,
    # UCC28951 Controller
    UCC28951Specification,
    design_ucc28951_components,
)

# ============================================================================
# Helper Functions
# ============================================================================

def get_mosfet_part_numbers():
    """Get list of available MOSFET part numbers"""
    mosfets = get_all_mosfets()
    return list(mosfets.keys())

def get_diode_part_numbers():
    """Get list of available diode part numbers"""
    diodes = get_all_diodes()
    return list(diodes.keys())

def load_mosfet_from_library(part_number):
    """Load MOSFET parameters from library"""
    mosfets = get_all_mosfets()
    if part_number in mosfets:
        mosfet_data = mosfets[part_number]
        mosfet = mosfet_data["device"]

        return (
            mosfet.v_dss,
            mosfet.i_d_continuous,
            mosfet.r_dson_25c * 1000,  # Convert to mΩ
            mosfet.r_dson_150c * 1000,
            mosfet.q_g * 1e9,  # Convert to nC
            mosfet.q_gs * 1e9,
            mosfet.q_gd * 1e9,
            mosfet.capacitances.c_iss_constant * 1e12,  # Convert to pF
            mosfet.capacitances.c_oss_constant * 1e12,
            mosfet.capacitances.c_rss_constant * 1e12,
        )
    return (650, 90, 20, 28, 142, 38, 52, 7200, 520, 15)

def load_diode_from_library(part_number):
    """Load diode parameters from library"""
    diodes = get_all_diodes()
    if part_number in diodes:
        diode_data = diodes[part_number]
        diode = diode_data["device"]

        return (
            diode.v_rrm,
            diode.i_f_avg,
            diode.v_f_25c,
            diode.v_f_125c,
            diode.t_rr * 1e9,  # Convert to ns
            diode.q_rr * 1e9,  # Convert to nC
        )
    return (1200, 30, 1.5, 1.3, 20, 10)

# ============================================================================
# Tab 1: MOSFET Loss Analysis
# ============================================================================

def calculate_mosfet_losses(
    part_number,
    v_dss, i_d, r_dson_25c, r_dson_150c,
    q_g, q_gs, q_gd,
    c_iss, c_oss, c_rss,
    i_rms, v_ds, frequency, duty_cycle, t_junction, v_gs_drive
):
    """Calculate MOSFET losses with all breakdown"""
    try:
        # Create MOSFET object
        mosfet = MOSFETParameters(
            part_number=part_number,
            v_dss=float(v_dss),
            i_d_continuous=float(i_d),
            r_dson_25c=float(r_dson_25c) / 1000,  # mΩ to Ω
            r_dson_25c_max=float(r_dson_25c) * 1.15 / 1000,
            r_dson_150c=float(r_dson_150c) / 1000,
            r_dson_150c_max=float(r_dson_150c) * 1.15 / 1000,
            capacitances=CapacitanceVsVoltage(
                c_iss_constant=float(c_iss) / 1e12,  # pF to F
                c_oss_constant=float(c_oss) / 1e12,
                c_rss_constant=float(c_rss) / 1e12,
            ),
            q_g=float(q_g) / 1e9,  # nC to C
            q_gs=float(q_gs) / 1e9,
            q_gd=float(q_gd) / 1e9,
            v_gs_plateau=4.5,
            t_r=25e-9,
            t_f=20e-9,
        )

        # Calculate losses
        p_cond = calculate_mosfet_conduction_loss(
            mosfet, float(i_rms), float(duty_cycle), float(t_junction)
        )

        p_sw = calculate_mosfet_switching_loss(
            mosfet, float(v_ds), float(i_rms) / duty_cycle if duty_cycle > 0 else float(i_rms),
            float(frequency) * 1000, float(t_junction)
        )

        p_gate = calculate_mosfet_gate_drive_loss(
            mosfet, float(v_gs_drive), float(frequency) * 1000
        )

        p_coss = 0.5 * mosfet.capacitances.get_c_oss(float(v_ds)) * float(v_ds)**2 * float(frequency) * 1000

        p_total = p_cond + p_sw + p_gate + p_coss

        # Create results text
        results = f"""
## Loss Breakdown for {part_number}

### Total Loss: **{p_total:.2f} W**

| Loss Type | Power (W) | Percentage |
|-----------|-----------|------------|
| Conduction | {p_cond:.2f} | {100*p_cond/p_total:.1f}% |
| Switching | {p_sw:.2f} | {100*p_sw/p_total:.1f}% |
| Gate Drive | {p_gate:.2f} | {100*p_gate/p_total:.1f}% |
| C_oss | {p_coss:.2f} | {100*p_coss/p_total:.1f}% |

### Operating Conditions
- Junction Temperature: {t_junction}°C
- RMS Current: {i_rms} A
- Switching Voltage: {v_ds} V
- Frequency: {frequency} kHz
- Duty Cycle: {duty_cycle}

### Efficiency Impact
For {(v_ds * i_rms * duty_cycle):.0f}W output power:
- Power loss: {p_total:.2f}W
- Approximate efficiency: {100 * (1 - p_total/(v_ds * i_rms * duty_cycle + p_total)):.2f}%
"""

        # Create pie chart data
        labels = ['Conduction', 'Switching', 'Gate Drive', 'C_oss']
        values = [p_cond, p_sw, p_gate, p_coss]

        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 6))
        colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
        ax.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
        ax.set_title(f'MOSFET Loss Breakdown - {part_number}\nTotal: {p_total:.2f}W')

        return results, fig

    except Exception as e:
        return f"Error: {str(e)}", None

# ============================================================================
# Tab 2: Diode Loss Analysis
# ============================================================================

def calculate_diode_losses(
    part_number,
    v_rrm, i_f_avg,
    v_f_25c, v_f_125c,
    t_rr, q_rr,
    i_f_avg_actual, i_f_rms, v_r, frequency, t_junction
):
    """Calculate diode losses"""
    try:
        # Create diode object
        diode = DiodeParameters(
            part_number=part_number,
            v_rrm=float(v_rrm),
            i_f_avg=float(i_f_avg),
            v_f0=0.8,
            r_f=0.015,
            v_f_25c=float(v_f_25c),
            v_f_125c=float(v_f_125c),
            t_rr=float(t_rr) / 1e9,  # ns to s
            q_rr=float(q_rr) / 1e9,  # nC to C
            c_j0=500e-12,
        )

        # Calculate losses
        p_cond = calculate_diode_conduction_loss(
            diode, float(i_f_avg_actual), float(i_f_rms), float(t_junction)
        )

        p_rr = calculate_diode_reverse_recovery_loss(
            diode, float(v_r), float(frequency) * 1000
        )

        p_total = p_cond + p_rr

        # Create results text
        results = f"""
## Loss Breakdown for {part_number}

### Total Loss: **{p_total:.2f} W**

| Loss Type | Power (W) | Percentage |
|-----------|-----------|------------|
| Conduction | {p_cond:.2f} | {100*p_cond/p_total:.1f}% |
| Reverse Recovery | {p_rr:.2f} | {100*p_rr/p_total:.1f}% |

### Operating Conditions
- Junction Temperature: {t_junction}°C
- Average Current: {i_f_avg_actual} A
- RMS Current: {i_f_rms} A
- Reverse Voltage: {v_r} V
- Frequency: {frequency} kHz

### Device Type
{"SiC Schottky (Low reverse recovery)" if q_rr < 50 else "Si PN Diode (Higher reverse recovery)"}
"""

        # Create pie chart
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 6))
        colors = ['#ff9999', '#66b3ff']
        ax.pie([p_cond, p_rr], labels=['Conduction', 'Reverse Recovery'],
               autopct='%1.1f%%', colors=colors, startangle=90)
        ax.set_title(f'Diode Loss Breakdown - {part_number}\nTotal: {p_total:.2f}W')

        return results, fig

    except Exception as e:
        return f"Error: {str(e)}", None

# ============================================================================
# Tab 3: Datasheet Parser
# ============================================================================

def parse_datasheet(file):
    """Parse uploaded PDF datasheet"""
    if file is None:
        return "No file uploaded", None

    try:
        from psfb_loss_analyzer.Datasheet_analyzer import DatasheetParser

        parser = DatasheetParser()
        result = parser.parse_datasheet(file.name)

        # Format results
        output = f"""
## Extraction Results

**Part Number:** {result.part_number}
**Manufacturer:** {result.manufacturer}
**Device Type:** {result.device_type.value}
**Overall Confidence:** {result.overall_confidence:.0%}

### Extracted Parameters

| Parameter | Value | Unit | Confidence | Source |
|-----------|-------|------|------------|--------|
"""

        for param_name, param in result.parameters.items():
            value_str = f"{param.value:.3e}" if param.value != 0 else "N/A"
            output += f"| {param.name} | {value_str} | {param.unit} | {param.confidence:.0%} | {param.source} |\n"

        if result.warnings:
            output += "\n### ⚠️ Warnings\n\n"
            for warning in result.warnings:
                output += f"- {warning}\n"

        output += "\n### Next Steps\n\n"
        output += "1. Review extracted parameters for accuracy\n"
        output += "2. Manually verify values from graphs (Q_g, capacitances)\n"
        output += "3. Click 'Add to Component Library' to save\n"

        return output, None

    except ImportError:
        return "Datasheet parser not available. Install: pip install pdfplumber PyPDF2", None
    except Exception as e:
        return f"Error parsing datasheet: {str(e)}", None

# ============================================================================
# Tab 4: System Analysis
# ============================================================================

def analyze_system(
    power_total, v_in, v_out, frequency,
    n_phases, phase_shift_deg,
    primary_mosfet, secondary_diode,
    t_junction_mosfet, t_junction_diode
):
    """Analyze complete PSFB system"""
    try:
        # Get components from library
        mosfets = get_all_mosfets()
        diodes = get_all_diodes()

        if primary_mosfet not in mosfets:
            return "Selected MOSFET not found in library", None, None
        if secondary_diode not in diodes:
            return "Selected diode not found in library", None, None

        mosfet = mosfets[primary_mosfet]["device"]
        diode = diodes[secondary_diode]["device"]

        # Calculate per-phase power
        power_per_phase = float(power_total) / int(n_phases)
        i_out = float(power_total) / float(v_out)
        i_out_per_phase = i_out / int(n_phases)

        # Analyze system
        from psfb_loss_analyzer.system_analyzer import SystemLossResult

        # For simplicity, create basic analysis
        duty_cycle = float(v_out) / (2 * float(v_in)) * 0.9  # Approximate

        # Calculate MOSFET losses (primary side)
        i_rms_primary = i_out_per_phase * float(v_out) / float(v_in) / duty_cycle
        p_mosfet_cond = calculate_mosfet_conduction_loss(
            mosfet, i_rms_primary, duty_cycle, float(t_junction_mosfet)
        )
        p_mosfet_sw = calculate_mosfet_switching_loss(
            mosfet, float(v_in), i_rms_primary / duty_cycle,
            float(frequency) * 1000, float(t_junction_mosfet)
        )
        p_mosfet_gate = calculate_mosfet_gate_drive_loss(
            mosfet, 18.0, float(frequency) * 1000
        )
        p_mosfet_total = p_mosfet_cond + p_mosfet_sw + p_mosfet_gate

        # Calculate diode losses (secondary side)
        p_diode_cond = calculate_diode_conduction_loss(
            diode, i_out_per_phase * 0.5, i_out_per_phase * 0.55,
            float(t_junction_diode)
        )
        p_diode_rr = calculate_diode_reverse_recovery_loss(
            diode, float(v_in), float(frequency) * 1000
        )
        p_diode_total = p_diode_cond + p_diode_rr

        # Estimate magnetic losses (simplified)
        p_magnetic = power_per_phase * 0.015  # 1.5% estimate

        # Estimate capacitor losses
        p_capacitor = power_per_phase * 0.005  # 0.5% estimate

        # Total per-phase loss
        p_phase_total = (p_mosfet_total * 4 +  # 4 MOSFETs per phase
                        p_diode_total * 2 +     # 2 diodes per phase
                        p_magnetic + p_capacitor)

        # System totals
        p_system_total = p_phase_total * int(n_phases)
        efficiency = 100 * float(power_total) / (float(power_total) + p_system_total)

        # Create results
        results = f"""
## System Analysis Results

### Configuration
- **Total Power:** {power_total}W
- **Phases:** {n_phases} @ {phase_shift_deg}° phase shift
- **Input:** {v_in}V → **Output:** {v_out}V
- **Frequency:** {frequency}kHz

### Components
- **Primary MOSFET:** {primary_mosfet}
- **Secondary Diode:** {secondary_diode}

### System Performance
- **Total Loss:** {p_system_total:.2f}W
- **Efficiency:** {efficiency:.2f}%
- **Input Power:** {float(power_total) + p_system_total:.1f}W

### Loss Breakdown (Per Phase)

| Component | Loss (W) | Count | Total (W) | Percentage |
|-----------|----------|-------|-----------|------------|
| Primary MOSFETs | {p_mosfet_total:.2f} | 4 | {p_mosfet_total * 4:.2f} | {100 * p_mosfet_total * 4 / p_phase_total:.1f}% |
| Secondary Diodes | {p_diode_total:.2f} | 2 | {p_diode_total * 2:.2f} | {100 * p_diode_total * 2 / p_phase_total:.1f}% |
| Magnetics | {p_magnetic:.2f} | 1 | {p_magnetic:.2f} | {100 * p_magnetic / p_phase_total:.1f}% |
| Capacitors | {p_capacitor:.2f} | - | {p_capacitor:.2f} | {100 * p_capacitor / p_phase_total:.1f}% |
| **Phase Total** | - | - | **{p_phase_total:.2f}** | **100%** |

### System Totals
- **Per-Phase Loss:** {p_phase_total:.2f}W
- **System Loss:** {p_system_total:.2f}W ({int(n_phases)} phases)
"""

        # Create loss breakdown pie chart
        import matplotlib.pyplot as plt
        fig1, ax1 = plt.subplots(figsize=(8, 6))

        labels = ['MOSFETs', 'Diodes', 'Magnetics', 'Capacitors']
        values = [
            p_mosfet_total * 4,
            p_diode_total * 2,
            p_magnetic,
            p_capacitor
        ]
        colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']

        ax1.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
        ax1.set_title(f'Per-Phase Loss Breakdown\nTotal: {p_phase_total:.2f}W')

        # Create efficiency bar chart
        fig2, ax2 = plt.subplots(figsize=(8, 6))

        categories = ['Output\nPower', 'Losses', 'Input\nPower']
        heights = [float(power_total), p_system_total, float(power_total) + p_system_total]
        colors_bar = ['#90EE90', '#FF6B6B', '#4FC3F7']

        bars = ax2.bar(categories, heights, color=colors_bar, alpha=0.7)
        ax2.set_ylabel('Power (W)')
        ax2.set_title(f'System Power Flow - Efficiency: {efficiency:.2f}%')
        ax2.grid(axis='y', alpha=0.3)

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}W',
                    ha='center', va='bottom')

        return results, fig1, fig2

    except Exception as e:
        import traceback
        return f"Error: {str(e)}\n\n{traceback.format_exc()}", None, None

# ============================================================================
# Tab 5: Magnetic Design
# ============================================================================

def design_transformer_gui(
    power, vin_min, vin_nom, vin_max, vout, frequency,
    duty_min, duty_max, flux_density, current_density
):
    """Design transformer"""
    try:
        spec = TransformerSpec(
            power=float(power),
            vin_min=float(vin_min),
            vin_nom=float(vin_nom),
            vin_max=float(vin_max),
            vout=float(vout),
            frequency=float(frequency) * 1000,  # kHz to Hz
            duty_cycle_min=float(duty_min),
            duty_cycle_max=float(duty_max),
            efficiency_est=0.97,
            flux_density_max=float(flux_density),
            current_density=float(current_density) * 1e6,  # A/mm² to A/m²
        )

        # Try N87 material first
        result = design_transformer(spec, CoreMaterial.N87())

        results = f"""
## Transformer Design Results

### Specifications
- **Power:** {power}W
- **Input:** {vin_min}-{vin_max}V (nominal {vin_nom}V)
- **Output:** {vout}V
- **Frequency:** {frequency}kHz
- **Flux Density:** {flux_density}T
- **Current Density:** {current_density}A/mm²

### Design Summary
- **Turns Ratio:** {result.n_primary}:{result.n_secondary}
- **Core:** {result.core_name}
- **Core Material:** N87 (TDK)

### Winding Design

**Primary Winding:**
- Turns: {result.n_primary}
- Wire: AWG {result.primary_winding.awg} ({result.primary_winding.diameter_mm:.2f}mm)
- Strands: {result.primary_winding.strands}
- Layers: {result.primary_winding.layers}
- Resistance: {result.primary_winding.resistance_dc * 1000:.2f}mΩ

**Secondary Winding:**
- Turns: {result.n_secondary}
- Wire: AWG {result.secondary_winding.awg} ({result.secondary_winding.diameter_mm:.2f}mm)
- Strands: {result.secondary_winding.strands}
- Layers: {result.secondary_winding.layers}
- Resistance: {result.secondary_winding.resistance_dc * 1000:.2f}mΩ

### Loss Breakdown
- **Core Loss:** {result.core_loss:.2f}W
- **Copper Loss:** {result.copper_loss:.2f}W
- **Total Loss:** {result.total_loss:.2f}W
- **Efficiency:** {100 * (1 - result.total_loss / float(power)):.2f}%

### Operating Point
- **Flux Density:** {result.flux_density:.3f}T ({100 * result.flux_density / float(flux_density):.1f}% of max)
- **Primary Current:** {result.primary_current_rms:.2f}A RMS
- **Secondary Current:** {result.secondary_current_rms:.2f}A RMS
"""

        # Create loss breakdown chart
        import matplotlib.pyplot as plt
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # Loss pie chart
        labels = ['Core Loss', 'Copper Loss']
        values = [result.core_loss, result.copper_loss]
        colors = ['#ff9999', '#66b3ff']

        ax1.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
        ax1.set_title(f'Transformer Loss Breakdown\nTotal: {result.total_loss:.2f}W')

        # Operating point bar chart
        categories = ['Flux\nDensity', 'Pri\nCurrent', 'Sec\nCurrent']
        values_bar = [
            100 * result.flux_density / float(flux_density),
            result.primary_current_rms,
            result.secondary_current_rms
        ]
        colors_bar = ['#99ff99', '#ffcc99', '#ff9999']

        ax2.bar(categories, values_bar, color=colors_bar, alpha=0.7)
        ax2.set_ylabel('Flux Density (% of max) / Current (A)')
        ax2.set_title('Operating Parameters')
        ax2.grid(axis='y', alpha=0.3)

        return results, fig

    except Exception as e:
        import traceback
        return f"Error: {str(e)}\n\n{traceback.format_exc()}", None

def design_inductor_gui(
    inductor_type, inductance, current_dc, current_ripple,
    frequency, flux_density
):
    """Design inductor (resonant or output)"""
    try:
        import matplotlib.pyplot as plt

        if inductor_type == "Resonant Inductor (ZVS)":
            result = design_resonant_inductor(
                inductance=float(inductance) * 1e-6,  # µH to H
                current_rms=float(current_dc),
                frequency=float(frequency) * 1000,
                flux_density_max=float(flux_density),
            )

            results = f"""
## Resonant Inductor Design

### Specifications
- **Inductance:** {inductance}µH
- **RMS Current:** {current_dc}A
- **Frequency:** {frequency}kHz
- **Flux Density:** {flux_density}T

### Design
- **Core:** {result.core_name}
- **Turns:** {result.n_turns}
- **Air Gap:** {result.air_gap_mm:.2f}mm

### Winding
- **Wire:** AWG {result.winding.awg} ({result.winding.diameter_mm:.2f}mm)
- **Strands:** {result.winding.strands}
- **Layers:** {result.winding.layers}

### Performance
- **Core Loss:** {result.core_loss:.2f}W
- **Copper Loss:** {result.copper_loss:.2f}W
- **Total Loss:** {result.total_loss:.2f}W
"""
        else:  # Output Inductor
            result = design_output_inductor(
                inductance=float(inductance) * 1e-6,
                current_dc=float(current_dc),
                current_ripple=float(current_ripple),
                frequency=float(frequency) * 1000,
                flux_density_max=float(flux_density),
            )

            results = f"""
## Output Inductor Design

### Specifications
- **Inductance:** {inductance}µH
- **DC Current:** {current_dc}A
- **Ripple Current:** {current_ripple}A
- **Frequency:** {frequency}kHz
- **Flux Density:** {flux_density}T

### Design
- **Core:** {result.core_name}
- **Turns:** {result.n_turns}
- **Air Gap:** {result.air_gap_mm:.2f}mm

### Winding
- **Wire:** AWG {result.winding.awg} ({result.winding.diameter_mm:.2f}mm)
- **Strands:** {result.winding.strands}
- **Layers:** {result.winding.layers}

### Performance
- **Core Loss:** {result.core_loss:.2f}W
- **Copper Loss:** {result.copper_loss:.2f}W
- **Total Loss:** {result.total_loss:.2f}W
- **DC Resistance:** {result.winding.resistance_dc * 1000:.2f}mΩ
"""

        # Create visualization
        fig, ax = plt.subplots(figsize=(8, 6))

        labels = ['Core Loss', 'Copper Loss']
        values = [result.core_loss, result.copper_loss]
        colors = ['#ff9999', '#66b3ff']

        ax.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
        ax.set_title(f'{inductor_type} Loss Breakdown\nTotal: {result.total_loss:.2f}W')

        return results, fig

    except Exception as e:
        import traceback
        return f"Error: {str(e)}\n\n{traceback.format_exc()}", None

# ============================================================================
# Tab 6: Optimizer
# ============================================================================

def run_optimizer(
    power_min, power_rated, power_max,
    vin_min, vin_nom, vin_max,
    vout, n_phases,
    efficiency_target, objective_choice,
    max_eval
):
    """Run automated design optimization"""
    try:
        spec = DesignSpecification(
            power_min=float(power_min),
            power_rated=float(power_rated),
            power_max=float(power_max),
            vin_min=float(vin_min),
            vin_nom=float(vin_nom),
            vin_max=float(vin_max),
            vout_nom=float(vout),
            n_phases=int(n_phases),
            efficiency_target=float(efficiency_target) / 100,
            zvs_enable=True,
        )

        # Map objective
        objective_map = {
            "Maximum Efficiency": ObjectiveFunction.EFFICIENCY,
            "Minimum Cost": ObjectiveFunction.COST,
            "Balanced (Efficiency + Cost)": ObjectiveFunction.BALANCED,
        }
        objective = objective_map[objective_choice]

        # Run optimization
        result = optimize_design(
            spec=spec,
            objective=objective,
            max_evaluations=int(max_eval),
            verbose=True,
        )

        # Format results
        output = f"""
## Optimization Results

### Specification
- **Power:** {power_rated}W ({power_min}-{power_max}W)
- **Input:** {vin_min}-{vin_max}V (nominal {vin_nom}V)
- **Output:** {vout}V
- **Phases:** {n_phases}
- **Efficiency Target:** {efficiency_target}%
- **Objective:** {objective_choice}

### Design Space
- **Total Candidates:** {result.total_candidates}
- **Valid Designs:** {result.valid_designs_count}
- **Pareto Optimal:** {len(result.pareto_frontier)}

---

"""

        if result.best_efficiency:
            output += f"""
### 🏆 Best Efficiency Design
- **Primary MOSFET:** {result.best_efficiency.primary_mosfet_part}
- **Secondary Diode:** {result.best_efficiency.secondary_diode_part}
- **Frequency:** {result.best_efficiency.switching_frequency / 1000:.0f}kHz
- **Transformer:** {result.best_efficiency.transformer_core}
- **Turns Ratio:** {result.best_efficiency.turns_ratio:.1f}:1
- **Full Load Efficiency:** {result.best_efficiency.efficiency_full_load * 100:.2f}%
- **CEC Efficiency:** {result.best_efficiency.efficiency_cec * 100:.2f}%
- **Relative Cost:** {result.best_efficiency.relative_cost:.2f}×

"""

        if result.best_cost:
            output += f"""
### 💰 Best Cost Design
- **Primary MOSFET:** {result.best_cost.primary_mosfet_part}
- **Secondary Diode:** {result.best_cost.secondary_diode_part}
- **Frequency:** {result.best_cost.switching_frequency / 1000:.0f}kHz
- **Transformer:** {result.best_cost.transformer_core}
- **Turns Ratio:** {result.best_cost.turns_ratio:.1f}:1
- **Full Load Efficiency:** {result.best_cost.efficiency_full_load * 100:.2f}%
- **CEC Efficiency:** {result.best_cost.efficiency_cec * 100:.2f}%
- **Relative Cost:** {result.best_cost.relative_cost:.2f}×

"""

        if result.best_balanced:
            output += f"""
### ⚖️ Best Balanced Design
- **Primary MOSFET:** {result.best_balanced.primary_mosfet_part}
- **Secondary Diode:** {result.best_balanced.secondary_diode_part}
- **Frequency:** {result.best_balanced.switching_frequency / 1000:.0f}kHz
- **Transformer:** {result.best_balanced.transformer_core}
- **Turns Ratio:** {result.best_balanced.turns_ratio:.1f}:1
- **Full Load Efficiency:** {result.best_balanced.efficiency_full_load * 100:.2f}%
- **CEC Efficiency:** {result.best_balanced.efficiency_cec * 100:.2f}%
- **Relative Cost:** {result.best_balanced.relative_cost:.2f}×

"""

        output += f"""
---

### Pareto Frontier
{len(result.pareto_frontier)} non-dominated designs found.

**Trade-off Analysis:**
- Efficiency range: {min(d.efficiency_full_load for d in result.pareto_frontier) * 100:.2f}% - {max(d.efficiency_full_load for d in result.pareto_frontier) * 100:.2f}%
- Cost range: {min(d.relative_cost for d in result.pareto_frontier):.2f}× - {max(d.relative_cost for d in result.pareto_frontier):.2f}×
"""

        # Create Pareto frontier plot
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot all candidates
        all_eff = [d.efficiency_full_load * 100 for d in result.all_valid_designs]
        all_cost = [d.relative_cost for d in result.all_valid_designs]
        ax.scatter(all_eff, all_cost, alpha=0.3, s=30, label='All Designs', color='gray')

        # Plot Pareto frontier
        pareto_eff = [d.efficiency_full_load * 100 for d in result.pareto_frontier]
        pareto_cost = [d.relative_cost for d in result.pareto_frontier]
        ax.scatter(pareto_eff, pareto_cost, s=100, label='Pareto Frontier',
                  color='red', marker='*', edgecolors='black', linewidths=1.5)

        # Highlight best designs
        if result.best_efficiency:
            ax.scatter([result.best_efficiency.efficiency_full_load * 100],
                      [result.best_efficiency.relative_cost],
                      s=200, marker='^', color='green', edgecolors='black',
                      linewidths=2, label='Best Efficiency', zorder=5)

        if result.best_cost:
            ax.scatter([result.best_cost.efficiency_full_load * 100],
                      [result.best_cost.relative_cost],
                      s=200, marker='s', color='blue', edgecolors='black',
                      linewidths=2, label='Best Cost', zorder=5)

        if result.best_balanced:
            ax.scatter([result.best_balanced.efficiency_full_load * 100],
                      [result.best_balanced.relative_cost],
                      s=200, marker='D', color='orange', edgecolors='black',
                      linewidths=2, label='Best Balanced', zorder=5)

        ax.set_xlabel('Full Load Efficiency (%)', fontsize=12)
        ax.set_ylabel('Relative Cost (×)', fontsize=12)
        ax.set_title(f'Design Space Exploration\n{result.valid_designs_count} Valid Designs', fontsize=14)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)

        return output, fig

    except Exception as e:
        import traceback
        return f"Error: {str(e)}\n\n{traceback.format_exc()}", None

# ============================================================================
# Tab 7: UCC28951 Controller Design
# ============================================================================

def design_ucc28951_gui(
    vin_min, vin_nom, vin_max, vout, iout_max,
    turns_ratio, leakage_inductance,
    output_inductance, output_capacitance, output_cap_esr,
    switching_frequency,
    target_crossover_freq, target_phase_margin
):
    """Design UCC28951 controller components"""
    try:
        # Create specification
        spec = UCC28951Specification(
            vin_min=float(vin_min),
            vin_nom=float(vin_nom),
            vin_max=float(vin_max),
            vout=float(vout),
            iout_max=float(iout_max),
            turns_ratio=float(turns_ratio),
            leakage_inductance=float(leakage_inductance) * 1e-6,  # µH to H
            output_inductance=float(output_inductance) * 1e-6,  # µH to H
            output_capacitance=float(output_capacitance) * 1e-6,  # µF to F
            output_cap_esr=float(output_cap_esr) * 1e-3,  # mΩ to Ω
            switching_frequency=float(switching_frequency) * 1e3,  # kHz to Hz
            target_crossover_freq=float(target_crossover_freq),
            target_phase_margin=float(target_phase_margin),
        )

        # Design components
        components = design_ucc28951_components(spec)

        # Create results markdown
        results = f"""
## UCC28951 Component Design Results

### Power Stage Analysis
- **DC Gain:** {20 * np.log10(spec.vin_nom / spec.turns_ratio):.1f} dB
- **LC Resonance:** {1/(2*np.pi*np.sqrt(spec.output_inductance * spec.output_capacitance)):.0f} Hz
- **ESR Zero:** {1/(2*np.pi*spec.output_cap_esr * spec.output_capacitance):.0f} Hz

### Loop Performance
- **Crossover Frequency:** {components.gain_crossover_freq:.0f} Hz {'✓' if components.gain_crossover_freq >= target_crossover_freq else '✗'}
- **Phase Margin:** {components.phase_margin:.1f}° {'✓' if components.phase_margin >= target_phase_margin else '✗'}
- **Gain Margin:** {components.gain_margin:.1f} dB

---

### Bill of Materials

**Timing Circuit:**
- RT = {components.rt/1e3:.0f} kΩ (1%, metal film)
- CT = {components.ct*1e9:.0f} nF (C0G/NP0, ±5%)

**Voltage Feedback:**
- R_FB_TOP = {components.r_fb_top/1e3:.0f} kΩ (1%, metal film)
- R_FB_BOT = {components.r_fb_bot/1e3:.0f} kΩ (1%, metal film)

**Current Sensing:**
- R_CS = {components.r_cs*1e3:.1f} mΩ (1%, ±50ppm/°C, 2W+)
- R_CS_FILTER = {components.r_cs_filter/1e3:.1f} kΩ (1%)
- C_CS_FILTER = {components.c_cs_filter*1e9:.1f} nF (C0G/NP0)

**Compensation Network (Type III):**
- R_COMP_UPPER = {components.r_comp_upper/1e3:.0f} kΩ (1%, metal film)
- R_COMP_LOWER = {components.r_comp_lower/1e3:.0f} kΩ (1%, metal film)
- C_COMP_HF = {components.c_comp_hf*1e12:.0f} pF (C0G/NP0, ±5%)
- C_COMP_LF = {components.c_comp_lf*1e9:.1f} nF (C0G/NP0, ±10%)
- C_COMP_POLE = {components.c_comp_pole*1e12:.0f} pF (C0G/NP0, ±10%)

**Soft-Start:**
- C_SS = {components.c_ss*1e6:.2f} µF (ceramic or film)

---

### Design Targets
Target Crossover: {target_crossover_freq:.0f} Hz → Achieved: {components.gain_crossover_freq:.0f} Hz
Target Phase Margin: {target_phase_margin:.0f}° → Achieved: {components.phase_margin:.1f}°
"""

        # Create Bode plot visualization
        import matplotlib.pyplot as plt
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

        # Frequency range for Bode plot
        freqs = np.logspace(1, 6, 1000)  # 10 Hz to 1 MHz
        s = 2j * np.pi * freqs

        # Power stage transfer function (simplified)
        f0 = 1/(2*np.pi*np.sqrt(spec.output_inductance * spec.output_capacitance))
        fz_esr = 1/(2*np.pi*spec.output_cap_esr * spec.output_capacitance)
        Gdc = spec.vin_nom / spec.turns_ratio

        w0 = 2*np.pi*f0
        wz_esr = 2*np.pi*fz_esr
        Q = 7.0  # Typical

        # Power stage
        Gp = Gdc * (1 + s/wz_esr) / (1 + s/(Q*w0) + s**2/w0**2)

        # Compensator (Type III)
        fz1 = 1/(2*np.pi*components.r_comp_upper*components.c_comp_lf)
        fz2 = 1/(2*np.pi*components.r_comp_upper*components.c_comp_hf)
        fp1 = 1/(2*np.pi*components.r_comp_lower*components.c_comp_lf)
        fp2 = 1/(2*np.pi*components.r_comp_upper*components.c_comp_pole)

        wz1 = 2*np.pi*fz1
        wz2 = 2*np.pi*fz2
        wp1 = 2*np.pi*fp1
        wp2 = 2*np.pi*fp2

        s_safe = s + 1e-10
        Gc = (components.r_comp_upper/components.r_comp_lower) * \
             (1 + s/wz1) * (1 + s/wz2) / (s_safe/wp1 * (1 + s/wp2))

        # Loop gain
        T = Gp * Gc
        T_mag = 20 * np.log10(np.abs(T) + 1e-12)
        T_phase = np.angle(T, deg=True)

        # Magnitude plot
        ax1.semilogx(freqs, T_mag, 'b-', linewidth=2, label='Loop Gain')
        ax1.axhline(0, color='k', linestyle='--', alpha=0.3)
        ax1.axvline(components.gain_crossover_freq, color='r', linestyle='--',
                   alpha=0.5, label=f'Crossover: {components.gain_crossover_freq:.0f} Hz')
        ax1.grid(True, which='both', alpha=0.3)
        ax1.set_ylabel('Magnitude (dB)', fontsize=11)
        ax1.set_title('Loop Gain Bode Plot', fontsize=12, fontweight='bold')
        ax1.legend(loc='upper right')
        ax1.set_ylim([-60, 100])

        # Phase plot
        ax2.semilogx(freqs, T_phase, 'r-', linewidth=2, label='Phase')
        ax2.axhline(-180, color='k', linestyle='--', alpha=0.3)
        ax2.axvline(components.gain_crossover_freq, color='r', linestyle='--',
                   alpha=0.5, label=f'PM: {components.phase_margin:.1f}°')
        ax2.grid(True, which='both', alpha=0.3)
        ax2.set_xlabel('Frequency (Hz)', fontsize=11)
        ax2.set_ylabel('Phase (degrees)', fontsize=11)
        ax2.legend(loc='lower left')
        ax2.set_ylim([-270, 90])

        plt.tight_layout()

        return results, fig

    except Exception as e:
        import traceback
        return f"Error: {str(e)}\n\n{traceback.format_exc()}", None

# ============================================================================
# Create Gradio Interface
# ============================================================================

def create_gui():
    """Create complete Gradio GUI"""

    with gr.Blocks(title="PSFB Loss Analyzer", theme=gr.themes.Soft()) as app:

        gr.Markdown("# PSFB Loss Analyzer & Optimization Suite")
        gr.Markdown("Complete power loss analysis and design optimization for Phase-Shifted Full-Bridge converters")

        with gr.Tabs():

            # ================================================================
            # Tab 1: MOSFET Loss Analysis
            # ================================================================
            with gr.Tab("MOSFET Loss Analysis"):
                gr.Markdown("## MOSFET Loss Calculator")

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Component Selection")
                        mosfet_part = gr.Dropdown(
                            choices=get_mosfet_part_numbers(),
                            label="Select from Library",
                            value="IMZA65R020M2H" if "IMZA65R020M2H" in get_mosfet_part_numbers() else None
                        )
                        load_mosfet_btn = gr.Button("Load Parameters from Library")

                        gr.Markdown("### Device Parameters")
                        mosfet_v_dss = gr.Number(label="V_DSS (V)", value=650)
                        mosfet_i_d = gr.Number(label="I_D Continuous (A)", value=90)
                        mosfet_rdson_25c = gr.Number(label="R_DS(on) @ 25°C (mΩ)", value=20)
                        mosfet_rdson_150c = gr.Number(label="R_DS(on) @ 150°C (mΩ)", value=28)

                        with gr.Row():
                            mosfet_qg = gr.Number(label="Q_g (nC)", value=142)
                            mosfet_qgs = gr.Number(label="Q_gs (nC)", value=38)
                            mosfet_qgd = gr.Number(label="Q_gd (nC)", value=52)

                        with gr.Row():
                            mosfet_ciss = gr.Number(label="C_iss (pF)", value=7200)
                            mosfet_coss = gr.Number(label="C_oss (pF)", value=520)
                            mosfet_crss = gr.Number(label="C_rss (pF)", value=15)

                    with gr.Column():
                        gr.Markdown("### Operating Conditions")
                        mosfet_i_rms = gr.Slider(0, 100, value=20, label="I_RMS (A)")
                        mosfet_v_ds = gr.Slider(0, 1000, value=400, label="V_DS (V)")
                        mosfet_freq = gr.Slider(10, 500, value=100, label="Frequency (kHz)")
                        mosfet_duty = gr.Slider(0, 1, value=0.45, label="Duty Cycle")
                        mosfet_tj = gr.Slider(25, 175, value=100, label="Junction Temperature (°C)")
                        mosfet_vgs = gr.Slider(10, 20, value=18, label="Gate Drive Voltage (V)")

                        calc_mosfet_btn = gr.Button("Calculate Losses", variant="primary")

                with gr.Row():
                    mosfet_results = gr.Markdown("Results will appear here...")
                    mosfet_plot = gr.Plot(label="Loss Breakdown")

                # Connect load button
                load_mosfet_btn.click(
                    fn=load_mosfet_from_library,
                    inputs=[mosfet_part],
                    outputs=[
                        mosfet_v_dss, mosfet_i_d, mosfet_rdson_25c, mosfet_rdson_150c,
                        mosfet_qg, mosfet_qgs, mosfet_qgd,
                        mosfet_ciss, mosfet_coss, mosfet_crss
                    ]
                )

                # Connect calculate button
                calc_mosfet_btn.click(
                    fn=calculate_mosfet_losses,
                    inputs=[
                        mosfet_part,
                        mosfet_v_dss, mosfet_i_d, mosfet_rdson_25c, mosfet_rdson_150c,
                        mosfet_qg, mosfet_qgs, mosfet_qgd,
                        mosfet_ciss, mosfet_coss, mosfet_crss,
                        mosfet_i_rms, mosfet_v_ds, mosfet_freq, mosfet_duty, mosfet_tj, mosfet_vgs
                    ],
                    outputs=[mosfet_results, mosfet_plot]
                )

            # ================================================================
            # Tab 2: Diode Loss Analysis
            # ================================================================
            with gr.Tab("Diode Loss Analysis"):
                gr.Markdown("## Diode Loss Calculator")

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Component Selection")
                        diode_part = gr.Dropdown(
                            choices=get_diode_part_numbers(),
                            label="Select from Library",
                            value=get_diode_part_numbers()[0] if get_diode_part_numbers() else None
                        )
                        load_diode_btn = gr.Button("Load Parameters from Library")

                        gr.Markdown("### Device Parameters")
                        diode_v_rrm = gr.Number(label="V_RRM (V)", value=1200)
                        diode_i_f = gr.Number(label="I_F Average Rating (A)", value=30)
                        diode_vf_25c = gr.Number(label="V_F @ 25°C (V)", value=1.5)
                        diode_vf_125c = gr.Number(label="V_F @ 125°C (V)", value=1.3)
                        diode_trr = gr.Number(label="t_rr (ns)", value=20)
                        diode_qrr = gr.Number(label="Q_rr (nC)", value=10)

                    with gr.Column():
                        gr.Markdown("### Operating Conditions")
                        diode_i_f_avg = gr.Slider(0, 100, value=20, label="I_F Average (A)")
                        diode_i_f_rms = gr.Slider(0, 100, value=22, label="I_F RMS (A)")
                        diode_v_r = gr.Slider(0, 1000, value=400, label="Reverse Voltage (V)")
                        diode_freq = gr.Slider(10, 500, value=100, label="Frequency (kHz)")
                        diode_tj = gr.Slider(25, 175, value=100, label="Junction Temperature (°C)")

                        calc_diode_btn = gr.Button("Calculate Losses", variant="primary")

                with gr.Row():
                    diode_results = gr.Markdown("Results will appear here...")
                    diode_plot = gr.Plot(label="Loss Breakdown")

                # Connect load button
                load_diode_btn.click(
                    fn=load_diode_from_library,
                    inputs=[diode_part],
                    outputs=[diode_v_rrm, diode_i_f, diode_vf_25c, diode_vf_125c, diode_trr, diode_qrr]
                )

                # Connect calculate button
                calc_diode_btn.click(
                    fn=calculate_diode_losses,
                    inputs=[
                        diode_part,
                        diode_v_rrm, diode_i_f,
                        diode_vf_25c, diode_vf_125c,
                        diode_trr, diode_qrr,
                        diode_i_f_avg, diode_i_f_rms, diode_v_r, diode_freq, diode_tj
                    ],
                    outputs=[diode_results, diode_plot]
                )

            # ================================================================
            # Tab 3: Datasheet Parser
            # ================================================================
            with gr.Tab("Datasheet Parser"):
                gr.Markdown("## Automatic Datasheet Parameter Extraction")
                gr.Markdown("Upload MOSFET or diode datasheets (PDF) for automatic parameter extraction")

                with gr.Row():
                    with gr.Column():
                        pdf_file = gr.File(
                            label="📄 Drag & Drop PDF Datasheet Here",
                            file_types=[".pdf"],
                            type="filepath"
                        )
                        parse_btn = gr.Button("Extract Parameters", variant="primary")

                        gr.Markdown("""
                        ### Supported Devices
                        - SiC MOSFETs (Infineon, Wolfspeed, Rohm, ST, OnSemi)
                        - SiC Schottky Diodes
                        - Si MOSFETs
                        - Si PN Diodes

                        ### Note
                        Some parameters (especially from graphs) may require manual verification.
                        """)

                    with gr.Column():
                        parser_results = gr.Markdown("Upload a PDF to begin extraction...")
                        parser_plot = gr.Plot(label="Parameter Visualization")

                # Connect parse button
                parse_btn.click(
                    fn=parse_datasheet,
                    inputs=[pdf_file],
                    outputs=[parser_results, parser_plot]
                )

            # ================================================================
            # Tab 4: System Analysis
            # ================================================================
            with gr.Tab("System Analysis"):
                gr.Markdown("## Multi-Phase PSFB System Analyzer")
                gr.Markdown("Analyze complete PSFB system with multiple interleaved phases")

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### System Configuration")
                        sys_power = gr.Number(label="Total Output Power (W)", value=6600)
                        sys_vin = gr.Number(label="Input Voltage (V)", value=400)
                        sys_vout = gr.Number(label="Output Voltage (V)", value=48)
                        sys_freq = gr.Slider(10, 500, value=100, label="Switching Frequency (kHz)")
                        sys_phases = gr.Radio([1, 2, 3, 4], value=3, label="Number of Phases")
                        sys_phase_shift = gr.Radio([0, 90, 120, 180], value=120, label="Phase Shift (degrees)")

                        gr.Markdown("### Component Selection")
                        sys_mosfet = gr.Dropdown(
                            choices=get_mosfet_part_numbers(),
                            label="Primary MOSFET",
                            value="IMZA65R020M2H" if "IMZA65R020M2H" in get_mosfet_part_numbers() else None
                        )
                        sys_diode = gr.Dropdown(
                            choices=get_diode_part_numbers(),
                            label="Secondary Diode",
                            value=get_diode_part_numbers()[0] if get_diode_part_numbers() else None
                        )

                    with gr.Column():
                        gr.Markdown("### Operating Conditions")
                        sys_tj_mosfet = gr.Slider(25, 175, value=100, label="MOSFET Junction Temp (°C)")
                        sys_tj_diode = gr.Slider(25, 175, value=100, label="Diode Junction Temp (°C)")

                        analyze_btn = gr.Button("Analyze System", variant="primary", size="lg")

                        gr.Markdown("""
                        ### Analysis Features
                        - Per-phase loss breakdown
                        - Multi-phase aggregation
                        - System efficiency calculation
                        - Component count and totals
                        """)

                with gr.Row():
                    sys_results = gr.Markdown("Configure system and click Analyze...")

                with gr.Row():
                    sys_plot1 = gr.Plot(label="Loss Breakdown")
                    sys_plot2 = gr.Plot(label="Power Flow")

                # Connect analyze button
                analyze_btn.click(
                    fn=analyze_system,
                    inputs=[
                        sys_power, sys_vin, sys_vout, sys_freq,
                        sys_phases, sys_phase_shift,
                        sys_mosfet, sys_diode,
                        sys_tj_mosfet, sys_tj_diode
                    ],
                    outputs=[sys_results, sys_plot1, sys_plot2]
                )

            # ================================================================
            # Tab 5: Magnetic Design
            # ================================================================
            with gr.Tab("Magnetic Design"):
                gr.Markdown("## Transformer & Inductor Design")

                with gr.Tabs():
                    # Sub-tab for transformer
                    with gr.Tab("Transformer Design"):
                        with gr.Row():
                            with gr.Column():
                                gr.Markdown("### Specifications")
                                xfmr_power = gr.Number(label="Power (W)", value=3000)
                                xfmr_vin_min = gr.Number(label="V_in Min (V)", value=360)
                                xfmr_vin_nom = gr.Number(label="V_in Nominal (V)", value=400)
                                xfmr_vin_max = gr.Number(label="V_in Max (V)", value=440)
                                xfmr_vout = gr.Number(label="V_out (V)", value=48)
                                xfmr_freq = gr.Slider(10, 500, value=100, label="Frequency (kHz)")

                            with gr.Column():
                                gr.Markdown("### Design Parameters")
                                xfmr_duty_min = gr.Slider(0.1, 0.5, value=0.35, label="Duty Cycle Min")
                                xfmr_duty_max = gr.Slider(0.1, 0.5, value=0.5, label="Duty Cycle Max")
                                xfmr_bmax = gr.Slider(0.1, 0.4, value=0.3, step=0.05, label="Max Flux Density (T)")
                                xfmr_jmax = gr.Slider(2, 10, value=5, step=0.5, label="Current Density (A/mm²)")

                                design_xfmr_btn = gr.Button("Design Transformer", variant="primary")

                        with gr.Row():
                            xfmr_results = gr.Markdown("Enter specifications and click Design...")
                            xfmr_plot = gr.Plot(label="Design Results")

                        design_xfmr_btn.click(
                            fn=design_transformer_gui,
                            inputs=[
                                xfmr_power, xfmr_vin_min, xfmr_vin_nom, xfmr_vin_max, xfmr_vout, xfmr_freq,
                                xfmr_duty_min, xfmr_duty_max, xfmr_bmax, xfmr_jmax
                            ],
                            outputs=[xfmr_results, xfmr_plot]
                        )

                    # Sub-tab for inductors
                    with gr.Tab("Inductor Design"):
                        with gr.Row():
                            with gr.Column():
                                gr.Markdown("### Type & Specifications")
                                ind_type = gr.Radio(
                                    ["Resonant Inductor (ZVS)", "Output Inductor"],
                                    value="Resonant Inductor (ZVS)",
                                    label="Inductor Type"
                                )
                                ind_l = gr.Number(label="Inductance (µH)", value=10)
                                ind_idc = gr.Number(label="DC/RMS Current (A)", value=20)
                                ind_ripple = gr.Number(label="Ripple Current (A)", value=5, visible=False)
                                ind_freq = gr.Slider(10, 500, value=100, label="Frequency (kHz)")
                                ind_bmax = gr.Slider(0.1, 0.4, value=0.3, step=0.05, label="Max Flux Density (T)")

                                design_ind_btn = gr.Button("Design Inductor", variant="primary")

                                # Show/hide ripple based on type
                                def update_ripple_visibility(inductor_type):
                                    return gr.update(visible=(inductor_type == "Output Inductor"))

                                ind_type.change(
                                    fn=update_ripple_visibility,
                                    inputs=[ind_type],
                                    outputs=[ind_ripple]
                                )

                            with gr.Column():
                                ind_results = gr.Markdown("Select type and click Design...")
                                ind_plot = gr.Plot(label="Design Results")

                        design_ind_btn.click(
                            fn=design_inductor_gui,
                            inputs=[ind_type, ind_l, ind_idc, ind_ripple, ind_freq, ind_bmax],
                            outputs=[ind_results, ind_plot]
                        )

            # ================================================================
            # Tab 6: Optimizer
            # ================================================================
            with gr.Tab("Optimizer"):
                gr.Markdown("## Automated Design Optimization")
                gr.Markdown("Multi-objective optimization with Pareto frontier analysis")

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Power Specification")
                        opt_power_min = gr.Number(label="Min Power (W)", value=2500)
                        opt_power_rated = gr.Number(label="Rated Power (W)", value=3000)
                        opt_power_max = gr.Number(label="Max Power (W)", value=3300)

                        gr.Markdown("### Input Voltage Range")
                        opt_vin_min = gr.Number(label="V_in Min (V)", value=360)
                        opt_vin_nom = gr.Number(label="V_in Nominal (V)", value=400)
                        opt_vin_max = gr.Number(label="V_in Max (V)", value=440)

                    with gr.Column():
                        gr.Markdown("### Output & Configuration")
                        opt_vout = gr.Number(label="V_out (V)", value=48)
                        opt_phases = gr.Radio([1, 2, 3, 4], value=1, label="Number of Phases")
                        opt_eff_target = gr.Slider(90, 99, value=95, step=0.5, label="Efficiency Target (%)")

                        gr.Markdown("### Optimization Settings")
                        opt_objective = gr.Radio(
                            ["Maximum Efficiency", "Minimum Cost", "Balanced (Efficiency + Cost)"],
                            value="Balanced (Efficiency + Cost)",
                            label="Objective Function"
                        )
                        opt_max_eval = gr.Slider(5, 100, value=20, step=5, label="Max Evaluations")

                        optimize_btn = gr.Button("Run Optimization", variant="primary", size="lg")

                with gr.Row():
                    opt_results = gr.Markdown("""
                    Configure specifications and click **Run Optimization**.

                    The optimizer will:
                    1. Generate design space from component library
                    2. Evaluate each design candidate
                    3. Find Pareto optimal solutions
                    4. Recommend best designs for efficiency, cost, and balance

                    **Note:** Optimization may take 30-120 seconds depending on design space size.
                    """)

                with gr.Row():
                    opt_plot = gr.Plot(label="Pareto Frontier")

                # Connect optimize button
                optimize_btn.click(
                    fn=run_optimizer,
                    inputs=[
                        opt_power_min, opt_power_rated, opt_power_max,
                        opt_vin_min, opt_vin_nom, opt_vin_max,
                        opt_vout, opt_phases,
                        opt_eff_target, opt_objective,
                        opt_max_eval
                    ],
                    outputs=[opt_results, opt_plot]
                )

            # ================================================================
            # Tab 7: UCC28951 Controller Design
            # ================================================================
            with gr.Tab("UCC28951 Controller"):
                gr.Markdown("## UCC28951 Controller Component Calculation")
                gr.Markdown("Design compensation loop for phase-shifted full-bridge controller")

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Power Stage Parameters")
                        ucc_vin_min = gr.Number(label="V_in Min (V)", value=360)
                        ucc_vin_nom = gr.Number(label="V_in Nominal (V)", value=400)
                        ucc_vin_max = gr.Number(label="V_in Max (V)", value=440)
                        ucc_vout = gr.Number(label="V_out (V)", value=48)
                        ucc_iout_max = gr.Number(label="I_out Max (A)", value=62.5)

                        gr.Markdown("### Transformer & Filter")
                        ucc_turns_ratio = gr.Number(label="Turns Ratio (N_pri/N_sec)", value=8.0)
                        ucc_leakage = gr.Number(label="Leakage Inductance (µH)", value=10)
                        ucc_lo = gr.Number(label="Output Inductance (µH)", value=10)
                        ucc_co = gr.Number(label="Output Capacitance (µF)", value=1000)
                        ucc_esr = gr.Number(label="Output Cap ESR (mΩ)", value=10)

                    with gr.Column():
                        gr.Markdown("### Operating Conditions")
                        ucc_fsw = gr.Slider(50, 200, value=100, step=10, label="Switching Frequency (kHz)")

                        gr.Markdown("### Design Targets")
                        ucc_fc_target = gr.Slider(1000, 10000, value=3000, step=500,
                                                 label="Target Crossover Frequency (Hz)")
                        ucc_pm_target = gr.Slider(30, 80, value=50, step=5,
                                                 label="Target Phase Margin (°)")

                        design_ucc_btn = gr.Button("Design Controller", variant="primary", size="lg")

                        gr.Markdown("""
                        ### Design Goals
                        - Crossover Frequency: > 1 kHz
                        - Phase Margin: > 45°
                        - Stable across load range

                        ### Features
                        - Type III compensation network
                        - Bode plot visualization
                        - Complete BOM with tolerances
                        """)

                with gr.Row():
                    ucc_results = gr.Markdown("Enter parameters and click Design Controller...")

                with gr.Row():
                    ucc_plot = gr.Plot(label="Loop Gain Bode Plot")

                # Connect design button
                design_ucc_btn.click(
                    fn=design_ucc28951_gui,
                    inputs=[
                        ucc_vin_min, ucc_vin_nom, ucc_vin_max, ucc_vout, ucc_iout_max,
                        ucc_turns_ratio, ucc_leakage,
                        ucc_lo, ucc_co, ucc_esr,
                        ucc_fsw,
                        ucc_fc_target, ucc_pm_target
                    ],
                    outputs=[ucc_results, ucc_plot]
                )

            # ================================================================
            # Tab 8: About
            # ================================================================
            with gr.Tab("About"):
                gr.Markdown("""
                # PSFB Loss Analyzer & Optimization Suite

                **Version:** 1.0.0 - Complete GUI Interface

                ## GUI Tabs Overview

                This comprehensive GUI provides access to all PSFB Loss Analyzer features:

                ### 1️⃣ MOSFET Loss Analysis
                - Component library with SiC and Si MOSFETs
                - Conduction, switching, gate drive, and C_oss losses
                - Temperature-dependent calculations
                - Interactive loss breakdown visualization

                ### 2️⃣ Diode Loss Analysis
                - SiC Schottky and Si PN diode library
                - Conduction and reverse recovery losses
                - Device type comparison
                - Temperature effects analysis

                ### 3️⃣ Datasheet Parser
                - **Drag & drop PDF upload**
                - Automatic parameter extraction for MOSFETs and diodes
                - Multi-manufacturer support (Infineon, Wolfspeed, Rohm, ST, OnSemi)
                - Confidence scoring and warnings

                ### 4️⃣ System Analysis
                - Multi-phase PSFB system analysis (1-4 phases)
                - Interleaved phase configurations (90°, 120°, 180°)
                - Complete loss breakdown by component type
                - System efficiency and power flow visualization

                ### 5️⃣ Magnetic Design
                - **Transformer Design:** Complete winding design with Kg method
                - **Resonant Inductor:** ZVS operation design
                - **Output Inductor:** DC bias and ripple handling
                - Core selection and loss calculation

                ### 6️⃣ Optimizer
                - **Automated design optimization** with component library
                - Multi-objective optimization (efficiency, cost, balanced)
                - **Pareto frontier** visualization
                - Best design recommendations

                ### 7️⃣ UCC28951 Controller (NEW!)
                - **TI UCC28951/UCC28950** component calculation
                - **Type III compensation** network design
                - **Bode plot** visualization (magnitude + phase)
                - Loop stability analysis (crossover, phase margin)
                - Complete BOM with component specs
                - Design targets: Crossover > 1kHz, PM > 45°

                ### 8️⃣ About
                - Documentation and references

                ---

                ## Complete Feature Set

                ✅ **Loss Calculations**
                - MOSFET: conduction, switching, gate drive, C_oss
                - Diode: conduction, reverse recovery
                - Magnetics: core and copper losses
                - Capacitors: ESR losses with ripple cancellation

                ✅ **Magnetic Design**
                - Resonant inductor for ZVS operation
                - Transformer with Kg area product method
                - Output inductor with DC bias
                - Comprehensive core database

                ✅ **System Integration**
                - Single-phase and multi-phase analysis
                - Phase shift optimization
                - Per-phase and system-level breakdown
                - Efficiency calculation

                ✅ **Design Optimization**
                - Component library (6 MOSFETs, 5 diodes)
                - Automated magnetic design
                - Pareto frontier generation
                - Design space exploration

                ✅ **Datasheet Tools**
                - PDF parsing for MOSFETs and diodes
                - Table extraction and pattern matching
                - Batch processing capability

                ---

                ## Technical Methodology

                Based on industry-standard approaches:

                **MOSFET Losses:**
                - Infineon AN2019-10: "MOSFET Power Losses Calculation Using the Data Sheet Parameters"
                - Temperature-dependent R_DS(on) modeling
                - ZVS and hard-switching analysis

                **Magnetic Design:**
                - McLyman: "Transformer and Inductor Design Handbook" (Kg method)
                - Erickson & Maksimovic: "Fundamentals of Power Electronics"
                - Steinmetz equation for core losses

                **Optimization:**
                - Multi-objective Pareto optimization
                - Component library filtering
                - Constraint satisfaction

                ---

                ## Documentation

                Complete documentation available:
                - **INSTALL.md** - Windows 11 + WSL2 + VS Code installation
                - **QUICK_START.md** - 10-minute tutorial with examples
                - **TESTING.md** - Comprehensive testing guide
                - **VSCODE.md** - VS Code integration and debugging

                ---

                ## Usage Tips

                **Getting Started:**
                1. Try **MOSFET Loss Analysis** - Load a component from library and calculate
                2. Explore **System Analysis** - Analyze a 6.6kW 3-phase system (default values)
                3. Use **Optimizer** - Find optimal designs automatically

                **Datasheet Parser:**
                - Drag & drop PDF datasheets into the upload area
                - Works with major manufacturers (Infineon, Wolfspeed, Rohm, etc.)
                - Some parameters (graphs) may need manual verification

                **Performance:**
                - Loss calculations are instant
                - Magnetic design: < 1 second
                - System analysis: 1-2 seconds
                - Optimization: 30-120 seconds (depending on design space)

                ---

                ## Author

                PSFB Loss Analysis Tool Development Team

                **Version:** 1.0.0 - Released 2025

                ---

                **Get Started:** Select a tab above to begin your PSFB converter analysis!
                """)

        return app

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("PSFB LOSS ANALYZER - GUI")
    print("=" * 80)
    print()
    print("Starting web interface...")
    print()
    print("The GUI will open in your default browser.")
    print("If it doesn't open automatically, navigate to: http://localhost:7860")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 80)
    print()

    app = create_gui()
    app.launch(
        server_name="0.0.0.0",  # Allow access from WSL2
        server_port=7860,
        share=False,  # Set to True to create public link
        show_error=True,
    )

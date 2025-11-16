# PSFB Loss Analyzer - Quick Start Guide

Get started with PSFB Loss Analyzer in 10 minutes!

## Prerequisites

Before starting, complete the installation: See [INSTALL.md](INSTALL.md)

## Quick Test

Verify your installation works:

```bash
# Activate virtual environment
source venv/bin/activate

# Run installation test
python test_installation.py
```

You should see: `✓ ALL TESTS PASSED - Installation is complete!`

---

## Your First Analysis (3 minutes)

Let's analyze a simple 3kW, 400V→48V PSFB converter.

### Step 1: Import the Library

Create a new file: `my_first_psfb.py`

```python
from psfb_loss_analyzer import (
    MOSFETParameters,
    DiodeParameters,
    CapacitanceVsVoltage,
    calculate_mosfet_conduction_loss,
    calculate_diode_conduction_loss,
)

# Define a MOSFET
mosfet = MOSFETParameters(
    part_number="IMZA65R020M2H",
    v_dss=650.0,  # 650V rating
    i_d_continuous=90.0,  # 90A continuous
    r_dson_25c=16e-3,  # 16mΩ @ 25°C
    r_dson_25c_max=20e-3,
    r_dson_150c=22e-3,  # 22mΩ @ 150°C
    r_dson_150c_max=28e-3,
    capacitances=CapacitanceVsVoltage(
        c_iss_constant=7200e-12,  # 7.2nF
        c_oss_constant=520e-12,   # 520pF
        c_rss_constant=15e-12,    # 15pF
    ),
    q_g=142e-9,  # 142nC gate charge
    q_gs=38e-9,
    q_gd=52e-9,
    v_gs_plateau=4.5,  # 4.5V Miller plateau
    t_r=25e-9,  # 25ns rise time
    t_f=20e-9,  # 20ns fall time
)

# Calculate conduction loss
i_rms = 20.0  # 20A RMS current
duty = 0.45   # 45% duty cycle
temp = 100.0  # 100°C junction temperature

loss = calculate_mosfet_conduction_loss(
    mosfet=mosfet,
    i_rms=i_rms,
    duty_cycle=duty,
    t_junction=temp,
)

print(f"MOSFET Conduction Loss: {loss:.2f}W")
```

**Run it:**
```bash
python my_first_psfb.py
```

**Output:**
```
MOSFET Conduction Loss: 8.60W
```

✅ **Congratulations!** You just calculated your first MOSFET loss!

---

## Complete System Analysis (5 minutes)

Now let's analyze a complete PSFB system using the built-in examples.

### Run the 6.6kW Example

```bash
python psfb_loss_analyzer/examples/example_6p6kw_complete_analysis.py
```

**What it does:**
- Analyzes 3-phase interleaved 6.6kW PSFB (3 × 2.2kW @ 120°)
- Calculates all losses: MOSFETs, diodes, magnetics, capacitors
- Computes efficiency at multiple load points
- Shows per-phase and system-level breakdown

**Expected output:**
```
================================================================================
SYSTEM LOSS ANALYSIS - 3-PHASE PSFB (6.6kW Marine Application)
================================================================================

Operating Point: 6600.0W @ 400V → 48V
Frequency: 100.0kHz
Phases: 3 (120° shift)

TOTAL SYSTEM LOSSES:
--------------------------------------------------------------------------------
Total System Loss:      156.8W
System Efficiency:      97.67%
Input Power:            6756.8W

LOSS BREAKDOWN:
  MOSFET Losses:        85.2W (54.3%)
  Diode Losses:         28.5W (18.2%)
  Magnetic Losses:      32.8W (20.9%)
  Capacitor Losses:     10.3W (6.6%)

PER-PHASE ANALYSIS:
  Phase 1 Loss:         52.3W (Eff: 97.68%)
  Phase 2 Loss:         52.1W (Eff: 97.68%)
  Phase 3 Loss:         52.4W (Eff: 97.67%)

✓ Analysis complete!
```

---

## Automated Design Optimization (2 minutes)

Use the optimizer to automatically design a converter!

### Run the Auto-Design Example

```bash
python psfb_loss_analyzer/examples/example_auto_design.py
```

**What it does:**
- Automatically selects components from library
- Designs magnetics for each candidate
- Evaluates efficiency, cost, size
- Finds Pareto optimal designs

**Expected output:**
```
================================================================================
AUTOMATED PSFB DESIGN - 3kW Telecom
================================================================================

Specification:
  Power:    3.0kW
  Input:    300-420V (nominal 380V)
  Output:   48V
  Efficiency Target: > 95%

Design Space: 48 candidates
Evaluating...
[====================] 48/48 (100%)

Valid Designs: 42

BEST DESIGNS:
--------------------------------------------------------------------------------

Best Efficiency:
  Part: IMZA65R020M2H + C4D30120A
  Frequency: 100kHz
  Efficiency: 97.8%
  Cost: 2.5× (relative)

Best Cost:
  Part: IMZA65R040M2H + C3D16065D
  Frequency: 80kHz
  Efficiency: 96.2%
  Cost: 1.8× (relative)

Best Balanced:
  Part: IMZA65R020M2H + C3D16065D
  Frequency: 100kHz
  Efficiency: 97.2%
  Cost: 2.1× (relative)

Pareto Frontier: 8 non-dominated designs

✓ Optimization complete!
```

---

## What's Next?

Now that you've run your first analyses, explore these areas:

### 1. Learn More Examples

```bash
cd psfb_loss_analyzer/examples/

# Efficiency mapping
python example_efficiency_analysis.py

# Custom circuit design
python example_custom_circuit.py
```

### 2. Read the Documentation

- **[TESTING.md](TESTING.md)** - Comprehensive testing guide
- **[VSCODE.md](VSCODE.md)** - VS Code integration and debugging
- **Module READMEs** - Detailed module documentation

### 3. Build Your Own Design

Create your custom PSFB design:

```python
from psfb_loss_analyzer import (
    DesignSpecification,
    optimize_design,
    ObjectiveFunction,
)

# Your specifications
spec = DesignSpecification(
    power_rated=5000.0,  # 5kW
    vin_min=300.0,
    vin_nom=400.0,
    vin_max=450.0,
    vout_nom=54.0,  # 54V battery charging
    n_phases=2,  # 2-phase interleaved
    efficiency_target=0.96,
)

# Run optimization
result = optimize_design(
    spec=spec,
    objective=ObjectiveFunction.BALANCED,
    max_evaluations=100,
    verbose=True,
)

# Print results
print(f"Best design efficiency: {result.best_efficiency.efficiency_cec:.1%}")
```

---

## Common Tasks

### Calculate MOSFET Losses

```python
from psfb_loss_analyzer import (
    calculate_mosfet_conduction_loss,
    calculate_mosfet_switching_loss,
    calculate_mosfet_gate_drive_loss,
)

# Your MOSFET and conditions
p_cond = calculate_mosfet_conduction_loss(mosfet, i_rms=20.0, duty_cycle=0.45, t_junction=100.0)
p_sw = calculate_mosfet_switching_loss(mosfet, v_ds=400.0, i_d=25.0, frequency=100e3, t_junction=100.0)
p_gate = calculate_mosfet_gate_drive_loss(mosfet, v_gs_drive=18.0, frequency=100e3)

p_total = p_cond + p_sw + p_gate
print(f"Total MOSFET loss: {p_total:.2f}W")
```

### Design a Transformer

```python
from psfb_loss_analyzer import (
    TransformerSpec,
    CoreMaterial,
    design_transformer,
)

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
    flux_density_max=0.3,  # 300mT
    current_density=5.0e6,  # 5A/mm²
)

result = design_transformer(spec, CoreMaterial.N87())

print(f"Turns Ratio: {result.n_primary}:{result.n_secondary}")
print(f"Core: {result.core_name}")
print(f"Core Loss: {result.core_loss:.2f}W")
print(f"Copper Loss: {result.copper_loss:.2f}W")
```

### Generate Efficiency Map

```python
from psfb_loss_analyzer import generate_efficiency_map

efficiency_map = generate_efficiency_map(
    rated_power=3000.0,
    output_voltage=48.0,
    frequency=100e3,
    voltage_range=(360, 440, 5),  # 360-440V in 5V steps
    load_points=[0.1, 0.25, 0.5, 0.75, 1.0],
    # ... component definitions ...
)

# Export to CSV
efficiency_map.to_csv("efficiency_map.csv")
```

---

## Debugging Tips

### Issue: Import Errors

```bash
# Verify virtual environment is activated
which python
# Should show: /home/user/projects/CLD_test/venv/bin/python

# Reinstall if needed
pip install -e .
```

### Issue: Calculation Errors

```python
# Add verbose output
result = calculate_mosfet_conduction_loss(
    mosfet, i_rms, duty, temp
)

# Debug print
print(f"R_DS(on) @ {temp}°C: {mosfet.get_rdson(temp) * 1000:.2f}mΩ")
print(f"I_RMS: {i_rms}A")
print(f"Loss: {result:.2f}W")
```

### Issue: Optimization Slow

```python
# Reduce design space
result = optimize_design(
    spec=spec,
    max_evaluations=20,  # Smaller for testing
    verbose=True,  # See progress
)
```

---

## Get Help

- **Examples:** See `psfb_loss_analyzer/examples/`
- **Tests:** See `tests/` directory and `TESTING.md`
- **Issues:** Check GitHub issues or create a new one
- **Documentation:** Read module docstrings:

```python
from psfb_loss_analyzer import calculate_mosfet_conduction_loss
help(calculate_mosfet_conduction_loss)
```

---

## Next Steps

1. ✅ Run examples
2. ✅ Modify examples for your application
3. ✅ Run tests: `python tests/test_suite.py`
4. ✅ Design your first PSFB converter!

---

**You're ready to start designing!** 🚀

For detailed information:
- Installation: [INSTALL.md](INSTALL.md)
- Testing: [TESTING.md](TESTING.md)
- VS Code: [VSCODE.md](VSCODE.md)

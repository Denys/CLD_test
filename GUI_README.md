# PSFB Loss Analyzer - GUI User Guide

Complete graphical user interface for PSFB converter analysis and design.

## Quick Start

### Launch the GUI

```bash
# Activate virtual environment
source venv/bin/activate

# Launch GUI
python psfb_gui.py
```

The GUI will automatically open in your default web browser at: **http://localhost:7860**

If running in WSL2, the browser will open in Windows and connect to the WSL2 server automatically.

---

## GUI Overview

The interface consists of 7 tabs providing complete access to all PSFB Loss Analyzer features:

### Tab 1: MOSFET Loss Analysis

Calculate complete MOSFET losses for any device in the component library.

**Features:**
- Component library dropdown with 6 pre-configured MOSFETs (4 SiC + 2 Si)
- Load parameters button for quick setup
- All MOSFET parameters editable (V_DSS, R_DS(on), gate charge, capacitances)
- Operating condition sliders (current, voltage, frequency, duty cycle, temperature)
- Real-time loss calculation
- Pie chart visualization of loss breakdown

**Workflow:**
1. Select MOSFET from dropdown (e.g., "IMZA65R020M2H")
2. Click **"Load Parameters from Library"**
3. Adjust operating conditions as needed
4. Click **"Calculate Losses"**
5. View results table and pie chart

**Example Results:**
```
Total Loss: 15.2W
- Conduction: 8.6W (56.6%)
- Switching: 5.4W (35.5%)
- Gate Drive: 0.9W (5.9%)
- C_oss: 0.3W (2.0%)
```

---

### Tab 2: Diode Loss Analysis

Calculate diode conduction and reverse recovery losses.

**Features:**
- Diode library with 5 devices (3 SiC Schottky + 2 Si PN)
- Forward voltage temperature dependence
- Reverse recovery loss calculation
- SiC vs Si comparison
- Loss breakdown visualization

**Workflow:**
1. Select diode from dropdown (e.g., "C4D30120A")
2. Click **"Load Parameters from Library"**
3. Set operating conditions
4. Click **"Calculate Losses"**

**Key Parameters:**
- V_F @ 25°C and 125°C (forward voltage drop)
- t_rr (reverse recovery time) - very low for SiC (~20ns), high for Si (~200ns)
- Q_rr (reverse recovery charge)

---

### Tab 3: Datasheet Parser

Automatically extract MOSFET and diode parameters from PDF datasheets.

**Features:**
- **Drag & drop** PDF upload
- Automatic table extraction
- Pattern matching for key parameters
- Multi-manufacturer support:
  - Infineon (IMZA, IMW, IPx series)
  - Wolfspeed (C2M, C3M series)
  - Rohm (SCT series)
  - ST Microelectronics
  - OnSemi

**Workflow:**
1. Drag PDF datasheet into upload area
2. Click **"Extract Parameters"**
3. Review extracted parameters with confidence scores
4. Verify values (especially from graphs)

**Extracted Parameters:**
- Part number and manufacturer
- V_DSS / V_RRM (voltage rating)
- I_D / I_F (current rating)
- R_DS(on) @ 25°C and 150°C
- Gate charge (Q_g, Q_gs, Q_gd)
- Capacitances (C_iss, C_oss, C_rss)
- Switching times (t_r, t_f)

**Note:** Some parameters from graphs (like gate charge curves) may require manual verification.

---

### Tab 4: System Analysis

Analyze complete multi-phase PSFB systems.

**Features:**
- 1-4 phase configurations
- Phase shift selection (0°, 90°, 120°, 180°)
- Component selection from library
- Per-phase loss breakdown
- System-level aggregation
- Dual visualizations:
  - Loss breakdown pie chart
  - Power flow bar chart

**Workflow:**
1. Set system configuration:
   - Total power (e.g., 6600W)
   - Input/output voltages (e.g., 400V → 48V)
   - Number of phases (e.g., 3)
   - Phase shift (e.g., 120°)
2. Select components (MOSFET + diode)
3. Set junction temperatures
4. Click **"Analyze System"**

**Example Output:**
```
Configuration: 6600W, 3 phases @ 120°
Efficiency: 97.67%
Total Loss: 156.8W

Per-Phase Breakdown:
- MOSFETs (4×): 34.1W
- Diodes (2×): 11.4W
- Magnetics: 9.9W
- Capacitors: 3.3W
Phase Total: 52.3W
```

**Default Configuration:**
The tab opens with default values for a 6.6kW marine PSFB (3× 2.2kW @ 120°) - just click **"Analyze System"** to see it in action!

---

### Tab 5: Magnetic Design

Design transformers and inductors for PSFB converters.

**Two Sub-Tabs:**

#### 5a. Transformer Design

Complete transformer design using Kg area product method.

**Input Specifications:**
- Power rating (W)
- Input voltage range (min/nom/max)
- Output voltage
- Switching frequency
- Duty cycle range
- Max flux density (typically 0.3T for ferrite)
- Current density (typically 5 A/mm²)

**Design Outputs:**
- Turns ratio (e.g., 16:2 for 400V→48V)
- Core selection (PQ, ETD, E cores)
- Winding design:
  - Wire gauge (AWG)
  - Number of strands (Litz wire)
  - Number of layers
  - DC resistance
- Loss breakdown:
  - Core loss (Steinmetz equation)
  - Copper loss (AC + DC)
  - Total loss

**Workflow:**
1. Enter power and voltage specifications
2. Set frequency and design parameters
3. Click **"Design Transformer"**
4. Review turns ratio, core selection, and losses

**Example Result:**
```
Turns Ratio: 16:2
Core: PQ32/30 (N87 ferrite)
Core Loss: 8.5W
Copper Loss: 12.3W
Total Loss: 20.8W
Efficiency: 99.3%
```

#### 5b. Inductor Design

Design resonant inductors (for ZVS) or output inductors.

**Input Specifications:**
- Inductor type (Resonant or Output)
- Inductance (µH)
- DC/RMS current
- Ripple current (for output inductor only)
- Frequency
- Max flux density

**Design Outputs:**
- Core selection
- Number of turns
- Air gap length
- Winding details (AWG, strands, layers)
- Core and copper losses

**Workflow:**
1. Select inductor type
2. Enter inductance and current
3. Click **"Design Inductor"**

**Example:**
```
Resonant Inductor: 10µH @ 20A RMS
Core: E38/8/25
Turns: 12
Air Gap: 1.2mm
Total Loss: 3.5W
```

---

### Tab 6: Optimizer

Automated design optimization with multi-objective analysis.

**Features:**
- Automatic component selection from library
- Automated magnetic design for each candidate
- Multi-objective optimization:
  - Maximum efficiency
  - Minimum cost
  - Balanced (efficiency + cost)
- Pareto frontier generation
- Visual design space exploration

**Input Specifications:**
- Power range (min/rated/max)
- Input voltage range (min/nom/max)
- Output voltage
- Number of phases
- Efficiency target (%)
- Objective function selection
- Max evaluations (design space size)

**Workflow:**
1. Enter power and voltage specifications
2. Select objective function:
   - **Maximum Efficiency** - Prioritize best efficiency
   - **Minimum Cost** - Prioritize lowest cost
   - **Balanced** - Optimize both efficiency and cost
3. Set max evaluations (5-100)
   - Small (5-20): Fast, good for testing
   - Medium (20-50): Balanced
   - Large (50-100): Comprehensive search
4. Click **"Run Optimization"**
5. Wait 30-120 seconds for results

**Output:**
- **Design Space Summary**
  - Total candidates evaluated
  - Valid designs (meet constraints)
  - Pareto optimal designs

- **Best Designs**
  - 🏆 Best Efficiency Design
  - 💰 Best Cost Design
  - ⚖️ Best Balanced Design

- **Pareto Frontier Plot**
  - X-axis: Efficiency (%)
  - Y-axis: Relative Cost (×)
  - Gray dots: All designs
  - Red stars: Pareto frontier
  - Markers: Best designs

**Example Result:**
```
Design Space: 48 candidates
Valid Designs: 42
Pareto Optimal: 8

Best Efficiency Design:
- MOSFET: IMZA65R020M2H
- Diode: C4D30120A
- Frequency: 100kHz
- Efficiency: 97.8%
- Cost: 2.5×

Best Cost Design:
- MOSFET: IMZA65R040M2H
- Diode: C3D16065D
- Frequency: 80kHz
- Efficiency: 96.2%
- Cost: 1.8×
```

**Interpretation:**
The Pareto frontier shows the trade-off between efficiency and cost. Designs on the frontier are "non-dominated" - you can't improve one objective without worsening the other.

**Performance:**
- Small design space (20 evaluations): ~30 seconds
- Medium (50 evaluations): ~60 seconds
- Large (100 evaluations): ~120 seconds

---

### Tab 7: About

Documentation, references, and usage tips.

---

## Usage Examples

### Example 1: Quick MOSFET Loss Check

**Goal:** Calculate losses for IMZA65R020M2H at 20A RMS, 400V, 100kHz

1. Go to **"MOSFET Loss Analysis"** tab
2. Select **"IMZA65R020M2H"** from dropdown
3. Click **"Load Parameters from Library"**
4. Set sliders:
   - I_RMS: 20A
   - V_DS: 400V
   - Frequency: 100kHz
   - Duty Cycle: 0.45
   - Junction Temp: 100°C
5. Click **"Calculate Losses"**

**Result:** Total loss ~15W (conduction ~8.6W, switching ~5.4W, gate ~0.9W)

---

### Example 2: Analyze 6.6kW 3-Phase System

**Goal:** Analyze complete 6.6kW marine PSFB system

1. Go to **"System Analysis"** tab
2. Default values are already set for 6.6kW system:
   - Power: 6600W
   - Phases: 3 @ 120°
   - Components: IMZA65R020M2H + diode
3. Click **"Analyze System"** (no changes needed!)

**Result:**
- Efficiency: ~97.67%
- Total Loss: ~157W
- Per-phase: ~52W

---

### Example 3: Design 3kW Transformer

**Goal:** Design transformer for 3kW, 400V→48V @ 100kHz

1. Go to **"Magnetic Design"** → **"Transformer Design"** sub-tab
2. Enter specifications:
   - Power: 3000W
   - V_in: 360V min, 400V nom, 440V max
   - V_out: 48V
   - Frequency: 100kHz
3. Keep default design parameters (or adjust)
4. Click **"Design Transformer"**

**Result:**
- Turns ratio: 16:2 (or similar)
- Core: PQ32/30 or ETD39
- Total loss: ~20-25W
- Complete winding design

---

### Example 4: Find Optimal Design

**Goal:** Find best 3kW PSFB design with >95% efficiency

1. Go to **"Optimizer"** tab
2. Enter specifications:
   - Power: 2500W min, 3000W rated, 3300W max
   - V_in: 360-440V (nom 400V)
   - V_out: 48V
   - Phases: 1
   - Efficiency Target: 95%
3. Select **"Balanced (Efficiency + Cost)"**
4. Set Max Evaluations: 20 (for quick test)
5. Click **"Run Optimization"**
6. Wait ~30-60 seconds
7. Review Pareto frontier plot and best designs

**Result:**
- Multiple optimal designs shown
- Trade-off visualization
- Specific component recommendations

---

### Example 5: Extract Parameters from Datasheet

**Goal:** Extract parameters from Infineon IMZA65R020M2H datasheet PDF

1. Download datasheet PDF from manufacturer website
2. Go to **"Datasheet Parser"** tab
3. Drag PDF file into upload area (or click to browse)
4. Click **"Extract Parameters"**
5. Review extracted parameters and confidence scores
6. Verify critical parameters (especially from graphs)

**Extracted:**
- Part number, voltage/current ratings
- R_DS(on) @ 25°C and 150°C
- Gate charge values
- Capacitances
- Confidence scores for each parameter

---

## Technical Details

### Component Library

**MOSFETs (6 devices):**
- **SiC (4):** IMZA65R020M2H, IMZA65R048M1H, C2M0080120D, C3M0065090D
- **Si (2):** IPP60R099C6, SPP20N60C3

**Diodes (5 devices):**
- **SiC Schottky (3):** C4D30120A, C3D16065D, IDH16G65C5
- **Si PN (2):** DSEP30-06A, MBR20100CT

### Loss Calculation Methods

**MOSFET:**
- Conduction: `P = R_DS(on)(Tj) × I²_rms`
- Switching: Based on Infineon AN2019-10
- Gate drive: `P = Q_g × V_gs × f`
- C_oss: `P = 0.5 × C_oss × V²_ds × f`

**Diode:**
- Conduction: `P = V_F(Tj) × I_avg + r_f × I²_rms`
- Reverse recovery: `P = 0.5 × Q_rr × V_r × f`

**Magnetics:**
- Core loss: Steinmetz equation
- Copper loss: DC + AC (skin/proximity effects)

### Optimization Algorithm

1. **Design Space Generation**
   - Component combinations from library
   - Frequency range (typically 80-200kHz)
   - Automatic transformer design for each

2. **Evaluation**
   - Calculate losses at multiple load points
   - Compute CEC efficiency
   - Estimate relative cost and size

3. **Pareto Frontier**
   - Find non-dominated solutions
   - Multi-objective comparison

4. **Ranking**
   - Best efficiency (max η)
   - Best cost (min cost)
   - Best balanced (max score)

---

## Troubleshooting

### Issue: GUI doesn't open in browser

**Solution:**
```bash
# Manually open browser to:
http://localhost:7860

# If using WSL2, try:
http://[::1]:7860
```

### Issue: "Gradio not installed"

**Solution:**
```bash
pip install gradio
```

### Issue: Import errors for psfb_loss_analyzer

**Solution:**
```bash
# Reinstall package
pip install -e .
```

### Issue: Datasheet parser not working

**Solution:**
```bash
# Install PDF parsing dependencies
pip install pdfplumber PyPDF2 pandas
```

### Issue: Optimization is slow

**Solution:**
- Reduce Max Evaluations (try 5-10 for quick test)
- Use fewer phases (1-phase faster than 3-phase)

### Issue: "Component not found in library"

**Solution:**
- Check spelling of part number
- Use dropdown to select from available components
- Verify component is in library (see list in Tab 1 dropdown)

---

## Performance Tips

### Fast Workflows

**Quick Loss Check:**
- Use **MOSFET/Diode Loss Analysis** tabs
- Load from library → Calculate
- Time: < 1 second

**System Analysis:**
- Use default values for 6.6kW example
- Modify as needed
- Time: 1-2 seconds

**Optimization:**
- Start with small design space (10-20 evaluations)
- Increase if needed
- Time: 30-60 seconds

### Slow Workflows to Avoid

**Large Optimization:**
- Max evaluations > 100
- Multi-phase with large design space
- Can take 5+ minutes

**Solution:** Use smaller max evaluations for iterative design

---

## WSL2 Specific Notes

### Running GUI in WSL2

The GUI works seamlessly in WSL2:

1. **Launch from WSL2 terminal:**
   ```bash
   python psfb_gui.py
   ```

2. **Browser opens automatically in Windows**
   - WSL2 automatically forwards port 7860
   - Windows browser connects to WSL2 server

3. **Access from Windows:**
   - Use: `http://localhost:7860`
   - Server runs in WSL2, browser in Windows

### Troubleshooting WSL2

**If browser doesn't open automatically:**
1. Check firewall settings
2. Manually navigate to `http://localhost:7860`

**If connection refused:**
```bash
# Check if port is already in use
netstat -tuln | grep 7860

# Kill process if needed
kill <PID>
```

---

## Keyboard Shortcuts

When GUI is running:

- **Ctrl+C** in terminal: Stop server
- **F5** in browser: Refresh page
- **Ctrl+R**: Reload browser (keeps session)
- **Ctrl+Shift+R**: Hard reload (clears cache)

---

## Next Steps

1. ✅ **Try each tab** - Explore all 7 tabs to understand capabilities
2. ✅ **Run examples** - Follow the example workflows above
3. ✅ **Design your PSFB** - Use optimizer to find best design
4. ✅ **Export results** - Copy/paste markdown results to reports

---

## Additional Resources

- **INSTALL.md** - Installation guide
- **QUICK_START.md** - 10-minute tutorial
- **TESTING.md** - Testing guide
- **VSCODE.md** - VS Code integration
- **psfb_loss_analyzer/README.md** - Technical documentation

---

## Support

For issues or questions:
1. Check this README
2. Review documentation files
3. Check GitHub issues
4. Create new issue with details

---

**Version:** 1.0.0 - Complete GUI Interface
**Author:** PSFB Loss Analysis Tool Development Team

**Enjoy designing high-efficiency PSFB converters!** 🚀

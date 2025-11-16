# PSFB Loss Analyzer & Optimization Suite

A comprehensive Python-based loss analysis and automated design tool for Phase-Shifted Full-Bridge (PSFB) converters, implementing methodologies from Infineon's "MOSFET Power Losses Calculation Using the DataSheet Parameters" application note and advanced optimization algorithms.

## Overview

This tool provides complete power loss analysis, magnetic design, efficiency mapping, and automated design optimization for PSFB converters from 1kW to 10kW+, with specific focus on SiC-based high-efficiency designs for telecom, marine, industrial, and EV charging applications.

### Key Features

- **✅ Complete Loss Analysis**
  - MOSFET conduction and switching losses (temperature-dependent)
  - Diode/SR losses with SiC Schottky vs Si PN comparison
  - Transformer and inductor core + copper losses
  - Capacitor ESR losses with multi-phase ripple cancellation
  - System-level loss integration and efficiency calculation

- **✅ Magnetic Component Design**
  - Resonant inductor design for ZVS operation
  - Transformer design using Kg area product method
  - Output inductor design with DC bias and ripple control
  - Comprehensive core database (TDK PQ, Ferroxcube ETD, EPCOS E)
  - Core loss calculation using Steinmetz equation

- **✅ Multi-Phase Support**
  - 1-4 phase interleaved operation
  - Phase shift optimization (180°, 120°, 90°)
  - Ripple cancellation analysis
  - Per-phase and system-level loss breakdown

- **✅ Efficiency Mapping**
  - Efficiency vs load curves (10-100%)
  - 2D efficiency maps (voltage vs load)
  - CEC weighted efficiency calculation
  - European efficiency calculation
  - CSV export for analysis

- **✅ Automated Design Optimization**
  - Multi-objective optimization (efficiency, cost, size)
  - Pareto frontier generation
  - Component library with SiC/Si MOSFETs and diodes
  - Automatic magnetic component design
  - Design space exploration with constraints

- **✅ Datasheet Parameter Extraction**
  - Automatic PDF parsing for MOSFETs and diodes
  - Table extraction and parameter pattern matching
  - Batch processing and comparison
  - Component library generation

- **✅ Graphical User Interface (NEW!)**
  - Complete 7-tab web-based GUI using Gradio
  - MOSFET and diode loss analysis with component library
  - Drag & drop PDF datasheet parser
  - Multi-phase system analyzer
  - Interactive magnetic design (transformer + inductors)
  - Automated optimization with Pareto frontier visualization
  - Real-time calculations and interactive plots

- **⚙️ Advanced Features (Planned)**
  - Thermal iteration solver (manual junction temp currently)
  - Automated report generation with plots
  - Sensitivity analysis
  - Monte Carlo tolerance analysis

## Graphical User Interface

**NEW in v1.0.0!** Complete web-based GUI for interactive analysis and design.

### Launch GUI

```bash
python psfb_gui.py
# Opens browser to http://localhost:7860
```

### GUI Features (7 Tabs)

1. **MOSFET Loss Analysis** - Component library, loss calculations, visualizations
2. **Diode Loss Analysis** - SiC/Si comparison, loss breakdown
3. **Datasheet Parser** - Drag & drop PDF extraction, auto-parameter detection
4. **System Analysis** - Multi-phase PSFB system analyzer (1-4 phases)
5. **Magnetic Design** - Transformer and inductor design with loss calculation
6. **Optimizer** - Automated design with Pareto frontier
7. **About** - Documentation and references

See **[GUI_README.md](../GUI_README.md)** for complete GUI user guide with examples and workflows.

## Project Status

**Current Version: 1.0.0 - Complete GUI Interface** ✅

### Implemented Modules ✅

| Module | Status | Description |
|--------|--------|-------------|
| `psfb_gui.py` | ✅ **NEW!** | **7-tab web GUI with Gradio** |
| `circuit_params.py` | ✅ Complete | Data class definitions for all components |
| `mosfet_losses.py` | ✅ Complete | MOSFET conduction, switching, gate drive losses |
| `diode_losses.py` | ✅ Complete | Diode conduction and reverse recovery losses |
| `magnetics_design.py` | ✅ Complete | Base magnetic design utilities |
| `resonant_inductor_design.py` | ✅ Complete | ZVS resonant inductor design |
| `transformer_design.py` | ✅ Complete | Transformer design with Kg method + losses |
| `output_inductor_design.py` | ✅ Complete | Output inductor with DC bias |
| `system_analyzer.py` | ✅ Complete | Complete system loss integration |
| `efficiency_mapper.py` | ✅ Complete | Efficiency curves and maps |
| `optimizer.py` | ✅ Complete | Multi-objective design optimization |
| `component_library.py` | ✅ Complete | Component database (MOSFETs, diodes, caps) |
| `core_database.py` | ✅ Complete | Magnetic core database |
| `config_loader.py` | ✅ Complete | JSON configuration support |
| `Datasheet_analyzer/` | ✅ Complete | PDF datasheet parsing |

### Not Yet Implemented ❌

| Module | Status | Notes |
|--------|--------|-------|
| `thermal_solver.py` | ❌ Pending | Iterative thermal solver (currently uses fixed junction temp) |
| `report_generator.py` | ❌ Pending | Automated report generation with plots |

**Note:** Transformer losses ARE implemented in `transformer_design.py` and `magnetics_design.py` (core + copper losses). A standalone `transformer_losses.py` is not needed.

## Installation

### Requirements

- **Python 3.8+** (3.10+ recommended)
- **Platform:** Windows 11 (WSL2), Linux, macOS
- **Dependencies:** numpy, scipy, matplotlib, pandas

### Quick Install (Windows 11 + WSL2)

See **[INSTALL.md](../INSTALL.md)** for complete step-by-step installation guide.

```bash
# 1. Install WSL2 and Ubuntu 22.04 (see INSTALL.md)

# 2. Clone repository
git clone <repo-url>
cd CLD_test

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install package
pip install -e .

# 5. Install optional dependencies for datasheet parsing
pip install pdfplumber PyPDF2 pandas
```

### Verify Installation

```bash
python test_installation.py
```

Expected output: `✓ ALL TESTS PASSED - Installation is complete!`

## Quick Start

See **[QUICK_START.md](../QUICK_START.md)** for 10-minute tutorial.

### 1. Your First Loss Calculation (3 minutes)

```python
from psfb_loss_analyzer import (
    MOSFETParameters,
    CapacitanceVsVoltage,
    calculate_mosfet_conduction_loss,
)

# Define MOSFET
mosfet = MOSFETParameters(
    part_number="IMZA65R020M2H",
    v_dss=650.0,
    i_d_continuous=90.0,
    r_dson_25c=16e-3,
    r_dson_150c=22e-3,
    capacitances=CapacitanceVsVoltage(
        c_iss_constant=7200e-12,
        c_oss_constant=520e-12,
        c_rss_constant=15e-12,
    ),
    q_g=142e-9,
)

# Calculate loss
loss = calculate_mosfet_conduction_loss(
    mosfet=mosfet,
    i_rms=20.0,
    duty_cycle=0.45,
    t_junction=100.0,
)

print(f"MOSFET Loss: {loss:.2f}W")  # Output: ~8.6W
```

### 2. Complete System Analysis (5 minutes)

```bash
# Run 6.6kW 3-phase example
python psfb_loss_analyzer/examples/example_6p6kw_complete_analysis.py
```

Output shows complete loss breakdown, per-phase analysis, and system efficiency.

### 3. Automated Design Optimization (2 minutes)

```bash
# Run auto-design optimizer
python psfb_loss_analyzer/examples/example_auto_design.py
```

Automatically selects components, designs magnetics, and finds Pareto optimal designs!

## Documentation

| Document | Description |
|----------|-------------|
| **[INSTALL.md](../INSTALL.md)** | Complete Windows 11 + WSL2 + VS Code installation guide |
| **[QUICK_START.md](../QUICK_START.md)** | 10-minute tutorial with examples |
| **[TESTING.md](../TESTING.md)** | Comprehensive testing guide with test code |
| **[VSCODE.md](../VSCODE.md)** | VS Code integration, debugging, shortcuts |
| **[REFERENCES.md](docs/REFERENCES.md)** | Reference materials and methodology |

## Testing

See **[TESTING.md](../TESTING.md)** for detailed testing instructions.

### Run All Tests

```bash
# Full test suite
python tests/test_suite.py

# Quick tests only
python tests/test_suite.py --quick

# Specific component
python tests/unit/test_mosfet_loss.py
```

### Test Coverage

- ✅ Circuit parameters
- ✅ MOSFET loss calculations
- ✅ Diode loss calculations
- ✅ Transformer design
- ✅ System analyzer
- ✅ Optimizer
- ⚙️ Integration tests (partial)

## Example Designs

Three complete reference designs are provided:

### 1. 6.6kW Marine PSFB (3-Phase Interleaved)
- **Application:** High-power marine systems
- **Configuration:** 3 × 2.2kW @ 120° phase shift
- **Input:** 400V DC
- **Output:** 48V @ 137.5A (6.6kW total)
- **Primary:** Infineon IMZA65R020M2H (650V, 20mΩ SiC)
- **Secondary:** Wolfspeed C4D30120A (1200V, 30A SiC Schottky)
- **Efficiency:** 97.67% @ full load
- **File:** `examples/example_6p6kw_complete_analysis.py`

### 2. 3kW Telecom PSFB (Automated Design)
- **Application:** Telecom/data center
- **Input:** 300-420V DC (380V nominal)
- **Output:** 48V @ 62.5A
- **Automated component selection and optimization**
- **File:** `examples/example_auto_design.py`

### 3. 5kW Industrial PSFB
- **Application:** Industrial equipment
- **Input:** 300V DC
- **Output:** 48V @ 104A
- **Primary:** Infineon IMZA65R020M2H
- **File:** `examples/example_5kw_infineon_20mohm.py`

## Architecture

### Module Organization

```
psfb_loss_analyzer/
├── Core Parameters & Configuration
│   ├── circuit_params.py          # Dataclass definitions
│   ├── config_loader.py            # JSON configuration
│   └── core_database.py            # Magnetic core database
│
├── Loss Calculations (IMPLEMENTED ✅)
│   ├── mosfet_losses.py            # MOSFET losses
│   └── diode_losses.py             # Diode losses
│
├── Magnetic Design (IMPLEMENTED ✅)
│   ├── magnetics_design.py         # Base magnetic utilities
│   ├── resonant_inductor_design.py # ZVS inductor
│   ├── transformer_design.py       # Transformer + losses
│   └── output_inductor_design.py   # Output inductor
│
├── System Analysis (IMPLEMENTED ✅)
│   ├── system_analyzer.py          # Complete system integration
│   └── efficiency_mapper.py        # Efficiency analysis
│
├── Optimization (IMPLEMENTED ✅)
│   ├── component_library.py        # Component database
│   └── optimizer.py                # Multi-objective optimization
│
├── Datasheet Tools (IMPLEMENTED ✅)
│   └── Datasheet_analyzer/
│       ├── datasheet_parser.py     # PDF parsing
│       ├── table_extractor.py      # Table extraction
│       └── batch_processor.py      # Batch processing
│
├── Future Enhancements (PENDING ⚙️)
│   ├── thermal_solver.py           # Iterative thermal solver
│   └── report_generator.py         # Automated reporting
│
└── Examples & Documentation
    ├── examples/                   # Reference designs
    ├── docs/                       # Documentation
    └── tests/                      # Test suite
```

### API Overview

#### Loss Calculations
```python
from psfb_loss_analyzer import (
    calculate_mosfet_conduction_loss,
    calculate_mosfet_switching_loss,
    calculate_mosfet_gate_drive_loss,
    calculate_diode_conduction_loss,
    calculate_diode_reverse_recovery_loss,
)
```

#### Magnetic Design
```python
from psfb_loss_analyzer import (
    design_resonant_inductor,
    design_transformer,
    design_output_inductor,
)
```

#### System Analysis
```python
from psfb_loss_analyzer import (
    analyze_psfb_phase,
    analyze_psfb_system,
    sweep_efficiency_vs_load,
    generate_efficiency_map,
)
```

#### Optimization
```python
from psfb_loss_analyzer import (
    DesignSpecification,
    optimize_design,
    ObjectiveFunction,
)
```

## Methodology & References

This tool implements industry-standard methodologies:

### Primary References
1. **Infineon Application Note**: "MOSFET Power Losses Calculation Using the Data Sheet Parameters" (2006)
   - MOSFET conduction loss with temperature dependence
   - Switching loss calculation (hard switching and ZVS)
   - Miller time calculation

2. **Erickson & Maksimovic**: "Fundamentals of Power Electronics" 3rd Ed (2020)
   - Chapter 13: Soft Switching (ZVS principles)
   - Chapter 14: Magnetics Design

3. **McLyman**: "Transformer and Inductor Design Handbook" 4th Ed (2011)
   - Kg area product method
   - Core loss (Steinmetz equation)
   - Winding AC resistance (Dowell method)

4. **Texas Instruments**: UCC28950/UCC28951 PSFB Controller Datasheet
   - PSFB topology operation
   - Phase shift modulation

### Key Equations

**MOSFET Conduction Loss:**
```
P_cond = R_DS(on)(Tj) × I²_rms

where:
R_DS(on)(Tj) = R_DS(on)_max(25°C) × [1 + α/100 × (Tj - 25)]
α = 100 × (R_DS(on)_150C / R_DS(on)_25C - 1) / (150 - 25)
```

**Transformer Core Loss:**
```
P_core = k × f^α × B^β × V_e
```

**ZVS Switching:**
```
E_on ≈ 0 (capacitive turn-on energy only)
E_off = V_DS × I_D × (t_ru + t_fi) / 2
```

See **[REFERENCES.md](docs/REFERENCES.md)** for complete methodology documentation.

## Development Roadmap

- [x] **Phase 1:** Input parameter interface ✅
- [x] **Phase 2:** Loss calculation engine ✅
- [x] **Phase 3:** Magnetic component design ✅
- [x] **Phase 4:** System integration & efficiency mapping ✅
- [x] **Phase 5:** Automated design optimization ✅
- [x] **Phase 6:** Datasheet parameter extraction ✅
- [x] **Phase 6.5:** Graphical user interface ✅ **NEW!**
- [ ] **Phase 7:** Thermal iteration solver ⚙️
- [ ] **Phase 8:** Report generation ⚙️
- [ ] **Phase 9:** Validation against experimental data ⚙️

## Contributing

Contributions welcome! Areas for enhancement:

- **Thermal Solver:** Iterative junction temperature calculation with convergence
- **Report Generator:** Automated plot generation and PDF reports
- **Component Library:** Expand with more MOSFETs/diodes
- **Validation:** Compare against lab measurements
- **GUI:** Web-based or desktop interface

## License

[To be determined]

## Author

PSFB Loss Analysis Tool Development Team

---

**Get Started:**
1. Install: [INSTALL.md](../INSTALL.md)
2. Learn: [QUICK_START.md](../QUICK_START.md)
3. Test: [TESTING.md](../TESTING.md)
4. Develop: [VSCODE.md](../VSCODE.md)

**Questions?** Check the documentation or run examples!

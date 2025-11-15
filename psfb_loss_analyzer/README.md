# PSFB Loss Analyzer & Optimization Suite

A comprehensive Python-based loss analysis tool for Phase-Shifted Full-Bridge (PSFB) converters, implementing the methodology from Infineon's "MOSFET Power Losses Calculation Using the DataSheet Parameters" application note.

## Overview

This tool provides detailed power loss analysis for PSFB converters in the 1.7kW-7kW range, with specific focus on marine and industrial applications. It calculates losses across all major components and provides efficiency optimization guidance.

### Key Features

- **Comprehensive Loss Analysis**
  - MOSFET conduction and switching losses (primary & secondary)
  - Transformer core and winding losses
  - Rectifier losses (diode or synchronous MOSFET)
  - Passive component losses (inductors, capacitors)

- **Advanced Thermal Modeling**
  - Junction temperature iteration with feedback
  - Temperature-dependent RDS(on) calculation
  - Heatsink and cooling system analysis

- **Multi-Phase Support**
  - 1-4 phase interleaved operation
  - Current sharing analysis
  - Phase shift optimization

- **Flexible Component Modeling**
  - Voltage-dependent capacitances
  - AC resistance with skin/proximity effects
  - SiC vs Si MOSFET comparison

## Project Status

**Current Phase: Input Parameter Interface (COMPLETE ✓)**

The input parameter interface is fully implemented and ready for use. The following components are available:

- ✅ Complete data class definitions (`circuit_params.py`)
- ✅ Configuration loader with JSON support (`config_loader.py`)
- ✅ **Magnetic core database** with TDK PQ, Ferroxcube ETD, EPCOS E cores (`core_database.py`)
- ✅ **Three reference design examples:**
  - 3kW Marine PSFB (48V→24V) with Wolfspeed C3M0065090J
  - 5kW Telecom PSFB (300V→48V) with Infineon IMZA65R020M2H
  - 3kW Fanless PSFB (380V→48V) with Infineon IMZA65R040M2H
- ✅ CLI interface (`main.py`)
- ✅ Configuration validation
- ✅ **Comprehensive reference documentation** (`docs/REFERENCES.md`)

**Next Phase: Loss Calculation Engine (PENDING)**

The following modules need to be implemented:
- `mosfet_losses.py` - MOSFET loss calculations
- `transformer_losses.py` - Magnetic component losses
- `diode_losses.py` - Rectifier losses
- `thermal_solver.py` - Thermal iteration
- `efficiency_mapper.py` - Efficiency curves
- `optimizer.py` - Design optimization
- `report_generator.py` - Results visualization

## Installation

### Requirements

- Python 3.9 or higher
- Dependencies: `numpy`, `scipy`, `matplotlib`, `pandas` (to be added)

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd psfb_loss_analyzer

# Install dependencies (when requirements.txt is added)
# pip install -r requirements.txt
```

## Quick Start

### 1. Run with Example Configuration

```bash
python main.py --example --show-params
```

This loads a pre-configured 3kW marine PSFB converter (48V→24V) and displays all parameters.

### 2. Export Configuration Template

```bash
python main.py --export-template my_design.json
```

Edit the exported JSON file with your design parameters.

### 3. Analyze Your Design

```bash
python main.py --config my_design.json --show-params
```

### 4. Validate Configuration Only

```bash
python main.py --config my_design.json --validate-only
```

## Example Configurations

Three reference designs are provided to demonstrate different use cases:

### 1. 3kW Marine PSFB (Wolfspeed SiC)
**File**: `examples/example_3kw_marine_psfb.py`

- **Application**: Marine power systems
- **Input**: 36-60V DC (48V nominal)
- **Output**: 24V @ 125A (3000W)
- **Primary**: Wolfspeed C3M0065090J (650V, 65mΩ SiC)
- **Secondary**: TI CSD19538Q3A (100V, 1.8mΩ SR MOSFET)
- **Transformer**: ETD59 with 3C95 ferrite
- **Frequency**: 100 kHz
- **Cooling**: Forced air (15 CFM)

Run: `python examples/example_3kw_marine_psfb.py`

### 2. 5kW Telecom PSFB (Infineon IMZA65R020M2H)
**File**: `examples/example_5kw_infineon_20mohm.py`

- **Application**: Telecom/Datacom power supplies, EV charging
- **Input**: 200-400V DC (300V nominal, high-voltage DC link)
- **Output**: 48V @ 104A (5000W)
- **Primary**: Infineon IMZA65R020M2H (650V, 20mΩ CoolSiC™)
- **Secondary**: Infineon IMZA120R007M2H (1200V, 7mΩ SiC SR)
- **Transformer**: TDK PQ80/60 with PC95 ferrite
- **Frequency**: 150 kHz (high frequency enabled by SiC)
- **Cooling**: Forced air (25 CFM)
- **Key Feature**: Ultra-low RDS(on) for high efficiency at high voltage

Run: `python examples/example_5kw_infineon_20mohm.py`

### 3. 3kW Fanless PSFB (Infineon IMZA65R040M2H)
**File**: `examples/example_3kw_infineon_40mohm.py`

- **Application**: Industrial equipment, renewable energy, fanless operation
- **Input**: 300-450V DC (380V nominal)
- **Output**: 48V @ 62.5A (3000W)
- **Primary**: Infineon IMZA65R040M2H (650V, 40mΩ CoolSiC™)
- **Secondary**: TI CSD19536KTT (100V, 3.9mΩ Si SR MOSFET)
- **Transformer**: Ferroxcube ETD59 with 3C95 ferrite
- **Frequency**: 120 kHz (moderate for natural convection)
- **Cooling**: **Natural convection only (fanless)**
- **Key Feature**: Cost-optimized design with SiC primary, Si secondary

Run: `python examples/example_3kw_infineon_40mohm.py`

### Comparison of Examples

| Parameter | Marine 3kW | Telecom 5kW | Fanless 3kW |
|-----------|------------|-------------|-------------|
| **Input Voltage** | 48V | 300V | 380V |
| **Power Level** | 3kW | 5kW | 3kW |
| **Primary Tech** | SiC (Wolfspeed) | SiC (Infineon 20mΩ) | SiC (Infineon 40mΩ) |
| **Secondary Tech** | Si SR | SiC SR | Si SR |
| **Frequency** | 100 kHz | 150 kHz | 120 kHz |
| **Transformer Core** | ETD59 | PQ80/60 | ETD59 |
| **Cooling** | Forced Air | Forced Air | Natural Convection |
| **Target Application** | Low voltage, high current | High voltage, high power | Fanless, industrial |

## Magnetic Core Database

A comprehensive database of transformer cores is included in `core_database.py`:

### TDK PQ Cores (Large Power)
- **PQ 60/42**: 630mm² Ae, suitable for 3-5kW
- **PQ 65/50**: 842mm² Ae, suitable for 4-6kW
- **PQ 80/60**: 1230mm² Ae, suitable for 5-8kW
- **PQ 107/87**: 2210mm² Ae, suitable for 8-12kW

### Ferroxcube ETD Cores
- **ETD39 through ETD59**: Complete range for 1-7kW

### EPCOS E Cores
- **E 42/21/20 through E 65/32/27**: Standard E-core range

### Core Loss Coefficients (Steinmetz)
Pre-calculated coefficients for:
- **Ferroxcube 3C95** (25-200kHz optimal)
- **Ferroxcube 3F3** (100-500kHz optimal)
- **EPCOS N87** (25-200kHz optimal)
- **EPCOS N97** (100-500kHz optimal, lower loss)
- **Nanocrystalline** (>200kHz, very low loss)

Temperature-dependent coefficients provided at 25°C, 60°C, 100°C, and 120°C with automatic interpolation.

**Usage**:
```python
from core_database import get_core_geometry, get_core_loss_coefficients, list_available_cores

# Get specific core
core = get_core_geometry("PQ80/60")

# Get loss coefficients at operating temperature
coeffs = get_core_loss_coefficients(CoreMaterial.FERRITE_3C95, temperature=85.0)

# List cores suitable for power range
cores = list_available_cores(min_power_kw=3.0, max_power_kw=5.0)
```

## Input Parameter Interface

The input interface is organized into hierarchical data classes, providing type-safe and well-documented parameter definitions.

### Top-Level Configuration Structure

```python
PSFBConfiguration
├── project_name: str
├── topology: CircuitTopology
├── components: ComponentSet
├── thermal: ThermalParameters
└── operating_point: OperatingConditions
```

### Circuit Topology Parameters

Defines the fundamental converter specifications:

```python
CircuitTopology(
    v_in=VoltageRange(min, nominal, max),  # Input voltage range
    v_out=float,                            # Output voltage
    p_out=float,                            # Output power (W)
    f_sw=float,                             # Switching frequency (Hz)
    phase_shift_min=float,                  # Min phase shift angle (°)
    phase_shift_max=float,                  # Max phase shift angle (°)
    n_phases=int,                           # Number of interleaved phases (1-4)
    dead_time_primary=float,                # Primary dead time (s)
    dead_time_secondary=float,              # Secondary dead time (s)
    transformer_turns_ratio=float           # Np/Ns ratio
)
```

### MOSFET Parameters

Complete datasheet-based MOSFET characterization:

```python
MOSFETParameters(
    part_number=str,                        # Device part number
    v_dss=float,                            # Voltage rating (V)
    i_d_continuous=float,                   # Current rating (A)

    # Temperature-dependent RDS(on) - critical for accuracy
    r_dson_25c=float,                       # @ 25°C typical (Ω)
    r_dson_25c_max=float,                   # @ 25°C maximum (Ω)
    r_dson_150c=float,                      # @ 150°C typical (Ω)
    r_dson_150c_max=float,                  # @ 150°C maximum (Ω)

    # Gate charge characteristics
    q_g=float,                              # Total gate charge (C)
    q_gs=float,                             # Gate-source charge (C)
    q_gd=float,                             # Gate-drain (Miller) charge (C)
    v_gs_plateau=float,                     # Miller plateau voltage (V)

    # Capacitances (voltage-dependent)
    capacitances=CapacitanceVsVoltage(...),

    # Switching times
    t_r=float,                              # Rise time (s)
    t_f=float,                              # Fall time (s)

    # Body diode parameters
    v_sd=float,                             # Forward voltage (V)
    q_rr=float,                             # Reverse recovery charge (C)
    t_rr=float,                             # Reverse recovery time (s)

    # Thermal
    r_th_jc=float,                          # Junction-to-case (°C/W)
    t_j_max=float,                          # Max junction temp (°C)

    # Gate drive
    v_gs_drive=float,                       # Drive voltage (V)
    r_g_internal=float,                     # Internal gate resistance (Ω)
    r_g_external=float                      # External gate resistance (Ω)
)
```

**Key Feature: Temperature Coefficient Calculation**

The `alpha_rdson` property automatically calculates the temperature coefficient α from the two-point RDS(on) data, per Infineon methodology:

```
R_DS(on)(Tj) = R_DS(on)_max(25°C) × [1 + α/100 × (Tj - 25)]
```

### Voltage-Dependent Capacitances

MOSFETs have significant capacitance variation with VDS. Two modes are supported:

**Option 1: Constant Values (Simplified)**
```python
CapacitanceVsVoltage(
    c_iss_constant=1350e-12,  # 1350 pF
    c_oss_constant=95e-12,     # 95 pF
    c_rss_constant=25e-12      # 25 pF
)
```

**Option 2: Voltage-Dependent Curves (Accurate)**
```python
CapacitanceVsVoltage(
    capacitance_curve=[
        # (V_DS, C_iss, C_oss, C_rss) in Farads
        (25.0,  1350e-12, 95e-12, 25e-12),
        (100.0, 1300e-12, 45e-12, 12e-12),
        (200.0, 1270e-12, 30e-12, 8e-12),
        (400.0, 1250e-12, 20e-12, 5e-12),
    ]
)
```

The tool automatically interpolates capacitance values at any VDS.

### Transformer Parameters

Complete magnetic component specification:

```python
TransformerParameters(
    core_geometry=CoreGeometry(
        core_type=str,              # e.g., "ETD59", "PQ40/40"
        effective_area=float,       # Ae (m²)
        effective_length=float,     # le (m)
        effective_volume=float,     # Ve (m³)
        window_area=float,          # Wa (m²)
        b_sat=float                 # Saturation flux density (T)
    ),
    core_material=CoreMaterial,     # Ferrite type (3C95, N87, etc.)
    core_loss_coefficients=CoreLossCoefficients(
        k=float,                    # Steinmetz coefficient
        alpha=float,                # Frequency exponent
        beta=float,                 # Flux density exponent
        temperature=float           # Valid at this temp (°C)
    ),
    primary_winding=WindingParameters(...),
    secondary_winding=WindingParameters(...),
    leakage_inductance=float,       # Lleak (H)
    magnetizing_inductance=float,   # Lmag (H)
    isolation_capacitance=float     # Cpri-sec (F)
)
```

**Winding Parameters:**
```python
WindingParameters(
    n_turns=int,                    # Number of turns
    wire_diameter=float,            # Wire diameter with insulation (m)
    wire_conductors=int,            # Parallel strands (Litz wire)
    dc_resistance=float,            # DC resistance @ 20°C (Ω)
    layers=int,                     # Number of layers
    foil_winding=bool               # True for foil, False for round wire
)
```

### Thermal Parameters

Thermal environment and cooling specification:

```python
ThermalParameters(
    t_ambient=float,                # Ambient temperature (°C)
    cooling_method=CoolingMethod,   # NATURAL_CONVECTION, FORCED_AIR, LIQUID_COOLING
    forced_air_cfm=float,           # Air flow rate (CFM)
    heatsink_r_th_ca=float,         # Case-to-ambient thermal resistance (°C/W)
    thermal_interface_r_th=float,   # TIM resistance (°C/W)
    target_t_j_max=float            # Design target max Tj (°C)
)
```

### Operating Conditions

Defines the analysis operating point:

```python
OperatingConditions(
    load_percentage=float,          # Load % of rated power (10-100%)
    input_voltage=float,            # Actual Vin for this point (V)
    output_current=float,           # Output current (A)
    phase_shift_angle=float,        # Phase shift angle (°)
    zvs_achieved_primary=bool       # ZVS status (affects switching losses)
)
```

## Example: 3kW Marine PSFB Converter

A complete reference design is provided in `examples/example_3kw_marine_psfb.py`:

**Specifications:**
- Input: 36-60V DC (48V nominal, marine battery system)
- Output: 24V DC @ 125A (3kW)
- Switching frequency: 100 kHz
- Primary: Wolfspeed C3M0065090J (650V 65mΩ SiC MOSFET)
- Secondary: TI CSD19538Q3A (100V 1.8mΩ synchronous rectifier)
- Transformer: ETD59 core with 3C95 ferrite, 12:12 turns
- Cooling: Forced air, 15 CFM, 50°C ambient

### Running the Example

```bash
# View complete parameter details
python main.py --example --show-params

# Validate the design
python main.py --example --validate-only

# Generate example configuration
python examples/example_3kw_marine_psfb.py
```

## Creating Your Own Configuration

### Method 1: Python Script

Create a Python file similar to `example_3kw_marine_psfb.py`:

```python
from circuit_params import *

def create_my_config():
    topology = CircuitTopology(
        v_in=VoltageRange(min=20.0, nominal=24.0, max=30.0),
        v_out=12.0,
        p_out=1500.0,  # 1.5kW
        f_sw=150e3,     # 150 kHz
        # ... other parameters
    )

    # Define MOSFETs, transformer, etc.
    # ...

    config = PSFBConfiguration(
        project_name="My 1.5kW PSFB",
        topology=topology,
        components=components,
        thermal=thermal,
        operating_point=operating_point
    )

    return config

if __name__ == "__main__":
    config = create_my_config()
    config.to_json("my_design.json")
```

### Method 2: JSON Configuration

Export a template and edit the JSON directly:

```bash
python main.py --export-template my_design.json
```

Then edit `my_design.json` with your parameters and load it:

```bash
python main.py --config my_design.json
```

## Configuration Validation

The tool performs automatic validation checks:

- **Voltage Ratings:** Ensures component voltage ratings have adequate margin
- **Current Ratings:** Verifies current capacity vs. expected load
- **Thermal Margins:** Checks that target Tj doesn't exceed device limits
- **Transformer Turns Ratio:** Validates against expected voltage transformation
- **Operating Point:** Ensures phase shift and other parameters are within valid ranges

Run validation:
```bash
python main.py --config my_design.json --validate-only
```

## Theoretical Foundation

### MOSFET Conduction Losses (Infineon Section 2.1)

```
P_cond = R_DS(on)(Tj) × I²_rms

where:
R_DS(on)(Tj) = R_DS(on)_max(25°C) × [1 + α/100 × (Tj - 25)]

α = 100 × (R_DS(on)_150C / R_DS(on)_25C - 1) / (150 - 25)
```

### MOSFET Switching Losses (Infineon Section 2.2)

**Hard Switching:**
```
E_on = U_DD × I_Don × (t_ri + t_fu)/2 + Q_rr × U_DD
E_off = U_DD × I_Doff × (t_ru + t_fi)/2
P_sw = (E_on + E_off) × f_sw
```

**ZVS Operation:**
```
E_on ≈ 0  (capacitive turn-on energy only)
E_off = U_DD × I_Doff × (t_ru + t_fi)/2
```

### Miller Time Calculation (Infineon Page 8-9)

Two-point capacitance approximation:
```
t_fu = (C_gd1 + C_gd2)/2 × (U_DD - V_plateau) / [(V_gs - V_plateau) / R_g]
```

### Transformer Core Losses (Steinmetz Equation)

```
P_core = k × f^α × B^β × V_e

where:
- k, α, β: Material coefficients from datasheet
- f: Switching frequency (Hz)
- B: Peak flux density (T)
- V_e: Effective core volume (m³)
```

### Thermal Iteration

1. Start with assumed Tj (e.g., 125°C)
2. Calculate all losses using temperature-dependent parameters
3. Compute junction temperature:
   ```
   Tj = Tamb + P_total × (R_th_jc + R_th_TIM + R_th_ca)
   ```
4. Update R_DS(on)(Tj) and re-calculate losses
5. Iterate until ΔTj < 1°C

## Input Parameter Guidelines

### Extracting Parameters from Datasheets

**MOSFET Parameters:**
- RDS(on): Use "typical" for nominal analysis, "maximum" for worst-case
- Look for RDS(on) vs Temperature curve - extract at 25°C and 150°C
- Gate charge: Use values at rated VDS and VGS=drive voltage
- Capacitances: Extract C-V curves from "Typical Characteristics" section
- Switching times: Note test conditions (VGS, RG, ID) - must match your application

**Transformer Core:**
- Core loss coefficients: Extract from manufacturer's material datasheet
  - Ferroxcube: Check core loss curves in material specs (3C95, 3F3, etc.)
  - EPCOS/TDK: Similar material data available
  - Use curve-fitting tools to extract k, α, β for Steinmetz equation
- Winding resistance: Measure or calculate from wire gauge and length

**Thermal Resistance:**
- Heatsink R_th_ca: From heatsink datasheet at specified airflow
- If forced air: Use curve of R_th vs CFM
- Thermal interface: 0.1-0.3 °C/W typical for thermal pads/paste

### Common Pitfalls

❌ **Using RDS(on) at wrong VGS**
- Ensure datasheet value matches your gate drive voltage

❌ **Ignoring temperature coefficient**
- RDS(on) can increase 40-50% from 25°C to 150°C

❌ **Constant capacitances for high-voltage designs**
- Coss varies 5-10× over voltage range - use curves for accuracy

❌ **Overlooking body diode reverse recovery**
- Critical for secondary SR MOSFETs in hard-switching rectification

## File Structure

```
psfb_loss_analyzer/
├── __init__.py                 # Package interface ✓
├── circuit_params.py           # Data class definitions ✓
├── config_loader.py            # JSON configuration loader ✓
├── core_database.py            # Magnetic core database ✓
├── main.py                     # CLI interface ✓
├── requirements.txt            # Python dependencies ✓
├── README.md                   # Main documentation ✓
│
├── docs/
│   └── REFERENCES.md           # Reference materials catalog ✓
│
├── PDFs/
│   └── README.md               # PDF library documentation ✓
│   # Place reference PDFs here (see docs/REFERENCES.md)
│
├── examples/
│   ├── example_3kw_marine_psfb.py           # 3kW Marine (48V→24V) ✓
│   ├── example_5kw_infineon_20mohm.py       # 5kW Telecom (300V→48V) ✓
│   ├── example_3kw_infineon_40mohm.py       # 3kW Fanless (380V→48V) ✓
│   ├── 3kw_marine_psfb_config.json          # Exported config ✓
│   ├── 5kw_infineon_20mohm_config.json      # Exported config ✓
│   ├── 3kw_infineon_40mohm_config.json      # Exported config ✓
│   └── template.json                         # Configuration template ✓
│
├── tests/                      # Unit tests (TODO)
│
└── [Future Loss Calculation Modules]
    ├── mosfet_losses.py        # MOSFET loss calculations (TODO)
    ├── transformer_losses.py   # Magnetic losses (TODO)
    ├── diode_losses.py         # Rectifier losses (TODO)
    ├── thermal_solver.py       # Thermal iteration (TODO)
    ├── efficiency_mapper.py    # Efficiency analysis (TODO)
    ├── optimizer.py            # Design optimization (TODO)
    └── report_generator.py     # Results output (TODO)
```

## API Reference

### Key Classes

- **`PSFBConfiguration`**: Top-level configuration container
- **`CircuitTopology`**: Converter topology specification
- **`MOSFETParameters`**: Complete MOSFET datasheet model
- **`TransformerParameters`**: Magnetic component specification
- **`ThermalParameters`**: Thermal environment definition
- **`ComponentSet`**: Complete component selection

### Key Functions

```python
# Load configuration from JSON
config = load_configuration("my_design.json")

# Validate configuration
issues = config.validate()
is_valid = validate_configuration(config)  # Prints results

# Export configuration
config.to_json("output.json", indent=2)

# Access calculated properties
alpha = mosfet.alpha_rdson  # Temperature coefficient
r_g_tot = mosfet.r_g_total  # Total gate resistance
c_oss = mosfet.capacitances.get_coss(vds=100.0)  # Coss @ 100V
```

## Reference Materials

This project is built upon industry-standard methodologies and validated designs. Comprehensive reference documentation is provided in `docs/REFERENCES.md`.

### Required Reference Documents

Place the following PDFs in `psfb_loss_analyzer/PDFs/` directory:

#### Core Methodology (Essential)
- **Infineon "MOSFET Power Losses Calculation Using the DataSheet Parameters" (2006)**
  - PRIMARY reference for all MOSFET loss calculations
  - Implements temperature-dependent RDS(on), switching energies, Miller time calculation

#### PSFB Topology References
- **Texas Instruments "UCC28950, UCC28951 - Phase-Shifted Full-Bridge Controller"**
  - PSFB design equations, dead time calculation, phase shift modulation
- **"Implementation of a PSFB DC-DC ZVS converter" - Assel Zhaksvlvk Thesis (2019)**
  - Detailed ZVS analysis and experimental validation
- **Microchip "Phase-Shifted Full-Bridge Quarter Brick DC-DC Converter Reference Design"**
  - Complete design example with measured efficiency data

#### Power Electronics Textbooks
- **"Fundamentals of Power Electronics" 3rd Edition (2020)** - Erickson & Maksimovic
  - Chapter 13: Soft Switching (ZVS principles)
  - Chapter 14: Magnetics Design
- **"Transformer and Inductor Design Handbook" 4th Edition (2011)** - Colonel Wm. T. McLyman
  - Core loss calculation (Steinmetz equation)
  - Winding AC resistance (Dowell method)
  - Thermal design

#### Component Datasheets
- **Infineon IMZA65R020M2H** (650V, 20mΩ CoolSiC™ MOSFET)
- **Infineon IMZA65R040M2H** (650V, 40mΩ CoolSiC™ MOSFET)
- **TDK "Large PQ series TDK PQ60x42 to PQ107x87x70"** (Transformer cores)

### Reference Documentation Structure

**`docs/REFERENCES.md`** provides:
- Detailed description of each reference material
- Specific equations and page numbers
- Parameter extraction procedures from datasheets
- Implementation mapping to code modules
- Quick reference tables for key formulas

**`PDFs/README.md`** lists all expected PDF files and copyright information.

### Using the References

The references are organized by implementation phase:

1. **For MOSFET Loss Implementation** → Infineon AN + MOSFET datasheets
2. **For Transformer Design** → McLyman Handbook + Core datasheets
3. **For PSFB Topology** → UCC28951 datasheet + Zhaksvlvk thesis
4. **For Validation** → Microchip reference design + measured data

See `docs/REFERENCES.md` for reading order and specific sections to reference.

## Contributing

This project is currently in development. The input parameter interface is complete. Contributions to the loss calculation engine are welcome!

### Development Roadmap

- [x] Phase 1: Input parameter interface
- [x] Phase 1.5: Core database and reference examples
- [ ] Phase 2: Loss calculation engine
- [ ] Phase 3: Thermal solver
- [ ] Phase 4: Efficiency mapping
- [ ] Phase 5: Optimization engine
- [ ] Phase 6: Report generation
- [ ] Phase 7: Validation against reference designs

## References

### Primary Methodology
1. **Infineon Application Note**: "MOSFET Power Losses Calculation Using the Data Sheet Parameters" (2006)
2. **McLyman, Colonel Wm. T.**: "Transformer and Inductor Design Handbook" 4th Edition (2011)
3. **Erickson & Maksimovic**: "Fundamentals of Power Electronics" 3rd Edition (2020)

### PSFB Topology
4. **Texas Instruments**: "UCC28950, UCC28951 - Phase-Shifted Full-Bridge Controller" Datasheet
5. **Zhaksvlvk, Assel**: "Implementation of a PSFB DC-DC ZVS converter with Peak Current Mode Control" Master's Thesis (2019)
6. **Microchip**: "Phase-Shifted Full-Bridge (PSFB) Quarter Brick DC-DC Converter Reference Design"

### Fundamental Theory
7. **Dowell, P.L.**: "Effects of Eddy Currents in Transformer Windings" (1966)
8. **Steinmetz, C.P.**: "On the Law of Hysteresis" (1984)

### Component Datasheets
9. **Infineon**: IMZA65R020M2H, IMZA65R040M2H CoolSiC™ MOSFET Datasheets
10. **TDK**: Large PQ Series Ferrite Core Catalog
11. **Ferroxcube**: Soft Ferrite Material Specifications (3C95, 3F3)

**For detailed reference information, parameter extraction guides, and implementation mapping, see `docs/REFERENCES.md`.**

## License

[To be determined]

## Author

PSFB Loss Analysis Tool

---

**Questions or Issues?**

Please refer to the examples and validation output. Ensure all datasheets are consulted for accurate parameter extraction.

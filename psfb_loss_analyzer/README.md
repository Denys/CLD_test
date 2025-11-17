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
- ✅ Example 3kW marine PSFB design
- ✅ CLI interface (`main.py`)
- ✅ Configuration validation

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

### 1. Run GUI Application

```bash
python psfb_gui.py
```

The GUI provides a comprehensive interface for:
- **UCC28951 Controller Design**: Automatic component calculation, Bode plots, and BOM generation
- **Loss Analysis**: (Coming soon) Complete power loss analysis
- **Thermal Analysis**: (Coming soon) Junction temperature modeling
- **Optimization**: (Coming soon) Design parameter optimization

### 2. Run with Example Configuration (CLI)

```bash
python main.py --example --show-params
```

This loads a pre-configured 3kW marine PSFB converter (48V→24V) and displays all parameters.

### 3. Export Configuration Template (CLI)

```bash
python main.py --export-template my_design.json
```

Edit the exported JSON file with your design parameters.

### 4. Analyze Your Design (CLI)

```bash
python main.py --config my_design.json --show-params
```

### 5. Validate Configuration Only (CLI)

```bash
python main.py --config my_design.json --validate-only
```

## GUI Application

### UCC28951 Controller Design Tab

The GUI includes a comprehensive UCC28951 Phase-Shifted Full-Bridge Controller design tool.

**Features:**
- **Input Fields**: Power stage specifications (voltages, power, frequency, transformer)
- **Real-Time Calculation**: Automatic component value calculation
- **Bode Plot Visualization**: Loop stability analysis with phase/gain margins
- **BOM Export**: Generate bill of materials in CSV format

**Usage:**
1. Launch GUI: `python psfb_gui.py`
2. Navigate to "UCC28951 Controller" tab
3. Enter power stage specifications:
   - Input voltage range (min/nom/max)
   - Output voltage and power
   - Switching frequency and dead time
   - Transformer turns ratio and inductances
4. Select control mode (Voltage Mode or Peak Current Mode)
5. Click "Calculate Components" to design controller
6. View results in three tabs:
   - **Component Values**: Calculated resistor/capacitor values with explanations
   - **Bode Plot**: Loop gain and phase response with stability margins
   - **Bill of Materials**: Complete component list for ordering

**Component Calculations:**
- **Timing Components (RT, CT)**: Set oscillator frequency
- **Soft-Start (CSS)**: Set startup time (default 10ms)
- **Adaptive Delay (RADS)**: Optimize ZVS transitions
- **Feedback Divider**: Set output voltage regulation
- **Compensation Network**: Type II loop compensation with automatic zero/pole placement
- **UVLO Divider**: Set input undervoltage lockout threshold
- **Current Sense (RCS)**: For peak current mode control

**BOM Export:**
- Click "Export BOM" to save complete bill of materials
- CSV format compatible with most BOM management tools
- Includes designator, value, description, and package size

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
├── circuit_params.py                    # Data class definitions ✓
├── config_loader.py                     # JSON configuration loader ✓
├── main.py                              # CLI interface ✓
├── psfb_gui.py                          # GUI application ✓
├── ucc28951_controller.py               # UCC28951 controller design ✓
├── mosfet_losses.py                    # MOSFET loss calculations (TODO)
├── transformer_losses.py               # Magnetic losses (TODO)
├── diode_losses.py                     # Rectifier losses (TODO)
├── thermal_solver.py                   # Thermal iteration (TODO)
├── efficiency_mapper.py                # Efficiency analysis (TODO)
├── optimizer.py                        # Design optimization (TODO)
├── report_generator.py                 # Results output (TODO)
├── examples/
│   ├── example_3kw_marine_psfb.py                 ✓
│   ├── example_2_2kw_marine_psfb_diode.py         ✓
│   ├── 3kw_marine_psfb_config.json                ✓
│   └── 2_2kw_marine_psfb_diode_config.json        ✓
├── tests/                              # Unit tests (TODO)
├── requirements.txt                    # Python dependencies ✓
└── README.md                           # This file ✓
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

## Contributing

This project is currently in development. The input parameter interface is complete. Contributions to the loss calculation engine are welcome!

### Development Roadmap

- [x] Phase 1: Input parameter interface
- [ ] Phase 2: Loss calculation engine
- [ ] Phase 3: Thermal solver
- [ ] Phase 4: Efficiency mapping
- [ ] Phase 5: Optimization engine
- [ ] Phase 6: Report generation
- [ ] Phase 7: Validation against reference designs

## References

1. Infineon Application Note: "MOSFET Power Losses Calculation Using the Data Sheet Parameters"
2. Dowell, P.L.: "Effects of Eddy Currents in Transformer Windings"
3. Steinmetz, C.P.: "On the Law of Hysteresis"
4. Erickson & Maksimovic: "Fundamentals of Power Electronics"

## License

[To be determined]

## Author

PSFB Loss Analysis Tool

---

**Questions or Issues?**

Please refer to the examples and validation output. Ensure all datasheets are consulted for accurate parameter extraction.

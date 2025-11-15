# Reference Materials and Design Resources

This document catalogs the reference materials used in developing the PSFB Loss Analyzer and provides guidance on extracting parameters for analysis.

## 📚 Reference Library

### Core Methodology - Loss Calculation

**Primary Reference:**
- **"MOSFET Power Losses Calculation Using the DataSheet Parameters" (2006)** - Infineon
  - **Status**: ⭐ PRIMARY REFERENCE
  - **Location**: `PDF/! MOSFET Power Losses Calculation Using the DataSheet Parameters 2006.pdf`
  - **Usage**: Foundation for all MOSFET loss calculations
  - **Key Sections**:
    - Section 2.1: Conduction Losses (RDS(on) temperature dependency)
    - Section 2.2: Switching Losses (Turn-on, turn-off energy)
    - Section 2.3: Gate Drive Losses
    - Pages 8-9: Miller time calculation with two-point capacitance method
  - **Implementation**:
    - `mosfet_losses.py` - Direct implementation of Equations 1-15
    - Temperature coefficient α calculation from Equation 3
    - Miller plateau analysis for switching time estimation

### Power Electronics Fundamentals

**Textbook:**
- **"Fundamentals of Power Electronics" 3rd Edition (2020)** - Erickson & Maksimovic
  - **Location**:
    - `PDF/Fundamentals of Power Electronics 3ed 2020 - Part 1.pdf`
    - `PDF/Fundamentals of Power Electronics 3ed 2020 - Part 2.pdf`
    - `PDF/Fundamentals of Power Electronics 3ed 2020 - Magnetics Chapters.pdf`
  - **Usage**: Theoretical foundation and topology analysis
  - **Key Chapters**:
    - Chapter 6: Converter Circuits
    - Chapter 13: Soft Switching (ZVS, ZCS principles)
    - Chapter 14: Magnetics Design
      - Core loss mechanisms
      - Steinmetz equation application
      - Winding loss analysis
  - **Implementation**:
    - `transformer_losses.py` - Core and winding loss models
    - ZVS achievement verification algorithms

### PSFB Topology Specific

**Controller IC Documentation:**
- **"UCC28950, UCC28951 - Phase-Shifted Full-Bridge Controller"** - Texas Instruments
  - **Status**: ⭐ PSFB DESIGN REFERENCE
  - **Location**: `PDF/! UCC28950, UCC28951 - Phase-Shifted Full-Bridge Controller.pdf`
  - **Usage**: PSFB-specific design equations and timing relationships
  - **Key Sections**:
    - Dead time calculation for ZVS
    - Phase shift angle vs duty cycle relationship
    - Current sensing and protection
    - Adaptive delay control
  - **Parameters to Extract**:
    - Minimum dead time for ZVS: `t_dead = 2 × (Q_oss / I_load) × (V_in / 2)`
    - Phase shift modulation equations
    - Output current estimation: `I_out = (V_in × D_eff) / (8 × f_sw × L_leak × n)`
  - **Implementation**:
    - `psfb_equations.py` - Design equations module
    - Operating point calculation from phase shift angle

**Reference Design:**
- **"Phase-Shifted Full-Bridge (PSFB) Quarter Brick DC-DC Converter Reference Design"** - Microchip
  - **Location**: `PDF/Phase-Shifted Full-Bridge (PSFB) Quarter Brick DC-DC Converter Reference Design.pdf`
  - **Usage**: Complete design example for validation
  - **Contents**:
    - Bill of materials
    - Component selection rationale
    - Measured efficiency data
    - Thermal management approach
  - **Implementation**:
    - Create validation test case in `tests/test_microchip_reference.py`
    - Compare calculated vs measured efficiency

**Academic Thesis:**
- **"Implementation of a PSFB DC-DC ZVS converter with Peak Current Mode Control"** - Assel Zhaksvlvk (2019)
  - **Location**: `PDF/Implementation of a PSFB DC-DC ZVS converter with Peak Current Mode Control - Assel Zhaksvlvk 2019.pdf`
  - **Usage**: Detailed practical implementation insights
  - **Key Topics**:
    - ZVS condition derivation
    - Peak current mode control implementation
    - Experimental validation methodology
  - **Implementation**:
    - ZVS verification algorithm
    - Current waveform analysis

### Magnetics Design

**Comprehensive Reference:**
- **"Transformer and Inductor Design Handbook" 4th Edition (2011)** - Colonel Wm. T. McLyman
  - **Location**: `PDF/Transformer and Inductor Design Handbook 4ed 2011 - Colonel Wm. T. McLyman.pdf`
  - **Usage**: Authoritative guide for magnetic component design
  - **Key Topics**:
    - Core material selection (Chapter 2)
    - Core loss calculation methods (Chapter 3)
    - Winding resistance with AC effects (Chapter 4)
      - Skin depth: δ = 66.2 / √f_Hz mm (copper at 100°C)
      - Dowell equations for proximity effect
    - Thermal design of magnetics (Chapter 8)
  - **Implementation**:
    - `transformer_losses.py` - AC resistance calculation (Dowell method)
    - `magnetics_design.py` - Core selection and design automation

### Component Datasheets

**Infineon CoolSiC™ MOSFETs (650V):**

1. **IMZA65R020M2H** (20mΩ, 650V)
   - **Location**: `PDF/infineon-imza65r020m2h-datasheet-en.pdf`
   - **Key Parameters** (to extract):
     - RDS(on) @ 25°C: ~16 mΩ typ, 20 mΩ max
     - RDS(on) @ 150°C: ~22 mΩ typ, 28 mΩ max
     - Gate charge: Qg, Qgs, Qgd @ VDS=400V, VGS=18V
     - Capacitances: Ciss, Coss, Crss vs VDS (extract C-V curves)
     - Switching energies: Eon, Eoff @ test conditions
     - Body diode: VSD, Qrr (should be minimal for SiC)
     - Thermal: Rth(j-c), Zth(j-c) transient
   - **Usage**: Example for high-power PSFB (5-10kW range)
   - **Configuration File**: `examples/psfb_infineon_20mohm.py`

2. **IMZA65R040M2H** (40mΩ, 650V)
   - **Location**: `PDF/infineon-imza65r040m2h-datasheet-en.pdf`
   - **Key Parameters** (to extract):
     - RDS(on) @ 25°C: ~32 mΩ typ, 40 mΩ max
     - RDS(on) @ 150°C: ~44 mΩ typ, 55 mΩ max
     - Gate charge: Qg, Qgs, Qgd @ VDS=400V, VGS=18V
     - Capacitances: Ciss, Coss, Crss vs VDS
     - Switching energies: Eon, Eoff
     - Body diode: VSD, Qrr
     - Thermal: Rth(j-c)
   - **Usage**: Example for mid-power PSFB (2-5kW range)
   - **Configuration File**: `examples/psfb_infineon_40mohm.py`

**TDK Magnetics - Large PQ Cores:**
- **"Large PQ series TDK PQ60x42 to PQ107x87x70"**
  - **Location**: `PDF/Large PQ series TDK PQ60x42 to PQ107x87x70.pdf`
  - **Contents**:
    - Core geometries (Ae, le, Ve, Wa)
    - Core loss curves for PC95 ferrite material
    - Thermal resistance data
    - Mechanical dimensions
  - **Core Sizes Covered**:
    - PQ 60/42: ~600mm² Ae, suitable for 3-5kW
    - PQ 80/60: ~1200mm² Ae, suitable for 5-8kW
    - PQ 107/87: ~2200mm² Ae, suitable for 8-12kW
  - **Usage**: Transformer core selection database
  - **Implementation**:
    - Add TDK PQ cores to `CoreGeometry` database
    - Extract Steinmetz coefficients from loss curves

---

## 📊 Parameter Extraction Guide

### From MOSFET Datasheets

**1. RDS(on) Temperature Characterization:**
```python
# From "Electrical Characteristics" table:
r_dson_25c = [value at VGS=18V, Tj=25°C, typical]
r_dson_25c_max = [value at VGS=18V, Tj=25°C, maximum]

# From "Thermal Characteristics" or graphs:
r_dson_150c = [value at VGS=18V, Tj=150°C, typical]
r_dson_150c_max = [value at VGS=18V, Tj=150°C, maximum]

# Tool automatically calculates α coefficient
```

**2. Capacitance vs Voltage Curves:**
```python
# From "Typical Characteristics" - look for "Capacitances vs. VDS" graph
# Extract points manually or use curve digitizer
capacitance_curve = [
    (VDS_1, Ciss_1, Coss_1, Crss_1),  # e.g., (25V, 4500pF, 180pF, 45pF)
    (VDS_2, Ciss_2, Coss_2, Crss_2),  # e.g., (100V, 4200pF, 95pF, 22pF)
    (VDS_3, Ciss_3, Coss_3, Crss_3),  # e.g., (400V, 4000pF, 55pF, 12pF)
    # Add more points for accuracy
]
```

**3. Gate Charge:**
```python
# From "Electrical Characteristics" table or "Gate Charge" graph
# Ensure test condition matches your VDS and VGS:
q_g = [Total gate charge @ VDS=400V, VGS=18V]  # in Coulombs (nC × 1e-9)
q_gs = [Gate-source charge]  # From gate charge curve inflection
q_gd = [Gate-drain charge]    # From Miller plateau width
v_gs_plateau = [Miller plateau voltage]  # From gate charge curve
```

**4. Switching Energies (if available):**
```python
# From "Switching Characteristics" table
# Note test conditions: VDS, ID, RG, VGS, temperature
e_on_datasheet = [Turn-on energy @ test conditions]  # Joules
e_off_datasheet = [Turn-off energy @ test conditions]

# For SiC MOSFETs with ZVS:
# e_on ≈ 0 (we'll calculate capacitive charging)
# Use e_off from datasheet and scale to actual conditions
```

**5. Thermal Parameters:**
```python
r_th_jc = [Junction-to-case thermal resistance]  # From datasheet table
# Also note if transient thermal impedance curve is available
# for pulse/transient analysis
```

### From Transformer Core Datasheets

**1. Core Geometry (from mechanical drawings):**
```python
CoreGeometry(
    core_type="PQ80/60",  # From datasheet designation
    effective_area=Ae,     # mm² → convert to m²
    effective_length=le,   # mm → convert to m
    effective_volume=Ve,   # mm³ → convert to m³
    window_area=Wa,        # mm² → convert to m²
    b_sat=0.39            # From material specs @ operating temp
)
```

**2. Core Loss Coefficients (Steinmetz):**
```python
# From core loss density vs frequency curves at specific flux density
# Use curve fitting tool or extract from table:
# P_v [kW/m³] = k × f^α × B^β

# For PC95 ferrite @ 100°C (example values - extract from datasheet):
CoreLossCoefficients(
    k=31.5,      # Material constant
    alpha=1.65,  # Frequency exponent
    beta=2.68,   # Flux density exponent
    temperature=100.0
)
```

### From PSFB Controller Datasheets (UCC28951)

**1. Dead Time Calculation:**
```python
# From UCC28951 application section:
# t_dead = Time for output capacitance to discharge/charge

# For ZVS achievement:
# t_dead_min = (Q_oss × V_in) / (2 × I_resonant)
# where I_resonant = resonant current at switching instant

dead_time_primary = [calculated or measured value]  # seconds
```

**2. Phase Shift to Duty Relationship:**
```python
# From controller equations:
# D_eff = φ / 180°  (for 0° < φ < 180°)
# where φ is phase shift angle in degrees

phase_shift_angle = [control variable, 0-180 degrees]
```

---

## 🎯 Implementation Roadmap with References

### Phase 2: MOSFET Loss Calculations (`mosfet_losses.py`)

**Reference**: Infineon AN "MOSFET Power Losses Calculation Using the DataSheet Parameters"

**Functions to Implement:**

```python
def calculate_rdson_at_temp(r_dson_25c_max, r_dson_150c_max, t_junction):
    """
    Infineon AN Equation 3 (Page 5)
    R_DS(on)(Tj) = R_DS(on)_max(25°C) × [1 + α/100 × (Tj - 25)]
    """
    pass

def calculate_conduction_loss(mosfet_params, i_rms, t_junction):
    """
    Infineon AN Equation 1 (Page 4)
    P_cond = R_DS(on)(Tj) × I²_rms
    """
    pass

def calculate_switching_energy_hard(v_ds, i_d, t_ri, t_fu, t_ru, t_fi, q_rr):
    """
    Infineon AN Equations 7-8 (Page 10)
    E_on = U_DD × I_Don × (t_ri + t_fu)/2 + Q_rr × U_DD
    E_off = U_DD × I_Doff × (t_ru + t_fi)/2
    """
    pass

def calculate_miller_time(c_gd1, c_gd2, v_dd, v_plateau, v_gs, r_g):
    """
    Infineon AN Pages 8-9
    Two-point capacitance approximation for Miller plateau
    """
    pass

def calculate_zvs_capacitive_loss(c_oss, v_ds, f_sw):
    """
    For ZVS operation: E_cap = ½ × C_oss × V²_DS
    P_cap = E_cap × f_sw
    """
    pass
```

### Phase 3: Transformer Losses (`transformer_losses.py`)

**References**:
- McLyman "Transformer and Inductor Design Handbook" Ch. 3-4
- Erickson "Fundamentals of Power Electronics" Ch. 14

**Functions to Implement:**

```python
def calculate_core_loss_steinmetz(k, alpha, beta, f_sw, b_peak, v_core):
    """
    McLyman Ch. 3 / Erickson Ch. 14
    P_core = k × f^α × B^β × V_e
    """
    pass

def calculate_winding_dc_loss(r_dc, i_rms):
    """
    Simple I²R loss
    """
    pass

def calculate_winding_ac_resistance(r_dc, freq, wire_diameter, layers):
    """
    McLyman Ch. 4 - Dowell method
    R_ac = R_dc × F_r(frequency, geometry)
    """
    pass

def calculate_skin_depth(frequency, temperature=100):
    """
    δ = 66.2 / √f_Hz mm for copper @ 100°C
    """
    pass
```

### Phase 4: Thermal Solver (`thermal_solver.py`)

**Reference**: Infineon AN Section on thermal feedback

**Functions to Implement:**

```python
def iterative_thermal_solve(config, max_iterations=20, tolerance=1.0):
    """
    1. Assume Tj = 125°C
    2. Calculate all losses with temperature-dependent params
    3. Calculate Tj = Tamb + P_total × R_th_total
    4. Update parameters with new Tj
    5. Repeat until ΔTj < tolerance
    """
    pass
```

### Phase 5: PSFB-Specific Calculations (`psfb_equations.py`)

**Reference**: UCC28951 datasheet, Zhaksvlvk thesis

**Functions to Implement:**

```python
def calculate_output_power_from_phase_shift(v_in, v_out, n, l_leak, f_sw, phi):
    """
    UCC28951 equation for phase-shift modulation
    P_out = (V_in² × φ × (180° - φ)) / (8 × n² × L_leak × f_sw × 180°²)
    """
    pass

def verify_zvs_condition(i_magnetizing, i_reflected, c_oss, v_in, t_dead):
    """
    Zhaksvlvk thesis - ZVS achievement verification
    Resonant current must be sufficient to discharge C_oss
    """
    pass
```

---

## 📝 Next Steps for Reference Integration

1. **Extract Infineon MOSFET Parameters** ✓
   - Create `examples/psfb_infineon_20mohm.py` with IMZA65R020M2H
   - Create `examples/psfb_infineon_40mohm.py` with IMZA65R040M2H
   - Extract parameters from datasheets manually

2. **Build TDK Core Database** ✓
   - Add PQ60/42, PQ80/60, PQ107/87 to core library
   - Extract Steinmetz coefficients from PC95 curves

3. **Implement Loss Calculation Modules**
   - `mosfet_losses.py` - Using Infineon AN methodology
   - `transformer_losses.py` - Using McLyman handbook
   - `thermal_solver.py` - Iterative junction temperature

4. **Create Validation Test Cases**
   - UCC28951 reference design validation
   - Microchip quarter-brick reference comparison
   - Zhaksvlvk thesis experimental data comparison

5. **Documentation Updates**
   - Cross-reference equations to specific page numbers
   - Add formula derivations in appendix
   - Create parameter extraction tutorial

---

## 🔍 Quick Reference: Key Equations

### MOSFET Losses (Infineon AN)

| Loss Type | Equation | Reference |
|-----------|----------|-----------|
| Conduction | `P_cond = R_DS(on)(Tj) × I²_rms` | Infineon AN Eq. 1 |
| RDS(on) temp | `R_DS(on)(Tj) = R_DS(on)_max(25°C) × [1 + α/100 × (Tj - 25)]` | Infineon AN Eq. 3 |
| Turn-on (hard) | `E_on = V_DS × I_D × (t_ri + t_fu)/2 + Q_rr × V_DS` | Infineon AN Eq. 7 |
| Turn-off | `E_off = V_DS × I_D × (t_ru + t_fi)/2` | Infineon AN Eq. 8 |
| Gate drive | `P_gate = Q_g × V_GS × f_sw × N_parallel` | Infineon AN Eq. 14 |

### Transformer Losses (McLyman)

| Loss Type | Equation | Reference |
|-----------|----------|-----------|
| Core loss | `P_core = k × f^α × B^β × V_e` | McLyman Ch. 3 |
| Skin depth | `δ = 66.2 / √f mm` (Cu @ 100°C) | McLyman Ch. 4 |
| AC resistance | `R_ac = R_dc × F_r` | McLyman Ch. 4 |
| Flux density | `B = (V × 10⁸) / (4 × f × N × A_e)` | McLyman Ch. 2 |

### PSFB Power Transfer (UCC28951)

| Parameter | Equation | Reference |
|-----------|----------|-----------|
| Output power | `P_out = V_in² × φ × (180-φ) / (8 × n² × L_leak × f_sw × 180²)` | UCC28951 |
| Duty cycle | `D_eff = φ / 180°` | UCC28951 |
| ZVS dead time | `t_dead > Q_oss × V_in / (2 × I_res)` | UCC28951 |

---

## 📚 Reading Order for Implementation

**For MOSFET Loss Implementation:**
1. Infineon AN "MOSFET Power Losses..." - Complete read (20 pages)
2. Infineon datasheets - Extract parameters for examples
3. Erickson Ch. 13 - Soft switching background

**For Transformer Design:**
1. McLyman Ch. 2-4 - Core selection and loss calculation
2. Erickson Ch. 14 - Power electronics perspective
3. TDK datasheet - Specific core parameters

**For PSFB Topology:**
1. UCC28951 datasheet - Section 8 (Application Information)
2. Zhaksvlvk thesis - Chapters 2-3 (Design and analysis)
3. Microchip reference design - Complete design example

**For Validation:**
1. Compare calculations with Microchip measured efficiency
2. Verify transformer design with McLyman examples
3. Cross-check MOSFET losses with Infineon examples

---

**Document Version**: 1.0
**Last Updated**: 2025-11-15
**Status**: Reference catalog complete, awaiting PDF accessibility for parameter extraction

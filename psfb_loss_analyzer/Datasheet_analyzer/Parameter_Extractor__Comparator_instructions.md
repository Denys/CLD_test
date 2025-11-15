# Datasheet Parameter Extractor & Comparator Instructions

## Overview

This tool automatically extracts electrical parameters from SiC MOSFET and Schottky diode datasheets (PDF format) and converts them into Python dataclass objects compatible with the PSFB Loss Analyzer.

## Supported Devices

### 1. SiC MOSFETs
- **Manufacturers:** Infineon (CoolSiC), Wolfspeed (C3M/C2M), Rohm, STMicroelectronics, OnSemi
- **Voltage Classes:** 650V, 900V, 1200V, 1700V
- **Package Types:** TO-247, TO-247-4, TO-263, D2PAK, etc.

### 2. SiC Schottky Diodes
- **Manufacturers:** Wolfspeed, Infineon, STMicroelectronics, Rohm, OnSemi
- **Voltage Classes:** 600V, 650V, 1200V, 1700V
- **Package Types:** TO-220, TO-247, DPAK, etc.

### 3. Si PN Diodes (Optional)
- **For comparison and cost-sensitive applications**

---

## Parameters to Extract

### A. SiC MOSFET Parameters

#### Absolute Maximum Ratings
| Parameter | Symbol | Location | Notes |
|-----------|--------|----------|-------|
| Drain-Source Voltage | V_DSS | Absolute Maximum Ratings table | Look for "Drain-Source voltage" |
| Continuous Drain Current | I_D | Absolute Maximum Ratings table | At T_C = 25°C or 100°C |
| Pulsed Drain Current | I_DM | Absolute Maximum Ratings table | Optional |
| Gate-Source Voltage | V_GS | Absolute Maximum Ratings table | Typically ±20V or ±25V for SiC |
| Total Power Dissipation | P_D | Absolute Maximum Ratings table | At T_C = 25°C |
| Junction Temperature | T_J | Absolute Maximum Ratings table | Typically 175°C for SiC |

#### Static Electrical Characteristics
| Parameter | Symbol | Test Conditions | Location | Notes |
|-----------|--------|-----------------|----------|-------|
| On-State Resistance (25°C) | R_DS(on) @ 25°C | V_GS = 18V or 20V, I_D = specified | Electrical Characteristics | Extract both typical and max |
| On-State Resistance (150°C) | R_DS(on) @ 150°C | V_GS = 18V or 20V, T_J = 150°C | Electrical Characteristics | Extract both typical and max |
| Gate Threshold Voltage | V_GS(th) | V_DS = V_GS, I_D = 1mA | Electrical Characteristics | Typical value |
| Zero Gate Voltage Drain Current | I_DSS | V_DS = rated, V_GS = 0V | Electrical Characteristics | Leakage current |

#### Dynamic Characteristics
| Parameter | Symbol | Test Conditions | Location | Notes |
|-----------|--------|-----------------|----------|-------|
| Input Capacitance | C_iss | V_DS = 400V or 800V, V_GS = 0V, f = 1MHz | Electrical Characteristics or graphs | May be voltage-dependent |
| Output Capacitance | C_oss | V_DS = 400V or 800V, V_GS = 0V, f = 1MHz | Electrical Characteristics or graphs | Highly voltage-dependent |
| Reverse Transfer Capacitance | C_rss (C_gd) | V_DS = 400V or 800V, V_GS = 0V, f = 1MHz | Electrical Characteristics or graphs | Miller capacitance |
| Total Gate Charge | Q_g | V_DS = specified, V_GS = 0V to 18V, I_D = specified | Electrical Characteristics or Gate Charge graph | Critical for switching |
| Gate-Source Charge | Q_gs | From Gate Charge curve | Gate Charge graph | Before Miller plateau |
| Gate-Drain Charge | Q_gd | From Gate Charge curve | Gate Charge graph | Miller plateau region |
| Turn-on Delay | t_d(on) | Switching characteristics table | Electrical Characteristics | Test conditions important |
| Rise Time | t_r | Switching characteristics table | Electrical Characteristics | 10% to 90% V_DS |
| Turn-off Delay | t_d(off) | Switching characteristics table | Electrical Characteristics | Test conditions important |
| Fall Time | t_f | Switching characteristics table | Electrical Characteristics | 90% to 10% V_DS |
| Gate Plateau Voltage | V_GS(plateau) | From Gate Charge curve | Gate Charge graph | Miller plateau level |

#### Thermal Characteristics
| Parameter | Symbol | Location | Notes |
|-----------|--------|----------|-------|
| Junction-to-Case Thermal Resistance | R_th(j-c) | Thermal characteristics | °C/W |
| Junction-to-Ambient Thermal Resistance | R_th(j-a) | Thermal characteristics | °C/W (if available) |

#### Body Diode Characteristics
| Parameter | Symbol | Test Conditions | Location | Notes |
|-----------|--------|-----------------|----------|-------|
| Continuous Source Current | I_S | Absolute Maximum Ratings | Body diode rating |
| Forward Voltage | V_SD | I_SD = specified, T_J = 25°C | Diode Characteristics | Typical value |
| Reverse Recovery Charge | Q_rr | Body Diode section | Electrical Characteristics | If listed (SiC body diodes have poor recovery) |

---

### B. SiC Schottky Diode Parameters

#### Absolute Maximum Ratings
| Parameter | Symbol | Location | Notes |
|-----------|--------|----------|-------|
| Repetitive Peak Reverse Voltage | V_RRM | Absolute Maximum Ratings | Working voltage |
| Average Forward Current | I_F(AV) | Absolute Maximum Ratings | At T_C = specified |
| Peak Forward Surge Current | I_FSM | Absolute Maximum Ratings | Single pulse |
| Operating Junction Temperature | T_J | Absolute Maximum Ratings | Typically 175°C for SiC |
| Storage Temperature | T_stg | Absolute Maximum Ratings | Range |

#### Static Electrical Characteristics
| Parameter | Symbol | Test Conditions | Location | Notes |
|-----------|--------|-----------------|----------|-------|
| Forward Voltage Drop (25°C) | V_F @ 25°C | I_F = specified (e.g., rated current) | Electrical Characteristics | Extract at multiple currents if available |
| Forward Voltage Drop (125°C) | V_F @ 125°C | I_F = specified, T_J = 125°C | Electrical Characteristics | Temperature coefficient |
| Forward Voltage Drop (175°C) | V_F @ 175°C | I_F = specified, T_J = 175°C | Electrical Characteristics | If available |
| Reverse Leakage Current | I_R | V_R = rated voltage, T_J = 25°C | Electrical Characteristics | Leakage |
| Reverse Leakage Current (High Temp) | I_R @ 125°C | V_R = rated voltage, T_J = 125°C | Electrical Characteristics | Temperature dependency |

#### Dynamic Characteristics
| Parameter | Symbol | Test Conditions | Location | Notes |
|-----------|--------|-----------------|----------|-------|
| Junction Capacitance | C_J | V_R = specified (e.g., 400V), f = 1MHz | Electrical Characteristics or graphs | Voltage-dependent |
| Reverse Recovery Time | t_rr | I_F = specified, di/dt = specified | Electrical Characteristics | Very low for SiC Schottky |
| Reverse Recovery Charge | Q_rr | I_F = specified, di/dt = specified | Electrical Characteristics | Minimal for SiC Schottky |

#### Thermal Characteristics
| Parameter | Symbol | Location | Notes |
|-----------|--------|----------|-------|
| Junction-to-Case Thermal Resistance | R_th(j-c) | Thermal characteristics | °C/W |
| Junction-to-Ambient Thermal Resistance | R_th(j-a) | Thermal characteristics | °C/W (if available) |

---

## Extraction Strategy

### 1. PDF Text Extraction
- **Primary Method:** Use `pdfplumber` or `PyPDF2` to extract text from tables
- **Fallback Method:** Use OCR (`pytesseract`) if PDF is scanned/image-based
- **Table Detection:** Look for table structures in "Electrical Characteristics" and "Absolute Maximum Ratings" sections

### 2. Graph Data Extraction
Some critical parameters are only available as graphs:
- **C_oss vs V_DS:** Output capacitance vs voltage
- **C_iss vs V_DS:** Input capacitance vs voltage
- **C_rss vs V_DS:** Reverse transfer capacitance vs voltage
- **Q_g vs V_GS:** Gate charge curve (extract Q_gs, Q_gd, V_plateau)
- **V_F vs I_F:** Forward voltage vs current (for diodes)
- **V_F vs T_J:** Forward voltage vs temperature

**Graph Extraction Methods:**
1. **Image extraction** from PDF
2. **Digitization** using `digitize` or manual point picking
3. **Curve fitting** to analytical models (e.g., C_oss = C0 + C1/(V_DS + V0))

### 3. Parameter Mapping
Map extracted values to dataclass fields:

**For MOSFETs:**
```python
MOSFETParameters(
    part_number="EXTRACTED_PART_NUMBER",
    v_dss=650.0,  # From Absolute Maximum Ratings
    i_d_continuous=90.0,  # From Absolute Maximum Ratings
    r_dson_25c=16e-3,  # From Electrical Characteristics (typical)
    r_dson_25c_max=20e-3,  # From Electrical Characteristics (max)
    r_dson_150c=22e-3,  # From Electrical Characteristics (typical)
    r_dson_150c_max=28e-3,  # From Electrical Characteristics (max)
    capacitances=CapacitanceVsVoltage(...),  # From graphs or tables
    q_g=142e-9,  # From Electrical Characteristics
    q_gs=38e-9,  # From Gate Charge graph
    q_gd=52e-9,  # From Gate Charge graph
    v_gs_plateau=4.5,  # From Gate Charge graph
    t_r=25e-9,  # From Switching Characteristics
    t_f=20e-9,  # From Switching Characteristics
)
```

**For Diodes:**
```python
DiodeParameters(
    part_number="EXTRACTED_PART_NUMBER",
    v_rrm=1200.0,  # From Absolute Maximum Ratings
    i_f_avg=30.0,  # From Absolute Maximum Ratings
    v_f0=0.8,  # From V_F curve fitting (V_F = V_F0 + R_F * I_F)
    r_f=0.015,  # From V_F curve fitting
    v_f_25c=1.5,  # From Electrical Characteristics at rated current
    v_f_125c=1.3,  # From Electrical Characteristics at 125°C
    t_rr=35e-9,  # From Electrical Characteristics (if available)
    q_rr=50e-9,  # From Electrical Characteristics (if available)
    c_j0=500e-12,  # From capacitance curve fitting
)
```

---

## Common Extraction Challenges

### 1. Unit Conversions
- **Resistance:** Convert mΩ to Ω (multiply by 1e-3)
- **Capacitance:** Convert pF to F (multiply by 1e-12), nF to F (multiply by 1e-9)
- **Charge:** Convert nC to C (multiply by 1e-9)
- **Time:** Convert ns to s (multiply by 1e-9)
- **Current:** Convert A to A (no change), mA to A (multiply by 1e-3)
- **Voltage:** Usually in V (no change)

### 2. Test Condition Variations
Different manufacturers use different test conditions:
- **Gate Voltage:** V_GS = 15V, 18V, or 20V for SiC MOSFETs
- **Drain Current:** R_DS(on) measured at different I_D levels
- **Capacitance Voltage:** C_oss measured at 400V, 600V, or 800V

**Solution:** Normalize to standard test conditions or store actual test conditions with parameter.

### 3. Missing Parameters
Not all datasheets list all parameters:
- **Estimate from graphs** if table value missing
- **Use typical industry values** as placeholders (mark as estimated)
- **Interpolate** from nearby temperature/voltage points

### 4. Manufacturer-Specific Terminology
| Infineon | Wolfspeed | Generic | Parameter |
|----------|-----------|---------|-----------|
| R_DS(on) | R_DS(on) | R_DS(on) | On-resistance |
| C_iss | C_iss | C_iss | Input capacitance |
| C_oss | C_oss | C_oss | Output capacitance |
| C_rss | C_rss | C_gd | Reverse transfer capacitance |
| V_SD | V_SD | V_F | Body diode forward voltage |

---

## Output Format

### Component Library Entry
```python
"PART_NUMBER": {
    "device": MOSFETParameters(...) or DiodeParameters(...),
    "metrics": ComponentMetrics(
        relative_cost=2.8,  # Manual or from pricing database
        availability="Standard",  # "Standard", "Limited", "EOL"
        package="TO-247-4",  # From datasheet
        manufacturer="Infineon",  # Extracted from PDF metadata
    ),
    "description": "Auto-generated from datasheet",
    "datasheet_url": "https://...",  # If available
    "extraction_date": "2025-11-15",
    "extraction_confidence": 0.95,  # 0-1 confidence score
}
```

### Comparison Report
Generate CSV/Excel comparison:
| Part Number | Manufacturer | V_DSS | I_D | R_DS(on) @ 25°C | R_DS(on) @ 150°C | Q_g | Cost | FOM (R_DS × Q_g) |
|-------------|--------------|-------|-----|-----------------|------------------|-----|------|------------------|
| IMZA65R020M2H | Infineon | 650V | 90A | 20mΩ | 28mΩ | 142nC | $$$ | 2840 |
| C3M0065090J | Wolfspeed | 650V | 108A | 25mΩ | 34mΩ | 156nC | $$ | 3900 |

**Figure of Merit (FOM):** Lower is better
- **R_DS(on) × Q_g:** For conduction + switching trade-off
- **R_DS(on) × A:** For cost-performance (A = die area estimate)

---

## Validation Checklist

After extraction, validate:
- [ ] All required parameters present (no missing critical values)
- [ ] Units converted correctly (check orders of magnitude)
- [ ] Parameter ranges sensible (R_DS(on) increases with temperature)
- [ ] Part number matches datasheet
- [ ] Test conditions documented
- [ ] Temperature coefficients correct (V_F decreases, R_DS increases with temp)
- [ ] Capacitances in expected range (C_iss > C_oss > C_rss for MOSFETs)
- [ ] Gate charge values consistent (Q_g > Q_gs + Q_gd)

---

## Usage Instructions

### Basic Extraction
```python
from psfb_loss_analyzer.Datasheet_analyzer import DatasheetParser

parser = DatasheetParser()

# Extract MOSFET parameters
mosfet_params = parser.extract_mosfet("path/to/datasheet.pdf")
print(mosfet_params)

# Extract diode parameters
diode_params = parser.extract_diode("path/to/datasheet.pdf")
print(diode_params)
```

### Batch Processing
```python
# Process directory of datasheets
results = parser.batch_process("datasheets/", device_type="mosfet")

# Export to component library format
parser.export_to_library(results, "component_library_new.py")
```

### Comparison
```python
# Compare multiple devices
comparison = parser.compare_devices([
    "datasheets/IMZA65R020M2H.pdf",
    "datasheets/C3M0065090J.pdf",
    "datasheets/SCT3030KL.pdf",
])
comparison.to_csv("comparison_report.csv")
```

---

## Advanced Features

### 1. Graph Digitization
Extract data from graphs:
```python
# Extract C_oss vs V_DS curve
c_oss_curve = parser.extract_graph(
    pdf_path="datasheet.pdf",
    graph_name="Output Capacitance",
    x_label="V_DS",
    y_label="C_oss",
)
```

### 2. Curve Fitting
Fit analytical models to extracted data:
```python
# Fit C_oss voltage dependence
fit_params = parser.fit_capacitance_model(c_oss_curve)
# Returns: CapacitanceVsVoltage dataclass
```

### 3. Confidence Scoring
Each extracted parameter has confidence score:
- **1.0:** Direct table extraction, clear value
- **0.8:** Interpolated from graph
- **0.5:** Estimated from similar devices
- **0.3:** Default/placeholder value

### 4. Manual Override
Review and manually correct extracted parameters:
```python
# Extract with manual review
params = parser.extract_mosfet("datasheet.pdf", review=True)
# Opens GUI for parameter verification/correction
```

---

## Dependencies

```bash
pip install pdfplumber PyPDF2 pytesseract pandas numpy scipy matplotlib opencv-python
```

**Optional for graph extraction:**
```bash
pip install digitize plotdigitizer
```

---

## Future Enhancements

1. **Machine Learning:** Train model to recognize parameter tables/graphs
2. **Multi-manufacturer support:** Handle more datasheet formats
3. **Thermal model extraction:** Extract Cauer/Foster thermal networks
4. **SPICE model generation:** Create SPICE subcircuits from extracted parameters
5. **Cost database integration:** Automatic pricing from Digi-Key/Mouser APIs
6. **Reliability data:** MTBF, FIT rates from qualification reports

---

## References

- Infineon Application Note AN2019-10: "MOSFET Power Losses Calculation"
- JEDEC JESD24-10: "Electrical Characteristics of SiC Power Devices"
- IEC 60747-9: "Semiconductor devices - Discrete devices - Part 9: Insulated-gate bipolar transistors (IGBTs)"
- Manufacturer datasheets: Infineon, Wolfspeed, Rohm, STMicroelectronics

---

**Version:** 1.0
**Last Updated:** 2025-11-15
**Author:** PSFB Loss Analyzer Development Team

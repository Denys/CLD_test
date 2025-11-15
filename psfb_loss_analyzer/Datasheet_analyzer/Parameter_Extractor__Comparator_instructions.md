# Project Prompt: Datasheet Parameter Extractor & Comparator

## Context
I'm a power electronics engineer who regularly evaluates 10-20+ MOSFETs/diodes per design iteration to find optimal components. Currently, manually extracting parameters from PDF datasheets (reading graphs, transcribing tables) takes 15-30 minutes per device. I need an automated tool that extracts key parameters from manufacturer PDFs, normalizes the data, and generates comparison matrices with Pareto frontier analysis for rapid component selection.

## Core Objectives
Build a Python-based tool that:

1. **Automated PDF Parameter Extraction**
   - Parse MOSFET/SiC MOSFET/diode datasheets from major vendors (Infineon, Wolfspeed, ON Semi, STMicro, Vishay, Rohm, TI)
   - Extract electrical parameters from:
     - Summary tables (text-based extraction)
     - Characteristic curves/graphs (image processing + OCR)
   - Handle multi-page documents with varying formats

2. **Database Construction**
   - Store extracted parameters in structured format (SQLite/CSV)
   - Version control for datasheet revisions
   - User-added custom parameters (e.g., distributor pricing, lead time)

3. **Normalized Comparison Engine**
   - Generate apples-to-apples comparison tables
   - Temperature normalization (e.g., R_DS(on) @ 25°C vs 150°C)
   - Figure-of-merit (FOM) calculations
   - Multi-criteria ranking

4. **Pareto Frontier Analysis**
   - Cost vs performance trade-off visualization
   - Identify dominated/non-dominated solutions
   - Interactive filtering by constraints

5. **Export & Reporting**
   - Excel/CSV comparison tables
   - Publication-ready plots
   - Component selection justification report

---

## Technical Requirements

### Phase 1: PDF Parameter Extraction

#### Target Parameters (MOSFETs/SiC MOSFETs)

**From Summary Tables:**
- Part number, package type, technology (Si/SiC)
- V_DSS (drain-source voltage rating)
- I_D (continuous drain current @ T_case)
- R_DS(on)_typ and R_DS(on)_max @ 25°C and @ 150°C (or 175°C for SiC)
- Q_g (total gate charge)
- Q_gd (gate-drain charge / Miller charge)
- Q_oss (output charge)
- C_iss, C_oss, C_rss (input/output/reverse transfer capacitance)
- V_GS(th) (gate threshold voltage)
- t_d(on), t_r, t_d(off), t_f (switching times)
- E_on, E_off (switching energies at test conditions)
- R_th(j-c) (thermal resistance junction-to-case)
- Price (if available in datasheet or from user input)

**From Graphs (Image Processing Required):**
- R_DS(on) vs T_j curve → extract temperature coefficient α
- R_DS(on) vs I_D curve → check current derating
- C_oss vs V_DS curve → extract capacitance vs voltage data points
- I_D vs V_DS output characteristics (optional for advanced FOM)
- Safe Operating Area (SOA) boundaries (optional)

**From Diode/Body Diode Section:**
- V_F (forward voltage drop)
- Q_rr (reverse recovery charge)
- t_rr (reverse recovery time)
- I_rrm (peak reverse recovery current)

#### Extraction Strategy

**Text-Based Extraction (Summary Tables):**
```python
import pdfplumber
import re

def extract_mosfet_summary(pdf_path):
    """
    Parse tabular data from first 2-3 pages
    Pattern matching for:
    - "V_DSS" or "Drain-Source Voltage" → value + unit
    - "R_DS(on)" variations → typ/max @ temperature
    - "Q_g" or "Total Gate Charge" → value @ V_GS
    """
    with pdfplumber.open(pdf_path) as pdf:
        tables = pdf.pages[0].extract_tables()
        # Regex patterns for parameter names and units
        # Handle vendor-specific formatting differences
```

**Graph-Based Extraction (Curves):**
```python
import cv2
import matplotlib.pyplot as plt
from PIL import Image
import pytesseract

def extract_rdson_vs_temp_curve(pdf_path, page_num):
    """
    1. Convert PDF page to image
    2. Locate graph region (axis labels "R_DS(on)", "T_j [°C]")
    3. Detect axis scales using OCR
    4. Trace curve using edge detection / color segmentation
    5. Convert pixel coordinates to engineering units
    6. Fit polynomial: R_DS(on)(T) = a + b*T + c*T^2
    """
    # Use pdf2image to rasterize
    # OpenCV for graph region detection
    # Curve tracing algorithm (threshold → contour → interpolation)
```

**Challenges & Solutions:**

| Challenge | Solution |
|-----------|----------|
| Multi-vendor format variations | Template library per manufacturer + fallback heuristics |
| Graph axis auto-scaling | OCR tick labels → infer scale mapping |
| Logarithmic scales (C_oss vs V_DS) | Detect log scale via tick spacing → apply log transform |
| Overlapping curves in one plot | Color-based segmentation (e.g., "typ" = blue, "max" = red) |
| Poor scan quality | Image preprocessing (denoise, contrast enhancement) |

#### Extraction Workflow
```
User Input: PDF file(s) or directory
    ↓
PDF Analysis:
  - Vendor detection (text search for "Infineon", "Wolfspeed", etc.)
  - Table-of-contents parsing (find "Electrical Characteristics" page)
    ↓
Parameter Extraction:
  - Text tables → dict of parameters
  - Graph pages → curve data arrays
    ↓
Validation:
  - Sanity checks (e.g., R_DS(on)_max > R_DS(on)_typ)
  - Flag missing critical parameters
    ↓
Database Storage:
  - SQLite row: [part_number, V_DSS, R_DS(on)_typ_25C, ..., extraction_date]
```

---

### Phase 2: Database Schema & Management

**Database Structure (SQLite):**

```sql
CREATE TABLE mosfets (
    id INTEGER PRIMARY KEY,
    part_number TEXT UNIQUE NOT NULL,
    manufacturer TEXT,
    technology TEXT,  -- 'Si', 'SiC', 'GaN'
    package TEXT,
    
    -- Ratings
    v_dss_V REAL,
    i_d_A REAL,  -- @ 25°C
    i_d_pulse_A REAL,
    
    -- On-State
    rdson_typ_25C_mohm REAL,
    rdson_max_25C_mohm REAL,
    rdson_typ_150C_mohm REAL,
    rdson_max_150C_mohm REAL,
    rdson_temp_coeff_alpha REAL,  -- fitted from curve
    
    -- Gate Charge
    qg_total_nC REAL,
    qgd_miller_nC REAL,
    qoss_nC REAL,
    vgs_test_V REAL,  -- test condition for Q_g
    
    -- Capacitances
    ciss_pF REAL,
    coss_pF REAL,
    crss_pF REAL,
    coss_test_voltage_V REAL,
    
    -- Switching (at test condition)
    eon_uJ REAL,
    eoff_uJ REAL,
    switching_test_vds_V REAL,
    switching_test_id_A REAL,
    switching_test_rg_ohm REAL,
    
    -- Thermal
    rth_jc_K_per_W REAL,
    rth_ja_K_per_W REAL,  -- if available
    
    -- Body Diode
    vf_typ_V REAL,
    qrr_nC REAL,
    trr_ns REAL,
    
    -- Commercial
    price_USD REAL,  -- user-entered or scraped
    lead_time_weeks INTEGER,
    
    -- Metadata
    datasheet_path TEXT,
    extraction_date DATE,
    verified BOOLEAN DEFAULT 0  -- manual verification flag
);

CREATE TABLE curve_data (
    id INTEGER PRIMARY KEY,
    mosfet_id INTEGER,
    curve_type TEXT,  -- 'rdson_vs_temp', 'coss_vs_vds', etc.
    x_values TEXT,  -- JSON array
    y_values TEXT,  -- JSON array
    FOREIGN KEY(mosfet_id) REFERENCES mosfets(id)
);
```

**Management Functions:**
```python
def add_component(params_dict):
    """Insert extracted parameters with duplicate checking"""

def update_pricing(part_number, price, lead_time):
    """User update for commercial data"""

def export_database_to_csv():
    """Backup/sharing functionality"""

def import_user_library(csv_path):
    """Bulk import from existing spreadsheet"""
```

---

### Phase 3: Comparison & Analysis Engine

#### Normalized Comparison Table Generation

**Key Normalizations:**

1. **R_DS(on) Temperature Adjustment:**
   - Normalize all to 150°C (or user-specified T_j):
   ```python
   rdson_150C = rdson_25C * (1 + alpha/100 * (150 - 25))
   ```

2. **Current Rating Normalization:**
   - Some datasheets specify I_D @ 25°C, others @ 100°C
   - Normalize to same T_case using thermal resistance

3. **Gate Charge Test Conditions:**
   - Q_g measured at different V_GS (e.g., 10V vs 15V)
   - Approximate scaling: Q_g ∝ V_GS (crude but useful)

4. **Switching Energy Scaling:**
   - Test conditions vary (V_DS, I_D, R_G)
   - Scale to user's operating point:
   ```python
   E_on_scaled = E_on_datasheet * (V_op / V_test) * (I_op / I_test)
   ```

#### Figure-of-Merit (FOM) Calculations

**Standard FOMs:**
```python
FOM_1 = R_DS(on) * Q_g  # Conduction vs switching trade-off (lower is better)
FOM_2 = R_DS(on) * Q_gd  # Miller charge impact
FOM_3 = R_DS(on) * C_oss  # Output capacitance losses
FOM_4 = R_DS(on) * Q_oss  # COSS-related losses (relevant for ZVS)
```

**Application-Specific FOM (User-Defined):**
```python
def calculate_total_loss_fom(component, circuit_params):
    """
    Estimate losses for user's application:
    P_total = P_cond + P_sw + P_gate_drive
    
    circuit_params = {
        'I_rms': 20,  # A
        'V_bus': 400,  # V
        'f_sw': 100e3,  # Hz
        'duty': 0.5
    }
    """
    p_cond = component.rdson_150C * circuit_params['I_rms']**2
    p_sw = (component.eon + component.eoff) * circuit_params['f_sw']
    p_gate = component.qg * circuit_params['V_gs'] * circuit_params['f_sw']
    
    return p_cond + p_sw + p_gate  # Watts
```

#### Comparison Table Output

**Example: Top 10 MOSFETs for 650V, 30A RMS Application**

| Rank | Part Number | V_DSS | R_DS(on)@150°C | Q_g | FOM₁ | E_on+E_off | Price | Total Loss* | Cost/W |
|------|-------------|-------|----------------|-----|------|------------|-------|-------------|--------|
| 1 | C3M0120090D (SiC) | 900V | 120mΩ | 18nC | 2.16 | 85µJ | $4.50 | 12.3W | $0.37 |
| 2 | IPW65R045C7 (Si) | 650V | 65mΩ | 42nC | 2.73 | 145µJ | $2.10 | 18.5W | $0.11 |
| 3 | SCT3120AL (SiC) | 650V | 120mΩ | 25nC | 3.00 | 95µJ | $3.80 | 14.1W | $0.27 |
| ... |

*Calculated @ I_rms=30A, V_bus=400V, f_sw=100kHz, D=0.5

**Filtering Options:**
- Voltage class (650V ±10%)
- Current rating (≥ 30A @ 100°C)
- Package type (TO-247, TO-220, D2PAK)
- Technology (Si only, SiC only, both)
- Price range ($0-$5)
- Availability (in-stock only)

---

### Phase 4: Pareto Frontier Analysis

#### Multi-Objective Optimization

**Objective Axes (user-selectable):**
- **X-axis options:** Price, R_DS(on), Die Area, Package Size
- **Y-axis options:** FOM, Total Loss, Efficiency, Q_g

**Example: Cost vs Performance Pareto**
```
      Total Loss (W)
        ^
     20 |     ●  Si MOSFETs (dominated region)
        |   ●   ●
     15 |  ●  ● ●
        | ● ●●
     10 | ●●───────○ SiC MOSFETs (Pareto frontier)
        |○────○──○
      5 |──○──○
        |○
        └──────────────────────> Price ($)
         0   2   4   6   8
         
Legend:
● = Dominated solution (worse on both axes)
○ = Pareto-optimal (no other part is better on BOTH axes)
```

**Algorithm:**
```python
def compute_pareto_frontier(components, x_metric, y_metric, minimize_both=True):
    """
    For each component, check if any other component dominates it
    (i.e., better on both metrics)
    
    Returns: List of non-dominated components
    """
    pareto_set = []
    for candidate in components:
        dominated = False
        for other in components:
            if minimize_both:
                if (other[x_metric] < candidate[x_metric] and 
                    other[y_metric] < candidate[y_metric]):
                    dominated = True
                    break
        if not dominated:
            pareto_set.append(candidate)
    return pareto_set
```

**Interactive Plot Features:**
- Hover tooltips showing part number + key specs
- Click to highlight component and show full datasheet
- Region selection (e.g., "find all parts in $2-4, <15W loss zone")
- Color-code by manufacturer or technology

---

### Phase 5: Reporting & Export

#### Auto-Generated Selection Report

**Markdown/PDF Report Structure:**
```markdown
# MOSFET Selection Report
**Project:** 3kW PSFB Converter  
**Date:** 2025-01-15  
**Engineer:** Denys

## Design Requirements
- Voltage Rating: 650V (80% derating → ≥813V)
- Current Rating: 30A RMS @ 100°C
- Switching Frequency: 100kHz
- Target Efficiency: >95%

## Analysis Summary
- Datasheets analyzed: 47
- Candidates meeting voltage/current: 28
- Pareto-optimal solutions: 8

## Top 3 Recommendations

### 1. Wolfspeed C3M0120090D (SiC)
**Rationale:** Lowest total loss (12.3W) despite higher cost. Thermal margin excellent (T_j=98°C @ T_amb=50°C).

| Parameter | Value | Normalized |
|-----------|-------|------------|
| R_DS(on) @ 150°C | 120mΩ | - |
| Total Loss | 12.3W | Best |
| Price | $4.50 | 2.1× vs Si |
| Efficiency Impact | +0.8% | vs option 2 |

**Trade-offs:**
- ✓ 35% loss reduction vs best Si MOSFET
- ✓ Smaller heatsink possible
- ✗ 2× cost premium
- ✗ Longer lead time (12 weeks)

### 2. Infineon IPW65R045C7 (Si Superjunction)
...

## Pareto Frontier Plot
![pareto_plot.png]

## Sensitivity Analysis
- If cost <$3 required → Infineon IPW65R045C7
- If efficiency >96% required → SiC mandatory (C3M0120090D or SCT3120AL)
- If T_amb >70°C → C3M0120090D (wider thermal margin)
```

#### Export Formats

**Excel Workbook:**
- Sheet 1: Comparison table (sortable/filterable)
- Sheet 2: Pareto frontier data
- Sheet 3: Raw extracted parameters
- Sheet 4: Curve data (R_DS(on) vs T, C_oss vs V_DS)

**CSV for Tool Integration:**
- Direct import into LTspice (SPICE parameters)
- MATLAB/Python scripts for loss calculations

---

## Implementation Strategy

### Tech Stack
- **PDF Processing:** `pdfplumber` (text), `pdf2image` + `opencv-python` (graphs)
- **OCR:** `pytesseract` (Tesseract engine)
- **Database:** `sqlite3` (built-in Python)
- **Data Analysis:** `pandas`, `numpy`, `scipy`
- **Visualization:** `matplotlib`, `plotly` (interactive plots)
- **Reporting:** `markdown` → `pandoc` (PDF conversion)

### Project Structure
```
datasheet_comparator/
├── main.py                      # CLI interface
├── config.yaml                  # Extraction templates per vendor
├── extractors/
│   ├── text_extractor.py       # Table parsing
│   ├── curve_extractor.py      # Graph digitization
│   ├── vendor_templates/       # Manufacturer-specific patterns
│   │   ├── infineon.py
│   │   ├── wolfspeed.py
│   │   └── onsemi.py
├── database/
│   ├── db_manager.py           # SQLite CRUD operations
│   ├── schema.sql
│   └── mosfet_library.db
├── analysis/
│   ├── normalizer.py           # Temperature/condition scaling
│   ├── fom_calculator.py       # Figure-of-merit engines
│   ├── pareto_optimizer.py     # Multi-objective optimization
│   └── loss_estimator.py       # Application-specific loss calc
├── visualization/
│   ├── comparison_tables.py    # Pandas DataFrames → Excel
│   ├── pareto_plotter.py       # Interactive Plotly charts
│   └── report_generator.py     # Markdown → PDF
├── tests/
│   ├── test_extraction.py      # Validate against known datasheets
│   └── sample_datasheets/      # Test PDFs
├── requirements.txt
└── README.md
```

### Development Phases

**Phase 1 (MVP - Week 1):**
- Text-based extraction for 3 vendors (Infineon, Wolfspeed, ON Semi)
- SQLite database with core parameters
- Basic comparison table (no graph extraction yet)

**Phase 2 (Week 2):**
- Curve extraction for R_DS(on) vs T_j
- FOM calculations
- Excel export

**Phase 3 (Week 3):**
- Pareto frontier visualization
- Interactive Plotly charts
- Report generation

**Phase 4 (Polish):**
- Expand to 10+ vendors
- C_oss vs V_DS curve extraction
- Batch processing mode
- GUI (optional: Streamlit web interface)

---

## Validation & Testing

### Test Cases

**Known-Good Datasheets:**
1. Infineon IPW65R045C7 → Verify R_DS(on)_max = 45mΩ @ 25°C
2. Wolfspeed C3M0120090D → Check Q_g = 18nC @ V_GS=15V
3. ON Semi NVHL080N65S3 → Confirm E_on+E_off = 620µJ @ test conditions

**Extraction Accuracy Targets:**
- Text tables: 98% correct (allow 2% OCR errors)
- Graph curves: ±5% vs manual reading

**Comparison Validation:**
- Cross-check FOM rankings against published literature
- Verify Pareto frontier matches manual analysis

---

## User Workflow Example

### Scenario: Selecting MOSFET for 3kW PSFB Primary Side

```bash
# 1. Extract datasheets from folder
$ python main.py extract --input datasheets/650V_class/ --vendor auto

Processing: IPW65R045C7.pdf... ✓ (28 parameters extracted)
Processing: C3M0120090D.pdf... ✓ (32 parameters extracted)
...
Total: 47 datasheets processed, 45 successful

# 2. Define application constraints
$ python main.py analyze --voltage 650 --current 30 --freq 100e3

Filtering database... 28 candidates found

# 3. Generate comparison
$ python main.py compare \
    --metrics rdson_150C,qg,eon,eoff,price \
    --sort-by total_loss \
    --output comparison.xlsx

Comparison table saved: comparison.xlsx
Top recommendation: C3M0120090D (lowest loss: 12.3W)

# 4. Pareto frontier
$ python main.py pareto \
    --x-axis price \
    --y-axis total_loss \
    --interactive

Launching interactive plot... (browser opens)
8 Pareto-optimal solutions identified

# 5. Generate report
$ python main.py report \
    --template ieee_paper \
    --output mosfet_selection_report.pdf

Report generated: mosfet_selection_report.pdf (6 pages)
```

---

## Advanced Features (Future Enhancements)

1. **Web Scraping Integration:**
   - Auto-download datasheets from Digi-Key/Mouser APIs
   - Real-time pricing updates

2. **Machine Learning:**
   - Train classifier to auto-detect graph types
   - Predict missing parameters (e.g., E_on from Q_g + C_oss)

3. **SPICE Model Generation:**
   - Auto-create LTspice subcircuits from extracted parameters

4. **Thermal Simulation:**
   - Integrate with heatsink databases
   - 3D thermal FEA preview (OpenFOAM wrapper)

5. **Collaborative Database:**
   - Cloud-hosted DB for team sharing
   - User-contributed verification flags

---

## Success Metrics

- **Time Savings:** Component selection in 5 minutes (vs 2 hours manual)
- **Accuracy:** 95% extraction accuracy on validation set
- **Coverage:** Support 10+ manufacturers, 500+ components
- **Adoption:** Generate 20+ comparison reports in first month

---

## Constraints & Assumptions

- **Legal:** Respect copyright—extracted data for internal use only, no redistribution
- **Accuracy:** Graph extraction is approximate (±5%), suitable for screening not final verification
- **Scope:** Focus on power MOSFETs/SiC MOSFETs, diodes (not IGBTs, GaN yet)

---

## Deliverables

1. **Software Package:** Installable Python tool with CLI + optional GUI
2. **Sample Database:** Pre-populated with 50+ common parts
3. **User Guide:** Tutorial with example workflows
4. **Validation Report:** Benchmarking against manual extraction

---

1. start by building the **PDF text extraction module** with templates for Infineon/Wolfspeed, 
2. the **Pareto frontier visualization engine** 
# Datasheet Analyzer - Automatic Parameter Extraction

Automatic extraction of electrical parameters from SiC MOSFET and Schottky diode datasheets (PDF format).

## Features

- **Automatic PDF parsing** - Extract text and tables from datasheets
- **Intelligent parameter detection** - Pattern matching for common parameters
- **Unit conversion** - Automatic normalization to SI units
- **Batch processing** - Process multiple datasheets at once
- **Comparison reports** - Generate CSV comparisons of multiple devices
- **Component library generation** - Export to PSFB Loss Analyzer format
- **Confidence scoring** - Track extraction quality

## Installation

### Required Dependencies

```bash
pip install pdfplumber PyPDF2 pandas
```

### Optional Dependencies

```bash
# For OCR support (scanned PDFs)
pip install pytesseract

# For graph digitization
pip install opencv-python
```

## Quick Start

### 1. Parse Single Datasheet

```python
from psfb_loss_analyzer.Datasheet_analyzer import DatasheetParser

# Create parser
parser = DatasheetParser()

# Parse datasheet
result = parser.parse_datasheet("IMZA65R020M2H.pdf")

# Print report
parser.print_extraction_report(result)

# Convert to MOSFETParameters
mosfet = parser.to_mosfet_parameters(result)
print(f"R_DS(on): {mosfet.r_dson_25c * 1000:.1f}mΩ")
```

### 2. Batch Process Multiple Datasheets

```python
from psfb_loss_analyzer.Datasheet_analyzer import BatchProcessor

# Create batch processor
processor = BatchProcessor()

# Process all PDFs in directory
results = processor.process_directory("datasheets/")

# Create comparison report
report = processor.create_comparison(results)
report.print_summary()

# Export to CSV
report.to_csv("component_comparison.csv")

# Export to component library
processor.export_to_library(results, "extracted_components.py")
```

### 3. Table Extraction

```python
from psfb_loss_analyzer.Datasheet_analyzer import TableExtractor

# Create extractor
extractor = TableExtractor()

# Extract tables
tables = extractor.extract_tables_from_pdf("datasheet.pdf", device_type="mosfet")

# Find specific parameters
params = extractor.extract_mosfet_parameters_from_tables(tables)
```

## Usage Examples

### Command Line Usage

#### Single Datasheet
```bash
python datasheet_parser.py path/to/datasheet.pdf
```

#### Batch Processing
```bash
python batch_processor.py datasheets/ mosfet
```

#### Table Extraction
```bash
python table_extractor.py path/to/datasheet.pdf mosfet
```

### Python API Usage

See `examples/` directory for complete examples:
- `example_parse_single_datasheet.py` - Single datasheet extraction
- `example_batch_comparison.py` - Batch processing and comparison

## Supported Devices

### SiC MOSFETs
- **Manufacturers:** Infineon (CoolSiC), Wolfspeed (C3M/C2M), Rohm, STMicroelectronics, OnSemi
- **Voltage Classes:** 650V, 900V, 1200V, 1700V
- **Parameters Extracted:**
  - V_DSS (Drain-Source Voltage)
  - I_D (Continuous Drain Current)
  - R_DS(on) @ 25°C and 150°C
  - Gate charge (Q_g, Q_gs, Q_gd)
  - Capacitances (C_iss, C_oss, C_rss)
  - Switching times (t_r, t_f)
  - Thermal resistance

### SiC Schottky Diodes
- **Manufacturers:** Wolfspeed, Infineon, STMicroelectronics, Rohm, OnSemi
- **Voltage Classes:** 600V, 650V, 1200V, 1700V
- **Parameters Extracted:**
  - V_RRM (Repetitive Peak Reverse Voltage)
  - I_F (Average Forward Current)
  - V_F @ various temperatures
  - Reverse recovery (t_rr, Q_rr)
  - Junction capacitance (C_j)
  - Thermal resistance

## Extracted Parameters

### MOSFETs

| Parameter | Symbol | Unit | Source |
|-----------|--------|------|--------|
| Drain-Source Voltage | V_DSS | V | Table |
| Continuous Drain Current | I_D | A | Table |
| On-Resistance @ 25°C | R_DS(on) | Ω | Table |
| On-Resistance @ 150°C | R_DS(on) | Ω | Table |
| Gate Threshold Voltage | V_GS(th) | V | Table |
| Input Capacitance | C_iss | F | Table/Graph |
| Output Capacitance | C_oss | F | Table/Graph |
| Reverse Transfer Cap. | C_rss | F | Table/Graph |
| Total Gate Charge | Q_g | C | Table/Graph |
| Gate-Source Charge | Q_gs | C | Graph |
| Gate-Drain Charge | Q_gd | C | Graph |
| Gate Plateau Voltage | V_GS(plateau) | V | Graph |
| Rise Time | t_r | s | Table |
| Fall Time | t_f | s | Table |

### Diodes

| Parameter | Symbol | Unit | Source |
|-----------|--------|------|--------|
| Peak Reverse Voltage | V_RRM | V | Table |
| Average Forward Current | I_F | A | Table |
| Forward Voltage @ 25°C | V_F | V | Table |
| Forward Voltage @ 125°C | V_F | V | Table |
| Reverse Leakage Current | I_R | A | Table |
| Reverse Recovery Time | t_rr | s | Table |
| Reverse Recovery Charge | Q_rr | C | Table |
| Junction Capacitance | C_j | F | Table/Graph |

## Parameter Extraction Confidence

Each extracted parameter has a confidence score:

- **HIGH (1.0):** Direct table extraction, clear value
- **MEDIUM (0.7):** Interpolated from graph or calculated
- **LOW (0.4):** Estimated from similar devices
- **PLACEHOLDER (0.1):** Default value, manual review required

## Output Formats

### 1. Extraction Report (Console)
```
================================================================================
DATASHEET EXTRACTION REPORT
================================================================================
Device Type:    SiC MOSFET
Part Number:    IMZA65R020M2H
Manufacturer:   Infineon
Confidence:     75%

EXTRACTED PARAMETERS:
--------------------------------------------------------------------------------
Parameter            Value           Unit       Confidence   Source
--------------------------------------------------------------------------------
v_dss                6.500e+02       V          100%         table
i_d_continuous       9.000e+01       A          100%         table
r_dson_25c           2.000e-02       Ω          70%          table
```

### 2. Component Library (Python)
```python
"IMZA65R020M2H": {
    "device": MOSFETParameters(
        part_number="IMZA65R020M2H",
        v_dss=650.0,
        i_d_continuous=90.0,
        r_dson_25c=0.020,
        r_dson_25c_max=0.028,
        ...
    ),
    "metrics": ComponentMetrics(
        manufacturer="Infineon",
        package="TO-247-4",
    ),
    "extraction_confidence": 0.75,
}
```

### 3. Comparison Report (CSV)
```csv
Part Number,Manufacturer,Type,V_DSS,I_D,R_DS(on) @ 25°C,Q_g,FOM
IMZA65R020M2H,Infineon,SiC MOSFET,650,90,0.020,142e-9,2.84e-6
C3M0065090J,Wolfspeed,SiC MOSFET,650,108,0.025,156e-9,3.90e-6
```

## Limitations and Known Issues

### Current Limitations

1. **Graph Data Extraction:** Currently limited
   - Gate charge curves (Q_g vs V_GS) require manual extraction
   - Capacitance vs voltage curves not fully automated
   - **Workaround:** Manually enter graph-based parameters

2. **Test Conditions:** Not always captured
   - Different manufacturers use different test conditions
   - **Workaround:** Review datasheet for test conditions

3. **Scanned PDFs:** Limited OCR support
   - Best results with text-based PDFs
   - **Workaround:** Use pdfplumber with OCR fallback

4. **Table Format Variations:** Different manufacturers use different formats
   - May miss parameters in non-standard layouts
   - **Workaround:** Manual review of low-confidence extractions

### Planned Enhancements

- [ ] Graph digitization and curve fitting
- [ ] Machine learning for improved parameter detection
- [ ] SPICE model generation
- [ ] Cost database integration (Digi-Key, Mouser APIs)
- [ ] Interactive GUI for manual review
- [ ] Support for IGBTs and other power semiconductors

## Validation and Manual Review

**IMPORTANT:** Always manually review extracted parameters before using in production designs!

### Validation Checklist

- [ ] Part number correct
- [ ] Voltage/current ratings match datasheet
- [ ] R_DS(on) values reasonable (increases with temperature)
- [ ] V_F values reasonable (decreases with temperature for SiC Schottky)
- [ ] Gate charge values present (not default 0.0)
- [ ] Units converted correctly
- [ ] Test conditions documented

### Common Issues to Check

1. **Missing Gate Charge:** Requires manual extraction from graph
2. **Wrong Test Conditions:** Check V_GS for R_DS(on) measurement
3. **Unit Conversion Errors:** Verify mΩ → Ω, nC → C, etc.
4. **Temperature Coefficients:** R_DS(on) should increase ~40% from 25°C to 150°C

## Integration with PSFB Loss Analyzer

Extracted components can be directly integrated:

```python
# After extraction
from extracted_components import MOSFET_LIBRARY_EXTRACTED

# Add to main library
from psfb_loss_analyzer.component_library import MOSFET_LIBRARY_SIC
MOSFET_LIBRARY_SIC.update(MOSFET_LIBRARY_EXTRACTED)

# Use in optimizer
from psfb_loss_analyzer import optimize_design, DesignSpecification
spec = DesignSpecification(...)
result = optimize_design(spec)
```

## File Structure

```
Datasheet_analyzer/
├── __init__.py                          # Module initialization
├── README.md                            # This file
├── Parameter_Extractor__Comparator_instructions.md  # Detailed instructions
├── datasheet_parser.py                  # Core PDF parser
├── table_extractor.py                   # Advanced table extraction
├── batch_processor.py                   # Batch processing and comparison
└── examples/
    ├── example_parse_single_datasheet.py
    └── example_batch_comparison.py
```

## Contributing

To add support for additional manufacturers or parameters:

1. Add pattern matching in `ParameterPatterns` class
2. Update extraction methods in `DatasheetParser`
3. Add test datasheets to validation suite
4. Document manufacturer-specific quirks

## References

- **Infineon Application Note AN2019-10:** "MOSFET Power Losses Calculation"
- **JEDEC JESD24-10:** "Electrical Characteristics of SiC Power Devices"
- **pdfplumber documentation:** https://github.com/jsvine/pdfplumber
- **PSFB Loss Analyzer:** https://github.com/your-repo/psfb_loss_analyzer

## License

Part of PSFB Loss Analyzer project.

## Version History

- **1.0.0 (2025-11-15):** Initial release
  - Basic PDF text extraction
  - MOSFET and diode parameter extraction
  - Batch processing
  - CSV export
  - Component library generation

---

**Author:** PSFB Loss Analysis Tool
**Version:** 1.0.0
**Last Updated:** 2025-11-15

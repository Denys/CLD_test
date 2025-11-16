# PSFB Loss Analyzer - Comprehensive Testing Guide

Complete testing guide with detailed test scripts for all components.

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Test Suite Organization](#test-suite-organization)
3. [Running Tests](#running-tests)
4. [Component Testing](#component-testing)
5. [Integration Testing](#integration-testing)
6. [Performance Testing](#performance-testing)
7. [Validation Against Reference Data](#validation-against-reference-data)
8. [Debugging Failed Tests](#debugging-failed-tests)

---

## Testing Overview

### Test Levels

The PSFB Loss Analyzer uses a multi-level testing approach:

```
Level 1: Unit Tests
├── Circuit Parameters (MOSFETParameters, DiodeParameters, etc.)
├── Loss Calculations (MOSFET, Diode)
├── Magnetic Design (Inductor, Transformer)
└── Utility Functions

Level 2: Component Tests
├── Resonant Inductor Design
├── Transformer Design
├── Output Inductor Design
├── System Analyzer
├── Efficiency Mapper
└── Datasheet Parser

Level 3: Integration Tests
├── Complete System Analysis
├── Multi-Phase Interleaving
├── Optimizer End-to-End
└── Example Scripts

Level 4: Validation Tests
├── Compare vs Manufacturer Tools
├── Compare vs Published Designs
├── Compare vs Experimental Data
└── Parameter Sweeps
```

### Test Categories

- **✓ Unit Tests:** Test individual functions/classes
- **✓ Component Tests:** Test complete modules
- **✓ Integration Tests:** Test module interactions
- **✓ Validation Tests:** Verify against known results
- **✓ Performance Tests:** Check execution time
- **✓ Regression Tests:** Ensure no breaking changes

---

## Test Suite Organization

### Directory Structure

```
CLD_test/
├── tests/
│   ├── test_suite.py                    # Main test runner
│   ├── unit/
│   │   ├── test_circuit_params.py       # Circuit parameter tests
│   │   ├── test_mosfet_loss.py          # MOSFET loss calculation tests
│   │   ├── test_diode_loss.py           # Diode loss calculation tests
│   │   ├── test_resonant_inductor.py    # Resonant inductor tests
│   │   ├── test_transformer.py          # Transformer design tests
│   │   ├── test_output_inductor.py      # Output inductor tests
│   │   ├── test_system_analyzer.py      # System analyzer tests
│   │   ├── test_efficiency_mapper.py    # Efficiency mapper tests
│   │   ├── test_optimizer.py            # Optimizer tests
│   │   └── test_datasheet_parser.py     # Datasheet parser tests
│   ├── integration/
│   │   ├── test_complete_analysis.py    # Full system tests
│   │   ├── test_multiphase.py           # Multi-phase tests
│   │   └── test_examples.py             # Example script tests
│   ├── validation/
│   │   ├── test_vs_infineon.py          # Compare vs Infineon AN
│   │   ├── test_vs_experimental.py      # Compare vs lab data
│   │   └── reference_data/              # Reference datasets
│   └── performance/
│       └── test_performance.py          # Performance benchmarks
├── test_installation.py                 # Installation verification
└── TESTING.md                           # This file
```

---

## Running Tests

### Quick Test (Installation Verification)

```bash
# Activate virtual environment
source venv/bin/activate

# Run installation verification
python test_installation.py
```

### Full Test Suite

```bash
# Run all tests
python tests/test_suite.py

# Run with verbose output
python tests/test_suite.py -v

# Run specific test category
python tests/test_suite.py --unit         # Unit tests only
python tests/test_suite.py --integration  # Integration tests only
python tests/test_suite.py --validation   # Validation tests only
```

### Individual Component Tests

```bash
# Test MOSFET loss calculations
python tests/unit/test_mosfet_loss.py

# Test transformer design
python tests/unit/test_transformer.py

# Test optimizer
python tests/unit/test_optimizer.py
```

### Using pytest (if installed)

```bash
# Install pytest
pip install pytest pytest-cov

# Run all tests
pytest tests/

# Run with coverage report
pytest --cov=psfb_loss_analyzer tests/

# Run specific test file
pytest tests/unit/test_mosfet_loss.py

# Run specific test function
pytest tests/unit/test_mosfet_loss.py::test_conduction_loss

# Run with verbose output
pytest -v tests/
```

---

## Component Testing

### Test 1: Circuit Parameters

**File:** `tests/unit/test_circuit_params.py`

**What it tests:**
- MOSFETParameters creation and validation
- DiodeParameters creation and validation
- CapacitanceVsVoltage models
- CoreGeometry calculations
- Parameter ranges and units

**Expected results:**
- All parameters correctly initialized
- Capacitance calculations match expected values
- Core geometry properties computed correctly

**Run:**
```bash
python tests/unit/test_circuit_params.py
```

**Expected output:**
```
================================================================================
TEST: Circuit Parameters
================================================================================
✓ MOSFETParameters creation
✓ DiodeParameters creation
✓ CapacitanceVsVoltage @ 400V
✓ CoreGeometry calculations
✓ All tests passed!
```

### Test 2: MOSFET Loss Calculations

**File:** `tests/unit/test_mosfet_loss.py`

**What it tests:**
- Conduction loss calculation
- Switching loss (turn-on, turn-off)
- Gate drive loss
- Output capacitance loss (C_oss)
- Reverse recovery loss
- Total loss aggregation

**Test cases:**
1. **Conduction loss** - Verify I²R calculation with R_DS(on)
2. **Switching loss** - Verify energy calculation and frequency scaling
3. **Gate drive loss** - Verify Q_g × V_gs × f calculation
4. **Temperature scaling** - Verify R_DS(on) increases with temperature

**Run:**
```bash
python tests/unit/test_mosfet_loss.py
```

**Expected results:**
- Conduction loss: ~10-50W (depends on current and R_DS(on))
- Switching loss: ~5-30W @ 100kHz
- Gate drive loss: ~0.1-1W
- Total loss within expected range

### Test 3: Diode Loss Calculations

**File:** `tests/unit/test_diode_loss.py`

**What it tests:**
- Forward conduction loss (V_F × I_avg)
- Reverse recovery loss (Q_rr × V_R × f)
- Temperature dependence
- Comparison: SiC Schottky vs Si PN

**Test cases:**
1. **SiC Schottky** - Low V_F, minimal Q_rr
2. **Si PN diode** - Higher V_F, significant Q_rr
3. **Temperature scaling** - V_F decreases with temperature for SiC

**Run:**
```bash
python tests/unit/test_diode_loss.py
```

**Expected results:**
- SiC Schottky: Lower total losses (~5-15W)
- Si PN: Higher switching losses due to Q_rr
- Temperature coefficient: -2mV/°C for SiC

### Test 4: Resonant Inductor Design

**File:** `tests/unit/test_resonant_inductor.py`

**What it tests:**
- ZVS requirements calculation
- Inductor design (turns, wire size, core)
- Energy storage verification
- Losses (core + winding)

**Test cases:**
1. **650V MOSFET** - Design for typical C_oss
2. **Different power levels** - Scale design appropriately
3. **Frequency variation** - Verify design at 50kHz, 100kHz, 150kHz

**Run:**
```bash
python tests/unit/test_resonant_inductor.py
```

**Expected results:**
- Inductance: 5-50µH (typical range)
- Energy stored > ZVS requirement
- Core losses < 2W
- Total losses < 5W

### Test 5: Transformer Design

**File:** `tests/unit/test_transformer.py`

**What it tests:**
- Turns ratio calculation
- Core selection (Kg method)
- Primary and secondary winding design
- Flux density verification
- Thermal performance

**Test cases:**
1. **3kW, 400V→48V** - Standard telecom design
2. **6.6kW, 400V→48V** - High power design
3. **Different frequencies** - 50kHz vs 150kHz

**Run:**
```bash
python tests/unit/test_transformer.py
```

**Expected results:**
- Turns ratio: ~8:1 for 400V→48V
- Flux density: 200-300mT (SiC applications)
- Core losses: < 5W @ 100kHz
- Window utilization: 30-50%

### Test 6: Output Inductor Design

**File:** `tests/unit/test_output_inductor.py`

**What it tests:**
- Inductance calculation for ripple
- Core selection with air gap
- Winding design with DC bias
- Losses (core + copper + air gap)

**Test cases:**
1. **Single phase** - 48V, 60A output
2. **Multi-phase** - Interleaved ripple cancellation
3. **Ripple requirements** - 10%, 20%, 30% ripple

**Run:**
```bash
python tests/unit/test_output_inductor.py
```

**Expected results:**
- Inductance: 5-20µH typical
- Ripple current: Within specified limit
- Core losses: < 3W
- Total losses: < 5W

### Test 7: System Analyzer

**File:** `tests/unit/test_system_analyzer.py`

**What it tests:**
- Complete system loss integration
- Multi-phase analysis
- Capacitor ESR losses
- Ripple cancellation
- Efficiency calculation

**Test cases:**
1. **Single phase PSFB** - 3kW baseline
2. **3-phase interleaved** - 6.6kW with 120° shift
3. **Different load points** - 25%, 50%, 75%, 100%

**Run:**
```bash
python tests/unit/test_system_analyzer.py
```

**Expected results:**
- Total losses: 50-200W (depends on power level)
- Efficiency: 95-98%
- Multi-phase: Lower output ripple
- Loss breakdown: MOSFETs > Magnetics > Diodes

### Test 8: Efficiency Mapper

**File:** `tests/unit/test_efficiency_mapper.py`

**What it tests:**
- Efficiency vs load curves
- 2D efficiency maps (V_in vs P_out)
- CEC efficiency calculation
- European efficiency calculation
- CSV export functionality

**Test cases:**
1. **Efficiency curve** - 10% to 100% load
2. **Voltage variation** - 360V to 440V
3. **Weighted efficiency** - CEC and European standards

**Run:**
```bash
python tests/unit/test_efficiency_mapper.py
```

**Expected results:**
- Peak efficiency: 96-98% @ 50-75% load
- CEC efficiency: > 95%
- European efficiency: > 95%
- CSV export: Valid format

### Test 9: Optimizer

**File:** `tests/unit/test_optimizer.py`

**What it tests:**
- Design space generation
- Component filtering
- Design evaluation
- Pareto frontier calculation
- Best design selection

**Test cases:**
1. **Small design space** - 10-20 candidates
2. **Large design space** - 100+ candidates
3. **Multi-objective** - Efficiency vs cost vs size

**Run:**
```bash
python tests/unit/test_optimizer.py
```

**Expected results:**
- All candidates evaluated successfully
- Pareto frontier: 5-20 designs
- Best efficiency: > 95%
- Execution time: < 60s for 100 candidates

### Test 10: Datasheet Parser

**File:** `tests/unit/test_datasheet_parser.py`

**What it tests:**
- PDF text extraction
- Parameter pattern matching
- Unit conversion
- Table extraction
- Batch processing

**Test cases:**
1. **Mock datasheet** - Test pattern matching
2. **Unit conversion** - mΩ→Ω, pF→F, etc.
3. **Device type detection** - SiC MOSFET vs diode

**Run:**
```bash
python tests/unit/test_datasheet_parser.py
```

**Expected results:**
- Text extraction: Success
- Parameters extracted: > 5 parameters
- Unit conversion: Correct
- Confidence scores: > 0.5

---

## Integration Testing

### Test 11: Complete System Analysis

**File:** `tests/integration/test_complete_analysis.py`

**What it tests:**
- End-to-end system analysis workflow
- All modules working together
- Results consistency across modules

**Test scenario:**
Design and analyze a complete 3kW, 400V→48V PSFB converter

**Steps:**
1. Define circuit parameters
2. Design magnetics (resonant L, transformer, output L)
3. Analyze system losses
4. Calculate efficiency
5. Verify results

**Run:**
```bash
python tests/integration/test_complete_analysis.py
```

**Expected output:**
```
================================================================================
INTEGRATION TEST: Complete System Analysis
================================================================================

Step 1: Circuit Parameters
  ✓ MOSFETs and diodes defined

Step 2: Magnetic Design
  ✓ Resonant inductor: 15.2µH
  ✓ Transformer: 8:1, PQ32/30
  ✓ Output inductor: 8.5µH

Step 3: System Analysis
  ✓ MOSFET losses: 45.2W
  ✓ Diode losses: 12.8W
  ✓ Magnetic losses: 18.5W
  ✓ Total losses: 76.5W
  ✓ Efficiency: 97.5%

Step 4: Efficiency Mapping
  ✓ CEC efficiency: 96.8%
  ✓ European efficiency: 96.9%

✓ All integration tests passed!
```

### Test 12: Multi-Phase Interleaving

**File:** `tests/integration/test_multiphase.py`

**What it tests:**
- 2, 3, and 4-phase configurations
- Phase shift accuracy
- Ripple cancellation
- Load balancing

**Run:**
```bash
python tests/integration/test_multiphase.py
```

**Expected results:**
- 2-phase @ 180°: 80% ripple reduction
- 3-phase @ 120°: 85% ripple reduction
- 4-phase @ 90°: 90% ripple reduction

### Test 13: Example Scripts

**File:** `tests/integration/test_examples.py`

**What it tests:**
- All example scripts run without errors
- Results are reasonable
- Plots generated (if applicable)

**Run:**
```bash
python tests/integration/test_examples.py
```

---

## Performance Testing

### Test 14: Execution Time

**File:** `tests/performance/test_performance.py`

**Benchmarks:**
- MOSFET loss calculation: < 1ms
- Magnetic design: < 10ms
- System analysis: < 50ms
- Optimizer (50 candidates): < 30s
- Optimizer (200 candidates): < 2min

**Run:**
```bash
python tests/performance/test_performance.py
```

**Expected output:**
```
================================================================================
PERFORMANCE BENCHMARKS
================================================================================

MOSFET Loss Calculation:
  Iterations: 1000
  Average time: 0.45ms
  ✓ PASS (< 1ms target)

System Analysis:
  Iterations: 100
  Average time: 32ms
  ✓ PASS (< 50ms target)

Optimizer (50 candidates):
  Total time: 18.5s
  Per candidate: 370ms
  ✓ PASS (< 30s target)

✓ All performance tests passed!
```

---

## Validation Against Reference Data

### Test 15: Infineon Application Note Validation

**File:** `tests/validation/test_vs_infineon.py`

**Reference:** Infineon AN2019-10 "MOSFET Power Losses Calculation"

**Test cases:**
- Example 1: Buck converter loss calculation
- Example 2: Half-bridge switching loss
- Example 3: Full-bridge phase-shift

**Acceptance criteria:**
- Loss calculations within ±5% of reference
- Temperature coefficients match

**Run:**
```bash
python tests/validation/test_vs_infineon.py
```

### Test 16: Experimental Data Validation

**File:** `tests/validation/test_vs_experimental.py`

**Reference:** Laboratory measurements (if available)

**Test cases:**
- Compare calculated efficiency vs measured
- Compare calculated losses vs thermal camera
- Validate magnetic design vs physical prototypes

**Acceptance criteria:**
- Efficiency within ±1% of measured
- Loss distribution within ±10%

---

## Debugging Failed Tests

### Common Test Failures

#### 1. Import Errors

**Symptom:**
```
ModuleNotFoundError: No module named 'psfb_loss_analyzer'
```

**Solution:**
```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall package
pip install -e .

# Verify
python -c "import psfb_loss_analyzer; print('OK')"
```

#### 2. Numerical Tolerance Failures

**Symptom:**
```
AssertionError: 97.45 != 97.5
```

**Solution:**
- Tests use tolerance: `abs(result - expected) < 0.1`
- Small variations are normal due to floating-point
- If difference > 1%, investigate root cause

#### 3. Missing Test Data

**Symptom:**
```
FileNotFoundError: tests/validation/reference_data/test1.csv
```

**Solution:**
```bash
# Create reference data directory
mkdir -p tests/validation/reference_data

# Run data generation script (if available)
python tests/validation/generate_reference_data.py
```

#### 4. Timeout Errors

**Symptom:**
```
TimeoutError: Optimization took too long
```

**Solution:**
- Reduce number of candidates for testing
- Use faster model in optimizer
- Check for infinite loops

### Debugging Tips

1. **Run with verbose output:**
```bash
python tests/test_suite.py -v
```

2. **Run single test:**
```bash
python tests/unit/test_mosfet_loss.py
```

3. **Add debug prints:**
```python
print(f"DEBUG: Loss = {loss_watts}W, Expected = {expected_watts}W")
```

4. **Use Python debugger:**
```bash
python -m pdb tests/unit/test_mosfet_loss.py
```

5. **Check intermediate results:**
- Add assertions at each step
- Print intermediate calculations
- Verify input parameters

---

## Test Coverage

### Coverage Report

```bash
# Install coverage tool
pip install pytest-cov

# Run with coverage
pytest --cov=psfb_loss_analyzer --cov-report=html tests/

# Open report
# Windows WSL: explorer.exe htmlcov/index.html
# Or open in browser: htmlcov/index.html
```

### Target Coverage

- **Overall:** > 80%
- **Core modules:** > 90%
- **Loss calculations:** > 95%
- **Utilities:** > 70%

---

## Continuous Testing

### Pre-Commit Testing

Add to your workflow:

```bash
# Before committing changes
python tests/test_suite.py --quick

# Or with pytest
pytest tests/unit/
```

### Automated Testing

Set up GitHub Actions (optional):

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -e .
      - run: python tests/test_suite.py
```

---

## Test Reporting

### Generate Test Report

```bash
# Run tests and save output
python tests/test_suite.py > test_report.txt 2>&1

# Or with pytest
pytest tests/ --html=test_report.html
```

### Test Metrics

Track these metrics:
- **Pass rate:** % of tests passing
- **Coverage:** % of code covered by tests
- **Execution time:** Time to run full suite
- **Regression count:** Failed tests that previously passed

---

## Next Steps

After running tests:

1. **All tests pass?** → Proceed to examples and real designs
2. **Some tests fail?** → Review error messages and debug
3. **Performance issues?** → Profile and optimize
4. **Need more tests?** → Add custom test cases

**Ready to start designing?** See `QUICK_START.md`

---

**Testing Documentation Version:** 1.0
**Last Updated:** 2025-11-15

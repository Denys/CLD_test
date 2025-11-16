# PSFB Loss Analyzer - Installation Guide for Windows 11

Complete installation guide for Windows 11 using WSL2 (Ubuntu) and VS Code integration.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
3. [WSL2 Installation (Recommended)](#wsl2-installation-recommended)
4. [VS Code Setup](#vs-code-setup)
5. [Python Environment Setup](#python-environment-setup)
6. [Package Installation](#package-installation)
7. [Verification](#verification)
8. [Optional Dependencies](#optional-dependencies)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **Operating System:** Windows 11 (64-bit)
- **RAM:** Minimum 8GB (16GB recommended for optimization)
- **Disk Space:** 2GB free space
- **Processor:** Multi-core processor recommended

### Required Software

1. **Windows 11** with latest updates
2. **WSL2** (Windows Subsystem for Linux 2)
3. **Python 3.8+** (via WSL2 Ubuntu)
4. **Git** (for cloning repository)
5. **VS Code** (recommended IDE)

---

## Installation Methods

### Method 1: WSL2 + VS Code (Recommended)
✅ Best for development and testing
✅ Native Linux performance
✅ Full VS Code integration
✅ Easy package management

### Method 2: Native Windows Python
⚠️ May have dependency issues
⚠️ Some libraries may not work correctly
❌ Not recommended for production use

**This guide focuses on Method 1 (WSL2 + VS Code)**

---

## WSL2 Installation (Recommended)

### Step 1: Enable WSL2

Open **PowerShell as Administrator** and run:

```powershell
# Enable WSL
wsl --install

# If WSL is already installed, update to WSL2
wsl --set-default-version 2
```

**Restart your computer** after installation.

### Step 2: Install Ubuntu

After restart, open **PowerShell** and run:

```powershell
# Install Ubuntu 22.04 LTS (recommended)
wsl --install -d Ubuntu-22.04

# List installed distributions to verify
wsl --list --verbose
```

You should see:
```
  NAME            STATE           VERSION
* Ubuntu-22.04    Running         2
```

### Step 3: Set Up Ubuntu User

When Ubuntu first starts, it will ask you to create a user:

```
Enter new UNIX username: your_username
New password: ********
Retype new password: ********
```

**Remember these credentials!**

### Step 4: Update Ubuntu

Inside the Ubuntu terminal:

```bash
# Update package lists
sudo apt update

# Upgrade installed packages
sudo apt upgrade -y

# Install essential build tools
sudo apt install -y build-essential curl wget git
```

### Step 5: Verify WSL2 Installation

```bash
# Check WSL version (should show "2")
cat /proc/version

# Check Ubuntu version (should show 22.04)
lsb_release -a
```

---

## VS Code Setup

### Step 1: Install VS Code on Windows

1. Download from: https://code.visualstudio.com/
2. Run installer with default options
3. Launch VS Code

### Step 2: Install WSL Extension

In VS Code:
1. Click **Extensions** (Ctrl+Shift+X)
2. Search for **"WSL"**
3. Install **"WSL"** by Microsoft
4. Install **"Remote - WSL"** by Microsoft

### Step 3: Connect to WSL

**Method A - From VS Code:**
1. Press **F1** (or Ctrl+Shift+P)
2. Type: `WSL: Connect to WSL`
3. Select **Ubuntu-22.04**

**Method B - From WSL Terminal:**
```bash
# From Ubuntu WSL terminal
code .
```

VS Code will automatically connect to WSL and reopen in WSL mode.

**Verify WSL connection:**
- Look for **"WSL: Ubuntu-22.04"** in bottom-left corner of VS Code
- Terminal in VS Code should show Ubuntu prompt

### Step 4: Install VS Code Extensions in WSL

Install these extensions **in WSL** (not Windows):

1. **Python** by Microsoft
2. **Pylance** by Microsoft
3. **Python Debugger** by Microsoft
4. **Jupyter** by Microsoft (optional, for notebooks)
5. **GitLens** (optional, for Git visualization)

**To install in WSL:**
- Click Extensions (Ctrl+Shift+X)
- Each extension shows "Install in WSL: Ubuntu-22.04"
- Click that button

---

## Python Environment Setup

### Step 1: Install Python 3.10+

In WSL Ubuntu terminal:

```bash
# Python should be pre-installed, check version
python3 --version

# If version < 3.8, install Python 3.10
sudo apt install -y python3.10 python3.10-venv python3-pip

# Set Python 3.10 as default (optional)
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# Verify installation
python3 --version  # Should show 3.10+
pip3 --version
```

### Step 2: Install pip and venv

```bash
# Install pip (if not already installed)
sudo apt install -y python3-pip

# Install venv module
sudo apt install -y python3-venv

# Upgrade pip
pip3 install --upgrade pip
```

### Step 3: Create Virtual Environment

```bash
# Navigate to your projects directory
cd ~
mkdir -p projects
cd projects

# Clone repository
git clone <your-repo-url>/CLD_test.git
cd CLD_test

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Your prompt should now show (venv)
```

**To deactivate later:**
```bash
deactivate
```

### Step 4: Configure VS Code to Use Virtual Environment

In VS Code (connected to WSL):

1. Open Command Palette (Ctrl+Shift+P)
2. Type: `Python: Select Interpreter`
3. Select: `./venv/bin/python` (the venv you just created)

**Verify:**
- Bottom-right of VS Code should show: `Python 3.10.x ('venv')`

---

## Package Installation

### Step 1: Install Core Dependencies

With virtual environment activated:

```bash
# Ensure you're in the project directory
cd ~/projects/CLD_test

# Activate venv if not already activated
source venv/bin/activate

# Install core scientific packages
pip install numpy scipy matplotlib pandas

# Verify installation
python -c "import numpy; print(f'NumPy {numpy.__version__}')"
python -c "import scipy; print(f'SciPy {scipy.__version__}')"
python -c "import matplotlib; print(f'Matplotlib {matplotlib.__version__}')"
python -c "import pandas; print(f'Pandas {pandas.__version__}')"
```

Expected output:
```
NumPy 1.24.0 (or newer)
SciPy 1.10.0 (or newer)
Matplotlib 3.7.0 (or newer)
Pandas 2.0.0 (or newer)
```

### Step 2: Install PSFB Loss Analyzer

```bash
# Option A: Install in development mode (recommended for testing/development)
cd ~/projects/CLD_test
pip install -e .

# Option B: Install as package
cd ~/projects/CLD_test
pip install .

# Verify installation
python -c "import psfb_loss_analyzer; print(f'PSFB Loss Analyzer {psfb_loss_analyzer.__version__}')"
```

Expected output:
```
PSFB Loss Analyzer 0.5.0
```

### Step 3: Install Optional Dependencies

#### For Datasheet Analyzer:

```bash
# PDF parsing dependencies
pip install pdfplumber PyPDF2

# Data analysis
pip install pandas openpyxl

# Verify
python -c "import pdfplumber; print('pdfplumber OK')"
python -c "import PyPDF2; print('PyPDF2 OK')"
```

#### For Jupyter Notebooks (optional):

```bash
pip install jupyter ipykernel

# Register kernel with Jupyter
python -m ipykernel install --user --name=psfb_env --display-name="Python (PSFB)"

# Launch Jupyter
jupyter notebook
```

#### For Advanced Graph Extraction (optional):

```bash
# OCR support (requires system packages)
sudo apt install -y tesseract-ocr
pip install pytesseract

# Image processing
pip install opencv-python pillow

# Verify
python -c "import cv2; print('OpenCV OK')"
```

---

## Verification

### Quick Verification Script

Create a test file: `test_installation.py`

```python
"""
Installation Verification Script
Run this to verify all components are working
"""

import sys

def test_imports():
    """Test all module imports"""
    print("=" * 80)
    print("PSFB LOSS ANALYZER - INSTALLATION VERIFICATION")
    print("=" * 80)
    print()

    modules = [
        ("numpy", "NumPy"),
        ("scipy", "SciPy"),
        ("matplotlib", "Matplotlib"),
        ("pandas", "Pandas"),
        ("psfb_loss_analyzer", "PSFB Loss Analyzer"),
    ]

    optional_modules = [
        ("pdfplumber", "PDF Parsing (Datasheet Analyzer)"),
        ("PyPDF2", "PDF Reading (Datasheet Analyzer)"),
        ("cv2", "OpenCV (Graph Extraction)"),
    ]

    # Test core modules
    print("CORE MODULES:")
    print("-" * 80)
    all_ok = True
    for module_name, display_name in modules:
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'unknown')
            print(f"✓ {display_name:<30} {version}")
        except ImportError as e:
            print(f"✗ {display_name:<30} NOT FOUND")
            all_ok = False

    print()

    # Test optional modules
    print("OPTIONAL MODULES:")
    print("-" * 80)
    for module_name, display_name in optional_modules:
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'unknown')
            print(f"✓ {display_name:<30} {version}")
        except ImportError:
            print(f"○ {display_name:<30} Not installed (optional)")

    print()

    if not all_ok:
        print("✗ INSTALLATION INCOMPLETE - Install missing modules")
        return False

    return True


def test_psfb_modules():
    """Test PSFB Loss Analyzer modules"""
    print("PSFB LOSS ANALYZER MODULES:")
    print("-" * 80)

    modules = [
        "circuit_params",
        "mosfet_loss_calc",
        "diode_loss_calc",
        "resonant_inductor_design",
        "transformer_design",
        "output_inductor_design",
        "system_analyzer",
        "efficiency_mapper",
        "component_library",
        "optimizer",
    ]

    all_ok = True
    for module_name in modules:
        try:
            __import__(f"psfb_loss_analyzer.{module_name}")
            print(f"✓ {module_name}")
        except ImportError as e:
            print(f"✗ {module_name} - Error: {e}")
            all_ok = False

    print()
    return all_ok


def test_basic_functionality():
    """Test basic functionality"""
    print("BASIC FUNCTIONALITY TESTS:")
    print("-" * 80)

    try:
        from psfb_loss_analyzer import MOSFETParameters, CapacitanceVsVoltage

        # Create a simple MOSFET
        mosfet = MOSFETParameters(
            part_number="TEST_MOSFET",
            v_dss=650.0,
            i_d_continuous=90.0,
            r_dson_25c=20e-3,
            r_dson_25c_max=25e-3,
            r_dson_150c=28e-3,
            r_dson_150c_max=35e-3,
            capacitances=CapacitanceVsVoltage(
                c_iss_constant=7200e-12,
                c_oss_constant=520e-12,
                c_rss_constant=15e-12,
            ),
            q_g=142e-9,
            q_gs=38e-9,
            q_gd=52e-9,
            v_gs_plateau=4.5,
            t_r=25e-9,
            t_f=20e-9,
        )

        print(f"✓ Created MOSFET: {mosfet.part_number}")
        print(f"  V_DSS: {mosfet.v_dss}V")
        print(f"  I_D: {mosfet.i_d_continuous}A")
        print(f"  R_DS(on) @ 25°C: {mosfet.r_dson_25c * 1000:.1f}mΩ")
        print()

        return True

    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False


def main():
    """Main verification function"""
    results = []

    # Test imports
    results.append(("Imports", test_imports()))

    # Test PSFB modules
    results.append(("PSFB Modules", test_psfb_modules()))

    # Test basic functionality
    results.append(("Basic Functionality", test_basic_functionality()))

    # Summary
    print("=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {test_name}")

    print()

    if all(result[1] for result in results):
        print("✓ ALL TESTS PASSED - Installation is complete!")
        print()
        print("Next steps:")
        print("1. Run: python tests/test_suite.py")
        print("2. Try examples in: psfb_loss_analyzer/examples/")
        print("3. Read: QUICK_START.md")
        return 0
    else:
        print("✗ SOME TESTS FAILED - Please check errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

### Run Verification:

```bash
# Save the script above as test_installation.py
python test_installation.py
```

**Expected output:**
```
================================================================================
PSFB LOSS ANALYZER - INSTALLATION VERIFICATION
================================================================================

CORE MODULES:
--------------------------------------------------------------------------------
✓ NumPy                          1.24.3
✓ SciPy                          1.10.1
✓ Matplotlib                     3.7.1
✓ Pandas                         2.0.2
✓ PSFB Loss Analyzer            0.5.0

OPTIONAL MODULES:
--------------------------------------------------------------------------------
✓ PDF Parsing (Datasheet Analyzer) 0.9.0
✓ PDF Reading (Datasheet Analyzer) 3.0.1
○ OpenCV (Graph Extraction)      Not installed (optional)

PSFB LOSS ANALYZER MODULES:
--------------------------------------------------------------------------------
✓ circuit_params
✓ mosfet_loss_calc
✓ diode_loss_calc
✓ resonant_inductor_design
✓ transformer_design
✓ output_inductor_design
✓ system_analyzer
✓ efficiency_mapper
✓ component_library
✓ optimizer

BASIC FUNCTIONALITY TESTS:
--------------------------------------------------------------------------------
✓ Created MOSFET: TEST_MOSFET
  V_DSS: 650.0V
  I_D: 90.0A
  R_DS(on) @ 25°C: 20.0mΩ

================================================================================
VERIFICATION SUMMARY
================================================================================
✓ PASS - Imports
✓ PASS - PSFB Modules
✓ PASS - Basic Functionality

✓ ALL TESTS PASSED - Installation is complete!

Next steps:
1. Run: python tests/test_suite.py
2. Try examples in: psfb_loss_analyzer/examples/
3. Read: QUICK_START.md
```

---

## Optional Dependencies

### For Development

```bash
# Testing frameworks
pip install pytest pytest-cov

# Code formatting
pip install black isort flake8

# Type checking
pip install mypy

# Documentation
pip install sphinx sphinx-rtd-theme
```

### For Advanced Features

```bash
# Optimization
pip install scipy>=1.10.0

# Plotting
pip install seaborn plotly

# Excel support
pip install openpyxl xlsxwriter

# Performance profiling
pip install line_profiler memory_profiler
```

---

## Troubleshooting

### Issue 1: WSL2 Not Installing

**Error:** "WSL 2 requires an update to its kernel component"

**Solution:**
1. Download WSL2 kernel update: https://aka.ms/wsl2kernel
2. Run installer
3. Retry: `wsl --set-default-version 2`

### Issue 2: Python Module Not Found

**Error:** `ModuleNotFoundError: No module named 'psfb_loss_analyzer'`

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall in development mode
cd ~/projects/CLD_test
pip install -e .

# Verify
python -c "import psfb_loss_analyzer; print('OK')"
```

### Issue 3: VS Code Not Connecting to WSL

**Solution:**
1. Restart VS Code
2. Press F1 → `WSL: Connect to WSL`
3. If still fails, reinstall WSL extension

### Issue 4: NumPy/SciPy Installation Errors

**Error:** Building wheel for numpy failed

**Solution:**
```bash
# Install build dependencies
sudo apt update
sudo apt install -y python3-dev build-essential gfortran libopenblas-dev

# Retry installation
pip install numpy scipy
```

### Issue 5: Permission Denied

**Error:** `PermissionError: [Errno 13] Permission denied`

**Solution:**
```bash
# Don't use sudo with pip in venv
# If you get this error, recreate venv:
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### Issue 6: Import Errors in VS Code

**Problem:** VS Code shows import errors even though code runs

**Solution:**
1. Ctrl+Shift+P → `Python: Select Interpreter`
2. Choose `./venv/bin/python`
3. Reload window: Ctrl+Shift+P → `Developer: Reload Window`

### Issue 7: Matplotlib Not Displaying Plots

**Solution:**
```bash
# Install tkinter
sudo apt install python3-tk

# Verify
python -c "import tkinter; print('OK')"
```

### Getting Help

If you encounter issues not covered here:

1. Check the main README.md
2. Check TESTING.md for component-specific issues
3. Review example scripts for usage patterns
4. Check GitHub issues: [your-repo-url]/issues

---

## Quick Reference

### Common Commands

```bash
# Activate virtual environment
source ~/projects/CLD_test/venv/bin/activate

# Update PSFB Loss Analyzer
cd ~/projects/CLD_test
git pull
pip install -e .

# Run tests
python tests/test_suite.py

# Run example
python psfb_loss_analyzer/examples/example_6p6kw_complete_analysis.py

# Deactivate virtual environment
deactivate
```

### VS Code Shortcuts

- **Open Terminal:** Ctrl+`
- **Command Palette:** Ctrl+Shift+P
- **Python Interpreter:** Ctrl+Shift+P → "Python: Select Interpreter"
- **Run Python File:** F5 (or Ctrl+F5 without debugging)
- **Format Code:** Shift+Alt+F

---

## Next Steps

After successful installation:

1. **Read Quick Start Guide:** `QUICK_START.md`
2. **Run Test Suite:** `python tests/test_suite.py`
3. **Try Examples:** Explore `psfb_loss_analyzer/examples/`
4. **Read Testing Guide:** `TESTING.md`
5. **Design Your First Converter:** Use the optimizer!

---

**Installation Complete!** 🎉

You now have a fully functional PSFB Loss Analyzer environment on Windows 11 with WSL2 and VS Code integration.

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

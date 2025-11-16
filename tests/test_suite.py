#!/usr/bin/env python3
"""
PSFB Loss Analyzer - Main Test Suite

Comprehensive test runner for all components.

Usage:
    python tests/test_suite.py              # Run all tests
    python tests/test_suite.py -v           # Verbose output
    python tests/test_suite.py --unit       # Unit tests only
    python tests/test_suite.py --integration # Integration tests only

Author: PSFB Loss Analysis Tool
Version: 1.0
"""

import sys
import os
from pathlib import Path
import time
import traceback

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestResult:
    """Test result container"""
    def __init__(self, name, passed, time_ms, error=None):
        self.name = name
        self.passed = passed
        self.time_ms = time_ms
        self.error = error


class TestSuite:
    """Main test suite runner"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.results = []

    def run_test(self, test_func, test_name):
        """Run a single test function"""
        print(f"  Running: {test_name}...", end=" ")
        start_time = time.time()

        try:
            test_func()
            elapsed_ms = (time.time() - start_time) * 1000
            result = TestResult(test_name, True, elapsed_ms)
            print(f"✓ PASS ({elapsed_ms:.1f}ms)")
            self.results.append(result)
            return True

        except AssertionError as e:
            elapsed_ms = (time.time() - start_time) * 1000
            result = TestResult(test_name, False, elapsed_ms, str(e))
            print(f"✗ FAIL ({elapsed_ms:.1f}ms)")
            if self.verbose:
                print(f"    Error: {e}")
            self.results.append(result)
            return False

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            result = TestResult(test_name, False, elapsed_ms, str(e))
            print(f"✗ ERROR ({elapsed_ms:.1f}ms)")
            if self.verbose:
                print(f"    Exception: {e}")
                traceback.print_exc()
            self.results.append(result)
            return False

    def run_test_group(self, test_module_name, test_group_name):
        """Run a group of tests from a module"""
        print(f"\n{test_group_name}")
        print("=" * 80)

        try:
            # Import test module
            test_module = __import__(f"tests.unit.{test_module_name}", fromlist=[''])

            # Get all test functions
            test_functions = [
                (name, getattr(test_module, name))
                for name in dir(test_module)
                if name.startswith('test_') and callable(getattr(test_module, name))
            ]

            if not test_functions:
                print("  No tests found")
                return 0

            # Run all tests
            passed = 0
            for test_name, test_func in test_functions:
                if self.run_test(test_func, test_name):
                    passed += 1

            print(f"\n  Results: {passed}/{len(test_functions)} passed")
            return passed

        except ImportError as e:
            print(f"  ✗ Failed to import test module: {e}")
            return 0

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        total_time = sum(r.time_ms for r in self.results)

        print(f"Total tests:  {total}")
        print(f"Passed:       {passed} ({100 * passed / total if total > 0 else 0:.1f}%)")
        print(f"Failed:       {failed}")
        print(f"Total time:   {total_time:.1f}ms")
        print()

        if failed > 0:
            print("FAILED TESTS:")
            print("-" * 80)
            for result in self.results:
                if not result.passed:
                    print(f"  ✗ {result.name}")
                    if result.error and self.verbose:
                        print(f"    {result.error}")
            print()

        if passed == total:
            print("✓ ALL TESTS PASSED!")
            return 0
        else:
            print(f"✗ {failed} TEST(S) FAILED")
            return 1


def main():
    """Main test runner"""
    import argparse

    parser = argparse.ArgumentParser(description='PSFB Loss Analyzer Test Suite')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose output')
    parser.add_argument('--unit', action='store_true',
                        help='Run unit tests only')
    parser.add_argument('--integration', action='store_true',
                        help='Run integration tests only')
    parser.add_argument('--quick', action='store_true',
                        help='Run quick tests only (skip slow tests)')

    args = parser.parse_args()

    print("=" * 80)
    print("PSFB LOSS ANALYZER - TEST SUITE")
    print("=" * 80)

    suite = TestSuite(verbose=args.verbose)

    # Unit tests
    if not args.integration:
        suite.run_test_group('test_circuit_params', 'UNIT TESTS: Circuit Parameters')
        suite.run_test_group('test_mosfet_loss', 'UNIT TESTS: MOSFET Loss Calculations')
        suite.run_test_group('test_diode_loss', 'UNIT TESTS: Diode Loss Calculations')
        suite.run_test_group('test_resonant_inductor', 'UNIT TESTS: Resonant Inductor Design')
        suite.run_test_group('test_transformer', 'UNIT TESTS: Transformer Design')
        suite.run_test_group('test_output_inductor', 'UNIT TESTS: Output Inductor Design')
        suite.run_test_group('test_system_analyzer', 'UNIT TESTS: System Analyzer')
        suite.run_test_group('test_efficiency_mapper', 'UNIT TESTS: Efficiency Mapper')

        if not args.quick:
            suite.run_test_group('test_optimizer', 'UNIT TESTS: Optimizer')

    # Integration tests
    if args.integration or not args.unit:
        if not args.quick:
            suite.run_test_group('test_complete_analysis', 'INTEGRATION TESTS: Complete Analysis')

    # Print summary
    return suite.print_summary()


if __name__ == "__main__":
    sys.exit(main())

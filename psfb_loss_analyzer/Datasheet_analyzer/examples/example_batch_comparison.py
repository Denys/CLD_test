"""
Example: Batch Datasheet Processing and Comparison

Demonstrates how to process multiple datasheets and generate comparison reports.
Useful for evaluating multiple component options for a design.

Usage:
    python example_batch_comparison.py <directory_with_pdfs>

Author: PSFB Loss Analysis Tool
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from batch_processor import BatchProcessor


def main():
    """Main example function"""
    if len(sys.argv) < 2:
        print("Usage: python example_batch_comparison.py <directory_with_pdfs>")
        print("\nExample:")
        print("  python example_batch_comparison.py ../datasheets/")
        return

    directory = sys.argv[1]

    print("=" * 100)
    print("BATCH DATASHEET PROCESSING AND COMPARISON")
    print("=" * 100)
    print(f"Directory: {directory}")
    print()

    # Create batch processor
    processor = BatchProcessor()

    # Process all PDFs in directory
    print("PROCESSING DATASHEETS...")
    print("-" * 100)
    results = processor.process_directory(directory, file_pattern="*.pdf")

    if not results:
        print("\n✗ No datasheets successfully processed")
        return

    print("\n✓ Processing complete!")
    print(f"Successfully processed: {len(results)} datasheets\n")

    # Create comparison report
    print("=" * 100)
    print("GENERATING COMPARISON REPORT")
    print("=" * 100)

    report = processor.create_comparison(results)

    # Overall comparison
    print("\nALL DEVICES:")
    report.print_summary()

    # Filter and compare MOSFETs only
    mosfet_results = [r for r in results if 'MOSFET' in r.device_type.value]
    if mosfet_results:
        print("\n" + "=" * 100)
        print("MOSFET COMPARISON")
        print("=" * 100)

        mosfet_report = processor.create_comparison(mosfet_results)

        # Calculate figure of merit (R_DS(on) × Q_g)
        # Lower is better for switching applications
        mosfet_report.calculate_fom('r_dson_25c', 'q_g')

        # Sort by FOM
        mosfet_report.sort_by_parameter('fom', ascending=True)

        mosfet_report.print_summary()

        # Find best devices by criteria
        print("\nBEST DEVICES BY CRITERIA:")
        print("-" * 100)

        best_rdson = mosfet_report.get_best_by_parameter('r_dson_25c', minimize=True)
        if best_rdson:
            print(f"Lowest R_DS(on): {best_rdson.part_number}")
            print(f"  R_DS(on) @ 25°C: {best_rdson.parameters['r_dson_25c'] * 1000:.1f}mΩ")

        best_current = mosfet_report.get_best_by_parameter('i_d_continuous', minimize=False)
        if best_current:
            print(f"\nHighest Current Rating: {best_current.part_number}")
            print(f"  I_D: {best_current.parameters['i_d_continuous']}A")

        if 'fom' in mosfet_report.entries[0].parameters:
            best_fom = mosfet_report.get_best_by_parameter('fom', minimize=True)
            if best_fom:
                print(f"\nBest FOM (R_DS(on) × Q_g): {best_fom.part_number}")
                print(f"  FOM: {best_fom.parameters['fom']:.2e}")

        # Export MOSFET comparison to CSV
        mosfet_report.to_csv("mosfet_comparison.csv")
        print(f"\n✓ MOSFET comparison exported to: mosfet_comparison.csv")

    # Filter and compare diodes only
    diode_results = [r for r in results if 'Schottky' in r.device_type.value or 'Diode' in r.device_type.value]
    if diode_results:
        print("\n" + "=" * 100)
        print("DIODE COMPARISON")
        print("=" * 100)

        diode_report = processor.create_comparison(diode_results)

        # Sort by voltage rating
        diode_report.sort_by_parameter('v_rrm', ascending=False)

        diode_report.print_summary()

        # Find best devices
        print("\nBEST DEVICES BY CRITERIA:")
        print("-" * 100)

        best_vf = diode_report.get_best_by_parameter('v_f_25c', minimize=True)
        if best_vf:
            print(f"Lowest V_F: {best_vf.part_number}")
            print(f"  V_F @ 25°C: {best_vf.parameters['v_f_25c']}V")

        best_current = diode_report.get_best_by_parameter('i_f_avg', minimize=False)
        if best_current:
            print(f"\nHighest Current Rating: {best_current.part_number}")
            print(f"  I_F(avg): {best_current.parameters['i_f_avg']}A")

        # Export diode comparison to CSV
        diode_report.to_csv("diode_comparison.csv")
        print(f"\n✓ Diode comparison exported to: diode_comparison.csv")

    # Export all to component library format
    print("\n" + "=" * 100)
    print("EXPORTING TO COMPONENT LIBRARY")
    print("=" * 100)

    processor.export_to_library(results, "extracted_components.py")

    print("\n" + "=" * 100)
    print("BATCH PROCESSING COMPLETE!")
    print("=" * 100)
    print(f"✓ Processed {len(results)} datasheets")
    print(f"✓ Comparison reports saved to CSV")
    print(f"✓ Component library exported to: extracted_components.py")
    print()
    print("NEXT STEPS:")
    print("1. Review extracted parameters for accuracy")
    print("2. Manually add missing parameters from graphs")
    print("3. Add cost and availability information")
    print("4. Integrate into main component_library.py")
    print()


if __name__ == "__main__":
    main()

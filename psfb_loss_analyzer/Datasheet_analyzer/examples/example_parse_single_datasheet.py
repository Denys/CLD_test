"""
Example: Parse Single Datasheet

Demonstrates how to extract parameters from a single MOSFET or diode datasheet.

Usage:
    python example_parse_single_datasheet.py <path_to_pdf>

Author: PSFB Loss Analysis Tool
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from datasheet_parser import DatasheetParser, DeviceType


def main():
    """Main example function"""
    if len(sys.argv) < 2:
        print("Usage: python example_parse_single_datasheet.py <path_to_pdf>")
        print("\nExample:")
        print("  python example_parse_single_datasheet.py ../datasheets/IMZA65R020M2H.pdf")
        return

    pdf_path = sys.argv[1]

    # Create parser
    parser = DatasheetParser()

    print("=" * 80)
    print("DATASHEET PARAMETER EXTRACTION")
    print("=" * 80)
    print(f"PDF: {pdf_path}")
    print()

    # Parse datasheet
    result = parser.parse_datasheet(pdf_path)

    # Print extraction report
    parser.print_extraction_report(result)

    # Convert to appropriate dataclass
    print("\nCONVERTED TO DATACLASS:")
    print("=" * 80)

    if result.device_type in [DeviceType.SIC_MOSFET, DeviceType.SI_MOSFET]:
        mosfet = parser.to_mosfet_parameters(result)

        print("MOSFETParameters(")
        print(f"    part_number=\"{mosfet.part_number}\",")
        print(f"    v_dss={mosfet.v_dss},  # V")
        print(f"    i_d_continuous={mosfet.i_d_continuous},  # A")
        print(f"    r_dson_25c={mosfet.r_dson_25c},  # Ω")
        print(f"    r_dson_25c_max={mosfet.r_dson_25c_max},  # Ω")
        print(f"    r_dson_150c={mosfet.r_dson_150c},  # Ω")
        print(f"    r_dson_150c_max={mosfet.r_dson_150c_max},  # Ω")
        print(f"    q_g={mosfet.q_g},  # C")
        print(f"    q_gs={mosfet.q_gs},  # C")
        print(f"    q_gd={mosfet.q_gd},  # C")
        print(f"    v_gs_plateau={mosfet.v_gs_plateau},  # V")
        print(f"    t_r={mosfet.t_r},  # s")
        print(f"    t_f={mosfet.t_f},  # s")
        print(")")

        print("\nKEY SPECIFICATIONS:")
        print(f"  Voltage Rating: {mosfet.v_dss}V")
        print(f"  Current Rating: {mosfet.i_d_continuous}A")
        print(f"  R_DS(on) @ 25°C: {mosfet.r_dson_25c * 1000:.1f}mΩ")
        print(f"  R_DS(on) @ 150°C: {mosfet.r_dson_150c * 1000:.1f}mΩ")
        print(f"  Gate Charge: {mosfet.q_g * 1e9:.1f}nC")

    elif result.device_type in [DeviceType.SIC_SCHOTTKY, DeviceType.SI_PN_DIODE]:
        diode = parser.to_diode_parameters(result)

        print("DiodeParameters(")
        print(f"    part_number=\"{diode.part_number}\",")
        print(f"    v_rrm={diode.v_rrm},  # V")
        print(f"    i_f_avg={diode.i_f_avg},  # A")
        print(f"    v_f0={diode.v_f0},  # V")
        print(f"    r_f={diode.r_f},  # Ω")
        print(f"    v_f_25c={diode.v_f_25c},  # V")
        print(f"    v_f_125c={diode.v_f_125c},  # V")
        print(f"    t_rr={diode.t_rr},  # s")
        print(f"    q_rr={diode.q_rr},  # C")
        print(")")

        print("\nKEY SPECIFICATIONS:")
        print(f"  Voltage Rating: {diode.v_rrm}V")
        print(f"  Current Rating: {diode.i_f_avg}A")
        print(f"  V_F @ 25°C: {diode.v_f_25c}V")
        print(f"  V_F @ 125°C: {diode.v_f_125c}V")

    print()

    # Generate component library entry
    print("\nCOMPONENT LIBRARY ENTRY:")
    print("=" * 80)

    if result.device_type in [DeviceType.SIC_MOSFET, DeviceType.SI_MOSFET]:
        mosfet = parser.to_mosfet_parameters(result)
        print(f'"{mosfet.part_number}": {{')
        print(f'    "device": MOSFETParameters(...),')
        print(f'    "metrics": ComponentMetrics(')
        print(f'        manufacturer="{result.manufacturer}",')
        print(f'        package="TO-247",  # Extract from datasheet')
        print(f'        relative_cost=1.0,  # Set manually')
        print(f'    ),')
        print(f'    "description": "Auto-extracted from datasheet",')
        print(f'    "extraction_confidence": {result.overall_confidence:.2f},')
        print(f'}},')

    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("1. Review extracted parameters for accuracy")
    print("2. Manually add missing parameters (especially from graphs):")
    print("   - Gate charge values (Q_g, Q_gs, Q_gd) from gate charge curve")
    print("   - Switching times (t_r, t_f) from switching characteristics")
    print("   - Capacitance values (C_iss, C_oss, C_rss) from capacitance curves")
    print("3. Add cost and package information")
    print("4. Add to component library")
    print()


if __name__ == "__main__":
    main()

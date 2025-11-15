"""
Batch Datasheet Processing and Comparison

Processes multiple datasheets and generates comparison reports.
Useful for evaluating multiple component options.

Author: PSFB Loss Analysis Tool
Version: 1.0.0
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import warnings

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

from datasheet_parser import DatasheetParser, ExtractionResult, DeviceType


@dataclass
class ComparisonEntry:
    """Single component in comparison"""
    part_number: str
    manufacturer: str
    device_type: str
    parameters: Dict[str, float]
    confidence: float
    datasheet_path: str


@dataclass
class ComparisonReport:
    """Comparison report for multiple devices"""
    entries: List[ComparisonEntry] = field(default_factory=list)
    device_type_filter: Optional[str] = None

    def add_entry(self, entry: ComparisonEntry):
        """Add component to comparison"""
        self.entries.append(entry)

    def filter_by_type(self, device_type: str):
        """Filter comparison by device type"""
        self.device_type_filter = device_type
        self.entries = [e for e in self.entries if e.device_type == device_type]

    def sort_by_parameter(self, param_name: str, ascending: bool = True):
        """Sort entries by parameter value"""
        self.entries.sort(
            key=lambda e: e.parameters.get(param_name, float('inf')),
            reverse=not ascending
        )

    def get_best_by_parameter(self, param_name: str, minimize: bool = True) -> Optional[ComparisonEntry]:
        """Get best device based on parameter"""
        if not self.entries:
            return None

        valid_entries = [e for e in self.entries if param_name in e.parameters]
        if not valid_entries:
            return None

        if minimize:
            return min(valid_entries, key=lambda e: e.parameters[param_name])
        else:
            return max(valid_entries, key=lambda e: e.parameters[param_name])

    def calculate_fom(self, param1: str, param2: str, weight1: float = 1.0, weight2: float = 1.0):
        """
        Calculate figure of merit for each entry

        FOM = weight1 * param1 * weight2 * param2

        For MOSFETs: R_DS(on) * Q_g (lower is better)
        """
        for entry in self.entries:
            if param1 in entry.parameters and param2 in entry.parameters:
                fom = weight1 * entry.parameters[param1] * weight2 * entry.parameters[param2]
                entry.parameters['fom'] = fom

    def to_dataframe(self) -> Optional['pd.DataFrame']:
        """Convert comparison to pandas DataFrame"""
        if not PANDAS_AVAILABLE:
            warnings.warn("pandas not available")
            return None

        rows = []
        for entry in self.entries:
            row = {
                'Part Number': entry.part_number,
                'Manufacturer': entry.manufacturer,
                'Type': entry.device_type,
                'Confidence': f"{entry.confidence:.0%}",
            }
            row.update(entry.parameters)
            rows.append(row)

        return pd.DataFrame(rows)

    def to_csv(self, output_path: str):
        """Export comparison to CSV"""
        df = self.to_dataframe()
        if df is not None:
            df.to_csv(output_path, index=False)
            print(f"Comparison exported to: {output_path}")

    def print_summary(self):
        """Print comparison summary"""
        print("=" * 100)
        print("COMPONENT COMPARISON REPORT")
        print("=" * 100)
        print(f"Total components: {len(self.entries)}")
        if self.device_type_filter:
            print(f"Filtered by type: {self.device_type_filter}")
        print()

        if not self.entries:
            print("No components to compare")
            return

        # Get all parameter names
        all_params = set()
        for entry in self.entries:
            all_params.update(entry.parameters.keys())

        # Print table header
        header = f"{'Part Number':<20} {'Manufacturer':<15} {'Type':<15} {'Conf':<6}"
        print(header)
        print("-" * 100)

        # Print entries
        for entry in self.entries:
            type_str = entry.device_type[:13]
            conf_str = f"{entry.confidence:.0%}"
            print(f"{entry.part_number:<20} {entry.manufacturer:<15} {type_str:<15} {conf_str:<6}")

        print()

        # Print parameter comparison
        if PANDAS_AVAILABLE:
            df = self.to_dataframe()
            print("Parameter Comparison:")
            print(df.to_string(index=False))


class BatchProcessor:
    """Batch process multiple datasheets"""

    def __init__(self):
        """Initialize batch processor"""
        self.parser = DatasheetParser()
        self.results: List[ExtractionResult] = []

    def process_directory(
        self,
        directory: str,
        file_pattern: str = "*.pdf",
        device_type: Optional[str] = None
    ) -> List[ExtractionResult]:
        """
        Process all datasheets in directory

        Args:
            directory: Path to directory containing PDFs
            file_pattern: File pattern to match (default: *.pdf)
            device_type: Optional device type filter

        Returns:
            List of extraction results
        """
        directory_path = Path(directory)
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        pdf_files = list(directory_path.glob(file_pattern))
        print(f"Found {len(pdf_files)} PDF files in {directory}")
        print()

        results = []
        for idx, pdf_file in enumerate(pdf_files, start=1):
            print(f"[{idx}/{len(pdf_files)}] Processing: {pdf_file.name}")

            try:
                result = self.parser.parse_datasheet(str(pdf_file))

                # Filter by device type if specified
                if device_type:
                    if result.device_type.value.lower() != device_type.lower():
                        print(f"  ⊗ Skipped (wrong type: {result.device_type.value})")
                        continue

                results.append(result)
                print(f"  ✓ Extracted: {result.part_number} ({result.device_type.value})")
                print(f"    Confidence: {result.overall_confidence:.0%}")

                if result.warnings:
                    for warning in result.warnings:
                        print(f"    ⚠ {warning}")

            except Exception as e:
                print(f"  ✗ Error: {e}")

            print()

        self.results.extend(results)
        return results

    def process_file_list(self, file_paths: List[str]) -> List[ExtractionResult]:
        """
        Process list of datasheet files

        Args:
            file_paths: List of PDF file paths

        Returns:
            List of extraction results
        """
        results = []
        for idx, pdf_path in enumerate(file_paths, start=1):
            print(f"[{idx}/{len(file_paths)}] Processing: {os.path.basename(pdf_path)}")

            try:
                result = self.parser.parse_datasheet(pdf_path)
                results.append(result)
                print(f"  ✓ {result.part_number} ({result.device_type.value})")
            except Exception as e:
                print(f"  ✗ Error: {e}")

        self.results.extend(results)
        return results

    def create_comparison(
        self,
        results: Optional[List[ExtractionResult]] = None
    ) -> ComparisonReport:
        """
        Create comparison report from results

        Args:
            results: Optional list of results (uses self.results if None)

        Returns:
            ComparisonReport
        """
        if results is None:
            results = self.results

        report = ComparisonReport()

        for result in results:
            # Extract parameter values
            param_values = {}
            for param_name, param in result.parameters.items():
                param_values[param_name] = param.value

            entry = ComparisonEntry(
                part_number=result.part_number,
                manufacturer=result.manufacturer,
                device_type=result.device_type.value,
                parameters=param_values,
                confidence=result.overall_confidence,
                datasheet_path=result.datasheet_path
            )

            report.add_entry(entry)

        return report

    def export_to_library(
        self,
        results: Optional[List[ExtractionResult]] = None,
        output_path: str = "extracted_components.py"
    ):
        """
        Export results to component library format

        Args:
            results: Optional list of results (uses self.results if None)
            output_path: Output file path
        """
        if results is None:
            results = self.results

        with open(output_path, 'w') as f:
            f.write('"""\n')
            f.write('Auto-generated Component Library from Datasheet Extraction\n')
            f.write('"""\n\n')
            f.write('from circuit_params import MOSFETParameters, DiodeParameters, CapacitanceVsVoltage\n')
            f.write('from component_library import ComponentMetrics\n\n')

            # Separate MOSFETs and diodes
            mosfets = [r for r in results if r.device_type in [DeviceType.SIC_MOSFET, DeviceType.SI_MOSFET]]
            diodes = [r for r in results if r.device_type in [DeviceType.SIC_SCHOTTKY, DeviceType.SI_PN_DIODE]]

            if mosfets:
                f.write('# ============================================================================\n')
                f.write('# MOSFETs (Auto-extracted)\n')
                f.write('# ============================================================================\n\n')
                f.write('MOSFET_LIBRARY_EXTRACTED = {\n')

                for result in mosfets:
                    mosfet = self.parser.to_mosfet_parameters(result)
                    f.write(f'    "{mosfet.part_number}": {{\n')
                    f.write(f'        "device": MOSFETParameters(\n')
                    f.write(f'            part_number="{mosfet.part_number}",\n')
                    f.write(f'            v_dss={mosfet.v_dss},\n')
                    f.write(f'            i_d_continuous={mosfet.i_d_continuous},\n')
                    f.write(f'            r_dson_25c={mosfet.r_dson_25c},\n')
                    f.write(f'            r_dson_25c_max={mosfet.r_dson_25c_max},\n')
                    f.write(f'            r_dson_150c={mosfet.r_dson_150c},\n')
                    f.write(f'            r_dson_150c_max={mosfet.r_dson_150c_max},\n')
                    f.write(f'            q_g={mosfet.q_g},\n')
                    f.write(f'            q_gs={mosfet.q_gs},\n')
                    f.write(f'            q_gd={mosfet.q_gd},\n')
                    f.write(f'            v_gs_plateau={mosfet.v_gs_plateau},\n')
                    f.write(f'            t_r={mosfet.t_r},\n')
                    f.write(f'            t_f={mosfet.t_f},\n')
                    f.write(f'        ),\n')
                    f.write(f'        "metrics": ComponentMetrics(\n')
                    f.write(f'            manufacturer="{result.manufacturer}",\n')
                    f.write(f'        ),\n')
                    f.write(f'        "extraction_confidence": {result.overall_confidence},\n')
                    f.write(f'    }},\n\n')

                f.write('}\n\n')

            if diodes:
                f.write('# ============================================================================\n')
                f.write('# Diodes (Auto-extracted)\n')
                f.write('# ============================================================================\n\n')
                f.write('DIODE_LIBRARY_EXTRACTED = {\n')

                for result in diodes:
                    diode = self.parser.to_diode_parameters(result)
                    f.write(f'    "{diode.part_number}": {{\n')
                    f.write(f'        "device": DiodeParameters(\n')
                    f.write(f'            part_number="{diode.part_number}",\n')
                    f.write(f'            v_rrm={diode.v_rrm},\n')
                    f.write(f'            i_f_avg={diode.i_f_avg},\n')
                    f.write(f'            v_f0={diode.v_f0},\n')
                    f.write(f'            r_f={diode.r_f},\n')
                    f.write(f'            v_f_25c={diode.v_f_25c},\n')
                    f.write(f'            v_f_125c={diode.v_f_125c},\n')
                    f.write(f'            t_rr={diode.t_rr},\n')
                    f.write(f'            q_rr={diode.q_rr},\n')
                    f.write(f'        ),\n')
                    f.write(f'        "metrics": ComponentMetrics(\n')
                    f.write(f'            manufacturer="{result.manufacturer}",\n')
                    f.write(f'        ),\n')
                    f.write(f'        "extraction_confidence": {result.overall_confidence},\n')
                    f.write(f'    }},\n\n')

                f.write('}\n')

        print(f"Component library exported to: {output_path}")


# ============================================================================
# Module Information
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python batch_processor.py <directory> [device_type]")
        print("\nExample:")
        print("  python batch_processor.py datasheets/ mosfet")
        print("  python batch_processor.py datasheets/ diode")
        sys.exit(1)

    directory = sys.argv[1]
    device_type = sys.argv[2] if len(sys.argv) > 2 else None

    processor = BatchProcessor()

    # Process all PDFs in directory
    results = processor.process_directory(directory, device_type=device_type)

    if results:
        # Create comparison report
        report = processor.create_comparison(results)
        report.print_summary()

        # Export to CSV
        report.to_csv("component_comparison.csv")

        # Export to library format
        processor.export_to_library(results, "extracted_components.py")

        print("\n✓ Batch processing complete!")
        print(f"  Processed: {len(results)} datasheets")
        print(f"  Comparison: component_comparison.csv")
        print(f"  Library: extracted_components.py")
    else:
        print("\n✗ No datasheets successfully processed")

"""
Advanced Table Extraction from PDF Datasheets

Extracts structured data from tables in PDF datasheets using pdfplumber's
table detection capabilities. Handles various table formats from different
manufacturers.

Author: PSFB Loss Analysis Tool
Version: 1.0.0
"""

import re
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import warnings

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    warnings.warn("pdfplumber not installed. Install with: pip install pdfplumber")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None


@dataclass
class TableCell:
    """Single table cell"""
    value: str
    row: int
    col: int


@dataclass
class ExtractedTable:
    """Extracted table with metadata"""
    headers: List[str]
    rows: List[List[str]]
    page_number: int
    title: str = ""
    confidence: float = 1.0


class TableExtractor:
    """Extract tables from PDF datasheets"""

    # Common table keywords to identify relevant tables
    MOSFET_TABLE_KEYWORDS = [
        'absolute maximum ratings',
        'electrical characteristics',
        'static characteristics',
        'dynamic characteristics',
        'switching characteristics',
        'capacitance',
        'gate charge',
        'thermal characteristics',
    ]

    DIODE_TABLE_KEYWORDS = [
        'absolute maximum ratings',
        'electrical characteristics',
        'static characteristics',
        'dynamic characteristics',
        'reverse recovery',
        'thermal characteristics',
    ]

    def __init__(self):
        """Initialize table extractor"""
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError("pdfplumber required for table extraction. Install with: pip install pdfplumber")

    def extract_tables_from_pdf(self, pdf_path: str, device_type: str = "mosfet") -> List[ExtractedTable]:
        """
        Extract all relevant tables from PDF

        Args:
            pdf_path: Path to PDF file
            device_type: "mosfet" or "diode"

        Returns:
            List of extracted tables
        """
        tables = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # Get page text to identify table context
                page_text = page.extract_text() or ""

                # Extract tables from page
                page_tables = page.extract_tables()

                for table_idx, table in enumerate(page_tables):
                    if not table or len(table) < 2:
                        continue

                    # Try to find table title from preceding text
                    title = self._find_table_title(page_text, table_idx)

                    # Check if table is relevant
                    if not self._is_relevant_table(title, page_text, device_type):
                        continue

                    # Clean and structure table
                    cleaned_table = self._clean_table(table)
                    if not cleaned_table:
                        continue

                    headers, rows = cleaned_table

                    tables.append(ExtractedTable(
                        headers=headers,
                        rows=rows,
                        page_number=page_num,
                        title=title,
                        confidence=0.9
                    ))

        return tables

    def _find_table_title(self, page_text: str, table_idx: int) -> str:
        """Find table title from page text"""
        # Look for common table titles
        for keyword in self.MOSFET_TABLE_KEYWORDS + self.DIODE_TABLE_KEYWORDS:
            pattern = rf'(?i)\b{keyword}\b'
            if re.search(pattern, page_text):
                return keyword.title()
        return f"Table {table_idx + 1}"

    def _is_relevant_table(self, title: str, page_text: str, device_type: str) -> bool:
        """Check if table is relevant for parameter extraction"""
        title_lower = title.lower()
        text_lower = page_text.lower()

        keywords = self.MOSFET_TABLE_KEYWORDS if device_type == "mosfet" else self.DIODE_TABLE_KEYWORDS

        # Check title
        for keyword in keywords:
            if keyword in title_lower:
                return True

        # Check page text
        relevant_keywords = ['parameter', 'symbol', 'condition', 'min', 'typ', 'max', 'unit']
        matches = sum(1 for kw in relevant_keywords if kw in text_lower[:500])

        return matches >= 3

    def _clean_table(self, table: List[List[str]]) -> Optional[Tuple[List[str], List[List[str]]]]:
        """Clean and structure table data"""
        if not table or len(table) < 2:
            return None

        # Remove None values
        cleaned = []
        for row in table:
            cleaned_row = [cell.strip() if cell else "" for cell in row]
            if any(cleaned_row):  # Skip empty rows
                cleaned.append(cleaned_row)

        if len(cleaned) < 2:
            return None

        # First row is typically headers
        headers = cleaned[0]
        rows = cleaned[1:]

        # Ensure consistent column count
        max_cols = max(len(row) for row in [headers] + rows)
        headers = headers + [""] * (max_cols - len(headers))
        rows = [row + [""] * (max_cols - len(row)) for row in rows]

        return headers, rows

    def table_to_dataframe(self, table: ExtractedTable) -> Optional[Any]:
        """Convert extracted table to pandas DataFrame"""
        if not PANDAS_AVAILABLE:
            return None

        try:
            df = pd.DataFrame(table.rows, columns=table.headers)
            return df
        except Exception as e:
            warnings.warn(f"Failed to convert table to DataFrame: {e}")
            return None

    def find_parameter_in_tables(
        self,
        tables: List[ExtractedTable],
        parameter_names: List[str],
        symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for specific parameter across all tables

        Args:
            tables: List of extracted tables
            parameter_names: List of parameter name variations to search for
            symbol: Optional parameter symbol (e.g., "R_DS(on)")

        Returns:
            Dictionary with found values
        """
        results = {}

        for table in tables:
            # Convert to DataFrame for easier searching
            if PANDAS_AVAILABLE:
                df = self.table_to_dataframe(table)
                if df is None:
                    continue

                # Search in first column (usually parameter names)
                for param_name in parameter_names:
                    # Case-insensitive search
                    pattern = re.compile(param_name, re.IGNORECASE)

                    for idx, row in df.iterrows():
                        # Check first column
                        first_col = str(row.iloc[0]) if len(row) > 0 else ""

                        if pattern.search(first_col):
                            # Found parameter - extract values
                            row_dict = row.to_dict()
                            results[param_name] = {
                                'table_title': table.title,
                                'page': table.page_number,
                                'row': row_dict,
                                'confidence': table.confidence
                            }
                            break

            else:
                # Fallback: search in rows directly
                for row in table.rows:
                    if not row:
                        continue

                    first_cell = row[0].lower()

                    for param_name in parameter_names:
                        if param_name.lower() in first_cell:
                            results[param_name] = {
                                'table_title': table.title,
                                'page': table.page_number,
                                'row': row,
                                'confidence': table.confidence
                            }
                            break

        return results

    def extract_mosfet_parameters_from_tables(self, tables: List[ExtractedTable]) -> Dict[str, Any]:
        """Extract MOSFET parameters from tables"""
        params = {}

        # Define parameter search patterns
        search_patterns = {
            'v_dss': ['Drain-Source Voltage', 'V_DSS', 'V_DS', 'Drain Voltage'],
            'i_d': ['Drain Current', 'I_D', 'Continuous Drain Current', 'I_D (continuous)'],
            'r_dson': ['On-Resistance', 'R_DS(on)', 'R_DS(ON)', 'Drain-Source On-Resistance'],
            'v_gsth': ['Gate Threshold Voltage', 'V_GS(th)', 'V_th', 'Threshold Voltage'],
            'c_iss': ['Input Capacitance', 'C_iss', 'C_ISS'],
            'c_oss': ['Output Capacitance', 'C_oss', 'C_OSS'],
            'c_rss': ['Reverse Transfer Capacitance', 'C_rss', 'C_RSS', 'C_gd'],
            'q_g': ['Total Gate Charge', 'Q_g', 'Q_G', 'Gate Charge'],
            'q_gs': ['Gate-Source Charge', 'Q_gs', 'Q_GS'],
            'q_gd': ['Gate-Drain Charge', 'Q_gd', 'Q_GD', 'Miller Charge'],
            't_r': ['Rise Time', 't_r', 'Turn-On Rise Time'],
            't_f': ['Fall Time', 't_f', 'Turn-Off Fall Time'],
        }

        for param_key, search_terms in search_patterns.items():
            results = self.find_parameter_in_tables(tables, search_terms)
            if results:
                params[param_key] = results

        return params

    def extract_diode_parameters_from_tables(self, tables: List[ExtractedTable]) -> Dict[str, Any]:
        """Extract diode parameters from tables"""
        params = {}

        # Define parameter search patterns for diodes
        search_patterns = {
            'v_rrm': ['Repetitive Peak Reverse Voltage', 'V_RRM', 'V_R', 'Reverse Voltage'],
            'i_f': ['Average Forward Current', 'I_F', 'I_F(AV)', 'Forward Current'],
            'v_f': ['Forward Voltage', 'V_F', 'Forward Voltage Drop'],
            'i_r': ['Reverse Current', 'I_R', 'Leakage Current', 'Reverse Leakage'],
            't_rr': ['Reverse Recovery Time', 't_rr', 't_RR'],
            'q_rr': ['Reverse Recovery Charge', 'Q_rr', 'Q_RR'],
            'c_j': ['Junction Capacitance', 'C_j', 'C_J', 'C_T'],
        }

        for param_key, search_terms in search_patterns.items():
            results = self.find_parameter_in_tables(tables, search_terms)
            if results:
                params[param_key] = results

        return params

    def print_tables_summary(self, tables: List[ExtractedTable]):
        """Print summary of extracted tables"""
        print("=" * 80)
        print("EXTRACTED TABLES SUMMARY")
        print("=" * 80)
        print(f"Total tables found: {len(tables)}\n")

        for idx, table in enumerate(tables, start=1):
            print(f"Table {idx}:")
            print(f"  Title: {table.title}")
            print(f"  Page: {table.page_number}")
            print(f"  Dimensions: {len(table.rows)} rows × {len(table.headers)} columns")
            print(f"  Headers: {', '.join(table.headers[:5])}...")
            print(f"  Confidence: {table.confidence:.0%}")
            print()

    def export_tables_to_csv(self, tables: List[ExtractedTable], output_prefix: str = "table"):
        """Export tables to CSV files"""
        if not PANDAS_AVAILABLE:
            warnings.warn("pandas not available for CSV export")
            return

        for idx, table in enumerate(tables, start=1):
            df = self.table_to_dataframe(table)
            if df is not None:
                filename = f"{output_prefix}_{idx}_{table.title.replace(' ', '_')}.csv"
                df.to_csv(filename, index=False)
                print(f"Exported: {filename}")


# ============================================================================
# Module Information
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python table_extractor.py <path_to_pdf> [device_type]")
        print("\nExample:")
        print("  python table_extractor.py datasheets/IMZA65R020M2H.pdf mosfet")
        sys.exit(1)

    pdf_path = sys.argv[1]
    device_type = sys.argv[2] if len(sys.argv) > 2 else "mosfet"

    extractor = TableExtractor()

    print(f"Extracting tables from: {pdf_path}")
    print(f"Device type: {device_type}\n")

    tables = extractor.extract_tables_from_pdf(pdf_path, device_type)
    extractor.print_tables_summary(tables)

    if device_type == "mosfet":
        params = extractor.extract_mosfet_parameters_from_tables(tables)
    else:
        params = extractor.extract_diode_parameters_from_tables(tables)

    print("\nEXTRACTED PARAMETERS:")
    print("=" * 80)
    for param_name, param_data in params.items():
        print(f"{param_name}:")
        for source, data in param_data.items():
            print(f"  {source}: {data}")
        print()

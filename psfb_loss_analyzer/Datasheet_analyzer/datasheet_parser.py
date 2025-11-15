"""
Automatic Datasheet PDF Parser for SiC MOSFETs and Diodes

Extracts electrical parameters from semiconductor datasheets and converts them
to Python dataclass objects compatible with PSFB Loss Analyzer.

Features:
- PDF text extraction using pdfplumber
- Table detection and parsing
- Parameter pattern matching
- Unit conversion and normalization
- Confidence scoring for extracted values
- Support for SiC MOSFETs and Schottky diodes

Author: PSFB Loss Analysis Tool
Version: 1.0.0
"""

import re
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import warnings

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    warnings.warn("pdfplumber not installed. Install with: pip install pdfplumber")

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Import PSFB analyzer dataclasses
import sys
sys.path.append(str(Path(__file__).parent.parent))

try:
    from circuit_params import (
        MOSFETParameters,
        CapacitanceVsVoltage,
        DiodeParameters,
    )
    from component_library import ComponentMetrics
except ImportError:
    # Fallback for standalone usage
    @dataclass
    class MOSFETParameters:
        part_number: str = ""
        v_dss: float = 0.0
        i_d_continuous: float = 0.0
        r_dson_25c: float = 0.0
        r_dson_25c_max: float = 0.0
        r_dson_150c: float = 0.0
        r_dson_150c_max: float = 0.0
        q_g: float = 0.0
        q_gs: float = 0.0
        q_gd: float = 0.0
        v_gs_plateau: float = 4.5
        t_r: float = 0.0
        t_f: float = 0.0

    @dataclass
    class DiodeParameters:
        part_number: str = ""
        v_rrm: float = 0.0
        i_f_avg: float = 0.0
        v_f0: float = 0.0
        r_f: float = 0.0
        v_f_25c: float = 0.0
        v_f_125c: float = 0.0
        t_rr: float = 0.0
        q_rr: float = 0.0

    @dataclass
    class ComponentMetrics:
        relative_cost: float = 1.0
        availability: str = "Unknown"
        package: str = "Unknown"
        manufacturer: str = "Unknown"


class DeviceType(Enum):
    """Semiconductor device type"""
    SIC_MOSFET = "SiC MOSFET"
    SI_MOSFET = "Si MOSFET"
    SIC_SCHOTTKY = "SiC Schottky"
    SI_PN_DIODE = "Si PN Diode"
    UNKNOWN = "Unknown"


class ConfidenceLevel(Enum):
    """Extraction confidence level"""
    HIGH = 1.0  # Direct table extraction
    MEDIUM = 0.7  # Interpolated or calculated
    LOW = 0.4  # Estimated from similar devices
    PLACEHOLDER = 0.1  # Default value


@dataclass
class ExtractedParameter:
    """Single extracted parameter with metadata"""
    name: str
    value: Any
    unit: str
    confidence: float = 1.0
    source: str = "table"  # "table", "graph", "calculated", "default"
    test_conditions: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""


@dataclass
class ExtractionResult:
    """Complete extraction result for a device"""
    device_type: DeviceType
    part_number: str
    manufacturer: str
    parameters: Dict[str, ExtractedParameter]
    datasheet_path: str
    extraction_date: str
    overall_confidence: float
    warnings: List[str] = field(default_factory=list)
    raw_text: str = ""


class UnitConverter:
    """Unit conversion utilities"""

    @staticmethod
    def to_ohms(value: float, unit: str) -> float:
        """Convert resistance to ohms"""
        unit = unit.lower().strip()
        if 'mω' in unit or 'mohm' in unit or 'milliohm' in unit:
            return value * 1e-3
        elif 'µω' in unit or 'uohm' in unit or 'microohm' in unit:
            return value * 1e-6
        elif 'ω' in unit or 'ohm' in unit:
            return value
        return value

    @staticmethod
    def to_farads(value: float, unit: str) -> float:
        """Convert capacitance to farads"""
        unit = unit.lower().strip()
        if 'pf' in unit or 'picofarad' in unit:
            return value * 1e-12
        elif 'nf' in unit or 'nanofarad' in unit:
            return value * 1e-9
        elif 'µf' in unit or 'uf' in unit or 'microfarad' in unit:
            return value * 1e-6
        elif 'f' in unit and 'farad' in unit:
            return value
        return value

    @staticmethod
    def to_coulombs(value: float, unit: str) -> float:
        """Convert charge to coulombs"""
        unit = unit.lower().strip()
        if 'nc' in unit or 'nanocoulomb' in unit:
            return value * 1e-9
        elif 'µc' in unit or 'uc' in unit or 'microcoulomb' in unit:
            return value * 1e-6
        elif 'mc' in unit or 'millicoulomb' in unit:
            return value * 1e-3
        elif 'c' in unit and 'coulomb' in unit:
            return value
        return value

    @staticmethod
    def to_seconds(value: float, unit: str) -> float:
        """Convert time to seconds"""
        unit = unit.lower().strip()
        if 'ps' in unit or 'picosecond' in unit:
            return value * 1e-12
        elif 'ns' in unit or 'nanosecond' in unit:
            return value * 1e-9
        elif 'µs' in unit or 'us' in unit or 'microsecond' in unit:
            return value * 1e-6
        elif 'ms' in unit or 'millisecond' in unit:
            return value * 1e-3
        elif 's' in unit and 'second' in unit:
            return value
        return value

    @staticmethod
    def to_amperes(value: float, unit: str) -> float:
        """Convert current to amperes"""
        unit = unit.lower().strip()
        if 'ma' in unit or 'milliamp' in unit:
            return value * 1e-3
        elif 'µa' in unit or 'ua' in unit or 'microamp' in unit:
            return value * 1e-6
        elif 'ka' in unit or 'kiloamp' in unit:
            return value * 1e3
        elif 'a' in unit and ('amp' in unit or unit == 'a'):
            return value
        return value

    @staticmethod
    def to_volts(value: float, unit: str) -> float:
        """Convert voltage to volts"""
        unit = unit.lower().strip()
        if 'mv' in unit or 'millivolt' in unit:
            return value * 1e-3
        elif 'µv' in unit or 'uv' in unit or 'microvolt' in unit:
            return value * 1e-6
        elif 'kv' in unit or 'kilovolt' in unit:
            return value * 1e3
        elif 'v' in unit and ('volt' in unit or unit == 'v'):
            return value
        return value


class ParameterPatterns:
    """Regular expression patterns for parameter extraction"""

    # Part number patterns
    PART_NUMBER = [
        r'(?:Part Number|Part No\.|P/N|Device)[:\s]+([A-Z0-9\-]+)',
        r'([A-Z]{2,4}\d{5}[A-Z0-9]*)',  # Generic part number format
        r'(C[23]M\d{7}[A-Z])',  # Wolfspeed pattern
        r'(IM[Z]?[A-Z]\d{2}R\d{3}[A-Z]\d[A-Z])',  # Infineon CoolSiC pattern
    ]

    # Manufacturer patterns
    MANUFACTURER = [
        r'(?:Manufacturer|Company)[:\s]+(Infineon|Wolfspeed|ROHM|STMicroelectronics|OnSemi|ON Semiconductor)',
        r'(?:©|Copyright)[:\s]+(Infineon|Wolfspeed|ROHM|STMicroelectronics|OnSemi)',
    ]

    # MOSFET parameters
    MOSFET_VDSS = [
        r'V[_\s]?DSS[:\s]+(\d+\.?\d*)\s*V',
        r'Drain-Source Voltage[:\s]+(\d+\.?\d*)\s*V',
        r'(?:Maximum|Max\.?)\s+Drain-Source Voltage[:\s]+(\d+\.?\d*)\s*V',
    ]

    MOSFET_ID = [
        r'I[_\s]?D[:\s]+(\d+\.?\d*)\s*A',
        r'Continuous Drain Current[:\s]+(\d+\.?\d*)\s*A',
        r'(?:Maximum|Max\.?)\s+Drain Current[:\s]+(\d+\.?\d*)\s*A',
    ]

    MOSFET_RDSON = [
        r'R[_\s]?DS\(on\)[:\s]+(\d+\.?\d*)\s*(mΩ|mohm|milliohm)',
        r'On-State Resistance[:\s]+(\d+\.?\d*)\s*(mΩ|mohm)',
        r'Static Drain-Source On-Resistance[:\s]+(\d+\.?\d*)\s*(mΩ|mohm)',
    ]

    # Diode parameters
    DIODE_VRRM = [
        r'V[_\s]?RRM[:\s]+(\d+\.?\d*)\s*V',
        r'Repetitive Peak Reverse Voltage[:\s]+(\d+\.?\d*)\s*V',
        r'Maximum Reverse Voltage[:\s]+(\d+\.?\d*)\s*V',
    ]

    DIODE_IF = [
        r'I[_\s]?F[:\s]+(\d+\.?\d*)\s*A',
        r'Average Forward Current[:\s]+(\d+\.?\d*)\s*A',
        r'Forward Current[:\s]+(\d+\.?\d*)\s*A',
    ]

    DIODE_VF = [
        r'V[_\s]?F[:\s]+(\d+\.?\d*)\s*V',
        r'Forward Voltage[:\s]+(\d+\.?\d*)\s*V',
        r'Forward Voltage Drop[:\s]+(\d+\.?\d*)\s*V',
    ]


class DatasheetParser:
    """Main PDF datasheet parser"""

    def __init__(self):
        """Initialize parser"""
        self.converter = UnitConverter()
        self.patterns = ParameterPatterns()

        if not PDFPLUMBER_AVAILABLE and not PYPDF2_AVAILABLE:
            raise ImportError("Neither pdfplumber nor PyPDF2 available. Install with: pip install pdfplumber PyPDF2")

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract all text from PDF"""
        text = ""

        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                return text
            except Exception as e:
                warnings.warn(f"pdfplumber extraction failed: {e}")

        if PYPDF2_AVAILABLE and not text:
            try:
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                return text
            except Exception as e:
                warnings.warn(f"PyPDF2 extraction failed: {e}")

        if not text:
            raise ValueError(f"Failed to extract text from PDF: {pdf_path}")

        return text

    def detect_device_type(self, text: str) -> DeviceType:
        """Detect device type from datasheet text"""
        text_lower = text.lower()

        # SiC MOSFET indicators
        if any(keyword in text_lower for keyword in ['sic mosfet', 'silicon carbide mosfet', 'coolsic']):
            return DeviceType.SIC_MOSFET

        # SiC Schottky diode indicators
        if any(keyword in text_lower for keyword in ['sic schottky', 'silicon carbide schottky', 'sic diode']):
            return DeviceType.SIC_SCHOTTKY

        # Si MOSFET indicators
        if 'mosfet' in text_lower and 'sic' not in text_lower:
            return DeviceType.SI_MOSFET

        # Si PN diode indicators
        if ('diode' in text_lower or 'rectifier' in text_lower) and 'schottky' not in text_lower:
            return DeviceType.SI_PN_DIODE

        return DeviceType.UNKNOWN

    def extract_part_number(self, text: str) -> str:
        """Extract part number from datasheet"""
        for pattern in self.patterns.PART_NUMBER:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "UNKNOWN"

    def extract_manufacturer(self, text: str) -> str:
        """Extract manufacturer from datasheet"""
        for pattern in self.patterns.MANUFACTURER:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Fallback: check for manufacturer names anywhere in first 500 chars
        text_start = text[:500].lower()
        if 'infineon' in text_start:
            return 'Infineon'
        elif 'wolfspeed' in text_start or 'cree' in text_start:
            return 'Wolfspeed'
        elif 'rohm' in text_start:
            return 'ROHM'
        elif 'stmicro' in text_start or 'st micro' in text_start:
            return 'STMicroelectronics'
        elif 'onsemi' in text_start or 'on semiconductor' in text_start:
            return 'OnSemi'

        return "Unknown"

    def extract_value_with_unit(self, text: str, patterns: List[str]) -> Optional[Tuple[float, str]]:
        """Extract numerical value with unit using patterns"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1))
                    unit = match.group(2) if match.lastindex >= 2 else ""
                    return (value, unit)
                except (ValueError, IndexError):
                    continue
        return None

    def extract_mosfet_parameters(self, text: str, part_number: str) -> Dict[str, ExtractedParameter]:
        """Extract MOSFET-specific parameters"""
        params = {}

        # V_DSS
        result = self.extract_value_with_unit(text, self.patterns.MOSFET_VDSS)
        if result:
            value, unit = result
            params['v_dss'] = ExtractedParameter(
                name='v_dss',
                value=self.converter.to_volts(value, unit),
                unit='V',
                confidence=ConfidenceLevel.HIGH.value,
                source='table'
            )

        # I_D
        result = self.extract_value_with_unit(text, self.patterns.MOSFET_ID)
        if result:
            value, unit = result
            params['i_d_continuous'] = ExtractedParameter(
                name='i_d_continuous',
                value=self.converter.to_amperes(value, unit),
                unit='A',
                confidence=ConfidenceLevel.HIGH.value,
                source='table'
            )

        # R_DS(on) - more complex, need to find multiple values at different temperatures
        # This is simplified - real implementation would parse tables
        result = self.extract_value_with_unit(text, self.patterns.MOSFET_RDSON)
        if result:
            value, unit = result
            ohms = self.converter.to_ohms(value, unit)
            params['r_dson_25c'] = ExtractedParameter(
                name='r_dson_25c',
                value=ohms,
                unit='Ω',
                confidence=ConfidenceLevel.MEDIUM.value,
                source='table',
                notes='Assumed from first R_DS(on) value found'
            )

        # Add placeholders for missing critical parameters
        if 'q_g' not in params:
            params['q_g'] = ExtractedParameter(
                name='q_g',
                value=0.0,
                unit='C',
                confidence=ConfidenceLevel.PLACEHOLDER.value,
                source='default',
                notes='Requires manual extraction from gate charge graph'
            )

        return params

    def extract_diode_parameters(self, text: str, part_number: str) -> Dict[str, ExtractedParameter]:
        """Extract diode-specific parameters"""
        params = {}

        # V_RRM
        result = self.extract_value_with_unit(text, self.patterns.DIODE_VRRM)
        if result:
            value, unit = result
            params['v_rrm'] = ExtractedParameter(
                name='v_rrm',
                value=self.converter.to_volts(value, unit),
                unit='V',
                confidence=ConfidenceLevel.HIGH.value,
                source='table'
            )

        # I_F
        result = self.extract_value_with_unit(text, self.patterns.DIODE_IF)
        if result:
            value, unit = result
            params['i_f_avg'] = ExtractedParameter(
                name='i_f_avg',
                value=self.converter.to_amperes(value, unit),
                unit='A',
                confidence=ConfidenceLevel.HIGH.value,
                source='table'
            )

        # V_F
        result = self.extract_value_with_unit(text, self.patterns.DIODE_VF)
        if result:
            value, unit = result
            params['v_f_25c'] = ExtractedParameter(
                name='v_f_25c',
                value=self.converter.to_volts(value, unit),
                unit='V',
                confidence=ConfidenceLevel.MEDIUM.value,
                source='table'
            )

        return params

    def parse_datasheet(self, pdf_path: str) -> ExtractionResult:
        """
        Parse complete datasheet and extract all parameters

        Args:
            pdf_path: Path to PDF datasheet file

        Returns:
            ExtractionResult with all extracted parameters
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Extract text
        text = self.extract_text_from_pdf(pdf_path)

        # Detect device type
        device_type = self.detect_device_type(text)

        # Extract metadata
        part_number = self.extract_part_number(text)
        manufacturer = self.extract_manufacturer(text)

        # Extract parameters based on device type
        if device_type in [DeviceType.SIC_MOSFET, DeviceType.SI_MOSFET]:
            parameters = self.extract_mosfet_parameters(text, part_number)
        elif device_type in [DeviceType.SIC_SCHOTTKY, DeviceType.SI_PN_DIODE]:
            parameters = self.extract_diode_parameters(text, part_number)
        else:
            parameters = {}

        # Calculate overall confidence
        if parameters:
            confidences = [p.confidence for p in parameters.values()]
            overall_confidence = sum(confidences) / len(confidences)
        else:
            overall_confidence = 0.0

        # Collect warnings
        warnings_list = []
        if device_type == DeviceType.UNKNOWN:
            warnings_list.append("Could not determine device type")
        if part_number == "UNKNOWN":
            warnings_list.append("Could not extract part number")
        if overall_confidence < 0.5:
            warnings_list.append("Low extraction confidence - manual review recommended")

        return ExtractionResult(
            device_type=device_type,
            part_number=part_number,
            manufacturer=manufacturer,
            parameters=parameters,
            datasheet_path=pdf_path,
            extraction_date="2025-11-15",
            overall_confidence=overall_confidence,
            warnings=warnings_list,
            raw_text=text[:1000]  # First 1000 chars for debugging
        )

    def to_mosfet_parameters(self, result: ExtractionResult) -> MOSFETParameters:
        """Convert extraction result to MOSFETParameters dataclass"""
        params = result.parameters

        def get_value(name: str, default: float = 0.0) -> float:
            """Helper to get parameter value"""
            if name in params:
                return params[name].value
            return default

        return MOSFETParameters(
            part_number=result.part_number,
            v_dss=get_value('v_dss'),
            i_d_continuous=get_value('i_d_continuous'),
            r_dson_25c=get_value('r_dson_25c'),
            r_dson_25c_max=get_value('r_dson_25c_max', get_value('r_dson_25c') * 1.15),
            r_dson_150c=get_value('r_dson_150c', get_value('r_dson_25c') * 1.4),
            r_dson_150c_max=get_value('r_dson_150c_max', get_value('r_dson_25c') * 1.6),
            q_g=get_value('q_g'),
            q_gs=get_value('q_gs'),
            q_gd=get_value('q_gd'),
            v_gs_plateau=get_value('v_gs_plateau', 4.5),
            t_r=get_value('t_r'),
            t_f=get_value('t_f'),
        )

    def to_diode_parameters(self, result: ExtractionResult) -> DiodeParameters:
        """Convert extraction result to DiodeParameters dataclass"""
        params = result.parameters

        def get_value(name: str, default: float = 0.0) -> float:
            """Helper to get parameter value"""
            if name in params:
                return params[name].value
            return default

        return DiodeParameters(
            part_number=result.part_number,
            v_rrm=get_value('v_rrm'),
            i_f_avg=get_value('i_f_avg'),
            v_f0=get_value('v_f0', 0.8),  # Typical for SiC Schottky
            r_f=get_value('r_f', 0.015),  # Estimated
            v_f_25c=get_value('v_f_25c'),
            v_f_125c=get_value('v_f_125c', get_value('v_f_25c') * 0.85),  # Typical temp coefficient
            t_rr=get_value('t_rr'),
            q_rr=get_value('q_rr'),
        )

    def print_extraction_report(self, result: ExtractionResult):
        """Print formatted extraction report"""
        print("=" * 80)
        print("DATASHEET EXTRACTION REPORT")
        print("=" * 80)
        print(f"Device Type:    {result.device_type.value}")
        print(f"Part Number:    {result.part_number}")
        print(f"Manufacturer:   {result.manufacturer}")
        print(f"Datasheet:      {os.path.basename(result.datasheet_path)}")
        print(f"Confidence:     {result.overall_confidence:.1%}")
        print()

        if result.warnings:
            print("WARNINGS:")
            for warning in result.warnings:
                print(f"  ⚠ {warning}")
            print()

        print("EXTRACTED PARAMETERS:")
        print("-" * 80)
        print(f"{'Parameter':<20} {'Value':<15} {'Unit':<10} {'Confidence':<12} {'Source':<10}")
        print("-" * 80)

        for param_name, param in result.parameters.items():
            value_str = f"{param.value:.3e}" if param.value != 0 else "N/A"
            conf_str = f"{param.confidence:.0%}"
            print(f"{param.name:<20} {value_str:<15} {param.unit:<10} {conf_str:<12} {param.source:<10}")

            if param.notes:
                print(f"  Note: {param.notes}")

        print("=" * 80)


# ============================================================================
# Module Information
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python datasheet_parser.py <path_to_pdf>")
        print("\nExample:")
        print("  python datasheet_parser.py datasheets/IMZA65R020M2H.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    parser = DatasheetParser()
    result = parser.parse_datasheet(pdf_path)
    parser.print_extraction_report(result)

    if result.device_type in [DeviceType.SIC_MOSFET, DeviceType.SI_MOSFET]:
        print("\nMOSFETParameters object:")
        print("-" * 80)
        mosfet = parser.to_mosfet_parameters(result)
        print(f"  Part: {mosfet.part_number}")
        print(f"  V_DSS: {mosfet.v_dss}V")
        print(f"  I_D: {mosfet.i_d_continuous}A")
        print(f"  R_DS(on) @ 25°C: {mosfet.r_dson_25c*1000:.1f}mΩ")
        print(f"  R_DS(on) @ 150°C: {mosfet.r_dson_150c*1000:.1f}mΩ")

    elif result.device_type in [DeviceType.SIC_SCHOTTKY, DeviceType.SI_PN_DIODE]:
        print("\nDiodeParameters object:")
        print("-" * 80)
        diode = parser.to_diode_parameters(result)
        print(f"  Part: {diode.part_number}")
        print(f"  V_RRM: {diode.v_rrm}V")
        print(f"  I_F(avg): {diode.i_f_avg}A")
        print(f"  V_F @ 25°C: {diode.v_f_25c}V")

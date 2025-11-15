"""
Datasheet Analyzer Module

Automatic parameter extraction from SiC MOSFET and diode datasheets.

Features:
- PDF text extraction and parsing
- Table detection and extraction
- Parameter pattern matching
- Unit conversion and normalization
- Batch processing and comparison
- Component library generation

Author: PSFB Loss Analysis Tool
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "PSFB Loss Analysis Tool"

# Import main classes and functions
try:
    from .datasheet_parser import (
        DatasheetParser,
        ExtractionResult,
        ExtractedParameter,
        DeviceType,
        ConfidenceLevel,
        UnitConverter,
    )

    from .table_extractor import (
        TableExtractor,
        ExtractedTable,
    )

    from .batch_processor import (
        BatchProcessor,
        ComparisonReport,
        ComparisonEntry,
    )

    __all__ = [
        # Core parser
        'DatasheetParser',
        'ExtractionResult',
        'ExtractedParameter',
        'DeviceType',
        'ConfidenceLevel',
        'UnitConverter',

        # Table extraction
        'TableExtractor',
        'ExtractedTable',

        # Batch processing
        'BatchProcessor',
        'ComparisonReport',
        'ComparisonEntry',
    ]

except ImportError as e:
    import warnings
    warnings.warn(f"Failed to import Datasheet_analyzer modules: {e}")
    warnings.warn("Install dependencies: pip install pdfplumber pandas")

    __all__ = []

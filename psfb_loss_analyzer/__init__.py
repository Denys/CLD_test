"""
PSFB Loss Analyzer & Optimization Suite

A comprehensive Python-based loss analysis tool for Phase-Shifted Full-Bridge (PSFB)
converters, implementing the methodology from Infineon's "MOSFET Power Losses
Calculation Using the DataSheet Parameters" application note.

Author: PSFB Loss Analysis Tool
Version: 0.1.0 (Input Interface Complete)
"""

__version__ = "0.1.0"
__author__ = "PSFB Loss Analysis Tool"

# Import main classes for easy access
from .circuit_params import (
    PSFBConfiguration,
    CircuitTopology,
    VoltageRange,
    ComponentSet,
    MOSFETParameters,
    CapacitanceVsVoltage,
    TransformerParameters,
    CoreGeometry,
    CoreLossCoefficients,
    CoreMaterial,
    WindingParameters,
    InductorParameters,
    CapacitorParameters,
    DiodeParameters,
    ThermalParameters,
    CoolingMethod,
    OperatingConditions,
    RectifierType,
    validate_configuration,
)

from .config_loader import (
    ConfigurationLoader,
    load_configuration,
)

__all__ = [
    # Main configuration
    'PSFBConfiguration',
    'validate_configuration',

    # Topology
    'CircuitTopology',
    'VoltageRange',
    'OperatingConditions',

    # Components
    'ComponentSet',
    'MOSFETParameters',
    'CapacitanceVsVoltage',
    'DiodeParameters',
    'InductorParameters',
    'CapacitorParameters',

    # Transformer
    'TransformerParameters',
    'CoreGeometry',
    'CoreLossCoefficients',
    'CoreMaterial',
    'WindingParameters',

    # Thermal
    'ThermalParameters',
    'CoolingMethod',

    # Enums
    'RectifierType',

    # Configuration loading
    'ConfigurationLoader',
    'load_configuration',
]

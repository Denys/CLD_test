"""
PSFB Loss Analyzer & Optimization Suite

A comprehensive Python-based loss analysis tool for Phase-Shifted Full-Bridge (PSFB)
converters, implementing the methodology from Infineon's "MOSFET Power Losses
Calculation Using the DataSheet Parameters" application note.

Author: PSFB Loss Analysis Tool
Version: 0.2.0 (MOSFET Loss Calculations Implemented)
"""

__version__ = "0.2.0"
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

from .mosfet_losses import (
    MOSFETCurrentWaveform,
    MOSFETLosses,
    calculate_rdson_at_temp,
    calculate_conduction_loss,
    calculate_miller_time,
    calculate_switching_energy_hard,
    calculate_switching_energy_zvs,
    calculate_switching_loss,
    calculate_gate_drive_loss,
    calculate_mosfet_losses,
    estimate_psfb_primary_waveform,
)

from .core_database import (
    get_core_geometry,
    get_core_loss_coefficients,
    list_available_cores,
)

from .diode_losses import (
    DiodeCurrentWaveform,
    DiodeLosses,
    calculate_forward_voltage,
    calculate_forward_conduction_loss,
    calculate_reverse_recovery_loss,
    calculate_diode_losses,
    estimate_fullbridge_diode_waveform,
    estimate_centertap_diode_waveform,
    verify_diode_ratings,
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

    # MOSFET loss calculations
    'MOSFETCurrentWaveform',
    'MOSFETLosses',
    'calculate_rdson_at_temp',
    'calculate_conduction_loss',
    'calculate_miller_time',
    'calculate_switching_energy_hard',
    'calculate_switching_energy_zvs',
    'calculate_switching_loss',
    'calculate_gate_drive_loss',
    'calculate_mosfet_losses',
    'estimate_psfb_primary_waveform',

    # Core database
    'get_core_geometry',
    'get_core_loss_coefficients',
    'list_available_cores',

    # Diode loss calculations
    'DiodeCurrentWaveform',
    'DiodeLosses',
    'calculate_forward_voltage',
    'calculate_forward_conduction_loss',
    'calculate_reverse_recovery_loss',
    'calculate_diode_losses',
    'estimate_fullbridge_diode_waveform',
    'estimate_centertap_diode_waveform',
    'verify_diode_ratings',
]

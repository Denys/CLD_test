"""
PSFB Loss Analyzer & Optimization Suite

A comprehensive Python-based loss analysis tool for Phase-Shifted Full-Bridge (PSFB)
converters, implementing the methodology from Infineon's "MOSFET Power Losses
Calculation Using the DataSheet Parameters" application note.

Author: PSFB Loss Analysis Tool
Version: 0.3.0 (Magnetic Component Design Implemented)
"""

__version__ = "0.3.0"
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

from .magnetics_design import (
    MagneticDesignSpec,
    MagneticDesignResult,
    WindingDesign,
    WindingType,
    calculate_kg_geometrical_constant,
    calculate_required_kg,
    calculate_kg_fe,
    select_core_by_kg,
    calculate_number_of_turns,
    calculate_wire_diameter,
    calculate_dc_resistance,
    calculate_skin_depth,
    calculate_ac_resistance_dowell,
    design_winding,
    calculate_core_loss_steinmetz,
    estimate_temperature_rise,
    calculate_window_utilization,
)

from .resonant_inductor_design import (
    ZVSRequirements,
    calculate_zvs_inductor_value,
    calculate_inductor_current_waveform,
    design_resonant_inductor,
)

from .transformer_design import (
    TransformerSpec,
    calculate_turns_ratio,
    calculate_magnetizing_inductance,
    estimate_leakage_inductance,
    design_transformer,
)

from .output_inductor_design import (
    OutputInductorSpec,
    calculate_output_inductance,
    calculate_air_gap_length,
    calculate_inductor_current_stress,
    calculate_core_loss_with_dc_bias,
    design_output_inductor,
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

    # Magnetic component design
    'MagneticDesignSpec',
    'MagneticDesignResult',
    'WindingDesign',
    'WindingType',
    'calculate_kg_geometrical_constant',
    'calculate_required_kg',
    'calculate_kg_fe',
    'select_core_by_kg',
    'calculate_number_of_turns',
    'calculate_wire_diameter',
    'calculate_dc_resistance',
    'calculate_skin_depth',
    'calculate_ac_resistance_dowell',
    'design_winding',
    'calculate_core_loss_steinmetz',
    'estimate_temperature_rise',
    'calculate_window_utilization',

    # Resonant inductor design
    'ZVSRequirements',
    'calculate_zvs_inductor_value',
    'calculate_inductor_current_waveform',
    'design_resonant_inductor',

    # Transformer design
    'TransformerSpec',
    'calculate_turns_ratio',
    'calculate_magnetizing_inductance',
    'estimate_leakage_inductance',
    'design_transformer',

    # Output inductor design
    'OutputInductorSpec',
    'calculate_output_inductance',
    'calculate_air_gap_length',
    'calculate_inductor_current_stress',
    'calculate_core_loss_with_dc_bias',
    'design_output_inductor',
]

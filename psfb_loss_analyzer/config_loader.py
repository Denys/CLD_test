"""
Configuration Loader Utility

Provides functions to load PSFB configurations from JSON files
and validate them.

Author: PSFB Loss Analysis Tool
"""

import json
from typing import Optional, List, Tuple
from pathlib import Path

from circuit_params import (
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
)


class ConfigurationLoader:
    """
    Load and validate PSFB configurations from various sources
    """

    @staticmethod
    def from_json_file(filepath: str) -> PSFBConfiguration:
        """
        Load configuration from JSON file

        Args:
            filepath: Path to JSON configuration file

        Returns:
            PSFBConfiguration object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON is malformed or missing required fields
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")

        with open(filepath, 'r') as f:
            data = json.load(f)

        return ConfigurationLoader.from_dict(data)

    @staticmethod
    def from_dict(data: dict) -> PSFBConfiguration:
        """
        Reconstruct PSFBConfiguration from dictionary

        Args:
            data: Dictionary representation of configuration

        Returns:
            PSFBConfiguration object
        """
        # Helper function to convert enum strings back to enums
        def parse_enum(enum_class, value):
            if isinstance(value, str):
                return enum_class(value)
            return value

        # Parse voltage range
        v_in_data = data['topology']['v_in']
        v_in = VoltageRange(
            min=v_in_data['min'],
            nominal=v_in_data['nominal'],
            max=v_in_data['max']
        )

        # Parse topology
        topology = CircuitTopology(
            v_in=v_in,
            v_out=data['topology']['v_out'],
            p_out=data['topology']['p_out'],
            f_sw=data['topology']['f_sw'],
            phase_shift_min=data['topology'].get('phase_shift_min', 0.0),
            phase_shift_max=data['topology'].get('phase_shift_max', 180.0),
            n_phases=data['topology'].get('n_phases', 1),
            dead_time_primary=data['topology'].get('dead_time_primary', 100e-9),
            dead_time_secondary=data['topology'].get('dead_time_secondary', 50e-9),
            transformer_turns_ratio=data['topology'].get('transformer_turns_ratio', 1.0)
        )

        # Parse primary MOSFETs
        primary_data = data['components']['primary_mosfets']
        primary_caps_data = primary_data['capacitances']

        # Parse capacitances
        if 'capacitance_curve' in primary_caps_data and primary_caps_data['capacitance_curve']:
            # Convert list of lists to list of tuples
            curve = [tuple(point) for point in primary_caps_data['capacitance_curve']]
            primary_caps = CapacitanceVsVoltage(capacitance_curve=curve)
        else:
            primary_caps = CapacitanceVsVoltage(
                c_iss_constant=primary_caps_data.get('c_iss_constant'),
                c_oss_constant=primary_caps_data.get('c_oss_constant'),
                c_rss_constant=primary_caps_data.get('c_rss_constant')
            )

        primary_mosfets = MOSFETParameters(
            part_number=primary_data['part_number'],
            v_dss=primary_data['v_dss'],
            i_d_continuous=primary_data['i_d_continuous'],
            r_dson_25c=primary_data['r_dson_25c'],
            r_dson_25c_max=primary_data['r_dson_25c_max'],
            r_dson_150c=primary_data['r_dson_150c'],
            r_dson_150c_max=primary_data['r_dson_150c_max'],
            q_g=primary_data['q_g'],
            q_gs=primary_data['q_gs'],
            q_gd=primary_data['q_gd'],
            v_gs_plateau=primary_data.get('v_gs_plateau', 5.0),
            capacitances=primary_caps,
            t_r=primary_data.get('t_r', 10e-9),
            t_f=primary_data.get('t_f', 10e-9),
            v_sd=primary_data.get('v_sd', 1.0),
            q_rr=primary_data.get('q_rr', 0.0),
            t_rr=primary_data.get('t_rr', 0.0),
            r_th_jc=primary_data.get('r_th_jc', 1.0),
            t_j_max=primary_data.get('t_j_max', 175.0),
            v_gs_drive=primary_data.get('v_gs_drive', 12.0),
            r_g_internal=primary_data.get('r_g_internal', 1.0),
            r_g_external=primary_data.get('r_g_external', 5.0)
        )

        # Parse secondary rectifier
        rectifier_type = parse_enum(
            RectifierType,
            data['components']['secondary_rectifier_type']
        )

        secondary_mosfets = None
        secondary_diodes = None

        if rectifier_type == RectifierType.SYNCHRONOUS_MOSFET:
            sec_data = data['components']['secondary_mosfets']
            sec_caps_data = sec_data['capacitances']

            if 'capacitance_curve' in sec_caps_data and sec_caps_data['capacitance_curve']:
                curve = [tuple(point) for point in sec_caps_data['capacitance_curve']]
                sec_caps = CapacitanceVsVoltage(capacitance_curve=curve)
            else:
                sec_caps = CapacitanceVsVoltage(
                    c_iss_constant=sec_caps_data.get('c_iss_constant'),
                    c_oss_constant=sec_caps_data.get('c_oss_constant'),
                    c_rss_constant=sec_caps_data.get('c_rss_constant')
                )

            secondary_mosfets = MOSFETParameters(
                part_number=sec_data['part_number'],
                v_dss=sec_data['v_dss'],
                i_d_continuous=sec_data['i_d_continuous'],
                r_dson_25c=sec_data['r_dson_25c'],
                r_dson_25c_max=sec_data['r_dson_25c_max'],
                r_dson_150c=sec_data['r_dson_150c'],
                r_dson_150c_max=sec_data['r_dson_150c_max'],
                q_g=sec_data['q_g'],
                q_gs=sec_data['q_gs'],
                q_gd=sec_data['q_gd'],
                v_gs_plateau=sec_data.get('v_gs_plateau', 5.0),
                capacitances=sec_caps,
                t_r=sec_data.get('t_r', 10e-9),
                t_f=sec_data.get('t_f', 10e-9),
                v_sd=sec_data.get('v_sd', 1.0),
                q_rr=sec_data.get('q_rr', 0.0),
                t_rr=sec_data.get('t_rr', 0.0),
                r_th_jc=sec_data.get('r_th_jc', 1.0),
                t_j_max=sec_data.get('t_j_max', 175.0),
                v_gs_drive=sec_data.get('v_gs_drive', 12.0),
                r_g_internal=sec_data.get('r_g_internal', 1.0),
                r_g_external=sec_data.get('r_g_external', 5.0)
            )
        elif 'secondary_diodes' in data['components']:
            diode_data = data['components']['secondary_diodes']
            secondary_diodes = DiodeParameters(
                part_number=diode_data['part_number'],
                v_rrm=diode_data['v_rrm'],
                i_f_avg=diode_data['i_f_avg'],
                v_f0=diode_data.get('v_f0', 0.7),
                r_d=diode_data.get('r_d', 0.01),
                q_rr=diode_data.get('q_rr', 0.0),
                t_rr=diode_data.get('t_rr', 0.0),
                r_th_jc=diode_data.get('r_th_jc', 2.0),
                t_j_max=diode_data.get('t_j_max', 150.0)
            )

        # Parse transformer
        xfmr_data = data['components']['transformer']

        core_geom = CoreGeometry(
            core_type=xfmr_data['core_geometry']['core_type'],
            effective_area=xfmr_data['core_geometry']['effective_area'],
            effective_length=xfmr_data['core_geometry']['effective_length'],
            effective_volume=xfmr_data['core_geometry']['effective_volume'],
            window_area=xfmr_data['core_geometry']['window_area'],
            b_sat=xfmr_data['core_geometry'].get('b_sat', 0.4)
        )

        core_loss = CoreLossCoefficients(
            k=xfmr_data['core_loss_coefficients']['k'],
            alpha=xfmr_data['core_loss_coefficients']['alpha'],
            beta=xfmr_data['core_loss_coefficients']['beta'],
            temperature=xfmr_data['core_loss_coefficients'].get('temperature', 100.0)
        )

        pri_winding = WindingParameters(
            n_turns=xfmr_data['primary_winding']['n_turns'],
            wire_diameter=xfmr_data['primary_winding']['wire_diameter'],
            wire_conductors=xfmr_data['primary_winding'].get('wire_conductors', 1),
            dc_resistance=xfmr_data['primary_winding']['dc_resistance'],
            layers=xfmr_data['primary_winding'].get('layers', 1),
            foil_winding=xfmr_data['primary_winding'].get('foil_winding', False)
        )

        sec_winding = WindingParameters(
            n_turns=xfmr_data['secondary_winding']['n_turns'],
            wire_diameter=xfmr_data['secondary_winding']['wire_diameter'],
            wire_conductors=xfmr_data['secondary_winding'].get('wire_conductors', 1),
            dc_resistance=xfmr_data['secondary_winding']['dc_resistance'],
            layers=xfmr_data['secondary_winding'].get('layers', 1),
            foil_winding=xfmr_data['secondary_winding'].get('foil_winding', False)
        )

        transformer = TransformerParameters(
            core_geometry=core_geom,
            core_material=parse_enum(CoreMaterial, xfmr_data['core_material']),
            core_loss_coefficients=core_loss,
            primary_winding=pri_winding,
            secondary_winding=sec_winding,
            leakage_inductance=xfmr_data['leakage_inductance'],
            magnetizing_inductance=xfmr_data['magnetizing_inductance'],
            isolation_capacitance=xfmr_data.get('isolation_capacitance', 100e-12)
        )

        # Parse inductors and capacitors
        output_inductor = InductorParameters(
            inductance=data['components']['output_inductor']['inductance'],
            dc_resistance=data['components']['output_inductor']['dc_resistance'],
            ac_resistance_100khz=data['components']['output_inductor'].get('ac_resistance_100khz'),
            core_loss_density=data['components']['output_inductor'].get('core_loss_density'),
            core_volume=data['components']['output_inductor'].get('core_volume'),
            current_rating=data['components']['output_inductor'].get('current_rating', 10.0),
            saturation_current=data['components']['output_inductor'].get('saturation_current', 15.0)
        )

        input_cap = CapacitorParameters(
            capacitance=data['components']['input_capacitor']['capacitance'],
            voltage_rating=data['components']['input_capacitor']['voltage_rating'],
            esr=data['components']['input_capacitor'].get('esr', 0.01),
            esl=data['components']['input_capacitor'].get('esl', 10e-9),
            ripple_current_rating=data['components']['input_capacitor'].get('ripple_current_rating', 5.0)
        )

        output_cap = CapacitorParameters(
            capacitance=data['components']['output_capacitor']['capacitance'],
            voltage_rating=data['components']['output_capacitor']['voltage_rating'],
            esr=data['components']['output_capacitor'].get('esr', 0.01),
            esl=data['components']['output_capacitor'].get('esl', 10e-9),
            ripple_current_rating=data['components']['output_capacitor'].get('ripple_current_rating', 5.0)
        )

        # Create component set
        components = ComponentSet(
            primary_mosfets=primary_mosfets,
            secondary_rectifier_type=rectifier_type,
            secondary_mosfets=secondary_mosfets,
            secondary_diodes=secondary_diodes,
            transformer=transformer,
            output_inductor=output_inductor,
            input_capacitor=input_cap,
            output_capacitor=output_cap
        )

        # Parse thermal parameters
        thermal = ThermalParameters(
            t_ambient=data['thermal']['t_ambient'],
            cooling_method=parse_enum(CoolingMethod, data['thermal']['cooling_method']),
            forced_air_cfm=data['thermal'].get('forced_air_cfm', 10.0),
            heatsink_r_th_ca=data['thermal'].get('heatsink_r_th_ca', 5.0),
            thermal_interface_r_th=data['thermal'].get('thermal_interface_r_th', 0.2),
            target_t_j_max=data['thermal'].get('target_t_j_max', 125.0)
        )

        # Parse operating conditions
        operating_point = OperatingConditions(
            load_percentage=data['operating_point']['load_percentage'],
            input_voltage=data['operating_point'].get('input_voltage'),
            output_current=data['operating_point'].get('output_current'),
            phase_shift_angle=data['operating_point'].get('phase_shift_angle', 90.0),
            zvs_achieved_primary=data['operating_point'].get('zvs_achieved_primary', True)
        )

        # Create final configuration
        config = PSFBConfiguration(
            project_name=data['project_name'],
            topology=topology,
            components=components,
            thermal=thermal,
            operating_point=operating_point
        )

        return config

    @staticmethod
    def validate_and_load(filepath: str, verbose: bool = True) -> Tuple[PSFBConfiguration, bool]:
        """
        Load configuration and validate it

        Args:
            filepath: Path to configuration file
            verbose: Print validation results

        Returns:
            Tuple of (configuration, is_valid)
        """
        config = ConfigurationLoader.from_json_file(filepath)

        if verbose:
            print(f"Loaded configuration: {config.project_name}")
            print("-" * 70)

        issues = config.validate()
        is_valid = len(issues) == 0

        if verbose:
            if is_valid:
                print("✓ Configuration validation passed")
            else:
                print("⚠ Configuration validation warnings:")
                for i, issue in enumerate(issues, 1):
                    print(f"  {i}. {issue}")

        return config, is_valid


def load_configuration(filepath: str) -> PSFBConfiguration:
    """
    Convenience function to load a configuration file

    Args:
        filepath: Path to JSON configuration file

    Returns:
        PSFBConfiguration object
    """
    return ConfigurationLoader.from_json_file(filepath)


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python config_loader.py <config_file.json>")
        sys.exit(1)

    config_path = sys.argv[1]

    try:
        config, valid = ConfigurationLoader.validate_and_load(config_path, verbose=True)
        print(config)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

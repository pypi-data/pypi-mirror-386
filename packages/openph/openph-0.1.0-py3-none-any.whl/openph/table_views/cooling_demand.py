# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

from collections.abc import Sequence

from openph_demand.cooling_demand.cooling_demand import OpPhCoolingDemand
from openph_demand.solvers import OpPhGroundSolver
from rich.console import Console
from rich.table import Table

from openph.model import climate, enums


def cooling_demand_peak_month_table(_cooling_demand: OpPhCoolingDemand) -> None:
    """Print out the Cooling Demand PEAK MONTH Table."""

    def _get_value_in_display_format(value: float | int | str, decimal_places=1) -> str:
        try:
            return f"{float(value):,.{decimal_places}f}"
        except (ValueError, TypeError):
            return str(value)

    def _build_row(
        _type_name: str, _unit_: str, _data: Sequence, _decimal_places=2
    ) -> list[str]:
        return [
            _type_name,
            _unit_,
            *[_get_value_in_display_format(_, _decimal_places) for _ in _data],
        ]

    table = Table(title="Peak Month Cooling Demand (PHPP-10 | Cooling | AI81:AO156)")

    # ------------------------------------------------------------------------------------------------------------------
    # -- Setup the Table Headings, Columns
    table.add_column("Type", justify="left")
    table.add_column("Unit", justify="left")
    for period in _cooling_demand.peak_month.periods:
        table.add_column(
            f"{period.period_climate.period_length_days}-Day", justify="right"
        )
    table.add_column("Entire Month", justify="left")

    # ------------------------------------------------------------------------------------------------------------------
    # -- Setup the Table Body
    climate_rows = [
        (
            "82  | Delta-T",
            "C",
            [
                period.period_climate.temperature_difference_C
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "83  | Days",
            "-",
            [
                period.period_climate.period_length_days
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "84  | Outside Temp",
            "C",
            [
                period.period_climate.temperature_air_c
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "85  | Daily Radiation - North",
            "kwh/m2",
            [
                period.period_climate.radiation_north_kwh_m2_day
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "86  | Daily Radiation - East",
            "kwh/m2",
            [
                period.period_climate.radiation_east_kwh_m2_day
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "87  | Daily Radiation - South",
            "kwh/m2",
            [
                period.period_climate.radiation_south_kwh_m2_day
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "88  | Daily Radiation - West",
            "kwh/m2",
            [
                period.period_climate.radiation_west_kwh_m2_day
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "89  | Daily Radiation - Horiz.",
            "kwh/m2",
            [
                period.period_climate.radiation_horizontal_kwh_m2_day
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "90  | Dew Point",
            "C",
            [
                period.period_climate.temperature_dewpoint_c
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "91  | Sky Temp",
            "C",
            [
                period.period_climate.temperature_sky_c
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "92  | Ground Temp.",
            "C",
            [
                period.period_climate.temperature_ground_c
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "93  | Daily Radiation - Opaque",
            "kwh/m2",
            [
                period.period_climate.radiation_opaque_kwh_m2_day
                for period in _cooling_demand.peak_month.periods
            ],
        ),
    ]
    radiation_rows = [
        (
            "102 | Period Radiation - North",
            "kwh/m2",
            [
                period.period_climate.radiation_north_kwh_m2
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "103 | Period Radiation - East",
            "kwh/m2",
            [
                period.period_climate.radiation_east_kwh_m2
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "104 | Period Radiation - South",
            "kwh/m2",
            [
                period.period_climate.radiation_south_kwh_m2
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "105 | Period Radiation - West",
            "kwh/m2",
            [
                period.period_climate.radiation_west_kwh_m2
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "106 | Period Radiation - Horiz.",
            "kwh/m2",
            [
                period.period_climate.radiation_horizontal_kwh_m2
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "107 | Hours / Month",
            "hr",
            [
                period.period_climate.period_length_hours
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
    ]
    degree_hours_rows = [
        (
            "108 | Degree-Hours (Air)",
            "kHr-K",
            [
                period.kilo_degree_hours_ambient_air_kK_hr
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "109 | Degree-Hours (Sky)",
            "kHr-K",
            [
                period.kilo_degree_hours_to_sky_kK_hr
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "110 | Degree-Hours (Ground)",
            "kHr-K",
            [
                period.kilo_degree_hours_to_ground_kK_hr
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "111 | Degree-Hours (EWU)",
            "kHr-K",
            [
                period.kilo_degree_hours_to_EWU_kK_hr
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
    ]
    transmission_losses = [
        (
            "112 | Transmission Losses (Ambient-Air)",
            "kwh",
            [
                period.conductive_heat_loss_to_ambient_air_kwh
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "113 | Transmission Losses (Ground)",
            "kwh",
            [
                period.conductive_heat_loss_to_ground_kwh
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "114 | Transmission Losses (Convective)",
            "kwh",
            [
                period.convective_heat_loss_to_ambient_kwh
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "115 | Transmission Losses (Radiative)",
            "kwh",
            [
                period.radiative_heat_loss_to_sky_kwh
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
    ]
    balanced_vent_losses = [
        (
            "116 | Balanced Vent. Air Temp w/o HR",
            "C",
            [
                period.balanced_mech_vent_supply_air_temperature_without_heat_recovery_C
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "117 | Balanced Vent. Air Dewpoint w/o HR",
            "C",
            [
                period.balanced_mech_vent_supply_air_dew_point_temperature_without_heat_recovery_C
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "118 | Balanced Vent. Air Water Vapor Pressure w/o HR",
            "Pa",
            [
                period.balanced_mech_vent_supply_air_water_vapor_pressure_without_heat_recovery_Pa
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "119 | Balanced Vent. Air Absolute Humidity w/o HR",
            "kg/kg",
            [
                period.balanced_mech_vent_supply_air_absolute_humidity_without_heat_recovery_kg_kg
                for period in _cooling_demand.peak_month.periods
            ],
            4,
        ),
        (
            "120 | Balanced Vent. Air Enthalpy w/o HR",
            "kJ/kg",
            [
                period.balanced_mech_vent_supply_air_enthalpy_without_heat_recovery_kJ_kG
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "121 | Balanced Vent. Air Temp w/ HR",
            "C",
            [
                period.balanced_mech_vent_supply_air_temperature_with_heat_recovery_C
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "122 | Balanced Vent. Air Absolute Humidity w/ HR",
            "kg/kg",
            [
                period.balanced_mech_vent_supply_air_absolute_humidity_with_heat_recovery_kg_kg
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
            4,
        ),
        (
            "123 | Balanced Vent. Air Enthalpy w/ HR",
            "kJ/kg",
            [
                period.balanced_mech_vent_supply_air_enthalpy_with_heat_recovery_kJ_kg
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "124 | WRG/FRG At Target Conditions?",
            "-",
            [
                str(period.balanced_mech_vent_is_supply_air_at_target_indoor_conditions)
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "125 | Balanced Vent. Air Conductance (Ambient-Air)",
            "W/K",
            [
                period.balanced_mech_vent_conductance_to_air_W_K
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "126 | Balanced Vent. Air Conductance (Ground)",
            "W/K",
            [
                period.balanced_mech_vent_conductance_to_soil_W_K
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "127 | Balanced Balanced Vent. Air Mass Flow",
            "kg/hr",
            [
                period.balanced_mech_vent_supply_air_mass_flow_kg_hour
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
    ]
    envelope_vent_losses = [
        (
            "128 | Envelope Vent. Air Mass Flow",
            "kg/hr",
            [
                period.envelope_vent_air_mass_flow_rate_kg_hour
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "129 | Balanced Vent. Losses (Ambient-Air)",
            "kwh",
            [
                period.balanced_mech_vent_heat_loss_to_ambient_air_kwh
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "130 | Balanced Vent. Losses (EWU)",
            "kwh",
            [
                period.balanced_mech_vent_heat_loss_to_ground_kwh
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "131 | Outside Air Water Vapor Pressure",
            "Pa",
            [
                period.period_climate.outdoor_air_water_vapor_pressure_Pa
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "132 | Outside Air Absolute Humidity",
            "kg/kg",
            [
                period.period_climate.outdoor_air_absolute_humidity_kg_kg
                for period in _cooling_demand.peak_month.periods
            ],
            4,
        ),
    ]
    exhaust_vent_losses = [
        (
            "133 | Exhaust Vent. Time Constant",
            "-",
            [
                period.exhaust_mech_vent_time_constant
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "134 | Exhaust Vent. Average Temp.",
            "°C",
            [
                period.exhaust_mech_vent_average_temperature_C
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "135 | Exhaust Vent. Conductance",
            "W/K",
            [
                period.exhaust_mech_vent_thermal_conductance_W_K
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "136 | Exhaust Vent. Total Heat Loss",
            "kwh",
            [
                period.exhaust_mech_vent_total_heat_loss_kwh
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        # -- Envelope (Window) Ventilation
        (
            "137 | Window Vent. Average Temp.",
            "°C",
            [
                period.envelope_vent_air_average_temperature_C
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "138 | Window Vent. Volume Flow",
            "m3/hr",
            [
                period.envelope_vent_air_volume_flow_rate_m3_hour
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "139 | Window Vent. Achievable Conductance",
            "W/K",
            [
                period.envelope_vent_window_achievable_thermal_conductance_W_K
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "140 | Window Vent. Effective Conductance",
            "W/K",
            [
                period.envelope_vent_window_effective_thermal_conductance_W_K
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "141 | Ventilation Losses (Vent. Window)",
            "kwh",
            [
                period.envelope_vent_total_heat_loss_kwh
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
    ]
    heat_gains = [
        (
            "142 | Solar Gain (North)",
            "kwh",
            [
                period.solar_heat_gain_north_windows_kwh
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "143 | Solar Gain (East)",
            "kwh",
            [
                period.solar_heat_gain_east_windows_kwh
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "144 | Solar Gain (South)",
            "kwh",
            [
                period.solar_heat_gain_south_windows_kwh
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "145 | Solar Gain (West)",
            "kwh",
            [
                period.solar_heat_gain_west_windows_kwh
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "146 | Solar Gain (Horiz.)",
            "kwh",
            [
                period.solar_heat_gain_horizontal_windows_kwh
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "147 | Solar Gain (Opaque)",
            "kwh",
            [
                period.solar_heat_gain_opaque_kwh
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "148 | Internal Gain",
            "kwh",
            [
                period.internal_heat_gain_kwh
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
    ]
    results = [
        (
            "149 | Total Heat Loss",
            "kwh",
            [
                period.total_heat_loss_kwh
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "150 | Total Heat Gain",
            "kwh",
            [
                period.total_heat_gain_kwh
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "151 | Time Constant",
            "hours",
            [period.time_constant for period in _cooling_demand.peak_month.periods],
        ),
        (
            "152 | Average Monthly Procedure",
            "-",
            [
                period.monthly_procedure_factor
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "153 | Loss-to-Gain Ratio",
            "%",
            [
                100 * period.loss_to_gain_ratio
                for period in _cooling_demand.peak_month.periods
            ],
        ),
        (
            "154 | Heat loss efficiency",
            "%",
            [
                100 * period.utilization_factor
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "155 | Useful Cooling",
            "kwh",
            [
                period.cooling_demand_kwh
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
        (
            "156 | In Cooling Period?",
            "-",
            [
                "True" if period.in_cooling_period else "False"
                for period in _cooling_demand.peak_month.periods_with_total_monthly
            ],
        ),
    ]

    table_data: list[list[tuple[str, str, list]]] = []
    table_data.append(climate_rows)
    table_data.append(radiation_rows)
    table_data.append(degree_hours_rows)
    table_data.append(transmission_losses)
    table_data.append(balanced_vent_losses)
    table_data.append(envelope_vent_losses)
    table_data.append(exhaust_vent_losses)
    table_data.append(heat_gains)
    table_data.append(results)

    for group in table_data:
        for row in group:
            table.add_row(*_build_row(*row))
        table.add_section()

    # --
    console = Console()
    console.print(table)


def cooling_demand_table(
    _cooling_demand: OpPhCoolingDemand, _ground: OpPhGroundSolver
) -> None:
    """Print out the Cooling Demand Table."""

    def _get_value_in_display_format(value: float | int | str, decimal_places=1) -> str:
        try:
            return f"{float(value):,.{decimal_places}f}"
        except (ValueError, TypeError):
            return str(value)

    def _build_row(
        _type_name: str,
        _unit_: str,
        _data: Sequence[float | int | str],
        _decimal_places=1,
    ) -> list[str]:
        return [
            _type_name,
            _unit_,
            *[_get_value_in_display_format(_, _decimal_places) for _ in _data],
        ]

    table = Table(title="Monthly Cooling Demand (PHPP-10 | Cooling | T102:AE156)")
    opph_climate: climate.OpPhClimate = _cooling_demand.phpp.climate

    # -- Table Headings
    table.add_column("Type", justify="left")
    table.add_column("Unit", justify="left")
    for calc_period in opph_climate.periods:
        table.add_column(calc_period.display_name, justify="right")

    # -- Table Body
    table_data: list[list[tuple]] = [
        [
            ("92 | Ground Temp.", "C", _cooling_demand.temperature_ground_c),
        ],
        [
            (
                "102 | Effective Radiation - North",
                "kwh/m2",
                _cooling_demand.window_surface_period_total_radiation_per_m2_by_orientation(
                    enums.CardinalOrientation.NORTH
                ),
            ),
            (
                "103 | Effective Radiation - East",
                "kwh/m2",
                _cooling_demand.window_surface_period_total_radiation_per_m2_by_orientation(
                    enums.CardinalOrientation.EAST
                ),
            ),
            (
                "104 | Effective Radiation - South",
                "kwh/m2",
                _cooling_demand.window_surface_period_total_radiation_per_m2_by_orientation(
                    enums.CardinalOrientation.SOUTH
                ),
            ),
            (
                "105 | Effective Radiation - West",
                "kwh/m2",
                _cooling_demand.window_surface_period_total_radiation_per_m2_by_orientation(
                    enums.CardinalOrientation.WEST
                ),
            ),
            (
                "106 | Effective Radiation - Horiz.",
                "kwh/m2",
                _cooling_demand.window_surface_period_total_radiation_per_m2_by_orientation(
                    enums.CardinalOrientation.HORIZONTAL
                ),
            ),
            ("107 | Hours / Month", "hr", _cooling_demand.period_hours),
        ],
        [
            (
                "108 | Degree-Hours (Air)",
                "kHr-K",
                opph_climate.cooling_degree_hours_ambient_air,
            ),
            (
                "109 | Degree-Hours (Sky)",
                "kHr-K",
                opph_climate.cooling_degree_hours_sky_kKhr,
            ),
            (
                "110 | Degree-Hours (Ground)",
                "kHr-K",
                _cooling_demand.kilodegree_hours_ground_kK_hr,
            ),
            (
                "111 | Degree-Hours (EWU)",
                "kHr-K",
                _cooling_demand.balanced_mech_vent_kilodegree_hours_ground_heat_exchanger,
            ),
        ],
        [
            (
                "112 | Transmission Losses (Ambient-Air)",
                "kwh",
                _cooling_demand.conductive_heat_loss_to_ambient_air_kwh,
            ),
            (
                "113 | Transmission Losses (Ground)",
                "kwh",
                _cooling_demand.conductive_heat_loss_to_ground_kwh,
            ),
            (
                "114 | Transmission Losses (Convective)",
                "kwh",
                _cooling_demand.convective_heat_loss_to_ambient_kwh,
            ),
            (
                "115 | Transmission Losses (Radiative)",
                "kwh",
                _cooling_demand.radiative_heat_loss_to_sky_kwh,
            ),
            (
                "116 | Balanced Vent. Air Temp w/o HR",
                "C",
                _cooling_demand.balanced_mech_vent_supply_air_temperature_without_heat_recovery_C,
            ),
            (
                "117 | Balanced Vent. Air Dewpoint w/o HR",
                "C",
                _cooling_demand.balanced_mech_vent_supply_air_dew_point_temperature_without_heat_recovery_C,
            ),
            (
                "118 | Balanced Vent. Air Water Vapor Pressure w/o HR",
                "Pa",
                _cooling_demand.balanced_mech_vent_supply_air_water_vapor_pressure_without_heat_recovery_Pa,
            ),
            (
                "119 | Balanced Vent. Air Absolute Humidity w/o HR",
                "kg/kg",
                _cooling_demand.balanced_mech_vent_supply_air_absolute_humidity_without_heat_recovery_kg_kg,
                4,
            ),
            (
                "120 | Balanced Vent. Air Enthalpy w/o HR",
                "kJ/kg",
                _cooling_demand.balanced_mech_vent_supply_air_enthalpy_without_heat_recovery_kJ_kG,
            ),
            (
                "121 | Balanced Vent. Air Temp w/ HR",
                "C",
                _cooling_demand.balanced_mech_vent_supply_air_temperature_with_heat_recovery_C,
            ),
            (
                "122 | Balanced Vent. Air Absolute Humidity w/ HR",
                "kg/kg",
                _cooling_demand.balanced_mech_vent_supply_air_absolute_humidity_with_heat_recovery_kg_kg,
                4,
            ),
            (
                "123 | Balanced Vent. Air Enthalpy w/ HR",
                "kJ/kg",
                _cooling_demand.balanced_mech_vent_supply_air_enthalpy_with_heat_recovery_kJ_kg,
            ),
            (
                "124 | WRG/FRG At Target Conditions?",
                "-",
                [
                    str(_)
                    for _ in _cooling_demand.balanced_mech_vent_is_supply_air_at_target_indoor_conditions
                ],
            ),
            (
                "125 | Balanced Vent. Air Conductance (Ambient-Air)",
                "W/K",
                _cooling_demand.balanced_mech_vent_conductance_to_air_W_K,
            ),
            (
                "126 | Balanced Vent. Air Conductance (Ground)",
                "W/K",
                _cooling_demand.balanced_mech_vent_conductance_to_soil_W_K,
            ),
            (
                "127 | Balanced Balanced Vent. Air Mass Flow",
                "kg/hr",
                _cooling_demand.balanced_mech_vent_supply_air_mass_flow_kg_hour,
            ),
        ],
        # --
        [
            (
                "128 | Envelope Vent. Air Mass Flow",
                "kg/hr",
                _cooling_demand.envelope_vent_air_mass_flow_rate_kg_hour,
            ),
            (
                "129 | Balanced Vent. Losses (Ambient-Air)",
                "kwh",
                _cooling_demand.balanced_mech_vent_heat_loss_to_ambient_air_kwh,
            ),
            (
                "130 | Balanced Vent. Losses (EWU)",
                "kwh",
                _cooling_demand.balanced_mech_vent_heat_loss_to_ground_kwh,
            ),
            (
                "131 | Outside Air Water Vapor Pressure",
                "Pa",
                _cooling_demand.outdoor_air_water_vapor_pressure_Pa,
            ),
            (
                "132 | Outside Air Absolute Humidity",
                "kg/kg",
                _cooling_demand.outdoor_air_absolute_humidity_kg_kg,
                4,
            ),
            # -- Exhaust Ventilation
            (
                "133 | Exhaust Vent. Time Constant",
                "-",
                _cooling_demand.exhaust_mech_vent_time_constant,
            ),
            (
                "134 | Exhaust Vent. Average Temp.",
                "°C",
                _cooling_demand.exhaust_mech_vent_average_temperature_C,
            ),
            (
                "135 | Exhaust Vent. Conductance",
                "W/K",
                _cooling_demand.exhaust_mech_vent_thermal_conductance_W_K,
            ),
            (
                "136 | Exhaust Vent. Total Heat Loss",
                "kwh",
                _cooling_demand.exhaust_mech_vent_total_heat_loss_kwh,
            ),
            # -- Envelope (Window) Ventilation
            (
                "137 | Window Vent. Average Temp.",
                "°C",
                _cooling_demand.envelope_vent_air_average_temperature_C,
            ),
            (
                "138 | Window Vent. Volume Flow",
                "m3/hr",
                _cooling_demand.envelope_vent_air_volume_flow_rate_m3_hour,
            ),
            (
                "139 | Window Vent. Achievable Conductance",
                "W/K",
                _cooling_demand.envelope_vent_window_achievable_thermal_conductance_W_K,
            ),
            (
                "140 | Window Vent. Effective Conductance",
                "W/K",
                _cooling_demand.envelope_vent_window_effective_thermal_conductance_W_K,
            ),
            (
                "141 | Ventilation Losses (Vent. Window)",
                "kwh",
                _cooling_demand.envelope_vent_total_heat_loss_kwh,
            ),
            # --
        ],
        [
            (
                "142 | Solar Gain (North)",
                "kwh",
                _cooling_demand.solar_heat_gain_north_windows_kwh,
            ),
            (
                "143 | Solar Gain (East)",
                "kwh",
                _cooling_demand.solar_heat_gain_east_windows_kwh,
            ),
            (
                "144 | Solar Gain (South)",
                "kwh",
                _cooling_demand.solar_heat_gain_south_windows_kwh,
            ),
            (
                "145 | Solar Gain (West)",
                "kwh",
                _cooling_demand.solar_heat_gain_west_windows_kwh,
            ),
            (
                "146 | Solar Gain (Horiz.)",
                "kwh",
                _cooling_demand.solar_heat_gain_horizontal_windows_kwh,
            ),
            (
                "147 | Solar Gain (Opaque)",
                "kwh",
                _cooling_demand.solar_heat_gain_opaque_kwh,
            ),
            ("148 | Internal Gain", "kwh", _cooling_demand.internal_heat_gain_kwh),
        ],
        [
            ("149 | Total Heat Loss", "kwh", _cooling_demand.total_heat_loss_kwh),
            ("150 | Total Heat Gain", "kwh", _cooling_demand.total_heat_gain_kwh),
        ],
        [
            ("151 | Time Constant", "hours", _cooling_demand.time_constant),
            (
                "152 | Average Monthly Procedure",
                "-",
                _cooling_demand.monthly_procedure_factor,
            ),
            (
                "153 | Loss-to-Gain Ratio",
                "%",
                [_ * 100 for _ in _cooling_demand.loss_to_gain_ratio],
            ),
            (
                "154 | Heat loss efficiency",
                "%",
                [_ * 100 for _ in _cooling_demand.utilization_factor],
            ),
            ("155 | Useful Cooling", "kwh", _cooling_demand.cooling_demand_kwh),
            (
                "156 | In Cooling Period?",
                "-",
                ["True" if _ else "False" for _ in _cooling_demand.in_cooling_period],
            ),
        ],
    ]
    for group in table_data:
        for row in group:
            table.add_row(*_build_row(*row))
        table.add_section()

    console = Console()
    console.print(table)

    console.print("107 | Hours / Day: 24")
    console.print(
        f"108 | Inside Temperature: {_cooling_demand.phpp.set_points.max_interior_temp_c:.1f} °C"
    )
    console.print(
        f"109 | Conductance Transmission total: {_cooling_demand.envelope_total_conductance_W_K:.2f} W/K"
    )
    console.print(
        f"110 | Ground conductivity for time constant: "
        f"{_cooling_demand.envelop_conductance_to_ground_for_time_constant_W_K:.2f} W/K"
    )
    console.print(
        f"111 | Temperature EWU: {_ground.average_ground_surface_temp_C:.2f} °C"
    )
    console.print(
        f"112 | Conductance Factor (Air): {_cooling_demand.envelop_conductance_to_ambient_air_W_K:.2f} W/K"
    )
    console.print(
        f"113 | Conductance Factor (Ground): {_cooling_demand.envelop_conductance_to_ground_W_K:.2f} W/K"
    )
    console.print(
        f"114 | Convective Factor (Air): {_cooling_demand.envelope_convective_factor_W_K:.2f} W/K"
    )
    console.print(
        f"115 | Radiative Factor (Sky): {_cooling_demand.envelope_radiative_factor_W_K:.2f} W/K"
    )
    console.print("- " * 25)
    console.print(
        f"142 | Solar Aperture (North): {_cooling_demand.phpp.areas.windows.north.summer_eff_solar_gain_area_m2:.2f} m2"
    )
    console.print(
        f"143 | Solar Aperture (East): {_cooling_demand.phpp.areas.windows.east.summer_eff_solar_gain_area_m2:.2f} m2"
    )
    console.print(
        f"144 | Solar Aperture (South): {_cooling_demand.phpp.areas.windows.south.summer_eff_solar_gain_area_m2:.2f} m2"
    )
    console.print(
        f"145 | Solar Aperture (West): {_cooling_demand.phpp.areas.windows.west.summer_eff_solar_gain_area_m2:.2f} m2"
    )
    console.print(
        f"146 | Solar Aperture (Horiz.): "
        f"{_cooling_demand.phpp.areas.windows.horizontal.summer_eff_solar_gain_area_m2:.2f} m2"
    )
    console.print("- " * 25)
    console.print(
        f"148 | Internal load: {_cooling_demand.average_annual_internal_heat_gain_W:.2f} W"
    )
    console.print(
        f"149 | Conductance transmission for time constant: {_cooling_demand.conductance_for_time_constant_W_K:.2f} W/K"
    )
    console.print(
        f"150 | Spec. Heat Capacity: {_cooling_demand.specific_heat_capacity_Wh_m2K:.2f} Wh/(m²K)"
    )
    console.print(
        f"151 | Heat Capacity: {_cooling_demand.phpp.areas.heat_capacity_Wh_K:.2f} Wh/K"
    )
    return None


def cooling_demand_opaque_surface_radiation(
    _cooling_demand: OpPhCoolingDemand, _orientation: str
) -> None:
    """Print out the Opaque Surface Radiation (kwh/m2) - Cooling Season."""

    phpp_ranges = {
        "north": "DB41:DL140",
        "east": "EF41:EQ140",
        "south": "CM41:CX140",
        "west": "DQ41:EB140",
    }

    table = Table(
        title=(
            f"Opaque Surface Radiation (kwh/m2) {_orientation.upper()} - Cooling Season "
            f"(PHPP-10 | Areas | {phpp_ranges[_orientation]})"
        )
    )

    # -- Table Headings
    table.add_column("Surface", justify="left")
    table.add_column("Angle From Horizontal (DEG)", justify="left")
    table.add_column("Effective Heat Gain Area (M2)", justify="left")
    for calc_period in _cooling_demand.phpp.climate.periods:
        table.add_column(calc_period.display_name, justify="right")

    # -- Table Body
    transposed = list(
        map(
            list,
            zip(
                *getattr(
                    _cooling_demand,
                    f"opaque_surface_radiation_{_orientation.lower()}",
                )
            ),
        )
    )
    for surface, data in zip(_cooling_demand.phpp.areas.opaque_surfaces, transposed):
        table.add_row(
            surface.display_name,
            f"{surface.angle_from_horizontal:.1f}",
            f"{surface.heat_gain.summer.eff_heat_gain_area_m2: .3f}",
            *[f"{i:,.1f}" for i in data],
        )

    console = Console()
    console.print(table)


def cooling_demand_window_surface_radiation(
    _cooling_demand: OpPhCoolingDemand, _orientation: str
) -> None:
    """Print out the Window Surface Radiation (kwh/m2) - Cooling Season."""

    phpp_ranges = {
        "north": "GX23:HI174",
        "east": "IH23:IS174",
        "south": "GF23:GQ174",
        "west": "HP23:IA174",
        "total": "IZ23:JK174",
    }

    table = Table(
        title=(
            f"Window Surface Radiation (kwh/m2) {_orientation.upper()} - Cooling Season "
            f"(PHPP-10 | Windows | {phpp_ranges[_orientation]})"
        )
    )

    # -- Table Headings
    table.add_column("Surface", justify="left")
    table.add_column("Angle From Horizontal (DEG)", justify="left")
    table.add_column("Orientation", justify="left")
    for calc_period in _cooling_demand.phpp.climate.periods:
        table.add_column(calc_period.display_name, justify="right")

    # -- Table Body
    transposed = list(
        map(
            list,
            zip(
                *getattr(
                    _cooling_demand,
                    f"window_surface_radiation_{_orientation.lower()}",
                )
            ),
        )
    )
    for window, data in zip(_cooling_demand.phpp.areas.windows, transposed):
        table.add_row(
            window.display_name,
            f"{window.angle_from_horizontal:.1f}",
            f"{window.cardinal_orientation_name}",
            *[f"{i:,.1f}" for i in data],
        )

    console = Console()
    console.print(table)


def cooling_demand_window_total_radiation(_cooling_demand: OpPhCoolingDemand) -> None:
    """Print out the Window TOTAL Radiation (kwh/m2) by Orientation - Cooling Season."""

    table = Table(
        title="Window Surface TOTAL Radiation (kwh/m2) - Cooling Season (PHPP-10 | Windows | GF6:GQ10 )"
    )

    # -- Table Headings
    table.add_column("Surface", justify="left")
    table.add_column("Glazing Area (m2)", justify="left")
    for calc_period in _cooling_demand.phpp.climate.periods:
        table.add_column(calc_period.display_name, justify="right")

    for orientation in enums.CardinalOrientation:
        aperture_group = _cooling_demand.phpp.areas.aperture_surfaces.by_orientation(
            orientation
        )
        table.add_row(
            orientation.name,
            f"{aperture_group.total_glazing_area_m2:.1f}",
            *[
                f"{i:,.1f}"
                for i in _cooling_demand.window_surface_period_total_radiation_per_m2_by_orientation(
                    orientation
                )
            ],
        )

    console = Console()
    console.print(table)


def cooling_demand_opaque_area_heat_gains(_cooling_demand: OpPhCoolingDemand) -> None:
    table = Table(
        title="Total Effective Solar Heat Gain - Cooling Season (PHPP-10 | Areas | CP5:DA10)"
    )

    # -- Table Headings
    table.add_column("Surface", justify="left")
    for calc_period in _cooling_demand.phpp.climate.periods:
        table.add_column(calc_period.display_name, justify="right")

    # -- Table Body
    table.add_row(
        "Opaque-Surfaces",
        *[f"{i:,.1f}" for i in _cooling_demand.opaque_surface_radiation_total],
    )
    table.add_row(
        "Thermal-Bridges",
        *[
            f"{i:,.1f}"
            for i in _cooling_demand.total_thermal_bridge_solar_gain_by_period_kwh
        ],
    )
    table.add_row(
        "Window-Frames",
        *[
            f"{i:,.1f}"
            for i in _cooling_demand.total_window_frame_solar_gain_by_period_kwh
        ],
    )
    table.add_row(
        "Total",
        *[
            f"{i:,.1f}"
            for i in _cooling_demand.total_opaque_element_solar_gain_by_period_kwh
        ],
    )

    console = Console()
    console.print(table)

# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

from collections.abc import Sequence

from openph_demand.heating_demand.heating_demand import OpPhHeatingDemand
from openph_demand.solvers import OpPhGroundSolver
from rich.console import Console
from rich.table import Table

from openph.model import climate, enums


def heating_demand_table(
    _heating_demand: OpPhHeatingDemand, _ground: OpPhGroundSolver
) -> None:
    """Print out the Heating Demand Table."""

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

    table = Table(title="Monthly Heating Demand (PHPP-10 | Heating | T90:AG118)")
    opph_climate: climate.OpPhClimate = _heating_demand.phpp.climate

    # -- Table Headings
    table.add_column("Type", justify="left")
    table.add_column("Unit", justify="left")
    for calc_period in opph_climate.periods:
        table.add_column(calc_period.display_name, justify="right")

    # -- Table Body
    table_data: list[list[tuple]] = [
        [
            (
                "91  | Effective Radiation - North",
                "kwh/m2",
                _heating_demand.get_window_surface_period_total_radiation_per_m2_for_orientation(
                    enums.CardinalOrientation.NORTH
                ),
            ),
            (
                "92  | Effective Radiation - East",
                "kwh/m2",
                _heating_demand.get_window_surface_period_total_radiation_per_m2_for_orientation(
                    enums.CardinalOrientation.EAST
                ),
            ),
            (
                "93  | Effective Radiation - South",
                "kwh/m2",
                _heating_demand.get_window_surface_period_total_radiation_per_m2_for_orientation(
                    enums.CardinalOrientation.SOUTH
                ),
            ),
            (
                "94  | Effective Radiation - West",
                "kwh/m2",
                _heating_demand.get_window_surface_period_total_radiation_per_m2_for_orientation(
                    enums.CardinalOrientation.WEST
                ),
            ),
            (
                "95  | Effective Radiation - Horiz.",
                "kwh/m2",
                _heating_demand.get_window_surface_period_total_radiation_per_m2_for_orientation(
                    enums.CardinalOrientation.HORIZONTAL
                ),
            ),
            ("96  | Hours / Month", "hr", _heating_demand.period_hours),
        ],
        [
            ("97  | Degree-Hours (Air)", "kHr-K", _heating_demand.kilodegree_hours_air),
            ("98  | Degree-Hours (Sky)", "kHr-K", _heating_demand.kilodegree_hours_sky),
            (
                "99  | Degree-Hours (Ground)",
                "kHr-K",
                _heating_demand.kilodegree_hours_ground,
            ),
            (
                "100 | Degree-Hours (EWU)",
                "kHr-K",
                _heating_demand.kilodegree_hours_EWU,
            ),
        ],
        [
            (
                "101 | Transmission Losses (Ambient-Air)",
                "kwh",
                _heating_demand.transmission_heat_loss_to_ambient,
            ),
            (
                "102 | Transmission Losses (Ground)",
                "kwh",
                _heating_demand.transmission_heat_loss_to_ground,
            ),
            (
                "103 | Transmission Losses (EWU)",
                "kwh",
                _heating_demand.convective_heat_loss_to_EWU,
            ),
            (
                "104 | Convective Losses to Ambient",
                "kwh",
                _heating_demand.convective_heat_loss_to_ambient,
            ),
            (
                "105 | Radiative Losses to Sky",
                "kwh",
                _heating_demand.radiative_heat_loss_to_sky,
            ),
        ],
        [
            (
                "106 | North Window Solar Gain",
                "kwh",
                _heating_demand.north_window_solar_heat_gain,
            ),
            (
                "107 | East Window Solar Gain",
                "kwh",
                _heating_demand.east_window_solar_heat_gain,
            ),
            (
                "108 | South Window Solar Gain",
                "kwh",
                _heating_demand.south_window_solar_heat_gain,
            ),
            (
                "109 | West Window Solar Gain",
                "kwh",
                _heating_demand.west_window_solar_heat_gain,
            ),
            (
                "110 | Hori. Window Solar Gain",
                "kwh",
                _heating_demand.horizontal_window_solar_heat_gain,
            ),
            (
                "111 | Opaque Surface Solar Gain",
                "kwh",
                _heating_demand.opaque_surface_solar_heat_gain,
            ),
            ("112 | Internal Heat Gain", "kwh", _heating_demand.internal_heat_gain),
        ],
        [
            ("113 | Total Heat Loss", "kwh", _heating_demand.total_heat_losses),
            ("114 | Total Heat Gain", "kwh", _heating_demand.total_heat_gains),
            (
                "115 | Gains / Losses",
                "%",
                [_ * 100 for _ in _heating_demand.gain_to_loss_ratio],
            ),
            (
                "116 | Utilization Factor",
                "%",
                [_ * 100 for _ in _heating_demand.utilization_factor],
            ),
            ("117 | Heating Demand", "kwh", _heating_demand.heating_demand),
            (
                "118 | In Heating Period?",
                "-",
                ["True" if _ else "False" for _ in _heating_demand.in_heating_period],
            ),
        ],
    ]
    for group in table_data:
        for row in group:
            table.add_row(*_build_row(*row))
        table.add_section()

    console = Console()
    console.print(table)

    console.print("-" * 25)
    console.print("96 | Hours / Day: 24")
    console.print("-" * 25)
    console.print(
        f"98  | Interior Temp [C]: {_heating_demand.phpp.set_points.min_interior_temp_c:.2f}"
    )
    console.print(f"99  | Ground Temp [C]: {_ground.average_ground_surface_temp_C:.2f}")
    console.print(
        f"100 | Conductivity to Ground [W/K]: {_heating_demand.ground_conductivity_for_time_constant:.2f}"
    )
    console.print(
        f"101 | Conductance Factor to Air [W/K]: {_heating_demand.conductance_factor_to_outdoor_air:.2f}"
    )
    console.print(
        f"102 | Conductance Factor to Ground [W/K]: {_heating_demand.conductance_factor_to_ground:.2f}"
    )
    console.print(
        f"103 | Conductance Factor to EWU [W/K]: {_heating_demand.conductance_factor_to_EWU:.2f}"
    )
    console.print(
        f"104 | Convection Factor [W/K]: {_heating_demand.convection_factor_W_K:.2f}"
    )
    console.print(
        f"105 | Radiation Factor [W/K]: {_heating_demand.radiation_factor_W_K:.2f}"
    )
    console.print("-" * 25)
    console.print(
        f"106 | North Window Area [M2]: {_heating_demand.north_effective_window_area_m2:.2f}"
    )
    console.print(
        f"107 | East Window Area [M2]: {_heating_demand.east_effective_window_area_m2:.2f}"
    )
    console.print(
        f"108 | South Window Area [M2]: {_heating_demand.south_effective_window_area_m2:.2f}"
    )
    console.print(
        f"109 | West Window Area [M2]: {_heating_demand.west_effective_window_area_m2:.2f}"
    )
    console.print(
        f"110 | Hori. Window Area [M2]: {_heating_demand.horizontal_effective_window_area_m2:.2f}"
    )
    console.print("-" * 25)
    console.print(
        f"112 | Internal Heat Gains [W]: {_heating_demand.internal_heat_gain_rate_W:.2f}"
    )
    console.print(
        f"113 | Specific Heat Capacity [Wh/M2-K]: {_heating_demand.specific_heat_capacity_Wh_m2K:.2f}"
    )
    console.print(
        f"114 | Heat Capacity [Wh/K]: {_heating_demand.heat_capacity_Wh_K:.2f}"
    )

    return None

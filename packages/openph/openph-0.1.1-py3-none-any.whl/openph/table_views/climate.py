# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Functions for Printing out the PHPP | Climate | Calculation-Step Tables."""

from collections.abc import Sequence
from typing import Any

from rich.console import Console
from rich.table import Table

from openph.model.climate import (
    OpPhClimate,
    OpPhClimatePeakCoolingLoad,
    OpPhClimatePeakHeatingLoad,
)


def annual_climate_data_table(_climate: OpPhClimate) -> None:
    """Print out the Climate Data Table."""

    def _build_row(_type_name, _data: Sequence[float | int]) -> list[str]:
        return [
            _type_name,
            *[f"{float(_):,.1f}" for _ in _data],
        ]

    table = Table(title="Climate Data (PHPP-10 | Climate | E26:P33)")
    table.add_column("Type", justify="left")
    for calc_period in _climate.periods:
        table.add_column(calc_period.display_name, justify="right")

    table.add_row(*_build_row("24 | Period Days", _climate.period_days))
    table.add_row(*_build_row("26 | Exterior Temperature", _climate.temperature_air_c))
    table.add_row(
        *_build_row("27 | Radiation - North", _climate.radiation_north_kwh_m2)
    )
    table.add_row(*_build_row("28 | Radiation - East", _climate.radiation_east_kwh_m2))
    table.add_row(
        *_build_row("29 | Radiation - South", _climate.radiation_south_kwh_m2)
    )
    table.add_row(*_build_row("30 | Radiation - West", _climate.radiation_west_kwh_m2))
    table.add_row(
        *_build_row("31 | Radiation - Hori", _climate.radiation_global_kwh_m2)
    )
    table.add_row(
        *_build_row("32 | Dew-point Temperature", _climate.temperature_dewpoint_C)
    )
    table.add_row(*_build_row("33 | Sky Temperature", _climate.temperature_sky_c))
    table.add_section()
    table.add_row(
        *_build_row(
            "42 | Share of Max Loss to Cover",
            _climate.share_of_maximum_losses_to_be_covered,
        )
    )
    table.add_row(*_build_row("42 | HT-Factor", _climate.h_t_factor))

    console = Console()
    console.print(table)
    console.print(f"K9 | Heating Period Days: {_climate.heating_period_days:0.1f}")
    console.print(f"K10 | Heating Gt: {_climate.heating_degree_hours:0.1f}")

    return None


def peak_load_climate_data_table(_climate: OpPhClimate) -> None:
    def render_value(_value: Any) -> str:
        try:
            return f"{float(_value):,.2f}"
        except Exception:
            return str(_value)

    def _build_row(
        _type_name: str, _unit: str, _data: Sequence[float | int | None]
    ) -> list[str]:
        return [
            _type_name,
            _unit,
            *[render_value(_) for _ in _data],
        ]

    table = Table(title="Peak Load Climate Data (PHPP-10 | Climate | Q23:T36)")

    table.add_column("Type", justify="left")
    table.add_column("Unit", justify="right")
    table.add_column("Heating - 1", justify="right")
    table.add_column("Heating - 2", justify="right")
    table.add_column("Cooling - 1", justify="right")
    table.add_column("Cooling - 2", justify="right")

    periods: list[OpPhClimatePeakCoolingLoad | OpPhClimatePeakHeatingLoad] = [
        _climate.peak_heating_1,
        _climate.peak_heating_2,
        _climate.peak_cooling_1,
        _climate.peak_cooling_2,
    ]

    table_data = [
        [
            ("26 | Exterior Temperature", "C", [p.temperature_air_c for p in periods]),
            (
                "27 | Radiation - North",
                "kwh/m2",
                [p.radiation_north_kwh_m2 for p in periods],
            ),
            (
                "28 | Radiation - East",
                "kwh/m2",
                [p.radiation_east_kwh_m2 for p in periods],
            ),
            (
                "29 | Radiation - South",
                "kwh/m2",
                [p.radiation_south_kwh_m2 for p in periods],
            ),
            (
                "30 | Radiation - West",
                "kwh/m2",
                [p.radiation_west_kwh_m2 for p in periods],
            ),
            (
                "31 | Radiation - Hori",
                "kwh/m2",
                [p.radiation_horizontal_kwh_m2 for p in periods],
            ),
            (
                "32 | Dew-point Temperature",
                "C",
                [p.temperature_dewpoint_c for p in periods],
            ),
            ("33 | Sky Temperature", "C", [p.temperature_sky_c for p in periods]),
            ("35 | Ground Temperature", "C", [p.temperature_ground_c for p in periods]),
        ],
    ]

    for group in table_data:
        for row in group:
            table.add_row(*_build_row(*row))
        table.add_section()

    console = Console()
    console.print(table)
    return None


def radiation_factors_table(_climate: OpPhClimate) -> None:
    """Print out the Radiation Factors Table."""

    def _build_row(_type_name, _data: Sequence[float | int]) -> list[str]:
        return [
            _type_name,
            *[f"{float(_):,.2f}" for _ in _data],
        ]

    table = Table(title="Radiation Factors (PHPP-10 | Windows | FN11:FY19)")

    table.add_column("Type", justify="left")
    for calc_period in _climate.periods:
        table.add_column(calc_period.display_name, justify="right")

    table_data = [
        [("Radiation (Ground)", [p.f_ground for p in _climate.periods])],
        [
            ("East-West", []),
            ("A0", [p.f_EW_A0 for p in _climate.periods]),
            ("A1", [p.f_EW_A1 for p in _climate.periods]),
            ("A2", [p.f_EW_A2 for p in _climate.periods]),
            ("B1", [p.f_EW_B1 for p in _climate.periods]),
        ],
        [
            ("North-South", []),
            ("A0", [p.f_NS_A0 for p in _climate.periods]),
            ("A1", [p.f_NS_A1 for p in _climate.periods]),
            ("A2", [p.f_NS_A2 for p in _climate.periods]),
        ],
        [
            ("alpha", [p.f_alpha for p in _climate.periods]),
        ],
    ]

    for group in table_data:
        for row in group:
            table.add_row(*_build_row(*row))
        table.add_section()

    console = Console()
    console.print(table)
    console.print(f"Exponent: {_climate.periods[0].EXPONENT:0.1f}")
    console.print(f"Rad. (pi/180): {_climate.periods[0].RAD:0.3f} ")
    console.print(f"Albedo: {_climate.periods[0].GROUND_ALBEDO:0.3f}")
    return None

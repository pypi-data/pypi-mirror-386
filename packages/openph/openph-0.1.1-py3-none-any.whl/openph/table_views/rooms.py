# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Functions for Printing out the PHPP | Addl Vent | Rooms."""

import textwrap

from rich.console import Console
from rich.table import Table

from openph.model.rooms import OpPhRooms


def _get_nested_attr(s, a: str):
    """Return nested attribute from an object.

    ie: "heat_gain.summer.non_perpendicular_radiation" -> s.heat_gain.summer.non_perpendicular_radiation
    """
    attrs = a.split(".")
    for attr in attrs:
        s = getattr(s, attr)
    return s


def room_ventilation_properties(_ph_rooms: OpPhRooms) -> None:
    table = Table(title="Room Ventilation Properties (PHPP-10 | Addl Vent | C56:M85)")

    plot_data: dict[str, tuple[str, str]] = {
        "Name": ("display_name", ""),
        "Gross Floor Area (M2)": ("floor_area_m2", ",.1f"),
        "TFA Factor": ("weighting_factor", ".1f"),
        "TFA (M2)": ("weighted_floor_area_m2", ".1f"),
        "Height (M)": ("clear_height_m", ".1f"),
        "Vn50 (M3)": ("net_volume_m3", ",.1f"),
        "Vv (M3)": ("ventilated_volume_m3", ",.1f"),
        "V_sup (m3/h)": ("ventilation.load.supply_airflow_m3_h", ",.1f"),
        "V_eta (m3/h)": ("ventilation.load.exhaust_airflow_m3_h", ",.1f"),
        "V_trans (m3/h)": ("ventilation.load.transfer_airflow_m3_h", ",.1f"),
        "Room ACH": ("ventilation_design_ach", ",.2f"),
    }
    for item in plot_data.keys():
        table.add_column(textwrap.fill(item, width=15), justify="center", no_wrap=True)

    for rooms in _ph_rooms.rooms_by_ventilation_device.values():
        for room in rooms:
            table.add_row(
                *[f"{_get_nested_attr(room, _[0]):{_[1]}}" for _ in plot_data.values()]
            )
        table.add_section()

    console = Console()
    console.print(table)
    return None


def room_ventilation_schedule(_ph_rooms: OpPhRooms) -> None:
    table = Table(title="Room Ventilation Schedule (PHPP-10 | Addl Vent | N56:Z85)")

    plot_data: dict[str, tuple[str, str]] = {
        "Name": ("display_name", ""),
        "H/d": ("ventilation.schedule.operating_hours", ""),
        "d/week": ("ventilation.schedule.operating_days", ""),
        "holidays/year": ("ventilation.schedule.holiday_days", ""),
        "Reduction Factor 1": (
            "ventilation.schedule.operating_periods.high.period_operation_speed",
            ".1%",
        ),
        "Operation Factor 1": (
            "ventilation.schedule.operating_periods.high.period_operating_percentage",
            ".1%",
        ),
        "Reduction Factor 2": (
            "ventilation.schedule.operating_periods.standard.period_operation_speed",
            ".1%",
        ),
        "Operation Factor 2": (
            "ventilation.schedule.operating_periods.standard.period_operating_percentage",
            ".1%",
        ),
        "Reduction Factor 3": (
            "ventilation.schedule.operating_periods.basic.period_operation_speed",
            ".1%",
        ),
        "Operation Factor 3": (
            "ventilation.schedule.operating_periods.basic.period_operating_percentage",
            ".1%",
        ),
        "Reduction Factor 4": (
            "ventilation.schedule.operating_periods.minimum.period_operation_speed",
            ".1%",
        ),
        "Operation Factor 4": (
            "ventilation.schedule.operating_periods.minimum.period_operating_percentage",
            ".1%",
        ),
        "Annual Avg. V_Sup (m3/h)": ("average_annual_supply_airflow_rate_m3_h", ",.1f"),
        "Annual Avg. V_Eta (m3/h)": (
            "average_annual_exhaust_airflow_rate_m3_h",
            ",.1f",
        ),
        "Annual Avg. V_Trans (m3/h)": (
            "average_annual_transfer_airflow_rate_m3_h",
            ",.1f",
        ),
        "Room ACH": ("average_annual_ach", ",.2f"),
    }
    for item in plot_data.keys():
        table.add_column(textwrap.fill(item, width=15), justify="center", no_wrap=True)

    for rooms in _ph_rooms.rooms_by_ventilation_device.values():
        for room in rooms:
            table.add_row(
                *[f"{_get_nested_attr(room, _[0]):{_[1]}}" for _ in plot_data.values()]
            )
        table.add_section()

    console = Console()
    console.print(table)
    return None

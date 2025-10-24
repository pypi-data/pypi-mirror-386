# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Functions for Printing out the PHPP | Addl Vent | Duct Calculations."""

import textwrap

from rich.console import Console
from rich.table import Table

from openph.model.hvac.hvac import OpPhHVAC


def _get_nested_attr(s, a: str):
    """Return nested attribute from an object.

    ie: "heat_gain.summer.non_perpendicular_radiation" -> s.heat_gain.summer.non_perpendicular_radiation
    """
    attrs = a.split(".")
    for attr in attrs:
        s = getattr(s, attr)
    return s


def ventilation_duct_inputs(_ph_hvac: OpPhHVAC) -> None:
    table = Table(title="Duct Input Properties (PHPP-10 | Addl Vent | E127:L146)")

    supply_duct_data: dict[str, tuple[str, str]] = {
        "Unit": ("display_name", ""),
        "Type": ("ducting.supply_ducting.duct_type.name", ""),
        "Diameter [MM]": ("ducting.supply_ducting.diameter_mm", ".1f"),
        "Width [MM]": ("ducting.supply_ducting.width_mm", ".1f"),
        "Height [MM]": ("ducting.supply_ducting.height_mm", ".1f"),
        "Insulation Thickness [MM]": (
            "ducting.supply_ducting.insulation_thickness_mm",
            ".1f",
        ),
        "Insulation Conductivity [Wmk]": (
            "ducting.supply_ducting.insulation_conductivity_w_mk",
            ".1f",
        ),
        "Insulation Reflective?": ("ducting.supply_ducting.insulation_reflective", ""),
        "Duct Conductance [W/mk]?": ("ducting.supply_ducting.conductance_w_m_k", ".3f"),
        "Length [M]": ("ducting.supply_ducting.length_m", ".1f"),
    }
    exhaust_duct_data: dict[str, tuple[str, str]] = {
        "Unit": ("display_name", ""),
        "Type": ("ducting.exhaust_ducting.duct_type.name", ""),
        "Diameter [MM]": ("ducting.exhaust_ducting.diameter_mm", ".1f"),
        "Width [MM]": ("ducting.exhaust_ducting.width_mm", ".1f"),
        "Height [MM]": ("ducting.exhaust_ducting.height_mm", ".1f"),
        "Insulation Thickness [MM]": (
            "ducting.exhaust_ducting.insulation_thickness_mm",
            ".1f",
        ),
        "Insulation Conductivity [Wmk]": (
            "ducting.exhaust_ducting.insulation_conductivity_w_mk",
            ".1f",
        ),
        "Insulation Reflective?": ("ducting.exhaust_ducting.insulation_reflective", ""),
        "Duct Conductance [W/mk]?": (
            "ducting.exhaust_ducting.conductance_w_m_k",
            ".3f",
        ),
        "Length [M]": ("ducting.exhaust_ducting.length_m", ".1f"),
    }

    for item in supply_duct_data.keys():
        table.add_column(item, justify="center", no_wrap=True)

    for d in _ph_hvac.ventilation_system.device_collection.devices:
        table.add_row(
            *[f"{_get_nested_attr(d, _[0]):{_[1]}}" for _ in supply_duct_data.values()]
        )
        table.add_row(
            *[f"{_get_nested_attr(d, _[0]):{_[1]}}" for _ in exhaust_duct_data.values()]
        )
        table.add_section()

    console = Console()
    console.print(table)
    return None


def ventilation_duct_results(_ph_hvac: OpPhHVAC) -> None:
    table = Table(
        title="Duct Calculated Properties (PHPP-10 | Addl Vent | AM127:BE146)"
    )

    supply_duct_data: dict[str, tuple[str, str]] = {
        "Unit": ("display_name", ""),
        "Type": ("ducting.supply_ducting.duct_type.name", ""),
        "Heat Loss Coeff. (W/K)": (
            "ducting.supply_ducting.heat_loss_coefficient_W_K",
            ".3f",
        ),
        "Duct Coeff.": ("ducting.supply_ducting.duct_coefficient", ".3f"),
        "Avg. Airflow (m3/h)": (
            "ducting.supply_ducting.average_annual_airflow_rate_m3_h",
            ".1f",
        ),
        "Duct Type": ("ducting.supply_ducting.duct_type_number", ""),
        "Approx. Diameter (MM)": (
            "ducting.supply_ducting.hydraulic_diameter_mm",
            ".1f",
        ),
        "Equiv. Diameter (MM)": (
            "ducting.supply_ducting.equivalent_diameter_mm",
            ".1f",
        ),
        "Outer Diam without Insul. (MM)": (
            "ducting.supply_ducting.outer_diameter_without_insulation_mm",
            ".1f",
        ),
        "Nusselt Number": ("ducting.supply_ducting.nusselt_number_takeover", ".1f"),
        "Temp. Diff. DJ": ("ducting.supply_ducting.temperature_difference_DJ", ".1f"),
        "Outer Diam without Insul. (M)": (
            "ducting.supply_ducting.outer_diameter_without_insulation_m",
            ".3f",
        ),
        "Outer Diam with Insul. (M)": (
            "ducting.supply_ducting.outer_diameter_with_insulation_m",
            ".3f",
        ),
        "Alpha Inside": ("ducting.supply_ducting.alpha_inside", ".2f"),
        "Alpha Surface": ("ducting.supply_ducting.alpha_surface", ".2f"),
    }
    exhaust_duct_data: dict[str, tuple[str, str]] = {
        "Unit": ("display_name", ""),
        "Type": ("ducting.exhaust_ducting.duct_type.name", ""),
        "Heat Loss Coeff. (W/K)": (
            "ducting.exhaust_ducting.heat_loss_coefficient_W_K",
            ".3f",
        ),
        "Duct Coeff.": ("ducting.exhaust_ducting.duct_coefficient", ".3f"),
        "Avg. Airflow (m3/h)": (
            "ducting.exhaust_ducting.average_annual_airflow_rate_m3_h",
            ".1f",
        ),
        "Duct Type": ("ducting.exhaust_ducting.duct_type_number", ""),
        "Approx. Diameter (MM)": (
            "ducting.exhaust_ducting.hydraulic_diameter_mm",
            ".1f",
        ),
        "Equiv. Diameter (MM)": (
            "ducting.exhaust_ducting.equivalent_diameter_mm",
            ".1f",
        ),
        "Outer Diam without Insul. (MM)": (
            "ducting.exhaust_ducting.outer_diameter_without_insulation_mm",
            ".1f",
        ),
        "Nusselt Number": ("ducting.exhaust_ducting.nusselt_number_takeover", ".1f"),
        "Temp. Diff. DJ": ("ducting.exhaust_ducting.temperature_difference_DJ", ".1f"),
        "Outer Diam without Insul. (M)": (
            "ducting.exhaust_ducting.outer_diameter_without_insulation_m",
            ".3f",
        ),
        "Outer Diam with Insul. (M)": (
            "ducting.exhaust_ducting.outer_diameter_with_insulation_m",
            ".3f",
        ),
        "Alpha Inside": ("ducting.exhaust_ducting.alpha_inside", ".2f"),
        "Alpha Surface": ("ducting.exhaust_ducting.alpha_surface", ".2f"),
    }

    for item in supply_duct_data.keys():
        table.add_column(textwrap.fill(item, width=15), justify="center", no_wrap=True)

    for d in _ph_hvac.ventilation_system.device_collection.devices:
        table.add_row(
            *[f"{_get_nested_attr(d, _[0]):{_[1]}}" for _ in supply_duct_data.values()]
        )
        table.add_row(
            *[f"{_get_nested_attr(d, _[0]):{_[1]}}" for _ in exhaust_duct_data.values()]
        )
        table.add_section()

    console = Console()
    console.print(table)
    return None


def ventilation_duct_iterative_solver(_ph_hvac: OpPhHVAC) -> None:
    table = Table(
        title="Duct Iterative Solver Results (PHPP-10 | Addl Vent | BI127:BT146)"
    )

    supply_duct_data: dict[str, tuple[str, str]] = {
        "Unit": ("display_name", ""),
        "Type": ("ducting.supply_ducting.duct_type.name", ""),
        "(1)\na-Approx. (W/K)": (
            "ducting.supply_ducting.alpha_approximation_iteration_1",
            ".3f",
        ),
        "(1)\nk-Approx. (W/mk)": (
            "ducting.supply_ducting.thermal_transmittance_approximation_iteration_1",
            ".3f",
        ),
        "(1)\nTemp-Difference (K)": (
            "ducting.supply_ducting.surface_temperature_difference_iteration_1",
            ".3f",
        ),
        "(2)\na-Approx. (W/K)": (
            "ducting.supply_ducting.alpha_approximation_iteration_2",
            ".3f",
        ),
        "(2)\nk-Approx. (W/mk)": (
            "ducting.supply_ducting.thermal_transmittance_approximation_iteration_2",
            ".3f",
        ),
        "(2)\nTemp-Difference (K)": (
            "ducting.supply_ducting.surface_temperature_difference_iteration_2",
            ".3f",
        ),
        "(3)\na-Approx. (W/K)": (
            "ducting.supply_ducting.alpha_approximation_iteration_3",
            ".3f",
        ),
        "(3)\nk-Approx. (W/mk)": (
            "ducting.supply_ducting.thermal_transmittance_approximation_iteration_3",
            ".3f",
        ),
        "(3)\nTemp-Difference (K)": (
            "ducting.supply_ducting.surface_temperature_difference_iteration_3",
            ".3f",
        ),
        "(4)\na-Approx. (W/K)": (
            "ducting.supply_ducting.alpha_approximation_iteration_4",
            ".3f",
        ),
        "(4)\nk-Approx. (W/mk)": (
            "ducting.supply_ducting.thermal_transmittance_approximation_iteration_4",
            ".3f",
        ),
        "(4)\nTemp-Difference (K)": (
            "ducting.supply_ducting.surface_temperature_difference_iteration_4",
            ".3f",
        ),
        "(5)\na-Approx. (W/K)": (
            "ducting.supply_ducting.alpha_approximation_iteration_5",
            ".3f",
        ),
        "(5)\nk-Approx. (W/mk)": (
            "ducting.supply_ducting.thermal_transmittance_approximation_iteration_5",
            ".3f",
        ),
        "(5)\nTemp-Difference (K)": (
            "ducting.supply_ducting.surface_temperature_difference_iteration_5",
            ".3f",
        ),
    }
    exhaust_duct_data: dict[str, tuple[str, str]] = {
        "Unit": ("display_name", ""),
        "Type": ("ducting.exhaust_ducting.duct_type.name", ""),
        "(1)\na-Approx. (W/K)": (
            "ducting.exhaust_ducting.alpha_approximation_iteration_1",
            ".3f",
        ),
        "(1)\nk-Approx. (W/mk)": (
            "ducting.exhaust_ducting.thermal_transmittance_approximation_iteration_1",
            ".3f",
        ),
        "(1)\nTemp-Difference (K)": (
            "ducting.exhaust_ducting.surface_temperature_difference_iteration_1",
            ".3f",
        ),
        "(2)\na-Approx. (W/K)": (
            "ducting.exhaust_ducting.alpha_approximation_iteration_2",
            ".3f",
        ),
        "(2)\nk-Approx. (W/mk)": (
            "ducting.exhaust_ducting.thermal_transmittance_approximation_iteration_2",
            ".3f",
        ),
        "(2)\nTemp-Difference (K)": (
            "ducting.exhaust_ducting.surface_temperature_difference_iteration_2",
            ".3f",
        ),
        "(3)\na-Approx. (W/K)": (
            "ducting.exhaust_ducting.alpha_approximation_iteration_3",
            ".3f",
        ),
        "(3)\nk-Approx. (W/mk)": (
            "ducting.exhaust_ducting.thermal_transmittance_approximation_iteration_3",
            ".3f",
        ),
        "(3)\nTemp-Difference (K)": (
            "ducting.exhaust_ducting.surface_temperature_difference_iteration_3",
            ".3f",
        ),
        "(4)\na-Approx. (W/K)": (
            "ducting.exhaust_ducting.alpha_approximation_iteration_4",
            ".3f",
        ),
        "(4)\nk-Approx. (W/mk)": (
            "ducting.exhaust_ducting.thermal_transmittance_approximation_iteration_4",
            ".3f",
        ),
        "(4)\nTemp-Difference (K)": (
            "ducting.exhaust_ducting.surface_temperature_difference_iteration_4",
            ".3f",
        ),
        "(5)\na-Approx. (W/K)": (
            "ducting.exhaust_ducting.alpha_approximation_iteration_5",
            ".3f",
        ),
        "(5)\nk-Approx. (W/mk)": (
            "ducting.exhaust_ducting.thermal_transmittance_approximation_iteration_5",
            ".3f",
        ),
        "(5)\nTemp-Difference (K)": (
            "ducting.exhaust_ducting.surface_temperature_difference_iteration_5",
            ".3f",
        ),
    }

    for item in supply_duct_data.keys():
        table.add_column(textwrap.fill(item, width=15), justify="center", no_wrap=True)

    for d in _ph_hvac.ventilation_system.device_collection.devices:
        table.add_row(
            *[f"{_get_nested_attr(d, _[0]):{_[1]}}" for _ in supply_duct_data.values()]
        )
        table.add_row(
            *[f"{_get_nested_attr(d, _[0]):{_[1]}}" for _ in exhaust_duct_data.values()]
        )
        table.add_section()

    console = Console()
    console.print(table)
    return None


def ventilation_duct_nusselt_number_calcs(_ph_hvac: OpPhHVAC) -> None:
    table = Table(
        title="Duct Nusselt Number Results (PHPP-10 | Addl Vent | BU127:CA146)"
    )

    supply_duct_data: dict[str, tuple[str, str]] = {
        "Unit": ("display_name", ""),
        "Type": ("ducting.supply_ducting.duct_type.name", ""),
        "Airflow Velocity [Rect Ducts]": (
            "ducting.supply_ducting.air_velocity_rectangular_m_s",
            ".3f",
        ),
        "Reynolds Number [Rect Ducts]": (
            "ducting.supply_ducting.reynolds_number_rectangular",
            ",.3f",
        ),
        "Nusselt Number [Rect Ducts]": (
            "ducting.supply_ducting.nusselt_number_rectangular",
            ".3f",
        ),
        "Airflow Velocity [Round Ducts]": (
            "ducting.supply_ducting.air_velocity_round_m_s",
            ".3f",
        ),
        "Reynolds Number [Round Ducts]": (
            "ducting.supply_ducting.reynolds_number_round",
            ",.3f",
        ),
        "Nusselt Number [Round Ducts]": (
            "ducting.supply_ducting.nusselt_number_round",
            ".3f",
        ),
        "Duct R-Value (mk/W)": (
            "ducting.supply_ducting.insulation_thermal_resistance_per_m",
            ".3f",
        ),
    }
    exhaust_duct_data: dict[str, tuple[str, str]] = {
        "Unit": ("display_name", ""),
        "Type": ("ducting.exhaust_ducting.duct_type.name", ""),
        "Airflow Velocity [Rect Ducts]": (
            "ducting.exhaust_ducting.air_velocity_rectangular_m_s",
            ".3f",
        ),
        "Reynolds Number [Rect Ducts]": (
            "ducting.exhaust_ducting.reynolds_number_rectangular",
            ",.3f",
        ),
        "Nusselt Number [Rect Ducts]": (
            "ducting.exhaust_ducting.nusselt_number_rectangular",
            ".3f",
        ),
        "Airflow Velocity [Round Ducts]": (
            "ducting.exhaust_ducting.air_velocity_round_m_s",
            ".3f",
        ),
        "Reynolds Number [Round Ducts]": (
            "ducting.exhaust_ducting.reynolds_number_round",
            ",.3f",
        ),
        "Nusselt Number [Round Ducts]": (
            "ducting.exhaust_ducting.nusselt_number_round",
            ".3f",
        ),
        "Duct R-Value (mk/W)": (
            "ducting.exhaust_ducting.insulation_thermal_resistance_per_m",
            ".3f",
        ),
    }

    for item in supply_duct_data.keys():
        table.add_column(textwrap.fill(item, width=15), justify="center", no_wrap=True)

    for d in _ph_hvac.ventilation_system.device_collection.devices:
        table.add_row(
            *[f"{_get_nested_attr(d, _[0]):{_[1]}}" for _ in supply_duct_data.values()]
        )
        table.add_row(
            *[f"{_get_nested_attr(d, _[0]):{_[1]}}" for _ in exhaust_duct_data.values()]
        )
        table.add_section()

    console = Console()
    console.print(table)
    return None

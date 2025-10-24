# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Functions for Printing out the PHPP | Areas | Calculation-Step Tables."""

from typing import Any

from rich.console import Console
from rich.table import Table

from openph.model.areas import (
    OpPhApertureSurface,
    OpPhAreas,
    OpPhOpaqueSurface,
    OpPhPhvelopeSurfaceGroup,
)
from openph.model.enums import Season


def _get_nested_attr(s: OpPhOpaqueSurface | OpPhApertureSurface, a: str) -> Any:
    """Return nested attribute from an object.

    ie: "heat_gain.summer.non_perpendicular_radiation" -> s.heat_gain.summer.non_perpendicular_radiation
    """
    attrs = a.split(".")
    for attr in attrs:
        s = getattr(s, attr)
    return s


def opaque_surface_attributes_table(_ph_energy_areas: OpPhAreas) -> None:
    """Print out the Opaque Surface Attributes Table."""

    table = Table(title="Opaque Surface Attributes (PHPP-10 | Areas | L41:AJ140)")

    data: dict[str, tuple[str, str]] = {
        "ID.": ("id_num", "03d"),
        "Name": ("display_name", ""),
        "Quan.": ("quantity", ""),
        "Exposure": ("exposure_exterior.name", ""),
        "Type": ("face_type.name", ""),
        "Gross Area\n(m2)": ("area_m2", ",.1f"),
        "Net Area\n(m2)": ("net_area_m2", ",.1f"),
        "Construction Type": ("construction.display_name", ""),
        "U-Value\n(W/m2K)": ("u_value_W_m2_k", ".3f"),
        "Deg. from\nNorth": ("cardinal_orientation_angle", ".1f"),
        "Deg. from\nHoriz.": ("angle_from_horizontal", ".1f"),
        "Orientation": ("cardinal_orientation_name", ""),
    }

    for item in data.keys():
        table.add_column(item, justify="center", no_wrap=True)

    for s in _ph_energy_areas._opaque_surface_list:
        surface_data = [f"{_get_nested_attr(s, _[0]):{_[1]}}" for _ in data.values()]
        table.add_row(*surface_data)

    console = Console()
    console.print(table)
    return None


def opaque_surface_heat_gain_table(_ph_energy_areas: OpPhAreas) -> None:
    """Print out the Opaque Surface Heat Gain Table. Areas | L41:BU140"""

    table = Table(title="Opaque Surface Heat Gain (PHPP-10 | Areas | L41:BU140)")

    data: dict[str, tuple[str, str]] = {
        "ID.": ("id_num", "03d"),
        "Name": ("display_name", ""),
        "Shading\nFactor": ("heat_gain.winter.shading_factor", ".2f"),
        "Ext.\nAbsorptance": ("absorptance", ".2f"),
        "Ext.\nEmissivity": ("emissivity", ".2f"),
        "Conductance Fac.\n(W/K)": ("heat_loss_factor_W_K", ".2f"),
        "BR | \u03b1-Sky": ("heat_gain.winter.alpha_sky", ".2f"),
        "BS | \u03b1-Air": ("heat_gain.winter.alpha_air", ".2f"),
        "BT | Radiative Fac.\n(W/K)": ("heat_gain.winter.radiative_factor_W_K", ".2f"),
        "BU | Convective Fac.\n(W/K)": (
            "heat_gain.winter.convective_factor_W_K",
            ".2f",
        ),
    }

    for item in data.keys():
        table.add_column(item, justify="center", no_wrap=True)

    for s in _ph_energy_areas._opaque_surface_list:
        surface_data = [f"{_get_nested_attr(s, _[0]):{_[1]}}" for _ in data.values()]
        table.add_row(*surface_data)

    console = Console()
    console.print(table)
    return None


def area_summary_table(_ph_energy_areas: OpPhAreas) -> None:
    """Print out the Area Summary Table."""

    table = Table(title="Areas Summary (PHPP-10 | Areas | K6:P29)")

    for data in [
        ("Group Type", "left"),
        ("Area\n(m2)", "center"),
        ("Avg. U-Value\n(W/m2K)", "center"),
    ]:
        table.add_column(data[0], justify=data[1], no_wrap=True)

    def build_row(_surface_group: OpPhPhvelopeSurfaceGroup) -> list[str]:
        return [
            f"{_surface_group.area_m2:.1f}",
            f"{_surface_group.average_u_value:.3f}",
        ]

    table.add_row("Windows - North", *build_row(_ph_energy_areas.windows.north))
    table.add_row("Windows - East", *build_row(_ph_energy_areas.windows.east))
    table.add_row("Windows - South", *build_row(_ph_energy_areas.windows.south))
    table.add_row("Windows - West", *build_row(_ph_energy_areas.windows.west))
    table.add_row("Windows - West", *build_row(_ph_energy_areas.windows.horizontal))
    table.add_row(
        "Ext Wall - Ambient", *build_row(_ph_energy_areas.all_walls.above_grade)
    )
    table.add_row(
        "Ext Wall - Ground", *build_row(_ph_energy_areas.all_walls.below_grade)
    )
    table.add_row(
        "Roof / Ceiling - Ambient", *build_row(_ph_energy_areas.all_roofs.above_grade)
    )
    table.add_row(
        "Floor Slab / Basement Ceiling",
        *build_row(_ph_energy_areas.all_floors.below_grade),
    )

    console = Console()
    console.print(table)
    return None


def aperture_surfaces_table(_ph_energy_areas: OpPhAreas) -> None:
    """Print out the Aperture Surface Attributes Table."""

    table = Table(title="Window Surface Attributes (PHPP-10 | Windows | L23:BA174)")

    data: dict[str, tuple[str, str]] = {
        "ID.": ("id_num", "03d"),
        "Quan.": ("quantity", ""),
        "Name": ("display_name", ""),
        "Deg. from\nNorth": ("cardinal_orientation_angle", ".1f"),
        "Deg. from\nHoriz.": ("angle_from_horizontal", ".1f"),
        "Orientation": ("cardinal_orientation_name", ""),
        "Width\n(m)": ("width_m", ".1f"),
        "Height\n(m)": ("height_m", ".1f"),
        "Glass Type": ("construction.glazing_type_display_name", ""),
        "Frame Type": ("construction.frame_type_display_name", ""),
        "Win. Area\n(m2)": ("area_m2", ",.1f"),
        "Glazing Area\n(m2)": ("glazing_area_m2", ".2f"),
        "Frame Area\n(m2)": ("frame_area_m2", ".2f"),
        "U-W-Installed\n(W/m2K)": ("u_value_wm2k", ".3f"),
    }

    for item in data.keys():
        table.add_column(item, justify="center", no_wrap=True)

    for s in _ph_energy_areas.windows:
        surface_data = [f"{_get_nested_attr(s, _[0]):{_[1]}}" for _ in data.values()]
        table.add_row(*surface_data)

    console = Console()
    console.print(table)
    return None


def aperture_surface_heat_gain_attribute_table(_ph_energy_areas: OpPhAreas) -> None:
    """Print out the Aperture Frame Heat Gain Table."""

    table = Table(title="Window Heat Gain Attributes (PHPP-10 | Windows | JR23:JX174)")

    data: dict[str, tuple[str, str]] = {
        "ID.": ("id_num", "03d"),
        "Name": ("display_name", ""),
        "U-Value\n(W/m2K)": ("u_value_wm2k", ".3f"),
        "Frame\nEff. Heating Area\n(m2)": (
            "heat_gain.winter.eff_heat_gain_area_m2",
            ".4f",
        ),
        "Sky-View Fac.\n(-)": ("heat_gain.winter.sky_view", ".3f"),
        "\u03b1-Sky\n(W/m2K)": ("heat_gain.winter.alpha_sky", ".3f"),
        "\u03b1-Air\n(W/m2K)": ("heat_gain.winter.alpha_air", ".3f"),
        "Radiative Fac.\n(W/K)": ("heat_gain.winter.radiative_factor_W_K", ".3f"),
        "Convective Fac.\n(W/K)": ("heat_gain.winter.convective_factor_W_K", ".3f"),
    }

    for item in data.keys():
        table.add_column(item, justify="center")

    for s in _ph_energy_areas.windows:
        surface_data = [f"{_get_nested_attr(s, _[0]):{_[1]}}" for _ in data.values()]
        table.add_row(*surface_data)

    console = Console()
    console.print(table)
    return None


def aperture_seasonal_solar_reduction_factors(
    _ph_energy_areas: OpPhAreas, _season: Season
) -> None:
    """Print out the Aperture Seasonal Solar Reduction Factors Table."""

    table = Table(
        title=f"Window {_season.name.capitalize()} Solar Reduction Factors (PHPP-10 | Windows | L___:BA____)"
    )

    data: dict[str, tuple[str, str]] = {
        "ID.": ("id_num", "03d"),
        "Quan.": ("quantity", ""),
        "Name": ("display_name", ""),
        "g-Value\n(%)": ("g_value", ".3f"),
        "Dirt\n(%)": (f"heat_gain.{_season.name.lower()}.dirt", ".3f"),
        "Non-Perpendicular Radiation\n(%)": (
            f"heat_gain.{_season.name.lower()}.non_perpendicular_radiation",
            ".3f",
        ),
        "Shading\n(%)": (f"heat_gain.{_season.name.lower()}.shading_factor", ".3f"),
        f"{_season.name.capitalize()} Reduction Fac.\n(%)": (
            f"heat_gain.{_season.name.lower()}.total_reduction_factor",
            ".3f",
        ),
    }

    for item in data.keys():
        table.add_column(item, justify="center", no_wrap=True)

    for s in _ph_energy_areas.windows:
        surface_data = [f"{_get_nested_attr(s, _[0]):{_[1]}}" for _ in data.values()]
        table.add_row(*surface_data)

    console = Console()
    console.print(table)
    return None

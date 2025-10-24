# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

""" "Functions for Printing out the PHPP | Ground | Calculation-Step Tables."""

from collections.abc import Sequence

from openph_demand.solvers import OpPhGroundSolver
from rich.console import Console
from rich.table import Table

from openph.model import climate


def ground_table(_ground: OpPhGroundSolver) -> None:
    """Print out the Ground Table."""

    def _build_row(_type_name, _data: Sequence[float | int]) -> list[str]:
        return [
            _type_name,
            *[f"{float(_):,.2f}" for _ in _data],
        ]

    table = Table(title="Ground (PHPP-10 | Ground | E123:P200)")
    opph_climate: climate.OpPhClimate = _ground.phpp.climate

    # -- Table Headings
    table.add_column("Type", justify="left")
    for calc_period in opph_climate.periods:
        table.add_column(calc_period.display_name, justify="right")

    # -- Table Body
    table.add_row(*_build_row("112 | Heat Flow", _ground.total_heat_flow_to_ground_w))
    table.add_row(
        *_build_row("123 | Month", [_ for _ in range(1, len(_ground.periods) + 1)])
    )

    for iteration in _ground.iterations:
        table.add_section()
        table.add_row(
            *_build_row(
                "Summer Heat Supply to Ground [W]",
                [p.summer_heat_flow_to_ground_w for p in iteration.periods],
            )
        )
        table.add_row(
            *_build_row(
                "Ground Temp: Winter [C]",
                [p.winter_ground_temp for p in iteration.periods],
            )
        )
        table.add_row(
            *_build_row(
                "Ground Temp: Summer [C]",
                [p.summer_ground_temp for p in iteration.periods],
            )
        )
        table.add_row(
            *_build_row(
                "Air Temp: [C]", [p.interior_air_temp for p in iteration.periods]
            )
        )
        table.add_row(*_build_row("Q-pi [1]", [p.q_pi for p in iteration.periods]))
        table.add_row(*_build_row("Q-ges [1]", [p.q_ges for p in iteration.periods]))

    console = Console()
    console.print(table)
    console.print(f"P09 | Indoor Temp - Winter [C]: {_ground.min_interior_temp_c:.2f}")
    console.print(f"P10 | Indoor Temp - Summer [C]: {_ground.max_interior_temp_c:.2f}")
    console.print(
        f"P11 | Average Ground Surface Temp [C]: {_ground.average_ground_surface_temp_C:.2f}"
    )
    console.print(
        f"P12 | Amplitude - theta_e_m [C]: {_ground.amplitude_theta_e_m_deg_C:.2f}"
    )
    console.print(
        f"P13 | Phase Shift - theta_e: {_ground.phase_shift_theta_e_Months:.2f}"
    )
    console.print(
        f"P14 | Length of Heating Period: {_ground.heating_period_length:.2f}"
    )
    console.print(f"P15 | Heating Degree Hours: {_ground.heating_degree_hours:.2f}")
    return None

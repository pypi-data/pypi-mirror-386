# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Functions for Printing out the PHPP Calculation-Step Tables."""

from typing import Callable

from rich import print

from .areas import *
from .climate import *
from .cooling_demand import *
from .ground import *
from .heating_demand import *
from .rooms import *
from .ventilation import *


def add_divider(f: Callable) -> Callable[..., None]:
    def wrapper(*args, **kwargs) -> None:
        print("[green bold]" + " -" * 85 + "[/green bold]")
        f(*args, **kwargs)

    return wrapper


opaque_surface_attributes_table = add_divider(opaque_surface_attributes_table)
opaque_surface_heat_gain_table = add_divider(opaque_surface_heat_gain_table)
area_summary_table = add_divider(area_summary_table)
aperture_surfaces_table = add_divider(aperture_surfaces_table)
aperture_surface_heat_gain_attribute_table = add_divider(
    aperture_surface_heat_gain_attribute_table
)
aperture_seasonal_solar_reduction_factors = add_divider(
    aperture_seasonal_solar_reduction_factors
)
annual_climate_data_table = add_divider(annual_climate_data_table)
radiation_factors_table = add_divider(radiation_factors_table)
ground_table = add_divider(ground_table)
cooling_demand_table = add_divider(cooling_demand_table)
ventilation_duct_inputs = add_divider(ventilation_duct_inputs)
ventilation_duct_results = add_divider(ventilation_duct_results)
ventilation_duct_iterative_solver = add_divider(ventilation_duct_iterative_solver)
ventilation_duct_nusselt_number_calcs = add_divider(
    ventilation_duct_nusselt_number_calcs
)
room_ventilation_properties = add_divider(room_ventilation_properties)
room_ventilation_schedule = add_divider(room_ventilation_schedule)

# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Settings Dataclasses."""

from dataclasses import dataclass


@dataclass
class OpPhSetPoints:
    min_interior_temp_c: float = 20.0
    max_interior_temp_c: float = 25.0
    max_absolute_humidity: float = 12  # g/kg

# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHPP Mechanical System Collection."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from openph.phpp import OpPhPHPP

from openph.model.hvac.hot_water import OpPhHotWaterSystem
from openph.model.hvac.ventilation_system import OpPhVentilationSystem


@dataclass
class OpPhHVAC:
    phpp: "OpPhPHPP"
    ventilation_system: OpPhVentilationSystem = field(init=False)
    hot_water_system: OpPhHotWaterSystem = field(init=False)

    def __post_init__(self):
        self.ventilation_system = OpPhVentilationSystem(phpp=self.phpp)
        self.hot_water_system = OpPhHotWaterSystem(phpp=self.phpp)

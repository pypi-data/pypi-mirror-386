# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHPP Hot-Water System and Devices."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from openph.phpp import OpPhPHPP


@dataclass
class OpPhHotWaterSystem:
    phpp: "OpPhPHPP"

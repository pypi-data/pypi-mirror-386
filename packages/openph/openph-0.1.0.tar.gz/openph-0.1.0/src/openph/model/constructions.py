# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""OpPh Opaque and Aperture Constructions."""

import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class OpPhConstructionOpaque:
    identifier: str = field(default_factory=lambda: str(uuid.uuid4()))
    id_num: int = 0
    display_name: str = ""
    u_value: float = 1.0  # W/m2k


@dataclass(frozen=True)
class OpPhWindowFrameElement:
    width: float = 0.1  # m
    u_value: float = 1.0  # W/m2k
    psi_glazing: float = 0.00  # W/mk
    psi_install: float = 0.00  # W/mk


@dataclass(frozen=True)
class OpPhGlazing:
    identifier: str = field(default_factory=lambda: str(uuid.uuid4()))
    id_num: int = 0
    display_name: str = ""
    u_value: float = 1.0
    g_value: float = 0.4


@dataclass(frozen=True)
class OpPhConstructionAperture:
    identifier: str = field(default_factory=lambda: str(uuid.uuid4()))
    id_num: int = 0
    display_name: str = ""
    glazing_type_display_name: str = ""
    frame_type_display_name: str = ""

    glazing: OpPhGlazing = field(default_factory=OpPhGlazing)
    frame_top: OpPhWindowFrameElement = field(default_factory=OpPhWindowFrameElement)
    frame_bottom: OpPhWindowFrameElement = field(default_factory=OpPhWindowFrameElement)
    frame_left: OpPhWindowFrameElement = field(default_factory=OpPhWindowFrameElement)
    frame_right: OpPhWindowFrameElement = field(default_factory=OpPhWindowFrameElement)

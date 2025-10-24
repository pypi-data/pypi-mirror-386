# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""OpPhPHPP Top-Level Dataclass to organize all PHPP elements / worksheets."""

import importlib.metadata as metadata
from typing import Protocol, Type

from openph.model.areas import OpPhAreas
from openph.model.climate import OpPhClimate
from openph.model.components import OpPhConstructionCollection
from openph.model.constants import OpPhConstants
from openph.model.constructions import OpPhConstructionAperture, OpPhConstructionOpaque
from openph.model.hvac.hvac import OpPhHVAC
from openph.model.ihg import OpPhIHG
from openph.model.loads.infiltration import OpPhInfiltration
from openph.model.rooms import OpPhRooms
from openph.model.schedules.collection import OpPhScheduleCollection
from openph.model.schedules.ventilation import OpPhScheduleVentilation
from openph.model.set_points import OpPhSetPoints


class OpPhSolverProtocol(Protocol):
    """Protocol that all solver-plugins must implement."""

    def __init__(self, phpp: "OpPhPHPP") -> None: ...


class OpPhPHPP:
    active_cooling_on = True  # To Do: Get from Model

    def __init__(self) -> None:
        self.constants = OpPhConstants()
        self.schedules = OpPhScheduleCollection[OpPhScheduleVentilation]()
        self.opaque_constructions = OpPhConstructionCollection[OpPhConstructionOpaque]()
        self.aperture_constructions = OpPhConstructionCollection[
            OpPhConstructionAperture
        ]()
        self.set_points = OpPhSetPoints()
        self.climate = OpPhClimate(phpp=self)
        self.infiltration = OpPhInfiltration(phpp=self)
        self.areas = OpPhAreas(phpp=self)
        self.rooms = OpPhRooms(phpp=self)
        self.ihg = OpPhIHG(phpp=self)
        self.hvac = OpPhHVAC(phpp=self)

        # Plugin registry
        self._solver_classes: dict[str, Type[OpPhSolverProtocol]] = {}
        self._solvers: dict[str, OpPhSolverProtocol] = {}
        self._load_solvers()

    def _load_solvers(self) -> None:
        """Discover and load Solver plugins.

        This uses the solver plugin's pyproject.toml "project.entry-points". All solvers should
        be logged under the group 'openph.solvers'. For example:

        >>> [project.entry-points."openph.solvers"]
        >>> solar_radiation = "openph_solar.solvers:OpPhSolarRadiationSolver"
        """
        for entry_point in metadata.entry_points(group="openph.solvers"):
            print(f"'{entry_point.name}' solver found.")
            self._solver_classes[entry_point.name] = entry_point.load()

    def get_solver(self, solver_name: str) -> OpPhSolverProtocol:
        """Get a Solver Plugin.

        Args:
            solver_name: Name of the solver (e.g., 'solar_radiation')

        Returns:
            Solver instance

        Raises:
            TypeError: If solver type is not found
        """
        # -- Return cached instance if exists
        if solver_name in self._solvers:
            return self._solvers[solver_name]

        # -- Get the solver class
        solver_class = self._solver_classes.get(solver_name)
        if solver_class is None:
            available = list(self._solver_classes.keys())
            raise TypeError(
                f"Solver '{solver_name}' not found. Available solvers: {available}"
            )

        # -- Create instance NOW (all phpp attributes are ready)
        print(f"Instantiating '{solver_name}' solver...")
        instance = solver_class(phpp=self)
        self._solvers[solver_name] = instance

        return instance

    @property
    def solvers(self) -> list[OpPhSolverProtocol]:
        """Return a list of the Solver Plugins loaded to the model."""
        return [self.get_solver(solver_name) for solver_name in self._solver_classes]

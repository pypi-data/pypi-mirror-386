# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""....."""

from typing import TYPE_CHECKING

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from openph.phpp import OpPhPHPP

from openph_solar.solvers import OpPhSolarRadiationSolver


def get_openph_solar_solver(phpp: "OpPhPHPP") -> "OpPhSolarRadiationSolver":
    """Type-safe accessor for the 'solar_radiation' solver.

    This function ensures proper type hints and validates the solver instance.

    Args:
        phpp: The OpPhPHPP controller instance

    Returns:
        The solver instance with full type information

    Raises:
        TypeError: If the registered solver is not the expected type
    """
    return phpp.get_solver(solver_name="solar_radiation")  # type: ignore

# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""....."""

from typing import TYPE_CHECKING

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from openph.phpp import OpPhPHPP

    from openph_demand.solvers import OpPhEnergyDemandSolver, OpPhGroundSolver


def get_openph_energy_demand_solver(phpp: "OpPhPHPP") -> "OpPhEnergyDemandSolver":
    """Type-safe accessor for the 'energy_demand' solver.

    This function ensures proper type hints and validates the solver instance.

    Args:
        phpp: The OpPhPHPP controller instance

    Returns:
        The solver instance with full type information

    Raises:
        TypeError: If the registered solver is not the expected type
    """
    return phpp.get_solver(solver_name="energy_demand")  # type: ignore


def get_openph_ground_solver(phpp: "OpPhPHPP") -> "OpPhGroundSolver":
    """Type-safe accessor for the 'energy_demand' solver.

    This function ensures proper type hints and validates the solver instance.

    Args:
        phpp: The OpPhPHPP controller instance

    Returns:
        The solver instance with full type information

    Raises:
        TypeError: If the registered solver is not the expected type
    """
    return phpp.get_solver(solver_name="ground")  # type: ignore

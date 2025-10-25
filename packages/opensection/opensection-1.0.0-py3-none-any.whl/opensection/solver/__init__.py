"""
Solver module for opensection

This module provides numerical solvers for section analysis
using fiber discretization and Newton-Raphson method.
"""

from opensection.solver.section_solver import SectionSolver, SolverResult

__all__ = [
    "SectionSolver",
    "SolverResult",
]

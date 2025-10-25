"""
High-level API helpers for solving with validation.
"""

from typing import Optional

from opensection.geometry.section import Section
from opensection.materials.concrete import ConcreteEC2
from opensection.materials.steel import SteelEC2
from opensection.reinforcement.rebar import RebarGroup
from opensection.solver.section_solver import SectionSolver, SolverResult
from opensection.validation.validators import SectionValidator


def validate_and_solve(
    section: Section,
    concrete: ConcreteEC2,
    steel: SteelEC2,
    rebars: RebarGroup,
    N: float,
    My: float = 0.0,
    Mz: float = 0.0,
    tol: Optional[float] = None,
    max_iter: Optional[int] = None,
    use_relative_tol: bool = False,
    exposure_class: Optional[str] = None,
) -> SolverResult:
    """
    Validate inputs (geometry, materials, reinforcement, loads) then solve.
    Raises validation exceptions if inputs are inconsistent.
    """
    # Validate inputs
    SectionValidator.validate_all(
        section=section,
        concrete=concrete,
        steel=steel,
        rebars=rebars,
        N=N,
        M_y=My,
        M_z=Mz,
        exposure_class=exposure_class,
    )

    # Solve
    solver = SectionSolver(section=section, concrete=concrete, steel=steel, rebars=rebars)
    return solver.solve(
        N=N, My=My, Mz=Mz, tol=tol, max_iter=max_iter, use_relative_tol=use_relative_tol
    )

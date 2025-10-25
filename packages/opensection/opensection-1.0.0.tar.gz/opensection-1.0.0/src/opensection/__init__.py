"""
opensection - Professional Concrete Section Analysis
==================================================

A Python library for structural concrete section analysis according to Eurocodes.

Main modules:
- geometry: Section geometry and properties
- materials: Material constitutive laws (concrete, steel)
- reinforcement: Reinforcement management
- solver: Section analysis solver
- eurocodes: Eurocode verification
- interaction: Interaction diagrams
- postprocess: Visualization and reporting

Author: opensection Contributors
License: MIT
"""

__version__ = "1.0.0"
__author__ = "opensection Contributors"
__license__ = "MIT"

# Eurocodes
from opensection.eurocodes.verification import EC2Verification

# Geometry
from opensection.geometry.contour import Contour, Point
from opensection.geometry.properties import GeometricProperties
from opensection.geometry.section import CircularSection, RectangularSection, Section, TSection

# Interaction diagrams
from opensection.interaction.diagram import InteractionDiagram

# Materials
from opensection.materials.concrete import ConcreteEC2
from opensection.materials.steel import PrestressingSteelEC2, SteelEC2, StructuralSteelEC3
from opensection.postprocess.report import ReportGenerator

# Postprocessing
from opensection.postprocess.visualization import SectionPlotter

# Reinforcement
from opensection.reinforcement.rebar import Rebar, RebarGroup
from opensection.solver.api import validate_and_solve

# Solver
from opensection.solver.section_solver import SectionSolver, SolverResult

__all__ = [
    # Version
    "__version__",
    "__author__",
    "__license__",
    # Geometry
    "Point",
    "Contour",
    "Section",
    "RectangularSection",
    "CircularSection",
    "TSection",
    "GeometricProperties",
    # Materials
    "ConcreteEC2",
    "SteelEC2",
    "PrestressingSteelEC2",
    "StructuralSteelEC3",
    # Reinforcement
    "Rebar",
    "RebarGroup",
    # Solver
    "SectionSolver",
    "SolverResult",
    "validate_and_solve",
    # Eurocodes
    "EC2Verification",
    # Interaction
    "InteractionDiagram",
    # Postprocessing
    "SectionPlotter",
    "ReportGenerator",
]

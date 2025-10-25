"""
Validation module with analytical reference cases and validators
"""

from opensection.validation.analytical_cases import (
    RectangularBeamCase,
    TBeamCase,
    ValidationDatabase,
)
from opensection.validation.exceptions import (
    GeometryValidationError,
    LoadValidationError,
    MaterialValidationError,
    RebarValidationError,
    ValidationError,
)
from opensection.validation.validators import (
    GeometryValidator,
    LoadValidator,
    MaterialValidator,
    RebarValidator,
    SectionValidator,
)

__all__ = [
    # Analytical cases
    "RectangularBeamCase",
    "TBeamCase",
    "ValidationDatabase",
    # Exceptions
    "ValidationError",
    "GeometryValidationError",
    "MaterialValidationError",
    "RebarValidationError",
    "LoadValidationError",
    # Validators
    "GeometryValidator",
    "MaterialValidator",
    "RebarValidator",
    "LoadValidator",
    "SectionValidator",
]

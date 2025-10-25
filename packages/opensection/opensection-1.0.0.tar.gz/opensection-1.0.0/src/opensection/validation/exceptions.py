"""
Custom exceptions for validation errors

Toutes les exceptions de validation héritent de ValidationError et fournissent
des messages détaillés pour faciliter le débogage et l'assistance utilisateur.
"""


class ValidationError(Exception):
    """Base class for validation errors in opensection"""

    def __init__(
        self, message: str, parameter_name: str = None, parameter_value=None, context: str = None
    ):
        """
        Initialize validation error with detailed information

        Args:
            message: Main error message
            parameter_name: Name of the parameter that failed validation
            parameter_value: Value that caused the error
            context: Additional context about where the error occurred
        """
        self.parameter_name = parameter_name
        self.parameter_value = parameter_value
        self.context = context

        # Build comprehensive error message
        full_message = message
        if parameter_name:
            full_message += f"\nParamètre : {parameter_name}"
        if parameter_value is not None:
            if isinstance(parameter_value, (int, float)):
                full_message += f"\nValeur reçue : {parameter_value}"
            else:
                full_message += f"\nValeur reçue : {repr(parameter_value)}"
        if context:
            full_message += f"\nContexte : {context}"

        super().__init__(full_message)


class GeometryValidationError(ValidationError):
    """Raised when geometry validation fails"""

    def __init__(
        self, message: str, parameter_name: str = None, parameter_value=None, context: str = None
    ):
        context = context or "Validation géométrique"
        super().__init__(message, parameter_name, parameter_value, context)


class MaterialValidationError(ValidationError):
    """Raised when material properties validation fails"""

    def __init__(
        self, message: str, parameter_name: str = None, parameter_value=None, context: str = None
    ):
        context = context or "Validation matériau"
        super().__init__(message, parameter_name, parameter_value, context)


class RebarValidationError(ValidationError):
    """Raised when reinforcement validation fails"""

    def __init__(
        self, message: str, parameter_name: str = None, parameter_value=None, context: str = None
    ):
        context = context or "Validation armatures"
        super().__init__(message, parameter_name, parameter_value, context)


class LoadValidationError(ValidationError):
    """Raised when load validation fails"""

    def __init__(
        self, message: str, parameter_name: str = None, parameter_value=None, context: str = None
    ):
        context = context or "Validation charges"
        super().__init__(message, parameter_name, parameter_value, context)

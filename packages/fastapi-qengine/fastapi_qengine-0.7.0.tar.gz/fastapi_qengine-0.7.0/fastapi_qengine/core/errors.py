"""
Custom exceptions for fastapi-qengine.
"""


class QEngineError(Exception):
    """Base exception for all fastapi-qengine errors."""

    pass


class ParseError(QEngineError):
    """Raised when filter parsing fails."""

    def __init__(
        self, message: str, source: str | None = None, position: int | None = None
    ):
        super().__init__(message)
        self.source: str | None = source
        self.position: int | None = position


class ValidationError(QEngineError):
    """Raised when filter validation fails."""

    def __init__(
        self, message: str, field: str | None = None, value: object | None = None
    ):
        super().__init__(message)
        self.field: str | None = field
        self.value: object | None = value


class SecurityError(QEngineError):
    """Raised when security policy is violated."""

    def __init__(self, message: str, policy_name: str | None = None):
        super().__init__(message)
        self.policy_name: str | None = policy_name


class CompilerError(QEngineError):
    """Raised when AST compilation fails."""

    def __init__(self, message: str, backend: str | None = None):
        super().__init__(message)
        self.backend: str | None = backend


class UnsupportedOperatorError(QEngineError):
    """Raised when an unsupported operator is used."""

    def __init__(self, operator: str, backend: str | None = None):
        message = f"Operator '{operator}' is not supported"
        if backend:
            message += f" for backend '{backend}'"
        super().__init__(message)
        self.operator: str = operator
        self.backend: str | None = backend


class RegistryError(QEngineError):
    """Raised when registry operations fail."""

    pass


class OptimizationError(QEngineError):
    """Raised when AST optimization fails."""

    pass

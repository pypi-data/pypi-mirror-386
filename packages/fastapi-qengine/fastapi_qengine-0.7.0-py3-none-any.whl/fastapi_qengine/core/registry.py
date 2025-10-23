"""
Registry for managing operators (custom operators only).

Note:
- Backend compiler registration has been removed. Each backend now
  encapsulates its logic and exposes its own engine explicitly.
"""

from typing import cast
from .errors import RegistryError


class OperatorRegistry:
    """Registry for managing custom operators."""

    def __init__(self):
        self._operators: dict[str, dict[str, object]] = {}

    def register_operator(
        self, name: str, implementation: object, backends: list[str] | None = None
    ) -> None:
        """
        Register a custom operator.

        Args:
            name: Operator name (e.g., '$custom_op')
            implementation: Operator implementation
            backends: list of backends this operator supports (None = all)
        """
        if not name.startswith("$"):
            raise RegistryError("Operator names must start with '$'")

        self._operators[name] = {
            "implementation": implementation,
            "backends": backends or [],
        }

    def get_operator(self, name: str, backend: str | None = None) -> object:
        """
        Get operator implementation.

        Args:
            name: Operator name
            backend: Backend name (for backend-specific operators)

        Returns:
            Operator implementation
        """
        if name not in self._operators:
            raise RegistryError(f"Unknown operator '{name}'")

        operator_info = self._operators[name]

        # Check backend compatibility
        if (
            backend
            and operator_info["backends"]
            and backend not in cast(list[str], operator_info["backends"])
        ):
            raise RegistryError(
                f"Operator '{name}' not supported for backend '{backend}'"
            )

        return operator_info["implementation"]

    def is_registered(self, name: str, backend: str | None = None) -> bool:
        """Check if an operator is registered."""
        if name not in self._operators:
            return False

        if backend:
            operator_info = self._operators[name]
            return not operator_info["backends"] or backend in cast(
                list[str], operator_info["backends"]
            )

        return True

    def list_operators(self, backend: str | None = None) -> list[str]:
        """list all registered operators."""
        if backend:
            return [
                name
                for name, info in self._operators.items()
                if not info["backends"] or backend in cast(list[str], info["backends"])
            ]
        return list(self._operators.keys())


# Global operator registry
operator_registry = OperatorRegistry()

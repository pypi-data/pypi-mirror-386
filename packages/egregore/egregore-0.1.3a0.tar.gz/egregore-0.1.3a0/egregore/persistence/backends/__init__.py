"""Persistence backend interfaces and implementations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class PersistenceBackend(ABC):
    """Abstract interface for scaffold state persistence backends.

    All backends must implement: save, load, delete, exists
    """

    @abstractmethod
    def save(self, key: str, data: Dict[str, Any]) -> None:
        """Save state data.

        Args:
            key: Unique identifier (scaffold.id)
            data: Serialized state dictionary
        """
        pass

    @abstractmethod
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load state data.

        Args:
            key: Unique identifier (scaffold.id)

        Returns:
            Deserialized state dict or None if not found
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete persisted state.

        Args:
            key: Unique identifier (scaffold.id)
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if state exists.

        Args:
            key: Unique identifier (scaffold.id)

        Returns:
            True if state exists
        """
        pass

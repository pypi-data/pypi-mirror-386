"""
High-level Connection helper.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, Optional

from .datastar_api import DatastarAPI
from ._defaults import DEFAULT_DESCRIPTION


class Connection(ABC):
    """Represents a connection scoped to a project."""

    _connection_counter: ClassVar[int] = 1
    _api_client: ClassVar[Optional[DatastarAPI]] = None

    def __init__(
        self,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        sandbox: Optional[bool] = False,
    ):
        super().__init__()
        self.name = name or self._next_connection_name()
        self.description = description or DEFAULT_DESCRIPTION

        # Note: Sandbox is a special case, it is not persisted
        if sandbox:
            self.id = DatastarAPI.SANDBOX_CONNECTOR_ID
        else:
            self.id: str = self._persist_new()

    @classmethod
    def get_collections(cls, connector_type: Optional[str] = None) -> list[str]:
        """
        Return the list of connection names.
        """
        response = cls._api().get_connectors()
        items = response["items"]

        # Apply filter
        if connector_type:
            items = [item for item in items if item["type"] == connector_type]

        return [item["name"] for item in items]

    def save(self) -> None:
        """
        Persist connection changes to the server.
        """
        assert self.id

        # Build configuration payload similar to creation, excluding top-level fields
        self._api().update_connection(self.id, self._to_json())

    def delete(self) -> None:

        if not self.id:
            return

        self._api().delete_connection(self.id)

    # ------------------------------------------------------------------
    # Internal

    @classmethod
    def _next_connection_name(cls) -> str:
        counter = cls._connection_counter
        cls._connection_counter += 1
        return f"Connection {counter}"

    @classmethod
    def _api(cls) -> DatastarAPI:
        if cls._api_client is None:
            cls._api_client = DatastarAPI()
        return cls._api_client

    @classmethod
    def _name_to_id(cls, name: str) -> str | None:
        """
        Resolve a connector identifier from its display name.

        Args:
            name: Connector name to search for.

        Returns:
            The connector UUID as a string.

        Raises:
            ValueError: If the name is empty or no connector matches.
        """

        if not name or not name.strip():
            raise ValueError("Connector name is required.")

        target = name.strip().lower()
        response = cls._api().get_connectors()
        for entry in DatastarAPI.coerce_collection(response):
            candidate = entry.get("name")
            if isinstance(candidate, str) and candidate.strip().lower() == target:
                connector_id = entry.get("id")
                if connector_id:
                    return str(connector_id)

        return None

    # ------------------------------------------------------------------
    # Lifecycle helpers

    def _persist_new(self) -> str:

        return self._api().create_connection(self._to_json())

    # ------------------------------------------------------------------
    # JSON translation helpers

    def _to_json(self) -> Dict[str, Any]:

        configuration: Dict[str, Any] = {
            "name": self.name,
            "description": self.description,
        }

        # Note: Unlike Task, connection format is flattened
        configuration.update(self._to_configuration())

        return configuration

    def _from_json(self, payload: Dict[str, Any]) -> None:

        self.id = payload["id"]
        self.name = payload["name"]
        self.description = payload.get("description")

        # Add subclass data via overridden method
        self._from_configuration(payload)

    # ------------------------------------------------------------------
    # Abstract methods

    @abstractmethod
    def _from_configuration(self, payload: Dict[str, Any]) -> None:
        assert False

    @abstractmethod
    def _to_configuration(self) -> Dict[str, Any]:
        assert False

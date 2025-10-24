# pyright: reportPrivateUsage=false, reportPrivateImportUsage=false
# pylint: disable=protected-access, import-outside-toplevel
"""
High-level Task utilities for DataStarExp.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Iterator, TYPE_CHECKING
from ._defaults import DEFAULT_DESCRIPTION

if TYPE_CHECKING:
    from .macro import Macro

T = TypeVar("T", bound="Task")


class Task(ABC):
    """Representation of a Datastar task."""

    def __init__(
        self,
        macro: "Macro",
        *,
        task_id: str = "",
        name: str = "",
        description: str = "",
        auto_join: bool = True,
        previous_task: Optional[Task] = None,
        persist: bool = True,
    ):
        self.macro: Macro = macro
        self.name: str = name or self.macro._next_task_name()
        self.description: str = description or DEFAULT_DESCRIPTION
        # If no id is supplied then create
        if task_id:
            self._id = task_id
        elif persist:
            # Defer to save() to avoid duplicating creation logic
            self._id = ""
            self.save(auto_join=auto_join, previous_task=previous_task)
        else:
            # Construct without persisting
            self._id = ""

    def is_persisted(self) -> bool:
        return bool(self._id)

    def save(
        self,
        *,
        auto_join: bool = True,
        previous_task: Optional[Task] = None,
    ) -> None:

        # If already persisted, update
        if self.is_persisted():
            configuration: Dict[str, Any] = self._to_configuration()

            self.macro.project._api().update_task(
                self.macro.project._id,
                self._id,
                name=self.name,
                configuration=configuration,
                description=self.description,
            )
            return

        # Otherwise, create a new task on the server
        self._id = self._persist_new()

        # Join task to either previous task (auto) or specified task, or leave unconnected
        if auto_join:
            self._add_dependency_id(self.macro._last_task_added_id)
        elif previous_task:
            self._add_dependency_id(previous_task._id)

        self.macro._last_task_added_id = self._id

    def delete(self) -> None:
        """
        Delete this task
        """
        self.macro.project._api().delete_task(self.macro.project._id, self._id)

    def add_dependency(self, previous_task_name: str) -> None:
        """
        Connect this task to a previous task
        """

        dependency_id = self._get_dependency_by_name(previous_task_name)
        if dependency_id is None:
            return

        self.macro.project._api().create_task_dependency(
            self.macro.project._id, self._id, dependency_id
        )

    def remove_dependency(self, previous_task_name: str) -> None:
        """
        Remove the connection between this task and a previous task
        """

        dependency_id = self._get_dependency_by_name(previous_task_name)
        if dependency_id is None:
            return

        self.macro.project._api().delete_task_dependency(
            self.macro.project._id, dependency_id
        )

    def get_dependencies(self) -> List[str]:
        """
        List all tasks, that have incoming connections to this one, by name
        """

        response = self.macro.project._api().get_task_dependencies(
            self.macro.project._id, self._id
        )

        task_data = self.macro._get_task_data()

        task_list: List[str] = []
        for item in response["items"]:
            task_id = item["dependencyTaskId"]
            name: str = self._get_task_name_from_data(task_data, task_id)
            task_list.append(name)

        return task_list

    # ------------------------------------------------------------------
    # Internals

    def _add_dependency_id(self, previous_task_id: str) -> None:

        self.macro.project._api().create_task_dependency(
            self.macro.project._id, self._id, previous_task_id
        )

    def _persist_new(self) -> str:
        assert self.macro is not None

        response = self.macro.project._api().create_task(
            self.macro.project._id,
            self.macro._id,
            name=self.name,
            task_type=self._get_task_type(),
            configuration=self._to_configuration(),
            description=self.description,
        )
        return response["item"]["id"]

    def _get_task_data_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:

        task_data = self.macro._get_task_data()

        for item in task_data:
            if item["id"] == task_id:
                return item

        return None

    def _get_task_name_from_data(
        self, data: Iterator[Dict[str, Any]], task_id: str
    ) -> str:

        for item in data:
            if item["id"] == task_id:
                return item["name"]

        assert False

    def _get_dependency_by_name(self, name: str) -> Optional[str]:

        response = self.macro.project._api().get_task_dependencies(
            self.macro.project._id, self._id
        )

        for item in response["items"]:
            if item["name"] == name:
                return item["id"]

        return None

    @classmethod
    def _read_from(cls: Type[T], macro: Macro, task_data: Dict[str, Any]) -> Task:

        assert cls is not Task
        assert (macro._id) == task_data["workflowId"]

        # Construct instance of subclass
        new_task = cls.__new__(cls)

        # Get base parameters
        task_id: str = task_data["id"]
        task_name: str = task_data["name"]
        task_description: str = task_data["description"]

        Task.__init__(
            new_task,
            macro,
            task_id=task_id,
            name=task_name,
            description=task_description,
        )

        new_task._from_configuration(task_data["configuration"])

        return new_task

    # ------------------------------------------------------------------
    # Abstract methods

    @abstractmethod
    def _get_task_type(self) -> str:
        assert False

    @abstractmethod
    def _to_configuration(self) -> Dict[str, Any]:
        assert False

    @abstractmethod
    def _from_configuration(self, configuration: Dict[str, Any]) -> None:
        assert False

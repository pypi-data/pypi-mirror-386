# pyright: reportPrivateUsage=false, reportPrivateImportUsage=false
# pylint: disable=protected-access, import-outside-toplevel
"""
Datastar library: Macro interface.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Iterator, Type, TYPE_CHECKING

from .task import Task
from .task_registry import _get_task_class
from ._defaults import DEFAULT_DESCRIPTION

if TYPE_CHECKING:
    from .project import Project
    from .tasks import ImportTask, ExportTask, RunSQLTask, RunPythonTask


class Macro:
    """User-facing wrapper around a DataStar macro."""

    def __init__(
        self,
        project: "Project",
        *,
        macro_id: str = "",
        name: str = "",
        description: str = "",
    ):
        self.project: Project = project
        self.name: str = name or self.project._next_macro_name()
        self.description: str = description or DEFAULT_DESCRIPTION
        self._task_counter: int = 1

        if macro_id:
            self._id = macro_id
        else:
            self._id: str = self.project._api().create_macro(
                self.project._id, name=self.name, description=self.description
            )

        self._last_task_added_id: str = self._get_start_task_id()

    def save(self) -> None:
        """
        Persist macro details to database
        """
        self.project._api().update_macro(
            self.project._id, self._id, name=self.name, description=self.description
        )

    def delete(self) -> None:
        """
        Delete macro from project
        """
        self.project._api().delete_macro(self.project._id, self._id)

    # ------------------------------------------------------------------
    # Tasks

    def get_task(self, name: str) -> Optional[Task]:
        """
        Returns a task by name
        """

        # Note: This requires all task types are added in task_registry

        for task_data in self._get_task_data():

            if task_data["name"] == name:

                # Construct to correct subclass of Type per the type returned
                task_type = task_data["taskType"]
                class_to_create: Type[Task] = _get_task_class(task_type)
                return class_to_create._read_from(self, task_data)

        return None

    def get_tasks(self, *, type_filter: Optional[str] = None) -> List[str]:
        """
        Get a list of task names in the macro
        """

        data = self._get_task_data(type_filter=type_filter)

        task_list: List[str] = []
        for item in data:
            task_list.append(str(item.get("name")))

        return task_list

    def delete_task(self, name: str) -> None:
        """
        Delete a task by name from the macro
        """
        task = self.get_task(name)
        if task is not None:
            task.delete()

    # ------------------------------------------------------------------
    # Task creation helper functions

    def add_task(
        self,
        task: Task,
        *,
        auto_join: bool = True,
        previous_task: Optional[Task] = None,
    ) -> Task:
        """
        Persist a pre-configured task and add it to this macro.

        The task must have been constructed with this macro. If it is already
        persisted, this is a no-op and returns the task.
        """

        if task.macro is not self:
            raise ValueError("Task belongs to a different macro")

        task.save(auto_join=auto_join, previous_task=previous_task)
        return task

    def add_import_task(self, **kwargs: Any) -> "ImportTask":
        """
        Add a new ImportTask to this macro (db will be updated)
        """
        from .tasks import ImportTask

        return ImportTask(self, **kwargs)

    def add_export_task(self, **kwargs: Any) -> "ExportTask":
        """
        Add a new ExportTask to this macro (db will be updated)
        """
        from .tasks import ExportTask

        return ExportTask(self, **kwargs)

    def add_run_sql_task(self, **kwargs: Any) -> "RunSQLTask":
        """
        Add a new RunSQLTask to this macro (db will be updated)
        """
        from .tasks import RunSQLTask

        return RunSQLTask(self, **kwargs)

    def add_run_python_task(self, **kwargs: Any) -> "RunPythonTask":
        """
        Add a new RunPythonTask to this macro (db will be updated)
        """
        from .tasks import RunPythonTask

        return RunPythonTask(self, **kwargs)

    # ------------------------------------------------------------------
    # Running a macro

    def run(self, parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Run a macro as a job
        """

        parameters = parameters or {}

        response = self.project._api().execute_macro(
            self.project._id, self._id, parameters=parameters
        )

        return response["item"]["id"]

    def get_run_status(self, macro_run_id: str) -> str:
        """
        Get the current status of a job
        """
        response = self.project._api().get_macro_run(self.project._id, macro_run_id)

        return response["item"]["status"]

    def wait_for_done(self, macro_run_id: str, *, verbose: bool = False) -> None:
        """
        Wait for a job to complete
        """

        status = "pending"
        counter = 0
        while status == "pending" or status == "processing":

            # Polling 3 sec interval
            time.sleep(3)

            status = self.get_run_status(macro_run_id)

            if verbose:
                counter += 1
                print(
                    f"Waiting for run completion ({counter}). Current run status = {status}"
                )

    # ------------------------------------------------------------------
    # Internal helpers

    @classmethod
    def _read_from(cls, project: Project, task_data: Dict[str, Any]) -> Macro:

        # Get parameters
        macro_id: str = task_data["id"]
        macro_name: str = task_data["name"]
        macro_description: str = task_data["description"]

        return Macro(
            project, macro_id=macro_id, name=macro_name, description=macro_description
        )

    def _get_task_data(
        self, *, type_filter: Optional[str] = None
    ) -> Iterator[Dict[str, Any]]:

        response = self.project._api().get_tasks(self.project._id, self._id)

        for item in response.get("items", []):
            if type_filter and type_filter != item["taskType"]:
                continue

            yield item

    def _get_start_task_id(self):

        tasks = self._get_task_data(type_filter="start")

        first_item = next(tasks)

        return first_item["id"]

    def _next_task_name(self) -> str:
        counter = self._task_counter
        self._task_counter += 1
        return f"Task {counter}"

    def _from_json(self, payload: Dict[str, Any]) -> None:
        self._id = str(payload["id"])
        self.name = str(payload["name"])
        self.description = payload.get("description") or DEFAULT_DESCRIPTION

    @classmethod
    def _from_existing(cls, project: "Project", payload: Dict[str, Any]) -> "Macro":
        instance: "Macro" = cls.__new__(cls)
        instance.project = project
        instance._task_counter = 0
        instance._from_json(payload)
        return instance

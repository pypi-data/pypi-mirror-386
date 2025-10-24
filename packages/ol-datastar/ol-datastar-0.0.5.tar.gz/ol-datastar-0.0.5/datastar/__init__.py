from .connection import Connection
from .project import Project
from .macro import Macro
from .task import Task

# Re-export convenient subpackages
from . import connections as connections
from . import tasks as tasks

# Single source of truth for version
from ._version import __version__

# Public API of the package
__all__ = [
    "Project",
    "Macro",
    "Task",
    "Connection",
    "connections",
    "tasks",
    "__version__",
]

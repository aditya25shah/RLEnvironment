"""Compatibility shim that re-exports symbols from the root tasks.py module."""

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_ROOT_MODULE = Path(__file__).resolve().parent.parent / "tasks.py"
_SPEC = spec_from_file_location("tasks", _ROOT_MODULE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Could not load tasks module from {_ROOT_MODULE}")

_MODULE = module_from_spec(_SPEC)
sys.modules.setdefault("tasks", _MODULE)
_SPEC.loader.exec_module(_MODULE)

TaskExpectation = _MODULE.TaskExpectation
SupportTask = _MODULE.SupportTask
TASKS = _MODULE.TASKS
TASK_ORDER = _MODULE.TASK_ORDER
TASKS_WITH_GRADERS = _MODULE.TASKS_WITH_GRADERS
get_task = _MODULE.get_task
select_task_by_seed = _MODULE.select_task_by_seed

__all__ = [
    "TaskExpectation",
    "SupportTask",
    "TASKS",
    "TASK_ORDER",
    "TASKS_WITH_GRADERS",
    "get_task",
    "select_task_by_seed",
]

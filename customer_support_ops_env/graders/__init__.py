"""Compatibility shim that re-exports symbols from the root graders.py module."""

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

if "tasks" not in sys.modules:
    _TASKS_ROOT = Path(__file__).resolve().parent.parent / "tasks.py"
    _TASKS_SPEC = spec_from_file_location("tasks", _TASKS_ROOT)
    if _TASKS_SPEC is None or _TASKS_SPEC.loader is None:
        raise ImportError(f"Could not load tasks module from {_TASKS_ROOT}")
    _TASKS_MODULE = module_from_spec(_TASKS_SPEC)
    sys.modules.setdefault("tasks", _TASKS_MODULE)
    _TASKS_SPEC.loader.exec_module(_TASKS_MODULE)

_ROOT_MODULE = Path(__file__).resolve().parent.parent / "graders.py"
_SPEC = spec_from_file_location("graders", _ROOT_MODULE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Could not load graders module from {_ROOT_MODULE}")

_MODULE = module_from_spec(_SPEC)
sys.modules.setdefault("graders", _MODULE)
_SPEC.loader.exec_module(_MODULE)

WorkspaceSnapshot = _MODULE.WorkspaceSnapshot
GradeResult = _MODULE.GradeResult
TASK_GRADERS = _MODULE.TASK_GRADERS
grade_workspace = _MODULE.grade_workspace
grade_easy_refund_renewal = _MODULE.grade_easy_refund_renewal
grade_medium_replacement_delay = _MODULE.grade_medium_replacement_delay
grade_hard_account_takeover = _MODULE.grade_hard_account_takeover
grade_task = _MODULE.grade_task

__all__ = [
    "WorkspaceSnapshot",
    "GradeResult",
    "TASK_GRADERS",
    "grade_workspace",
    "grade_easy_refund_renewal",
    "grade_medium_replacement_delay",
    "grade_hard_account_takeover",
    "grade_task",
]

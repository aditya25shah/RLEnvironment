"""Compatibility shims for per-task graders."""

from importlib import import_module

_root = import_module("graders")

TASK_GRADERS = _root.TASK_GRADERS
GradeResult = _root.GradeResult
WorkspaceSnapshot = _root.WorkspaceSnapshot
grade_easy_refund_renewal = _root.grade_easy_refund_renewal
grade_medium_replacement_delay = _root.grade_medium_replacement_delay
grade_hard_account_takeover = _root.grade_hard_account_takeover
grade_task = _root.grade_task

__all__ = [
    "GradeResult",
    "TASK_GRADERS",
    "WorkspaceSnapshot",
    "grade_easy_refund_renewal",
    "grade_hard_account_takeover",
    "grade_medium_replacement_delay",
    "grade_task",
]

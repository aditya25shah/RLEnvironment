# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Deterministic graders for customer support tasks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

try:
    from .tasks import SupportTask
except ImportError:
    from tasks import SupportTask


@dataclass(frozen=True)
class WorkspaceSnapshot:
    queue: str
    priority: str
    tags: List[str]
    notes_written: List[str]
    last_reply: str
    resolution_code: str
    refund_amount: float
    escalated: bool


@dataclass(frozen=True)
class GradeResult:
    total_score: float
    component_scores: Dict[str, float]
    feedback: List[str]
    remaining_objectives: List[str]


def _text_contains_all(text: str, keywords: List[str]) -> float:
    lowered = text.lower()
    matches = sum(1 for keyword in keywords if keyword.lower() in lowered)
    return matches / len(keywords) if keywords else 1.0


def _score_triage(task: SupportTask, snapshot: WorkspaceSnapshot) -> tuple[float, List[str], List[str]]:
    expected = task.expectation
    feedback: List[str] = []
    remaining: List[str] = []
    score = 0.0

    if snapshot.queue == expected.queue:
        score += 0.15
        feedback.append("Queue assignment is correct.")
    else:
        remaining.append(f"Move the case to the {expected.queue} queue.")

    if snapshot.priority == expected.priority:
        score += 0.10
        feedback.append("Priority matches the incident severity.")
    else:
        remaining.append(f"Set priority to {expected.priority}.")

    actual_tags = set(snapshot.tags)
    expected_tags = set(expected.tags)
    tag_fraction = len(actual_tags & expected_tags) / len(expected_tags)
    score += 0.10 * tag_fraction
    if tag_fraction == 1.0:
        feedback.append("Tags cover the key case attributes.")
    else:
        missing = ", ".join(sorted(expected_tags - actual_tags))
        remaining.append(f"Add missing tags: {missing}.")

    return score, feedback, remaining


def _score_notes(task: SupportTask, snapshot: WorkspaceSnapshot) -> tuple[float, List[str], List[str]]:
    note_text = "\n".join(snapshot.notes_written)
    fraction = _text_contains_all(note_text, task.expectation.note_keywords)
    score = 0.20 * fraction
    if fraction == 1.0:
        return score, ["Internal note captures the essential facts."], []
    return score, [], ["Expand the internal note with the key factual evidence."]


def _score_reply(task: SupportTask, snapshot: WorkspaceSnapshot) -> tuple[float, List[str], List[str]]:
    reply = snapshot.last_reply.strip()
    if not reply:
        return 0.0, [], ["Draft a customer-facing reply."]

    content_fraction = _text_contains_all(reply, task.expectation.reply_keywords)
    empathy_fraction = min(1.0, _text_contains_all(reply, task.expectation.reply_empathy_keywords))
    score = 0.20 * content_fraction + 0.05 * empathy_fraction
    feedback: List[str] = []
    remaining: List[str] = []

    if content_fraction == 1.0:
        feedback.append("Reply includes the required operational commitments.")
    else:
        remaining.append("Reply is missing one or more required next-step details.")

    if empathy_fraction == 1.0:
        feedback.append("Reply acknowledges customer impact appropriately.")
    else:
        remaining.append("Reply should show clearer empathy for the customer impact.")

    return score, feedback, remaining


def _score_resolution(task: SupportTask, snapshot: WorkspaceSnapshot) -> tuple[float, List[str], List[str]]:
    expected = task.expectation
    score = 0.0
    feedback: List[str] = []
    remaining: List[str] = []

    if snapshot.resolution_code == expected.resolution_code:
        score += 0.10
        feedback.append("Resolution code is correct.")
    else:
        remaining.append(f"Use resolution code {expected.resolution_code}.")

    if snapshot.escalated == expected.escalate:
        score += 0.05
        feedback.append("Escalation behavior matches policy.")
    else:
        target = "enable" if expected.escalate else "avoid"
        remaining.append(f"{target.capitalize()} escalation for this task.")

    if expected.resolution_code == "refund":
        amount_match = abs(snapshot.refund_amount - expected.refund_amount) < 0.01
        if amount_match:
            score += 0.05
            feedback.append("Refund amount is correct.")
        else:
            remaining.append(f"Set refund amount to {expected.refund_amount:.2f}.")
    else:
        if snapshot.refund_amount == 0.0:
            score += 0.05
            feedback.append("Refund handling follows policy.")
        else:
            remaining.append("Do not attach a refund amount to this resolution.")

    return score, feedback, remaining


def grade_workspace(task: SupportTask, snapshot: WorkspaceSnapshot) -> GradeResult:
    """Compute the task score and textual feedback."""
    component_scores: Dict[str, float] = {}
    feedback: List[str] = []
    remaining: List[str] = []

    triage_score, triage_feedback, triage_remaining = _score_triage(task, snapshot)
    notes_score, notes_feedback, notes_remaining = _score_notes(task, snapshot)
    reply_score, reply_feedback, reply_remaining = _score_reply(task, snapshot)
    resolution_score, resolution_feedback, resolution_remaining = _score_resolution(task, snapshot)

    component_scores["triage"] = round(triage_score, 4)
    component_scores["note"] = round(notes_score, 4)
    component_scores["reply"] = round(reply_score, 4)
    component_scores["resolution"] = round(resolution_score, 4)

    feedback.extend(triage_feedback + notes_feedback + reply_feedback + resolution_feedback)
    remaining.extend(triage_remaining + notes_remaining + reply_remaining + resolution_remaining)

    total_score = round(sum(component_scores.values()), 4)
    return GradeResult(
        total_score=total_score,
        component_scores=component_scores,
        feedback=feedback,
        remaining_objectives=remaining,
    )


def grade_easy_refund_renewal(
    task: SupportTask, snapshot: WorkspaceSnapshot
) -> GradeResult:
    """Task-specific grader for easy_refund_renewal."""
    return grade_workspace(task, snapshot)


def grade_medium_replacement_delay(
    task: SupportTask, snapshot: WorkspaceSnapshot
) -> GradeResult:
    """Task-specific grader for medium_replacement_delay."""
    return grade_workspace(task, snapshot)


def grade_hard_account_takeover(
    task: SupportTask, snapshot: WorkspaceSnapshot
) -> GradeResult:
    """Task-specific grader for hard_account_takeover."""
    return grade_workspace(task, snapshot)


TASK_GRADERS = {
    "easy_refund_renewal": grade_easy_refund_renewal,
    "medium_replacement_delay": grade_medium_replacement_delay,
    "hard_account_takeover": grade_hard_account_takeover,
}


def grade_task(task: SupportTask, snapshot: WorkspaceSnapshot) -> GradeResult:
    """Dispatch to the explicit grader for the current task."""
    grader = TASK_GRADERS[task.task_id]
    return grader(task, snapshot)

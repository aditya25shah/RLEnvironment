# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Customer support case handling environment."""

from __future__ import annotations

from uuid import uuid4

from openenv.core.env_server.interfaces import Environment

try:
    from ..graders import WorkspaceSnapshot, grade_task
    from ..models import CustomerSupportOpsAction, CustomerSupportOpsObservation, CustomerSupportOpsState
    from ..tasks import TASK_ORDER, get_task, select_task_by_seed
except ImportError:
    from graders import WorkspaceSnapshot, grade_task
    from models import CustomerSupportOpsAction, CustomerSupportOpsObservation, CustomerSupportOpsState
    from tasks import TASK_ORDER, get_task, select_task_by_seed


class CustomerSupportOpsEnvironment(
    Environment[CustomerSupportOpsAction, CustomerSupportOpsObservation, CustomerSupportOpsState]
):
    """Deterministic customer support environment with graded tasks."""

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._task = select_task_by_seed(0)
        self._state = CustomerSupportOpsState(episode_id=str(uuid4()), task_id=self._task.task_id)

    def reset(
        self,
        seed: int | None = None,
        episode_id: str | None = None,
        **kwargs: object,
    ) -> CustomerSupportOpsObservation:
        task_id = kwargs.get("task_id")
        difficulty = kwargs.get("difficulty")

        if isinstance(task_id, str):
            self._task = get_task(task_id)
        elif isinstance(difficulty, str):
            matching_task = next(task_id for task_id in TASK_ORDER if task_id.startswith(difficulty))
            self._task = get_task(matching_task)
        else:
            self._task = select_task_by_seed(seed)

        self._state = CustomerSupportOpsState(
            episode_id=episode_id or str(uuid4()),
            step_count=0,
            task_id=self._task.task_id,
            difficulty=self._task.difficulty,
            max_steps=4,
        )
        return self._build_observation(
            reward=0.0,
            status="ready",
            last_feedback=["Review the ticket, apply triage, then resolve the case."],
        )

    def step(
        self,
        action: CustomerSupportOpsAction,
        timeout_s: float | None = None,
        **kwargs: object,
    ) -> CustomerSupportOpsObservation:
        del timeout_s, kwargs
        previous_score = self._state.progress_score
        self._state.step_count += 1
        step_feedback: list[str] = []

        if action.operation == "triage":
            self._state.current_queue = action.queue or self._state.current_queue
            self._state.current_priority = action.priority or self._state.current_priority
            self._state.current_tags = sorted(set(action.tags))
            step_feedback.append("Triage fields updated.")
        elif action.operation == "note":
            if action.internal_note.strip():
                self._state.notes_written.append(action.internal_note.strip())
                step_feedback.append("Internal note saved.")
            else:
                step_feedback.append("Empty note ignored.")
        elif action.operation == "reply":
            self._state.last_reply = action.reply_text.strip()
            step_feedback.append("Reply draft updated.")
        elif action.operation == "resolve":
            self._state.resolution_code = action.resolution_code or self._state.resolution_code
            self._state.refund_amount = action.refund_amount
            self._state.escalated = action.escalate
            self._state.resolved = action.mark_resolved
            step_feedback.append("Resolution fields updated.")

        grade = grade_task(self._task, self._snapshot())
        self._state.progress_score = grade.total_score

        reward = round(max(0.0, grade.total_score - previous_score), 4)
        done = self._state.resolved or self._state.step_count >= self._state.max_steps
        status = "resolved" if self._state.resolved else ("failed" if done else "in_progress")

        last_feedback = step_feedback + grade.feedback
        if done and not self._state.resolved:
            last_feedback.append("Episode ended because the step budget was exhausted.")

        observation = self._build_observation(
            reward=reward,
            status=status,
            last_feedback=last_feedback,
            component_scores=grade.component_scores,
            remaining_objectives=grade.remaining_objectives,
        )
        observation.done = done
        return observation

    @property
    def state(self) -> CustomerSupportOpsState:
        return self._state

    def _snapshot(self) -> WorkspaceSnapshot:
        return WorkspaceSnapshot(
            queue=self._state.current_queue,
            priority=self._state.current_priority,
            tags=self._state.current_tags,
            notes_written=self._state.notes_written,
            last_reply=self._state.last_reply,
            resolution_code=self._state.resolution_code,
            refund_amount=self._state.refund_amount,
            escalated=self._state.escalated,
        )

    def _build_observation(
        self,
        reward: float,
        status: str,
        last_feedback: list[str],
        component_scores: dict[str, float] | None = None,
        remaining_objectives: list[str] | None = None,
    ) -> CustomerSupportOpsObservation:
        return CustomerSupportOpsObservation(
            task_id=self._task.task_id,
            difficulty=self._task.difficulty,  # type: ignore[arg-type]
            status=status,  # type: ignore[arg-type]
            ticket_summary=self._task.ticket_summary,
            customer_message=self._task.customer_message,
            policy_summary=self._task.policy_summary,
            current_queue=self._state.current_queue,
            current_priority=self._state.current_priority,
            current_tags=self._state.current_tags,
            notes_written=self._state.notes_written,
            last_reply=self._state.last_reply,
            progress_score=self._state.progress_score,
            component_scores=component_scores or {},
            remaining_objectives=remaining_objectives or self._task.constraints,
            last_feedback=last_feedback,
            reward=reward,
            done=False,
            metadata={
                "title": self._task.title,
                "constraints": self._task.constraints,
                "expected_resolution_family": self._task.expectation.resolution_code,
                "grader_name": self._task.grader_name,
                "step_count": self._state.step_count,
                "max_steps": self._state.max_steps,
            },
        )

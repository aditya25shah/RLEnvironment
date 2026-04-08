# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Typed models for the customer support operations environment."""

import json
from typing import Any, Dict, List, Literal

from openenv.core.env_server.types import Action, Observation, State
from pydantic import Field, field_validator

Difficulty = Literal["easy", "medium", "hard"]
Operation = Literal["triage", "note", "reply", "resolve"]
Priority = Literal["normal", "high", "urgent"]
QueueName = Literal["billing", "fulfillment", "account_security"]
ResolutionCode = Literal["refund", "replacement", "security_escalation"]
TagName = Literal[
    "billing",
    "refund",
    "renewal",
    "shipping_delay",
    "replacement",
    "vip",
    "security",
    "account_takeover",
    "fraud",
]
Status = Literal["ready", "in_progress", "resolved", "failed"]


class CustomerSupportOpsAction(Action):
    """One structured customer-support action."""

    operation: Operation = Field(..., description="Workflow action to perform this step")
    queue: QueueName | None = Field(default=None, description="Queue assignment")
    priority: Priority | None = Field(default=None, description="Priority assignment")
    tags: List[TagName] = Field(default_factory=list, description="Case tags")
    internal_note: str = Field(default="", description="Internal-only note")
    reply_text: str = Field(default="", description="Customer-facing reply")
    resolution_code: ResolutionCode | None = Field(default=None, description="Resolution code")
    refund_amount: float = Field(default=0.0, ge=0.0, description="Refund amount")
    escalate: bool = Field(default=False, description="Whether to escalate")
    mark_resolved: bool = Field(default=False, description="Whether to resolve the case")

    @field_validator("tags", mode="before")
    @classmethod
    def _coerce_tags(cls, value: Any) -> Any:
        """
        Accept the OpenEnv playground's text input for array fields.

        The current default web UI renders array schema fields as a textbox,
        so users often submit tags as:
        - "billing"
        - "billing, refund, renewal"
        - '["billing", "refund", "renewal"]'
        """
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            if raw.startswith("["):
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    pass
                else:
                    if isinstance(parsed, list):
                        return parsed
            return [item.strip() for item in raw.split(",") if item.strip()]
        return value


class CustomerSupportOpsObservation(Observation):
    """Observation shown to the agent after each step."""

    task_id: str = Field(default="", description="Current task identifier")
    difficulty: Difficulty = Field(default="easy", description="Task difficulty")
    status: Status = Field(default="ready", description="Episode status")
    ticket_summary: str = Field(default="", description="Short task summary")
    customer_message: str = Field(default="", description="Original customer message")
    policy_summary: str = Field(default="", description="Policy reference")
    available_operations: List[Operation] = Field(
        default_factory=lambda: ["triage", "note", "reply", "resolve"],
        description="Valid operations for the next step",
    )
    current_queue: str = Field(default="", description="Current queue")
    current_priority: str = Field(default="", description="Current priority")
    current_tags: List[str] = Field(default_factory=list, description="Current tags")
    notes_written: List[str] = Field(default_factory=list, description="Internal notes")
    last_reply: str = Field(default="", description="Latest reply draft")
    progress_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Current score")
    component_scores: Dict[str, float] = Field(default_factory=dict, description="Score breakdown")
    remaining_objectives: List[str] = Field(default_factory=list, description="Unmet objectives")
    last_feedback: List[str] = Field(default_factory=list, description="Feedback for the last step")


class CustomerSupportOpsState(State):
    """Serializable environment state."""

    task_id: str = Field(default="", description="Current task identifier")
    difficulty: Difficulty = Field(default="easy", description="Task difficulty")
    current_queue: str = Field(default="", description="Current queue")
    current_priority: str = Field(default="", description="Current priority")
    current_tags: List[str] = Field(default_factory=list, description="Current tags")
    notes_written: List[str] = Field(default_factory=list, description="Internal notes")
    last_reply: str = Field(default="", description="Latest reply draft")
    resolution_code: str = Field(default="", description="Chosen resolution code")
    refund_amount: float = Field(default=0.0, description="Refund amount")
    escalated: bool = Field(default=False, description="Whether the case was escalated")
    resolved: bool = Field(default=False, description="Whether the case is resolved")
    progress_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Current score")
    max_steps: int = Field(default=4, ge=1, description="Episode step budget")

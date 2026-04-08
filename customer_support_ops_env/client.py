# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Client for the customer support operations environment."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult

from .models import CustomerSupportOpsAction, CustomerSupportOpsObservation, CustomerSupportOpsState


class CustomerSupportOpsEnv(
    EnvClient[CustomerSupportOpsAction, CustomerSupportOpsObservation, CustomerSupportOpsState]
):
    """WebSocket client for the customer support operations environment."""

    def _step_payload(self, action: CustomerSupportOpsAction) -> Dict:
        return action.model_dump()

    def _parse_result(self, payload: Dict) -> StepResult[CustomerSupportOpsObservation]:
        obs_data = payload.get("observation", {})
        observation = CustomerSupportOpsObservation(
            task_id=obs_data.get("task_id", ""),
            difficulty=obs_data.get("difficulty", "easy"),
            status=obs_data.get("status", "ready"),
            ticket_summary=obs_data.get("ticket_summary", ""),
            customer_message=obs_data.get("customer_message", ""),
            policy_summary=obs_data.get("policy_summary", ""),
            available_operations=obs_data.get("available_operations", []),
            current_queue=obs_data.get("current_queue", ""),
            current_priority=obs_data.get("current_priority", ""),
            current_tags=obs_data.get("current_tags", []),
            notes_written=obs_data.get("notes_written", []),
            last_reply=obs_data.get("last_reply", ""),
            progress_score=obs_data.get("progress_score", 0.0),
            component_scores=obs_data.get("component_scores", {}),
            remaining_objectives=obs_data.get("remaining_objectives", []),
            last_feedback=obs_data.get("last_feedback", []),
            done=payload.get("done", False),
            reward=payload.get("reward"),
            metadata=obs_data.get("metadata", {}),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> CustomerSupportOpsState:
        return CustomerSupportOpsState(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
            task_id=payload.get("task_id", ""),
            difficulty=payload.get("difficulty", "easy"),
            current_queue=payload.get("current_queue", ""),
            current_priority=payload.get("current_priority", ""),
            current_tags=payload.get("current_tags", []),
            notes_written=payload.get("notes_written", []),
            last_reply=payload.get("last_reply", ""),
            resolution_code=payload.get("resolution_code", ""),
            refund_amount=payload.get("refund_amount", 0.0),
            escalated=payload.get("escalated", False),
            resolved=payload.get("resolved", False),
            progress_score=payload.get("progress_score", 0.0),
            max_steps=payload.get("max_steps", 4),
        )

# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Deterministic customer support task fixtures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class TaskExpectation:
    queue: str
    priority: str
    tags: List[str]
    note_keywords: List[str]
    reply_keywords: List[str]
    reply_empathy_keywords: List[str]
    resolution_code: str
    refund_amount: float
    escalate: bool


@dataclass(frozen=True)
class SupportTask:
    task_id: str
    difficulty: str
    title: str
    ticket_summary: str
    customer_message: str
    policy_summary: str
    constraints: List[str]
    expectation: TaskExpectation
    grader_name: str
    grader_module: str
    grader_function: str


TASKS: Dict[str, SupportTask] = {
    "easy_refund_renewal": SupportTask(
        task_id="easy_refund_renewal",
        difficulty="easy",
        title="Billing refund for accidental renewal",
        ticket_summary="A customer says they canceled a Pro annual plan but were charged at renewal this morning.",
        customer_message=(
            "I turned off auto-renew last night but still got charged $120 today for another year of Pro. "
            "I have not used the account since then. Please reverse it."
        ),
        policy_summary="Annual renewals canceled within 24 hours and with no post-renewal usage are fully refundable.",
        constraints=[
            "Route billing cases to the billing queue.",
            "Use high priority for customer-impacting billing errors.",
            "Reply should confirm the refund amount and timeframe.",
        ],
        expectation=TaskExpectation(
            queue="billing",
            priority="high",
            tags=["billing", "refund", "renewal"],
            note_keywords=["120", "auto-renew", "24 hours", "no usage"],
            reply_keywords=["refund", "$120", "3-5 business days"],
            reply_empathy_keywords=["sorry", "understand"],
            resolution_code="refund",
            refund_amount=120.0,
            escalate=False,
        ),
        grader_name="grade_easy_refund_renewal",
        grader_module="graders.easy_refund_renewal",
        grader_function="grade",
    ),
    "medium_replacement_delay": SupportTask(
        task_id="medium_replacement_delay",
        difficulty="medium",
        title="Replacement for VIP shipment error",
        ticket_summary="A VIP customer received the wrong item and needs a replacement sent overnight before a conference.",
        customer_message=(
            "I ordered two conference demo kits for tomorrow, but one box has the wrong charging dock. "
            "I am a Premier customer and need the correct unit overnighted today."
        ),
        policy_summary=(
            "Premier customers with fulfillment errors qualify for free overnight replacements. "
            "Do not ask for the incorrect item back before sending the replacement."
        ),
        constraints=[
            "Route shipping and warehouse issues to fulfillment.",
            "Use urgent priority when the failure blocks an imminent event.",
            "Reply should promise overnight replacement and confirm no return is needed first.",
        ],
        expectation=TaskExpectation(
            queue="fulfillment",
            priority="urgent",
            tags=["shipping_delay", "replacement", "vip"],
            note_keywords=["Premier", "overnight", "conference", "wrong charging dock"],
            reply_keywords=["overnight", "replacement", "no need to return"],
            reply_empathy_keywords=["sorry", "fix this quickly"],
            resolution_code="replacement",
            refund_amount=0.0,
            escalate=False,
        ),
        grader_name="grade_medium_replacement_delay",
        grader_module="graders.medium_replacement_delay",
        grader_function="grade",
    ),
    "hard_account_takeover": SupportTask(
        task_id="hard_account_takeover",
        difficulty="hard",
        title="Account takeover with fraudulent purchases",
        ticket_summary="A customer reports an account takeover, exported contacts, and unauthorized purchases.",
        customer_message=(
            "Someone logged into my account from another country, exported my contacts, and bought $480 in add-ons. "
            "I cannot log in anymore. Please lock the account and tell me what happens next."
        ),
        policy_summary=(
            "Suspected account takeovers must be routed to account_security, marked urgent, and escalated. "
            "Frontline agents must not promise immediate reimbursement, but should confirm account lock and specialist follow-up."
        ),
        constraints=[
            "Treat account takeover as urgent security work.",
            "Escalate to the security team instead of resolving directly with a refund.",
            "Reply should confirm account lock, escalation, and next-step guidance.",
        ],
        expectation=TaskExpectation(
            queue="account_security",
            priority="urgent",
            tags=["security", "account_takeover", "fraud"],
            note_keywords=["480", "exported contacts", "cannot log in", "another country"],
            reply_keywords=["locked", "security team", "next steps"],
            reply_empathy_keywords=["sorry", "take this seriously"],
            resolution_code="security_escalation",
            refund_amount=0.0,
            escalate=True,
        ),
        grader_name="grade_hard_account_takeover",
        grader_module="graders.hard_account_takeover",
        grader_function="grade",
    ),
}


TASK_ORDER: List[str] = [
    "easy_refund_renewal",
    "medium_replacement_delay",
    "hard_account_takeover",
]


TASKS_WITH_GRADERS: List[dict[str, str]] = [
    {
        "task_id": TASKS[task_id].task_id,
        "grader_name": TASKS[task_id].grader_name,
        "grader_module": TASKS[task_id].grader_module,
        "grader_function": TASKS[task_id].grader_function,
    }
    for task_id in TASK_ORDER
]


def get_task(task_id: str) -> SupportTask:
    """Return a task by id."""
    return TASKS[task_id]


def select_task_by_seed(seed: int | None) -> SupportTask:
    """Deterministically select a task from a seed."""
    if seed is None:
        return TASKS[TASK_ORDER[0]]
    return TASKS[TASK_ORDER[seed % len(TASK_ORDER)]]

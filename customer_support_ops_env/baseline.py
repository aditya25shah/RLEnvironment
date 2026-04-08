# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Baseline policy with reproducible task scores."""

from __future__ import annotations

from statistics import mean

from .models import CustomerSupportOpsAction
from .server.customer_support_ops_env_environment import CustomerSupportOpsEnvironment
from .tasks import TASK_ORDER


def run_task(env: CustomerSupportOpsEnvironment, task_id: str) -> float:
    """Run a deterministic heuristic policy for a task and return the final score."""
    env.reset(task_id=task_id)

    if task_id == "easy_refund_renewal":
        env.step(CustomerSupportOpsAction(operation="triage", queue="billing", priority="high", tags=["billing", "refund", "renewal"]))
        env.step(CustomerSupportOpsAction(operation="note", internal_note="Customer was charged 120 after auto-renew, contacted us within 24 hours, and shows no usage."))
        env.step(CustomerSupportOpsAction(operation="reply", reply_text="I am sorry about the renewal charge and understand the frustration. I have approved a $120 refund and it should appear in 3-5 business days."))
        final = env.step(CustomerSupportOpsAction(operation="resolve", resolution_code="refund", refund_amount=120.0, escalate=False, mark_resolved=True))
        return final.progress_score

    if task_id == "medium_replacement_delay":
        env.step(CustomerSupportOpsAction(operation="triage", queue="fulfillment", priority="urgent", tags=["shipping_delay", "replacement", "vip"]))
        env.step(CustomerSupportOpsAction(operation="note", internal_note="Premier customer needs overnight replacement for a conference because the shipment included the wrong charging dock."))
        env.step(CustomerSupportOpsAction(operation="reply", reply_text="I am sorry for the shipment error and will fix this quickly. We are sending an overnight replacement today, and there is no need to return the incorrect item before we ship."))
        final = env.step(CustomerSupportOpsAction(operation="resolve", resolution_code="replacement", refund_amount=0.0, escalate=False, mark_resolved=True))
        return final.progress_score

    env.step(CustomerSupportOpsAction(operation="triage", queue="account_security", priority="urgent", tags=["security", "account_takeover", "fraud"]))
    env.step(CustomerSupportOpsAction(operation="note", internal_note="Unauthorized purchases totaling 480 were made after a login from another country, the attacker exported contacts, and the customer cannot log in."))
    env.step(CustomerSupportOpsAction(operation="reply", reply_text="I am sorry this happened and we take this seriously. I have locked the account, escalated this to our security team, and they will send next steps after reviewing the unauthorized activity."))
    final = env.step(CustomerSupportOpsAction(operation="resolve", resolution_code="security_escalation", refund_amount=0.0, escalate=True, mark_resolved=True))
    return final.progress_score


def main() -> None:
    env = CustomerSupportOpsEnvironment()
    scores = {task_id: run_task(env, task_id) for task_id in TASK_ORDER}
    for task_id, score in scores.items():
        print(f"{task_id}: {score:.4f}")
    print(f"mean_score: {mean(scores.values()):.4f}")


if __name__ == "__main__":
    main()

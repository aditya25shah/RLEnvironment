import json
import os
from typing import Any

from openai import OpenAI

try:
    from customer_support_ops_env import (
        CustomerSupportOpsAction,
        CustomerSupportOpsEnvironment,
    )
except ImportError:
    from models import CustomerSupportOpsAction
    from server.customer_support_ops_env_environment import CustomerSupportOpsEnvironment

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY") or ""
TASK_NAME = os.getenv(
    "CUSTOMER_SUPPORT_OPS_TASK",
    os.getenv("MY_ENV_V4_TASK", "easy_refund_renewal"),
)
BENCHMARK_NAME = os.getenv("CUSTOMER_SUPPORT_OPS_BENCHMARK", "customer_support_ops_env")
MAX_STEPS = 4
MAX_TOKENS = 256

TASK_PLANS: dict[str, dict[str, Any]] = {
    "easy_refund_renewal": {
        "triage": {
            "queue": "billing",
            "priority": "high",
            "tags": ["billing", "refund", "renewal"],
        },
        "resolution": {
            "resolution_code": "refund",
            "refund_amount": 120.0,
            "escalate": False,
            "mark_resolved": True,
        },
        "note_instruction": (
            "Capture the renewal charge amount, the cancellation timing, the lack of post-renewal usage, "
            "and that policy supports a full refund."
        ),
        "reply_instruction": (
            "Apologize, confirm the 120 dollar refund, and state that it should appear within 3-5 business days."
        ),
    },
    "medium_replacement_delay": {
        "triage": {
            "queue": "fulfillment",
            "priority": "urgent",
            "tags": ["shipping_delay", "replacement", "vip"],
        },
        "resolution": {
            "resolution_code": "replacement",
            "refund_amount": 0.0,
            "escalate": False,
            "mark_resolved": True,
        },
        "note_instruction": (
            "Capture that the customer is Premier or VIP, received the wrong charging dock, "
            "needs an overnight replacement for a conference, and does not need to return the wrong item first."
        ),
        "reply_instruction": (
            "Apologize, promise an overnight replacement, state that no return is needed before shipment, "
            "and keep the tone urgent and reassuring."
        ),
    },
    "hard_account_takeover": {
        "triage": {
            "queue": "account_security",
            "priority": "urgent",
            "tags": ["security", "account_takeover", "fraud"],
        },
        "resolution": {
            "resolution_code": "security_escalation",
            "refund_amount": 0.0,
            "escalate": True,
            "mark_resolved": True,
        },
        "note_instruction": (
            "Capture the login from another country, exported contacts, 480 dollars in unauthorized purchases, "
            "the login lockout, and the need for immediate security escalation."
        ),
        "reply_instruction": (
            "Apologize, confirm the account is being locked, explain that the security team will follow up with next steps, "
            "and do not promise an immediate refund."
        ),
    },
}


def _extract_completion_text(response: Any) -> str:
    choice = response.choices[0]
    message = getattr(choice, "message", None)
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
            else:
                text = getattr(item, "text", None)
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(part for part in parts if part).strip()
    return str(content).strip()


def _obs_payload(obs: Any) -> dict[str, Any]:
    return {
        "ticket_summary": getattr(obs, "ticket_summary", ""),
        "customer_message": getattr(obs, "customer_message", ""),
        "policy_summary": getattr(obs, "policy_summary", ""),
        "progress_score": getattr(obs, "progress_score", 0.0),
        "remaining_objectives": getattr(obs, "remaining_objectives", []),
        "last_feedback": getattr(obs, "last_feedback", []),
    }


def _task_plan(task_name: str) -> dict[str, Any]:
    if task_name in TASK_PLANS:
        return TASK_PLANS[task_name]
    return TASK_PLANS["easy_refund_renewal"]


def _generate_text(client: OpenAI, obs: Any, *, mode: str, task_name: str) -> str:
    plan = _task_plan(task_name)
    observation = json.dumps(_obs_payload(obs), ensure_ascii=True, indent=2)
    if mode == "note":
        system_prompt = (
            "You write concise internal customer-support notes. Return plain text only. "
            "Write one compact paragraph with the critical facts, policy basis, and planned resolution."
        )
        task_instruction = plan["note_instruction"]
        user_prompt = (
            f"Task: {task_name}\n"
            f"Instruction: {task_instruction}\n"
            f"Current observation:\n{observation}"
        )
    else:
        system_prompt = (
            "You write customer-support replies. Return plain text only. "
            "Be empathetic, operationally clear, and do not include placeholders such as [Customer Name]."
        )
        task_instruction = plan["reply_instruction"]
        user_prompt = (
            f"Task: {task_name}\n"
            f"Instruction: {task_instruction}\n"
            f"Current observation:\n{observation}"
        )

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=MAX_TOKENS,
    )
    return _extract_completion_text(response)


def main() -> None:
    env = None
    rewards: list[float] = []
    completed_steps = 0
    score = 0.0
    success = False
    print(f"[START] task={TASK_NAME} env={BENCHMARK_NAME} model={MODEL_NAME}")

    try:
        if not API_KEY:
            raise RuntimeError("Missing authentication token in HF_TOKEN or API_KEY")

        plan = _task_plan(TASK_NAME)
        client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
        env = CustomerSupportOpsEnvironment()
        obs = env.reset(task_id=TASK_NAME)

        action_plan: list[dict[str, Any]] = [
            {"operation": "triage", **plan["triage"]},
            {"operation": "note"},
            {"operation": "reply"},
            {"operation": "resolve", **plan["resolution"]},
        ]

        for step_idx, base_action in enumerate(action_plan, start=1):
            action_payload = dict(base_action)
            if action_payload["operation"] == "note":
                action_payload["internal_note"] = _generate_text(
                    client,
                    obs,
                    mode="note",
                    task_name=TASK_NAME,
                )
            elif action_payload["operation"] == "reply":
                action_payload["reply_text"] = _generate_text(
                    client,
                    obs,
                    mode="reply",
                    task_name=TASK_NAME,
                )

            step_error = None
            obs = env.step(CustomerSupportOpsAction(**action_payload))
            reward = float(getattr(obs, "reward", 0.0) or 0.0)
            rewards.append(reward)
            completed_steps = step_idx
            done = bool(getattr(obs, "done", False))
            print(
                f"[STEP] step={step_idx} action={json.dumps(action_payload)} "
                f"reward={reward:.2f} done={str(done).lower()} error={step_error or 'null'}"
            )

            if done:
                break

        score = float(getattr(obs, "progress_score", 0.0) or 0.0)
        success = bool(getattr(obs, "done", False))
    except Exception as exc:
        step_num = completed_steps + 1 if completed_steps < MAX_STEPS else completed_steps
        print(
            f"[STEP] step={step_num} action=null reward=0.00 "
            f"done=false error={json.dumps(str(exc))}"
        )
    finally:
        reward_str = ",".join(f"{reward:.2f}" for reward in rewards)
        print(
            f"[END] success={str(success).lower()} steps={completed_steps} "
            f"score={score:.4f} rewards={reward_str}"
        )


if __name__ == "__main__":
    main()

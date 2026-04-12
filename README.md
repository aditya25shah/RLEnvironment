---
title: Customer Support Ops Environment
emoji: "🎧"
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8000
---

# Customer Support Ops Environment

`customer_support_ops_env` is a deterministic OpenEnv environment for customer-support workflows. Each episode requires exactly four actions in order:

1. `triage`
2. `note`
3. `reply`
4. `resolve`

The environment is live on Hugging Face:

`https://huggingface.co/spaces/aditya25shah/customer_support_ops_env`

## Tasks

- `easy_refund_renewal`: billing refund for an accidental renewal
- `medium_replacement_delay`: urgent replacement for a VIP fulfillment mistake
- `hard_account_takeover`: urgent security escalation for an account takeover

Explicit task-to-grader mapping:

- `easy_refund_renewal` -> `grade_easy_refund_renewal`
- `medium_replacement_delay` -> `grade_medium_replacement_delay`
- `hard_account_takeover` -> `grade_hard_account_takeover`

## Action Model

Each `CustomerSupportOpsAction` supports these fields:

- `operation`: `triage`, `note`, `reply`, or `resolve`
- `queue`: `billing`, `fulfillment`, or `account_security`
- `priority`: `normal`, `high`, or `urgent`
- `tags`: case tags
- `internal_note`: internal support note text
- `reply_text`: customer-facing reply text
- `resolution_code`: `refund`, `replacement`, or `security_escalation`
- `refund_amount`: refund amount when applicable
- `escalate`: whether the case should be escalated
- `mark_resolved`: whether to end the case

## Observation Fields

Each observation contains:

- `ticket_summary`
- `customer_message`
- `policy_summary`
- `progress_score`
- `remaining_objectives`
- `last_feedback`
- `done`
- `reward`

## Reward Model

The total task score is normalized to `[0.0, 1.0]` and is split across:

- triage: `0.35`
- internal note: `0.20`
- reply quality: `0.25`
- final resolution: `0.20`

Per-step reward is incremental:

```text
reward_t = max(0, score_t - score_(t-1))
```

## Local Setup

```bash
cd customer_support_ops_env
uv sync
```

Run the server locally:

```bash
uvicorn server.app:app --reload
```

Or:

```bash
uv run --project . server
```

## Direct Python Usage

```python
from customer_support_ops_env import CustomerSupportOpsAction, CustomerSupportOpsEnvironment

env = CustomerSupportOpsEnvironment()
obs = env.reset(task_id="easy_refund_renewal")

obs = env.step(
    CustomerSupportOpsAction(
        operation="triage",
        queue="billing",
        priority="high",
        tags=["billing", "refund", "renewal"],
    )
)

print(obs.progress_score, obs.reward, obs.remaining_objectives)
```

## Baseline

The deterministic baseline solves all three tasks perfectly:

```bash
python -m customer_support_ops_env.baseline
```

Expected output:

```text
easy_refund_renewal: 1.0000
medium_replacement_delay: 1.0000
hard_account_takeover: 1.0000
mean_score: 1.0000
```

## Inference Runner

The repo includes `inference.py`, which:

- uses the synchronous `CustomerSupportOpsEnvironment`
- preserves the `[START]`, `[STEP]`, `[END]` logging format
- chooses the correct 4-step workflow for each task
- uses the current observation fields for the `note` and `reply` LLM calls

Required environment variables:

- `API_BASE_URL`: LLM API base URL
- `MODEL_NAME`: model identifier used for inference
- `HF_TOKEN`: Hugging Face / API token passed to the OpenAI client

These required variables are also declared in [`openenv.yaml`](./openenv.yaml), and the inference entrypoint is the root-level `inference.py`.

Run it from inside this directory:

```bash
export API_BASE_URL="https://router.huggingface.co/v1"
export HF_TOKEN="hf_your_token"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export CUSTOMER_SUPPORT_OPS_TASK="easy_refund_renewal"
python inference.py
```

Backward-compatible alias:

```bash
export MY_ENV_V4_TASK="easy_refund_renewal"
python inference.py
```

## Playground Note

The default OpenEnv Playground renders `tags` as a text field. This repo now accepts all of these formats:

- `billing`
- `billing, refund, renewal`
- `["billing", "refund", "renewal"]`

For the refund task, the correct triage values are:

- `operation`: `triage`
- `queue`: `billing`
- `priority`: `high`
- `tags`: `billing, refund, renewal`

## API Example

```python
import requests

base_url = "https://aditya25shah-customer-support-ops-env.hf.space"

requests.post(
    f"{base_url}/reset",
    json={"task_id": "easy_refund_renewal"},
    timeout=30,
)

response = requests.post(
    f"{base_url}/step",
    json={
        "operation": "triage",
        "queue": "billing",
        "priority": "high",
        "tags": ["billing", "refund", "renewal"],
    },
    timeout=30,
)

print(response.json())
```

Validation-friendly endpoints:

- `GET /tasks`: lists all available tasks and marks each as having a grader
- `GET /validate`: returns a compact self-check payload with task counts

## Deployment

Validate locally:

```bash
openenv validate .
```

Deploy to Hugging Face:

```bash
openenv push .
```

## Project Files

- `models.py`: action, observation, and state models
- `tasks.py`: deterministic task fixtures
- `graders.py`: task-specific grading logic
- `baseline.py`: deterministic perfect-score baseline
- `inference.py`: LLM-driven runner with fixed 4-step control flow
- `server/customer_support_ops_env_environment.py`: synchronous environment implementation
- `server/app.py`: FastAPI and OpenEnv server entrypoint
- `Dockerfile`: deployment image for Hugging Face Spaces
- `openenv.yaml`: environment manifest
"# RLEnvironment" 

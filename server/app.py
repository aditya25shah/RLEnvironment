# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
FastAPI application for the Customer Support Ops Env Environment.

This module creates an HTTP server that exposes the CustomerSupportOpsEnvironment
over HTTP and WebSocket endpoints, compatible with EnvClient.

Endpoints:
    - POST /reset: Reset the environment
    - POST /step: Execute an action
    - GET /state: Get current environment state
    - GET /schema: Get action/observation schemas
    - WS /ws: WebSocket endpoint for persistent sessions

Usage:
    # Development (with auto-reload):
    uvicorn server.app:app --reload --host 0.0.0.0 --port 8000

    # Production:
    uvicorn server.app:app --host 0.0.0.0 --port 8000 --workers 4

    # Or run directly:
    python -m server.app
"""

import json
from pathlib import Path

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:  # pragma: no cover
    raise ImportError(
        "openenv is required for the web interface. Install dependencies with '\n    uv sync\n'"
    ) from e

try:
    from ..models import CustomerSupportOpsAction, CustomerSupportOpsObservation
    from ..tasks import TASK_ORDER, TASKS
    from .customer_support_ops_env_environment import CustomerSupportOpsEnvironment
except ImportError:
    from models import CustomerSupportOpsAction, CustomerSupportOpsObservation
    from tasks import TASK_ORDER, TASKS
    from server.customer_support_ops_env_environment import CustomerSupportOpsEnvironment


# Create the app with web interface and README integration
app = create_app(
    CustomerSupportOpsEnvironment,
    CustomerSupportOpsAction,
    CustomerSupportOpsObservation,
    env_name="customer_support_ops_env",
    max_concurrent_envs=1,  # increase this number to allow more concurrent WebSocket sessions
)


def _task_rows() -> list[dict[str, object]]:
    """Build a validator-friendly task listing with explicit grader metadata."""
    tasks: list[dict[str, object]] = []
    for task_id in TASK_ORDER:
        task = TASKS[task_id]
        tasks.append(
            {
                "id": task.task_id,
                "task_id": task.task_id,
                "difficulty": task.difficulty,
                "title": task.title,
                "description": task.ticket_summary,
                "has_grader": True,
                "grader": task.grader_path,
                "grader_name": task.grader_name,
                "grader_module": task.grader_module,
                "grader_function": task.grader_function,
                "grader_spec": {
                    "module": task.grader_module,
                    "function": task.grader_function,
                },
                "max_steps": 4,
                "task_file": f"tasks/{task.task_id}.json",
                "grader_file": f"graders/{task.task_id}.py",
            }
        )
    return tasks


def _task_manifest_rows() -> list[dict[str, object]]:
    """Build a single canonical manifest shape for validator-facing endpoints."""
    rows: list[dict[str, object]] = []
    for task in _task_rows():
        rows.append(
            {
                "task_id": task["task_id"],
                "id": task["id"],
                "title": task["title"],
                "description": task["description"],
                "difficulty": task["difficulty"],
                "max_steps": task["max_steps"],
                "has_grader": task["has_grader"],
                "grader": task["grader"],
                "grader_name": task["grader_name"],
                "grader_module": task["grader_module"],
                "grader_function": task["grader_function"],
                "grader_file": task["grader_file"],
                "task_file": task["task_file"],
            }
        )
    return rows


def _load_manifest(relative_path: str) -> dict[str, object]:
    manifest_path = Path(__file__).resolve().parents[1] / relative_path
    return json.loads(manifest_path.read_text(encoding="utf-8"))


@app.get("/tasks")
def list_tasks() -> dict[str, list[dict[str, object]]]:
    """List all available tasks and whether a grader exists for each."""
    return {"tasks": _task_rows()}


@app.get("/task_manifest.json")
@app.get("/task_manifest")
def task_manifest() -> dict[str, object]:
    """Expose a static-style task manifest for validators that inspect JSON files."""
    return {
        "env_name": "customer_support_ops_env",
        "num_tasks": len(TASK_ORDER),
        "tasks": _task_manifest_rows(),
    }


@app.get("/tasks/manifest.json")
def tasks_manifest() -> dict[str, object]:
    """Expose the richer tasks manifest with file-level task and grader metadata."""
    return {
        "env_name": "customer_support_ops_env",
        "num_tasks": len(TASK_ORDER),
        "tasks": _task_manifest_rows(),
    }


@app.get("/tasks/{task_id}.json")
def task_json(task_id: str) -> dict[str, object]:
    """Expose task JSON files directly for validators that fetch them over HTTP."""
    return _load_manifest(f"tasks/{task_id}.json")


@app.get("/validate")
def validate() -> dict[str, object]:
    """Return a compact self-check payload for hackathon validators."""
    tasks = _task_rows()
    task_ids = [task["task_id"] for task in tasks]
    graded_tasks = [task for task in tasks if task["grader_name"]]
    checks = {
        "min_3_tasks": len(task_ids) >= 3,
        "all_tasks_have_graders": len(graded_tasks) == len(task_ids),
        "min_3_graded_tasks": len(graded_tasks) >= 3,
        "task_ids": task_ids,
        "num_tasks": len(task_ids),
        "num_graded_tasks": len(graded_tasks),
    }
    return {
        "valid": bool(
            checks["min_3_tasks"]
            and checks["all_tasks_have_graders"]
            and checks["min_3_graded_tasks"]
        ),
        "checks": checks,
        "tasks": tasks,
        "env_name": "customer_support_ops_env",
    }


def main(host: str = "0.0.0.0", port: int = 8000):
    """
    Entry point for direct execution via uv run or python -m.

    This function enables running the server without Docker:
        uv run --project . server
        uv run --project . server --port 8001
        python -m customer_support_ops_env.server.app

    Args:
        host: Host address to bind to (default: "0.0.0.0")
        port: Port number to listen on (default: 8000)

    For production deployments, consider using uvicorn directly with
    multiple workers:
        uvicorn customer_support_ops_env.server.app:app --workers 4
    """
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == '__main__':
    main()

"""Validator-facing grader entrypoint for hard_account_takeover."""

try:
    from graders.hard_account_takeover import grade
except ImportError:
    from customer_support_ops_env.graders.hard_account_takeover import grade

__all__ = ["grade"]

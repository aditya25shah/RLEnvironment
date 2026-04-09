"""Explicit grader entrypoint for hard_account_takeover."""

try:
    from customer_support_ops_env.graders import grade_hard_account_takeover
except ImportError:
    from graders import grade_hard_account_takeover

grade = grade_hard_account_takeover

__all__ = ["grade", "grade_hard_account_takeover"]

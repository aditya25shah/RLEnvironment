"""Explicit grader entrypoint for medium_replacement_delay."""

try:
    from customer_support_ops_env.graders import grade_medium_replacement_delay
except ImportError:
    from graders import grade_medium_replacement_delay

__all__ = ["grade_medium_replacement_delay"]

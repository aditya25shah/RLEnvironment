"""Validator-facing grader entrypoint for medium_replacement_delay."""

try:
    from graders.medium_replacement_delay import grade
except ImportError:
    from customer_support_ops_env.graders.medium_replacement_delay import grade

__all__ = ["grade"]

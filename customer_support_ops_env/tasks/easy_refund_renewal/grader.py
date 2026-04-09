"""Validator-facing grader entrypoint for easy_refund_renewal."""

try:
    from graders.easy_refund_renewal import grade
except ImportError:
    from customer_support_ops_env.graders.easy_refund_renewal import grade

__all__ = ["grade"]

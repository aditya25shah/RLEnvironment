"""Explicit grader entrypoint for easy_refund_renewal."""

try:
    from customer_support_ops_env.graders import grade_easy_refund_renewal
except ImportError:
    from graders import grade_easy_refund_renewal

grade = grade_easy_refund_renewal

__all__ = ["grade", "grade_easy_refund_renewal"]

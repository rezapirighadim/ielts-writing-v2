"""
Custom exceptions for usage limit system.
"""


class LimitExceededException(Exception):
    """
    Exception raised when user exceeds their usage limit.

    Python Concept: Custom exceptions provide specific error handling
    for different types of limit violations.
    """

    def __init__(self, message: str, limit_type: str = "monthly", current_usage: int = 0, limit: int = 0):
        super().__init__(message)
        self.limit_type = limit_type
        self.current_usage = current_usage
        self.limit = limit

    def __str__(self) -> str:
        return f"Limit exceeded: {super().__str__()} (Usage: {self.current_usage}/{self.limit})"


class InvalidLimitException(Exception):
    """Exception raised when invalid limit configuration is encountered."""

    def __init__(self, message: str, limit_value: int = None):
        super().__init__(message)
        self.limit_value = limit_value

    def __str__(self) -> str:
        return f"Invalid limit: {super().__str__()}"
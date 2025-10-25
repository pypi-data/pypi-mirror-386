"""OpenAI-specific triggers for human review."""

from typing import Any, Dict

from ...enums import ReviewType


class OpenAIToolCallTrigger:
    """Trigger review when OpenAI tool/function calls are present."""

    def __init__(self, review_type: ReviewType = ReviewType.APPROVE):
        self.review_type = review_type

    def should_review(
        self, response: Any, request_kwargs: Dict[str, Any]
    ) -> tuple[bool, ReviewType | None]:
        """Check if response contains tool or function calls."""
        if self._contains_tool_calls(response):
            return True, self.review_type
        return False, None

    def _contains_tool_calls(self, response: Any) -> bool:
        """Check if the OpenAI response contains tool calls."""
        try:
            message = response.choices[0].message
            return bool(
                getattr(message, "function_call", None)
                or getattr(message, "tool_calls", None)
            )
        except (AttributeError, IndexError):
            return False

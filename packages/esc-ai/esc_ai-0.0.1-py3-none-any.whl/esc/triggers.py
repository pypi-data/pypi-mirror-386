"""Base trigger protocol that all provider-specific triggers implement."""

from typing import Any, Dict, Protocol, runtime_checkable

from .enums import ReviewType


@runtime_checkable
class Trigger(Protocol):
    """
    Protocol for review triggers across all LLM providers.

    Provider-specific triggers are located in their respective integration modules.
    For example:
    - OpenAI triggers: esc.integrations.openai
    - Anthropic triggers: esc.integrations.anthropic

    Examples
    --------
    >>> from esc.integrations.openai import OpenAIToolCallTrigger
    >>> from esc.integrations.anthropic import AnthropicToolCallTrigger
    """

    def should_review(
        self, response: Any, request_kwargs: Dict[str, Any]
    ) -> tuple[bool, ReviewType | None]:
        """
        Determine if a response should be reviewed.

        Parameters
        ----------
        response : Any
            The LLM response object (provider-specific).
        request_kwargs : Dict[str, Any]
            The original request parameters.

        Returns
        -------
        tuple[bool, ReviewType | None]
            (should_review, review_type). If False, review_type should be None.
        """
        ...

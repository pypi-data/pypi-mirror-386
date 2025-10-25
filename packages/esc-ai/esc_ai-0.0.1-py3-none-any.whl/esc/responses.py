import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .enums import ReviewType, Status


class ReviewContext(BaseModel):
    """Context sent to human reviewers."""

    review_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    review_type: ReviewType
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model: str
    messages: List[Dict[str, Any]]
    temperature: Optional[float] = None
    tools: Optional[List[Dict[str, Any]]] = None
    llm_response: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    callback_url: Optional[str] = None


class EscResponse(BaseModel):
    """
    Unified response from esc-wrapped LLM calls.

    This response wraps the underlying LLM response and adds
    escalation metadata when human review is required.

    Examples
    --------
    >>> response = client.chat.completions.create(...)
    >>> if response.is_approved:
    ...     print(response.ai_response.choices[0].message.content)
    >>> else:
    ...     print(f"Review needed: {response.review_id}")
    """

    status: Status
    review_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # LLM response (None if in review)
    ai_response: Optional[Any] = None

    # Review metadata (None if approved)
    review_type: Optional[ReviewType] = None
    review_context: Optional[ReviewContext] = None
    message: Optional[str] = None

    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_approved(self) -> bool:
        """Check if response was approved (no review needed)."""
        return self.status == Status.APPROVED

    @property
    def is_in_review(self) -> bool:
        """Check if response is pending human review."""
        return self.status == Status.IN_REVIEW

    @property
    def is_rejected(self) -> bool:
        """Check if response was rejected after review."""
        return self.status == Status.REJECTED

    def unwrap(self) -> Any:
        """
        Get the LLM response or raise if not approved.

        Raises
        ------
        ValueError
            If status is not APPROVED.

        Examples
        --------
        >>> try:
        ...     llm_resp = response.unwrap()
        ...     print(llm_resp.choices[0].message.content)
        ... except ValueError:
        ...     print("Response needs review")
        """
        if not self.is_approved:
            raise ValueError(
                f"Response status is {self.status.value}, cannot unwrap. "
                f"Review ID: {self.review_id}"
            )
        return self.ai_response

    def unwrap_or(self, default: Any = None) -> Any:
        """
        Get the LLM response or return default if not approved.

        Parameters
        ----------
        default : Any, optional
            Value to return if response is not approved.
        """
        return self.ai_response if self.is_approved else default

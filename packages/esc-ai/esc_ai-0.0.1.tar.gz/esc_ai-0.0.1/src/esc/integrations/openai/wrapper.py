"""Wrapper for OpenAI client to easily add human in the loop after the LLM calls."""

import logging
import uuid
from functools import wraps
from typing import TYPE_CHECKING, Any, Dict, List, Optional

try:
    import openai

    HAVE_OPENAI = True
except ImportError:
    HAVE_OPENAI = False

if TYPE_CHECKING:
    import openai

from ...api import send_review_context
from ...enums import ReviewType, Status
from ...responses import EscResponse, ReviewContext
from ...triggers import Trigger

logger = logging.getLogger(__name__)


def wrap_openai(
    client: "openai.OpenAI",
) -> "openai.OpenAI":
    """Wraps the OpenAI client to easily add human in the loop after the LLM calls.

    Parameters
    ----------
    client : openai.OpenAI
        The OpenAI client to patch.
    triggers : Optional[List[Trigger]], optional
        List of triggers to determine when to escalate to human review.
        If None, no reviews will be triggered.
    webhook_url : Optional[str], optional
        URL to POST review contexts to when review is triggered.

    Returns
    -------
    openai.OpenAI
        The patched OpenAI client.

    Examples
    --------
    >>> from .triggers import OpenAIToolCallTrigger
    >>> from ...enums import ReviewType
    >>>
    >>> triggers = [OpenAIToolCallTrigger(review_type=ReviewType.APPROVE)]
    >>> client = wrap_openai(openai.OpenAI(), triggers=triggers)
    """
    if not HAVE_OPENAI:
        raise ImportError(
            "OpenAI library is not installed. Please install it with: "
            "pip install openai"
        )

    if not isinstance(client, (openai.OpenAI)):
        raise ValueError("Invalid client. Please provide an OpenAI client.")

    create_func = client.chat.completions.create

    @wraps(create_func)
    def wrapped_create_func(*args, **kwargs):
        stream = kwargs.get("stream", False)
        triggers = kwargs.pop("triggers", [])
        webhook_url = kwargs.pop("webhook_url", None)

        if stream:
            raise ValueError(
                "Can only add human in the loop to non-streaming calls."
                "Please set stream=False and try again."
            )

        return handle_non_streaming_create(
            *args,
            create_func=create_func,
            triggers=triggers,
            webhook_url=webhook_url,
            **kwargs,
        )

    client.chat.completions.create = wrapped_create_func
    return client


def handle_non_streaming_create(
    create_func: callable,
    *args,
    triggers: List[Trigger],
    webhook_url: Optional[str] = None,
    **kwargs,
) -> EscResponse:
    """Handles the create method when streaming is disabled.

    Parameters
    ----------
    create_func : callable
        The create method to handle.
    triggers : List[Trigger]
        List of triggers to check for review conditions.
    webhook_url : Optional[str]
        URL to POST review contexts to.
    **kwargs
        Additional arguments passed to the create method.

    Returns
    -------
    EscResponse
        Unified response object with status and LLM response.
    """
    # Make the actual LLM call
    response = create_func(*args, **kwargs)

    # Check all triggers to see if any require review
    for trigger in triggers:
        should_review, review_type = trigger.should_review(response, kwargs)

        if should_review:
            # First trigger that fires wins
            return _create_escalation_response(
                response=response,
                request_kwargs=kwargs,
                review_type=review_type,
                webhook_url=webhook_url,
            )

    # No triggers fired - return approved response
    return EscResponse(
        status=Status.APPROVED,
        review_id=str(uuid.uuid4()),
        ai_response=response,
    )


def _create_escalation_response(
    response: "openai.types.chat.chat_completion.ChatCompletion",
    request_kwargs: Dict[str, Any],
    review_type: ReviewType,
    webhook_url: Optional[str] = None,
) -> EscResponse:
    """Create an escalation response with full context.

    Parameters
    ----------
    response : ChatCompletion
        The OpenAI response to review.
    request_kwargs : Dict[str, Any]
        The original request parameters.
    review_type : ReviewType
        The type of review needed.
    webhook_url : Optional[str]
        URL to POST the review context to.

    Returns
    -------
    EscResponse
        The escalation response with review context.
    """
    # Build the review context
    context = ReviewContext(
        review_type=review_type,
        model=request_kwargs.get("model", "unknown"),
        messages=request_kwargs.get("messages", []),
        temperature=request_kwargs.get("temperature"),
        tools=request_kwargs.get("tools"),
        llm_response=response.model_dump(),
    )

    # Send to webhook if configured
    if webhook_url:
        _send_to_webhook(webhook_url, context)

    return EscResponse(
        status=Status.IN_REVIEW,
        review_id=context.review_id,
        review_type=review_type,
        review_context=context,
        message="Response under review",
        ai_response=None,  # No AI response available during review
    )


def _send_to_webhook(webhook_url: str, context: ReviewContext) -> None:
    """Send review context to webhook URL.

    Parameters
    ----------
    webhook_url : str
        The URL to POST to.
    context : ReviewContext
        The review context to send.
    """
    send_review_context(url=webhook_url, context=context)

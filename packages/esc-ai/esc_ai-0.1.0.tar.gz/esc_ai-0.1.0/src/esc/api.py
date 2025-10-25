"""API client for external service communication."""

import logging
import time
from typing import Any, Dict, Optional

from .responses import ReviewContext

logger = logging.getLogger(__name__)


class WebhookClient:
    """
    Client for sending review contexts to webhook endpoints.

    Handles POST requests with automatic retries, timeout, and error handling.
    Failures are logged but don't raise exceptions to avoid breaking user workflows.

    Parameters
    ----------
    timeout : int, optional
        Request timeout in seconds. Default: 10.
    max_retries : int, optional
        Maximum number of retry attempts on failure. Default: 3.
    backoff_factor : float, optional
        Multiplier for exponential backoff between retries. Default: 2.0.
        Wait time = backoff_factor ^ (retry_number - 1) seconds.

    Examples
    --------
    >>> client = WebhookClient(timeout=5, max_retries=2)
    >>> success = client.send_review_context(
    ...     url="https://example.com/webhook",
    ...     context=review_context,
    ...     headers={"Authorization": "Bearer token"},
    ... )
    """

    def __init__(
        self,
        timeout: int = 10,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self._session = None

    def _get_session(self):
        """Lazy initialization of requests session."""
        if self._session is None:
            try:
                import requests

                self._session = requests.Session()
            except ImportError:
                raise ImportError(
                    "requests library is required for webhook functionality. "
                    "Install it with: pip install requests"
                )
        return self._session

    def send_review_context(
        self,
        url: str,
        context: ReviewContext,
        headers: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Send a review context to a webhook URL via POST request.

        The context is serialized to JSON and sent in the request body.
        If the request fails, it will be retried with exponential backoff.
        All errors are logged but not raised to avoid breaking user workflows.

        Parameters
        ----------
        url : str
            The webhook URL to POST to.
        context : ReviewContext
            The review context to send.
        headers : Optional[Dict[str, str]], optional
            Additional HTTP headers to include in the request.
            Common use: {"Authorization": "Bearer YOUR_TOKEN"}

        Returns
        -------
        bool
            True if the request succeeded, False if all retries failed.
        """
        if headers is None:
            headers = {}

        # Always set content-type to JSON
        headers.setdefault("Content-Type", "application/json")

        # Serialize context to JSON-compatible dict
        payload = context.model_dump(mode="json")

        session = self._get_session()

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(
                    "Sending review context to "
                    f"webhook (attempt {attempt}/{self.max_retries}): {url}"
                )

                response = session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )

                # Check if request was successful
                response.raise_for_status()

                logger.info(
                    f"Successfully sent review context {context.review_id} to {url}"
                )
                return True

            except Exception as e:
                logger.warning(
                    f"Webhook delivery attempt {attempt}/{self.max_retries} failed: {e}"
                )

                # If this was the last attempt, log error and give up
                if attempt == self.max_retries:
                    logger.error(
                        f"Failed to deliver review context {context.review_id} to {url} "
                        f"after {self.max_retries} attempts"
                    )
                    return False

                # Calculate backoff delay and wait before retrying
                delay = self.backoff_factor ** (attempt - 1)
                logger.debug(f"Retrying in {delay} seconds...")
                time.sleep(delay)

        return False

    def send_dict(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Send a raw dictionary payload to a webhook URL.

        Generic method for sending arbitrary JSON payloads.
        Useful for future extensions or custom notifications.

        Parameters
        ----------
        url : str
            The webhook URL to POST to.
        payload : Dict[str, Any]
            The data to send as JSON.
        headers : Optional[Dict[str, str]], optional
            Additional HTTP headers to include.

        Returns
        -------
        bool
            True if successful, False otherwise.
        """
        if headers is None:
            headers = {}

        headers.setdefault("Content-Type", "application/json")

        session = self._get_session()

        for attempt in range(1, self.max_retries + 1):
            try:
                response = session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                logger.info(f"Successfully sent payload to {url}")
                return True

            except Exception as e:
                logger.warning(f"Request attempt {attempt} failed: {e}")

                if attempt == self.max_retries:
                    logger.error(
                        f"Failed to send to {url} after {self.max_retries} attempts"
                    )
                    return False

                delay = self.backoff_factor ** (attempt - 1)
                time.sleep(delay)

        return False


# Global default client instance
_default_client = WebhookClient()


def send_review_context(
    url: str,
    context: ReviewContext,
    headers: Optional[Dict[str, str]] = None,
    client: Optional[WebhookClient] = None,
) -> bool:
    """
    Convenience function to send review context using default or custom client.

    Parameters
    ----------
    url : str
        Webhook URL to POST to.
    context : ReviewContext
        Review context to send.
    headers : Optional[Dict[str, str]], optional
        Additional HTTP headers.
    client : Optional[WebhookClient], optional
        Custom webhook client. If None, uses default client.

    Returns
    -------
    bool
        True if successful, False otherwise.
    """
    if client is None:
        client = _default_client

    return client.send_review_context(url, context, headers)

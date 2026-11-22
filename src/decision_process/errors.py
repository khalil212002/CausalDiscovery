"""Errors the decision process can run into, with messages fit to show users.

Every error from an outside service (Gemini, PubMed) is turned into one of
these, so callers only need to catch DecisionProcessError. Two flags on each
error tell the code what to do with it:

- retryable: trying again after a short wait may work (e.g. too many
  requests this minute, server briefly down). The clients retry these
  themselves before giving up.
- stops_search: every other pair would fail the same way (e.g. the daily
  quota is used up, or the API key is wrong), so domain_search stops instead
  of trying the remaining pairs.
"""


class DecisionProcessError(Exception):
    retryable = False
    stops_search = False

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.message = message  # safe to show to the user
        self.retry_after = retry_after  # seconds the service asked us to wait


# --- LLM -------------------------------------------------------------------

class LLMRateLimited(DecisionProcessError):
    """Too many requests in a short time (per-minute limit)."""

    retryable = True


class LLMQuotaExhausted(DecisionProcessError):
    """The daily quota is used up; it resets the next day."""

    stops_search = True


class LLMAuthError(DecisionProcessError):
    """Missing or invalid API key, or the model isn't available to it."""

    stops_search = True


class LLMUnavailable(DecisionProcessError):
    """The LLM service is down, overloaded, or can't be reached."""

    retryable = True


class LLMBadResponse(DecisionProcessError):
    """The LLM answered, but not in the format we asked for."""

    retryable = True


class LLMRequestError(DecisionProcessError):
    """The LLM rejected this request (e.g. the prompt is too long)."""


# --- PubMed ----------------------------------------------------------------

class PubMedUnavailable(DecisionProcessError):
    """PubMed is down, rate limiting us, or returned something unreadable."""

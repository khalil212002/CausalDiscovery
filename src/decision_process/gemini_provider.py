"""LLMProvider backed by Google's Gemini API (google-genai library)."""

import re
import time

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from decision_process.config import require_gemini_api_key
from decision_process.errors import (
    DecisionProcessError,
    LLMAuthError,
    LLMQuotaExhausted,
    LLMRateLimited,
    LLMRequestError,
    LLMUnavailable,
)
from decision_process.llm_provider import LLMProvider

# Retries for errors that may pass on their own (per-minute rate limit,
# server overloaded). The per-minute limit resets within 60 seconds.
MAX_RETRIES = 3
MAX_WAIT_SECONDS = 60


class GeminiProvider(LLMProvider):
    # A stable (non-preview) model that is fast and cheap enough to run once
    # per variable pair. Pass another name to use a different model.
    DEFAULT_MODEL = "gemini-3.5-flash"

    def __init__(self, model: str = DEFAULT_MODEL):
        self._client = genai.Client(api_key=require_gemini_api_key())
        self._model = model

    def generate(self, prompt: str) -> str:
        """Ask Gemini, retrying temporary failures.

        Raises a DecisionProcessError subclass if it still fails.
        """
        for attempt in range(MAX_RETRIES + 1):
            try:
                return self._generate_once(prompt)
            except DecisionProcessError as error:
                if not error.retryable or attempt == MAX_RETRIES:
                    raise
                wait = error.retry_after or 5 * 2**attempt  # 5s, 10s, 20s
                time.sleep(min(wait, MAX_WAIT_SECONDS))
        raise AssertionError("unreachable")

    def _generate_once(self, prompt: str) -> str:
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                # We don't give Gemini any tools, so turn off automatic function
                # calling (it also prints a warning on every call otherwise)
                config=types.GenerateContentConfig(
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                ),
            )
        except genai_errors.APIError as e:
            raise _translate_api_error(e, self._model) from e
        except httpx.TransportError as e:  # timeouts, no internet, DNS, ...
            raise LLMUnavailable(
                "Couldn't reach Gemini. Check your internet connection."
            ) from e
        # .text is None when the answer is blocked or empty
        return response.text or ""


def _translate_api_error(e: genai_errors.APIError, model: str) -> DecisionProcessError:
    """Turn a Gemini API error into one of our errors."""
    details = str(e.details)
    code = e.code or 0

    if code == 429:
        # The same 429 is used for the per-minute and per-day limits; the
        # quota ID in the details says which one was hit
        if "PerDay" in details:
            return LLMQuotaExhausted(
                "The Gemini daily quota is used up. It resets tomorrow; "
                "until then, use a different API key or a paid plan."
            )
        return LLMRateLimited(
            "Gemini is receiving too many requests. Wait a minute and try again.",
            retry_after=_retry_delay(details),
        )
    if code in (401, 403) or "API_KEY_INVALID" in details or "API key not valid" in details:
        return LLMAuthError("The Gemini API key is invalid or not allowed to use this model.")
    if code == 404:
        return LLMAuthError(f"The Gemini model '{model}' was not found.")
    if code >= 500:
        return LLMUnavailable("Gemini is temporarily unavailable. Try again in a few minutes.")
    return LLMRequestError(f"Gemini rejected the request: {e.message or e}")


def _retry_delay(details: str) -> float | None:
    # Gemini puts the wait it wants in the details, e.g. 'retryDelay': '41s'
    match = re.search(r"retryDelay'?\"?:\s*'?\"?(\d+(?:\.\d+)?)s", details)
    return float(match.group(1)) + 1 if match else None

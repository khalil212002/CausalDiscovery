"""LLMProvider backed by Google's Gemini API (google-genai library)."""

from google import genai
from google.genai import types

from decision_process.config import require_gemini_api_key
from decision_process.llm_provider import LLMProvider


class GeminiProvider(LLMProvider):
    # A stable (non-preview) model that is fast and cheap enough to run once
    # per variable pair. Pass another name to use a different model.
    DEFAULT_MODEL = "gemini-3.5-flash"

    def __init__(self, model: str = DEFAULT_MODEL):
        self._client = genai.Client(api_key=require_gemini_api_key())
        self._model = model

    def generate(self, prompt: str) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            # We don't give Gemini any tools, so turn off automatic function
            # calling (it also prints a warning on every call otherwise)
            config=types.GenerateContentConfig(
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
        # .text is None when the answer is blocked or empty
        return response.text or ""

"""The interface every LLM must follow to be used by the decision process.

The rest of the code only calls LLMProvider.generate(), so the LLM behind it
(Gemini, a local model, ...) can be swapped without changing anything else.
"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Send a prompt to the LLM and return its text answer."""

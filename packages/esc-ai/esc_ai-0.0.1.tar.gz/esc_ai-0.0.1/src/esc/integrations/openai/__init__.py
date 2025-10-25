"""OpenAI integration for esc."""

from .triggers import OpenAIToolCallTrigger
from .wrapper import wrap_openai

__all__ = ["wrap_openai", "OpenAIToolCallTrigger"]

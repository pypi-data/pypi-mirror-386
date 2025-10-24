"""Computer control tools for different agent APIs."""

from __future__ import annotations

from .anthropic import AnthropicComputerTool
from .hud import HudComputerTool
from .openai import OpenAIComputerTool
from .qwen import QwenComputerTool
from .settings import computer_settings

__all__ = [
    "AnthropicComputerTool",
    "HudComputerTool",
    "OpenAIComputerTool",
    "QwenComputerTool",
    "computer_settings",
]

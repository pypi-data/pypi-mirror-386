"""
Framework Translator - A tool for translating code across programming frameworks.

This package provides both CLI and SDK functionality for translating code
between different programming frameworks using OpenAI's language models.

For SDK usage, set your OpenAI API key as an environment variable:
    export OPENAI_API_KEY="your-api-key-here"
"""

from .sdk import (
    translate,
    get_supported_frameworks,
    get_supported_groups,
    get_supported_languages,
    get_framework_info,
)

__version__ = "1.0.1"

__all__ = [
    "translate",
    "get_supported_frameworks",
    "get_supported_groups",
    "get_supported_languages",
    "get_framework_info",
]

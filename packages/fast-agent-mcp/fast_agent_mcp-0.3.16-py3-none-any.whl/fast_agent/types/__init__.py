"""Shared type definitions and helpers for fast-agent.

Goals:
- Provide a stable import path for commonly used public types and helpers
- Keep dependencies minimal to reduce import-time cycles
"""

# Re-export common enums/types
# Public request parameters used to configure LLM calls
from fast_agent.llm.request_params import RequestParams

# Content helpers commonly used by users to build messages
from fast_agent.mcp.helpers.content_helpers import (
    ensure_multipart_messages,
    normalize_to_extended_list,
    text_content,
)

# Public message model used across providers and MCP integration
from fast_agent.mcp.prompt_message_extended import PromptMessageExtended

# Stop reason enum - imported directly to avoid circular dependency
from .llm_stop_reason import LlmStopReason

__all__ = [
    # Enums / types
    "LlmStopReason",
    "PromptMessageExtended",
    "RequestParams",
    # Content helpers
    "text_content",
    "ensure_multipart_messages",
    "normalize_to_extended_list",
]

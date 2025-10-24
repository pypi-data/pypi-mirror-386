"""Chat message models."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class Role(str, Enum):
    """Message role enum."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ToolCall(BaseModel):
    """Tool call information."""

    id: str
    name: str
    parameters: dict[str, Any]
    result: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    approved: bool = False
    error: Optional[str] = None


class ChatMessage(BaseModel):
    """Represents a single message in the conversation."""

    role: Role
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tokens: Optional[int] = None

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    def token_estimate(self) -> int:
        """Estimate token count (rough approximation)."""
        if self.tokens:
            return self.tokens
        # Rough estimate: ~4 chars per token
        return len(self.content) // 4 + sum(len(str(tc.parameters)) // 4 for tc in self.tool_calls)

"""
Data models for Durable Agent Framework

This module defines the request and response models used by the framework.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum
import uuid
import azure.durable_functions as df


class ChatRole(str, Enum):
    """Chat message role enum"""
    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"


@dataclass
class AgentSessionId:
    """
    Represents an agent session ID, which is used to identify a long-running agent session.

    Attributes:
        name: The name of the agent that owns the session (case-insensitive)
        key: The unique key of the agent session (case-sensitive)
    """
    name: str
    key: str

    @staticmethod
    def with_random_key(name: str) -> "AgentSessionId":
        """
        Creates a new AgentSessionId with the specified name and a randomly generated key.

        Args:
            name: The name of the agent that owns the session

        Returns:
            A new AgentSessionId with the specified name and a random GUID key
        """
        return AgentSessionId(name=name, key=uuid.uuid4().hex)

    def to_entity_id(self) -> df.EntityId:
        """
        Converts this AgentSessionId to a Durable Functions EntityId.

        Returns:
            EntityId for use with Durable Functions APIs
        """
        return df.EntityId(self.name, self.key)

    @staticmethod
    def from_entity_id(entity_id: df.EntityId) -> "AgentSessionId":
        """
        Creates an AgentSessionId from a Durable Functions EntityId.

        Args:
            entity_id: The EntityId to convert

        Returns:
            AgentSessionId instance
        """
        return AgentSessionId(name=entity_id.name, key=entity_id.key)

    def __str__(self) -> str:
        """Returns a string representation in the form @name@key"""
        return f"@{self.name}@{self.key}"

    def __repr__(self) -> str:
        """Returns a detailed string representation"""
        return f"AgentSessionId(name='{self.name}', key='{self.key}')"

    @staticmethod
    def parse(session_id_string: str) -> "AgentSessionId":
        """
        Parses a string representation of an agent session ID.

        Args:
            session_id_string: A string in the form @name@key

        Returns:
            AgentSessionId instance

        Raises:
            ValueError: If the string format is invalid
        """
        if not session_id_string.startswith("@"):
            raise ValueError(f"Invalid agent session ID format: {session_id_string}")

        parts = session_id_string[1:].split("@", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid agent session ID format: {session_id_string}")

        return AgentSessionId(name=parts[0], key=parts[1])


@dataclass
class RunRequest:
    """
    Represents a request to run an agent with a specific message and configuration.

    Attributes:
        message: The message to send to the agent
        role: The role of the message sender (user, system, or assistant)
        response_schema: Optional JSON schema for structured response format
        enable_tool_calls: Whether to enable tool calls for this request
        conversation_id: Optional conversation/session ID for tracking
        correlation_id: Optional correlation ID for tracking the response to this specific request
    """
    message: str
    role: Optional[ChatRole] = ChatRole.USER
    response_schema: Optional[Dict[str, Any]] = None
    enable_tool_calls: bool = True
    conversation_id: Optional[str] = None
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "message": self.message,
            "enable_tool_calls": self.enable_tool_calls,
        }
        if self.role:
            result["role"] = self.role.value if isinstance(self.role, ChatRole) else self.role
        if self.response_schema:
            result["response_schema"] = self.response_schema
        if self.conversation_id:
            result["conversation_id"] = self.conversation_id
        if self.correlation_id:
            result["correlation_id"] = self.correlation_id
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RunRequest":
        """Create RunRequest from dictionary"""
        role_str = data.get("role")
        if role_str:
            try:
                role = ChatRole(role_str.lower())
            except ValueError:
                role = ChatRole.USER  # Default to USER if invalid
        else:
            role = ChatRole.USER

        return cls(
            message=data.get("message", ""),
            role=role,
            response_schema=data.get("response_schema"),
            enable_tool_calls=data.get("enable_tool_calls", True),
            conversation_id=data.get("conversation_id"),
            correlation_id=data.get("correlation_id"),
        )


@dataclass
class AgentResponse:
    """
    Response from agent execution.

    Attributes:
        response: The agent's text response (or None for structured responses)
        message: The original message sent to the agent
        conversation_id: The conversation/session ID
        status: Status of the execution (success, error, etc.)
        message_count: Number of messages in the conversation
        error: Error message if status is error
        error_type: Type of error if status is error
        structured_response: Structured response if response_schema was provided
    """
    response: Optional[str]
    message: str
    conversation_id: Optional[str]
    status: str
    message_count: int = 0
    error: Optional[str] = None
    error_type: Optional[str] = None
    structured_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "message": self.message,
            "conversation_id": self.conversation_id,
            "status": self.status,
            "message_count": self.message_count,
        }

        # Add response or structured_response based on what's available
        if self.structured_response is not None:
            result["structured_response"] = self.structured_response
        elif self.response is not None:
            result["response"] = self.response

        if self.error:
            result["error"] = self.error
        if self.error_type:
            result["error_type"] = self.error_type

        return result

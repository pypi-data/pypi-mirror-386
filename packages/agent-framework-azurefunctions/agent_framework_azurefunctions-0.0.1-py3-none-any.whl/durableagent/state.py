"""
Agent State Management

This module defines the AgentState class for managing conversation state and
serializing agent framework responses.
"""

import logging
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from agent_framework import ChatMessage, AgentRunResponse

logger = logging.getLogger(__name__)


class AgentState:
    """
    Manages agent conversation state using agent_framework types (ChatMessage, AgentRunResponse).

    This class handles:
    - Conversation history tracking using ChatMessage objects
    - Agent response storage using AgentRunResponse objects with correlation IDs
    - State persistence and restoration
    - Message counting
    """

    def __init__(self):
        """Initialize empty agent state."""
        self.conversation_history: List[ChatMessage] = []
        self.last_response: Optional[str] = None
        self.message_count: int = 0

    def _current_timestamp(self) -> str:
        """Return an ISO 8601 UTC timestamp."""
        return datetime.now(timezone.utc).isoformat()

    def add_user_message(self, content: str, correlation_id: str, role: str = "user") -> None:
        """
        Add a user message to the conversation history as a ChatMessage object.

        Args:
            content: The message content
            correlation_id: Correlation identifier associated with the user message
            role: The message role (user, system, etc.)
        """
        self.message_count += 1
        timestamp = self._current_timestamp()
        chat_message = ChatMessage(
            role=role,
            text=content,
            additional_properties={"timestamp": timestamp, "correlation_id": correlation_id}
        )
        self.conversation_history.append(chat_message)
        logger.debug(f"Added {role} ChatMessage to history (message #{self.message_count})")

    def add_assistant_message(self, content: str, agent_response: AgentRunResponse, correlation_id: Optional[str] = None) -> None:
        """
        Add an assistant message to the conversation history with full agent response.

        Args:
            content: The text content of the response
            agent_response: The AgentRunResponse object from the agent framework
            correlation_id: Optional correlation ID for tracking this response
        """
        self.last_response = content
        timestamp = self._current_timestamp()
        serialized_response = self.serialize_response(agent_response)

        # Create a ChatMessage for the assistant response
        # The agent_response already contains messages, but we store it as a custom ChatMessage
        # with the agent_response stored in additional_properties for full metadata preservation
        additional_props: Dict[str, Any] = {
            "agent_response": serialized_response,
            "correlation_id": correlation_id,
            "timestamp": timestamp,
            "message_count": self.message_count
        }
        chat_message = ChatMessage(
            role="assistant",
            text=content,
            additional_properties=additional_props
        )

        self.conversation_history.append(chat_message)
        
        logger.debug(f"Added assistant ChatMessage to history with AgentRunResponse metadata (correlation_id: {correlation_id})")

    def try_get_agent_response(self, correlation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an agent response by correlation ID.

        Args:
            correlation_id: The correlation ID to look up

        Returns:
            The agent response data if found, None otherwise
        """
        for message in reversed(self.conversation_history):
            metadata = getattr(message, "additional_properties", {}) or {}
            if metadata.get("correlation_id") == correlation_id:
                return self._build_agent_response_payload(message, metadata)

        return None

    def serialize_response(self, response: Any) -> Dict[str, Any]:
        """
        Serialize any agent framework object to a dictionary.

        This is a utility method for custom serialization. The primary serialization
        path now uses ChatMessage.to_dict() and AgentRunResponse.to_dict().

        Args:
            response: The response object from the agent framework

        Returns:
            Dictionary containing all response fields
        """
        try:
            # Agent framework objects have to_dict method
            if hasattr(response, 'to_dict'):
                return response.to_dict()

            # If response has a model_dump method (Pydantic v2), use it
            if hasattr(response, 'model_dump'):
                return response.model_dump()

            # If response has __dict__, serialize it manually
            if hasattr(response, '__dict__'):
                return self._serialize_object_dict(response)

            # Fallback: convert to string
            return {"response": str(response)}

        except Exception as e:
            logger.warning(f"Error serializing response: {e}")
            return {"response": str(response), "serialization_error": str(e)}

    def _serialize_object_dict(self, obj: Any) -> Dict[str, Any]:
        """
        Serialize an object's __dict__ to a JSON-compatible dictionary.

        Args:
            obj: Object to serialize

        Returns:
            Dictionary with serialized fields
        """
        result = {}
        for key, value in obj.__dict__.items():
            # Skip private attributes
            if key.startswith('_'):
                continue

            # Recursively serialize nested objects
            if hasattr(value, '__dict__') or hasattr(value, 'dict') or hasattr(value, 'model_dump'):
                result[key] = self.serialize_response(value)
            elif isinstance(value, list):
                result[key] = [
                    self.serialize_response(item) if hasattr(item, '__dict__') else item
                    for item in value
                ]
            elif isinstance(value, dict):
                result[key] = value
            else:
                # Convert to string for non-serializable types
                try:
                    json.dumps(value)
                    result[key] = value
                except (TypeError, ValueError):
                    result[key] = str(value)

        return result

    def to_dict(self) -> Dict[str, Any]:
        """
        Get the current state as a dictionary for persistence.

        Returns:
            Dictionary containing conversation_history (as serialized ChatMessages),
            last_response, and message_count
        """
        return {
            "conversation_history": [msg.to_dict() for msg in self.conversation_history],
            "last_response": self.last_response,
            "message_count": self.message_count
        }

    def restore_state(self, state: Dict[str, Any]) -> None:
        """
        Restore state from a dictionary, reconstructing ChatMessage objects.

        Args:
            state: Dictionary containing conversation_history, last_response, and message_count
        """
        # Restore conversation history as ChatMessage objects
        history_data = state.get("conversation_history", [])
        self.conversation_history = [
            ChatMessage.from_dict(msg) if isinstance(msg, dict) else msg
            for msg in history_data
        ]

        self.last_response = state.get("last_response")
        self.message_count = state.get("message_count", 0)
        logger.debug(
            "Restored state: %s ChatMessages in history",
            len(self.conversation_history)
        )

    def reset(self) -> None:
        """Reset the state to empty."""
        self.conversation_history = []
        self.last_response = None
        self.message_count = 0
        logger.debug("State reset to empty")

    def __repr__(self) -> str:
        """String representation of the state."""
        return f"AgentState(messages={self.message_count}, history_length={len(self.conversation_history)})"

    def _build_agent_response_payload(
        self,
        message: ChatMessage,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Construct the agent response payload returned to callers."""

        return {
            "content": message.text,
            "agent_response": metadata.get("agent_response"),
            "message_count": metadata.get("message_count", self.message_count),
            "timestamp": metadata.get("timestamp"),
            "correlation_id": metadata.get("correlation_id")
        }

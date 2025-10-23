"""
Orchestration Support for Durable Agents

This module provides support for using agents inside Durable Function orchestrations.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, Union, Type, TypeVar, AsyncIterator
from agent_framework import AgentProtocol, AgentRunResponse, AgentRunResponseUpdate, AgentThread, ChatMessage
from azure.durable_functions import DurableOrchestrationContext, EntityId
from .models import RunRequest, AgentSessionId

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DurableAIAgent(AgentProtocol):
    """
    A durable agent implementation that uses entity methods to interact with agent entities.

    This class implements AgentProtocol and provides methods to work with Azure Durable Functions
    orchestrations, which use generators and yield instead of async/await.

    Key methods:
    - get_new_thread(): Create a new conversation thread
    - run(): Execute the agent and return a Task for yielding in orchestrations

    Note: The run() method is NOT async. It returns a Task directly that must be
    yielded in orchestrations to wait for the entity call to complete.

    Example usage in orchestration:
        writer = context.get_agent("WriterAgent")
        thread = writer.get_new_thread()  # NOT yielded - returns immediately

        response = yield writer.run(  # Yielded - waits for entity call
            message="Write a haiku about coding",
            thread=thread
        )
    """

    def __init__(self, context: DurableOrchestrationContext, agent_name: str):
        """
        Initialize the DurableAIAgent.

        Args:
            context: The orchestration context
            agent_name: Name of the agent (used to construct entity ID)
        """
        self.context = context
        self.agent_name = agent_name
        self._id = str(uuid.uuid4())
        self._name = agent_name
        self._display_name = agent_name
        self._description = f"Durable agent proxy for {agent_name}"
        logger.debug(f"[DurableAIAgent] Initialized for agent: {agent_name}")

    @property
    def id(self) -> str:
        """Get the unique identifier for this agent."""
        return self._id

    @property
    def name(self) -> Optional[str]:
        """Get the name of the agent."""
        return self._name

    @property
    def display_name(self) -> str:
        """Get the display name of the agent."""
        return self._display_name

    @property
    def description(self) -> Optional[str]:
        """Get the description of the agent."""
        return self._description

    def run(
        self,
        messages: Union[str, ChatMessage, List[ChatMessage], None] = None,
        *,
        thread: Optional[AgentThread] = None,
        **kwargs
    ) -> AgentRunResponse:
        """
        Execute the agent with messages and return a Task for orchestrations.

        This method implements AgentProtocol and returns a Task that can be yielded
        in Durable Functions orchestrations.

        Args:
            messages: The message(s) to send to the agent
            thread: Optional agent thread for conversation context
            **kwargs: Additional arguments (enable_tool_calls, response_schema, etc.)

        Returns:
            Task that will resolve to the agent response

        Example:
            @app.orchestration_trigger(context_name="context")
            def my_orchestration(context):
                agent = context.get_agent("MyAgent")
                thread = agent.get_new_thread()
                result = yield agent.run("Hello", thread=thread)
        """
        # Convert messages to string format
        if messages is None:
            message_str = ""
        elif isinstance(messages, str):
            message_str = messages
        elif isinstance(messages, ChatMessage):
            message_str = messages.text or ""
        elif isinstance(messages, list):
            message_str = self._messages_to_string(messages)
        else:
            message_str = str(messages)

        # Extract optional parameters from kwargs
        enable_tool_calls = kwargs.get('enable_tool_calls', True)
        response_schema = kwargs.get('response_schema', None)

        # Get the session ID for the entity
        if thread and hasattr(thread, '_durable_session_id'):
            session_id = thread._durable_session_id
        else:
            # Create a unique session ID for each call when no thread is provided
            # This ensures each call gets its own conversation context
            session_key = str(self.context.new_uuid())
            session_id = AgentSessionId(name=self.agent_name, key=session_key)
            logger.warning(f"[DurableAIAgent] No thread provided, created unique session_id: {session_id}")

        # Create entity ID from session ID
        entity_id = session_id.to_entity_id()

        # Generate a deterministic correlation ID for this call
        # This is required by the entity and must be unique per call
        correlation_id = str(self.context.new_uuid())

        # Prepare the request using RunRequest model
        run_request = RunRequest(
            message=message_str,
            enable_tool_calls=enable_tool_calls,
            correlation_id=correlation_id,
            conversation_id=session_id.key,
            response_schema=response_schema
        )

        logger.info(f"[DurableAIAgent] Calling entity {entity_id} with message: {message_str[:100]}...")

        # Call the entity and return the Task directly
        # The orchestration will yield this Task
        return self.context.call_entity(entity_id, "run_agent", run_request.to_dict())

    def run_stream(
        self,
        messages: Union[str, ChatMessage, List[ChatMessage], None] = None,
        *,
        thread: Optional[AgentThread] = None,
        **kwargs
    ) -> AsyncIterator[AgentRunResponseUpdate]:
        """
        Run the agent with streaming (not supported for durable agents).

        Raises:
            NotImplementedError: Streaming is not supported for durable agents.
        """
        raise NotImplementedError(
            "Streaming is not supported for durable agents in orchestrations."
        )

    def get_new_thread(self) -> AgentThread:
        """
        Create a new agent thread for this orchestration instance.

        Each call creates a unique thread with its own conversation context.
        The session ID is deterministic (uses context.new_uuid()) to ensure
        orchestration replay works correctly.

        Returns:
            A new AgentThread instance with a unique session ID
        """
        # Generate a deterministic unique key for this thread
        # Using context.new_uuid() ensures the same GUID is generated during replay
        session_key = str(self.context.new_uuid())

        # Create AgentSessionId with agent name and session key
        session_id = AgentSessionId(name=self.agent_name, key=session_key)

        thread = AgentThread()

        # Store session_id as a custom attribute for entity calls
        thread._durable_session_id = session_id

        logger.debug(f"[DurableAIAgent] Created new thread with session_id: {session_id}")
        return thread

    def _messages_to_string(self, messages: List[ChatMessage]) -> str:
        """
        Convert a list of ChatMessage objects to a single string.

        Args:
            messages: List of ChatMessage objects

        Returns:
            Concatenated string of message contents
        """
        return "\n".join([msg.text or "" for msg in messages])


def get_agent(context: DurableOrchestrationContext, agent_name: str) -> DurableAIAgent:
    """
    Extension method to get a DurableAIAgent from an orchestration context.

    This provides a convenient way to create agent wrappers in orchestrations.

    Usage:
        from durableagent.orchestration import get_agent

        @app.orchestration_trigger(context_name="context")
        def my_orchestration(context: DurableOrchestrationContext):
            writer = get_agent(context, "WriterAgent")
            thread = writer.get_new_thread()  # NOT yielded
            response = yield writer.run_async("Write a haiku", thread=thread)  # Yielded

    Args:
        context: The orchestration context
        agent_name: Name of the agent entity

    Returns:
        DurableAIAgent wrapper for the specified agent
    """
    return DurableAIAgent(context, agent_name)


# Also add as a method to DurableOrchestrationContext for convenience
# This allows: context.get_agent("WriterAgent")
def _get_agent_method(self, agent_name: str) -> DurableAIAgent:
    """
    Get a DurableAIAgent wrapper for use in orchestrations.

    This is an extension method added to DurableOrchestrationContext that provides
    a convenient way to create agent wrappers.

    Args:
        agent_name: Name of the agent entity

    Returns:
        DurableAIAgent wrapper for the specified agent

    Example:
        @app.orchestration_trigger(context_name="context")
        def my_orchestration(context: DurableOrchestrationContext):
            writer = context.get_agent("WriterAgent")
            thread = writer.get_new_thread()
            response = yield writer.run_async("Write a haiku", thread=thread)
    """
    return get_agent(self, agent_name)


def _add_get_agent_extension():
    """
    Add get_agent method to DurableOrchestrationContext.

    This is called when the module is imported to add the extension method.
    """
    if not hasattr(DurableOrchestrationContext, 'get_agent'):
        DurableOrchestrationContext.get_agent = _get_agent_method
        logger.debug("[orchestration] Added get_agent() extension method to DurableOrchestrationContext")


# Execute the extension when module is imported
_add_get_agent_extension()

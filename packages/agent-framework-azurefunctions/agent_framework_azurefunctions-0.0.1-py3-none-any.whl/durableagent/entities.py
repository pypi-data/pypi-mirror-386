"""
Durable Entity for Agent Execution

This module defines a durable entity that manages agent state and execution.
Using entities instead of orchestrations provides better state management and
allows for long-running agent conversations.
"""

import asyncio
import inspect
import json
import logging
from collections.abc import AsyncIterable
from typing import Any, Dict, List, Optional, Union

from agent_framework import AgentProtocol, AgentRunResponse, AgentRunResponseUpdate
import azure.durable_functions as df

from .callbacks import AgentCallbackContext, AgentResponseCallbackProtocol
from .models import RunRequest, AgentResponse, ChatRole
from .state import AgentState

logger = logging.getLogger(__name__)


class AgentEntity:
    """
    Durable entity that manages agent execution and conversation state.

    This entity:
    - Maintains conversation history
    - Executes agent with messages
    - Stores agent responses
    - Handles tool execution

    Operations:
    - run_agent: Execute the agent with a message
    - get_state: Retrieve current conversation state
    - reset: Clear conversation history

    Attributes:
        agent: The AgentProtocol instance
        state: The AgentState managing conversation history
    """

    agent: AgentProtocol
    state: AgentState

    def __init__(
        self,
        agent: AgentProtocol,
        callback: Optional[AgentResponseCallbackProtocol] = None,
    ):
        """
        Initialize the agent entity.

        Args:
            agent: The Microsoft Agent Framework agent instance (must implement AgentProtocol)
            callback: Optional callback invoked during streaming updates and final responses
        """
        self.agent = agent
        self.state = AgentState()
        self.callback = callback

        logger.info(f"[AgentEntity] Initialized with agent type: {type(agent).__name__}")

    async def run_agent(self, context, request: Union[RunRequest, Dict[str, Any], str]) -> Dict[str, Any]:
        """
        Execute the agent with a message directly in the entity.

        Args:
            context: Entity context
            request: RunRequest object, dict, or string message (for backward compatibility)

        Returns:
            Dict with status information and response (serialized AgentResponse)

        Note:
            The agent returns an AgentRunResponse object which is stored in state.
            This method extracts the text/structured response and returns an AgentResponse dict.
        """
        # Handle backward compatibility - convert string or dict to RunRequest
        if isinstance(request, str):
            run_request = RunRequest(message=request, role=ChatRole.USER)
        elif isinstance(request, dict):
            run_request = RunRequest.from_dict(request)
        else:
            run_request = request

        message = run_request.message
        conversation_id = run_request.conversation_id
        correlation_id = run_request.correlation_id
        if not conversation_id:
            raise ValueError("RunRequest must include a conversation_id")
        if not correlation_id:
            raise ValueError("RunRequest must include a correlation_id")
        role = run_request.role or ChatRole.USER
        response_schema = run_request.response_schema
        enable_tool_calls = run_request.enable_tool_calls

        logger.info("=" * 70)
        logger.info(f"[AgentEntity.run_agent] Received message: {message}")
        logger.info(f"[AgentEntity.run_agent] Conversation ID: {conversation_id}")
        logger.info(f"[AgentEntity.run_agent] Correlation ID: {correlation_id}")
        logger.info(f"[AgentEntity.run_agent] Role: {role.value if isinstance(role, ChatRole) else role}")
        logger.info(f"[AgentEntity.run_agent] Enable tool calls: {enable_tool_calls}")
        logger.info(f"[AgentEntity.run_agent] Response schema: {'provided' if response_schema else 'none'}")

        # Store message in history with role
        role_str = role.value if isinstance(role, ChatRole) else role
        self.state.add_user_message(message, role=role_str, correlation_id=correlation_id)

        logger.info("[AgentEntity.run_agent] Executing agent...")

        try:
            logger.info("[AgentEntity.run_agent] Starting agent invocation")

            run_kwargs: Dict[str, Any] = {"messages": message}
            if not enable_tool_calls:
                run_kwargs["tools"] = None
            if response_schema:
                run_kwargs["response_format"] = response_schema

            agent_run_response = await self._invoke_agent(
                run_kwargs=run_kwargs,
                correlation_id=correlation_id,
                conversation_id=conversation_id,
                request_message=message,
            )

            logger.info(
                "[AgentEntity.run_agent] Agent invocation completed - response type: %s",
                type(agent_run_response).__name__,
            )

            response_text = None
            structured_response = None

            try:
                if response_schema:
                    try:
                        if hasattr(agent_run_response, "text"):
                            response_str = str(agent_run_response.text)
                        else:
                            response_str = str(agent_run_response)
                        structured_response = json.loads(response_str)
                        logger.info("Parsed structured JSON response")
                    except json.JSONDecodeError as decode_error:
                        logger.warning(f"Failed to parse JSON response: {decode_error}")
                        response_text = response_str
                else:
                    if hasattr(agent_run_response, "text"):
                        response_text = agent_run_response.text
                        preview = str(response_text)
                        logger.info(
                            f"Response: {preview[:100]}..." if len(preview) > 100 else f"Response: {preview}"
                        )
                        response_text = preview if response_text is not None else "No response"
                    else:
                        response_text = "Response received (no text attribute)"
                        logger.warning("Response has no text attribute")
            except Exception as extraction_error:
                logger.error(
                    f"Error extracting response: {extraction_error}",
                    exc_info=True,
                )
                response_text = "Error extracting response"

            agent_response = AgentResponse(
                response=response_text,
                message=str(message),
                conversation_id=str(conversation_id),
                status="success",
                message_count=self.state.message_count,
                structured_response=structured_response,
            )
            result = agent_response.to_dict()

            content = json.dumps(structured_response) if structured_response else response_text
            self.state.add_assistant_message(content, agent_run_response, correlation_id)
            logger.info("[AgentEntity.run_agent] AgentRunResponse stored in conversation history")

            logger.info("=" * 70)
            return result

        except Exception as exc:
            import traceback

            error_traceback = traceback.format_exc()
            logger.error("=" * 70)
            logger.error("[AgentEntity.run_agent] Agent execution failed")
            logger.error(f"Error: {str(exc)}")
            logger.error(f"Error type: {type(exc).__name__}")
            logger.error(f"Full traceback:\n{error_traceback}")
            logger.error("=" * 70)

            error_response = AgentResponse(
                response=f"Error: {str(exc)}",
                message=str(message),
                conversation_id=str(conversation_id),
                status="error",
                message_count=self.state.message_count,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            result = error_response.to_dict()

            logger.info("=" * 70)
            return result

    async def _invoke_agent(
        self,
        run_kwargs: Dict[str, Any],
        correlation_id: str,
        conversation_id: str,
        request_message: str,
    ) -> AgentRunResponse:
        """Execute the agent, preferring streaming when available."""

        callback_context: Optional[AgentCallbackContext] = None
        if self.callback is not None:
            callback_context = self._build_callback_context(
                correlation_id=correlation_id,
                conversation_id=conversation_id,
                request_message=request_message,
            )

        run_stream_callable = getattr(self.agent, "run_stream", None)
        if callable(run_stream_callable):
            try:
                stream_candidate = run_stream_callable(**run_kwargs)
                if inspect.isawaitable(stream_candidate):
                    stream_candidate = await stream_candidate

                return await self._consume_stream(
                    stream=stream_candidate,
                    callback_context=callback_context,
                )
            except TypeError as type_error:
                if "__aiter__" not in str(type_error):
                    raise
                logger.debug(
                    "run_stream returned a non-async result; falling back to run(): %s",
                    type_error,
                )
            except Exception as stream_error:
                logger.warning(
                    "run_stream failed; falling back to run(): %s",
                    stream_error,
                    exc_info=True,
                )
        else:
            logger.debug("Agent does not expose run_stream; falling back to run().")

        agent_run_response = await self._invoke_non_stream(run_kwargs)
        await self._notify_final_response(agent_run_response, callback_context)
        return agent_run_response

    async def _consume_stream(
        self,
        stream: AsyncIterable[AgentRunResponseUpdate],
        callback_context: Optional[AgentCallbackContext] = None,
    ) -> AgentRunResponse:
        """Consume streaming responses and build the final AgentRunResponse."""

        updates: List[AgentRunResponseUpdate] = []

        async for update in stream:
            updates.append(update)
            await self._notify_stream_update(update, callback_context)

        if updates:
            response = AgentRunResponse.from_agent_run_response_updates(updates)
        else:
            logger.debug("[AgentEntity] No streaming updates received; creating empty response")
            response = AgentRunResponse(messages=[])

        await self._notify_final_response(response, callback_context)
        return response

    async def _invoke_non_stream(self, run_kwargs: Dict[str, Any]) -> AgentRunResponse:
        """Invoke the agent without streaming support."""

        run_callable = getattr(self.agent, "run", None)
        if run_callable is None or not callable(run_callable):
            raise AttributeError("Agent does not implement run() method")

        result = run_callable(**run_kwargs)
        if inspect.isawaitable(result):
            result = await result

        return result

    async def _notify_stream_update(
        self,
        update: AgentRunResponseUpdate,
        context: Optional[AgentCallbackContext],
    ) -> None:
        """Invoke the streaming callback if one is registered."""

        if self.callback is None or context is None:
            return

        try:
            callback_result = self.callback.on_streaming_response_update(update, context)
            if inspect.isawaitable(callback_result):
                await callback_result
        except Exception as exc:
            logger.warning(
                "[AgentEntity] Streaming callback raised an exception: %s",
                exc,
                exc_info=True,
            )

    async def _notify_final_response(
        self,
        response: AgentRunResponse,
        context: Optional[AgentCallbackContext],
    ) -> None:
        """Invoke the final response callback if one is registered."""

        if self.callback is None or context is None:
            return

        try:
            callback_result = self.callback.on_agent_response(response, context)
            if inspect.isawaitable(callback_result):
                await callback_result
        except Exception as exc:
            logger.warning(
                "[AgentEntity] Response callback raised an exception: %s",
                exc,
                exc_info=True,
            )

    def _build_callback_context(
        self,
        correlation_id: str,
        conversation_id: str,
        request_message: str,
    ) -> AgentCallbackContext:
        """Create the callback context provided to consumers."""

        agent_name = getattr(self.agent, "name", None) or type(self.agent).__name__
        return AgentCallbackContext(
            agent_name=agent_name,
            correlation_id=correlation_id,
            conversation_id=conversation_id,
            request_message=request_message,
        )

    def get_state(self, context) -> Dict[str, Any]:
        """
        Get the current state of the entity.

        Returns:
            Dict with conversation history and statistics
        """
        logger.info("[AgentEntity.get_state] Retrieving entity state")

        state_dict = self.state.to_dict()
        state_dict["agent_type"] = type(self.agent).__name__
        return state_dict

    def reset(self, context) -> None:
        """
        Reset the entity state (clear conversation history).
        """
        logger.info("[AgentEntity.reset] Resetting entity state")
        self.state.reset()
        logger.info("[AgentEntity.reset] State reset complete")


def create_agent_entity(
    agent: AgentProtocol,
    callback: Optional[AgentResponseCallbackProtocol] = None,
):
    """
    Factory function to create an agent entity class.

    Args:
        agent: The Microsoft Agent Framework agent instance (must implement AgentProtocol)
        callback: Optional callback invoked during streaming and final responses

    Returns:
        Entity function configured with the agent
    """

    async def _entity_coroutine(context: df.DurableEntityContext) -> None:
        """Async handler that executes the entity operations."""
        try:
            logger.info("=" * 70)
            logger.info("[entity_function] Entity triggered")
            logger.info(f"[entity_function] Operation: {context.operation_name}")
            logger.info("=" * 70)

            current_state = context.get_state(lambda: None)
            logger.info("Retrieved state: %s", current_state)
            entity = AgentEntity(agent, callback)

            if current_state is not None:
                entity.state.restore_state(current_state)
                logger.info(
                    "[entity_function] Restored entity from state (message_count: %s)",
                    entity.state.message_count
                )
            else:
                logger.info("[entity_function] Created new entity instance")

            operation = context.operation_name

            if operation == "run_agent":
                input_data = context.get_input()

                # Support both old format (message + conversation_id) and new format (RunRequest dict)
                # This provides backward compatibility
                if isinstance(input_data, dict) and "message" in input_data:
                    # Input can be either old format or new RunRequest format
                    request = input_data
                else:
                    # Fall back to treating input as message string
                    request = str(input_data)

                result = await entity.run_agent(context, request)
                context.set_result(result)

            elif operation == "get_state":
                context.set_result(entity.get_state(context))

            elif operation == "reset":
                entity.reset(context)
                context.set_result({"status": "reset"})

            else:
                logger.error("[entity_function] Unknown operation: %s", operation)
                context.set_result({"error": f"Unknown operation: {operation}"})

            context.set_state(entity.state.to_dict())
            logger.info(f"[entity_function] Operation {operation} completed successfully")

        except Exception as exc:
            import traceback

            logger.error("=" * 70)
            logger.error("[entity_function] Error in entity: %s", str(exc))
            logger.error(f"[entity_function] Traceback:\n{traceback.format_exc()}")
            logger.error("=" * 70)
            context.set_result({"error": str(exc), "status": "error"})

    def entity_function(context: df.DurableEntityContext) -> None:
        """Synchronous wrapper invoked by the Durable Functions runtime."""
        try:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if loop.is_running():
                temp_loop = asyncio.new_event_loop()
                try:
                    temp_loop.run_until_complete(_entity_coroutine(context))
                finally:
                    temp_loop.close()
            else:
                loop.run_until_complete(_entity_coroutine(context))

        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("[entity_function] Unexpected error executing entity: %s", exc, exc_info=True)
            context.set_result({"error": str(exc), "status": "error"})

    return entity_function

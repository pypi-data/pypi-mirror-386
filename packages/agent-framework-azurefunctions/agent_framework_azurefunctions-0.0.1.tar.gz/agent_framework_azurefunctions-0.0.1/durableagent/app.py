"""
AgentFunctionApp - Main application class

This module provides the AgentFunctionApp class that integrates Microsoft Agent Framework
with Azure Durable Entities, enabling stateful and durable AI agent execution.
"""

import json
import logging
import re
from collections.abc import Mapping
from typing import Any, Dict, List, Optional, Tuple

from agent_framework import AgentProtocol

import azure.durable_functions as df
import azure.functions as func

from .callbacks import AgentResponseCallbackProtocol
from .entities import create_agent_entity
from .errors import IncomingRequestError
from .models import AgentSessionId, RunRequest
from .state import AgentState

logger = logging.getLogger(__name__)

SESSION_ID_FIELD: str = "sessionId"
SESSION_KEY_FIELD: str = "sessionKey"
SESSION_IDENTIFIER_KEYS: Tuple[str, str] = (
    SESSION_ID_FIELD,
    SESSION_KEY_FIELD,
)


class AgentFunctionApp(df.DFApp):
    """
    Main application class for creating durable agent function apps using Durable Entities.

    This class uses Durable Entities pattern for agent execution, providing:
    - Stateful agent conversations
    - Conversation history management
    - Signal-based operation invocation
    - Better state management than orchestrations

    Usage:
        ```python
        from durableagent import AgentFunctionApp
        from agent_framework.azure import AzureOpenAIAssistantsClient

        # Create agents with unique names
        weather_agent = AzureOpenAIAssistantsClient(...).create_agent(
            name="WeatherAgent",
            instructions="You are a helpful weather agent.",
            tools=[get_weather],
        )
        
        math_agent = AzureOpenAIAssistantsClient(...).create_agent(
            name="MathAgent",
            instructions="You are a helpful math assistant.",
            tools=[calculate],
        )

        # Option 1: Pass list of agents during initialization
        app = AgentFunctionApp(agents=[weather_agent, math_agent])

        # Option 2: Add agents after initialization
        app = AgentFunctionApp()
        app.add_agent(weather_agent)
        app.add_agent(math_agent)
        ```

    This creates:
    - HTTP trigger endpoint for each agent's requests
    - Durable entity for each agent's state management and execution
    - Full access to all Azure Functions capabilities

    Attributes:
        agents: Dictionary of agent name to AgentProtocol instance
        enable_health_check: Whether health check endpoint is enabled
    """

    agents: Dict[str, AgentProtocol]
    enable_health_check: bool

    def __init__(
        self,
        agents: Optional[List[AgentProtocol]] = None,
        http_auth_level: func.AuthLevel = func.AuthLevel.ANONYMOUS,
        enable_health_check: bool = True,
        default_callback: Optional[AgentResponseCallbackProtocol] = None,
    ):
        """
        Initialize the AgentFunctionApp.

        Args:
            agents: List of agent instances to register
            http_auth_level: HTTP authentication level (default: ANONYMOUS)
            enable_health_check: Enable built-in health check endpoint (default: True)
            default_callback: Optional callback invoked for agents without specific callbacks

        Note:
            If no agents are provided, they can be added later using add_agent().
        """
        logger.info("=" * 70)
        logger.info("[AgentFunctionApp] Initializing with Durable Entities...")

    # Initialize parent DFApp
        super().__init__(http_auth_level=http_auth_level)

        # Initialize agents dictionary
        self.agents = {}
        self.enable_health_check = enable_health_check
        self.default_callback = default_callback

        if agents:
            # Register all provided agents
            logger.info(f"[AgentFunctionApp] Registering {len(agents)} agent(s)")
            for agent_instance in agents:
                self.add_agent(agent_instance)

        # Setup health check if enabled
        if self.enable_health_check:
            self._setup_health_route()

        logger.info(f"[AgentFunctionApp] Initialization complete")
        logger.info("=" * 70)


    def add_agent(
        self,
        agent: AgentProtocol,
        callback: Optional[AgentResponseCallbackProtocol] = None,
    ) -> None:
        """
        Add an agent to the function app after initialization.

        Args:
            agent: The Microsoft Agent Framework agent instance (must implement AgentProtocol)
                   The agent must have a 'name' attribute.
            callback: Optional callback invoked during agent execution

        Raises:
            ValueError: If the agent doesn't have a 'name' attribute or if an agent 
                       with the same name is already registered
        """
        # Get agent name from the agent's name attribute
        name = getattr(agent, 'name', None)
        if name is None:
            raise ValueError("Agent does not have a 'name' attribute. All agents must have a 'name' attribute.")

        if name in self.agents:
            raise ValueError(f"Agent with name '{name}' is already registered. Each agent must have a unique name.")

        logger.info("=" * 70)
        logger.info(f"[AgentFunctionApp] Adding agent: {name}")
        logger.info(f"[AgentFunctionApp] Route: /api/agents/{name}")

        self.agents[name] = agent

        effective_callback = callback or self.default_callback

        self._setup_agent_functions(agent, name, effective_callback)

        logger.info(f"[AgentFunctionApp] Agent '{name}' added successfully")
        logger.info("=" * 70)

    def _setup_agent_functions(
        self,
        agent: AgentProtocol,
        agent_name: str,
        callback: Optional[AgentResponseCallbackProtocol],
    ):
        """
        Set up the HTTP trigger and entity for a specific agent.

        Args:
            agent: The agent instance
            agent_name: The name to use for routing and entity registration
            callback: Optional callback to receive response updates
        """
        logger.info(f"[AgentFunctionApp] Setting up functions for agent '{agent_name}'...")

        self._setup_http_run_route(agent_name)
        self._setup_agent_entity(agent, agent_name, callback)
        self._setup_get_state_route(agent_name)

    def _setup_http_run_route(self, agent_name: str) -> None:
        """
        Register the POST route that triggers agent execution.

        Args:
            agent_name: The agent name (used for both routing and entity identification)
        """

        run_function_name = self._build_function_name(agent_name, "run")

        @self.function_name(run_function_name)
        @self.route(route=f"agents/{agent_name}/run", methods=["POST"])
        @self.durable_client_input(client_name="client")
        async def http_start(req: func.HttpRequest, client: df.DurableOrchestrationClient) -> func.HttpResponse:
            """
            HTTP trigger that calls a durable entity to execute the agent and returns the result.

            Expected request body (RunRequest format):
            {
                "message": "user message to agent",
                "sessionId": "optional session id (or sessionKey)",
                "role": "user|system" (optional, default: "user"),
                "response_schema": {...} (optional JSON schema for structured responses),
                "enable_tool_calls": true|false (optional, default: true)
            }
            """
            logger.info("=" * 70)
            logger.info(f"[HTTP Trigger] Received request on route: /api/agents/{agent_name}/run")

            try:
                req_body, message = self._parse_incoming_request(req)
                session_key = self._resolve_session_key(req=req, req_body=req_body)
                wait_for_completion = self._should_wait_for_completion(req=req, req_body=req_body)

                logger.debug(f"[HTTP Trigger] Message: {message}")
                logger.debug(f"[HTTP Trigger] Session Key: {session_key}")
                logger.debug(f"[HTTP Trigger] wait_for_completion: {wait_for_completion}")

                if not message:
                    logger.warning("[HTTP Trigger] Request rejected: Missing message")
                    return func.HttpResponse(
                        json.dumps({"error": "Message is required"}),
                        status_code=400,
                        mimetype="application/json"
                    )

                session_id = self._create_session_id(agent_name, session_key)
                correlation_id = self._generate_unique_id()

                logger.info(f"[HTTP Trigger] Using session ID: {session_id}")
                logger.info(f"[HTTP Trigger] Generated correlation ID: {correlation_id}")
                logger.info("[HTTP Trigger] Calling entity to run agent...")

                entity_instance_id = session_id.to_entity_id()
                run_request = self._build_request_data(
                    req_body,
                    message,
                    session_key,
                    correlation_id,
                )
                logger.info("Signalling entity %s with request: %s", entity_instance_id, run_request)
                await client.signal_entity(entity_instance_id, "run_agent", run_request)

                logger.info(f"[HTTP Trigger] Signal sent to entity {session_id}")

                if wait_for_completion:
                    result = await self._get_response_from_entity(
                        client=client,
                        entity_instance_id=entity_instance_id,
                        correlation_id=correlation_id,
                        message=message,
                        session_key=session_key
                    )

                    logger.info(f"[HTTP Trigger] Result status: {result.get('status', 'unknown')}")
                    logger.info("=" * 70)

                    return func.HttpResponse(
                        json.dumps(result),
                        status_code=200 if result.get("status") == "success" else 500,
                        mimetype="application/json"
                    )

                logger.info("[HTTP Trigger] wait_for_completion disabled; returning correlation ID")
                logger.info("=" * 70)

                accepted_response = self._build_accepted_response(
                    message=message,
                    session_key=session_key,
                    correlation_id=correlation_id
                )

                return func.HttpResponse(
                    json.dumps(accepted_response),
                    status_code=202,
                    mimetype="application/json"
                )

            except IncomingRequestError as exc:
                logger.warning(f"[HTTP Trigger] Request rejected: {str(exc)}")
                return func.HttpResponse(
                    json.dumps({"error": str(exc)}),
                    status_code=exc.status_code,
                    mimetype="application/json"
                )
            except ValueError as exc:
                logger.error(f"[HTTP Trigger] Invalid JSON: {str(exc)}")
                return func.HttpResponse(
                    json.dumps({"error": "Invalid JSON"}),
                    status_code=400,
                    mimetype="application/json"
                )
            except Exception as exc:
                logger.error(f"[HTTP Trigger] Error: {str(exc)}", exc_info=True)
                return func.HttpResponse(
                    json.dumps({"error": str(exc)}),
                    status_code=500,
                    mimetype="application/json"
                )

    def _setup_agent_entity(
        self,
        agent: AgentProtocol,
        agent_name: str,
        callback: Optional[AgentResponseCallbackProtocol],
    ) -> None:
        """
        Register the durable entity responsible for agent state.

        Args:
            agent: The agent instance
            agent_name: The agent name (used for both entity identification and function naming)
            callback: Optional callback for response updates
        """
        # Generate the Azure Function name for the entity
        entity_function_name = self._build_function_name(agent_name, "entity")

        def entity_function(context: df.DurableEntityContext) -> None:
            """
            Durable entity that manages agent execution and conversation state.

            Operations:
            - run_agent: Execute the agent with a message
            - get_state: Retrieve current conversation state
            - reset: Clear conversation history
            """

            entity_handler = create_agent_entity(agent, callback)
            entity_handler(context)

        # Set function name for Azure Functions (used in function.json generation)
        # Note: The entity is registered with entity_name parameter, so this __name__ is only
        # used by Azure Functions infrastructure, not for entity identification
        entity_function.__name__ = entity_function_name
        self.entity_trigger(context_name="context", entity_name=agent_name)(entity_function)

    def _setup_get_state_route(self, agent_name: str) -> None:
        """
        Register the GET route for retrieving conversation state.

        Args:
            agent_name: The agent name (used for both routing and entity identification)
        """

        state_function_name = self._build_function_name(agent_name, "state")

        @self.function_name(state_function_name)
        @self.route(
            route=f"agents/{agent_name}/" + "{" + SESSION_ID_FIELD + "}",
            methods=["GET"],
        )
        @self.durable_client_input(client_name="client")
        async def get_conversation_state(
            req: func.HttpRequest,
            client: df.DurableOrchestrationClient
        ) -> func.HttpResponse:
            """
            GET endpoint to retrieve conversation state for a given sessionId.

            URL: GET /api/agents/{agent_name}/{sessionId}
            """

            session_key = req.route_params.get(SESSION_ID_FIELD)

            logger.info("=" * 70)
            logger.info(f"[GET State] Retrieving state for session: {session_key}")

            try:
                # Create session ID
                session_id = AgentSessionId(name=agent_name, key=session_key)
                entity_instance_id = session_id.to_entity_id()

                state_response = await client.read_entity_state(entity_instance_id)

                if not state_response or not state_response.entity_exists:
                    logger.warning(f"[GET State] Session not found: {session_key}")
                    return func.HttpResponse(
                        json.dumps({"error": "Session not found"}),
                        status_code=404,
                        mimetype="application/json"
                    )

                state = state_response.entity_state
                if isinstance(state, str):
                    state = json.loads(state) if state else {}

                logger.info(f"[GET State] Found conversation with {state.get('message_count', 0)} messages")
                logger.info("=" * 70)

                return func.HttpResponse(
                    json.dumps(state, indent=2),
                    status_code=200,
                    mimetype="application/json"
                )

            except Exception as exc:
                logger.error(f"[GET State] Error: {str(exc)}", exc_info=True)
                return func.HttpResponse(
                    json.dumps({"error": str(exc)}),
                    status_code=500,
                    mimetype="application/json"
                )

    def _setup_health_route(self) -> None:
        """Register the optional health check route."""

        @self.route(route="health", methods=["GET"])
        def health_check(req: func.HttpRequest) -> func.HttpResponse:
            """Built-in health check endpoint."""

            agent_info = [
                {"name": name, "type": type(agent).__name__}
                for name, agent in self.agents.items()
            ]
            return func.HttpResponse(
                json.dumps({
                    "status": "healthy",
                    "agents": agent_info,
                    "agent_count": len(self.agents)
                }),
                status_code=200,
                mimetype="application/json"
            )

    @staticmethod
    def _build_function_name(agent_name: str, suffix: str) -> str:
        """Generate a unique, Azure Functions-compliant name for an agent function."""
        sanitized = re.sub(r"[^0-9a-zA-Z_]", "_", agent_name or "agent").strip("_")

        if not sanitized:
            sanitized = "agent"

        if sanitized[0].isdigit():
            sanitized = f"agent_{sanitized}"

        return f"{sanitized}_{suffix}"

    async def _read_cached_state(
        self,
        client: df.DurableOrchestrationClient,
        entity_instance_id: df.EntityId,
    ) -> Optional[AgentState]:
        state_response = await client.read_entity_state(entity_instance_id)
        if not state_response or not state_response.entity_exists:
            return None

        state_payload = state_response.entity_state
        if not isinstance(state_payload, dict):
            return None

        agent_state = AgentState()
        agent_state.restore_state(state_payload)
        return agent_state

    async def _get_response_from_entity(
        self,
        client: df.DurableOrchestrationClient,
        entity_instance_id: df.EntityId,
        correlation_id: str,
        message: str,
        session_key: str
    ) -> Dict[str, Any]:
        """Poll the entity state until a response is available or timeout occurs."""

        import asyncio

        max_retries = 10
        retry_count = 0
        result: Optional[Dict[str, Any]] = None

        logger.info(f"[HTTP Trigger] Waiting for response with correlation ID: {correlation_id}")

        while retry_count < max_retries:
            await asyncio.sleep(0.5)

            result = await self._poll_entity_for_response(
                client=client,
                entity_instance_id=entity_instance_id,
                correlation_id=correlation_id,
                message=message,
                session_key=session_key
            )
            if result is not None:
                break
            
            logger.debug(f"[HTTP Trigger] Response not available yet (retry {retry_count})")
            retry_count += 1

        if result is not None:
            return result

        logger.warning(
            f"[HTTP Trigger] Response with correlation ID {correlation_id} not found in time (waited {max_retries * 0.5} seconds)"
        )
        return await self._build_timeout_result(
            message=message,
            session_key=session_key,
            correlation_id=correlation_id
        )

    async def _poll_entity_for_response(
        self,
        client: df.DurableOrchestrationClient,
        entity_instance_id: df.EntityId,
        correlation_id: str,
        message: str,
        session_key: str
    ) -> Optional[Dict[str, Any]]:
        
        result: Optional[Dict[str, Any]] = None
        try:
            state = await self._read_cached_state(client, entity_instance_id)

            if state is None:
                return None

            agent_response = state.try_get_agent_response(correlation_id)
            if agent_response:
                result = self._build_success_result(
                    response_data=agent_response,
                    message=message,
                    session_key=session_key,
                    correlation_id=correlation_id,
                    state=state
                )
                logger.info(f"[HTTP Trigger] Found response for correlation ID: {correlation_id}")

        except Exception as exc:
            logger.warning(f"[HTTP Trigger] Error reading entity state: {exc}")

        return result

    async def _build_timeout_result(
        self,
        message: str,
        session_key: str,
        correlation_id: str
    ) -> Dict[str, Any]:
        """Create the timeout response."""

        return {
            "response": "Agent is still processing or timed out...",
            "message": message,
            SESSION_ID_FIELD: session_key,
            "status": "timeout",
            "correlationId": correlation_id
        }

    def _build_success_result(
        self,
        response_data: Dict[str, Any],
        message: str,
        session_key: str,
        correlation_id: str,
        state: AgentState
    ) -> Dict[str, Any]:
        """Build the success result returned to the HTTP caller."""

        return {
            "response": response_data.get("content"),
            "message": message,
            SESSION_ID_FIELD: session_key,
            "status": "success",
            "message_count": response_data.get("message_count", state.message_count),
            "correlationId": correlation_id
        }

    def _build_request_data(
        self,
        req_body: Dict[str, Any],
        message: str,
        conversation_id: str,
        correlation_id: str
    ) -> Dict[str, Any]:
        """Create the durable entity request payload."""

        enable_tool_calls_value = req_body.get("enable_tool_calls")
        enable_tool_calls = (
            True if enable_tool_calls_value is None
            else self._coerce_to_bool(enable_tool_calls_value)
        )

        return RunRequest(
            message=message,
            role=req_body.get("role", "user"),
            response_schema=req_body.get("response_schema"),
            enable_tool_calls=enable_tool_calls,
            conversation_id=conversation_id,
            correlation_id=correlation_id
        ).to_dict()

    def _build_accepted_response(
        self,
        message: str,
        session_key: str,
        correlation_id: str
    ) -> Dict[str, Any]:
        """Build the response returned when not waiting for completion."""

        return {
            "response": "Agent request accepted",
            "message": message,
            SESSION_ID_FIELD: session_key,
            "status": "accepted",
            "correlationId": correlation_id
        }

    def _generate_unique_id(self) -> str:
        """Generate a new unique identifier."""

        import uuid

        return uuid.uuid4().hex

    def _create_session_id(self, func_name: str, session_key: Optional[str]) -> AgentSessionId:
        """Create a session identifier using the provided key or a random value."""

        if session_key:
            return AgentSessionId(name=func_name, key=session_key)
        return AgentSessionId.with_random_key(name=func_name)

    def _resolve_session_key(
        self,
        req: func.HttpRequest,
        req_body: Dict[str, Any]
    ) -> str:
        """Retrieve the session key from request body or query parameters."""

        params = req.params or {}

        for key in SESSION_IDENTIFIER_KEYS:
            if key in req_body:
                return req_body.get(key)

        for key in SESSION_IDENTIFIER_KEYS:
            if key in params:
                return params.get(key)

        logger.debug("[HTTP Trigger] No session identifier provided; using random session key")
        return self._generate_unique_id()


    def _parse_incoming_request(self, req: func.HttpRequest) -> Tuple[Dict[str, Any], Any]:
        """Parse the incoming run request supporting JSON and plain text bodies."""

        headers = req.headers or {}
        if not isinstance(headers, Mapping):
            headers = {}
        content_type_header = headers.get("content-type")

        normalized_content_type = ""
        if content_type_header:
            normalized_content_type = content_type_header.split(";")[0].strip().lower()

        if normalized_content_type in {"application/json"} or normalized_content_type.endswith("+json"):
            parser = self._parse_json_body
        else:
            parser = self._parse_text_body

        return parser(req)

    @staticmethod
    def _parse_json_body(req: func.HttpRequest) -> Tuple[Dict[str, Any], Any]:
        req_body = req.get_json()
        if not isinstance(req_body, dict):
            raise IncomingRequestError("Invalid JSON payload. Expected an object.")

        message = req_body.get("message", "")
        return req_body, message

    @staticmethod
    def _parse_text_body(req: func.HttpRequest) -> Tuple[Dict[str, Any], Any]:
        body_bytes = req.get_body()
        text_body = body_bytes.decode("utf-8", errors="replace") if body_bytes else ""
        message = text_body.strip()

        if not message:
            raise IncomingRequestError("Message is required")

        return {}, message

    def _should_wait_for_completion(self, req: func.HttpRequest, req_body: Dict[str, Any]) -> bool:
        """Determine whether the caller requested to wait for completion."""

        header_value = None
        for key in req.headers:
            if key.lower() == "x-wait-for-completion":
                header_value = req.headers.get(key)
                break

        if header_value is not None:
            return self._coerce_to_bool(header_value)

        for key in ("wait_for_completion", "waitForCompletion", "WaitForCompletion"):
            if key in req_body:
                return self._coerce_to_bool(req_body.get(key))

        return False

    def _coerce_to_bool(self, value: Any) -> bool:
        """Convert various representations into a boolean flag."""

        if isinstance(value, bool):
            return value
        if value is None:
            return False
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes", "y", "on"}
        return False

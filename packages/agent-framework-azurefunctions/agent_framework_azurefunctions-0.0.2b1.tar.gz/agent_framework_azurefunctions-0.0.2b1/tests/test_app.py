"""
Unit tests for AgentFunctionApp

Run with: pytest tests/test_app.py -v
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import azure.functions as func
import azure.durable_functions as df
from agent_framework import ChatMessage
from durableagent.app import AgentFunctionApp
from durableagent.errors import IncomingRequestError


class TestAgentFunctionAppInit:
    """Test suite for AgentFunctionApp initialization"""

    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        mock_agent = Mock()
        mock_agent.name = "TestAgent"

        app = AgentFunctionApp(agents=[mock_agent])

        assert len(app.agents) == 1
        assert "TestAgent" in app.agents
        assert app.enable_health_check is True

    def test_init_with_custom_auth_level(self):
        """Test initialization with custom auth level"""
        mock_agent = Mock()
        mock_agent.name = "TestAgent"

        app = AgentFunctionApp(
            agents=[mock_agent],
            http_auth_level=func.AuthLevel.FUNCTION
        )

        # App should be created successfully
        assert "TestAgent" in app.agents

    def test_init_with_health_check_disabled(self):
        """Test initialization with health check disabled"""
        mock_agent = Mock()
        mock_agent.name = "TestAgent"

        app = AgentFunctionApp(agents=[mock_agent], enable_health_check=False)

        assert app.enable_health_check is False

    def test_init_stores_agent_reference(self):
        """Test that agent reference is stored correctly"""
        mock_agent = Mock()
        mock_agent.name = "TestAgent"

        app = AgentFunctionApp(agents=[mock_agent])

        assert app.agents["TestAgent"].name == "TestAgent"

    def test_add_agent_uses_specific_callback(self):
        """Verify that a per-agent callback overrides the default."""

        mock_agent = Mock()
        mock_agent.name = "CallbackAgent"
        specific_callback = Mock()

        with patch.object(AgentFunctionApp, "_setup_agent_functions") as setup_mock:
            app = AgentFunctionApp(default_callback=Mock())
            app.add_agent(mock_agent, callback=specific_callback)

        setup_mock.assert_called_once()
        _, _, passed_callback = setup_mock.call_args[0]
        assert passed_callback is specific_callback

    def test_default_callback_applied_when_no_specific(self):
        """Ensure the default callback is supplied when add_agent lacks override."""

        mock_agent = Mock()
        mock_agent.name = "DefaultAgent"
        default_callback = Mock()

        with patch.object(AgentFunctionApp, "_setup_agent_functions") as setup_mock:
            app = AgentFunctionApp(default_callback=default_callback)
            app.add_agent(mock_agent)

        setup_mock.assert_called_once()
        _, _, passed_callback = setup_mock.call_args[0]
        assert passed_callback is default_callback

    def test_init_with_agents_uses_default_callback(self):
        """Agents provided in __init__ should receive the default callback."""

        mock_agent = Mock()
        mock_agent.name = "InitAgent"
        default_callback = Mock()

        with patch.object(AgentFunctionApp, "_setup_agent_functions") as setup_mock:
            AgentFunctionApp(agents=[mock_agent], default_callback=default_callback)

        setup_mock.assert_called_once()
        _, _, passed_callback = setup_mock.call_args[0]
        assert passed_callback is default_callback


class TestAgentFunctionAppSetup:
    """Test suite for AgentFunctionApp setup and configuration"""

    def test_app_is_dfapp_instance(self):
        """Test that AgentFunctionApp is a DFApp instance"""
        mock_agent = Mock()
        mock_agent.name = "TestAgent"

        app = AgentFunctionApp(agents=[mock_agent])

        assert isinstance(app, df.DFApp)

    def test_setup_creates_http_trigger(self):
        """Test that setup creates HTTP trigger"""
        mock_agent = Mock()
        mock_agent.name = "TestAgent"

        def passthrough_decorator(*args, **kwargs):
            def decorator(func):
                return func

            return decorator

        with patch.object(AgentFunctionApp, 'route', new=passthrough_decorator):
            with patch.object(AgentFunctionApp, 'durable_client_input', new=passthrough_decorator):
                with patch.object(AgentFunctionApp, 'entity_trigger', new=passthrough_decorator):
                    app = AgentFunctionApp(agents=[mock_agent])

                    # Verify agent is registered
                    assert "TestAgent" in app.agents

    def test_multiple_apps_independent(self):
        """Test that multiple AgentFunctionApp instances are independent"""
        agent1 = Mock()
        agent1.name = "Agent1"
        agent2 = Mock()
        agent2.name = "Agent2"

        app1 = AgentFunctionApp(agents=[agent1])
        app2 = AgentFunctionApp(agents=[agent2])

        assert app1.agents["Agent1"].name == "Agent1"
        assert app2.agents["Agent2"].name == "Agent2"
        assert "Agent1" in app1.agents
        assert "Agent2" in app2.agents


class TestWaitForCompletionAndCorrelationId:
    """Tests for wait_for_completion flag and correlation ID handling."""

    def _create_app(self) -> AgentFunctionApp:
        mock_agent = Mock()
        mock_agent.__class__.__name__ = "MockAgent"
        mock_agent.name = "MockAgent"
        return AgentFunctionApp(agents=[mock_agent], enable_health_check=False)

    def _make_request(self, headers=None, params=None):
        request = Mock()
        request.headers = headers or {}
        request.params = params or {}
        return request

    def test_wait_for_completion_header_true(self):
        app = self._create_app()
        request = self._make_request(headers={"X-Wait-For-Completion": "true"})

        assert app._should_wait_for_completion(request, {}) is True

    def test_wait_for_completion_body_variants(self):
        app = self._create_app()
        request = self._make_request()

        assert app._should_wait_for_completion(request, {"wait_for_completion": "true"}) is True
        assert app._should_wait_for_completion(request, {"waitForCompletion": "1"}) is True
        assert app._should_wait_for_completion(request, {"WaitForCompletion": "no"}) is False


class TestAgentEntityOperations:
    """Test suite for entity operations"""

    @pytest.mark.asyncio
    async def test_entity_run_agent_operation(self):
        """Test that entity can run agent operation"""
        from durableagent.entities import AgentEntity

        mock_agent = Mock()
        mock_agent.run = AsyncMock(return_value=Mock(text="Test response"))

        entity = AgentEntity(mock_agent)
        mock_context = Mock()

        result = await entity.run_agent(
            mock_context,
            {"message": "Test message", "conversation_id": "test-conv-123", "correlation_id": "corr-app-entity-1"}
        )

        assert result["status"] == "success"
        assert result["response"] == "Test response"
        assert result["message"] == "Test message"
        assert result["conversation_id"] == "test-conv-123"
        assert entity.state.message_count == 1

    @pytest.mark.asyncio
    async def test_entity_stores_conversation_history(self):
        """Test that entity stores conversation history"""
        from durableagent.entities import AgentEntity

        mock_agent = Mock()
        mock_agent.run = AsyncMock(return_value=Mock(text="Response 1"))

        entity = AgentEntity(mock_agent)
        mock_context = Mock()

        # Send first message
        await entity.run_agent(
            mock_context,
            {"message": "Message 1", "conversation_id": "conv-1", "correlation_id": "corr-app-entity-2"}
        )

        history = entity.state.conversation_history
        assert len(history) == 2  # User + assistant

        user_msg = history[0]
        user_role = getattr(user_msg.role, "value", user_msg.role)
        assert user_role == "user"
        assert user_msg.text == "Message 1"

        assistant_msg = history[1]
        assistant_role = getattr(assistant_msg.role, "value", assistant_msg.role)
        assert assistant_role == "assistant"
        assert assistant_msg.text == "Response 1"

    @pytest.mark.asyncio
    async def test_entity_increments_message_count(self):
        """Test that entity increments message count"""
        from durableagent.entities import AgentEntity

        mock_agent = Mock()
        mock_agent.run = AsyncMock(return_value=Mock(text="Response"))

        entity = AgentEntity(mock_agent)
        mock_context = Mock()

        assert entity.state.message_count == 0

        await entity.run_agent(
            mock_context,
            {"message": "Message 1", "conversation_id": "conv-1", "correlation_id": "corr-app-entity-3a"}
        )
        assert entity.state.message_count == 1

        await entity.run_agent(
            mock_context,
            {"message": "Message 2", "conversation_id": "conv-1", "correlation_id": "corr-app-entity-3b"}
        )
        assert entity.state.message_count == 2

    def test_entity_get_state(self):
        """Test that entity returns correct state"""
        from durableagent.entities import AgentEntity

        mock_agent = Mock()
        mock_agent.__class__.__name__ = "TestAgent"

        entity = AgentEntity(mock_agent)
        entity.state.message_count = 5
        entity.state.last_response = "Last response text"
        entity.state.conversation_history = [
            ChatMessage(role="user", text="test", additional_properties={"timestamp": "2024-01-01T00:00:00Z"})
        ]

        mock_context = Mock()
        state = entity.get_state(mock_context)

        assert state["message_count"] == 5
        assert state["last_response"] == "Last response text"
        assert len(state["conversation_history"]) == 1
        assert state["agent_type"] == "TestAgent"

    def test_entity_reset(self):
        """Test that entity reset clears state"""
        from durableagent.entities import AgentEntity

        mock_agent = Mock()
        entity = AgentEntity(mock_agent)

        # Set some state
        entity.state.message_count = 10
        entity.state.last_response = "Some response"
        entity.state.conversation_history = [
            ChatMessage(role="user", text="test", additional_properties={"timestamp": "2024-01-01T00:00:00Z"})
        ]

        # Reset
        mock_context = Mock()
        entity.reset(mock_context)

        assert entity.state.message_count == 0
        assert entity.state.last_response is None
        assert len(entity.state.conversation_history) == 0


class TestAgentEntityFactory:
    """Test suite for entity factory function"""

    def test_create_agent_entity_returns_function(self):
        """Test that create_agent_entity returns a function"""
        from durableagent.entities import create_agent_entity

        mock_agent = Mock()
        entity_function = create_agent_entity(mock_agent)

        assert callable(entity_function)

    def test_entity_function_handles_run_agent_operation(self):
        """Test that entity function handles run_agent operation"""
        from durableagent.entities import create_agent_entity

        mock_agent = Mock()
        mock_agent.run = AsyncMock(return_value=Mock(text="Response"))

        entity_function = create_agent_entity(mock_agent)

        # Mock context
        mock_context = Mock()
        mock_context.operation_name = "run_agent"
        mock_context.get_input.return_value = {
            "message": "Test message",
            "conversation_id": "conv-123",
            "correlation_id": "corr-app-factory-1"
        }
        mock_context.get_state.return_value = None

        # Execute entity function
        entity_function(mock_context)

        # Verify result was set
        assert mock_context.set_result.called
        assert mock_context.set_state.called

    def test_entity_function_handles_get_state_operation(self):
        """Test that entity function handles get_state operation"""
        from durableagent.entities import create_agent_entity

        mock_agent = Mock()
        entity_function = create_agent_entity(mock_agent)

        # Mock context with existing state
        mock_context = Mock()
        mock_context.operation_name = "get_state"
        mock_context.get_state.return_value = {
            "message_count": 5,
            "conversation_history": [],
            "last_response": "Test"
        }

        # Execute entity function
        entity_function(mock_context)

        # Verify result was set
        assert mock_context.set_result.called
        result_call = mock_context.set_result.call_args[0][0]
        assert result_call["message_count"] == 5

    def test_entity_function_handles_reset_operation(self):
        """Test that entity function handles reset operation"""
        from durableagent.entities import create_agent_entity

        mock_agent = Mock()
        entity_function = create_agent_entity(mock_agent)

        # Mock context
        mock_context = Mock()
        mock_context.operation_name = "reset"
        mock_context.get_state.return_value = {
            "message_count": 5,
            "conversation_history": [{"role": "user", "content": "test"}],
            "last_response": "Test"
        }

        # Execute entity function
        entity_function(mock_context)

        # Verify result was set
        assert mock_context.set_result.called
        result_call = mock_context.set_result.call_args[0][0]
        assert result_call["status"] == "reset"

    def test_entity_function_handles_unknown_operation(self):
        """Test that entity function handles unknown operation"""
        from durableagent.entities import create_agent_entity

        mock_agent = Mock()
        entity_function = create_agent_entity(mock_agent)

        # Mock context with unknown operation
        mock_context = Mock()
        mock_context.operation_name = "unknown_operation"
        mock_context.get_state.return_value = None

        # Execute entity function
        entity_function(mock_context)

        # Verify error result was set
        assert mock_context.set_result.called
        result_call = mock_context.set_result.call_args[0][0]
        assert "error" in result_call
        assert "unknown_operation" in result_call["error"]

    def test_entity_function_restores_state(self):
        """Test that entity function restores state from context"""
        from durableagent.entities import create_agent_entity

        mock_agent = Mock()
        entity_function = create_agent_entity(mock_agent)

        # Mock context with existing state
        existing_state = {
            "message_count": 3,
            "conversation_history": [
                {"role": "user", "content": "msg1"},
                {"role": "assistant", "content": "resp1"}
            ],
            "last_response": "resp1"
        }

        mock_context = Mock()
        mock_context.operation_name = "get_state"
        mock_context.get_state.return_value = existing_state

        # Execute entity function
        entity_function(mock_context)

        # Verify state was restored
        result_call = mock_context.set_result.call_args[0][0]
        assert result_call["message_count"] == 3
        assert len(result_call["conversation_history"]) == 2


class TestErrorHandling:
    """Test suite for error handling"""

    @pytest.mark.asyncio
    async def test_entity_handles_agent_error(self):
        """Test that entity handles agent execution errors"""
        from durableagent.entities import AgentEntity

        mock_agent = Mock()
        mock_agent.run = AsyncMock(side_effect=Exception("Agent error"))

        entity = AgentEntity(mock_agent)
        mock_context = Mock()

        result = await entity.run_agent(
            mock_context,
            {"message": "Test message", "conversation_id": "conv-1", "correlation_id": "corr-app-error-1"}
        )

        assert result["status"] == "error"
        assert "error" in result
        assert "Agent error" in result["error"]
        assert result["error_type"] == "Exception"

    def test_entity_function_handles_exception(self):
        """Test that entity function handles exceptions gracefully"""
        from durableagent.entities import create_agent_entity

        mock_agent = Mock()
        # Force an exception by making get_input fail
        mock_agent.run = AsyncMock(side_effect=Exception("Test error"))

        entity_function = create_agent_entity(mock_agent)

        mock_context = Mock()
        mock_context.operation_name = "run_agent"
        mock_context.get_input.side_effect = Exception("Input error")
        mock_context.get_state.return_value = None

        # Execute entity function - should not raise
        entity_function(mock_context)

        # Verify error result was set
        assert mock_context.set_result.called
        result_call = mock_context.set_result.call_args[0][0]
        assert "error" in result_call


class TestIncomingRequestParsing:
    """Tests for parsing run requests with JSON and plain text bodies."""

    def _create_app(self) -> AgentFunctionApp:
        mock_agent = Mock()
        mock_agent.name = "ParserAgent"
        return AgentFunctionApp(agents=[mock_agent], enable_health_check=False)

    def test_parse_plain_text_body(self):
        app = self._create_app()

        request = Mock()
        request.get_json.side_effect = ValueError("Invalid JSON")
        request.get_body.return_value = b"Plain text message"

        req_body, message = app._parse_incoming_request(request)

        assert req_body == {}
        assert message == "Plain text message"

    def test_parse_plain_text_requires_content(self):
        app = self._create_app()

        request = Mock()
        request.get_json.side_effect = ValueError("Invalid JSON")
        request.get_body.return_value = b"   "

        with pytest.raises(IncomingRequestError) as exc_info:
            app._parse_incoming_request(request)

        assert "Message is required" in str(exc_info.value)

    def test_extract_session_key_from_query_params(self):
        app = self._create_app()

        request = Mock()
        request.params = {"sessionId": "query-session"}
        req_body = {}

        session_key = app._resolve_session_key(request, req_body)

        assert session_key == "query-session"


class TestHttpRunRoute:
    """Tests for the HTTP run route behavior."""

    @pytest.mark.asyncio
    async def test_http_run_accepts_plain_text(self):
        mock_agent = Mock()
        mock_agent.name = "HttpAgent"

        captured_handlers = {}

        def capture_decorator(*args, **kwargs):
            def decorator(func):
                return func

            return decorator

        def capture_route(*args, **kwargs):
            def decorator(func):
                route_key = kwargs.get("route") if kwargs else None
                captured_handlers[route_key] = func
                return func

            return decorator

        with patch.object(AgentFunctionApp, "function_name", new=capture_decorator), \
                patch.object(AgentFunctionApp, "route", new=capture_route), \
                patch.object(AgentFunctionApp, "durable_client_input", new=capture_decorator), \
                patch.object(AgentFunctionApp, "entity_trigger", new=capture_decorator):
            app = AgentFunctionApp(agents=[mock_agent], enable_health_check=False)

        run_route = f"agents/{mock_agent.name}/run"
        handler = captured_handlers[run_route]

        request = Mock()
        request.headers = {}
        request.params = {}
        request.route_params = {}
        request.get_json.side_effect = ValueError("Invalid JSON")
        request.get_body.return_value = b"Plain text via HTTP"

        client = AsyncMock()

        response = await handler(request, client)

        assert response.status_code == 202

        signal_args = client.signal_entity.call_args[0]
        run_request = signal_args[2]

        assert run_request["message"] == "Plain text via HTTP"
        assert run_request["role"] == "user"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

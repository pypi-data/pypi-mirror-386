"""
Unit tests for orchestration support (DurableAIAgent)

Run with: pytest tests/test_orchestration.py -v
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from agent_framework import AgentThread, BaseAgent
from durableagent.orchestration import DurableAIAgent, get_agent


class TestDurableAIAgent:
    """Test suite for DurableAIAgent wrapper"""

    def test_init(self):
        """Test DurableAIAgent initialization"""
        mock_context = Mock()
        mock_context.instance_id = "test-instance-123"

        agent = DurableAIAgent(mock_context, "TestAgent")

        assert agent.context == mock_context
        assert agent.agent_name == "TestAgent"

    def test_implements_agent_protocol(self):
        """Test that DurableAIAgent implements AgentProtocol"""
        from agent_framework import AgentProtocol
        mock_context = Mock()
        agent = DurableAIAgent(mock_context, "TestAgent")

        # Check that agent satisfies AgentProtocol
        assert isinstance(agent, AgentProtocol)

    def test_has_agent_protocol_properties(self):
        """Test that DurableAIAgent has AgentProtocol properties"""
        mock_context = Mock()
        agent = DurableAIAgent(mock_context, "TestAgent")

        # AgentProtocol properties
        assert hasattr(agent, 'id')
        assert hasattr(agent, 'name')
        assert hasattr(agent, 'description')
        assert hasattr(agent, 'display_name')

        # Verify values
        assert agent.name == "TestAgent"
        assert agent.description == "Durable agent proxy for TestAgent"
        assert agent.display_name == "TestAgent"
        assert agent.id is not None  # Auto-generated UUID

    def test_get_new_thread(self):
        """Test creating a new agent thread"""
        from durableagent.models import AgentSessionId

        mock_context = Mock()
        mock_context.instance_id = "test-instance-456"
        mock_context.new_uuid = Mock(return_value="test-guid-456")

        agent = DurableAIAgent(mock_context, "WriterAgent")
        thread = agent.get_new_thread()

        assert isinstance(thread, AgentThread)
        assert hasattr(thread, '_durable_session_id')
        assert isinstance(thread._durable_session_id, AgentSessionId)
        assert thread._durable_session_id.name == "WriterAgent"
        assert thread._durable_session_id.key == "test-guid-456"
        mock_context.new_uuid.assert_called_once()

    def test_get_new_thread_deterministic(self):
        """Test that get_new_thread creates deterministic session IDs"""
        from durableagent.models import AgentSessionId

        mock_context = Mock()
        mock_context.instance_id = "test-instance-789"
        mock_context.new_uuid = Mock(side_effect=["session-guid-1", "session-guid-2"])

        agent = DurableAIAgent(mock_context, "EditorAgent")

        # Create multiple threads - they should have unique session IDs
        thread1 = agent.get_new_thread()
        thread2 = agent.get_new_thread()

        assert isinstance(thread1._durable_session_id, AgentSessionId)
        assert isinstance(thread2._durable_session_id, AgentSessionId)
        assert thread1._durable_session_id.name == "EditorAgent"
        assert thread2._durable_session_id.name == "EditorAgent"
        assert thread1._durable_session_id.key == "session-guid-1"
        assert thread2._durable_session_id.key == "session-guid-2"
        assert mock_context.new_uuid.call_count == 2

    def test_run_creates_entity_call(self):
        """Test that run() creates proper entity call and returns a Task"""
        mock_context = Mock()
        mock_context.instance_id = "test-instance-001"
        mock_context.new_uuid = Mock(side_effect=["thread-guid", "correlation-guid"])

        # Mock call_entity to return a Task-like object
        mock_task = Mock()
        mock_task._is_scheduled = False  # Task attribute that orchestration checks

        mock_context.call_entity = Mock(return_value=mock_task)

        agent = DurableAIAgent(mock_context, "TestAgent")

        # Create thread
        thread = agent.get_new_thread()

        # Call run() - it should return the Task directly
        task = agent.run(
            messages="Test message",
            thread=thread,
            enable_tool_calls=True
        )

        # Verify run() returns the Task from call_entity
        assert task == mock_task

        # Verify call_entity was called with correct parameters
        assert mock_context.call_entity.called
        call_args = mock_context.call_entity.call_args
        entity_id, operation, request = call_args[0]

        assert operation == "run_agent"
        assert request["message"] == "Test message"
        assert request["enable_tool_calls"] is True
        assert "correlation_id" in request
        assert request["correlation_id"] == "correlation-guid"
        assert "conversation_id" in request
        assert request["conversation_id"] == "thread-guid"

    def test_run_without_thread(self):
        """Test that run() works without explicit thread (creates unique session key)"""
        mock_context = Mock()
        mock_context.instance_id = "test-instance-002"
        # Two calls to new_uuid: one for session_key, one for correlation_id
        mock_context.new_uuid = Mock(side_effect=["auto-generated-guid", "correlation-guid"])

        mock_task = Mock()
        mock_task._is_scheduled = False
        mock_context.call_entity = Mock(return_value=mock_task)

        agent = DurableAIAgent(mock_context, "TestAgent")

        # Call without thread
        task = agent.run(messages="Test message")

        assert task == mock_task

        # Verify the entity ID uses the auto-generated GUID
        call_args = mock_context.call_entity.call_args
        entity_id = call_args[0][0]
        assert entity_id.name == "TestAgent"
        assert entity_id.key == "auto-generated-guid"
        # Should be called twice: once for session_key, once for correlation_id
        assert mock_context.new_uuid.call_count == 2

    def test_run_with_response_schema(self):
        """Test that run() passes response schema correctly"""
        mock_context = Mock()
        mock_context.instance_id = "test-instance-003"

        mock_task = Mock()
        mock_task._is_scheduled = False
        mock_context.call_entity = Mock(return_value=mock_task)

        agent = DurableAIAgent(mock_context, "TestAgent")

        schema = {"type": "object", "properties": {"key": {"type": "string"}}}

        # Create thread and call
        thread = agent.get_new_thread()

        task = agent.run(
            messages="Test message",
            thread=thread,
            response_schema=schema
        )

        assert task == mock_task

        # Verify schema was passed in the call_entity arguments
        call_args = mock_context.call_entity.call_args
        input_data = call_args[0][2]  # Third argument is input_data
        assert "response_schema" in input_data
        assert input_data["response_schema"] == schema

    def test_messages_to_string(self):
        """Test converting ChatMessage list to string"""
        from agent_framework import ChatMessage

        mock_context = Mock()
        agent = DurableAIAgent(mock_context, "TestAgent")

        messages = [
            ChatMessage(role="user", text="Hello"),
            ChatMessage(role="assistant", text="Hi there"),
            ChatMessage(role="user", text="How are you?")
        ]

        result = agent._messages_to_string(messages)

        assert result == "Hello\nHi there\nHow are you?"

    def test_run_with_chat_message(self):
        """Test that run() handles ChatMessage input"""
        from agent_framework import ChatMessage

        mock_context = Mock()
        mock_context.new_uuid = Mock(side_effect=["thread-guid", "correlation-guid"])
        mock_task = Mock()
        mock_context.call_entity = Mock(return_value=mock_task)

        agent = DurableAIAgent(mock_context, "TestAgent")
        thread = agent.get_new_thread()

        # Call with ChatMessage
        msg = ChatMessage(role="user", text="Hello")
        task = agent.run(messages=msg, thread=thread)

        assert task == mock_task

        # Verify message was converted to string
        call_args = mock_context.call_entity.call_args
        request = call_args[0][2]
        assert request["message"] == "Hello"

    def test_run_stream_raises_not_implemented(self):
        """Test that run_stream() method raises NotImplementedError"""
        mock_context = Mock()
        agent = DurableAIAgent(mock_context, "TestAgent")

        with pytest.raises(NotImplementedError) as exc_info:
            agent.run_stream("Test message")

        error_msg = str(exc_info.value)
        assert "Streaming is not supported" in error_msg

    def test_entity_id_format(self):
        """Test that EntityId is created with correct format (name, key)"""
        from azure.durable_functions import EntityId

        mock_context = Mock()
        mock_context.new_uuid = Mock(return_value="test-guid-789")
        mock_context.call_entity = Mock(return_value=Mock())

        agent = DurableAIAgent(mock_context, "WriterAgent")
        thread = agent.get_new_thread()

        # Call run() to trigger entity ID creation
        agent.run("Test", thread=thread)

        # Verify call_entity was called with correct EntityId
        call_args = mock_context.call_entity.call_args
        entity_id = call_args[0][0]

        # EntityId should be EntityId(name="WriterAgent", key="test-guid-789")
        # Which formats as "@writeragent@test-guid-789"
        assert isinstance(entity_id, EntityId)
        assert entity_id.name == "WriterAgent"
        assert entity_id.key == "test-guid-789"
        assert str(entity_id) == "@writeragent@test-guid-789"


class TestGetAgentExtension:
    """Test suite for get_agent extension method"""

    def test_get_agent_function(self):
        """Test get_agent function creates DurableAIAgent"""
        mock_context = Mock()
        mock_context.instance_id = "test-instance-100"

        agent = get_agent(mock_context, "MyAgent")

        assert isinstance(agent, DurableAIAgent)
        assert agent.agent_name == "MyAgent"
        assert agent.context == mock_context

    def test_get_agent_context_extension(self):
        """Test that get_agent is added to DurableOrchestrationContext"""
        from azure.durable_functions import DurableOrchestrationContext

        # Verify the extension method exists
        assert hasattr(DurableOrchestrationContext, 'get_agent')

    def test_get_agent_via_context_method(self):
        """Test calling get_agent via context method"""
        from azure.durable_functions import DurableOrchestrationContext

        mock_context = Mock(spec=DurableOrchestrationContext)
        mock_context.instance_id = "test-instance-200"

        # Manually add the method for testing (since Mock doesn't inherit extensions)
        mock_context.get_agent = lambda agent_name: get_agent(mock_context, agent_name)

        agent = mock_context.get_agent("TestAgent")

        assert isinstance(agent, DurableAIAgent)
        assert agent.agent_name == "TestAgent"


class TestOrchestrationIntegration:
    """Integration tests for orchestration scenarios"""

    def test_sequential_agent_calls_simulation(self):
        """Simulate sequential agent calls in an orchestration"""
        mock_context = Mock()
        mock_context.instance_id = "test-orchestration-001"
        # new_uuid will be called 3 times:
        # 1. thread creation
        # 2. correlation_id for first call
        # 3. correlation_id for second call
        mock_context.new_uuid = Mock(side_effect=["deterministic-guid-001", "corr-1", "corr-2"])

        # Track entity calls
        entity_calls = []

        def mock_call_entity_side_effect(entity_id, operation, input_data):
            entity_calls.append({
                "entity_id": str(entity_id),
                "operation": operation,
                "input": input_data
            })

            # Return a mock Task
            mock_task = Mock()
            mock_task._is_scheduled = False
            return mock_task

        mock_context.call_entity = Mock(side_effect=mock_call_entity_side_effect)

        # Create agent
        agent = get_agent(mock_context, "WriterAgent")

        # Create thread
        thread = agent.get_new_thread()

        # First call - returns Task
        task1 = agent.run("Write something", thread=thread)
        assert hasattr(task1, '_is_scheduled')

        # Second call - returns Task
        task2 = agent.run(f"Improve: something", thread=thread)
        assert hasattr(task2, '_is_scheduled')

        # Verify both calls used the same entity (same session key)
        assert len(entity_calls) == 2
        assert entity_calls[0]["entity_id"] == entity_calls[1]["entity_id"]
        # EntityId format is @writeragent@deterministic-guid-001
        assert "@writeragent@deterministic-guid-001" == entity_calls[0]["entity_id"]
        # new_uuid called 3 times: thread + 2 correlation IDs
        assert mock_context.new_uuid.call_count == 3

    def test_multiple_agents_in_orchestration(self):
        """Test using multiple different agents in one orchestration"""
        mock_context = Mock()
        mock_context.instance_id = "test-orchestration-002"
        # Mock new_uuid to return different GUIDs for each call
        # Order: writer thread, editor thread, writer correlation, editor correlation
        mock_context.new_uuid = Mock(side_effect=["writer-guid-001", "editor-guid-002", "writer-corr", "editor-corr"])

        entity_calls = []

        def mock_call_entity_side_effect(entity_id, operation, input_data):
            entity_calls.append(str(entity_id))
            mock_task = Mock()
            mock_task._is_scheduled = False
            return mock_task

        mock_context.call_entity = Mock(side_effect=mock_call_entity_side_effect)

        # Create multiple agents
        writer = get_agent(mock_context, "WriterAgent")
        editor = get_agent(mock_context, "EditorAgent")

        writer_thread = writer.get_new_thread()
        editor_thread = editor.get_new_thread()

        # Call both agents - returns Tasks
        writer_task = writer.run("Write", thread=writer_thread)
        editor_task = editor.run("Edit", thread=editor_thread)

        assert hasattr(writer_task, '_is_scheduled')
        assert hasattr(editor_task, '_is_scheduled')

        # Verify different entity IDs were used
        assert len(entity_calls) == 2
        # EntityId format is @agentname@guid (lowercased agent name)
        assert entity_calls[0] == "@writeragent@writer-guid-001"
        assert entity_calls[1] == "@editoragent@editor-guid-002"


class TestAgentThreadSerialization:
    """Test that AgentThread can be serialized for orchestration state"""

    @pytest.mark.asyncio
    async def test_agent_thread_serialize(self):
        """Test that AgentThread can be serialized"""
        thread = AgentThread()

        # Serialize
        serialized = await thread.serialize()

        assert isinstance(serialized, dict)
        assert "service_thread_id" in serialized

    @pytest.mark.asyncio
    async def test_agent_thread_deserialize(self):
        """Test that AgentThread can be deserialized"""
        thread = AgentThread()
        serialized = await thread.serialize()

        # Deserialize
        restored = await AgentThread.deserialize(serialized)

        assert isinstance(restored, AgentThread)
        assert restored.service_thread_id == thread.service_thread_id

    @pytest.mark.asyncio
    async def test_durable_agent_thread_serialization(self):
        """Test that thread with _durable_session_id can be serialized"""
        from durableagent.models import AgentSessionId

        mock_context = Mock()
        mock_context.instance_id = "test-instance-999"
        mock_context.new_uuid = Mock(return_value="test-guid-999")

        agent = DurableAIAgent(mock_context, "TestAgent")
        thread = agent.get_new_thread()

        # Verify custom attribute exists
        assert hasattr(thread, '_durable_session_id')
        session_id = thread._durable_session_id
        assert isinstance(session_id, AgentSessionId)
        assert session_id.name == "TestAgent"
        assert session_id.key == "test-guid-999"

        # Standard serialization should still work
        serialized = await thread.serialize()
        assert isinstance(serialized, dict)

        # After deserialization, we'd need to restore the custom attribute
        # This would be handled by the orchestration framework
        restored = await AgentThread.deserialize(serialized)
        assert isinstance(restored, AgentThread)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

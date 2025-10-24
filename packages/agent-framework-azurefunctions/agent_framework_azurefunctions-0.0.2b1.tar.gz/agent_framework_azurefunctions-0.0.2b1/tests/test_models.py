"""
Unit tests for data models (AgentSessionId, RunRequest, AgentResponse, ChatRole)

Run with: pytest tests/test_models.py -v
"""

import pytest
import uuid
import azure.durable_functions as df
from durableagent.models import AgentSessionId, RunRequest, AgentResponse, ChatRole


class TestChatRole:
    """Test suite for ChatRole enum"""

    def test_chat_role_values(self):
        """Test that ChatRole has correct values"""
        assert ChatRole.USER == "user"
        assert ChatRole.SYSTEM == "system"
        assert ChatRole.ASSISTANT == "assistant"

    def test_chat_role_is_string(self):
        """Test that ChatRole values are strings"""
        assert isinstance(ChatRole.USER.value, str)
        assert isinstance(ChatRole.SYSTEM.value, str)
        assert isinstance(ChatRole.ASSISTANT.value, str)


class TestAgentSessionId:
    """Test suite for AgentSessionId"""

    def test_init_creates_session_id(self):
        """Test that AgentSessionId initializes correctly"""
        session_id = AgentSessionId(name="AgentEntity", key="test-key-123")

        assert session_id.name == "AgentEntity"
        assert session_id.key == "test-key-123"

    def test_with_random_key_generates_guid(self):
        """Test that with_random_key generates a GUID"""
        session_id = AgentSessionId.with_random_key(name="AgentEntity")

        assert session_id.name == "AgentEntity"
        assert len(session_id.key) == 32  # UUID hex is 32 chars
        # Verify it's a valid hex string
        int(session_id.key, 16)

    def test_with_random_key_unique_keys(self):
        """Test that with_random_key generates unique keys"""
        session_id1 = AgentSessionId.with_random_key(name="AgentEntity")
        session_id2 = AgentSessionId.with_random_key(name="AgentEntity")

        assert session_id1.key != session_id2.key

    def test_to_entity_id_conversion(self):
        """Test conversion to EntityId"""
        session_id = AgentSessionId(name="AgentEntity", key="test-key")
        entity_id = session_id.to_entity_id()

        assert isinstance(entity_id, df.EntityId)
        assert entity_id.name == "AgentEntity"
        assert entity_id.key == "test-key"

    def test_from_entity_id_conversion(self):
        """Test creation from EntityId"""
        entity_id = df.EntityId(name="AgentEntity", key="test-key")
        session_id = AgentSessionId.from_entity_id(entity_id)

        assert isinstance(session_id, AgentSessionId)
        assert session_id.name == "AgentEntity"
        assert session_id.key == "test-key"

    def test_round_trip_entity_id_conversion(self):
        """Test round-trip conversion to and from EntityId"""
        original = AgentSessionId(name="AgentEntity", key="test-key")
        entity_id = original.to_entity_id()
        restored = AgentSessionId.from_entity_id(entity_id)

        assert restored.name == original.name
        assert restored.key == original.key

    def test_str_representation(self):
        """Test string representation"""
        session_id = AgentSessionId(name="AgentEntity", key="test-key-123")
        str_repr = str(session_id)

        assert str_repr == "@AgentEntity@test-key-123"

    def test_repr_representation(self):
        """Test repr representation"""
        session_id = AgentSessionId(name="AgentEntity", key="test-key")
        repr_str = repr(session_id)

        assert "AgentSessionId" in repr_str
        assert "AgentEntity" in repr_str
        assert "test-key" in repr_str

    def test_parse_valid_session_id(self):
        """Test parsing valid session ID string"""
        session_id = AgentSessionId.parse("@AgentEntity@test-key-123")

        assert session_id.name == "AgentEntity"
        assert session_id.key == "test-key-123"

    def test_parse_invalid_format_no_prefix(self):
        """Test parsing invalid format without @ prefix"""
        with pytest.raises(ValueError) as exc_info:
            AgentSessionId.parse("AgentEntity@test-key")

        assert "Invalid agent session ID format" in str(exc_info.value)

    def test_parse_invalid_format_single_part(self):
        """Test parsing invalid format with single part"""
        with pytest.raises(ValueError) as exc_info:
            AgentSessionId.parse("@AgentEntity")

        assert "Invalid agent session ID format" in str(exc_info.value)

    def test_parse_with_multiple_at_signs_in_key(self):
        """Test parsing with @ signs in the key"""
        session_id = AgentSessionId.parse("@AgentEntity@key-with@symbols")

        assert session_id.name == "AgentEntity"
        assert session_id.key == "key-with@symbols"

    def test_parse_round_trip(self):
        """Test round-trip parse and string conversion"""
        original = AgentSessionId(name="AgentEntity", key="test-key")
        str_repr = str(original)
        parsed = AgentSessionId.parse(str_repr)

        assert parsed.name == original.name
        assert parsed.key == original.key


class TestRunRequest:
    """Test suite for RunRequest"""

    def test_init_with_defaults(self):
        """Test RunRequest initialization with defaults"""
        request = RunRequest(message="Hello", conversation_id="conv-default")

        assert request.message == "Hello"
        assert request.role == ChatRole.USER
        assert request.response_schema is None
        assert request.enable_tool_calls is True
        assert request.conversation_id == "conv-default"

    def test_init_with_all_fields(self):
        """Test RunRequest initialization with all fields"""
        schema = {"type": "object", "properties": {"answer": {"type": "string"}}}
        request = RunRequest(
            message="Hello",
            conversation_id="conv-123",
            role=ChatRole.SYSTEM,
            response_schema=schema,
            enable_tool_calls=False,
        )

        assert request.message == "Hello"
        assert request.role == ChatRole.SYSTEM
        assert request.response_schema == schema
        assert request.enable_tool_calls is False
        assert request.conversation_id == "conv-123"

    def test_to_dict_with_defaults(self):
        """Test to_dict with default values"""
        request = RunRequest(message="Test message", conversation_id="conv-to-dict")
        data = request.to_dict()

        assert data["message"] == "Test message"
        assert data["enable_tool_calls"] is True
        assert data["role"] == "user"
        assert "response_schema" not in data or data["response_schema"] is None
        assert data["conversation_id"] == "conv-to-dict"

    def test_to_dict_with_all_fields(self):
        """Test to_dict with all fields"""
        schema = {"type": "object"}
        request = RunRequest(
            message="Hello",
            conversation_id="conv-456",
            role=ChatRole.ASSISTANT,
            response_schema=schema,
            enable_tool_calls=False,
        )
        data = request.to_dict()

        assert data["message"] == "Hello"
        assert data["role"] == "assistant"
        assert data["response_schema"] == schema
        assert data["enable_tool_calls"] is False
        assert data["conversation_id"] == "conv-456"

    def test_from_dict_with_defaults(self):
        """Test from_dict with minimal data"""
        data = {"message": "Hello", "conversation_id": "conv-from-dict"}
        request = RunRequest.from_dict(data)

        assert request.message == "Hello"
        assert request.role == ChatRole.USER
        assert request.enable_tool_calls is True
        assert request.conversation_id == "conv-from-dict"

    def test_from_dict_with_all_fields(self):
        """Test from_dict with all fields"""
        data = {
            "message": "Test",
            "role": "system",
            "response_schema": {"type": "object"},
            "enable_tool_calls": False,
            "conversation_id": "conv-789"
        }
        request = RunRequest.from_dict(data)

        assert request.message == "Test"
        assert request.role == ChatRole.SYSTEM
        assert request.response_schema == {"type": "object"}
        assert request.enable_tool_calls is False
        assert request.conversation_id == "conv-789"

    def test_from_dict_invalid_role_defaults_to_user(self):
        """Test from_dict with invalid role defaults to USER"""
        data = {
            "message": "Test",
            "role": "invalid_role",
            "conversation_id": "conv-invalid-role"
        }
        request = RunRequest.from_dict(data)

        assert request.role == ChatRole.USER

    def test_from_dict_empty_message(self):
        """Test from_dict with empty message"""
        data = {"conversation_id": "conv-empty"}
        request = RunRequest.from_dict(data)

        assert request.message == ""
        assert request.role == ChatRole.USER
        assert request.conversation_id == "conv-empty"

    def test_round_trip_dict_conversion(self):
        """Test round-trip to_dict and from_dict"""
        original = RunRequest(
            message="Test message",
            conversation_id="conv-123",
            role=ChatRole.SYSTEM,
            response_schema={"type": "string"},
            enable_tool_calls=False,
        )

        data = original.to_dict()
        restored = RunRequest.from_dict(data)

        assert restored.message == original.message
        assert restored.role == original.role
        assert restored.response_schema == original.response_schema
        assert restored.enable_tool_calls == original.enable_tool_calls
        assert restored.conversation_id == original.conversation_id

    def test_init_with_correlation_id(self):
        """Test RunRequest initialization with correlation_id"""
        request = RunRequest(
            message="Test message",
            conversation_id="conv-corr-init",
            correlation_id="corr-123"
        )

        assert request.message == "Test message"
        assert request.correlation_id == "corr-123"

    def test_to_dict_with_correlation_id(self):
        """Test to_dict includes correlation_id"""
        request = RunRequest(
            message="Test",
            conversation_id="conv-corr-to-dict",
            correlation_id="corr-456"
        )
        data = request.to_dict()

        assert data["message"] == "Test"
        assert data["correlation_id"] == "corr-456"

    def test_from_dict_with_correlation_id(self):
        """Test from_dict with correlation_id"""
        data = {
            "message": "Test",
            "correlation_id": "corr-789",
            "conversation_id": "conv-corr-from-dict"
        }
        request = RunRequest.from_dict(data)

        assert request.message == "Test"
        assert request.correlation_id == "corr-789"
        assert request.conversation_id == "conv-corr-from-dict"

    def test_round_trip_with_correlation_id(self):
        """Test round-trip to_dict and from_dict with correlation_id"""
        original = RunRequest(
            message="Test message",
            conversation_id="conv-123",
            role=ChatRole.SYSTEM,
            correlation_id="corr-123",
        )

        data = original.to_dict()
        restored = RunRequest.from_dict(data)

        assert restored.message == original.message
        assert restored.role == original.role
        assert restored.correlation_id == original.correlation_id
        assert restored.conversation_id == original.conversation_id


class TestAgentResponse:
    """Test suite for AgentResponse"""

    def test_init_with_required_fields(self):
        """Test AgentResponse initialization with required fields"""
        response = AgentResponse(
            response="Test response",
            message="Test message",
            conversation_id="conv-123",
            status="success"
        )

        assert response.response == "Test response"
        assert response.message == "Test message"
        assert response.conversation_id == "conv-123"
        assert response.status == "success"
        assert response.message_count == 0
        assert response.error is None
        assert response.error_type is None
        assert response.structured_response is None

    def test_init_with_all_fields(self):
        """Test AgentResponse initialization with all fields"""
        structured = {"answer": "42"}
        response = AgentResponse(
            response=None,
            message="What is the answer?",
            conversation_id="conv-456",
            status="success",
            message_count=5,
            error=None,
            error_type=None,
            structured_response=structured
        )

        assert response.response is None
        assert response.structured_response == structured
        assert response.message_count == 5

    def test_to_dict_with_text_response(self):
        """Test to_dict with text response"""
        response = AgentResponse(
            response="Text response",
            message="Message",
            conversation_id="conv-1",
            status="success",
            message_count=3
        )
        data = response.to_dict()

        assert data["response"] == "Text response"
        assert data["message"] == "Message"
        assert data["conversation_id"] == "conv-1"
        assert data["status"] == "success"
        assert data["message_count"] == 3
        assert "structured_response" not in data
        assert "error" not in data
        assert "error_type" not in data

    def test_to_dict_with_structured_response(self):
        """Test to_dict with structured response"""
        structured = {"answer": 42, "confidence": 0.95}
        response = AgentResponse(
            response=None,
            message="Question",
            conversation_id="conv-2",
            status="success",
            structured_response=structured
        )
        data = response.to_dict()

        assert data["structured_response"] == structured
        assert "response" not in data

    def test_to_dict_with_error(self):
        """Test to_dict with error"""
        response = AgentResponse(
            response=None,
            message="Failed message",
            conversation_id="conv-3",
            status="error",
            error="Something went wrong",
            error_type="ValueError"
        )
        data = response.to_dict()

        assert data["status"] == "error"
        assert data["error"] == "Something went wrong"
        assert data["error_type"] == "ValueError"

    def test_to_dict_prefers_structured_over_text(self):
        """Test to_dict prefers structured_response over response"""
        structured = {"result": "structured"}
        response = AgentResponse(
            response="Text response",
            message="Message",
            conversation_id="conv-4",
            status="success",
            structured_response=structured
        )
        data = response.to_dict()

        assert "structured_response" in data
        assert data["structured_response"] == structured
        # Text response should not be included when structured is present
        assert "response" not in data


class TestModelIntegration:
    """Test suite for integration between models"""

    def test_run_request_with_session_id(self):
        """Test using RunRequest with AgentSessionId"""
        session_id = AgentSessionId.with_random_key("AgentEntity")
        request = RunRequest(
            message="Test message",
            conversation_id=str(session_id)
        )

        assert request.conversation_id == str(session_id)
        assert request.conversation_id.startswith("@AgentEntity@")

    def test_response_from_run_request(self):
        """Test creating AgentResponse from RunRequest"""
        request = RunRequest(
            message="What is 2+2?",
            conversation_id="conv-123",
            role=ChatRole.USER
        )

        response = AgentResponse(
            response="4",
            message=request.message,
            conversation_id=request.conversation_id,
            status="success",
            message_count=1
        )

        assert response.message == request.message
        assert response.conversation_id == request.conversation_id


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

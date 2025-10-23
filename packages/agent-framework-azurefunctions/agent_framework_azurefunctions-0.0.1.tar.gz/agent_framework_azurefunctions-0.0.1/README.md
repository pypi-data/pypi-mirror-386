# Durable Agent Framework (Python)

A Python framework for building stateful, durable AI agents using **Microsoft Agent Framework** and **Azure Durable Functions**. This framework leverages **Durable Entities** to provide automatic state persistence, conversation history tracking, and reliable agent execution.

## Features

### Core Capabilities

- **Stateful Agent Execution**: Agents run inside Durable Entities with automatic state persistence
- **Conversation History**: Full conversation history tracking per conversation ID
- **Durable by Design**: Built-in reliability, automatic retries, and error handling
- **Zero Boilerplate**: Simple API - just define your agent and tools
- **Full Azure Functions Integration**: Inherits from DFApp, so you can add timers, queues, blobs, etc.
- **Production Ready**: Built on Azure Durable Functions for enterprise-scale reliability

### Architecture Highlights

- **Entity-Based Pattern**: Uses Durable Entities (not orchestrations) for better state management
- **Direct Execution**: Agents run directly inside entities - no middleware layer needed
- **Conversation Retrieval**: GET endpoint to retrieve conversation state by ID
- **Native Agent Framework Types**: Uses `ChatMessage` and `AgentRunResponse` objects for type safety
- **Automatic Serialization**: State is automatically persisted and restored using agent_framework's `to_dict()` / `from_dict()`
- **Signal-Based Operations**: Efficient entity signaling for agent execution

## Quick Start

### Prerequisites

- Python 3.10+
- Azure Functions Core Tools v4
- Azure subscription (for deployment)

### Installation

```bash
pip install agent-framework-azurefunctions
```

Or add to your `requirements.txt`:
```
agent-framework-azurefunctions
```

For development installation from source:
```bash
pip install -e .
```

### Create Your First Agent

#### 1. Create a new Azure Functions project

```bash
func init my-agent-app --python
cd my-agent-app
```

#### 2. Create `function_app.py`

```python
import os
from durableagent import AgentFunctionApp
from agent_framework.azure import AzureOpenAIAssistantsClient
from azure.identity import AzureCliCredential


# Define your tools (optional)
def get_weather(location: str) -> dict:
    """Get the weather for a location."""
    return {
        "location": location,
        "temperature": 72,
        "conditions": "Sunny"
    }


# Create your agent
agent = AzureOpenAIAssistantsClient(
    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4"),
    credential=AzureCliCredential(),
).create_agent(
    name="WeatherAgent",
    instructions="You are a helpful weather assistant.",
    tools=[get_weather],
)

# Create the function app - that's it!
app = AgentFunctionApp(agents=[agent])
```

#### 3. Configure environment variables

Create a `.env` file or set in `local.settings.json`:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_OPENAI_ENDPOINT": "<https://your-endpoint.openai.azure.com>",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4"
  }
}
```

#### 4. Run locally

```bash
func start
```

#### 5. Test your agent

```bash
curl -X POST http://localhost:7071/api/agents/WeatherAgent/run \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the weather like in Seattle?",
    "sessionId": "user-123"
  }'
```

Response:
```json
{
  "response": "The weather in Seattle is currently 72°F and sunny.",
  "message": "What is the weather like in Seattle?",
  "sessionId": "user-123",
  "status": "success",
  "message_count": 1
}
```

#### 6. Retrieve conversation state

```bash
curl http://localhost:7071/api/agents/WeatherAgent/user-123
```

Response:
```json
{
  "message_count": 1,
  "conversation_history": [
    {
      "role": "user",
      "content": "What is the weather like in Seattle?",
      "timestamp": "2025-01-15T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "The weather in Seattle is currently 72°F and sunny.",
      "timestamp": "2025-01-15T10:30:05Z",
      "agent_response": {
        "text": "The weather in Seattle is currently 72°F and sunny.",
        "kind": "agent_message",
        "tool_calls": [],
        "usage": {
          "prompt_tokens": 45,
          "completion_tokens": 12,
          "total_tokens": 57
        }
      }
    }
  ],
  "last_response": "The weather in Seattle is currently 72°F and sunny.",
  "agent_type": "Agent"
}
```

**Note:**
- Conversation history uses native `ChatMessage` objects from agent_framework
- Assistant messages include full `AgentRunResponse` metadata in `additional_properties.agent_response`
- This preserves all framework details: `kind`, `tool_calls`, `usage` (tokens), and other fields
- The state is serialized using agent_framework's `to_dict()` and restored using `from_dict()`

## Multi-Agent Support

The framework supports multiple agents in a single app, giving you two flexible options:

### Option 1: Pass a list of agents during initialization

```python
from durableagent import AgentFunctionApp
from agent_framework.azure import AzureOpenAIAssistantsClient

# Create multiple agents with unique names
weather_agent = AzureOpenAIAssistantsClient(...).create_agent(
    name="WeatherAgent",
    instructions="You are a helpful weather assistant.",
    tools=[get_weather],
)

math_agent = AzureOpenAIAssistantsClient(...).create_agent(
    name="MathAgent",
    instructions="You are a helpful math assistant.",
    tools=[calculate],
)

# Register all agents at once
app = AgentFunctionApp(agents=[weather_agent, math_agent])
```

This creates separate routes for each agent:
- `POST /api/agents/WeatherAgent/run`
- `GET /api/agents/WeatherAgent/{sessionId}`
- `POST /api/agents/MathAgent/run`
- `GET /api/agents/MathAgent/{sessionId}`

**Note**: Each agent must have a unique `name` attribute. The framework uses this name to create routes and identify agents.

### Option 2: Add agents incrementally with `add_agent()`

```python
from durableagent import AgentFunctionApp

# Start with an empty app
app = AgentFunctionApp()

# Add agents one at a time (agents use their name attribute for routing)
app.add_agent(weather_agent)
app.add_agent(math_agent)
```

### Health Check with Multiple Agents

The health check endpoint returns information about all registered agents:

```bash
curl http://localhost:7071/api/health
```

Response:
```json
{
  "status": "healthy",
  "agents": [
    {"name": "WeatherAgent", "type": "AzureOpenAIAssistantsAgent"},
    {"name": "MathAgent", "type": "AzureOpenAIAssistantsAgent"}
  ],
  "agent_count": 2
}
```

See the [02_MultiAgent sample](samples/02_MultiAgent/) for a complete example.

## API Reference

### AgentFunctionApp

The main class for creating a durable agent function app.

```python
class AgentFunctionApp(df.DFApp):
    def __init__(
        self,
        agents: Optional[List[AgentProtocol]] = None,
        http_auth_level: func.AuthLevel = func.AuthLevel.ANONYMOUS,
        enable_health_check: bool = True,
        default_callback: Optional[AgentResponseCallbackProtocol] = None,
    )
```

**Parameters:**

- `agents`: List of agent instances to register. Each agent must have a `name` attribute.
- `http_auth_level`: Authentication level for HTTP triggers
- `enable_health_check`: Enable built-in health check endpoint at `/health`
- `default_callback`: Optional callback invoked for agents that don't have a specific per-agent callback

**Note:** If no agents are provided, they can be added later using `add_agent()`.

**Type Safety:**
- The framework uses `AgentProtocol` type hints for full type safety
- All agents from `agent_framework` implement `AgentProtocol`
- Provides IntelliSense support and compile-time type checking

**Automatically Creates (per agent):**

1. **POST `/api/agents/{agent_name}/run`**: Send messages to the agent
2. **GET `/api/agents/{agent_name}/{sessionId}`**: Retrieve conversation state
3. **GET `/api/health`**: Health check endpoint showing all agents (if enabled)

**Methods:**

```python
def add_agent(
    self,
    agent: AgentProtocol,
    callback: Optional[AgentResponseCallbackProtocol] = None,
) -> None
```

Add an agent to the app after initialization. The agent's `name` attribute is used for routing.

Raises `ValueError` if:
- The agent doesn't have a `name` attribute
- An agent with the same name is already registered

**Response Callbacks:**

Use `AgentResponseCallbackProtocol` implementations to observe streaming updates and final responses. Pass a default callback when constructing the app or provide per-agent overrides via the `callback` argument to `add_agent`. Callbacks receive an `AgentCallbackContext` that includes the agent name, correlation ID, conversation ID, and request message.

```python
from durableagent import AgentFunctionApp
from durableagent.callbacks import AgentCallbackContext, AgentResponseCallbackProtocol


class ConsoleLogger(AgentResponseCallbackProtocol):
  async def on_streaming_response_update(self, update, context: AgentCallbackContext) -> None:
    print(f"[{context.agent_name}] chunk: {update.text}")

  async def on_agent_response(self, response, context: AgentCallbackContext) -> None:
    print(f"[{context.agent_name}] final: {response.text}")


app = AgentFunctionApp(default_callback=ConsoleLogger())
```

### AgentState

State management class that uses native agent_framework types.

```python
class AgentState:
    def __init__(self)

  def add_user_message(self, content: str, correlation_id: str, role: str = "user") -> None
      def add_assistant_message(self, content: str, agent_response: AgentRunResponse) -> None

      def get_state(self) -> Dict[str, Any]
      def restore_state(self, state: Dict[str, Any]) -> None
      def reset(self) -> None
```

**Key Features:**
- Uses `ChatMessage` objects from agent_framework for conversation history
- Stores full `AgentRunResponse` metadata in assistant messages
- Automatic serialization using `to_dict()` / `from_dict()`
- Preserves all agent framework response details (kind, tool_calls, usage/tokens, etc.)

**Example:**
```python
from durableagent import AgentState
from agent_framework import ChatMessage, AgentRunResponse

state = AgentState()

# Add user message
state.add_user_message("Hello!", correlation_id="corr-123")

# Add assistant response with full metadata
response = AgentRunResponse(
    messages=[ChatMessage(role='assistant', text='Hi there!')],
    response_id='123'
)
state.add_assistant_message("Hi there!", response)

# Serialize for persistence
serialized = state.get_state()

# Restore from persistence
restored = AgentState()
restored.restore_state(serialized)
```

### AgentSessionId

A session identifier that wraps Azure Durable Functions EntityId for type-safe session management.

```python
class AgentSessionId:
    def __init__(self, name: str, key: str)

    @staticmethod
    def with_random_key(name: str) -> AgentSessionId

    def to_entity_id(self) -> df.EntityId

    @staticmethod
    def from_entity_id(entity_id: df.EntityId) -> AgentSessionId

    @staticmethod
    def parse(session_id_string: str) -> AgentSessionId
```

**Examples:**

```python
from durableagent import AgentSessionId

# Create with specific key
session_id = AgentSessionId(name="AgentEntity", key="user-123")

# Create with random GUID
session_id = AgentSessionId.with_random_key(name="AgentEntity")

# Convert to EntityId for Durable Functions APIs
entity_id = session_id.to_entity_id()

# Parse from string format (@name@key)
session_id = AgentSessionId.parse("@AgentEntity@user-123")

# String representation
print(session_id)  # @AgentEntity@user-123
```

### Request/Response Format

#### POST `/api/agents/{agent_name}/run` - Send Message

**URL:** `POST /api/agents/{agent_name}/run`

**Request:**
```json
{
  "message": "Your message to the agent",
  "sessionId": "optional-session-id",
  "role": "user",
  "enable_tool_calls": true,
  "response_schema": {}
}
```

**Note:**
- Only `message` is required. If `sessionId` is not provided, a random session ID will be generated.
- `sessionKey` is also supported as an alias for `sessionId`

**Response:**
```json
{
  "response": "Agent's response",
  "message": "Your original message",
  "sessionId": "session-id",
  "status": "success",
  "message_count": 5
}
```

#### GET `/api/agents/{agent_name}/{sessionId}` - Get State

**URL:** `GET /api/agents/{agent_name}/{sessionId}`

**Response:**
```json
{
  "message_count": 5,
  "conversation_history": [
    {
      "role": "user",
      "content": "Message",
      "timestamp": "2025-01-15T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "Response text",
      "timestamp": "2025-01-15T10:30:05Z",
      "agent_response": {
        "text": "Response text",
        "kind": "agent_message",
        "tool_calls": [...],
        "usage": {
          "prompt_tokens": 100,
          "completion_tokens": 50,
          "total_tokens": 150
        }
      }
    }
  ],
  "last_response": "Last agent response",
  "agent_type": "Agent"
}
```

**Conversation History Structure:**
- **User messages**: Include `role`, `content`, `timestamp`
- **Assistant messages**: Include `role`, `content`, `timestamp`, and **`agent_response`**
  - `agent_response` contains the full Microsoft Agent Framework response object
  - Includes metadata: `kind`, `tool_calls`, `usage` (tokens), and other framework fields
  - Preserves all response details for analysis and debugging

## Advanced Usage

### Multiple Agents in One App

```python
from durableagent import AgentFunctionApp

# Create multiple agents
weather_agent = create_weather_agent()
news_agent = create_news_agent()

# Each agent gets its own route
weather_app = AgentFunctionApp(agent=weather_agent, agent_name="WeatherAgent")
news_app = AgentFunctionApp(agent=news_agent, agent_name="NewsAgent")
```

### Adding Custom Azure Functions

Since `AgentFunctionApp` inherits from `DFApp`, you can add any Azure Functions:

```python
import azure.functions as func
from durableagent import AgentFunctionApp

app = AgentFunctionApp(agent=my_agent)

# Add a timer trigger
@app.timer_trigger(schedule="0 */5 * * * *", arg_name="timer")
def periodic_task(timer: func.TimerRequest):
    print("Runs every 5 minutes")

# Add a queue trigger
@app.queue_trigger(arg_name="msg", queue_name="tasks", connection="AzureWebJobsStorage")
def process_queue(msg: func.QueueMessage):
    print(f"Processing: {msg.get_body()}")

# Add a blob trigger
@app.blob_trigger(arg_name="blob", path="uploads/{name}", connection="AzureWebJobsStorage")
def process_blob(blob: func.InputStream):
    print(f"Processing blob: {blob.name}")

# Add custom HTTP endpoints
@app.route(route="status", methods=["GET"])
def get_status(req: func.HttpRequest):
    return func.HttpResponse("Running", status_code=200)
```

### Using Different Agent Clients

#### Azure OpenAI Assistants API

```python
from agent_framework.azure import AzureOpenAIAssistantsClient
from azure.identity import AzureCliCredential

agent = AzureOpenAIAssistantsClient(
    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    deployment_name="gpt-4",
    credential=AzureCliCredential(),
).create_agent(
    name="MyAgent",
    instructions="You are a helpful assistant.",
    tools=[my_tool],
)
```

#### Azure AI Agent Service

```python
from azure.ai.projects.aio import AzureAIAgentClient
from azure.identity.aio import DefaultAzureCredential

agent = AzureAIAgentClient(
    async_credential=DefaultAzureCredential()
).create_agent(
    name="MyAgent",
    instructions="You are a helpful assistant.",
    tools=[my_tool],
)
```

### Custom Authentication

```python
import azure.functions as func
from durableagent import AgentFunctionApp

app = AgentFunctionApp(
    agent=my_agent,
    http_auth_level=func.AuthLevel.FUNCTION  # Requires function key
)
```

## Architecture

### How It Works

1. **HTTP Trigger** receives user message with optional conversation_id
2. **Durable Entity** is signaled with the message
3. **Agent runs directly** inside the entity, returning an `AgentRunResponse`
4. **Response is extracted** (text or structured data) and returned to caller
5. **Full AgentRunResponse** is stored in state with all metadata
6. **State is persisted** automatically (conversation history as ChatMessages, message count)
7. **GET endpoint** allows retrieving full conversation state with all response details

### Why Durable Entities?

Traditional orchestrations require middleware to intercept tool calls and execute them as activities. **Durable Entities provide a simpler pattern**:

- ✅ State is automatically durable - no middleware needed
- ✅ Operations run inside the entity - natural execution model
- ✅ Better for long-running conversations - entities are designed for state
- ✅ Simpler code - less boilerplate
- ✅ Direct agent execution - no interception layer

### Entity Operations

The framework creates entities with these operations:

- `run_agent`: Execute agent with a message
- `get_state`: Retrieve conversation state
- `reset`: Clear conversation history

## Deployment

### Deploy to Azure

#### 1. Create Azure resources

```bash
# Create resource group
az group create --name myResourceGroup --location eastus

# Create storage account
az storage account create \
  --name mystorageaccount \
  --resource-group myResourceGroup \
  --location eastus

# Create function app
az functionapp create \
  --name myagentapp \
  --resource-group myResourceGroup \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --storage-account mystorageaccount
```

#### 2. Configure app settings

```bash
az functionapp config appsettings set \
  --name myagentapp \
  --resource-group myResourceGroup \
  --settings \
    AZURE_OPENAI_ENDPOINT="your-endpoint" \
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
```

#### 3. Deploy

```bash
func azure functionapp publish myagentapp
```

### Monitoring

Enable Application Insights for monitoring:

```bash
az monitor app-insights component create \
  --app myagentapp-insights \
  --location eastus \
  --resource-group myResourceGroup

# Link to function app
az functionapp config appsettings set \
  --name myagentapp \
  --resource-group myResourceGroup \
  --settings \
    APPINSIGHTS_INSTRUMENTATIONKEY="your-key"
```

## Examples

See the `samples/` directory for complete examples:

- **`basic_agent.py`**: Simple weather agent with multiple tools
- **`full_featured_app.py`**: Advanced example with custom functions, timers, queues, and more
- **`function_app_example/`**: Complete deployable project template

## Troubleshooting

### Common Issues

**Agent not responding:**
- Check that Azure OpenAI endpoint and deployment are correct
- Verify authentication credentials (run `az login`)
- Check function app logs with `func start --verbose`

**State not persisting:**
- Ensure AzureWebJobsStorage is configured
- For local development, use Azurite storage emulator
- Check entity state with GET endpoint

**Import errors:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Verify Python version is 3.9 or higher

### Logging

The framework uses Python's standard logging. To see detailed logs:

```bash
func start --verbose
```

Or configure logging level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

Contributions are welcome! Please see the main repository for contribution guidelines.

## License

See LICENSE file in the repository root.

## Related Projects

- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [Azure Durable Functions](https://docs.microsoft.com/azure/azure-functions/durable/)
- [Azure Functions Python](https://docs.microsoft.com/azure/azure-functions/functions-reference-python)

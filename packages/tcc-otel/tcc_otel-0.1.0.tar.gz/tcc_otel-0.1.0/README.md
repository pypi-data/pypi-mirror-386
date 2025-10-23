# TCC OpenTelemetry SDK for Python

OpenTelemetry instrumentation for Python AI frameworks to send traces to [The Context Company](https://www.thecontext.company) platform.

## Features

- Zero-config setup - Just one function call to start tracing
- Framework-specific instrumentations - Currently supports LangChain, with more coming soon
- Automatic capture - LLM calls, tool executions, and workflow traces
- Custom metadata - Tag traces with your own business logic (user IDs, service names, environments, etc.)
- Secure - API key-based authentication
- Production-ready - Built on OpenTelemetry standards

## Installation

```bash
# Install base package
pip install tcc-otel

# Install with LangChain support
pip install tcc-otel[langchain]
```

## Quick Start

### LangChain

```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize TCC instrumentation BEFORE importing LangChain
from tcc_otel import instrument_langchain

instrument_langchain(
    api_key=os.getenv("TCC_API_KEY"),
)

# Now import and use LangChain - all operations will be automatically traced
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# Your code here...
```

## Configuration

### Environment Variables

```bash
TCC_API_KEY=your_api_key_here
```

### Parameters

- `api_key` (required): Your TCC API key
- `trace_content` (optional): Whether to capture prompts and completions (default: True)

## Adding Custom Metadata

Custom metadata allows you to tag your traces with your own business logic, such as:
- Service names (e.g., `"customer-chatbot"`, `"api-backend"`)
- User IDs (e.g., `"user-123"`)
- Environments (e.g., `"production"`, `"staging"`)
- Feature flags, tenant IDs, or any other custom dimensions

Custom metadata is added using **LangChain's RunnableConfig** by passing a `metadata` dict as the second argument to `invoke()`:

```python
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# Create your agent
model = ChatOpenAI(model="gpt-4")
agent = create_react_agent(model, tools=[])

# Add custom metadata via RunnableConfig
result = agent.invoke(
    {"messages": [("user", "Hello!")]},
    {
        "metadata": {
            "serviceName": "customer-chatbot",
            "userId": "user_123",
            "environment": "production"
        }
    }
)
```

All metadata passed via RunnableConfig will be automatically extracted and stored in the TCC platform, allowing you to filter and analyze traces by your custom dimensions.

### LangGraph Example with Custom Metadata

```python
from tcc_otel import instrument_langchain
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool

# Initialize instrumentation
instrument_langchain()

# Define a simple tool
@tool
def get_weather(location: str) -> str:
    """Get weather for a location."""
    return f"The weather in {location} is sunny"

# Create agent
model = ChatOpenAI(model="gpt-4")
agent = create_react_agent(model, tools=[get_weather])

# Run agent with custom metadata via RunnableConfig
result = agent.invoke(
    {"messages": [("user", "What's the weather in NYC?")]},
    {
        "metadata": {
            "serviceName": "support-agent",
            "userId": "user_456",
            "tier": "premium"
        }
    }
)
```

## Requirements

Supports Python 3.9+

### Dependencies

- `opentelemetry-api>=1.29.0`
- `opentelemetry-sdk>=1.29.0`
- `opentelemetry-exporter-otlp>=1.29.0`

### LangChain Support
- `opentelemetry-instrumentation-langchain>=0.47.3`

## Troubleshooting

### Traces not appearing in TCC dashboard

1. **Check API key**: Ensure `TCC_API_KEY` is set correctly
2. **Instrumentation order**: Call `instrument_langchain()` BEFORE importing LangChain
3. **Network**: Ensure your application has internet connectivity

### Import errors

Make sure you've installed the framework-specific extras:

```bash
pip install tcc-otel[langchain]
```

### Custom metadata not showing up

- Ensure you're passing metadata via RunnableConfig as the second argument to `invoke()`
- Format: `agent.invoke(input, {"metadata": {"key": "value"}})`
- Metadata is stored in the `traceloop.entity.input` JSON structure
- Check the TCC dashboard's run details to verify metadata appears in the `run_metadata` table

## License

MIT License - see [LICENSE](LICENSE) for details.

## Resources

- Documentation: https://docs.thecontext.company
- Website: https://www.thecontext.company
- Contact: founders@thecontext.company

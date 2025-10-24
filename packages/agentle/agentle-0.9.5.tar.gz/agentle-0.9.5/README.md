<div align="center">
  <img src="/docs/logo.png" alt="Agentle Logo" width="200"/>
  
  <h3>✨ <em>Elegantly Simple AI Agents for Production</em> ✨</h3>
  
  <p>
    <strong>Build powerful AI agents with minimal code, maximum control</strong>
  </p>

  <p>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.13+-blue.svg" alt="Python 3.13+"></a>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License"></a>
    <a href="https://badge.fury.io/py/agentle"><img src="https://badge.fury.io/py/agentle.svg" alt="PyPI version"></a>
  </p>

  <p>
    <a href="#-quick-start">Quick Start</a> •
    <a href="#-why-agentle">Why Agentle</a> •
    <a href="#-features">Features</a> •
    <a href="#-showcase">Showcase</a> •
    <a href="#-documentation">Docs</a>
  </p>
</div>

---

## 🎯 Why Agentle?

<table>
<tr>
<td width="50%">

### 🚀 **Simple Yet Powerful**
```python
# Just 5 lines to create an AI agent
agent = Agent(
    name="Assistant",
    generation_provider=GoogleGenerationProvider(),
    model="gemini-2.5-flash",
    instructions="You are a helpful assistant."
)

response = agent.run("Agentle is cool.")
```

</td>
<td width="50%">

### 🏗️ **Production Ready**
- 🔍 **Built-in Observability** with Langfuse
- 🌐 **Instant APIs** with automatic documentation
- 💪 **Type-Safe** with full type hints
- 🎯 **Structured Outputs** with Pydantic
- 🔧 **Tool Calling** support out of the box
- 📦 **Minimum dependencies** you only install what you need

</td>
</tr>
</table>

## ⚡ Quick Start

### Installation

```bash
pip install agentle
```

### Your First Agent in 30 Seconds

```python
from agentle.agents.agent import Agent
from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider

# Create a simple agent
agent = Agent(
    name="Quick Start Agent",
    generation_provider=GoogleGenerationProvider(),
    model="gemini-2.5-flash",
    instructions="You are a helpful assistant who provides concise information."
)

# Run the agent
response = agent.run("What are the three laws of robotics?")
print(response.text)
```

## 🌟 Features

<div align="center">

| 🎨 **Beautiful UIs** | 🌐 **Instant APIs** | 📊 **Observability** | 🗄️ **Production Caching** |
|:---:|:---:|:---:|:---:|
| Create chat interfaces with Streamlit in minutes | Deploy RESTful APIs with automatic Scalar docs | Track everything with built-in Langfuse integration | Flexible caching with InMemory & Redis stores |
| ![Streamlit UI](https://github.com/user-attachments/assets/1c31da4c-aeb2-4ca6-88ac-62fb903d6d92) | ![API Docs](https://github.com/user-attachments/assets/d9d743cb-ad9c-41eb-a059-eda089efa6b6) | ![Tracing](https://github.com/user-attachments/assets/94937238-405c-4011-83e2-147cec5cf3e7) | Intelligent document caching for performance |

</div>

### 🔥 Core Capabilities

<details>
<summary><b>🗄️ Production-Ready Caching</b> - Intelligent document caching for performance and scalability</summary>

```python
from agentle.agents.agent import Agent
from agentle.agents.knowledge.static_knowledge import StaticKnowledge
from agentle.parsing.cache import InMemoryDocumentCacheStore, RedisCacheStore
from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider

# In-Memory Cache (Development & Single Process)
memory_cache = InMemoryDocumentCacheStore(cleanup_interval=300)

agent = Agent(
    name="Research Assistant",
    generation_provider=GoogleGenerationProvider(),
    model="gemini-2.5-flash",
    instructions="You analyze documents efficiently with caching.",
    static_knowledge=[
        StaticKnowledge(content="large_report.pdf", cache=3600),  # Cache for 1 hour
        StaticKnowledge(content="https://api.example.com/data", cache="infinite"),  # Cache indefinitely
    ],
    document_cache_store=memory_cache
)

# Redis Cache (Production & Distributed)
redis_cache = RedisCacheStore(
    redis_url="redis://localhost:6379/0",
    key_prefix="agentle:docs:",
    default_ttl=7200  # 2 hours default
)

production_agent = Agent(
    name="Production Assistant",
    generation_provider=GoogleGenerationProvider(),
    model="gemini-2.5-flash",
    instructions="You handle high-volume document processing.",
    static_knowledge=[
        StaticKnowledge(content="enterprise_docs.pdf", cache=86400),  # Cache for 1 day
    ],
    document_cache_store=redis_cache
)

# Cache Management
stats = memory_cache.get_stats()
print(f"Active cache entries: {stats['active_entries']}")

# Clear cache when needed
await memory_cache.clear_async()
```

**Benefits:**
- 🚀 **Performance**: Avoid re-parsing large documents
- 💰 **Cost Efficiency**: Reduce API calls for URL-based documents
- 📊 **Scalability**: Share cached documents across processes (Redis)
- 🔄 **Consistency**: Same parsed content across multiple runs
</details>

<details>
<summary><b>🤖 Intelligent Agents</b> - Build specialized agents with knowledge, tools, and structured outputs</summary>

```python
from agentle.agents.agent import Agent
from agentle.agents.knowledge.static_knowledge import StaticKnowledge
from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider
from pydantic import BaseModel
from typing import List

# Define structured output
class WeatherForecast(BaseModel):
    location: str
    current_temperature: float
    conditions: str
    forecast: List[str]

# Create a weather tool
def get_weather(location: str) -> str:
    """Get the current weather for a location."""
    weather_data = {
        "New York": "Sunny, 75°F",
        "London": "Rainy, 60°F",
        "Tokyo": "Cloudy, 65°F",
    }
    return weather_data.get(location, f"Weather data not available for {location}")

# Build the agent
weather_agent = Agent(
    name="Weather Assistant",
    generation_provider=GoogleGenerationProvider(),
    model="gemini-2.5-flash",
    instructions="You are a weather forecasting assistant.",
    # Add domain knowledge
    static_knowledge=[
        StaticKnowledge(content="weather_data/climate_patterns.pdf", cache=3600),
        "A heat wave is defined as a period of abnormally hot weather generally lasting more than two days."
    ],
    # Add tools
    tools=[get_weather],
    # Ensure structured responses
    response_schema=WeatherForecast
)

# Get typed responses
response = weather_agent.run("What's the weather like in Tokyo?")
forecast = response.parsed
print(f"Weather in {forecast.location}: {forecast.current_temperature}°C, {forecast.conditions}")
```
</details>

<details>
<summary><b>🔗 Agent Pipelines</b> - Chain agents for complex workflows</summary>

```python
from agentle.agents.agent import Agent
from agentle.agents.agent_pipeline import AgentPipeline
from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider

# Create provider for reuse
provider = GoogleGenerationProvider()

# Create specialized agents
research_agent = Agent(
    name="Research Agent",
    generation_provider=provider,
    model="gemini-2.5-flash",
    instructions="""You are a research agent focused on gathering information.
    Be thorough and prioritize accuracy over speculation."""
)

analysis_agent = Agent(
    name="Analysis Agent",
    generation_provider=provider,
    model="gemini-2.5-flash",
    instructions="""You are an analysis agent that identifies patterns.
    Highlight meaningful relationships and insights from the data."""
)

summary_agent = Agent(
    name="Summary Agent",
    generation_provider=provider,
    model="gemini-2.5-flash",
    instructions="""You are a summary agent that creates concise summaries.
    Present key findings in a logical order with accessible language."""
)

# Create a pipeline
pipeline = AgentPipeline(
    agents=[research_agent, analysis_agent, summary_agent],
    debug_mode=True  # Enable to see intermediate steps
)

# Run the pipeline
result = pipeline.run("Research the impact of artificial intelligence on healthcare")
print(result.text)
```
</details>

<details>
<summary><b>👥 Agent Teams</b> - Dynamic orchestration with intelligent routing</summary>

```python
from agentle.agents.agent import Agent
from agentle.agents.agent_team import AgentTeam
from agentle.agents.a2a.models.agent_skill import AgentSkill
from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider

# Create provider for reuse
provider = GoogleGenerationProvider()

# Create specialized agents with different skills
research_agent = Agent(
    name="Research Agent",
    description="Specialized in finding accurate information on various topics",
    generation_provider=provider,
    model="gemini-2.5-flash",
    instructions="You are a research agent focused on gathering accurate information.",
    skills=[
        AgentSkill(name="search", description="Find information on any topic"),
        AgentSkill(name="fact-check", description="Verify factual claims"),
    ],
)

coding_agent = Agent(
    name="Coding Agent",
    description="Specialized in writing and debugging code",
    generation_provider=provider,
    model="gemini-2.5-flash",
    instructions="You are a coding expert focused on writing clean, efficient code.",
    skills=[
        AgentSkill(name="code-generation", description="Write code in various languages"),
        AgentSkill(name="debugging", description="Find and fix bugs in code"),
    ],
)

# Create a team with these agents
team = AgentTeam(
    agents=[research_agent, coding_agent],
    orchestrator_provider=provider,
    orchestrator_model="gemini-2.5-flash",
)

# Run the team with different queries
research_query = "What are the main challenges in quantum computing today?"
research_result = team.run(research_query)

coding_query = "Write a Python function to find the Fibonacci sequence up to n terms."
coding_result = team.run(coding_query)
```
</details>

<details>
<summary><b>🔌 MCP Integration</b> - Connect to external tools via Model Context Protocol</summary>

```python
from agentle.agents.agent import Agent
from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider
from agentle.mcp.servers.streamable_http_mcp_server import StreamableHTTPMCPServer
from agentle.mcp.servers.stdio_mcp_server import StdioMCPServer
from agentle.mcp.session_management import RedisSessionManager

# Set up provider
provider = GoogleGenerationProvider()

# Create MCP servers
stdio_server = StdioMCPServer(
    server_name="File System MCP",
    command="/path/to/filesystem_mcp_server",  # Replace with actual command
    server_env={"DEBUG": "1"},
)

# For development (single-process environments)
sse_server_dev = StreamableHTTPMCPServer(
    server_name="Weather API MCP",
    server_url="http://localhost:3000",  # Replace with actual server URL
)

# For production (multi-process environments)
redis_session = RedisSessionManager(
    redis_url="redis://redis-server:6379/0",
    key_prefix="agentle_mcp:",
    expiration_seconds=3600  # 1 hour session lifetime
)

sse_server_prod = StreamableHTTPMCPServer(
    server_name="Weather API MCP",
    server_url="https://api.example.com",
    session_manager=redis_session
)

# Create agent with MCP servers
agent = Agent(
    name="MCP-Augmented Assistant",
    description="An assistant that can access external tools via MCP",
    generation_provider=provider,
    model="gemini-2.5-flash",
    instructions="You are a helpful assistant with access to external tools.",
    mcp_servers=[stdio_server, sse_server_dev],
)

# Use the start_mcp_servers context manager for proper connection handling
with agent.start_mcp_servers():
    # Query that uses MCP server tools
    response = agent.run("What's the weather like in Tokyo today?")
    print(response.generation.text)
```
</details>

## 🖼️ Visual Showcase

### 🎨 Build Beautiful Chat UIs

Transform your agent into a professional chat interface with just a few lines:

```python
from agentle.agents.agent import Agent
from agentle.agents.ui.streamlit import AgentToStreamlit
from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider

# Create your agent
travel_agent = Agent(
    name="Travel Guide",
    description="A helpful travel guide that answers questions about destinations.",
    generation_provider=GoogleGenerationProvider(),
    model="gemini-2.5-flash",
    instructions="""You are a knowledgeable travel guide who helps users plan trips.""",
)

# Convert the agent to a Streamlit app
streamlit_app = AgentToStreamlit(
    title="Travel Assistant",
    description="Ask me anything about travel destinations and planning!",
    initial_mode="presentation",  # Can be "dev" or "presentation"
).adapt(travel_agent)

# Run the Streamlit app
if __name__ == "__main__":
    streamlit_app()
```

<img width="100%" alt="Streamlit Chat Interface" src="https://github.com/user-attachments/assets/1c31da4c-aeb2-4ca6-88ac-62fb903d6d92" />

### 🌐 Deploy Production APIs

Expose your agents, teams, and pipelines as RESTful APIs with automatic documentation:

<details>
<summary><b>🤖 Single Agent API</b> - Deploy individual agents as REST services</summary>

```python
from agentle.agents.agent import Agent
from agentle.agents.asgi.blacksheep.agent_to_blacksheep_application_adapter import AgentToBlackSheepApplicationAdapter
from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider

# Create your agent
code_assistant = Agent(
    name="Code Assistant",
    description="An AI assistant specialized in helping with programming tasks.",
    generation_provider=GoogleGenerationProvider(),
    model="gemini-2.5-flash",
    instructions="""You are a helpful programming assistant.
    You can answer questions about programming languages, help debug code,
    explain programming concepts, and provide code examples.""",
)

# Convert the agent to a BlackSheep ASGI application
app = AgentToBlackSheepApplicationAdapter().adapt(code_assistant)

# Run the API server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

**Generated API Endpoints:**
- `POST /api/v1/agents/code_assistant/run` - Execute the agent
- `POST /api/v1/agents/code_assistant/run/resume` - Resume suspended executions (HITL)
- `GET /docs` - Interactive API documentation
- `GET /openapi` - OpenAPI specification

</details>

<details>
<summary><b>👥 Agent Team API</b> - Deploy dynamic teams with intelligent orchestration</summary>

```python
from agentle.agents.agent import Agent
from agentle.agents.agent_team import AgentTeam
from agentle.agents.asgi.blacksheep.agent_to_blacksheep_application_adapter import AgentToBlackSheepApplicationAdapter
from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider

provider = GoogleGenerationProvider()

# Create specialized agents
research_agent = Agent(
    name="Research Agent",
    description="Specialized in finding and analyzing information",
    generation_provider=provider,
    model="gemini-2.5-flash",
    instructions="You are a research expert focused on gathering accurate information.",
)

coding_agent = Agent(
    name="Coding Agent", 
    description="Specialized in writing and debugging code",
    generation_provider=provider,
    model="gemini-2.5-flash",
    instructions="You are a coding expert that writes clean, efficient code.",
)

writing_agent = Agent(
    name="Writing Agent",
    description="Specialized in creating clear and engaging content",
    generation_provider=provider,
    model="gemini-2.5-flash", 
    instructions="You are a writing expert that creates compelling content.",
)

# Create a team with intelligent orchestration
team = AgentTeam(
    agents=[research_agent, coding_agent, writing_agent],
    orchestrator_provider=provider,
    orchestrator_model="gemini-2.5-flash"
)

# Deploy the team as an API
app = AgentToBlackSheepApplicationAdapter().adapt(team)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

**Generated API Endpoints:**
- `POST /api/v1/team/run` - Execute task with dynamic agent selection
- `POST /api/v1/team/resume` - Resume suspended team executions
- `GET /docs` - Interactive documentation with team composition details

</details>

<details>
<summary><b>🔗 Agent Pipeline API</b> - Deploy sequential processing workflows</summary>

```python
from agentle.agents.agent import Agent
from agentle.agents.agent_pipeline import AgentPipeline
from agentle.agents.asgi.blacksheep.agent_to_blacksheep_application_adapter import AgentToBlackSheepApplicationAdapter
from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider

provider = GoogleGenerationProvider()

# Create pipeline stages
data_processor = Agent(
    name="Data Processor",
    generation_provider=provider,
    model="gemini-2.5-flash",
    instructions="You process and clean raw data, handling missing values and formatting.",
)

analyzer = Agent(
    name="Data Analyzer", 
    generation_provider=provider,
    model="gemini-2.5-flash",
    instructions="You perform statistical analysis and identify patterns in processed data.",
)

reporter = Agent(
    name="Report Generator",
    generation_provider=provider,
    model="gemini-2.5-flash",
    instructions="You create comprehensive reports with insights and visualizations.",
)

# Create a sequential pipeline
pipeline = AgentPipeline(
    agents=[data_processor, analyzer, reporter],
    debug_mode=True  # Enable detailed logging
)

# Deploy the pipeline as an API
app = AgentToBlackSheepApplicationAdapter().adapt(pipeline)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

**Generated API Endpoints:**
- `POST /api/v1/pipeline/run` - Execute sequential pipeline processing
- `POST /api/v1/pipeline/resume` - Resume suspended pipeline executions
- `GET /docs` - Interactive documentation with pipeline stage details

</details>

<details>
<summary><b>🔄 HITL-Enabled APIs</b> - Production APIs with human approval workflows</summary>

All API types (Agent, Team, Pipeline) automatically support Human-in-the-Loop workflows:

```python
from agentle.agents.errors.tool_suspension_error import ToolSuspensionError

def sensitive_operation(amount: float, account: str) -> str:
    """A tool that requires human approval for large amounts."""
    if amount > 10000:
        raise ToolSuspensionError(
            reason=f"Transfer of ${amount} requires approval",
            approval_data={"amount": amount, "account": account},
            timeout_seconds=3600  # 1 hour timeout
        )
    return f"Transfer completed: ${amount} to {account}"

# Any agent with HITL tools will automatically expose resume endpoints
agent_with_hitl = Agent(
    name="Financial Agent",
    tools=[sensitive_operation],
    generation_provider=GoogleGenerationProvider(),
    model="gemini-2.5-flash",
    instructions="You handle financial operations with human oversight.",
)

app = AgentToBlackSheepApplicationAdapter().adapt(agent_with_hitl)
```

**HITL API Flow:**
1. `POST /api/v1/agents/financial_agent/run` - Returns 202 with `resumption_token` if suspended
2. Human approves via external system (web UI, mobile app, etc.)
3. `POST /api/v1/agents/financial_agent/run/resume` - Continues execution with approval data

</details>

**🎯 Key API Features:**
- **📚 Automatic Documentation**: Interactive Scalar UI with detailed endpoint descriptions
- **🔄 HITL Support**: Built-in suspension/resumption for human approval workflows  
- **📊 Structured Responses**: Consistent `AgentRunOutput` format across all endpoints
- **⚡ Async Processing**: Non-blocking execution with proper error handling
- **🔍 Type Safety**: Full OpenAPI schema generation with request/response validation
- **🏗️ Production Ready**: Built on BlackSheep ASGI for high-performance deployment

<img width="100%" alt="API Documentation" src="https://github.com/user-attachments/assets/d9d743cb-ad9c-41eb-a059-eda089efa6b6" />

### 📊 Enterprise-Grade Observability

Monitor every aspect of your agents in production:

```python
from agentle.generations.tracing.langfuse_otel_client import LangfuseOtelClient
from agentle.agents.agent import Agent
from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider

# Create a tracing client
tracing_client = LangfuseOtelClient()

# Create an agent with tracing enabled
agent = Agent(
    name="Traceable Agent",
    generation_provider=GoogleGenerationProvider(otel_clients=tracing_client),
    model="gemini-2.5-flash",
    instructions="You are a helpful assistant.",
    # Tracing is automatically enabled
)

# Run the agent - tracing happens automatically
response = agent.run(
    "What's the weather in Tokyo?", 
    trace_params={
        "name": "weather_query",
        "user_id": "user123",
        "metadata": {"source": "mobile_app"}
    }
)
```

<img width="100%" alt="Observability Dashboard" src="https://github.com/user-attachments/assets/94937238-405c-4011-83e2-147cec5cf3e7" />

<img width="100%" alt="Detailed Trace View" src="https://github.com/user-attachments/assets/c38429db-982c-4158-864f-f03e7118618e" />

**Automatic Scoring System** tracks:
- 🎯 **Model Tier Score** - Evaluates the capability tier of the model used
- 🔧 **Tool Usage Score** - Measures how effectively the agent uses available tools  
- 💰 **Token Efficiency Score** - Analyzes the balance between input and output tokens
- ⚡ **Cost Efficiency Score** - Tracks the cost-effectiveness of each generation

<img width="100%" alt="Trace Scores" src="https://github.com/user-attachments/assets/f0aab337-ead3-417b-97ef-0126c833d347" />


# WhatsApp Integration Guide (experimental, EvolutionAPI only)

This guide explains how to use Agentle's WhatsApp integration to build production-ready WhatsApp bots with Evolution API.

## Overview

Agentle's WhatsApp integration provides:

- **🚀 Easy Setup**: Simple configuration with Evolution API
- **📦 Session Management**: Production-ready session storage with Redis support
- **🔧 Flexible Architecture**: Pluggable providers for different WhatsApp APIs
- **📊 Built-in Observability**: Logging, error handling, and monitoring
- **🌐 Instant APIs**: Convert bots to REST APIs with automatic documentation
- **🛡️ Production Ready**: Error handling, retries, and graceful degradation

## Quick Start

### 1. Set Up Evolution API

1. Install and run Evolution API server
2. Create an instance in Evolution API
3. Get your API key and instance name

### 2. Basic Bot Example

```python
import asyncio
from agentle.agents.agent import Agent
from agentle.agents.whatsapp.whatsapp_bot import WhatsAppBot
from agentle.agents.whatsapp.providers.evolution.evolution_api_provider import EvolutionAPIProvider
from agentle.agents.whatsapp.providers.evolution.evolution_api_config import EvolutionAPIConfig
from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider

# Create agent
agent = Agent(
    name="My WhatsApp Bot",
    generation_provider=GoogleGenerationProvider(),
    model="gemini-2.5-flash",
    instructions="You are a helpful assistant."
)

# Configure Evolution API
config = EvolutionAPIConfig(
    base_url="http://localhost:8080",
    instance_name="my-bot",
    api_key="your-api-key"
)

# Create provider and bot
provider = EvolutionAPIProvider(config)
bot = WhatsAppBot(agent, provider)

# Run a sync service (async version also available)
bot.start()
```

## Session Management

### In-Memory Sessions (Development)

```python
from agentle.sessions.in_memory_session_store import InMemorySessionStore
from agentle.sessions.session_manager import SessionManager

# Create session store
session_store = InMemorySessionStore[WhatsAppSession](
    cleanup_interval_seconds=300  # Cleanup every 5 minutes
)

# Create session manager
session_manager = SessionManager[WhatsAppSession](
    session_store=session_store,
    default_ttl_seconds=1800,  # 30 minutes
    enable_events=True
)

# Use with provider
provider = EvolutionAPIProvider(
    config=evolution_config,
    session_manager=session_manager
)
```

### Redis Sessions (Production)

```python
from agentle.sessions.redis_session_store import RedisSessionStore

# Create Redis session store
session_store = RedisSessionStore[WhatsAppSession](
    redis_url="redis://localhost:6379/0",
    key_prefix="whatsapp:sessions:",
    default_ttl_seconds=3600,  # 1 hour
    session_class=WhatsAppSession
)

# Create session manager
session_manager = SessionManager[WhatsAppSession](
    session_store=session_store,
    default_ttl_seconds=3600,
    enable_events=True
)

# Use with provider
provider = EvolutionAPIProvider(
    config=evolution_config,
    session_manager=session_manager
)
```

### Session Events

```python
# Add event handlers
async def on_session_created(session_id: str, session_data: Any) -> None:
    print(f"New session: {session_id}")

async def on_session_deleted(session_id: str, session_data: Any) -> None:
    print(f"Session deleted: {session_id}")

session_manager.add_event_handler("session_created", on_session_created)
session_manager.add_event_handler("session_deleted", on_session_deleted)
```

## Bot Configuration

```python
from agentle.agents.whatsapp.models.whatsapp_bot_config import WhatsAppBotConfig

bot_config = WhatsAppBotConfig(
    typing_indicator=True,
    typing_duration=3,
    auto_read_messages=True,
    session_timeout_minutes=30,
    max_message_length=4000,
    welcome_message="Hello! How can I help you?",
    error_message="Sorry, something went wrong. Please try again.",
)

bot = WhatsAppBot(agent, provider, config=bot_config)
```

## Adding Tools

```python
def get_weather(location: str) -> str:
    """Get weather information for a location."""
    # Your weather API implementation
    return f"Weather in {location}: Sunny, 25°C"

def book_appointment(date: str, time: str) -> str:
    """Book an appointment."""
    # Your booking system implementation
    return f"Appointment booked for {date} at {time}"

# Create agent with tools
agent = Agent(
    name="Assistant Bot",
    generation_provider=GoogleGenerationProvider(),
    model="gemini-2.5-flash",
    instructions="""You are a helpful assistant that can:
    - Provide weather information
    - Book appointments
    Always be friendly and helpful.""",
    tools=[get_weather, book_appointment]
)
```

## REST API Deployment

### Simple API Server

```python
# Convert bot to BlackSheep application
app = bot.to_blacksheep_app(
    webhook_path="/webhook/whatsapp",
    show_error_details=False  # Set to True for development
)

# Run with uvicorn
# DOCUMENTATION AUTOMATICALLY AVAILABLE AT localhost:8000/docs
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Production API with Custom Configuration

```python
from blacksheep import Application
from blacksheep.server.openapi.v3 import OpenAPIHandler
from openapidocs.v3 import Info

# Create custom OpenAPI documentation
docs = OpenAPIHandler(
    ui_path="/api/docs",
    info=Info(
        title="My WhatsApp Bot API",
        version="1.0.0",
        description="Production WhatsApp bot with AI capabilities"
    )
)

# Convert bot to application
app = bot.to_blacksheep_app(
    webhook_path="/webhooks/whatsapp",
    docs=docs,
    show_error_details=False
)

# Add custom middleware, CORS, etc.
# app.use_cors()
# app.use_authentication()

# Deploy
uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Environment Configuration

### Environment Variables

```bash
# Evolution API Configuration
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_INSTANCE_NAME=my-bot
EVOLUTION_API_KEY=your-api-key

# Session Storage
REDIS_URL=redis://localhost:6379/0

# Bot Configuration
BOT_MODE=production  # simple, development, production
WEBHOOK_URL=https://your-domain.com/webhook/whatsapp
PORT=8000
DEBUG=false

# AI Provider
GOOGLE_API_KEY=your-google-api-key
```

### Configuration Class

```python
import os
from dataclasses import dataclass

@dataclass
class WhatsAppBotSettings:
    # Evolution API
    evolution_url: str = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
    evolution_instance: str = os.getenv("EVOLUTION_INSTANCE_NAME", "my-bot")
    evolution_api_key: str = os.getenv("EVOLUTION_API_KEY", "")
    
    # Session storage
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    session_ttl: int = int(os.getenv("SESSION_TTL", "3600"))
    
    # Bot behavior
    webhook_url: str = os.getenv("WEBHOOK_URL", "")
    typing_duration: int = int(os.getenv("TYPING_DURATION", "3"))
    auto_read: bool = os.getenv("AUTO_READ_MESSAGES", "true").lower() == "true"
    
    # Server
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

# Use configuration
settings = WhatsAppBotSettings()

evolution_config = EvolutionAPIConfig(
    base_url=settings.evolution_url,
    instance_name=settings.evolution_instance,
    api_key=settings.evolution_api_key
)
```

## Error Handling and Monitoring

### Custom Error Handling

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add custom webhook handlers
async def on_webhook_error(payload, error):
    logging.error(f"Webhook error: {error}")
    # Send to monitoring system
    
bot.add_webhook_handler(on_webhook_error)
```

### Health Checks

```python
# Add health check endpoint with blacksheep!
@app.router.post("/health")
async def health_check():
    stats = provider.get_stats()
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "stats": stats
    }
```

### Monitoring Stats

```python
# Get provider statistics
provider_stats = provider.get_stats()
print(f"Instance: {provider_stats['instance_name']}")
print(f"Active sessions: {provider_stats['session_stats']['store_stats']['total_sessions']}")

# Get session manager statistics
session_stats = session_manager.get_stats()
print(f"Session events enabled: {session_stats['events_enabled']}")
print(f"Default TTL: {session_stats['default_ttl_seconds']}s")
```

## Advanced Features

### Message Filtering

```python
class CustomWhatsAppBot(WhatsAppBot):
    async def handle_message(self, message: WhatsAppMessage) -> None:
        # Filter spam or unwanted messages
        if self.is_spam(message):
            return
        
        # Add custom preprocessing
        processed_message = self.preprocess_message(message)
        
        # Call parent handler
        await super().handle_message(processed_message)
    
    def is_spam(self, message: WhatsAppMessage) -> bool:
        # Your spam detection logic here...
        return False
    
    def preprocess_message(self, message: WhatsAppMessage) -> WhatsAppMessage:
        # Your preprocessing logic here...
        return message
```

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "whatsapp_bot_example.py", "production"]
```

### Docker Compose with Redis

```yaml
version: '3.8'

services:
  whatsapp-bot:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - EVOLUTION_API_URL=http://evolution:8080
      - BOT_MODE=production
    depends_on:
      - redis
      - evolution
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    
  evolution:
    image: atendai/evolution-api:latest
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/evolution
    depends_on:
      - postgres
    
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=evolution
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  redis_data:
  postgres_data:
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: whatsapp-bot
spec:
  replicas: 3
  selector:
    matchLabels:
      app: whatsapp-bot
  template:
    metadata:
      labels:
        app: whatsapp-bot
    spec:
      containers:
      - name: whatsapp-bot
        image: your-registry/whatsapp-bot:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379/0"
        - name: EVOLUTION_API_URL
          value: "http://evolution-service:8080"
        - name: BOT_MODE
          value: "production"
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "256Mi"
            cpu: "250m"
---
apiVersion: v1
kind: Service
metadata:
  name: whatsapp-bot-service
spec:
  selector:
    app: whatsapp-bot
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Best Practices

### 1. Security

- Use environment variables for sensitive configuration
- Implement webhook verification
- Rate limit API endpoints
- Use HTTPS in production
- Rotate API keys regularly

### 2. Performance

- Use Redis for session storage in production
- Implement proper caching strategies
- Monitor memory usage with session cleanup
- Use connection pooling for databases
- Implement graceful shutdowns

### 3. Reliability

- Implement retry logic for failed operations
- Use circuit breakers for external services
- Monitor webhook delivery
- Set up proper logging and alerting
- Implement health checks

### 4. Scalability

- Use horizontal scaling with load balancers
- Implement sticky sessions if needed
- Use distributed session storage (Redis)
- Monitor and tune session TTLs
- Implement proper resource limits

## Troubleshooting

### Common Issues

1. **Connection Errors**
   ```bash
   # Check Evolution API status
   curl http://localhost:8080/instance/fetchInstances
   
   # Check Redis connection
   redis-cli ping
   ```

2. **Session Issues**
   ```python
   # Check session statistics
   stats = session_manager.get_stats()
   print(f"Active sessions: {stats}")
   
   # List active sessions
   sessions = await session_manager.list_sessions()
   print(f"Session IDs: {sessions}")
   ```

3. **Webhook Problems**
   ```python
   # Verify webhook URL
   webhook_url = provider.get_webhook_url()
   print(f"Current webhook: {webhook_url}")
   
   # Re-register webhook
   await provider.set_webhook_url("https://your-domain.com/webhook")
   ```

### Debug Mode

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable agent debugging
agent = Agent(
    # ... other params ...
    debug=True
)

# Create development server with error details
app = bot.to_blacksheep_app(show_error_details=True)
```

### Monitoring

```python
# Add monitoring endpoints
@app.router.post("/metrics")
async def metrics():
    return {
        "provider_stats": provider.get_stats(),
        "session_stats": session_manager.get_stats(),
        "timestamp": datetime.now().isoformat()
    }

@app.router.post("/sessions")
async def list_sessions():
    sessions = await session_manager.list_sessions(include_metadata=True)
    return {"sessions": sessions}
```

## 🏗️ Real-World Examples

### 💬 Customer Support Agent

```python
from agentle.agents.agent import Agent
from agentle.agents.asgi.blacksheep.agent_to_blacksheep_application_adapter import AgentToBlackSheepApplicationAdapter
from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider

# Define support tools
def search_knowledge_base(query: str) -> str:
    """Search the support knowledge base."""
    # Implementation would search your KB
    return "Found solution: Reset password via email link"

def create_ticket(issue: str, priority: str = "medium") -> str:
    """Create a support ticket."""
    # Implementation would create ticket in your system
    return f"Ticket created with ID: SUPP-12345"

# Create support agent
support_agent = Agent(
    name="Support Hero",
    generation_provider=GoogleGenerationProvider(),
    model="gemini-2.5-flash",
    instructions="You are an empathetic customer support specialist.",
    tools=[search_knowledge_base, create_ticket],
    static_knowledge=["support_policies.pdf", "faq.md"]
)

# Deploy as API
api = AgentToBlackSheepApplicationAdapter().adapt(support_agent)
```

### 📊 Data Analysis Pipeline

```python
from agentle.agents.agent import Agent
from agentle.agents.agent_pipeline import AgentPipeline
from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider

provider = GoogleGenerationProvider()

# Create specialized agents
data_cleaner = Agent(
    name="Data Cleaner",
    generation_provider=provider,
    model="gemini-2.5-flash",
    instructions="You clean and preprocess data, handling missing values and outliers."
)

statistician = Agent(
    name="Statistician",
    generation_provider=provider,
    model="gemini-2.5-flash",
    instructions="You perform statistical analysis and identify significant patterns."
)

visualizer = Agent(
    name="Visualizer",
    generation_provider=provider,
    model="gemini-2.5-flash",
    instructions="You create clear descriptions of data visualizations and insights."
)

# Build analysis pipeline
analysis_pipeline = AgentPipeline(
    agents=[data_cleaner, statistician, visualizer]
)

# Process data
result = analysis_pipeline.run("Analyze this sales data: Q1: $1.2M, Q2: $1.5M, Q3: $1.1M, Q4: $2.1M")
```

### 🌍 Multi-Provider Resilience

```python
from agentle.agents.agent import Agent
from agentle.generations.providers.failover.failover_generation_provider import FailoverGenerationProvider
from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider
from agentle.generations.providers.openai.openai import OpenaiGenerationProvider
from agentle.generations.providers.cerebras.cerebras_generation_provider import CerebrasGenerationProvider

# Never go down - automatically failover between providers
resilient_provider = FailoverGenerationProvider(
    generation_providers=[
        GoogleGenerationProvider(),
        OpenaiGenerationProvider(api_key="your-openai-key"),
        CerebrasGenerationProvider(api_key="your-cerebras-key")
    ],
    shuffle=True
)

agent = Agent(
    name="Resilient Assistant",
    generation_provider=resilient_provider,
    # Use ModelKind instead of specific model names for better compatibility
    model="category_pro",  # Each provider maps this to their equivalent model
    instructions="You are a helpful assistant."
)
```

#### 🧠 Using ModelKind for Provider Abstraction

Agentle provides a powerful abstraction layer with `ModelKind` that decouples your code from specific provider model names:

```python
# Instead of hardcoding provider-specific model names:
agent = Agent(generation_provider=provider, model="gpt-4o")  # Only works with OpenAI

# Use ModelKind for provider-agnostic code:
agent = Agent(generation_provider=provider, model="category_pro")  # Works with any provider
```

**Benefits of ModelKind:**

- **Provider independence**: Write code that works with any AI provider
- **Future-proof**: When providers release new models, only mapping tables need updates
- **Capability-based selection**: Choose models based on capabilities, not names
- **Perfect for failover**: Each provider automatically maps to its equivalent model
- **Consistency**: Standardized categories across all providers

Each provider implements `map_model_kind_to_provider_model()` to translate these abstract categories to their specific models (e.g., "category_pro" → "gpt-4o" for OpenAI or "gemini-2.5-pro" for Google).

## 🛠️ Advanced Features

### 🤝 Human-in-the-Loop (HITL) Integration

Agentle provides enterprise-grade support for Human-in-the-Loop workflows, where human oversight and approval are integrated into AI agent execution. This is crucial for production systems that require human judgment for critical decisions, compliance, or safety.

The framework supports multiple storage backends for different deployment scenarios, with proper dependency injection for maximum flexibility and robustness.

#### 🔄 Tool-Level Human Approval

Use `before_call` and `after_call` callbacks to implement approval workflows:

```python
import asyncio
from datetime import datetime
from agentle.agents.agent import Agent
from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider
from agentle.generations.tools.tool import Tool

# Simulated approval system (in production, this would be a database/queue)
pending_approvals = {}
approval_results = {}

async def request_human_approval(tool_name: str, **kwargs) -> bool:
    """Request human approval before executing a sensitive tool."""
    approval_id = f"approval_{datetime.now().timestamp()}"
    
    # Store the pending approval
    pending_approvals[approval_id] = {
        "tool_name": tool_name,
        "arguments": kwargs,
        "timestamp": datetime.now(),
        "status": "pending"
    }
    
    print(f"🔔 Human approval requested for {tool_name}")
    print(f"   Approval ID: {approval_id}")
    print(f"   Arguments: {kwargs}")
    print(f"   Waiting for approval...")
    
    # In a real system, this would:
    # 1. Send notification to human operator
    # 2. Store request in database
    # 3. Return immediately, resuming later when approved
    
    # For demo: simulate waiting for approval
    while approval_id not in approval_results:
        await asyncio.sleep(1)  # Check every second
    
    approved = approval_results[approval_id]
    print(f"✅ Approval {approval_id}: {'APPROVED' if approved else 'DENIED'}")
    return approved

def log_tool_execution(tool_name: str, result: any, **kwargs):
    """Log tool execution for audit trail."""
    print(f"📝 Tool executed: {tool_name}")
    print(f"   Result: {str(result)[:100]}...")
    print(f"   Timestamp: {datetime.now()}")

# Define a sensitive tool that requires approval
def transfer_funds(from_account: str, to_account: str, amount: float) -> str:
    """Transfer funds between accounts - requires human approval."""
    return f"Transferred ${amount} from {from_account} to {to_account}"

def send_email(to: str, subject: str, body: str) -> str:
    """Send an email - requires human approval."""
    return f"Email sent to {to} with subject '{subject}'"

# Create tools with HITL callbacks
transfer_tool = Tool.from_callable(
    transfer_funds,
    before_call=lambda **kwargs: asyncio.create_task(
        request_human_approval("transfer_funds", **kwargs)
    ),
    after_call=lambda result, **kwargs: log_tool_execution(
        "transfer_funds", result, **kwargs
    )
)

email_tool = Tool.from_callable(
    send_email,
    before_call=lambda **kwargs: asyncio.create_task(
        request_human_approval("send_email", **kwargs)
    ),
    after_call=lambda result, **kwargs: log_tool_execution(
        "send_email", result, **kwargs
    )
)

# Create agent with HITL-enabled tools
financial_agent = Agent(
    name="Financial Assistant",
    generation_provider=GoogleGenerationProvider(),
    model="gemini-2.5-flash",
    instructions="""You are a financial assistant that can transfer funds and send notifications.
    Always confirm the details before executing any financial operations.""",
    tools=[transfer_tool, email_tool]
)

# Simulate the approval process
async def simulate_human_operator():
    """Simulate a human operator approving/denying requests."""
    await asyncio.sleep(2)  # Simulate human response time
    
    # In a real system, this would be a web interface or mobile app
    for approval_id in list(pending_approvals.keys()):
        if approval_id not in approval_results:
            # Simulate human decision (in real system, this comes from UI)
            approval_results[approval_id] = True  # Approve the request
            print(f"👤 Human operator approved: {approval_id}")

async def main():
    # Start the human operator simulation
    operator_task = asyncio.create_task(simulate_human_operator())
    
    # Run the agent (this will pause and wait for human approval)
    response = await financial_agent.run_async(
        "Transfer $1000 from account A123 to account B456 and send a confirmation email to user@example.com"
    )
    
    print(f"\n🎯 Final response: {response.text}")
    
    await operator_task

# Run the example
# asyncio.run(main())
```

#### 🏭 Production HITL Workflow

Here's a real-world example of an asynchronous HITL system where users can submit tasks, go about their day, and approve actions later:

```python
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

from agentle.agents.agent import Agent
from agentle.agents.context import Context
from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"

@dataclass
class ApprovalRequest:
    id: str
    user_id: str
    tool_name: str
    arguments: Dict
    context_id: str
    created_at: datetime
    expires_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

class HITLApprovalSystem:
    """Production-ready Human-in-the-Loop approval system."""
    
    def __init__(self):
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.contexts: Dict[str, Context] = {}
    
    async def request_approval(
        self, 
        user_id: str, 
        tool_name: str, 
        context: Context,
        **kwargs
    ) -> str:
        """Request human approval and pause agent execution."""
        approval_id = str(uuid.uuid4())
        
        # Store the approval request
        request = ApprovalRequest(
            id=approval_id,
            user_id=user_id,
            tool_name=tool_name,
            arguments=kwargs,
            context_id=context.context_id,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=7)  # 7-day expiry
        )
        
        self.pending_requests[approval_id] = request
        self.contexts[context.context_id] = context
        
        # Pause the context for human approval
        context.pause_execution(f"Waiting for approval: {tool_name}")
        context.set_checkpoint_data("approval_id", approval_id)
        context.set_checkpoint_data("pending_tool", tool_name)
        context.set_checkpoint_data("pending_args", kwargs)
        
        # In production: send notification (email, Slack, mobile push, etc.)
        await self._send_approval_notification(request)
        
        print(f"🔔 Approval requested: {approval_id}")
        print(f"   Tool: {tool_name}")
        print(f"   User: {user_id}")
        print(f"   Context paused until approval")
        
        return approval_id
    
    async def approve_request(self, approval_id: str, approver_id: str) -> bool:
        """Approve a pending request and resume agent execution."""
        if approval_id not in self.pending_requests:
            return False
        
        request = self.pending_requests[approval_id]
        if request.status != ApprovalStatus.PENDING:
            return False
        
        # Mark as approved
        request.status = ApprovalStatus.APPROVED
        request.approved_by = approver_id
        request.approved_at = datetime.now()
        
        # Resume the context
        context = self.contexts[request.context_id]
        context.resume_execution()
        
        print(f"✅ Request approved: {approval_id}")
        print(f"   Approved by: {approver_id}")
        print(f"   Context resumed: {context.context_id}")
        
        # In production: continue agent execution
        await self._resume_agent_execution(request, context)
        
        return True
    
    async def deny_request(self, approval_id: str, approver_id: str, reason: str = "") -> bool:
        """Deny a pending request."""
        if approval_id not in self.pending_requests:
            return False
        
        request = self.pending_requests[approval_id]
        request.status = ApprovalStatus.DENIED
        request.approved_by = approver_id
        request.approved_at = datetime.now()
        
        # Mark context as failed
        context = self.contexts[request.context_id]
        context.fail_execution(f"Request denied: {reason}")
        
        print(f"❌ Request denied: {approval_id}")
        print(f"   Reason: {reason}")
        
        return True
    
    async def _send_approval_notification(self, request: ApprovalRequest):
        """Send notification to user about pending approval."""
        # In production: integrate with notification systems
        print(f"📧 Notification sent to user {request.user_id}")
        print(f"   'Action required: Approve {request.tool_name} operation'")
    
    async def _resume_agent_execution(self, request: ApprovalRequest, context: Context):
        """Resume agent execution after approval."""
        # In production: this would trigger the agent to continue
        print(f"🔄 Resuming agent execution for context {context.context_id}")
        
        # Execute the approved tool
        tool_name = request.tool_name
        args = request.arguments
        print(f"   Executing: {tool_name}({args})")
        
        # Continue with the agent workflow...

# Example usage in a web API
hitl_system = HITLApprovalSystem()

def create_hitl_tool(tool_func, user_id: str):
    """Create a tool with HITL approval."""
    
    async def before_call_with_approval(context: Context = None, **kwargs):
        if context is None:
            raise ValueError("Context required for HITL approval")
        
        approval_id = await hitl_system.request_approval(
            user_id=user_id,
            tool_name=tool_func.__name__,
            context=context,
            **kwargs
        )
        
        # Wait for approval (in production, this would be handled differently)
        request = hitl_system.pending_requests[approval_id]
        while request.status == ApprovalStatus.PENDING:
            await asyncio.sleep(1)
        
        if request.status != ApprovalStatus.APPROVED:
            raise ValueError(f"Tool execution denied: {request.id}")
        
        return True
    
    return Tool.from_callable(
        tool_func,
        before_call=before_call_with_approval
    )

# Example: Financial operations requiring approval
def wire_transfer(amount: float, to_account: str, memo: str = "") -> str:
    """Execute a wire transfer - requires human approval."""
    return f"Wire transfer of ${amount} to {to_account} completed. Memo: {memo}"

# Create HITL-enabled agent
async def create_financial_agent(user_id: str) -> Agent:
    transfer_tool = create_hitl_tool(wire_transfer, user_id)
    
    return Agent(
        name="Financial Agent",
        generation_provider=GoogleGenerationProvider(),
        model="gemini-2.5-flash",
        instructions="You are a financial assistant that requires human approval for all transactions.",
        tools=[transfer_tool]
    )

# API endpoint simulation
async def submit_financial_task(user_id: str, task: str) -> str:
    """Submit a financial task that may require human approval."""
    agent = await create_financial_agent(user_id)
    
    try:
        # This will pause when approval is needed
        response = await agent.run_async(task)
        return f"Task completed: {response.text}"
    except Exception as e:
        return f"Task failed: {str(e)}"

# Approval interface simulation
async def approve_pending_request(approval_id: str, approver_id: str) -> bool:
    """Approve a pending request (called from web UI/mobile app)."""
    return await hitl_system.approve_request(approval_id, approver_id)

# Example workflow:
# 1. User submits: "Transfer $5000 to account 123-456-789"
# 2. Agent processes, reaches transfer tool, requests approval
# 3. User gets notification, goes about their day
# 4. Later (hours/days), user approves via mobile app
# 5. Agent resumes and completes the transfer
```

#### 🎯 Key Benefits of HITL in Agentle

- **🛡️ Safety & Compliance**: Critical operations require human oversight
- **⏸️ Pausable Execution**: Agents can pause and resume seamlessly
- **📱 Flexible Approval**: Approve via web, mobile, email, or any interface
- **🔍 Audit Trail**: Complete logging of all approvals and decisions
- **⏰ Asynchronous**: Users don't need to wait - approve when convenient
- **🔄 Context Preservation**: Full conversation state maintained during pauses

#### 🔧 Enhanced Tool Callbacks

Agentle now supports enhanced `before_call` and `after_call` callbacks in tools, with access to the execution context:

```python
from agentle.generations.tools.tool import Tool

def sensitive_operation(data: str) -> str:
    """A sensitive operation that requires approval."""
    return f"Processed: {data}"

async def request_approval(context=None, **kwargs):
    """Request human approval before tool execution."""
    print(f"🔔 Approval requested for operation with args: {kwargs}")
    # In production: send notification, pause context, wait for approval
    return True

def log_execution(context=None, result=None, **kwargs):
    """Log tool execution for audit trail."""
    print(f"📝 Tool executed with result: {result}")

# Create tool with HITL callbacks
secure_tool = Tool.from_callable(
    sensitive_operation,
    before_call=request_approval,  # Called before tool execution
    after_call=log_execution       # Called after tool execution
)

# The context is automatically passed to callbacks when available
agent = Agent(
    name="Secure Agent",
    generation_provider=GoogleGenerationProvider(),
    model="gemini-2.5-flash",
    instructions="You handle sensitive operations with human oversight.",
    tools=[secure_tool]
)
```

#### 🚀 True Asynchronous HITL Workflows

For production environments, Agentle supports **true asynchronous HITL** where agent execution can be suspended for days without blocking the process:

```python
from agentle.agents.errors.tool_suspension_error import ToolSuspensionError

def wire_transfer(amount: float, to_account: str) -> str:
    """Wire transfer that suspends for large amounts."""
    if amount > 10000:
        # Suspend execution - process doesn't block!
        raise ToolSuspensionError(
            reason=f"Transfer of ${amount} requires approval",
            approval_data={
                "amount": amount,
                "to_account": to_account,
                "risk_level": "high"
            },
            timeout_seconds=86400  # 24 hours
        )
    return f"Transfer completed: ${amount}"

# Agent execution suspends and returns immediately
result = await agent.run_async("Transfer $50,000 to account ABC-123")

if result.is_suspended:
    print(f"Suspended: {result.suspension_reason}")
    print(f"Resume token: {result.resumption_token}")
    
    # Process continues, user gets notification
    # Hours/days later, after approval:
    resumed_result = await agent.resume_async(
        result.resumption_token, 
        approval_data={"approved": True}
    )
```

**Key Benefits:**
- **🚀 Non-blocking**: Process never waits for human input
- **⏰ Persistent**: Suspensions survive process restarts (with proper storage)
- **🔄 Resumable**: Continue exactly where execution left off
- **📱 Flexible**: Approve via any interface (web, mobile, email, etc.)
- **🔀 Concurrent**: Handle thousands of suspended executions simultaneously

#### 🏗️ Production-Ready Suspension Stores

Agentle provides multiple suspension store implementations for different deployment scenarios:

```python
from agentle.agents.agent import Agent
from agentle.agents.suspension_manager import (
    SuspensionManager,
    InMemorySuspensionStore,
    SQLiteSuspensionStore,
    RedisSuspensionStore,
)

# Development: In-memory store (fast, no persistence)
dev_store = InMemorySuspensionStore()
dev_manager = SuspensionManager(dev_store)

# Single-instance production: SQLite store (persistent, single instance)
sqlite_store = SQLiteSuspensionStore("suspensions.db")
staging_manager = SuspensionManager(sqlite_store)

# Distributed production: Redis store (distributed, highly available)
redis_store = RedisSuspensionStore(
    redis_url="redis://redis-cluster:6379/0",
    key_prefix="agentle:prod:"
)
prod_manager = SuspensionManager(redis_store)

# Inject into agent constructor
agent = Agent(
    name="Production Financial Agent",
    generation_provider=GoogleGenerationProvider(),
    model="gemini-2.5-flash",
    instructions="You handle sensitive financial operations.",
    tools=[wire_transfer_tool, audit_tool],
    suspension_manager=prod_manager
)
```

**Store Comparison:**

| Store | Best For | Persistence | Scalability | Setup |
|-------|----------|-------------|-------------|-------|
| **InMemory** | Development, Testing | ❌ No | Single Process | Zero config |
| **SQLite** | Single Instance Prod | ✅ Yes | Single Instance | File path |
| **Redis** | Distributed Prod | ✅ Yes | Multi-Instance | Redis server |

#### 🔧 Environment-Specific Configuration

```python
import os
from agentle.agents.suspension_manager import SuspensionManager

def create_suspension_manager():
    """Factory function for environment-specific suspension managers."""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "development":
        return SuspensionManager(InMemorySuspensionStore())
    elif env == "staging":
        return SuspensionManager(SQLiteSuspensionStore("staging_suspensions.db"))
    elif env == "production":
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        return SuspensionManager(RedisSuspensionStore(redis_url))
    else:
        raise ValueError(f"Unknown environment: {env}")

# Use in agent creation
agent = Agent(
    # ... other parameters ...
    suspension_manager=create_suspension_manager()
)
```

This HITL integration makes Agentle suitable for production environments where AI agents handle sensitive operations that require human judgment and approval.

#### 🔀 Complex HITL Scenarios: Pipelines and Teams

Agentle's HITL system seamlessly handles complex multi-agent scenarios including **Agent Pipelines** and **Agent Teams** with sophisticated suspension and resumption capabilities:

##### 🔗 Pipeline Suspension & Resumption

When an agent in a pipeline requires approval, the entire pipeline suspends while preserving its state:

```python
from agentle.agents.agent_pipeline import AgentPipeline
from agentle.agents.errors.tool_suspension_error import ToolSuspensionError

def compliance_check(analysis_type: str) -> str:
    """Financial analysis that requires compliance approval."""
    if analysis_type in ["merger_analysis", "insider_trading"]:
        raise ToolSuspensionError(
            reason=f"Analysis type '{analysis_type}' requires compliance approval",
            approval_data={"analysis_type": analysis_type, "risk_level": "high"},
            timeout_seconds=7200  # 2 hours
        )
    return f"Analysis completed: {analysis_type}"

# Create a financial analysis pipeline
data_agent = Agent(name="Data Agent", tools=[data_access_tool], ...)
analysis_agent = Agent(name="Analysis Agent", tools=[compliance_check], ...)
report_agent = Agent(name="Report Agent", tools=[report_generation_tool], ...)

pipeline = AgentPipeline(agents=[data_agent, analysis_agent, report_agent])

# Pipeline execution suspends at analysis step
result = await pipeline.run_async("Analyze TechCorp for merger potential")

if result.is_suspended:
    print(f"Pipeline suspended: {result.suspension_reason}")
    # Pipeline state preserved: current step, intermediate outputs, context
    
    # Hours later, after compliance approval...
    await suspension_manager.approve_request(result.resumption_token, approved=True)
    
    # Resume from exact suspension point
    final_result = await pipeline.resume_async(result.resumption_token)
    print(f"Pipeline completed: {final_result.text}")
```

**Pipeline Suspension Features:**
- ✅ **State Preservation**: Current step, intermediate outputs, and full context maintained
- ✅ **Exact Resumption**: Continues from the next step after approval
- ✅ **Multiple Suspensions**: Single pipeline can suspend multiple times
- ✅ **Debug Support**: Full visibility into suspension points when debug_mode=True

##### 👥 Team Suspension & Orchestration

Agent Teams maintain conversation history and orchestration state during suspensions:

```python
from agentle.agents.agent_team import AgentTeam

# Create specialized agents with HITL tools
risk_agent = Agent(name="Risk Agent", tools=[financial_analysis_tool], ...)
governance_agent = Agent(name="Governance Agent", tools=[data_access_tool], ...)
legal_agent = Agent(name="Legal Agent", tools=[report_generation_tool], ...)

# Create compliance team
team = AgentTeam(
    agents=[risk_agent, governance_agent, legal_agent],
    orchestrator_provider=GoogleGenerationProvider(),
    orchestrator_model="gemini-2.5-flash"
)

# Team execution with dynamic agent selection
result = await team.run_async(
    "Perform insider trading analysis and access customer PII for compliance review"
)

if result.is_suspended:
    print(f"Team suspended: {result.suspension_reason}")
    # Team state preserved: iteration count, conversation history, selected agent
    
    # After approval...
    resumed_result = await team.resume_async(result.resumption_token)
    
    # Orchestrator continues decision-making from where it left off
    if resumed_result.is_suspended:
        # Handle additional suspensions in the same workflow
        await handle_additional_approval(resumed_result.resumption_token)
        final_result = await team.resume_async(resumed_result.resumption_token)
```

**Team Suspension Features:**
- ✅ **Conversation Continuity**: Full conversation history maintained across suspensions
- ✅ **Orchestration State**: Remembers which agent was selected and why
- ✅ **Dynamic Recovery**: Orchestrator continues intelligent agent selection after resumption
- ✅ **Multi-Suspension**: Teams can suspend multiple times during complex workflows

##### 🔀 Nested Scenarios: Teams within Pipelines

Complex enterprise workflows often involve teams within pipelines. Agentle handles these nested scenarios gracefully:

```python
# Create a pipeline where one step uses a team
prep_agent = Agent(name="Data Prep", ...)
compliance_team = AgentTeam(agents=[risk_agent, governance_agent, legal_agent], ...)
final_agent = Agent(name="Final Report", tools=[report_generation_tool], ...)

# Nested workflow execution
print("Step 1: Data preparation")
prep_result = await prep_agent.run_async("Prepare data for MegaCorp analysis")

print("Step 2: Compliance team analysis")
team_result = await compliance_team.run_async(prep_result.text)

if team_result.is_suspended:
    print(f"Nested team suspended: {team_result.suspension_reason}")
    # Both team state AND pipeline context preserved
    
    await suspension_manager.approve_request(team_result.resumption_token, approved=True)
    team_result = await compliance_team.resume_async(team_result.resumption_token)

print("Step 3: Final reporting")
final_result = await final_agent.run_async(f"Create report: {team_result.text}")

if final_result.is_suspended:
    # Handle final step suspension
    await handle_final_approval(final_result.resumption_token)
    final_result = await final_agent.resume_async(final_result.resumption_token)
```

**Nested Scenario Benefits:**
- ✅ **State Isolation**: Each level (pipeline/team/agent) maintains its own suspension state
- ✅ **Hierarchical Recovery**: Suspensions bubble up correctly through the hierarchy
- ✅ **Complete Context**: Full workflow state preserved across all levels
- ✅ **Enterprise Ready**: Handles real-world complex approval workflows

##### 🏢 Production Enterprise Scenarios

These complex HITL capabilities enable sophisticated enterprise workflows:

```python
# Financial compliance pipeline with multiple approval gates
financial_pipeline = AgentPipeline([
    data_collection_agent,    # May suspend for sensitive data access
    risk_assessment_team,     # Team may suspend for high-risk analysis
    legal_review_agent,       # May suspend for regulatory compliance
    executive_approval_agent, # May suspend for final sign-off
    distribution_agent        # May suspend for external distribution
])

# Workflow can suspend at any step, for any duration
result = await financial_pipeline.run_async(
    "Analyze Q4 financials for SEC filing and distribute to external auditors"
)

# Each suspension maintains complete state for resumption
# Supports approval workflows spanning days or weeks
# Full audit trail of all suspensions and approvals
```

**Enterprise Benefits:**
- 🏢 **Compliance Workflows**: Multi-step approval processes with proper oversight
- ⏰ **Flexible Timing**: Approvals can happen across days/weeks without losing progress
- 📊 **Audit Trail**: Complete logging of all suspensions, approvals, and state changes
- 🔄 **Resilient Recovery**: Workflows survive process restarts and system maintenance
- 👥 **Team Coordination**: Multiple stakeholders can be involved in approval processes

> **Note**: Working HITL examples are available:
> - `examples/simple_hitl_example.py` - Basic tool callbacks and approval workflows
> - `examples/async_hitl_example.py` - True asynchronous suspension and resumption
> - `examples/suspension_stores_example.py` - Different storage backend implementations
> - `examples/complex_hitl_pipeline_team_example.py` - Complex scenarios with pipelines and teams

### 🎭 Flexible Input Types

Agentle agents handle any input type seamlessly:

```python
from agentle.agents.agent import Agent
from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider
import pandas as pd
from PIL import Image
import numpy as np

# Create a basic agent
agent = Agent(
    generation_provider=GoogleGenerationProvider(),
    model="gemini-2.5-flash",
    instructions="You are a versatile assistant that can analyze different types of data."
)

# Process different input types
agent.run("What is the capital of Japan?")  # String

# DataFrame input
df = pd.DataFrame({
    "Country": ["Japan", "France", "USA"],
    "Capital": ["Tokyo", "Paris", "Washington DC"],
    "Population": [126.3, 67.8, 331.9]
})
agent.run(df)  # Automatically converts to markdown table

# Image input (for multimodal models)
img = Image.open("chart.png")
agent.run(img)  # Automatically handles image format

# Dictionary/JSON
user_data = {"name": "Alice", "interests": ["AI", "Python"]}
agent.run(user_data)  # Automatically formats as JSON
```

### 🧩 Prompt Management

Manage prompts with a flexible prompt provider system:

```python
from agentle.prompts.models.prompt import Prompt
from agentle.prompts.prompt_providers.fs_prompt_provider import FSPromptProvider

# Create a prompt provider that loads prompts from files
prompt_provider = FSPromptProvider(base_path="./prompts")

# Load a prompt
weather_prompt = prompt_provider.provide("weather_template")

# Compile the prompt with variables
compiled_prompt = weather_prompt.compile(
    location="Tokyo",
    units="celsius",
    days=5
)

# Use the prompt with an agent
agent.run(compiled_prompt)
```

### 💬 Rich Messaging System

Create multimodal conversations with fine-grained control:

```python
from agentle.generations.models.messages.user_message import UserMessage
from agentle.generations.models.messages.assistant_message import AssistantMessage
from agentle.generations.models.messages.developer_message import DeveloperMessage
from agentle.generations.models.message_parts.text import TextPart
from agentle.generations.models.message_parts.file import FilePart

# Create a conversation with multiple message types
messages = [
    # System instructions (not visible to the user)
    DeveloperMessage(parts=[
        TextPart(text="You are a helpful travel assistant that speaks in a friendly tone.")
    ]),
    
    # User's initial message with image
    UserMessage(parts=[
        TextPart(text="What can you tell me about this landmark?"),
        FilePart(
            data=open("landmark_photo.jpg", "rb").read(),
            mime_type="image/jpeg"
        )
    ]),
    
    # Previous assistant response in the conversation
    AssistantMessage(parts=[
        TextPart(text="That's the famous Tokyo Tower in Japan!")
    ]),
    
    # User's follow-up question
    UserMessage(parts=[
        TextPart(text="What's the best time to visit?")
    ])
]

# Pass the complete conversation to the agent
result = agent.run(messages)
```

## 📚 Full Feature Documentation

### 📁 File Path Handling Best Practices

When using `static_knowledge` with local files, proper path handling is crucial for reliability and security. Agentle provides robust file validation and error handling to ensure your agents work consistently across different environments.

#### ✅ Recommended Approaches

```python
from pathlib import Path
from agentle.agents.agent import Agent
from agentle.agents.knowledge.static_knowledge import StaticKnowledge
from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider

# 1. Use absolute paths with pathlib.Path (RECOMMENDED)
script_dir = Path(__file__).parent
document_path = script_dir / "data" / "curriculum.pdf"

# Check file existence before creating agent
if document_path.exists():
    agent = Agent(
        name="Document Expert",
        generation_provider=GoogleGenerationProvider(),
        model="gemini-2.5-flash",
        static_knowledge=[
            StaticKnowledge(
                content=str(document_path),  # Convert Path to string
                cache=3600,  # Cache for 1 hour
                parse_timeout=60
            )
        ],
        instructions="You are a helpful assistant with access to curriculum documents."
    )
else:
    print(f"Document not found: {document_path}")

# 2. Handle multiple sources with validation
mixed_knowledge = []

# Local file with validation
local_doc = script_dir / "important_document.pdf"
if local_doc.exists():
    mixed_knowledge.append(
        StaticKnowledge(
            content=str(local_doc),
            cache=7200,  # Cache for 2 hours
            parse_timeout=90
        )
    )

# URL (no validation needed)
mixed_knowledge.append(
    StaticKnowledge(
        content="https://example.com/public-document.pdf",
        cache=3600,
        parse_timeout=120
    )
)

# Raw text content
mixed_knowledge.append(
    StaticKnowledge(
        content="Important context: Always validate file paths.",
        cache="infinite"
    )
)

# 3. Proper error handling
try:
    agent = Agent(
        name="Multi-Source Agent",
        generation_provider=GoogleGenerationProvider(),
        model="gemini-2.5-flash",
        static_knowledge=mixed_knowledge,
        instructions="You have access to multiple knowledge sources."
    )
except ValueError as e:
    print(f"File validation error: {e}")
    # Handle the error appropriately
```

#### 🚨 Common Pitfalls to Avoid

```python
# ❌ DON'T: Use relative paths without validation
static_knowledge=[
    StaticKnowledge(content="./document.pdf")  # May fail in different working directories
]

# ❌ DON'T: Ignore file existence
static_knowledge=[
    StaticKnowledge(content="/path/to/nonexistent.pdf")  # Will raise ValueError
]

# ❌ DON'T: Use hardcoded absolute paths
static_knowledge=[
    StaticKnowledge(content="/Users/john/documents/file.pdf")  # Won't work on other machines
]

# ✅ DO: Use proper validation and error handling
from pathlib import Path

def create_agent_with_documents(document_paths: List[str]) -> Agent:
    """Create an agent with validated document paths."""
    validated_knowledge = []
    
    for path_str in document_paths:
        path = Path(path_str)
        if path.exists():
            validated_knowledge.append(
                StaticKnowledge(
                    content=str(path.resolve()),  # Use absolute path
                    cache=3600
                )
            )
        else:
            print(f"Warning: Document not found: {path}")
    
    if not validated_knowledge:
        raise ValueError("No valid documents found")
    
    return Agent(
        name="Document Agent",
        generation_provider=GoogleGenerationProvider(),
        model="gemini-2.5-flash",
        static_knowledge=validated_knowledge,
        instructions="You are a document analysis assistant."
    )
```

#### 🔧 Advanced Path Utilities

```python
from pathlib import Path
from typing import List, Optional

def find_documents_in_directory(directory: Path, extensions: List[str] = None) -> List[Path]:
    """Find all documents with specified extensions in a directory."""
    if extensions is None:
        extensions = [".pdf", ".txt", ".docx", ".md"]
    
    documents = []
    if directory.exists() and directory.is_dir():
        for ext in extensions:
            documents.extend(directory.glob(f"**/*{ext}"))
    
    return documents

def create_knowledge_from_directory(directory_path: str) -> List[StaticKnowledge]:
    """Create StaticKnowledge objects from all documents in a directory."""
    directory = Path(directory_path)
    documents = find_documents_in_directory(directory)
    
    knowledge = []
    for doc_path in documents:
        knowledge.append(
            StaticKnowledge(
                content=str(doc_path),
                cache=3600,  # Cache for 1 hour
                parse_timeout=120  # 2 minutes timeout
            )
        )
    
    return knowledge

# Usage
data_dir = Path(__file__).parent / "data"
knowledge_base = create_knowledge_from_directory(str(data_dir))

agent = Agent(
    name="Knowledge Base Agent",
    generation_provider=GoogleGenerationProvider(),
    model="gemini-2.5-flash",
    static_knowledge=knowledge_base,
    instructions="You have access to a comprehensive knowledge base."
)
```

> 💡 **Pro Tip**: Check out the complete example at [`examples/file_path_best_practices.py`](examples/file_path_best_practices.py) for a comprehensive demonstration of file path handling patterns.

### 🔗 Agent-to-Agent (A2A) Protocol

Agentle provides built-in support for Google's [A2A Protocol](https://google.github.io/A2A/):

```python
import os
import time

from agentle.agents.a2a.a2a_interface import A2AInterface
from agentle.agents.a2a.message_parts.text_part import TextPart
from agentle.agents.a2a.messages.message import Message
from agentle.agents.a2a.tasks.task_query_params import TaskQueryParams
from agentle.agents.a2a.tasks.task_send_params import TaskSendParams
from agentle.agents.a2a.tasks.task_state import TaskState
from agentle.agents.agent import Agent
from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider

# Set up agent and A2A interface
provider = GoogleGenerationProvider(api_key=os.environ.get("GOOGLE_API_KEY"))
agent = Agent(name="Example Agent", generation_provider=provider, model="gemini-2.5-flash")
a2a = A2AInterface(agent=agent)

# Send task to agent
message = Message(role="user", parts=[TextPart(text="What are three facts about the Moon?")])
task = a2a.tasks.send(TaskSendParams(message=message))
print(f"Task sent with ID: {task.id}")

# Wait for task completion and get result
while True:
    result = a2a.tasks.get(TaskQueryParams(id=task.id))
    status = result.result.status
    
    if status == TaskState.COMPLETED:
        print("\nResponse:", result.result.history[1].parts[0].text)
        break
    elif status == TaskState.FAILED:
        print(f"Task failed: {result.result.error}")
        break
    print(f"Status: {status}")
    time.sleep(1)
```

### 🔧 Tool Calling and Structured Outputs Combined

```python
from pydantic import BaseModel
from typing import List, Optional

# Define a tool
def get_city_data(city: str) -> dict:
    """Get basic information about a city."""
    city_database = {
        "Paris": {
            "country": "France",
            "population": 2161000,
            "timezone": "CET",
            "famous_for": ["Eiffel Tower", "Louvre", "Notre Dame"],
        },
        # More cities...
    }
    return city_database.get(city, {"error": f"No data found for {city}"})

# Define the structured response schema
class TravelRecommendation(BaseModel):
    city: str
    country: str
    population: int
    local_time: str
    attractions: List[str]
    best_time_to_visit: str
    estimated_daily_budget: float
    safety_rating: Optional[int] = None

# Create an agent with both tools and a structured output schema
travel_agent = Agent(
    name="Travel Advisor",
    generation_provider=GoogleGenerationProvider(),
    model="gemini-2.5-flash",
    instructions="""You are a travel advisor that provides structured recommendations for city visits.""",
    tools=[get_city_data],
    response_schema=TravelRecommendation,
)

# Run the agent
response = travel_agent.run("Create a travel recommendation for Tokyo.")

# Access structured data
rec = response.parsed
print(f"TRAVEL RECOMMENDATION FOR {rec.city}, {rec.country}")
print(f"Population: {rec.population:,}")
print(f"Best time to visit: {rec.best_time_to_visit}")
```

### 📄 Custom Document Parsers

```python
from typing import override
from pathlib import Path
from agentle.parsing.document_parser import DocumentParser
from agentle.parsing.parsed_document import ParsedFile
from agentle.parsing.section_content import SectionContent

# Create a custom parser
class CustomParser(DocumentParser):
    """Parser with specialized document understanding"""
    
    @override
    async def parse_async(self, document_path: str) -> ParsedFile:
        # Read the document file
        path = Path(document_path)
        file_content = path.read_text(encoding="utf-8")
        
        # Use your custom parsing logic
        parsed_content = file_content.upper()  # Simple example transformation
        
        # Return in the standard ParsedFile format
        return ParsedFile(
            name=path.name,
            sections=[
                SectionContent(
                    number=1,
                    text=parsed_content,
                    md=parsed_content
                )
            ]
        )

# Use the custom parser with an agent
from agentle.agents.agent import Agent
from agentle.agents.knowledge.static_knowledge import StaticKnowledge

agent = Agent(
    name="Document Expert",
    generation_provider=GoogleGenerationProvider(),
    model="gemini-2.5-flash",
    instructions="You analyze documents with precision.",
    static_knowledge=[
        StaticKnowledge(content="contracts/agreement.pdf", cache="infinite")
    ],
    # Pass your custom parser to the agent
    document_parser=CustomParser()
)
```

### 🗄️ Production-Ready Caching

Agentle provides a flexible caching system for parsed documents to improve performance and reduce redundant parsing operations in production environments:

```python
from agentle.agents.agent import Agent
from agentle.agents.knowledge.static_knowledge import StaticKnowledge
from agentle.parsing.cache import InMemoryDocumentCacheStore, RedisCacheStore
from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider

# Option 1: In-Memory Cache (Default)
# Perfect for single-process applications and development
in_memory_cache = InMemoryDocumentCacheStore(
    cleanup_interval=300  # Clean up expired entries every 5 minutes
)

agent_with_memory_cache = Agent(
    name="Research Assistant",
    generation_provider=GoogleGenerationProvider(),
    model="gemini-2.5-flash",
    instructions="You are a research assistant that analyzes documents.",
    static_knowledge=[
        StaticKnowledge(content="research_paper.pdf", cache=3600),  # Cache for 1 hour
        StaticKnowledge(content="https://example.com/data.pdf", cache="infinite"),  # Cache indefinitely
    ],
    document_cache_store=in_memory_cache
)

# Option 2: Redis Cache (Production)
# Perfect for distributed environments with multiple processes/servers
redis_cache = RedisCacheStore(
    redis_url="redis://localhost:6379/0",
    key_prefix="agentle:parsed:",
    default_ttl=3600  # 1 hour default TTL
)

agent_with_redis_cache = Agent(
    name="Production Assistant",
    generation_provider=GoogleGenerationProvider(),
    model="gemini-2.5-flash",
    instructions="You are a production assistant with distributed caching.",
    static_knowledge=[
        StaticKnowledge(content="large_document.pdf", cache=7200),  # Cache for 2 hours
        StaticKnowledge(content="https://api.example.com/report", cache=1800),  # Cache for 30 minutes
    ],
    document_cache_store=redis_cache
)

# Option 3: No Cache (Legacy behavior)
# Documents are parsed fresh every time
agent_no_cache = Agent(
    name="Simple Assistant",
    generation_provider=GoogleGenerationProvider(),
    model="gemini-2.5-flash",
    instructions="You are a simple assistant without caching.",
    static_knowledge=[
        "Raw text knowledge",  # No caching for raw text
        StaticKnowledge(content="document.pdf"),  # No cache specified = no caching
    ]
    # No document_cache_store specified = uses default InMemoryDocumentCacheStore but only for items with cache TTL
)

# Cache Management Operations
cache = InMemoryDocumentCacheStore()

# Check if a document is cached
cache_key = cache.get_cache_key("document.pdf", "PDFParser")
is_cached = await cache.exists_async(cache_key)

# Get cache statistics
stats = cache.get_stats()
print(f"Cache entries: {stats['active_entries']}")

# Clear all cached documents
await cache.clear_async()

# For Redis cache, get detailed info
if isinstance(cache, RedisCacheStore):
    cache_info = await cache.get_cache_info()
    print(f"Redis version: {cache_info['redis_version']}")
    await cache.close()  # Clean up Redis connection
```

**Cache Store Comparison:**

| Store | Best For | Persistence | Scalability | Setup |
|-------|----------|-------------|-------------|-------|
| **InMemory** | Development, Single Process | ❌ No | Single Process | Zero config |
| **Redis** | Production, Distributed | ✅ Yes | Multi-Instance | Redis server |

**Caching Benefits:**
- 🚀 **Performance**: Avoid re-parsing large documents
- 💰 **Cost Savings**: Reduce API calls for URL-based documents  
- 🔄 **Consistency**: Same parsed content across multiple agent runs
- 📊 **Scalability**: Share cached documents across processes (Redis)
- ⚡ **Responsiveness**: Faster agent startup with pre-cached knowledge

## 🧠 Philosophy

> **"Simplicity is the ultimate sophistication"** - Leonardo da Vinci

I created Agentle out of frustration with the direction of other agent frameworks. Many frameworks have lost sight of clean design principles by adding numerous configuration flags to their Agent constructors (like ``enable_whatever=True``, ``add_memory=True``, etc.). This approach creates countless possible combinations, making debugging and development unnecessarily complex. 

Also, there is a lot of market pressure that **unfortunately** leads the devs to push unpolished stuff into prod, because their framework must always be on the top of the frameworks. That's not the case right here. I made this for myself, but it might be helpful to other devs as well. I am a solo developer in this framework (for now), but I want to only ship stuff that developers will really need. And to ship stuff only when it's ready (e.g PROPERLY TYPED, since many frameworks just goes to **kwargs or "Any" in many cases).

I wanted to create a framework that was both helpful in some common scenarios, but let the developer do his job as well.

Agentle strives to maintain a careful balance between simplicity and practicality. For example, I've wrestled with questions like whether document parsing functionality belongs in the Agent constructor. While not "simple" in the purest sense, such features can be practical for users. Finding this balance is central to Agentle's design philosophy.

Core principles of Agentle:

* Avoiding configuration flags in constructors whenever possible
* Organizing each class and function in separate modules by design
* Following the Single Responsibility Principle rather than strictly Pythonic conventions (5000 SLOC types.py file)
* Creating a codebase that's not only easy to use but also easy to maintain and extend (though the limitations of python about circular imports, me (and other devs), should be aware of this issue when working with one class per module)

Through this thoughtful approach to architecture, Agentle aims to provide a framework that's both powerful and elegant for building the next generation of AI agents.

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">
  <p>
    <strong>Built with ❤️ by a developer, for developers</strong>
  </p>
  <p>
    <a href="#-agentle">⬆ Back to top</a>
  </p>
</div>

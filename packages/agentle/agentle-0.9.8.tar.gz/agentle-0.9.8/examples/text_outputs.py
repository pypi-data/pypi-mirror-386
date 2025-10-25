"""
Text Outputs Example

This example demonstrates how to create a simple agent that generates text responses
using the Agentle framework.
"""

import logging

from dotenv import load_dotenv

from agentle.agents.agent import Agent
from agentle.generations.providers.google.google_generation_provider import (
    GoogleGenerationProvider,
)
from agentle.generations.tracing.langfuse_otel_client import LangfuseOtelClient


logging.basicConfig(level=logging.DEBUG)

load_dotenv(override=True)

# Create a simple agent with minimal configuration
agent = Agent(
    name="Simple Text Agent",
    generation_provider=GoogleGenerationProvider(
        use_vertex_ai=True,
        otel_clients=LangfuseOtelClient(host="https://cloud.langfuse.com"),
        project="unicortex",
        location="global",
    ),
    model="gemini-2.5-flash",  # Use an appropriate model
    instructions="You are a helpful assistant who provides concise, accurate information.",
)

# Run the agent with a simple query
response = agent.run(
    "hi",
    trace_params={
        "name": "Agentle Workflow",
        "user_id": "arthur123",
        "session_id": "session-123",
        "tags": ["example tags"],
    },
)

# Print the response text
print(response.text)

# You can also access conversation steps - now always at least 1 step!
print(f"\nExecution steps: {len(response.context.steps)}")
for i, step in enumerate(response.context.steps):
    print(f"Step {i + 1}:")
    print(f"  Type: {step.step_type}")
    print(f"  Iteration: {step.iteration}")
    print(f"  Duration: {step.duration_ms:.1f}ms")
    print(f"  Has tool executions: {step.has_tool_executions}")
    print(f"  Successful: {step.is_successful}")
    if step.generation_text:
        preview = (
            step.generation_text[:100] + "..."
            if len(step.generation_text) > 100
            else step.generation_text
        )
        print(f"  Generated text preview: {preview}")
    if step.token_usage:
        print(
            f"  Token usage: {step.token_usage.prompt_tokens} prompt + {step.token_usage.completion_tokens} completion = {step.token_usage.total_tokens} total"
        )

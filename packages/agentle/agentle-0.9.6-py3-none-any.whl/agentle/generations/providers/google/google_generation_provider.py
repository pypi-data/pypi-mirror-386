"""
Google AI provider implementation for the Agentle framework.

This module provides integration with Google's Generative AI services, allowing
Agentle to use models from the Google AI ecosystem. It implements the necessary
provider interfaces to maintain compatibility with the broader Agentle framework
while handling all Google-specific implementation details internally.

The module supports:
- Both API key and credential-based authentication
- Optional Vertex AI integration for enterprise deployments
- Configurable HTTP options and timeouts
- Function/tool calling capabilities
- Structured output parsing via response schemas
- Tracing and observability integration

This provider transforms Agentle's unified message format into Google's Content
format and adapts responses back into Agentle's Generation objects, maintaining
a consistent interface regardless of the underlying AI provider being used.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator, AsyncIterator, Mapping, Sequence
import hashlib
from textwrap import dedent
from typing import TYPE_CHECKING, cast, overload, override

from agentle.generations.models.generation.generation import Generation
from agentle.generations.models.generation.generation_config import GenerationConfig
from agentle.generations.models.generation.generation_config_dict import (
    GenerationConfigDict,
)
from agentle.generations.models.message_parts.file import FilePart
from agentle.generations.models.message_parts.text import TextPart
from agentle.generations.models.messages.developer_message import DeveloperMessage
from agentle.generations.models.messages.message import Message
from agentle.generations.models.messages.user_message import UserMessage
from agentle.generations.providers.base.generation_provider import (
    GenerationProvider,
)
from agentle.generations.providers.decorators.model_kind_mapper import (
    override_model_kind,
)
from agentle.generations.providers.google.adapters.agentle_tool_to_google_tool_adapter import (
    AgentleToolToGoogleToolAdapter,
)
from agentle.generations.providers.google.adapters.generate_generate_content_response_to_generation_adapter import (
    GenerateGenerateContentResponseToGenerationAdapter,
)
from agentle.generations.providers.google.adapters.message_to_google_content_adapter import (
    MessageToGoogleContentAdapter,
)
from agentle.generations.providers.google.function_calling_config import (
    FunctionCallingConfig,
)
from agentle.generations.providers.types.model_kind import ModelKind
from agentle.generations.tools.tool import Tool
from agentle.generations.tracing import observe
from agentle.utils.describe_model_for_llm import describe_model_for_llm

if TYPE_CHECKING:
    from google.auth.credentials import Credentials
    from google.genai.client import (
        DebugConfig,
    )
    from google.genai.types import HttpOptions

    from agentle.generations.tracing.otel_client import OtelClient


type WithoutStructuredOutput = None

logger = logging.getLogger(__name__)


class GoogleGenerationProvider(GenerationProvider):
    """
    Provider implementation for Google's Generative AI service.

    This class implements the GenerationProvider interface for Google AI models,
    allowing seamless integration with the Agentle framework. It supports both
    standard API key authentication and Vertex AI integration for enterprise
    deployments.

    The provider handles message format conversion, tool adaptation, function
    calling configuration, and response processing to maintain consistency with
    Agentle's unified interface.

    Attributes:
        use_vertex_ai: Whether to use Google Vertex AI instead of standard API.
        api_key: Optional API key for authentication with Google AI.
        credentials: Optional credentials object for authentication.
        project: Google Cloud project ID (required for Vertex AI).
        location: Google Cloud region (required for Vertex AI).
        debug_config: Optional configuration for debug logging.
        http_options: HTTP options for the Google AI client.
        message_adapter: Adapter to convert Agentle messages to Google Content format.
        function_calling_config: Configuration for function calling behavior.
    """

    def __init__(
        self,
        *,
        otel_clients: Sequence[OtelClient] | OtelClient | None = None,
        use_vertex_ai: bool = False,
        api_key: str | None | None = None,
        credentials: Credentials | None = None,
        project: str | None = None,
        location: str | None = None,
        debug_config: DebugConfig | None = None,
        http_options: HttpOptions | None = None,
        function_calling_config: FunctionCallingConfig | None = None,
        provider_name: str | None = None,
    ) -> None:
        """
        Initialize the Google Generation Provider.

        Args:
            otel_clients: Optional client for observability and tracing.
            use_vertex_ai: Whether to use Google Vertex AI instead of standard API.
            api_key: Optional API key for authentication with Google AI.
            credentials: Optional credentials object for authentication.
            project: Google Cloud project ID (required for Vertex AI).
            location: Google Cloud region (required for Vertex AI).
            debug_config: Optional configuration for debug logging.
            http_options: HTTP options for the Google AI client.
            message_adapter: Optional adapter to convert Agentle messages to Google Content.
            function_calling_config: Optional configuration for function calling behavior.
        """
        from google import genai
        from google.genai import types

        # Establish a stable provider identity for circuit breaker/logging
        if provider_name:
            computed_provider_id = provider_name
        else:
            mode = "vertexai" if use_vertex_ai else "genai"
            cred_cls = credentials.__class__.__name__ if credentials else "none"
            key_hash = (
                hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:8]
                if (api_key and not use_vertex_ai)
                else "nokey"
            )
            computed_provider_id = f"{mode}|p:{project or 'none'}|l:{location or 'none'}|c:{cred_cls}|k:{key_hash}"

        super().__init__(otel_clients=otel_clients, provider_id=computed_provider_id)
        self.message_adapter = MessageToGoogleContentAdapter()
        self.function_calling_config = function_calling_config or {}

        _http_options = http_options or types.HttpOptions()
        self._client = genai.Client(
            vertexai=use_vertex_ai,
            api_key=api_key if not use_vertex_ai else None,
            credentials=credentials,
            project=project if use_vertex_ai else None,
            location=location if use_vertex_ai else None,
            debug_config=debug_config,
            http_options=_http_options,
        )

    # provider_id already set via super().__init__

    @property
    @override
    def default_model(self) -> str:
        """
        The default model to use for generation.
        """
        return "gemini-2.5-flash"

    @property
    @override
    def organization(self) -> str:
        """
        Get the provider organization identifier.

        Returns:
            str: The organization identifier, which is "google" for this provider.
        """
        return "google"

    async def stream_async[T = WithoutStructuredOutput](
        self,
        *,
        model: str | ModelKind | None = None,
        messages: Sequence[Message],
        response_schema: type[T] | None = None,
        generation_config: GenerationConfig | GenerationConfigDict | None = None,
        tools: Sequence[Tool] | None = None,
    ) -> AsyncGenerator[Generation[WithoutStructuredOutput], None]:
        from google.genai import types

        if self._normalize_generation_config(generation_config).n > 1:
            raise ValueError("streaming does not support n > 1.")

        used_model = self._resolve_model(model)
        _generation_config = self._normalize_generation_config(generation_config)

        system_instruction: str | None = None
        first_message = messages[0]
        if isinstance(first_message, DeveloperMessage):
            system_instruction = first_message.text

        if response_schema:
            model_description = describe_model_for_llm(response_schema)  # type: ignore[reportArgumentType]
            json_instruction = "Your Output must be a valid JSON string. Do not include any other text. You must provide an asnwer following the following json structure:"
            conditional_prefix = (
                "If, and only if, not calling any tools, " if tools else ""
            )

            instruction_text = (
                f"{conditional_prefix}{json_instruction}\n{model_description}"
            )

            system_instruction = (
                dedent(f"""\
                You are a helpful assistant. {instruction_text}
                """)
                if not system_instruction
                else system_instruction
                + dedent(f"""\
                \n\n
                {instruction_text}
                """)
            )

        message_tools = [
            part
            for message in messages
            for part in message.parts
            if isinstance(part, Tool)
        ]

        final_tools = (
            list(tools or []) + message_tools if tools or message_tools else None
        )

        disable_function_calling = self.function_calling_config.get("disable", True)
        # if disable_function_calling is True, set maximum_remote_calls to None
        maximum_remote_calls = None if disable_function_calling else 10
        ignore_call_history = self.function_calling_config.get(
            "ignore_call_history", False
        )

        _tools: types.ToolListUnion | None = (
            [AgentleToolToGoogleToolAdapter().adapt(tool) for tool in final_tools]
            if final_tools
            else None
        )

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=_generation_config.temperature,
            top_p=_generation_config.top_p,
            top_k=_generation_config.top_k,
            candidate_count=_generation_config.n,
            tools=_tools,
            max_output_tokens=_generation_config.max_output_tokens,
            response_schema=response_schema if bool(response_schema) else None,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=disable_function_calling,
                maximum_remote_calls=maximum_remote_calls,
                ignore_call_history=ignore_call_history,
            ),
        )

        user_messages = [msg for msg in messages if isinstance(msg, UserMessage)]
        if user_messages and all(
            isinstance(part, FilePart) for part in user_messages[-1].parts
        ):
            messages = list(messages) + [UserMessage(parts=[TextPart(text=".")])]

        # Developer message is usuarlly the first message. if it's not, then there is no developer message
        if isinstance(messages[0], DeveloperMessage):
            messages = messages[1:]

        contents = [self.message_adapter.adapt(msg) for msg in messages]

        try:
            async with asyncio.timeout(_generation_config.timeout_in_seconds):
                generate_content_response_stream: AsyncIterator[
                    types.GenerateContentResponse
                ] = await self._client.aio.models.generate_content_stream(
                    model=used_model,
                    contents=cast(types.ContentListUnion, contents),
                    config=config,
                )
        except asyncio.TimeoutError as e:
            e.add_note(
                f"Content generation timed out after {_generation_config.timeout_in_seconds}s"
            )
            raise

        # Create the response
        response = GenerateGenerateContentResponseToGenerationAdapter[
            WithoutStructuredOutput
        ](
            response_schema=None,
            model=used_model,
        ).adapt(generate_content_response_stream)

        # Yield from the async iterator to make this an async generator
        async for generation in response:
            yield generation

    @overload
    async def generate_async[T](
        self,
        *,
        model: str | ModelKind | None = None,
        messages: Sequence[Message],
        response_schema: type[T],
        generation_config: GenerationConfig | GenerationConfigDict | None = None,
        fallback_models: Sequence[str] | None = None,
    ) -> Generation[T]: ...

    @overload
    async def generate_async(
        self,
        *,
        model: str | ModelKind | None = None,
        messages: Sequence[Message],
        generation_config: GenerationConfig | GenerationConfigDict | None = None,
        tools: Sequence[Tool],
        fallback_models: Sequence[str] | None = None,
    ) -> Generation[WithoutStructuredOutput]: ...

    @overload
    async def generate_async(
        self,
        *,
        model: str | ModelKind | None = None,
        messages: Sequence[Message],
        generation_config: GenerationConfig | GenerationConfigDict | None = None,
        fallback_models: Sequence[str] | None = None,
    ) -> Generation[WithoutStructuredOutput]: ...

    @observe
    @override
    @override_model_kind
    async def generate_async[T = WithoutStructuredOutput](
        self,
        *,
        model: str | ModelKind | None = None,
        messages: Sequence[Message],
        response_schema: type[T] | None = None,
        generation_config: GenerationConfig | GenerationConfigDict | None = None,
        tools: Sequence[Tool] | None = None,
        fallback_models: Sequence[str] | None = None,
    ) -> Generation[T]:
        """
        Create a generation asynchronously using a Google AI model.

        This method handles the conversion of Agentle messages and tools to Google's
        format, sends the request to Google's API, and processes the response into
        Agentle's standardized Generation format. With the @observe decorator, all
        observability and tracing is handled automatically.

        Note: Google AI API does not natively support fallback models. The fallback_models
        parameter is accepted for API compatibility but ignored.

        Args:
            model: The Google AI model identifier to use (e.g., "gemini-1.5-pro").
            messages: A sequence of Agentle messages to send to the model.
            response_schema: Optional Pydantic model for structured output parsing.
            generation_config: Optional configuration for the generation request.
            tools: Optional sequence of Tool objects for function calling.

        Returns:
            Generation[T]: An Agentle Generation object containing the model's response,
                potentially with structured output if a response_schema was provided.
        """
        from google.genai import types

        used_model = self._resolve_model(model)
        _generation_config = self._normalize_generation_config(generation_config)

        system_instruction: str | None = None
        first_message = messages[0]
        if isinstance(first_message, DeveloperMessage):
            system_instruction = first_message.text

        message_tools = [
            part
            for message in messages
            for part in message.parts
            if isinstance(part, Tool)
        ]

        final_tools = (
            list(tools or []) + message_tools if tools or message_tools else None
        )

        disable_function_calling = self.function_calling_config.get("disable", True)
        # if disable_function_calling is True, set maximum_remote_calls to None
        maximum_remote_calls = None if disable_function_calling else 10
        ignore_call_history = self.function_calling_config.get(
            "ignore_call_history", False
        )

        _tools: types.ToolListUnion | None = (
            [AgentleToolToGoogleToolAdapter().adapt(tool) for tool in final_tools]
            if final_tools
            else None
        )

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=_generation_config.temperature,
            top_p=_generation_config.top_p,
            top_k=_generation_config.top_k,
            candidate_count=_generation_config.n,
            tools=_tools,
            max_output_tokens=_generation_config.max_output_tokens,
            response_schema=response_schema if bool(response_schema) else None,
            response_mime_type="application/json" if bool(response_schema) else None,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=disable_function_calling,
                maximum_remote_calls=maximum_remote_calls,
                ignore_call_history=ignore_call_history,
            ),
        )

        user_messages = [msg for msg in messages if isinstance(msg, UserMessage)]
        if user_messages and all(
            isinstance(part, FilePart) for part in user_messages[-1].parts
        ):
            messages = list(messages) + [UserMessage(parts=[TextPart(text=".")])]

        # Developer message is usuarlly the first message. if it's not, then there is no developer message
        if isinstance(messages[0], DeveloperMessage):
            messages = messages[1:]

        contents = [self.message_adapter.adapt(msg) for msg in messages]

        try:
            async with asyncio.timeout(_generation_config.timeout_in_seconds):
                generate_content_response: types.GenerateContentResponse = (
                    await self._client.aio.models.generate_content(
                        model=used_model,
                        contents=cast(types.ContentListUnion, contents),
                        config=config,
                    )
                )
        except asyncio.TimeoutError as e:
            e.add_note(
                f"Content generation timed out after {_generation_config.timeout_in_seconds}s"
            )
            raise

        # Create the response with pricing calculation
        adapter = GenerateGenerateContentResponseToGenerationAdapter[T](
            response_schema=response_schema,
            model=used_model,
            provider=self,
        )

        # Use async adapter if not streaming
        if hasattr(generate_content_response, "__aiter__"):
            response = adapter.adapt(generate_content_response)
        else:
            response = await adapter.adapt_async(generate_content_response)

        return response

    @override
    def map_model_kind_to_provider_model(
        self,
        model_kind: ModelKind,
    ) -> str:
        mapping: Mapping[ModelKind, str] = {
            # Stable models
            "category_nano": "gemini-2.5-flash-lite",
            "category_mini": "gemini-2.5-flash",
            "category_standard": "gemini-2.5-flash",
            "category_pro": "gemini-2.5-pro",
            "category_flagship": "gemini-2.5-pro",
            "category_reasoning": "gemini-2.5-pro",
            "category_vision": "gemini-2.5-pro-vision",
            "category_coding": "gemini-2.5-pro",
            "category_instruct": "gemini-2.5-flash",
            # Experimental models
            "category_nano_experimental": "gemini-2.5-flash-lite",  # no distinct experimental found
            "category_mini_experimental": "gemini-2.5-flash-preview-05-20",  # real preview model
            "category_standard_experimental": "gemini-2.5-flash-preview-05-20",  # fallback
            "category_pro_experimental": "gemini-2.5-pro",  # fallback
            "category_flagship_experimental": "gemini-2.5-pro",  # fallback
            "category_reasoning_experimental": "gemini-2.5-pro",  # fallback
            "category_vision_experimental": "gemini-2.5-pro-vision",  # fallback
            "category_coding_experimental": "gemini-2.5-pro",  # fallback
            "category_instruct_experimental": "gemini-2.5-flash-preview-05-20",  # closest preview
        }

        return mapping[model_kind]

    @override
    async def price_per_million_tokens_input(
        self, model: str, estimate_tokens: int | None = None
    ) -> float:
        """
        Get the price per million tokens for input/prompt tokens.

        Args:
            model: The model identifier.
            estimate_tokens: Optional estimate of token count.

        Returns:
            float: The price per million input tokens for the specified model.
        """
        # Pricing in USD per million tokens (from https://cloud.google.com/vertex-ai/generative-ai/pricing)
        # Format: (low_tier_price, high_tier_price, threshold) for tiered models
        model_to_price_per_million: Mapping[str, float | tuple[float, float, int]] = {
            # Gemini 2.5 Pro family (tiered pricing at 200K tokens)
            "gemini-2.5-pro": (1.25, 2.50, 200_000),
            "gemini-2.5-pro-vision": (1.25, 2.50, 200_000),
            # Gemini 2.5 Flash family
            "gemini-2.5-flash": 0.15,
            "gemini-2.5-flash-preview-05-20": 0.15,  # Assuming same as standard 2.5 Flash
            # Gemini 2.0 Flash family
            "gemini-2.5-flash-lite": 0.075,
        }

        price_info = model_to_price_per_million.get(model)
        if price_info is None:
            logger.warning(
                f"Model {model} not found in model_to_price_per_million yet. Returning 0.0 to not raise any errors."
            )
            return 0.0

        # If estimate_tokens is None, return the base price (or lower tier price for tiered models)
        if estimate_tokens is None:
            if isinstance(price_info, tuple):
                # Return the lower tier price for tiered models
                return price_info[0]
            return price_info

        # Calculate the price based on token tiers if applicable
        if isinstance(price_info, tuple):
            low_tier_price, high_tier_price, threshold = price_info

            # If tokens exceed threshold, use the higher tier price
            if estimate_tokens > threshold:
                return high_tier_price
            else:
                return low_tier_price
        else:
            # Standard pricing for non-tiered models
            return price_info

    @override
    async def price_per_million_tokens_output(
        self, model: str, estimate_tokens: int | None = None
    ) -> float:
        """
        Get the price per million tokens for output/completion tokens.

        Args:
            model: The model identifier.
            estimate_tokens: Optional estimate of token count.

        Returns:
            float: The price per million output tokens for the specified model.
        """
        # Pricing in USD per million tokens (from https://cloud.google.com/vertex-ai/generative-ai/pricing)
        # Note: For Gemini 2.5 Pro, output pricing depends on input token count, but we use conservative estimates
        model_to_price_per_million: Mapping[str, float | tuple[float, float, int]] = {
            # Gemini 2.5 Pro family (tiered pricing - using lower tier as conservative estimate)
            "gemini-2.5-pro": 10.0,  # Conservative estimate, could be 15.0 for >200K input
            "gemini-2.5-pro-vision": 10.0,
            # Gemini 2.5 Flash family (standard text output, not reasoning)
            "gemini-2.5-flash": 0.60,  # Standard text output (3.50 for thinking/reasoning)
            "gemini-2.5-flash-preview-05-20": 0.60,  # Assuming same as standard 2.5 Flash
            # Gemini 2.0 Flash family
            "gemini-2.5-flash-lite": 0.30,
        }

        price_info = model_to_price_per_million.get(model)
        if price_info is None:
            logger.warning(
                f"Model {model} not found in model_to_price_per_million yet. Returning 0.0 to not raise any errors."
            )
            return 0.0

        # For output tokens, we return the base price since output pricing complexity
        # cannot be properly handled without knowing input token count
        if isinstance(price_info, tuple):
            return price_info[0]
        return price_info

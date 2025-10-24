from typing import Literal

from agentle.generations.providers.base.generation_provider import GenerationProvider
from agentle.parsing.parsed_file import ParsedFile
from agentle.parsing.parsers.file_parser import FileParser


async def parse_async(
    document_path: str,
    strategy: Literal["low", "high"] = "high",
    visual_description_provider: GenerationProvider | None = None,
    audio_description_provider: GenerationProvider | None = None,
) -> ParsedFile:
    """
    Asynchronously parse any supported document type into a structured representation.

    This function is the asynchronous version of the main `parse()` function. It serves as
    the core implementation for document parsing in the Agentle framework, automatically
    selecting the appropriate parser based on the file extension and applying the
    requested parsing strategy.

    Args:
        document_path (str): Path to the document file to be parsed. The file extension
            is used to determine which parser to use.

        strategy (Literal["low", "high"], optional): Parsing strategy to use. Defaults to "high".
            - "high": More thorough parsing that may include OCR, image analysis,
                      and other CPU-intensive operations
            - "low": Faster parsing that skips some intensive operations

        visual_description_provider (Agent[VisualMediaDescription] | None, optional):
            Custom agent for analyzing visual content. If provided, this agent will be used
            instead of the default visual description agent. Useful for customizing
            the image analysis behavior. Defaults to None.

        audio_description_provider (Agent[AudioDescription] | None, optional):
            Custom agent for analyzing audio content. If provided, this agent will be used
            instead of the default audio description agent. Useful for customizing
            the audio analysis behavior. Defaults to None.

    Returns:
        ParsedFile: A structured representation of the parsed document with:
            - sections: list of content sections
            - images: extracted images with optional OCR text
            - structured items: headings, tables, and text blocks

    Raises:
        ValueError: If the file extension is not supported by any registered parser

    Examples:
        Parse a PDF document with default settings in an async function:
        ```python
        import asyncio
        from agentle.parsing.parsers.parse_async import parse_async

        async def process_document():
            parsed_doc = await parse_async("document.pdf")
            print(f"Document name: {parsed_doc.name}")

        asyncio.run(process_document())
        ```

        Parse an image with a "low" strategy (faster processing):
        ```python
        async def process_image():
            parsed_image = await parse_async("image.jpg", strategy="low")
            # Process the parsed image...
        ```

        Parse with both custom visual and audio description agents:
        ```python
        from agentle.agents.agent import Agent
        from agentle.generations.models.structured_outputs_store.visual_media_description import VisualMediaDescription
        from agentle.generations.models.structured_outputs_store.audio_description import AudioDescription

        async def process_mixed_media():
            # Create custom agents
            visual_agent = Agent(
                model="gemini-2.0-pro-vision",
                instructions="Describe images with focus on technical details",
                response_schema=VisualMediaDescription,
            )

            audio_agent = Agent(
                model="gemini-2.5-flash",
                instructions="Transcribe and analyze audio with focus on technical terminology",
                response_schema=AudioDescription,
            )

            # Use both custom agents
            parsed_file = await parse_async(
                "presentation.pptx",
                visual_description_provider=visual_agent,
                audio_description_provider=audio_agent
            )
        ```
    """
    if visual_description_provider is None and audio_description_provider is None:
        return await FileParser(
            strategy=strategy,
        ).parse_async(document_path)
    elif visual_description_provider is not None and audio_description_provider is None:
        return await FileParser(
            strategy=strategy,
            visual_description_provider=visual_description_provider,
        ).parse_async(document_path)
    elif visual_description_provider is None and audio_description_provider is not None:
        return await FileParser(
            strategy=strategy,
            audio_description_provider=audio_description_provider,
        ).parse_async(document_path)

    # At this point, both agents must be non-None
    assert visual_description_provider is not None
    assert audio_description_provider is not None
    return await FileParser(
        strategy=strategy,
        visual_description_provider=visual_description_provider,
        audio_description_provider=audio_description_provider,
    ).parse_async(document_path)

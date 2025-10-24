"""
Video File Parser Module

This module provides functionality for parsing video files (MP4) to extract descriptive information
from their visual content.
"""

from pathlib import Path
from typing import Literal

from rsb.functions.ext2mime import ext2mime

from rsb.models.field import Field

from agentle.generations.models.message_parts.file import FilePart
from agentle.generations.models.structured_outputs_store.visual_media_description import (
    VisualMediaDescription,
)
from agentle.generations.providers.base.generation_provider import GenerationProvider
from agentle.parsing.document_parser import DocumentParser
from agentle.parsing.parsed_file import ParsedFile
from agentle.parsing.section_content import SectionContent


class VideoFileParser(DocumentParser):
    """
    Parser for processing video files (MP4 format).

    This parser extracts descriptive information from video files by sending them to a
    visual description agent that can analyze the video content. The agent generates
    a structured description of the video, which is then used to create a ParsedFile.

    Currently, this parser only supports MP4 files and relies on the visual description
    agent to perform the actual analysis of the video content.

    **Attributes:**

    *   `visual_description_agent` (Agent[VisualMediaDescription]):
        The agent used to analyze and describe the video content. This agent should be
        capable of processing video data and generating structured descriptions.
        Defaults to the agent created by `visual_description_agent_default_factory()`.

        **Example:**
        ```python
        from agentle.agents.agent import Agent
        from agentle.generations.models.structured_outputs_store.visual_media_description import VisualMediaDescription

        custom_agent = Agent(
            model="gemini-2.0-pro-vision",
            instructions="Focus on describing movement and actions in videos",
            response_schema=VisualMediaDescription
        )

        parser = VideoFileParser(visual_description_agent=custom_agent)
        ```

    **Usage Examples:**

    Basic parsing of a video file:
    ```python
    from agentle.parsing.parsers.video import VideoFileParser

    # Create a parser with default settings
    parser = VideoFileParser()

    # Parse a video file
    parsed_video = parser.parse("example.mp4")

    # Access the video description
    print(parsed_video.sections[0].text)
    ```

    Using a custom visual description agent:
    ```python
    from agentle.agents.agent import Agent
    from agentle.generations.models.structured_outputs_store.visual_media_description import VisualMediaDescription
    from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider

    # Create a custom agent for specialized video analysis
    sports_video_agent = Agent(
        model="gemini-2.0-pro-vision",
        instructions="Analyze sports videos with focus on player movements and game statistics",
        generation_provider=GoogleGenerationProvider(),
        response_schema=VisualMediaDescription
    )

    # Create a parser with the custom agent
    sports_parser = VideoFileParser(visual_description_agent=sports_video_agent)

    # Parse a sports video
    game_analysis = sports_parser.parse("basketball_game.mp4")
    ```
    """

    type: Literal["video"] = "video"

    visual_description_agent: GenerationProvider = Field(...)
    """
    The agent to use for generating the visual description of the document.
    Useful when you want to customize the prompt for the visual description.
    """

    async def parse_async(self, document_path: str) -> ParsedFile:
        """
        Asynchronously parse a video file and generate a structured description.

        This method reads the video file data, sends it to the visual description agent for
        analysis, and creates a ParsedFile containing the generated description.

        Args:
            document_path (str): Path to the video file to be parsed

        Returns:
            ParsedFile: A structured representation of the parsed video with
                descriptive content in the first section

        Raises:
            ValueError: If the file is not an MP4 file

        Example:
            ```python
            import asyncio
            from agentle.parsing.parsers.video import VideoFileParser

            async def analyze_video():
                parser = VideoFileParser()
                result = await parser.parse_async("tutorial.mp4")
                print(f"Video description: {result.sections[0].text}")

            asyncio.run(analyze_video())
            ```
        """
        path = Path(document_path)
        if not path.exists() or not path.is_file():
            raise ValueError(f"Video file not found: {document_path}")
        suffix = path.suffix.lower()
        ext = suffix.lstrip(".")
        if ext != "mp4":
            raise ValueError(
                f"VideoFileParser only supports .mp4 files (got: {path.suffix or '(none)'})."
            )

        file_contents = path.read_bytes()
        visual_media_description = await self.visual_description_agent.generate_by_prompt_async(
            FilePart(data=file_contents, mime_type=ext2mime(suffix or ".mp4")),
            developer_prompt="You are a helpful assistant that deeply understands visual media.",
            response_schema=VisualMediaDescription,
        )

        return ParsedFile(
            name=path.name,
            sections=[
                SectionContent(
                    number=1,
                    text=visual_media_description.parsed.md,
                    md=visual_media_description.parsed.md,
                    images=[],
                )
            ],
        )

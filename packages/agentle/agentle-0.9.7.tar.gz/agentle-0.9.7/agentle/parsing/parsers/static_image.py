"""
Static Image Parser Module

This module provides functionality for parsing static image files (PNG, JPEG, TIFF, BMP, etc.)
into structured representations. It can extract visual content, perform OCR to identify text,
and generate detailed descriptions of image content.
"""

import io
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
from agentle.parsing.image import Image
from agentle.parsing.parsed_file import ParsedFile
from agentle.parsing.section_content import SectionContent


class StaticImageParser(DocumentParser):
    """
    Parser for processing static image files in various formats.

    This parser handles multiple image formats including PNG, JPEG, TIFF, BMP, and others.
    It uses a visual description agent to analyze image content, extract text via OCR,
    and generate descriptive text about the image contents. For certain formats like TIFF,
    the parser automatically converts the image to a compatible format (PNG) before processing.

    **Attributes:**

    *   `visual_description_agent` (Agent[VisualMediaDescription]):
        The agent used to analyze and describe the image content. This agent is responsible
        for generating descriptions and extracting text via OCR from the image.
        Defaults to the agent created by `visual_description_agent_default_factory()`.

        **Example:**
        ```python
        from agentle.agents.agent import Agent
        from agentle.generations.models.structured_outputs_store.visual_media_description import VisualMediaDescription

        custom_agent = Agent(
            model="gemini-2.0-pro-vision",
            instructions="Analyze images with focus on technical diagrams and charts",
            response_schema=VisualMediaDescription
        )

        parser = StaticImageParser(visual_description_agent=custom_agent)
        ```

    **Usage Examples:**

    Basic parsing of an image file:
    ```python
    from agentle.parsing.parsers.static_image import StaticImageParser

    # Create a parser with default settings
    parser = StaticImageParser()

    # Parse an image file
    parsed_image = parser.parse("photograph.jpg")

    # Access the description and OCR text
    print(f"Image description: {parsed_image.sections[0].text}")

    if parsed_image.sections[0].images[0].ocr_text:
        print(f"Text found in image: {parsed_image.sections[0].images[0].ocr_text}")
    ```

    Using the generic parse function:
    ```python
    from agentle.parsing.parse import parse

    # Parse different image formats
    png_result = parse("diagram.png")
    jpg_result = parse("photo.jpg")
    tiff_result = parse("scan.tiff")

    # All results have the same structure regardless of original format
    for result in [png_result, jpg_result, tiff_result]:
        print(f"Image file: {result.name}")
        print(f"Description: {result.sections[0].text[:100]}...")

        # Access the first (and only) image in the first section
        image = result.sections[0].images[0]
        if image.ocr_text:
            print(f"OCR text: {image.ocr_text}")
    ```
    """

    type: Literal["static_image"] = "static_image"

    visual_description_provider: GenerationProvider = Field(...)
    """
    The agent to use for generating the visual description of the document.
    Useful when you want to customize the prompt for the visual description.
    """

    async def parse_async(self, document_path: str) -> ParsedFile:
        """
        Asynchronously parse a static image file and generate a structured representation.

        This method reads an image file, converts it to a compatible format if necessary
        (e.g., TIFF to PNG), and processes it using a visual description agent to extract
        content and text via OCR.

        Args:
            document_path (str): Path to the image file to be parsed

        Returns:
            ParsedFile: A structured representation where:
                - The image is contained in a single section
                - The section includes the image data and a description
                - OCR text is extracted if text is present in the image

        Example:
            ```python
            import asyncio
            from agentle.parsing.parsers.static_image import StaticImageParser

            async def analyze_image():
                parser = StaticImageParser()
                result = await parser.parse_async("chart.png")

                # Access the image description
                print(f"Image description: {result.sections[0].text}")

                # Access OCR text if available
                image = result.sections[0].images[0]
                if image.ocr_text:
                    print(f"Text in image: {image.ocr_text}")

            asyncio.run(analyze_image())
            ```

        Note:
            For TIFF images, this method automatically converts them to PNG format
            before processing to ensure compatibility with the visual description agent.
        """
        from PIL import Image as PILImage

        path = Path(document_path)
        if not path.exists() or not path.is_file():
            raise ValueError(f"Image file not found: {document_path}")
        file_bytes = path.read_bytes()
        suffix = path.suffix.lower()
        ext = suffix.lstrip(".")

        # Convert to PNG if TIFF
        if ext in {"tiff", "tif"}:
            # Use Pillow to open, then convert to PNG in memory
            with io.BytesIO(file_bytes) as input_buffer:
                with PILImage.open(input_buffer) as pil_img:
                    # Convert to RGBA or RGB if needed
                    if pil_img.mode not in ("RGB", "RGBA"):
                        pil_img = pil_img.convert("RGBA")

                    # Save as PNG into a new buffer
                    output_buffer = io.BytesIO()
                    pil_img.save(output_buffer, format="PNG")
                    converted_bytes = output_buffer.getvalue()
            image_bytes = converted_bytes
            # Converted output is PNG regardless of original
            current_mime_type = "image/png"
        else:
            image_bytes = file_bytes
            if ext in {"png", "bmp"}:
                current_mime_type = f"image/{ext}"
            elif ext in {"jpg", "jpeg"}:
                current_mime_type = "image/jpeg"
            elif ext in {"gif", "webp"}:
                current_mime_type = f"image/{ext}"
            else:
                # Fallback to ext2mime; if it fails, default to octet-stream
                try:
                    current_mime_type = ext2mime(suffix or f".{ext}")
                except Exception:
                    current_mime_type = "application/octet-stream"

        image_ocr: str | None = None
        text_content = ""
        agent_input = FilePart(
            mime_type=current_mime_type,
            data=image_bytes,
        )
        agent_response = await self.visual_description_provider.generate_by_prompt_async(
            agent_input,
            developer_prompt="You are a helpful assistant that deeply understands visual media.",
            response_schema=VisualMediaDescription,
        )
        description_md = agent_response.parsed.md
        image_ocr = agent_response.parsed.ocr_text
        text_content = description_md

        image_obj = Image(name=path.name, contents=image_bytes, ocr_text=image_ocr)
        page_content = SectionContent(
            number=1,
            text=text_content,
            md=text_content,
            images=[image_obj],
        )

        return ParsedFile(
            name=path.name,
            sections=[page_content],
        )

from pathlib import Path
from typing import Literal, cast
from urllib.parse import urlparse

from rsb.functions.create_instance_dynamically import create_instance_dynamically
from rsb.models.field import Field

from agentle.generations.providers.base.generation_provider import GenerationProvider
from agentle.parsing.document_parser import DocumentParser
from agentle.parsing.parsed_file import ParsedFile
from agentle.utils.file_validation import (
    FileValidationError,
    resolve_file_path,
    validate_file_exists,
)
from agentle.utils.file_validation import (
    is_url as is_valid_url,
)


class FileParser(DocumentParser):
    """
    A facade parser that automatically selects the appropriate parser based on file extension.

    The FileParser class acts as a smart entry point to the parsing system, dynamically
    selecting and configuring the appropriate parser based on a document's file extension.
    This eliminates the need for users to know which specific parser to use for each file
    type, making the parsing system much easier to work with.

    FileParser delegates to the specific parser registered for a given file extension,
    passing along appropriate configuration options like the parsing strategy and any
    custom agents for visual or audio content analysis.

    **Attributes:**

    *   `strategy` (Literal["low", "high"]):
        The parsing strategy to use. Defaults to "high".
        - "high": More thorough parsing with intensive operations like OCR and content analysis
        - "low": More efficient parsing that skips some intensive operations

        **Example:**
        ```python
        parser = FileParser(strategy="low")  # Use faster, less intensive parsing
        ```

    *   `visual_description_agent` (Agent[VisualMediaDescription]):
        An optional custom agent for visual media description. If provided, this agent
        will be used instead of the default for analyzing images and visual content.

        **Example:**
        ```python
        from agentle.agents.agent import Agent
        from agentle.generations.models.structured_outputs_store.visual_media_description import VisualMediaDescription

        custom_visual_agent = Agent(
            model="gemini-2.0-pro-vision",
            instructions="Describe technical diagrams with precision",
            response_schema=VisualMediaDescription
        )

        parser = FileParser(visual_description_agent=custom_visual_agent)
        ```

    *   `audio_description_agent` (Agent[AudioDescription]):
        An optional custom agent for audio description. If provided, this agent
        will be used instead of the default for analyzing audio content.

        **Example:**
        ```python
        from agentle.agents.agent import Agent
        from agentle.generations.models.structured_outputs_store.audio_description import AudioDescription

        custom_audio_agent = Agent(
            model="gemini-2.5-flash",
            instructions="Transcribe technical terminology with high accuracy",
            response_schema=AudioDescription
        )

        parser = FileParser(audio_description_agent=custom_audio_agent)
        ```

    **Usage Examples:**

    Basic usage with default settings:
    ```python
    from agentle.parsing.parsers.file_parser import FileParser

    # Create a parser with default settings
    parser = FileParser()

    # Parse different file types with the same parser
    pdf_doc = parser.parse("document.pdf")
    image = parser.parse("diagram.png")
    spreadsheet = parser.parse("data.xlsx")
    ```

    Using different strategies for different files:
    ```python
    # Create parsers with different strategies
    high_detail_parser = FileParser(strategy="high")
    fast_parser = FileParser(strategy="low")

    # Use high detail for important documents
    contract = high_detail_parser.parse("contract.docx")

    # Use fast parsing for initial screening
    screening_results = fast_parser.parse("batch_of_images.zip")
    ```

    Using custom agents:
    ```python
    # Create custom agents for specialized parsing
    technical_visual_agent = Agent(
        model="gemini-2.0-pro-vision",
        instructions="Focus on technical details in diagrams and charts",
        response_schema=VisualMediaDescription
    )

    legal_audio_agent = Agent(
        model="gemini-2.5-flash",
        instructions="Transcribe legal terminology with high accuracy",
        response_schema=AudioDescription
    )

    # Create a parser with custom agents
    specialized_parser = FileParser(
        visual_description_agent=technical_visual_agent,
        audio_description_agent=legal_audio_agent
    )

    # Parse files with specialized agents
    technical_diagram = specialized_parser.parse("circuit_diagram.png")
    legal_recording = specialized_parser.parse("deposition.mp3")
    ```
    """

    type: Literal["file"] = "file"
    strategy: Literal["low", "high"] = Field(default="high")
    visual_description_provider: GenerationProvider | None = Field(
        default=None,
    )
    """
    The agent to use for generating the visual description of the document.
    Useful when you want to customize the prompt for the visual description.
    """

    audio_description_provider: GenerationProvider | None = Field(
        default=None,
    )
    """
    The agent to use for generating the audio description of the document.
    Useful when you want to customize the prompt for the audio description.
    """

    parse_timeout: float = Field(default=30)
    """The timeout for the parse operation in seconds."""

    max_concurrent_provider_tasks: int = Field(default=4)
    """Maximum number of concurrent provider API calls for visual/audio processing.
    
    This controls the concurrency level when making API calls to visual description
    or audio transcription providers. Higher values can speed up processing of
    documents with many images (e.g., PDFs) but may hit rate limits.
    
    Recommended values:
    - 4-7 for most use cases
    - 10+ for documents with many images and high rate limits
    - 1-2 for conservative rate limit compliance
    """

    max_concurrent_pages: int = Field(default=4)
    """Maximum number of PDF pages to process concurrently.
    
    Controls how many pages are processed in parallel during PDF parsing.
    Lower values reduce memory usage and prevent overloading smaller AWS instances.
    
    Recommended values:
    - 1-2 for small AWS instances (t2.micro, t2.small, t3.micro, t3.small)
    - 2-3 for medium instances (t2.medium, t3.medium)
    - 4-6 for large instances (t2.large, t3.large or better)
    - 6-8+ for local development machines with good specs
    
    Note: Total concurrent API calls = max_concurrent_pages × max_concurrent_provider_tasks
    Example: 2 pages × 4 provider tasks = 8 concurrent API calls
    """

    render_scale: float = Field(default=2.0)
    """Rendering scale for PDF page screenshots (PDF parsing only).
    
    Controls the resolution/quality of page screenshots in PDF parsing.
    Higher values produce better quality but use exponentially more memory.
    
    Recommended values:
    - 1.0-1.25 for AWS instances with limited RAM (t2.micro, t2.small, t3.small)
    - 1.5 for medium instances or when memory is constrained
    - 2.0 for large instances or local development (default)
    - 2.5-3.0 for high-quality analysis on powerful machines
    
    Memory impact: render_scale=2.0 can produce 4-8MB screenshots per page
                  render_scale=1.0 produces ~1-2MB screenshots per page
    """

    model: str | None = Field(default=None)
    """Model to use for visual description generation. If not provided, uses the provider's default model."""

    use_native_pdf_processing: bool = Field(default=False)
    """Enable native PDF processing by sending the entire PDF to the AI provider (PDF parsing only).
    
    When enabled for PDF files, the parser will send the complete PDF file directly 
    to the AI provider (if it supports native PDF file processing) and request 
    structured markdown extraction. This completely eliminates backend processing.
    
    Requirements:
    - visual_description_provider must be set
    - The provider must support FilePart with mime_type="application/pdf"
    - Only applies to PDF files (ignored for other file types)
    
    Benefits:
    - No PyMuPDF dependency required for PDFs
    - No memory-intensive screenshot rendering
    - Faster processing as AI handles everything
    - Works well on small AWS instances
    - Ideal for cloud deployments with minimal dependencies
    
    Example:
        ```python
        from agentle.parsing.parsers.file_parser import FileParser
        from agentle.generations.providers.google import GoogleGenerationProvider
        
        provider = GoogleGenerationProvider(api_key="your-key")
        parser = FileParser(
            visual_description_provider=provider,
            use_native_pdf_processing=True  # Let AI handle PDF processing
        )
        
        # PDF will be sent directly to AI, no local processing
        result = parser.parse("document.pdf")
        ```
    
    Note: When enabled, most PDF-specific configuration options (like image_processing_mode,
    render_scale, etc.) are ignored as the AI handles all processing.
    """

    use_native_docx_processing: bool = Field(default=False)
    """Enable native DOCX processing by sending the entire DOCX to the AI provider.
    
    When enabled, the parser will send the complete DOCX file directly to the AI provider
    (if it supports native DOCX file processing) and request structured markdown extraction.
    This completely eliminates backend processing and can run efficiently on AWS instances.
    
    Requirements:
    - visual_description_provider must be set
    - The provider must support FilePart with mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    Benefits:
    - No python-docx dependency required
    - No LibreOffice/pandoc conversion needed
    - Faster processing as AI handles everything
    - Works well on small AWS instances
    
    Note: When this is enabled, most other configuration options are ignored as the AI handles all processing.
    """

    async def parse_async(self, document_path: str) -> ParsedFile:
        """
        Asynchronously parse a document using the appropriate parser for its file type.

        This method examines the file extension of the provided document path, selects
        the appropriate parser for that file type, and delegates the parsing process to
        that specific parser instance. It automatically passes along configuration options
        like the parsing strategy and any custom agents to the selected parser.

        Args:
            document_path (str): Path to the document file to be parsed

        Returns:
            ParsedFile: A structured representation of the parsed document

        Raises:
            ValueError: If the file extension is not supported by any registered parser

        Example:
            ```python
            import asyncio
            from agentle.parsing.parsers.file_parser import FileParser

            async def process_documents():
                parser = FileParser(strategy="high")

                # Parse different document types
                pdf_result = await parser.parse_async("report.pdf")
                image_result = await parser.parse_async("chart.png")
                spreadsheet_result = await parser.parse_async("data.xlsx")

                # Process the parsed results
                for doc in [pdf_result, image_result, spreadsheet_result]:
                    print(f"Document: {doc.name}")
                    print(f"Section count: {len(doc.sections)}")

            asyncio.run(process_documents())
            ```
        """
        from agentle.parsing.parsers.link import LinkParser
        from agentle.parsing.parses import parser_registry

        # Enhanced path validation and resolution
        try:
            # Check if it's a URL first
            if is_valid_url(document_path):
                parser_cls = cast(
                    type[DocumentParser],
                    LinkParser,
                )

                return await create_instance_dynamically(
                    parser_cls,
                    visual_description_provider=self.visual_description_provider,
                    audio_description_provider=self.audio_description_provider,
                    parse_timeout=self.parse_timeout,
                    max_concurrent_provider_tasks=self.max_concurrent_provider_tasks,
                    max_concurrent_pages=self.max_concurrent_pages,
                    render_scale=self.render_scale,
                ).parse_async(document_path=document_path)

            # For file paths, resolve and validate
            resolved_path = resolve_file_path(document_path)
            validate_file_exists(resolved_path)

            # Use resolved path for further processing
            path = Path(resolved_path)

        except FileValidationError as e:
            raise ValueError(
                f"File validation failed for '{document_path}': {e}"
            ) from e

        # Normalize extension to be case-insensitive (e.g., .PDF -> pdf)
        normalized_ext = path.suffix.lstrip(".").lower()
        # Treat legacy .doc the same as .docx (conversion handled in DocxFileParser)
        if normalized_ext == "doc":
            normalized_ext = "docx"
        parser_cls: type[DocumentParser] | None = parser_registry.get(normalized_ext)

        if not parser_cls:
            # Double-check URL handling (fallback)
            parsed_url = urlparse(document_path)
            is_url = parsed_url.scheme in ["http", "https"]

            if is_url:
                parser_cls = cast(
                    type[DocumentParser],
                    LinkParser,
                )

                return await create_instance_dynamically(
                    parser_cls,
                    visual_description_provider=self.visual_description_provider,
                    audio_description_provider=self.audio_description_provider,
                    parse_timeout=self.parse_timeout,
                    max_concurrent_provider_tasks=self.max_concurrent_provider_tasks,
                    max_concurrent_pages=self.max_concurrent_pages,
                    render_scale=self.render_scale,
                ).parse_async(document_path=document_path)
            else:
                raise ValueError(
                    f"Unsupported file extension '{path.suffix}' for file: {resolved_path}"
                )

        return await create_instance_dynamically(
            parser_cls,
            visual_description_provider=self.visual_description_provider,
            audio_description_provider=self.audio_description_provider,
            parse_timeout=self.parse_timeout,
            max_concurrent_provider_tasks=self.max_concurrent_provider_tasks,
            max_concurrent_pages=self.max_concurrent_pages,
            render_scale=self.render_scale,
            use_native_pdf_processing=self.use_native_pdf_processing,
            use_native_docx_processing=self.use_native_docx_processing,
            strategy=self.strategy,
            model=self.model,
        ).parse_async(document_path=str(resolved_path))

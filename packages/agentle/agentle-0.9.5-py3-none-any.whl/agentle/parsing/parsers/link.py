import os
import tempfile
import logging
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from rsb.models.field import Field

from agentle.generations.providers.base.generation_provider import GenerationProvider
from agentle.parsing.document_parser import DocumentParser
from agentle.parsing.parsed_file import ParsedFile
from agentle.parsing.parsers.file_parser import FileParser
from agentle.parsing.section_content import SectionContent

logger = logging.getLogger(__name__)

"""Link parser module."""


class LinkParser(DocumentParser):
    """
    A parser for links.

    This parser handles both URLs and local file paths. For URLs, it uses Playwright
    to fetch the content and render any dynamic elements. For local files, it delegates
    to the appropriate FileParser.
    """

    type: Literal["link"] = "link"
    visual_description_provider: GenerationProvider | None = Field(default=None)
    audio_description_provider: GenerationProvider | None = Field(default=None)
    parse_timeout: float = Field(default=30)

    async def parse_async(self, document_path: str) -> ParsedFile:
        """
        Parse the link.

        Args:
            document_path (str): URL or local file path to parse

        Returns:
            ParsedFile: A structured representation of the parsed content
        """
        # Determine if the document_path is a URL or a local file path
        parsed_url = urlparse(document_path)
        is_url = parsed_url.scheme in ["http", "https"]

        if is_url:
            # Handle URL
            try:
                # We need to import these modules here to avoid dependency issues
                import aiohttp

                timeout = aiohttp.ClientTimeout(total=self.parse_timeout)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    try:
                        async with session.head(
                            document_path, allow_redirects=True
                        ) as response:
                            content_type = response.headers.get("Content-Type", "")
                            content_disposition = response.headers.get(
                                "Content-Disposition", ""
                            )

                            is_downloadable = (
                                # Content types that suggest a file
                                any(
                                    ct in content_type.lower()
                                    for ct in [
                                        "application/",
                                        "audio/",
                                        "video/",
                                        "image/",
                                    ]
                                )
                                or
                                # Content-Disposition header suggesting a file download
                                "attachment" in content_disposition
                                or
                                # Common file extensions in URL path
                                any(
                                    ext in Path(parsed_url.path).suffix.lower()
                                    for ext in [
                                        ".pdf",
                                        ".doc",
                                        ".docx",
                                        ".xls",
                                        ".xlsx",
                                        ".ppt",
                                        ".pptx",
                                        ".zip",
                                        ".rar",
                                        ".txt",
                                        ".csv",
                                        ".json",
                                        ".xml",
                                        ".jpg",
                                        ".jpeg",
                                        ".png",
                                        ".gif",
                                        ".mp3",
                                        ".mp4",
                                        ".avi",
                                        ".mov",
                                    ]
                                )
                            )

                            if is_downloadable:
                                # Download the file
                                return await self._download_and_parse_file(
                                    document_path
                                )
                    except Exception as e:
                        logger.debug(
                            "HEAD request failed for %s (%s); will fallback to GET",
                            document_path,
                            e,
                        )
            except ImportError:
                # If aiohttp is not available, proceed with Playwright
                pass

            # Handle as a web page using Playwright
            return await self._parse_webpage(document_path)

        # Handle local file
        file_parser = FileParser(
            visual_description_provider=self.visual_description_provider,
            audio_description_provider=self.audio_description_provider,
        )
        return await file_parser.parse_async(document_path)

    async def _download_and_parse_file(self, url: str) -> ParsedFile:
        """Download a file from a URL and parse it using the appropriate FileParser."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(urlparse(url).path).suffix
        ) as tmp_file:
            temp_path = tmp_file.name

        try:
            # Import aiohttp here to handle ImportError gracefully
            import aiohttp

            timeout = aiohttp.ClientTimeout(total=self.parse_timeout)
            max_bytes = 50 * 1024 * 1024  # 50MB safety limit
            total = 0
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    with open(temp_path, "wb") as f:
                        while True:
                            chunk = await response.content.read(65536)
                            if not chunk:
                                break
                            total += len(chunk)
                            if total > max_bytes:
                                raise ValueError(
                                    f"Remote file exceeds size limit ({max_bytes} bytes)"
                                )
                            f.write(chunk)

            # Parse the downloaded file
            file_parser = FileParser(
                visual_description_provider=self.visual_description_provider,
                audio_description_provider=self.audio_description_provider,
                parse_timeout=self.parse_timeout,
            )
            parsed_document = await file_parser.parse_async(temp_path)

            # Update the name to reflect the original URL
            original_name = Path(urlparse(url).path).name
            if original_name:
                # Mutate the existing ParsedFile's name (assuming attribute is writable)
                try:
                    parsed_document.name = original_name  # type: ignore[attr-defined]
                except Exception:
                    # Fallback: recreate only if constructor supports it
                    parsed_document = ParsedFile(
                        name=original_name, sections=parsed_document.sections
                    )

            return parsed_document
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    async def _parse_webpage(self, url: str) -> ParsedFile:
        """Parse a webpage using Playwright."""
        # Import playwright here to handle ImportError gracefully
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            # Launch a browser with default viewport size
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                # Go to the URL and wait for the network to be idle
                # This helps ensure dynamic content is loaded
                await page.goto(url, timeout=self.parse_timeout * 1000)

                # Give extra time for JavaScript-heavy pages to finish rendering
                await page.wait_for_timeout(2000)

                # Get the page title
                title = await page.title()

                # Get the page content
                content = await page.content()

                # Get the visible text
                text = await page.evaluate("""() => {
                    return document.body.innerText;
                }""")

                # Create a SectionContent with the parsed data
                section = SectionContent(number=1, text=text, md=f"# {title}\n\n{text}")

                # Create a temporary HTML file for the content
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".html"
                ) as tmp_file:
                    tmp_file.write(content.encode("utf-8"))
                    html_path = tmp_file.name

                try:
                    # Parse the HTML file to get any embedded media
                    file_parser = FileParser(
                        visual_description_provider=self.visual_description_provider,
                        audio_description_provider=self.audio_description_provider,
                        parse_timeout=self.parse_timeout,
                    )
                    html_parsed = await file_parser.parse_async(html_path)

                    # Combine sections if the HTML parser extracted additional information
                    if len(html_parsed.sections) > 0:
                        for i, html_section in enumerate(html_parsed.sections):
                            # If this is the first section, merge it with our main section
                            if i == 0:
                                # Update images and items from the HTML parser
                                section = SectionContent(
                                    number=section.number,
                                    text=section.text,
                                    md=section.md,
                                    images=html_section.images,
                                    items=html_section.items,
                                )
                            # For additional sections, add them as-is
                            else:
                                section = section + html_section
                finally:
                    # Clean up the temporary HTML file
                    if os.path.exists(html_path):
                        os.unlink(html_path)

                # Return the parsed document
                return ParsedFile(
                    name=title or Path(urlparse(url).path).name or "webpage",
                    sections=[section],
                )
            finally:
                # Close the browser
                await browser.close()

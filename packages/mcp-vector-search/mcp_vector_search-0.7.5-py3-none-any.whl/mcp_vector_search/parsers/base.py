"""Base parser interface for MCP Vector Search."""

from abc import ABC, abstractmethod
from pathlib import Path

from ..config.constants import DEFAULT_CHUNK_SIZE
from ..core.models import CodeChunk
from . import utils


class BaseParser(ABC):
    """Abstract base class for language parsers."""

    def __init__(self, language: str) -> None:
        """Initialize parser for a specific language.

        Args:
            language: Programming language name
        """
        self.language = language

    @abstractmethod
    async def parse_file(self, file_path: Path) -> list[CodeChunk]:
        """Parse a file and extract code chunks.

        Args:
            file_path: Path to the file to parse

        Returns:
            List of code chunks extracted from the file
        """
        ...

    @abstractmethod
    async def parse_content(self, content: str, file_path: Path) -> list[CodeChunk]:
        """Parse content and extract code chunks.

        Args:
            content: File content to parse
            file_path: Path to the source file (for metadata)

        Returns:
            List of code chunks extracted from the content
        """
        ...

    def supports_file(self, file_path: Path) -> bool:
        """Check if this parser supports the given file.

        Args:
            file_path: Path to check

        Returns:
            True if this parser can handle the file
        """
        return file_path.suffix.lower() in self.get_supported_extensions()

    @abstractmethod
    def get_supported_extensions(self) -> list[str]:
        """Get list of file extensions supported by this parser.

        Returns:
            List of file extensions (including the dot)
        """
        ...

    def _create_chunk(
        self,
        content: str,
        file_path: Path,
        start_line: int,
        end_line: int,
        chunk_type: str = "code",
        function_name: str | None = None,
        class_name: str | None = None,
        docstring: str | None = None,
    ) -> CodeChunk:
        """Create a code chunk with metadata.

        Args:
            content: Code content
            file_path: Source file path
            start_line: Starting line number (1-based)
            end_line: Ending line number (1-based)
            chunk_type: Type of chunk (code, function, class, etc.)
            function_name: Function name if applicable
            class_name: Class name if applicable
            docstring: Docstring if applicable

        Returns:
            CodeChunk instance
        """
        return CodeChunk(
            content=content.strip(),
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            language=self.language,
            chunk_type=chunk_type,
            function_name=function_name,
            class_name=class_name,
            docstring=docstring,
        )

    def _split_into_lines(self, content: str) -> list[str]:
        """Split content into lines, preserving line endings.

        Args:
            content: Content to split

        Returns:
            List of lines
        """
        return utils.split_into_lines(content)

    def _get_line_range(self, lines: list[str], start_line: int, end_line: int) -> str:
        """Extract a range of lines from content.

        Args:
            lines: List of lines
            start_line: Starting line number (1-based)
            end_line: Ending line number (1-based)

        Returns:
            Content for the specified line range
        """
        return utils.get_line_range(lines, start_line, end_line)


class FallbackParser(BaseParser):
    """Fallback parser for unsupported languages using simple text chunking."""

    def __init__(self, language: str = "text") -> None:
        """Initialize fallback parser."""
        super().__init__(language)

    async def parse_file(self, file_path: Path) -> list[CodeChunk]:
        """Parse file using simple text chunking."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            return await self.parse_content(content, file_path)
        except Exception:
            # Return empty list if file can't be read
            return []

    async def parse_content(self, content: str, file_path: Path) -> list[CodeChunk]:
        """Parse content using simple text chunking."""
        if not content.strip():
            return []

        lines = self._split_into_lines(content)
        chunks = []

        # Simple chunking: split into chunks of ~50 lines
        chunk_size = DEFAULT_CHUNK_SIZE
        for i in range(0, len(lines), chunk_size):
            start_line = i + 1
            end_line = min(i + chunk_size, len(lines))

            chunk_content = self._get_line_range(lines, start_line, end_line)

            if chunk_content.strip():
                chunk = self._create_chunk(
                    content=chunk_content,
                    file_path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    chunk_type="text",
                )
                chunks.append(chunk)

        return chunks

    def get_supported_extensions(self) -> list[str]:
        """Fallback parser supports all extensions."""
        return ["*"]  # Special marker for "all extensions"

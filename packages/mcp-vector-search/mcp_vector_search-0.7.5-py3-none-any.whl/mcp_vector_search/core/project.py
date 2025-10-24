"""Project detection and management for MCP Vector Search."""

import json
from pathlib import Path

from loguru import logger

from ..config.defaults import (
    DEFAULT_FILE_EXTENSIONS,
    DEFAULT_IGNORE_PATTERNS,
    get_default_config_path,
    get_default_index_path,
    get_language_from_extension,
)
from ..config.settings import ProjectConfig
from ..utils.gitignore import create_gitignore_parser
from .exceptions import (
    ConfigurationError,
    ProjectInitializationError,
    ProjectNotFoundError,
)
from .models import ProjectInfo


class ProjectManager:
    """Manages project detection, initialization, and configuration."""

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize project manager.

        Args:
            project_root: Project root directory. If None, will auto-detect.
        """
        self.project_root = project_root or self._detect_project_root()
        self._config: ProjectConfig | None = None

        # Initialize gitignore parser
        try:
            self.gitignore_parser = create_gitignore_parser(self.project_root)
        except Exception as e:
            logger.debug(f"Failed to load gitignore patterns: {e}")
            self.gitignore_parser = None

    def _detect_project_root(self) -> Path:
        """Auto-detect project root directory."""
        current = Path.cwd()

        # Look for common project indicators
        indicators = [
            ".git",
            ".mcp-vector-search",
            "pyproject.toml",
            "package.json",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "build.gradle",
            ".project",
        ]

        # Walk up the directory tree
        for path in [current] + list(current.parents):
            for indicator in indicators:
                if (path / indicator).exists():
                    logger.debug(f"Detected project root: {path} (found {indicator})")
                    return path

        # Default to current directory
        logger.debug(f"Using current directory as project root: {current}")
        return current

    def is_initialized(self) -> bool:
        """Check if project is initialized for MCP Vector Search."""
        config_path = get_default_config_path(self.project_root)
        index_path = get_default_index_path(self.project_root)

        return config_path.exists() and index_path.exists()

    def initialize(
        self,
        file_extensions: list[str] | None = None,
        embedding_model: str = "microsoft/codebert-base",
        similarity_threshold: float = 0.5,
        force: bool = False,
    ) -> ProjectConfig:
        """Initialize project for MCP Vector Search.

        Args:
            file_extensions: File extensions to index
            embedding_model: Embedding model to use
            similarity_threshold: Similarity threshold for search
            force: Force re-initialization if already exists

        Returns:
            Project configuration

        Raises:
            ProjectInitializationError: If initialization fails
        """
        if self.is_initialized() and not force:
            raise ProjectInitializationError(
                f"Project already initialized at {self.project_root}. Use --force to re-initialize."
            )

        try:
            # Create index directory
            index_path = get_default_index_path(self.project_root)
            index_path.mkdir(parents=True, exist_ok=True)

            # Detect languages and files
            detected_languages = self.detect_languages()
            file_count = self.count_indexable_files(
                file_extensions or DEFAULT_FILE_EXTENSIONS
            )

            # Create configuration
            config = ProjectConfig(
                project_root=self.project_root,
                index_path=index_path,
                file_extensions=file_extensions or DEFAULT_FILE_EXTENSIONS,
                embedding_model=embedding_model,
                similarity_threshold=similarity_threshold,
                languages=detected_languages,
            )

            # Save configuration
            self.save_config(config)

            logger.info(
                f"Initialized project at {self.project_root}",
                languages=detected_languages,
                file_count=file_count,
                extensions=config.file_extensions,
            )

            self._config = config
            return config

        except Exception as e:
            raise ProjectInitializationError(
                f"Failed to initialize project: {e}"
            ) from e

    def load_config(self) -> ProjectConfig:
        """Load project configuration.

        Returns:
            Project configuration

        Raises:
            ProjectNotFoundError: If project is not initialized
            ConfigurationError: If configuration is invalid
        """
        if not self.is_initialized():
            raise ProjectNotFoundError(
                f"Project not initialized at {self.project_root}. Run 'mcp-vector-search init' first."
            )

        config_path = get_default_config_path(self.project_root)

        try:
            with open(config_path) as f:
                config_data = json.load(f)

            # Convert paths back to Path objects
            config_data["project_root"] = Path(config_data["project_root"])
            config_data["index_path"] = Path(config_data["index_path"])

            config = ProjectConfig(**config_data)
            self._config = config
            return config

        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}") from e

    def save_config(self, config: ProjectConfig) -> None:
        """Save project configuration.

        Args:
            config: Project configuration to save

        Raises:
            ConfigurationError: If saving fails
        """
        config_path = get_default_config_path(self.project_root)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Convert to JSON-serializable format
            config_data = config.model_dump()
            config_data["project_root"] = str(config.project_root)
            config_data["index_path"] = str(config.index_path)

            with open(config_path, "w") as f:
                json.dump(config_data, f, indent=2)

            logger.debug(f"Saved configuration to {config_path}")

        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {e}") from e

    @property
    def config(self) -> ProjectConfig:
        """Get project configuration, loading if necessary."""
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def detect_languages(self) -> list[str]:
        """Detect programming languages in the project.

        Returns:
            List of detected language names
        """
        languages: set[str] = set()

        for file_path in self._iter_source_files():
            language = get_language_from_extension(file_path.suffix)
            if language != "text":
                languages.add(language)

        return sorted(languages)

    def count_indexable_files(self, extensions: list[str]) -> int:
        """Count files that can be indexed.

        Args:
            extensions: File extensions to count

        Returns:
            Number of indexable files
        """
        count = 0
        for file_path in self._iter_source_files():
            if file_path.suffix in extensions:
                count += 1
        return count

    def get_project_info(self) -> ProjectInfo:
        """Get comprehensive project information.

        Returns:
            Project information
        """
        config_path = get_default_config_path(self.project_root)
        index_path = get_default_index_path(self.project_root)

        is_initialized = self.is_initialized()
        languages = []
        file_count = 0

        if is_initialized:
            try:
                config = self.config
                languages = config.languages
                file_count = self.count_indexable_files(config.file_extensions)
            except Exception:
                # Ignore errors when getting detailed info
                pass

        return ProjectInfo(
            name=self.project_root.name,
            root_path=self.project_root,
            config_path=config_path,
            index_path=index_path,
            is_initialized=is_initialized,
            languages=languages,
            file_count=file_count,
        )

    def _iter_source_files(self) -> list[Path]:
        """Iterate over source files in the project.

        Returns:
            List of source file paths
        """
        files = []

        for path in self.project_root.rglob("*"):
            if not path.is_file():
                continue

            # Skip ignored patterns
            if self._should_ignore_path(path):
                continue

            files.append(path)

        return files

    def _should_ignore_path(self, path: Path) -> bool:
        """Check if a path should be ignored.

        Args:
            path: Path to check

        Returns:
            True if path should be ignored
        """
        # First check gitignore rules if available
        if self.gitignore_parser and self.gitignore_parser.is_ignored(path):
            return True

        # Check if any parent directory is in ignore patterns
        for part in path.parts:
            if part in DEFAULT_IGNORE_PATTERNS:
                return True

        # Check relative path from project root
        try:
            relative_path = path.relative_to(self.project_root)
            for part in relative_path.parts:
                if part in DEFAULT_IGNORE_PATTERNS:
                    return True
        except ValueError:
            # Path is not relative to project root
            return True

        return False

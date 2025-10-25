"""Pure domain value objects and DTOs."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum, IntEnum, StrEnum
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel


class SourceType(IntEnum):
    """The type of source."""

    UNKNOWN = 0
    FOLDER = 1
    GIT = 2


class SnippetContentType(StrEnum):
    """Type of snippet content."""

    UNKNOWN = "unknown"
    ORIGINAL = "original"
    SUMMARY = "summary"


class EnrichmentType(StrEnum):
    """Type of enrichment."""

    UNKNOWN = "unknown"
    SUMMARIZATION = "summarization"


@dataclass(frozen=True)
class Enrichment:
    """Enrichment domain value object."""

    type: EnrichmentType
    content: str


class SnippetContent(BaseModel):
    """Snippet content domain value object."""

    type: SnippetContentType
    value: str


class SnippetSearchResult(BaseModel):
    """Domain result object for snippet searches."""

    snippet_id: int
    content: str
    summary: str
    score: float
    file_path: Path
    language: str | None = None
    authors: list[str] = []


@dataclass(frozen=True)
class LanguageExtensions:
    """Value object for language to file extension mappings."""

    language: str
    extensions: list[str]

    @classmethod
    def get_supported_languages(cls) -> list[str]:
        """Get all supported programming languages."""
        return [
            "python",
            "javascript",
            "typescript",
            "java",
            "c",
            "cpp",
            "csharp",
            "go",
            "rust",
            "php",
            "ruby",
            "swift",
            "kotlin",
            "scala",
            "r",
            "sql",
            "html",
            "css",
            "json",
            "yaml",
            "xml",
            "markdown",
            "shell",
        ]

    @classmethod
    def get_extensions_for_language(cls, language: str) -> list[str]:
        """Get file extensions for a given language."""
        language_map = {
            "python": [".py", ".pyw", ".pyi"],
            "javascript": [".js", ".jsx", ".mjs"],
            "typescript": [".ts", ".tsx"],
            "java": [".java"],
            "c": [".c", ".h"],
            "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".hxx"],
            "csharp": [".cs"],
            "go": [".go"],
            "rust": [".rs"],
            "php": [".php"],
            "ruby": [".rb"],
            "swift": [".swift"],
            "kotlin": [".kt", ".kts"],
            "scala": [".scala", ".sc"],
            "r": [".r", ".R"],
            "sql": [".sql"],
            "html": [".html", ".htm"],
            "css": [".css", ".scss", ".sass", ".less"],
            "json": [".json"],
            "yaml": [".yaml", ".yml"],
            "xml": [".xml"],
            "markdown": [".md", ".markdown"],
            "shell": [".sh", ".bash", ".zsh", ".fish"],
        }
        return language_map.get(language.lower(), [])

    @classmethod
    def is_supported_language(cls, language: str) -> bool:
        """Check if a language is supported."""
        return language.lower() in cls.get_supported_languages()

    @classmethod
    def get_extensions_or_fallback(cls, language: str) -> list[str]:
        """Get extensions for language or return language as extension if not found."""
        language_lower = language.lower()
        if cls.is_supported_language(language_lower):
            return cls.get_extensions_for_language(language_lower)
        return [language_lower]


class SearchType(Enum):
    """Type of search to perform."""

    BM25 = "bm25"
    VECTOR = "vector"
    HYBRID = "hybrid"


@dataclass
class Document:
    """Generic document model for indexing."""

    snippet_id: str
    text: str


@dataclass
class DocumentSearchResult:
    """Generic document search result model."""

    snippet_id: str
    score: float


@dataclass
class SearchResult:
    """Generic search result model."""

    snippet_id: str
    score: float


@dataclass
class IndexRequest:
    """Generic indexing request."""

    documents: list[Document]


@dataclass
class SearchRequest:
    """Generic search request (single query string)."""

    query: str
    top_k: int = 10
    snippet_ids: list[str] | None = None


@dataclass
class DeleteRequest:
    """Generic deletion request."""

    snippet_ids: list[str]


@dataclass
class IndexResult:
    """Generic indexing result."""

    snippet_id: str


@dataclass(frozen=True)
class SnippetSearchFilters:
    """Value object for filtering snippet search results."""

    language: str | None = None
    author: str | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None
    source_repo: str | None = None
    file_path: str | None = None

    @classmethod
    def from_cli_params(
        cls,
        language: str | None = None,
        author: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        source_repo: str | None = None,
    ) -> "SnippetSearchFilters | None":
        """Create SnippetSearchFilters from CLI parameters.

        Args:
            language: Programming language filter (e.g., python, go, javascript)
            author: Author name filter
            created_after: Date string in YYYY-MM-DD format for filtering snippets
            created after
            created_before: Date string in YYYY-MM-DD format for filtering snippets
            created before
            source_repo: Source repository filter (e.g., github.com/example/repo)

        Returns:
            SnippetSearchFilters instance if any filters are provided, None otherwise

        Raises:
            ValueError: If date strings are in invalid format

        """
        # Only create filters if at least one parameter is provided
        if not any([language, author, created_after, created_before, source_repo]):
            return None

        # Parse date strings if provided
        parsed_created_after = None
        if created_after:
            try:
                parsed_created_after = datetime.fromisoformat(created_after)
            except ValueError as e:
                raise ValueError(
                    f"Invalid date format for created_after: {created_after}. "
                    "Expected ISO 8601 format (YYYY-MM-DD)"
                ) from e

        parsed_created_before = None
        if created_before:
            try:
                parsed_created_before = datetime.fromisoformat(created_before)
            except ValueError as e:
                raise ValueError(
                    f"Invalid date format for created_before: {created_before}. "
                    "Expected ISO 8601 format (YYYY-MM-DD)"
                ) from e

        return cls(
            language=language,
            author=author,
            created_after=parsed_created_after,
            created_before=parsed_created_before,
            source_repo=source_repo,
        )


@dataclass
class MultiSearchRequest:
    """Domain model for multi-modal search request."""

    top_k: int = 10
    text_query: str | None = None
    code_query: str | None = None
    keywords: list[str] | None = None
    filters: SnippetSearchFilters | None = None


@dataclass
class FusionRequest:
    """Domain model for fusion request."""

    id: str
    score: float


@dataclass
class FusionResult:
    """Domain model for fusion result."""

    id: str
    score: float
    original_scores: list[float]


@dataclass
class IndexCreateRequest:
    """Domain model for index creation request."""

    source_id: int


@dataclass
class IndexRunRequest:
    """Domain model for index run request."""

    index_id: int


@dataclass
class ProgressState:
    """Progress state."""

    current: int = 0
    total: int = 0
    operation: str = ""
    message: str = ""

    @property
    def percentage(self) -> float:
        """Calculate the percentage of completion."""
        return (self.current / self.total) * 100 if self.total > 0 else 0.0


@dataclass
class EmbeddingRequest:
    """Domain model for embedding request."""

    snippet_id: str
    text: str


@dataclass
class EmbeddingResponse:
    """Domain model for embedding response."""

    snippet_id: str
    embedding: list[float]


@dataclass
class IndexView:
    """Domain model for index information."""

    id: int
    created_at: datetime
    num_snippets: int
    updated_at: datetime | None = None
    source: str | None = None


class LanguageMapping:
    """Value object for language-to-extension mappings.

    This encapsulates the domain knowledge of programming languages and their
    associated file extensions. It provides bidirectional mapping capabilities
    and is designed to be immutable and reusable across the application.
    """

    # Comprehensive mapping of language names to their file extensions
    _LANGUAGE_TO_EXTENSIONS: ClassVar[dict[str, list[str]]] = {
        "python": ["py", "pyw", "pyx", "pxd"],
        "go": ["go"],
        "javascript": ["js", "jsx", "mjs"],
        "typescript": ["ts", "tsx"],
        "java": ["java"],
        "csharp": ["cs"],
        "cpp": ["cpp", "cc", "cxx", "hpp"],
        "c": ["c", "h"],
        "rust": ["rs"],
        "php": ["php"],
        "ruby": ["rb"],
        "swift": ["swift"],
        "kotlin": ["kt", "kts"],
        "scala": ["scala"],
        "r": ["r", "R"],
        "matlab": ["m"],
        "perl": ["pl", "pm"],
        "bash": ["sh", "bash"],
        "powershell": ["ps1"],
        "sql": ["sql"],
        "html": ["html", "htm"],
        "css": ["css", "scss", "sass"],
        "yaml": ["yml", "yaml"],
        "json": ["json"],
        "xml": ["xml"],
        "markdown": ["md", "markdown"],
    }

    @classmethod
    def get_extensions_for_language(cls, language: str) -> list[str]:
        """Get file extensions for a given language.

        Args:
            language: The programming language name (case-insensitive)

        Returns:
            List of file extensions (without leading dots) for the language

        Raises:
            ValueError: If the language is not supported

        """
        language_lower = language.lower()
        extensions = cls._LANGUAGE_TO_EXTENSIONS.get(language_lower)

        if extensions is None:
            raise ValueError(f"Unsupported language: {language}")

        return extensions.copy()  # Return a copy to prevent modification

    @classmethod
    def get_language_for_extension(cls, extension: str) -> str:
        """Get language for a given file extension.

        Args:
            extension: The file extension (with or without leading dot)

        Returns:
            The programming language name

        Raises:
            ValueError: If the extension is not supported

        """
        # Remove leading dot if present
        ext_clean = extension.removeprefix(".").lower()

        # Search through all languages to find matching extension
        for language, extensions in cls._LANGUAGE_TO_EXTENSIONS.items():
            if ext_clean in extensions:
                return language

        raise ValueError(f"Unsupported file extension: {extension}")

    @classmethod
    def get_extension_to_language_map(cls) -> dict[str, str]:
        """Get a mapping from file extensions to language names.

        Returns:
            Dictionary mapping file extensions (without leading dots) to language names

        """
        extension_map = {}
        for language, extensions in cls._LANGUAGE_TO_EXTENSIONS.items():
            for extension in extensions:
                extension_map[extension] = language
        return extension_map

    @classmethod
    def get_supported_languages(cls) -> list[str]:
        """Get list of all supported programming languages.

        Returns:
            List of supported language names

        """
        return list(cls._LANGUAGE_TO_EXTENSIONS.keys())

    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        """Get list of all supported file extensions.

        Returns:
            List of supported file extensions (without leading dots)

        """
        extensions = []
        for ext_list in cls._LANGUAGE_TO_EXTENSIONS.values():
            extensions.extend(ext_list)
        return extensions

    @classmethod
    def is_supported_language(cls, language: str) -> bool:
        """Check if a language is supported.

        Args:
            language: The programming language name (case-insensitive)

        Returns:
            True if the language is supported, False otherwise

        """
        return language.lower() in cls._LANGUAGE_TO_EXTENSIONS

    @classmethod
    def is_supported_extension(cls, extension: str) -> bool:
        """Check if a file extension is supported.

        Args:
            extension: The file extension (with or without leading dot)

        Returns:
            True if the extension is supported, False otherwise

        """
        try:
            cls.get_language_for_extension(extension)
        except ValueError:
            return False
        return True

    @classmethod
    def get_extensions_with_fallback(cls, language: str) -> list[str]:
        """Get file extensions for a language, falling back to passed language name.

        Args:
            language: The programming language name (case-insensitive)

        Returns:
            List of file extensions (without leading dots) for the language, or
            [language.lower()] if not found.

        """
        language_lower = language.lower()
        if cls.is_supported_language(language_lower):
            return cls.get_extensions_for_language(language_lower)
        return [language_lower]


class SnippetQuery(BaseModel):
    """Domain query object for snippet searches."""

    text: str
    search_type: SearchType = SearchType.HYBRID
    filters: SnippetSearchFilters = SnippetSearchFilters()
    top_k: int = 10


class FileProcessingStatus(IntEnum):
    """File processing status."""

    CLEAN = 0
    ADDED = 1
    MODIFIED = 2
    DELETED = 3


@dataclass
class FunctionDefinition:
    """Cached function definition."""

    name: str
    qualified_name: str
    start_byte: int
    end_byte: int


class QueuePriority(IntEnum):
    """Queue priority."""

    BACKGROUND = 10
    NORMAL = 20
    USER_INITIATED = 50


class ReportingState(StrEnum):
    """Reporting state."""

    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

    @staticmethod
    def is_terminal(state: "ReportingState") -> bool:
        """Check if a state is completed."""
        return state in [
            ReportingState.COMPLETED,
            ReportingState.FAILED,
            ReportingState.SKIPPED,
        ]


class TrackableType(StrEnum):
    """Trackable type."""

    INDEX = "indexes"
    KODIT_REPOSITORY = "kodit.repository"
    KODIT_COMMIT = "kodit.commit"


class TaskOperation(StrEnum):
    """Task operation."""

    ROOT = "kodit.root"
    CREATE_INDEX = "kodit.index.create"
    RUN_INDEX = "kodit.index.run"
    REFRESH_WORKING_COPY = "kodit.index.run.refresh_working_copy"
    DELETE_OLD_SNIPPETS = "kodit.index.run.delete_old_snippets"
    EXTRACT_SNIPPETS = "kodit.index.run.extract_snippets"
    CREATE_BM25_INDEX = "kodit.index.run.create_bm25_index"
    CREATE_CODE_EMBEDDINGS = "kodit.index.run.create_code_embeddings"
    ENRICH_SNIPPETS = "kodit.index.run.enrich_snippets"
    CREATE_TEXT_EMBEDDINGS = "kodit.index.run.create_text_embeddings"
    UPDATE_INDEX_TIMESTAMP = "kodit.index.run.update_index_timestamp"
    CLEAR_FILE_PROCESSING_STATUSES = "kodit.index.run.clear_file_processing_statuses"

    # New commit-based workflow
    KODIT_REPOSITORY = "kodit.repository"
    CREATE_REPOSITORY = "kodit.repository.create"
    DELETE_REPOSITORY = "kodit.repository.delete"
    CLONE_REPOSITORY = "kodit.repository.clone"
    SCAN_REPOSITORY = "kodit.repository.scan"
    KODIT_COMMIT = "kodit.commit"
    EXTRACT_SNIPPETS_FOR_COMMIT = "kodit.commit.extract_snippets"
    CREATE_BM25_INDEX_FOR_COMMIT = "kodit.commit.create_bm25_index"
    CREATE_CODE_EMBEDDINGS_FOR_COMMIT = "kodit.commit.create_code_embeddings"
    CREATE_SUMMARY_ENRICHMENT_FOR_COMMIT = "kodit.commit.create_summary_enrichment"
    CREATE_SUMMARY_EMBEDDINGS_FOR_COMMIT = "kodit.commit.create_summary_embeddings"
    CREATE_ARCHITECTURE_ENRICHMENT_FOR_COMMIT = (
        "kodit.commit.create_architecture_enrichment"
    )
    CREATE_PUBLIC_API_DOCS_FOR_COMMIT = "kodit.commit.create_public_api_docs"

    def is_repository_operation(self) -> bool:
        """Check if the task operation is a repository operation."""
        return self.startswith("kodit.repository.")

    def is_commit_operation(self) -> bool:
        """Check if the task operation is a commit operation."""
        return self.startswith("kodit.commit.")


class PrescribedOperations:
    """Prescribed common operations."""

    CREATE_NEW_REPOSITORY: ClassVar[list[TaskOperation]] = [
        TaskOperation.CLONE_REPOSITORY,
        TaskOperation.SCAN_REPOSITORY,
    ]
    INDEX_COMMIT: ClassVar[list[TaskOperation]] = [
        TaskOperation.EXTRACT_SNIPPETS_FOR_COMMIT,
        TaskOperation.CREATE_BM25_INDEX_FOR_COMMIT,
        TaskOperation.CREATE_CODE_EMBEDDINGS_FOR_COMMIT,
        TaskOperation.CREATE_SUMMARY_ENRICHMENT_FOR_COMMIT,
        TaskOperation.CREATE_SUMMARY_EMBEDDINGS_FOR_COMMIT,
        TaskOperation.CREATE_ARCHITECTURE_ENRICHMENT_FOR_COMMIT,
        TaskOperation.CREATE_PUBLIC_API_DOCS_FOR_COMMIT,
    ]
    SYNC_REPOSITORY: ClassVar[list[TaskOperation]] = [
        TaskOperation.SCAN_REPOSITORY,
    ]


class IndexStatus(StrEnum):
    """Status of commit indexing."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

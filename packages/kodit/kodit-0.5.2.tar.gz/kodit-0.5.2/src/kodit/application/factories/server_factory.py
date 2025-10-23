"""Create a big object that contains all the application services."""

from collections.abc import Callable
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from kodit.application.factories.reporting_factory import create_server_operation
from kodit.application.services.code_search_application_service import (
    CodeSearchApplicationService,
)
from kodit.application.services.commit_indexing_application_service import (
    CommitIndexingApplicationService,
)
from kodit.application.services.enrichment_query_service import (
    EnrichmentQueryService,
)
from kodit.application.services.queue_service import QueueService
from kodit.application.services.reporting import ProgressTracker
from kodit.application.services.sync_scheduler import SyncSchedulerService
from kodit.config import AppContext
from kodit.domain.enrichments.architecture.physical.formatter import (
    PhysicalArchitectureFormatter,
)
from kodit.domain.enrichments.enricher import Enricher
from kodit.domain.protocols import (
    FusionService,
    GitAdapter,
    GitBranchRepository,
    GitCommitRepository,
    GitRepoRepository,
    GitTagRepository,
    SnippetRepositoryV2,
    TaskStatusRepository,
)
from kodit.domain.services.bm25_service import BM25DomainService, BM25Repository
from kodit.domain.services.embedding_service import EmbeddingDomainService
from kodit.domain.services.git_repository_service import (
    GitRepositoryScanner,
    RepositoryCloner,
)
from kodit.domain.services.physical_architecture_service import (
    PhysicalArchitectureService,
)
from kodit.domain.tracking.resolution_service import TrackableResolutionService
from kodit.infrastructure.bm25.local_bm25_repository import LocalBM25Repository
from kodit.infrastructure.bm25.vectorchord_bm25_repository import (
    VectorChordBM25Repository,
)
from kodit.infrastructure.cloning.git.git_python_adaptor import GitPythonAdapter
from kodit.infrastructure.embedding.embedding_factory import (
    embedding_domain_service_factory,
)
from kodit.infrastructure.enricher.enricher_factory import (
    enricher_domain_service_factory,
)

# InMemoryGitTagRepository removed - now handled by InMemoryGitRepoRepository
from kodit.infrastructure.indexing.fusion_service import ReciprocalRankFusionService
from kodit.infrastructure.physical_architecture.formatters.narrative_formatter import (
    NarrativeFormatter,
)
from kodit.infrastructure.slicing.slicer import Slicer
from kodit.infrastructure.sqlalchemy.embedding_repository import (
    SqlAlchemyEmbeddingRepository,
    create_embedding_repository,
)
from kodit.infrastructure.sqlalchemy.enrichment_v2_repository import (
    EnrichmentV2Repository,
)
from kodit.infrastructure.sqlalchemy.git_branch_repository import (
    create_git_branch_repository,
)
from kodit.infrastructure.sqlalchemy.git_commit_repository import (
    create_git_commit_repository,
)
from kodit.infrastructure.sqlalchemy.git_repository import create_git_repo_repository
from kodit.infrastructure.sqlalchemy.git_tag_repository import (
    create_git_tag_repository,
)
from kodit.infrastructure.sqlalchemy.snippet_v2_repository import (
    create_snippet_v2_repository,
)
from kodit.infrastructure.sqlalchemy.task_status_repository import (
    create_task_status_repository,
)
from kodit.infrastructure.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork

if TYPE_CHECKING:
    from kodit.domain.services.enrichment_service import EnrichmentDomainService


class ServerFactory:
    """Factory for creating server application services."""

    def __init__(
        self,
        app_context: AppContext,
        session_factory: Callable[[], AsyncSession],
    ) -> None:
        """Initialize the ServerFactory."""
        self.app_context = app_context
        self.session_factory = session_factory
        self._repo_repository: GitRepoRepository | None = None
        self._snippet_v2_repository: SnippetRepositoryV2 | None = None
        self._git_adapter: GitAdapter | None = None
        self._scanner: GitRepositoryScanner | None = None
        self._cloner: RepositoryCloner | None = None
        self._commit_indexing_application_service: (
            CommitIndexingApplicationService | None
        ) = None
        self._enrichment_service: EnrichmentDomainService | None = None
        self._enricher_service: Enricher | None = None
        self._task_status_repository: TaskStatusRepository | None = None
        self._operation: ProgressTracker | None = None
        self._queue_service: QueueService | None = None
        self._slicer: Slicer | None = None
        self._bm25_service: BM25DomainService | None = None
        self._bm25_repository: BM25Repository | None = None
        self._code_search_service: EmbeddingDomainService | None = None
        self._text_search_service: EmbeddingDomainService | None = None
        self._sync_scheduler_service: SyncSchedulerService | None = None
        self._embedding_repository: SqlAlchemyEmbeddingRepository | None = None
        self._fusion_service: FusionService | None = None
        self._code_search_application_service: CodeSearchApplicationService | None = (
            None
        )
        self._git_commit_repository: GitCommitRepository | None = None
        self._git_branch_repository: GitBranchRepository | None = None
        self._git_tag_repository: GitTagRepository | None = None
        self._architecture_service: PhysicalArchitectureService | None = None
        self._enrichment_v2_repository: EnrichmentV2Repository | None = None
        self._architecture_formatter: PhysicalArchitectureFormatter | None = None
        self._trackable_resolution_service: TrackableResolutionService | None = None
        self._enrichment_query_service: EnrichmentQueryService | None = None

    def architecture_formatter(self) -> PhysicalArchitectureFormatter:
        """Create a PhysicalArchitectureFormatter instance."""
        if not self._architecture_formatter:
            self._architecture_formatter = NarrativeFormatter()
        return self._architecture_formatter

    def architecture_service(self) -> PhysicalArchitectureService:
        """Create a PhysicalArchitectureService instance."""
        if not self._architecture_service:
            self._architecture_service = PhysicalArchitectureService(
                formatter=self.architecture_formatter()
            )
        return self._architecture_service

    def enrichment_v2_repository(self) -> EnrichmentV2Repository:
        """Create a EnrichmentV2Repository instance."""
        if not self._enrichment_v2_repository:
            self._enrichment_v2_repository = EnrichmentV2Repository(
                session_factory=self.session_factory
            )
        return self._enrichment_v2_repository

    def queue_service(self) -> QueueService:
        """Create a QueueService instance."""
        if not self._queue_service:
            self._queue_service = QueueService(session_factory=self.session_factory)
        return self._queue_service

    def task_status_repository(self) -> TaskStatusRepository:
        """Create a TaskStatusRepository instance."""
        if not self._task_status_repository:
            self._task_status_repository = create_task_status_repository(
                session_factory=self.session_factory
            )
        return self._task_status_repository

    def operation(self) -> ProgressTracker:
        """Create a ProgressTracker instance."""
        if not self._operation:
            self._operation = create_server_operation(
                task_status_repository=self.task_status_repository()
            )
        return self._operation

    def slicer(self) -> Slicer:
        """Create a Slicer instance."""
        if not self._slicer:
            self._slicer = Slicer()
        return self._slicer

    def bm25_repository(self) -> BM25Repository:
        """Create a BM25Repository instance."""
        if not self._bm25_repository:
            if self.app_context.default_search.provider == "vectorchord":
                self._bm25_repository = VectorChordBM25Repository(
                    session_factory=self.session_factory
                )
            else:
                self._bm25_repository = LocalBM25Repository(
                    data_dir=self.app_context.get_data_dir()
                )
        return self._bm25_repository

    def bm25_service(self) -> BM25DomainService:
        """Create a BM25DomainService instance."""
        if not self._bm25_service:
            self._bm25_service = BM25DomainService(repository=self.bm25_repository())
        return self._bm25_service

    def code_search_service(self) -> EmbeddingDomainService:
        """Create a EmbeddingDomainService instance."""
        if not self._code_search_service:
            self._code_search_service = embedding_domain_service_factory(
                "code", self.app_context, self.session_factory
            )
        return self._code_search_service

    def text_search_service(self) -> EmbeddingDomainService:
        """Create a EmbeddingDomainService instance."""
        if not self._text_search_service:
            self._text_search_service = embedding_domain_service_factory(
                "text", self.app_context, self.session_factory
            )
        return self._text_search_service

    def commit_indexing_application_service(self) -> CommitIndexingApplicationService:
        """Create a CommitIndexingApplicationService instance."""
        if not self._commit_indexing_application_service:
            self._commit_indexing_application_service = (
                CommitIndexingApplicationService(
                    snippet_v2_repository=self.snippet_v2_repository(),
                    repo_repository=self.repo_repository(),
                    git_commit_repository=self.git_commit_repository(),
                    git_branch_repository=self.git_branch_repository(),
                    git_tag_repository=self.git_tag_repository(),
                    operation=self.operation(),
                    scanner=self.scanner(),
                    cloner=self.cloner(),
                    snippet_repository=self.snippet_v2_repository(),
                    slicer=self.slicer(),
                    queue=self.queue_service(),
                    bm25_service=self.bm25_service(),
                    code_search_service=self.code_search_service(),
                    text_search_service=self.text_search_service(),
                    embedding_repository=self.embedding_repository(),
                    architecture_service=self.architecture_service(),
                    enrichment_v2_repository=self.enrichment_v2_repository(),
                    enricher_service=self.enricher(),
                )
            )

        return self._commit_indexing_application_service

    def unit_of_work(self) -> SqlAlchemyUnitOfWork:
        """Create a SqlAlchemyUnitOfWork instance."""
        return SqlAlchemyUnitOfWork(session_factory=self.session_factory)

    def repo_repository(self) -> GitRepoRepository:
        """Create a GitRepoRepository instance."""
        if not self._repo_repository:
            self._repo_repository = create_git_repo_repository(
                session_factory=self.session_factory
            )
        return self._repo_repository

    # branch_repository and commit_repository removed - now handled by repo_repository
    # as GitRepo is the aggregate root

    def git_adapter(self) -> GitAdapter:
        """Create a GitAdapter instance."""
        if not self._git_adapter:
            self._git_adapter = GitPythonAdapter()
        return self._git_adapter

    # tag_repository removed - now handled by repo_repository

    def scanner(self) -> GitRepositoryScanner:
        """Create a GitRepositoryScanner instance."""
        if not self._scanner:
            self._scanner = GitRepositoryScanner(self.git_adapter())
        return self._scanner

    def cloner(self) -> RepositoryCloner:
        """Create a RepositoryCloner instance."""
        if not self._cloner:
            self._cloner = RepositoryCloner(
                self.git_adapter(), self.app_context.get_clone_dir()
            )
        return self._cloner

    def snippet_v2_repository(self) -> SnippetRepositoryV2:
        """Create a SnippetRepositoryV2 instance."""
        if not self._snippet_v2_repository:
            self._snippet_v2_repository = create_snippet_v2_repository(
                session_factory=self.session_factory
            )
        return self._snippet_v2_repository

    def enricher(self) -> Enricher:
        """Create a EnricherDomainService instance."""
        if not self._enricher_service:
            self._enricher_service = enricher_domain_service_factory(self.app_context)
        return self._enricher_service

    def sync_scheduler_service(self) -> SyncSchedulerService:
        """Create a SyncSchedulerService instance."""
        if not self._sync_scheduler_service:
            self._sync_scheduler_service = SyncSchedulerService(
                queue_service=self.queue_service(),
                repo_repository=self.repo_repository(),
            )
        return self._sync_scheduler_service

    def embedding_repository(self) -> SqlAlchemyEmbeddingRepository:
        """Create a SqlAlchemyEmbeddingRepository instance."""
        if not self._embedding_repository:
            self._embedding_repository = create_embedding_repository(
                session_factory=self.session_factory
            )
        return self._embedding_repository

    def fusion_service(self) -> FusionService:
        """Create a FusionService instance."""
        if not self._fusion_service:
            self._fusion_service = ReciprocalRankFusionService()
        return self._fusion_service

    def code_search_application_service(self) -> CodeSearchApplicationService:
        """Create a CodeSearchApplicationService instance."""
        if not self._code_search_application_service:
            self._code_search_application_service = CodeSearchApplicationService(
                bm25_service=self.bm25_service(),
                code_search_service=self.code_search_service(),
                text_search_service=self.text_search_service(),
                progress_tracker=self.operation(),
                snippet_repository=self.snippet_v2_repository(),
                fusion_service=self.fusion_service(),
            )
        return self._code_search_application_service

    def git_commit_repository(self) -> GitCommitRepository:
        """Create a GitCommitRepository instance."""
        if not self._git_commit_repository:
            self._git_commit_repository = create_git_commit_repository(
                session_factory=self.session_factory
            )
        return self._git_commit_repository

    def git_branch_repository(self) -> GitBranchRepository:
        """Create a GitBranchRepository instance."""
        if not self._git_branch_repository:
            self._git_branch_repository = create_git_branch_repository(
                session_factory=self.session_factory
            )
        return self._git_branch_repository

    def git_tag_repository(self) -> GitTagRepository:
        """Create a GitTagRepository instance."""
        if not self._git_tag_repository:
            self._git_tag_repository = create_git_tag_repository(
                session_factory=self.session_factory
            )
        return self._git_tag_repository

    def trackable_resolution_service(self) -> TrackableResolutionService:
        """Create a TrackableResolutionService instance."""
        if not self._trackable_resolution_service:
            self._trackable_resolution_service = TrackableResolutionService(
                commit_repo=self.git_commit_repository(),
                branch_repo=self.git_branch_repository(),
                tag_repo=self.git_tag_repository(),
            )
        return self._trackable_resolution_service

    def enrichment_query_service(self) -> EnrichmentQueryService:
        """Create a EnrichmentQueryService instance."""
        if not self._enrichment_query_service:
            self._enrichment_query_service = EnrichmentQueryService(
                trackable_resolution=self.trackable_resolution_service(),
                enrichment_repo=self.enrichment_v2_repository(),
            )
        return self._enrichment_query_service

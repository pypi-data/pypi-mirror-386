"""Mapping between domain Git entities and SQLAlchemy entities."""

import kodit.domain.entities.git as domain_git_entities
from kodit.domain.enrichments.development.snippet.snippet import SnippetEnrichment
from kodit.domain.enrichments.enrichment import EnrichmentV2
from kodit.domain.value_objects import Enrichment, EnrichmentType
from kodit.infrastructure.sqlalchemy import entities as db_entities


class SnippetMapper:
    """Mapper for converting between domain Git entities and database entities."""

    def to_domain_snippet_v2(
        self,
        db_snippet: db_entities.SnippetV2,
        db_files: list[db_entities.GitCommitFile],
        db_enrichments: list[EnrichmentV2],
    ) -> domain_git_entities.SnippetV2:
        """Convert SQLAlchemy SnippetV2 to domain SnippetV2."""
        # Convert enrichments from SnippetEnrichment to Enrichment value objects
        enrichments: list[Enrichment] = [
            Enrichment(
                type=EnrichmentType.SUMMARIZATION,
                content=enrichment.content,
            )
            for enrichment in db_enrichments
        ]

        derives_from = [
            domain_git_entities.GitFile(
                created_at=file.created_at,
                blob_sha=file.blob_sha,
                path=file.path,
                mime_type=file.mime_type,
                size=file.size,
                extension=file.extension,
            )
            for file in db_files
        ]

        return domain_git_entities.SnippetV2(
            sha=db_snippet.sha,
            created_at=db_snippet.created_at,
            updated_at=db_snippet.updated_at,
            derives_from=derives_from,
            content=db_snippet.content,
            enrichments=enrichments,
            extension=db_snippet.extension,
        )

    def from_domain_snippet_v2(
        self, domain_snippet: domain_git_entities.SnippetV2
    ) -> db_entities.SnippetV2:
        """Convert domain SnippetV2 to SQLAlchemy SnippetV2."""
        return db_entities.SnippetV2(
            sha=domain_snippet.sha,
            content=domain_snippet.content,
            extension=domain_snippet.extension,
        )

    def from_domain_enrichments(
        self,
        snippet_sha: str,
        enrichments: list[Enrichment],
    ) -> list[SnippetEnrichment]:
        """Convert domain enrichments to SnippetEnrichment entities."""
        return [
            SnippetEnrichment(
                entity_id=snippet_sha,
                content=enrichment.content,
            )
            for enrichment in enrichments
        ]

    def to_domain_commit_index(
        self,
        db_commit_index: db_entities.CommitIndex,
        snippets: list[domain_git_entities.SnippetV2],
    ) -> domain_git_entities.CommitIndex:
        """Convert SQLAlchemy CommitIndex to domain CommitIndex."""
        return domain_git_entities.CommitIndex(
            commit_sha=db_commit_index.commit_sha,
            created_at=db_commit_index.created_at,
            updated_at=db_commit_index.updated_at,
            snippets=snippets,
            status=domain_git_entities.IndexStatus(db_commit_index.status),
            indexed_at=db_commit_index.indexed_at,
            error_message=db_commit_index.error_message,
            files_processed=db_commit_index.files_processed,
            processing_time_seconds=float(db_commit_index.processing_time_seconds),
        )

    def from_domain_commit_index(
        self, domain_commit_index: domain_git_entities.CommitIndex
    ) -> db_entities.CommitIndex:
        """Convert domain CommitIndex to SQLAlchemy CommitIndex."""
        return db_entities.CommitIndex(
            commit_sha=domain_commit_index.commit_sha,
            status=domain_commit_index.status,
            indexed_at=domain_commit_index.indexed_at,
            error_message=domain_commit_index.error_message,
            files_processed=domain_commit_index.files_processed,
            processing_time_seconds=domain_commit_index.processing_time_seconds,
        )

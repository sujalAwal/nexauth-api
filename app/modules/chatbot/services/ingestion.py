import logging
import asyncio
import uuid as uuid_lib
from typing import Dict, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, timezone

from app.database import AsyncSessionLocal
from app.modules.chatbot.models.chatbot import Document, DocumentChunk, SyncJob
from app.modules.chatbot.models.sharepoint import Sharepoint
from app.utils.file_loader import FileLoader
from app.utils.chunking import TextChunker
from app.modules.chatbot.services.embedding import get_embedding_service
from app.core.config import settings
from app.integrations.sharepoint.auth import get_graph_token
from app.core.http_client import get_http_client


logger = logging.getLogger(__name__)

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
SYNC_PARALLELISM = 10


def _format_bytes(size: int) -> str:
    """Human-readable byte size (e.g. '3.66 GB', '512 B')."""
    value = float(size or 0)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.2f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"


class IngestionService:
    """Service for ingesting SharePoint documents into the vector database"""

    def __init__(self):
        self.file_loader = FileLoader()
        self.chunker = TextChunker()
        self.embedding_service = get_embedding_service()
        self._sync_semaphore = asyncio.Semaphore(SYNC_PARALLELISM)

    async def sync_all_documents(
        self,
        db: AsyncSession,
        job_id: Optional[str] = None,
        skip_uuids: Optional[Set[str]] = None,
    ) -> Dict:
        """Sync all enabled SharePoint files, smallest first.

        Files run in ordered windows of ``SYNC_BATCH_SIZE`` (default 50): up to
        that many are downloaded/extracted/embedded in parallel, then their
        rows are persisted and committed together. Ordering by file size means
        the largest file can only ever sit in the final window, so a single
        huge Office document cannot starve thousands of small files behind it.

        Each row is persisted inside its own savepoint, so one bad file rolls
        itself back without taking down the rest of the window. Progress is
        written to the SyncJob row after every window for live status polling.
        """
        result = await db.execute(
            select(Sharepoint)
            .where(Sharepoint.is_file == True)  # noqa: E712
            .where(Sharepoint.enable_sync == True)  # noqa: E712
            .order_by(Sharepoint.file_size.asc().nulls_first())
        )
        files = list(result.scalars().all())

        summary = {
            "total_found": len(files),
            "new": 0,
            "updated": 0,
            "deleted": 0,
            "failed": 0,
            "skipped": 0,
            "deferred": 0,
            "size_excluded": 0,
            "details": [],
        }
        logger.info(f"Found {len(files)} enabled SharePoint files to sync")

        job = None
        if job_id:
            job = await db.get(SyncJob, uuid_lib.UUID(str(job_id)))

        token = get_graph_token()
        skip_uuids = skip_uuids or set()

        async def _process(row: Sharepoint) -> Dict:
            if str(row.uuid) in skip_uuids:
                logger.debug(f"Deferring in-flight file (resumed run): {row.name}")
                return {"file": row.name, "status": "skipped", "reason": "deferred"}
            try:
                async with self._sync_semaphore:
                    return await self._extract_sharepoint_file(row, token)
            except Exception as e:
                logger.error(f"❌ Failed to fetch {row.name}: {e}")
                return {"file": row.name, "status": "failed", "error": str(e)}

        batch_size = settings.SYNC_BATCH_SIZE
        pushed = 0
        tasks: Dict[int, asyncio.Task] = {}
        try:
            while pushed < len(files) or tasks:
                if len(tasks) < batch_size and pushed < len(files):
                    tasks[pushed] = asyncio.create_task(_process(files[pushed]))
                    pushed += 1
                    continue

                for i in sorted(tasks):
                    result = await tasks[i]
                    del tasks[i]
                    await self._consume_result(result, summary, db)

                await db.commit()
                await self._publish_progress(job, summary, files, tasks, db)
        except asyncio.CancelledError:
            if job is not None:
                job.status = "cancelled"
                job.stats = dict(summary)
                job.error = "Cancelled while running"
                await db.commit()
            raise

        logger.info(f"Sync complete: {summary}")
        return summary

    async def _consume_result(self, result: Dict, summary: Dict, db: AsyncSession) -> None:
        data = result.get("data")
        reason = result.get("reason")
        if data is None:
            summary["details"].append(result)
            if result.get("status") == "failed":
                summary["failed"] += 1
            elif reason == "deferred":
                summary["deferred"] += 1
            elif reason == "size_excluded":
                summary["size_excluded"] += 1
            else:
                summary["skipped"] += 1
            return

        try:
            async with db.begin_nested():
                status = await self._persist_document(data, db, result["row"])
            summary[status] += 1
            summary["details"].append({"file": result["file"], "status": status})
        except Exception as e:
            logger.error(f"❌ Failed to persist {result.get('file')}: {e}")
            summary["failed"] += 1
            summary["details"].append({
                "file": result.get("file"),
                "status": "failed",
                "error": str(e),
            })

    async def _publish_progress(self, job, summary, files, tasks, db) -> None:
        if job is None:
            return
        snapshot = dict(summary)
        snapshot["active_files"] = sorted({str(files[i].uuid) for i in tasks})
        job.stats = snapshot
        await db.commit()

    async def _extract_sharepoint_file(self, row: Sharepoint, token: str) -> Dict:
        """Download one SharePoint file in-memory, hash, extract and embed.

        Returns {"file", "status", "row", "data"} where data is None when the
        file is unchanged/unsupported and nothing should be persisted.
        """
        file_name = row.name
        content_url = row.url
        if not content_url.startswith(("http://", "https://")):
            content_url = f"{GRAPH_BASE_URL}/{content_url.lstrip('/')}"

        # Cheap pre-filter on the Graph-reported size: skip before downloading.
        min_bytes = settings.sync_min_file_size_bytes
        max_bytes = settings.sync_max_file_size_bytes
        if row.file_size is not None and not (min_bytes <= row.file_size <= max_bytes):
            return {
                "file": file_name,
                "status": "skipped",
                "reason": "size_excluded",
                "size_bytes": row.file_size,
                "size_readable": _format_bytes(row.file_size),
            }

        async with get_http_client(timeout=60.0) as client:
            response = await client.get(
                content_url,
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            data = response.content

        content_hash = FileLoader.content_hash_from_bytes(data)

        # Incremental sync: skip files whose content did not change.
        if row.content_hash and row.content_hash == content_hash:
            logger.debug(f"Skipping unchanged file: {file_name}")
            return {
                "file": file_name,
                "status": "skipped",
                "reason": "unchanged",
            }

        try:
            text, file_info = FileLoader.extract_text_from_bytes(data, file_name)
        except ValueError as e:
            logger.warning(f"Unsupported file format, skipping {file_name}: {e}")
            return {"file": file_name, "status": "skipped", "reason": "unsupported"}
        if len(text.strip()) < 10:
            logger.warning(f"Extracted text too short, skipping {file_name}")
            return {"file": file_name, "status": "skipped", "reason": "empty_text"}

        department = (row.department or "general").lower()
        source_data = row.data or {}

        metadata = {
            "source": file_name,
            "department": department,
            "url": content_url,
            "web_url": source_data.get("webUrl"),
            "last_modified_at": row.last_modified_at.isoformat() if row.last_modified_at else None,
            "folder": (source_data.get("parentReference") or {}).get("path"),
        }
        chunks = self.chunker.chunk_text(text, metadata=metadata)

        chunk_texts = [chunk["text"] for chunk in chunks]
        embeddings = await self.embedding_service.embed_batch(chunk_texts)

        if embeddings and any(
            len(emb) != settings.EMBEDDING_DIMENSIONS for emb in embeddings
        ):
            raise ValueError(
                f"Embedding dimension mismatch: got {len(embeddings[0])}, "
                f"expected {settings.EMBEDDING_DIMENSIONS}"
            )

        body = {
            "content_hash": content_hash,
            "file_name": file_name,
            "department": department,
            "url": content_url,
            "file_path": row.url,
            "uuid": row.uuid,
            "web_url": source_data.get("webUrl"),
            "last_modified_at": row.last_modified_at,
            "file_type": file_info["file_type"],
            "file_size": file_info["file_size"],
            "chunks": chunks,
            "embeddings": embeddings,
        }

        return {"file": file_name, "status": "done", "row": row, "data": body}

    async def _persist_document(self, body: Dict, db: AsyncSession, row: Sharepoint) -> str:
        """Upsert a Document + chunks for a processed SharePoint file."""
        content_hash = body["content_hash"]
        file_name = body["file_name"]
        department = body["department"]

        existing = await db.execute(
            select(Document).where(Document.file_path == body["file_path"])
        )
        existing_doc = existing.scalar_one_or_none()

        if existing_doc:
            await db.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == existing_doc.id)
            )
            existing_doc.content_hash = content_hash
            existing_doc.file_size = body["file_size"]
            existing_doc.file_type = body["file_type"]
            existing_doc.status = "completed"
            existing_doc.chunk_count = len(body["chunks"])
            existing_doc.uuid = body["uuid"]
            existing_doc.url = body["url"]
            existing_doc.web_url = body["web_url"]
            existing_doc.last_modified_at = body["last_modified_at"]
            existing_doc.updated_at = datetime.now(timezone.utc)
            existing_doc.error_message = None
            doc = existing_doc
            status = "updated"
        else:
            doc = Document(
                source_type="sharepoint",
                file_path=body["file_path"],
                filename=file_name,
                department=department,
                content_hash=content_hash,
                file_size=body["file_size"],
                file_type=body["file_type"],
                status="completed",
                chunk_count=len(body["chunks"]),
                uuid=body["uuid"],
                url=body["url"],
                web_url=body["web_url"],
                last_modified_at=body["last_modified_at"],
            )
            db.add(doc)
            await db.flush()
            status = "new"

        for chunk, embedding in zip(body["chunks"], body["embeddings"]):
            chunk_record = DocumentChunk(
                document_id=doc.id,
                embedding=embedding,
                chunk_index=chunk["chunk_index"],
                department=department,
                source_file=file_name,
                url=body["url"],
                content_hash=content_hash,
                content_preview=chunk["text"][:200],
                chunk_metadata={
                    "page": self._detect_page(chunk["text"]),
                    "url": body["url"],
                    "web_url": body["web_url"],
                    "last_modified_at": body["last_modified_at"].isoformat() if body["last_modified_at"] else None,
                },
                token_count=chunk["token_count"],
            )
            db.add(chunk_record)

        row.content_hash = content_hash
        row.last_synced_at = datetime.now(timezone.utc)
        db.add(row)

        logger.info(f"✅ {status}: {file_name} ({len(body['chunks'])} chunks)")
        return status

    def _detect_page(self, text: str) -> Optional[str]:
        """Read a page/sheet/slide marker embedded by the extractor, if any."""
        for i, line in enumerate(text.splitlines()):
            if line.startswith("[Page ") or line.startswith("[Sheet: ") or line.startswith("[Slide "):
                return line.strip("[]")
        return None

    async def create_sync_job(self, db: AsyncSession) -> SyncJob:
        """Create a new sync job row (status pending)."""
        job = SyncJob(status="pending", stats={})
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    async def _collect_stale_running_files(self, db: AsyncSession, current_job_id: str) -> Set[str]:
        """Reset jobs left 'running' (e.g. the worker was restarted).

        Returns the Graph file UUIDs that were in flight so the new run can
        defer re-downloading them; those rows still carry content_hash = NULL
        and remain candidates for the run after this one.
        """
        result = await db.execute(select(SyncJob).where(SyncJob.status == "running"))
        jobs = result.scalars().all()
        active: Set[str] = set()
        now = datetime.now(timezone.utc)
        for job in jobs:
            if str(job.id) == current_job_id:
                continue
            job.status = "failed"
            job.error = "Reset: previous run interrupted"
            job.finished_at = now
            for uid in (job.stats or {}).get("active_files", []):
                active.add(str(uid))
        await db.commit()
        return active

    async def run_sync_job(self, job_id: str) -> None:
        """Run a sync job in a fresh session (for background tasks)."""
        try:
            async with AsyncSessionLocal() as db:
                job = await db.get(SyncJob, uuid_lib.UUID(str(job_id)))
                if job is None:
                    logger.error(f"Sync job {job_id} not found")
                    return

                job.status = "running"
                job.started_at = datetime.now(timezone.utc)
                job.error = None
                job.finished_at = None
                await db.commit()

                stale = await self._collect_stale_running_files(db, str(job.id))
                if stale:
                    logger.warning(
                        f"Recovered {len(stale)} in-flight file(s) from interrupted jobs; deferring this run."
                    )

                cancelled = False
                try:
                    stats = await self.sync_all_documents(
                        db, job_id=str(job.id), skip_uuids=stale
                    )
                except asyncio.CancelledError:
                    cancelled = True
                except Exception as e:
                    logger.error(f"Sync job {job_id} failed: {e}")
                    job.status = "failed"
                    job.error = str(e)

                if not cancelled and job.status not in ("cancelled", "failed"):
                    job.status = "completed"
                    job.stats = stats
                    job.error = None
                job.finished_at = datetime.now(timezone.utc)
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to run sync job {job_id}: {e}")

    async def get_latest_sync_job(self, db: AsyncSession) -> Optional[SyncJob]:
        """Get the most recent sync job."""
        result = await db.execute(
            select(SyncJob).order_by(SyncJob.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_sync_status(self, db: AsyncSession) -> Dict:
        """Get current sync status"""

        total_result = await db.execute(select(Document))
        total_docs = len(total_result.scalars().all())

        failed_result = await db.execute(
            select(Document).where(Document.status == "failed")
        )
        failed_docs = len(failed_result.scalars().all())

        chunks_result = await db.execute(select(DocumentChunk))
        total_chunks = len(chunks_result.scalars().all())

        job = await self.get_latest_sync_job(db)
        job_state = {
            "job_id": str(job.id) if job else None,
            "job_status": job.status if job else None,
            "job_started_at": job.started_at.isoformat() if job and job.started_at else None,
            "job_finished_at": job.finished_at.isoformat() if job and job.finished_at else None,
            "job_error": job.error if job else None,
        }

        return {
            "total_documents": total_docs,
            "failed_documents": failed_docs,
            "total_chunks": total_chunks,
            "last_sync": datetime.now(timezone.utc).isoformat(),
            "last_job": job_state,
        }


# Singleton
_ingestion_service: Optional[IngestionService] = None


def get_ingestion_service() -> IngestionService:
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = IngestionService()
    return _ingestion_service
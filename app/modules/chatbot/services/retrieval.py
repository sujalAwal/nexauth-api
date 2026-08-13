import asyncio
import logging
from typing import List, Dict, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.chatbot.services.embedding import get_embedding_service
from app.core.config import settings
from app.utils.file_loader import FileLoader
from app.utils.chunking import TextChunker
from app.integrations.sharepoint.auth import get_graph_token
from app.core.http_client import get_http_client


logger = logging.getLogger(__name__)

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"


class RetrievalService:
    """Service for retrieving relevant document chunks"""

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.chunker = TextChunker()

    async def search_similar_chunks(
        self,
        query: str,
        department: str,
        limit: int = None,
        similarity_threshold: float = None,
        db: AsyncSession = None
    ) -> List[Dict]:
        """
        Vector search returning chunk METADATA only (no full text).
        The full, latest text is fetched from SharePoint on-demand later.
        """

        if limit is None:
            limit = settings.MAX_CHUNKS_PER_QUERY

        if similarity_threshold is None:
            similarity_threshold = settings.SIMILARITY_THRESHOLD

        query_embedding = await self.embedding_service.embed_query(query)
        vector_str = f"[{','.join(map(str, query_embedding))}]"

        search_query = text("""
            SELECT 
                dc.id,
                dc.content_preview,
                dc.source_file,
                dc.department,
                dc.chunk_index,
                dc.url,
                dc.chunk_metadata,
                dc.content_hash,
                1 - (dc.embedding <=> :query_vector) AS similarity
            FROM document_chunks dc
            WHERE lower(dc.department) = lower(:department)
                AND 1 - (dc.embedding <=> :query_vector) > :threshold
            ORDER BY dc.embedding <=> :query_vector
            LIMIT :limit
        """)

        result = await db.execute(
            search_query,
            {
                "query_vector": vector_str,
                "department": department,
                "threshold": similarity_threshold,
                "limit": limit
            }
        )

        chunks = []
        for row in result:
            chunks.append({
                "id": str(row.id),
                "preview": row.content_preview or "",
                "source": row.source_file,
                "department": row.department,
                "chunk_index": row.chunk_index,
                "url": row.url,
                "chunk_metadata": row.chunk_metadata or {},
                "content_hash": row.content_hash,
                "similarity": round(float(row.similarity), 4)
            })

        logger.info(f"Found {len(chunks)} relevant chunks for query: '{query[:50]}...'")

        return chunks

    async def _keyword_search(
        self,
        query: str,
        department: str,
        limit: int,
        db: AsyncSession
    ) -> List[Dict]:
        """Metadata-only keyword fallback (searches preview + file name)."""
        keywords = [kw.replace("'", "''") for kw in query.replace(",", " ").split() if len(kw) > 2]
        if not keywords:
            return []

        conditions = " OR ".join([
            f"(dc.content_preview ILIKE '%%{kw}%%' OR dc.source_file ILIKE '%%{kw}%%')"
            for kw in keywords
        ])

        search_query = text(f"""
            SELECT 
                dc.id,
                dc.content_preview,
                dc.source_file,
                dc.department,
                dc.chunk_index,
                dc.url,
                dc.chunk_metadata,
                dc.content_hash,
                0.0 AS similarity
            FROM document_chunks dc
            WHERE lower(dc.department) = lower(:department)
                AND ({conditions})
            LIMIT :limit
        """)

        result = await db.execute(
            search_query,
            {"department": department, "limit": limit}
        )

        chunks = []
        for row in result:
            chunks.append({
                "id": str(row.id),
                "preview": row.content_preview or "",
                "source": row.source_file,
                "department": row.department,
                "chunk_index": row.chunk_index,
                "url": row.url,
                "chunk_metadata": row.chunk_metadata or {},
                "content_hash": row.content_hash,
                "similarity": 0.0
            })

        return chunks

    async def search_with_fallback(
        self,
        query: str,
        department: str,
        limit: int = None,
        db: AsyncSession = None
    ) -> Dict:
        """
        Search for relevant chunk metadata with graceful fallbacks.
        Returns {chunks, fallback_used}.
        1. Vector similarity above SIMILARITY_THRESHOLD
        2. Vector similarity above FALLBACK_SIMILARITY_THRESHOLD
        3. Keyword ILIKE match (on preview + filename)
        """

        if limit is None:
            limit = settings.MAX_CHUNKS_PER_QUERY

        chunks = await self.search_similar_chunks(
            query=query,
            department=department,
            limit=limit,
            db=db
        )
        if chunks:
            return {"chunks": chunks, "fallback_used": False}

        chunks = await self.search_similar_chunks(
            query=query,
            department=department,
            limit=limit,
            similarity_threshold=settings.FALLBACK_SIMILARITY_THRESHOLD,
            db=db
        )
        if chunks:
            logger.info("Using relaxed similarity threshold fallback for query.")
            return {"chunks": chunks, "fallback_used": True}

        chunks = await self._keyword_search(
            query=query,
            department=department,
            limit=limit,
            db=db
        )
        if chunks:
            logger.info("Using keyword fallback for query.")
            return {"chunks": chunks, "fallback_used": True}

        return {"chunks": [], "fallback_used": False}

    async def fetch_chunk_contents(
        self,
        chunks: List[Dict],
        token: str = None,
        parallelism: int = 5,
    ) -> List[Dict]:
        """
        Fetch the LATEST text for retrieved chunks on-demand from SharePoint.

        Downloads each unique file, re-extracts + re-chunks with the same
        deterministic parameters used at ingestion, then pulls the chunk at
        the matching chunk_index (clamped if the file changed size).
        """
        token = token or get_graph_token()
        unique_urls = list({c["url"] for c in chunks if c.get("url")})
        semaphore = asyncio.Semaphore(parallelism)

        async def _fetch(url: str):
            async with semaphore:
                try:
                    content_url = url
                    if not content_url.startswith(("http://", "https://")):
                        content_url = f"{GRAPH_BASE_URL}/{content_url.lstrip('/')}"

                    async with get_http_client(timeout=60.0) as client:
                        response = await client.get(
                            content_url,
                            headers={"Authorization": f"Bearer {token}"},
                        )
                        response.raise_for_status()
                        data = response.content

                    source = next(
                        (c.get("source") for c in chunks if c.get("url") == url),
                        content_url,
                    )
                    text, _ = FileLoader.extract_text_from_bytes(data, source)

                    index = {
                        chunk["chunk_index"]: chunk
                        for chunk in self.chunker.chunk_text(text)
                    }
                    return url, index
                except Exception as e:
                    logger.error(f"On-demand fetch failed for {url}: {e}")
                    return url, None

        fetched = await asyncio.gather(*[_fetch(url) for url in unique_urls])
        document_index = {url: idx for url, idx in fetched if idx}

        enriched = []
        for chunk in chunks:
            doc_index = document_index.get(chunk.get("url"))
            if not doc_index:
                continue

            chunk_text = doc_index.get(chunk["chunk_index"])
            if chunk_text is None:
                indexes = sorted(doc_index.keys())
                if indexes:
                    nearest = min(indexes, key=lambda i: abs(i - chunk["chunk_index"]))
                    chunk_text = doc_index.get(nearest)

            if chunk_text is None:
                continue

            lines = chunk_text["text"].splitlines()
            page = lines[0].strip("[]") if lines and lines[0].startswith("[") else None

            enriched.append({
                "text": chunk_text["text"],
                "source": chunk.get("source"),
                "url": chunk.get("url"),
                "page": page or chunk.get("chunk_metadata", {}).get("page"),
                "chunk_index": chunk.get("chunk_index"),
                "chunk_metadata": chunk.get("chunk_metadata", {}),
            })

        return enriched

    async def search_with_permissions(
        self,
        query: str,
        user_id: str,
        db: AsyncSession
    ) -> List[Dict]:
        """
        Search chunks with department permissions check
        """

        perm_query = text("""
            SELECT department 
            FROM chatbot.department_permissions 
            WHERE user_id = :user_id
        """)

        result = await db.execute(perm_query, {"user_id": user_id})
        allowed_departments = [row[0] for row in result]

        if not allowed_departments:
            logger.warning(f"No department permissions for user {user_id}")
            return []

        all_chunks = []
        for department in allowed_departments:
            chunks = await self.search_similar_chunks(
                query=query,
                department=department,
                db=db
            )
            all_chunks.extend(chunks)

        all_chunks.sort(key=lambda x: x["similarity"], reverse=True)
        return all_chunks[:settings.MAX_CHUNKS_PER_QUERY]


# Singleton
_retrieval_service: Optional[RetrievalService] = None


def get_retrieval_service() -> RetrievalService:
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service
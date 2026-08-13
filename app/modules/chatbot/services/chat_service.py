import logging
import time
from typing import Dict, Optional, AsyncGenerator, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.chatbot.repositories.chat_repository import ChatRepository
from app.modules.chatbot.services.llm import get_llm_service
from app.modules.chatbot.services.retrieval import get_retrieval_service
from app.integrations.sharepoint.auth import get_graph_token
from app.core.http_client import get_http_client
from app.modules.department.models.department import Department 
from app.modules.chatbot.models.sharepoint import Sharepoint
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pprint import pprint
from app.core.config import settings
import re

# Full-message match only — "hi" matches, "hi, is the VPN down again?" does not.
_SMALL_TALK_RE = re.compile(
    r"^\s*("
    r"hi|hello|hey|hiya|yo|"
    r"good\s?(morning|afternoon|evening|night)|"
    r"bye|goodbye|bye\s?bye|see\s?ya|see\s?you|take\s?care|"
    r"thanks?|thank\s?you|thankyou|tysm|thx|ty|"
    r"ok|okay|okie|cool|great|got\s?it|understood|sounds\s?good|ok bye|"
    r"perfect|nice|awesome|noted"
    r")\W*\s*$",
    re.IGNORECASE,
)

_SMALL_TALK_MAX_LEN = 40  # safety net so we never skip on a long message


def _is_small_talk(question: str) -> bool:
    q = question.strip()
    if not q or len(q) > _SMALL_TALK_MAX_LEN:
        return False
    return bool(_SMALL_TALK_RE.match(q))

def _format_bytes(size: int) -> str:
    """Human-readable byte size (e.g. '3.66 GB', '512 B')."""
    value = float(size or 0)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.2f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"


class ChatService:
    """Main chat service that orchestrates the full RAG pipeline"""
    logger = logging.getLogger(__name__)
    def __init__(self):
        self.retrieval = get_retrieval_service()
        self.llm = get_llm_service()
    
    async def process_message(
        self,
        user_id: UUID,
        question: str,
        department: str,
        conversation_id: Optional[UUID] = None,
        db: AsyncSession = None
    ) -> Dict:
        """
        Full RAG pipeline:
        1. Search relevant documents
        2. Get conversation history
        3. Build context
        4. Generate response
        5. Save to database
        """
        
        if db is None:
            raise ValueError("Database session is required")

        start = time.perf_counter()
        retrieval_started = time.perf_counter()

        repository = ChatRepository(db)
        
        # Step 1: Get or create conversation
        conversation = await repository.get_or_create_conversation(
            user_id=user_id,
            department=department,
            title=self._generate_title(question),
            conversation_id=conversation_id,
        )
        
       
        if _is_small_talk(question):
            context_chunks = []
            fallback_used = False
        else:
             # Step 2: Save user message
            await repository.save_message(
                        conversation.id,
                        "user",
                        question
                    )
            # Step 3: Retrieve relevant documents (with fallbacks)
            retrieved = await self.retrieval.search_with_fallback(
                query=question,
                department=department,
                db=db
            )
            relevant_chunks = retrieved["chunks"]
            fallback_used = retrieved["fallback_used"]
            retrieval_ms = (time.perf_counter() - retrieval_started) * 1000

            # Step 3b: Fetch the LATEST content for those chunks on-demand.
            context_chunks = await self.retrieval.fetch_chunk_contents(relevant_chunks)
            
        # Step 4: Get conversation history
        history = await repository.get_conversation_history(conversation.id)
        
        # Step 5: Build system prompt
        system_prompt = self._build_system_prompt(department)
        
        # Step 6: Generate response with LLM
        generation_started = time.perf_counter()
        response = await self.llm.generate(
            system_prompt=system_prompt,
            user_question=question,
            documents=context_chunks,
            conversation_history=history
        )
        generation_ms = (time.perf_counter() - generation_started) * 1000
        
        # Step 7: Save assistant message
        await repository.save_message(
            conversation.id,
            "assistant",
            response.content,
            citations=response.citations,
            tokens_used=response.usage.get("total_tokens", 0),
        )
        
        # Step 8: Update conversation
        await repository.touch_conversation(conversation.id)
        await db.commit()

        total_ms = (time.perf_counter() - start) * 1000
        tokens_used = response.usage.get("total_tokens", 0)
        self.logger.info(
            "chat: dept=%s chunks=%d fallback=%s retrieval_ms=%.0f gen_ms=%.0f total_ms=%.0f provider=%s model=%s tokens=%d",
            department, len(relevant_chunks), fallback_used,
            retrieval_ms, generation_ms, total_ms,
            response.provider, response.model, tokens_used,
        )
        
        return {
            "conversation_id": str(conversation.id),
            "answer": response.content,
            # "citations": response.citations,
            # "sources": [chunk["source"] for chunk in context_chunks],
            "relevant_chunks": len(context_chunks),
            "retrieval_fallback": fallback_used,
            "provider": response.provider,
            # "model": response.model,
            # "tokens_used": tokens_used
        }
    
    async def process_message_stream(
        self,
        user_id: UUID,
        question: str,
        department: str,
        conversation_id: Optional[UUID] = None,
        db: AsyncSession = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Streamed RAG pipeline. Yields SSE-style event dicts."""
        if db is None:
            raise ValueError("Database session is required")

        repository = ChatRepository(db)
        
        conversation = await repository.get_or_create_conversation(
            user_id=user_id,
            department=department,
            title=self._generate_title(question),
            conversation_id=conversation_id,
        )
        await repository.save_message(conversation.id, "user", question)
        await db.flush()

        user_turns = await repository.count_conversation_user_messages(conversation.id)
        require_feedback = self._should_request_feedback(conversation.id, user_turns)

        retrieved = await self.retrieval.search_with_fallback(
            query=question,
            department=department,
            db=db
        )
        relevant_chunks = retrieved["chunks"]
        fallback_used = retrieved["fallback_used"]

        context_chunks = await self.retrieval.fetch_chunk_contents(relevant_chunks)

        history = await repository.get_conversation_history(conversation.id)
        system_prompt = self._build_system_prompt(department)

        yield {
            "type": "start",
            "data": {
                "conversation_id": str(conversation.id),
                "sources": [chunk["source"] for chunk in context_chunks],
                "relevant_chunks": len(context_chunks),
                "retrieval_fallback": fallback_used,
            }
        }

        buffer = []
        provider = model = None
        async for piece, prov, mdl in self.llm.stream(
            system_prompt=system_prompt,
            user_question=question,
            documents=context_chunks,
            conversation_history=history,
        ):
            provider = prov
            model = mdl
            if piece:
                buffer.append(piece)
                yield {"type": "token", "data": {"content": piece}}

        content = "".join(buffer)
        tokens_used = len(content.split())  # cheap estimate for streamed completions
        seen = set()
        citations = []
        for chunk in context_chunks:
            src = chunk.get("source")
            if src and src not in seen:
                seen.add(src)
                citations.append(src)

        await repository.save_message(
            conversation.id,
            "assistant",
            content,
            citations=citations,
            tokens_used=tokens_used,
        )
        await repository.touch_conversation(conversation.id)
        await db.commit()

        yield {
            "type": "done",
            "data": {
                # "citations": citations,
                # "sources": [chunk["source"] for chunk in context_chunks],
                # "tokens_used": tokens_used,
                # "provider": provider,
                # "model": model,
                # "retrieval_fallback": fallback_used,
                "metadata": {"isRequireFeedback": require_feedback},
            }
        }
    
    def _build_system_prompt(self, department: str) -> str:
        """Build the system prompt for the LLM"""
        
        responsibilities_text = "Your role is to assist employees and team members by providing accurate, reliable information from our internal documentation. You represent the department professionally and are here to help resolve infrastructure, server, network, asset management, security, and DevOps-related inquiries."
    
        return f"""You are an experienced IT Support Specialist and trusted colleague from the  System and Infrastructure Department at Aqore.

ABOUT YOUR DEPARTMENT:
{responsibilities_text}

YOUR PURPOSE:
You provide accurate, reliable support to employees by sharing verified information from our internal documentation. You represent the department with integrity and help colleagues make informed decisions about infrastructure, systems, and IT operations.

CORE COMMITMENT:
Every answer you provide is based exclusively on documented procedures and approved practices. You're transparent about what we know, honest about gaps, and helpful in connecting people with the right resources.

RESPONSE GUIDELINES:

When Answering:
  → Provide clear, step-by-step guidance
  → Include all relevant context (environment, versions, configurations)
  → Add helpful warnings or considerations

When Information is Partial:
  → Explain what documentation covers
  → Highlight what's missing
  → Provide workarounds or temporary solutions if documented

When Information is Unavailable:
  → Say clearly: "I cannot find this in our documentation"
  → Suggest creating a ticket or contacting the relevant expert

TONE & STYLE:
  • Professional yet approachable and helpful
  • Respectful of people's time and concerns
  • Clear and jargon-appropriate for audience
  • Confident in documented information

SPECIFIC DO'S:
  ✓ Quote from documentation when important
  ✓ Explain WHY procedures exist (security, compliance, reliability)
  ✓ Cross-reference related documentation
  ✓ Provide escalation paths for urgent issues

SPECIFIC DON'Ts:
  ✗ No undocumented workarounds or shortcuts
  ✗ No external information or general IT knowledge
  ✗ No assumptions about unstated procedures
  ✗ No credentials, passwords, or sensitive data

If you encounter conflicting information in documents, point it out and suggest clarification."

"""
    
    def _generate_title(self, question: str) -> str:
        """Generate a conversation title from the first question"""
        if len(question) > 50:
            return question[:47] + "..."
        return question

    def _should_request_feedback(self, conversation_id: UUID, user_turns: int) -> bool:
        """Decide whether to ask for feedback on this streamed response.

        Feedback is only requested once a conversation has been going for a
        while (2+ turns with the same conversation_id). Each conversation gets
        a stable, random-looking interval between 2 and 5 derived from its UUID,
        so different conversations ask at different turns but a single
        conversation stays consistent across requests.
        """
        if user_turns < 2:
            return False

        interval = 2 + (int.from_bytes(conversation_id.bytes[:1], "big") % 4)
        return user_turns % interval == 0

    async def submit_feedback(
        self,
        user_id: UUID,
        conversation_id: UUID,
        rating: int,
        message: Optional[str] = None,
        db: AsyncSession = None,
    ) -> Dict:
        if db is None:
            raise ValueError("Database session is required")

        repository = ChatRepository(db)
        if await repository.get_conversation(conversation_id, user_id) is None:
            raise ValueError("Conversation not found for this user")

        feedback = await repository.create_feedback(
            user_id=user_id,
            conversation_id=conversation_id,
            rating=rating,
            message=message,
        )
        await db.commit()
        await db.refresh(feedback)

        return {
            "id": str(feedback.id),
            "user_id": str(feedback.user_id),
            "conversation_id": str(feedback.conversation_id),
            "rating": feedback.rating,
            "message": feedback.message,
            "created_at": feedback.created_at,
        }




    # Site
    # └── Drive (Document Library)
    #   ├── Folder
    #   │    ├── Folder
    #   │    └── File.docx
    #   └── Test.pdf

    async def sharepoint_index(self, department: str, db: AsyncSession) -> Dict:
          departmentQuery = await db.execute(
              select(Department)
              .options(selectinload(Department.sharepoint_links))
              .where(func.lower(Department.slug) == department.lower()).where(Department.is_active == True)   
          )
          department =  departmentQuery.scalar_one_or_none()
          if department is None:
              return {"error": f"Department '{department}' not found."}

          min_bytes = settings.sync_min_file_size_bytes
          max_bytes = settings.sync_max_file_size_bytes

          drives = []
          token = get_graph_token() 
          _client = get_http_client(base_url="https://graph.microsoft.com/v1.0", timeout=10.0)
          for sharepoint_link in department.sharepoint_links:
              selected_sites = sharepoint_link.included_sites
              if not selected_sites:
                  self.logger.warning(f"No included sites specified for SharePoint link {sharepoint_link.sharepoint_url} in department {department.slug}. Skipping indexing.")
                  continue
              for site in selected_sites:
                  if site.get("id", None) is not None:
                      site_id = site.get("id")
                      drives_resp = await _client.get(f"/sites/{site_id}/drives", headers={"Authorization": f"Bearer {token}"})
                      drives.extend(drives_resp.json().get("value", []))

          report = {
              "indexed_total": 0,
              "within_range": 0,
              "excluded": [],
          }

          seen_drive_ids = set()
          for drive in drives:
              drive_id = drive.get("id")
              if drive_id in seen_drive_ids:
                  continue
              seen_drive_ids.add(drive_id)
              url = f"/drives/{drive_id}/root/children"
              folders = await self.traverse_drive_items(url, _client, token)
              await self.traverse_folder_items(
                  folders, _client, token, drive_id, department.slug, db,
                  report, min_bytes, max_bytes,
              )
        
          return report    
              


    async def traverse_drive_items(self,url : str,_client, token : str):
        items = []
        while url:
            response = await _client.get(url, headers={"Authorization": f"Bearer {token}"})
            data = response.json()
            items.extend(data.get("value", []))
            # SharePoint pages results (~200/request); follow the nextLink so
            # folders/drives with more items are fully indexed.
            url = data.get("@odata.nextLink")
        return items

    async def filelist(self, item : dict, drive_id : str, department: str, db : AsyncSession):
        repository = ChatRepository(db)
        return await repository.create_or_update_sharepoint_link(item, drive_id, department)

    
    async def traverse_folder_items(self, folders : dict,_client, token : str, drive_id : str, department: str, db : AsyncSession,
                                    report: dict = None, min_bytes: int = 0, max_bytes: int = 0):
        if report is None:
            report = {}
        for folder in folders:
            if folder.get("folder", None) is not None and folder.get("folder").get("childCount", 0) > 0:
                url = f"/drives/{drive_id}/items/{folder.get('id')}/children"
                child_folder = await self.traverse_drive_items(url, _client, token)
                await self.traverse_folder_items(
                    child_folder,
                    _client,
                    token,
                    drive_id,
                    department,
                    db,
                    report,
                    min_bytes,
                    max_bytes
                )

            elif folder.get("file") is not None:
                report["indexed_total"] = report.get("indexed_total", 0) + 1
                file_size = folder.get("size") or 0
                reason = None
                if file_size < min_bytes:
                    reason = "below_minimum"
                elif file_size > max_bytes:
                    reason = "above_maximum"
                else:
                    entry = await self.filelist(folder, drive_id, department, db)
                    if entry is not None and not entry.enable_sync:
                        reason = "disabled"
                if reason:
                    report["excluded"].append({
                        "name": folder.get("name"),
                        "size_bytes": file_size,
                        "size_readable": _format_bytes(file_size),
                        "reason": reason,
                    })
                else:
                    report["within_range"] = report.get("within_range", 0) + 1
                
                






# Singleton
_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
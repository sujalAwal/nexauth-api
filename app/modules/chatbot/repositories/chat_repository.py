from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.chatbot.models.sharepoint import Sharepoint
from app.modules.chatbot.models.chatbot import ChatFeedback, Conversation, Message


class ChatRepository:
    """Repository for chatbot conversation persistence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_conversation(self, conversation_id: UUID, user_id: UUID) -> Conversation | None:
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create_conversation(
        self,
        user_id: UUID,
        department: str,
        title: str,
        conversation_id: Optional[UUID] = None,
    ) -> Conversation:
        if conversation_id:
            conversation = await self.get_conversation(conversation_id, user_id)
            if conversation:
                return conversation

        conversation = Conversation(
            user_id=user_id,
            department=department,
            title=title,
            is_active=True,
        )
        self.db.add(conversation)
        await self.db.flush()
        return conversation

    async def save_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        citations: Optional[List[str]] = None,
        tokens_used: int = 0,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            citations=citations or [],
            tokens_used=tokens_used,
        )
        self.db.add(message)
        await self.db.flush()
        return message

    async def touch_conversation(self, conversation_id: UUID) -> None:
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            conversation.updated_at = datetime.now(timezone.utc)
            self.db.add(conversation)

    async def get_conversation_history(self, conversation_id: UUID, limit: int = 10) -> list[dict]:
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )

        messages = result.scalars().all()
        messages.reverse()
        return [{"role": message.role, "content": message.content} for message in messages]

    async def list_recent_conversations(self, limit: int = 20) -> List[Conversation]:
        result = await self.db.execute(
            select(Conversation)
            .order_by(Conversation.updated_at.desc(), Conversation.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def count_conversation_user_messages(self, conversation_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conversation_id,
                Message.role == "user",
            )
        )
        return result.scalar() or 0

    async def create_feedback(
        self,
        user_id: UUID,
        conversation_id: UUID,
        rating: int,
        message: Optional[str] = None,
    ) -> ChatFeedback:
        feedback = ChatFeedback(
            user_id=user_id,
            conversation_id=conversation_id,
            rating=rating,
            message=message,
        )
        self.db.add(feedback)
        await self.db.flush()
        return feedback
    
    async def create_or_update_sharepoint_link(self, item: dict, drive_id: str, department: str = None) -> Sharepoint:
        department = department.lower() if department else department
        exists = await self.db.execute(select(Sharepoint).where(Sharepoint.uuid == item.get("id")))
        sharepoint_entry = exists.scalar_one_or_none()
        last_modified = parse_graph_datetime(item.get("lastModifiedDateTime"))
        if sharepoint_entry is None:
            new_entry = Sharepoint(
                name=item.get("name"),
                uuid=item.get("id"),
                url=f"drives/{drive_id}/items/{item.get('id')}/content",
                department=department,
                is_file=True,
                file_size=item.get("size"),
                enable_sync=True,
                file_created_at=parse_graph_datetime(item.get("createdDateTime")),
                last_modified_at=last_modified,
                data=item
            )
            self.db.add(new_entry)
            await self.db.commit()
            await self.db.refresh(new_entry)
            return new_entry
        else:
            changed = (
                sharepoint_entry.last_modified_at != last_modified
                or sharepoint_entry.url != f"drives/{drive_id}/items/{item.get('id')}/content"
                or sharepoint_entry.file_size != item.get("size")
            )
            sharepoint_entry.name = item.get("name")
            sharepoint_entry.url = f"drives/{drive_id}/items/{item.get('id')}/content"
            sharepoint_entry.department = department
            sharepoint_entry.is_file = True
            sharepoint_entry.file_size = item.get("size")
            # enable_sync is intentionally NOT touched here so a manual off
            # toggle survives re-indexing.
            sharepoint_entry.file_created_at = parse_graph_datetime(item.get("createdDateTime"))
            sharepoint_entry.last_modified_at = last_modified
            sharepoint_entry.data = item
            if changed:
                # Content may have changed -> force a re-sync.
                sharepoint_entry.content_hash = None
                sharepoint_entry.last_synced_at = None
            await self.db.commit()
            await self.db.refresh(sharepoint_entry)
            return sharepoint_entry
            
    
   

def parse_graph_datetime(value: str):
    if not value:
        return None

    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )
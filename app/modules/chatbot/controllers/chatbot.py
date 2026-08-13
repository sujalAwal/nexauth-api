import json
from fastapi import APIRouter, Depends, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.modules.chatbot.schemas.requests.chat_request import ChatRequest , SharepointIndexRequest , ChatFeedbackRequest
from app.modules.chatbot.schemas.response.chat_response import (
    ChatResponse,
    ConversationCollection,
    ConversationResponse,
    SyncResponse,
    SyncStats,
    SyncStatusResponse,
    FeedbackResponse,
)
from app.modules.chatbot.services import get_chat_service, get_ingestion_service
from app.schemas.response import ApiResponse
from fastapi import HTTPException
from pprint import pprint

chatbot_router = APIRouter()

@chatbot_router.post("/sharepoint/index", status_code=status.HTTP_200_OK)
async def sharepoint_index(request : SharepointIndexRequest,db : AsyncSession = Depends(get_db)):
    try:
        response = await get_chat_service().sharepoint_index(request.department, db)
        return response 
    except Exception as exc:
        print(repr(exc))
        raise HTTPException(
        status_code=500,
        detail=str(exc)
        )
    
            


@chatbot_router.post("/chat", response_model=ApiResponse[ChatResponse], status_code=status.HTTP_200_OK)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """Main chat endpoint - full RAG pipeline"""
    try:
        chat_service = get_chat_service()
        response = await chat_service.process_message(
            user_id=request.user_id,
            question=request.question,
            department=request.department,
            conversation_id=request.conversation_id,
            db=db
        )

        return ApiResponse(
            success=True,
            message="Chat response generated successfully",
            data=ChatResponse.model_validate(response),
        )

    except ValueError as exc:
        return ApiResponse(
            success=False,
            message=str(exc),
            errors={"validation": str(exc)},
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            message="Failed to process chat message",
            errors={"error": str(exc)},
        )


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _stream_event(evt: dict) -> dict:
    payload = dict(evt["data"])
    payload["isCompleted"] = evt["type"] == "done"
    return payload


@chatbot_router.post("/chat/stream", status_code=status.HTTP_200_OK)
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """Streamed RAG chat (SSE events: start, token, done).

    Every event carries ``isCompleted`` (bool); the final ``done`` event is
    ``true`` and also carries ``metadata.isRequireFeedback`` so the frontend
    knows whether to prompt for a rating.
    """
    async def event_generator():
        try:
            chat_service = get_chat_service()
            async for evt in chat_service.process_message_stream(
                user_id=request.user_id,
                question=request.question,
                department=request.department,
                conversation_id=request.conversation_id,
                db=db,
            ):
                yield _sse(evt["type"], _stream_event(evt))
        except Exception as exc:
            yield _sse("error", {"error": str(exc), "isCompleted": True})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@chatbot_router.post("/feedback", response_model=ApiResponse[FeedbackResponse], status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    request: ChatFeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """Submit feedback (rating 1-5 + optional message) for a chat."""
    try:
        chat_service = get_chat_service()
        feedback = await chat_service.submit_feedback(
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            rating=request.rating,
            message=request.message,
            db=db,
        )

        return ApiResponse(
            success=True,
            message="Feedback submitted successfully",
            data=FeedbackResponse.model_validate(feedback),
        )
    except ValueError as exc:
        return ApiResponse(
            success=False,
            message=str(exc),
            errors={"validation": str(exc)},
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            message="Failed to submit feedback",
            errors={"error": str(exc)},
        )


@chatbot_router.post("/sync", response_model=ApiResponse[SyncResponse], status_code=status.HTTP_202_ACCEPTED)
async def sync_documents(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Trigger document sync as a background job (non-blocking)"""
    try:
        ingestion = get_ingestion_service()
        job = await ingestion.create_sync_job(db)
        background_tasks.add_task(ingestion.run_sync_job, str(job.id))

        return ApiResponse(
            success=True,
            message="Document sync started in background",
            data=SyncResponse(
                status="started",
                message="Sync running in background",
                stats=SyncStats(),
            ),
        )

    except Exception as exc:
        return ApiResponse(
            success=False,
            message="Failed to start document sync",
            errors={"error": str(exc)},
        )


@chatbot_router.get("/sync/status", response_model=ApiResponse[SyncStatusResponse], status_code=status.HTTP_200_OK)
async def sync_status(
    db: AsyncSession = Depends(get_db)
):
    """Get sync status"""
    try:
        ingestion = get_ingestion_service()
        status_data = await ingestion.get_sync_status(db)
        return ApiResponse(
            success=True,
            message="Sync status retrieved successfully",
            data=SyncStatusResponse.model_validate(status_data),
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            message="Failed to retrieve sync status",
            errors={"error": str(exc)},
        )


@chatbot_router.get("/conversations", response_model=ApiResponse[ConversationCollection], status_code=status.HTTP_200_OK)
async def list_conversations(
    db: AsyncSession = Depends(get_db)
):
    """List conversations"""
    try:
        from app.modules.chatbot.repositories.chat_repository import ChatRepository

        repository = ChatRepository(db)
        conversations = await repository.list_recent_conversations()

        return ApiResponse(
            success=True,
            message="Conversations retrieved successfully",
            data=ConversationCollection(
                conversations=[ConversationResponse.model_validate(conversation) for conversation in conversations]
            ),
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            message="Failed to retrieve conversations",
            errors={"error": str(exc)},
        )
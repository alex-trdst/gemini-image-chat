"""
Image Chat REST API Routes

세션 관리, 메시지, 이미지 생성 엔드포인트
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.image_chat import (
    ChatMessageCreate,
    GenerateImageRequest,
    ImageChatMessageResponse,
    ImageChatSessionCreate,
    ImageChatSessionDetailResponse,
    ImageChatSessionResponse,
    ImagePurposePresetResponse,
    RefineImageRequest,
    SessionListResponse,
    SessionStatus,
)
from src.services.image_chat_service import ImageChatService
from src.storage.database import get_db

router = APIRouter(prefix="/api/image-chat", tags=["image-chat"])


def get_service(db: AsyncSession = Depends(get_db)) -> ImageChatService:
    """서비스 의존성"""
    return ImageChatService(db)


# =============================================================================
# Session Endpoints
# =============================================================================


@router.post("/sessions", response_model=ImageChatSessionResponse)
async def create_session(
    data: ImageChatSessionCreate,
    service: ImageChatService = Depends(get_service),
):
    """새 채팅 세션 생성"""
    return await service.create_session(data)


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    limit: int = 20,
    offset: int = 0,
    status: Optional[SessionStatus] = None,
    service: ImageChatService = Depends(get_service),
):
    """채팅 세션 목록 조회"""
    sessions, total = await service.list_sessions(limit=limit, offset=offset, status=status)
    return SessionListResponse(
        sessions=sessions,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/sessions/{session_id}", response_model=ImageChatSessionDetailResponse)
async def get_session(
    session_id: str,
    service: ImageChatService = Depends(get_service),
):
    """채팅 세션 상세 조회 (메시지 포함)"""
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return session


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    service: ImageChatService = Depends(get_service),
):
    """채팅 세션 삭제"""
    deleted = await service.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return {"message": "세션이 삭제되었습니다.", "session_id": session_id}


# =============================================================================
# Chat Endpoints
# =============================================================================


@router.post("/sessions/{session_id}/message", response_model=ImageChatMessageResponse)
async def send_message(
    session_id: str,
    data: ChatMessageCreate,
    service: ImageChatService = Depends(get_service),
):
    """채팅 메시지 전송"""
    try:
        return await service.send_message(session_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Image Generation Endpoints
# =============================================================================


@router.post("/sessions/{session_id}/generate", response_model=ImageChatMessageResponse)
async def generate_image(
    session_id: str,
    data: GenerateImageRequest,
    service: ImageChatService = Depends(get_service),
):
    """이미지 생성"""
    try:
        return await service.generate_image(session_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/{session_id}/refine", response_model=ImageChatMessageResponse)
async def refine_image(
    session_id: str,
    data: RefineImageRequest,
    service: ImageChatService = Depends(get_service),
):
    """이미지 개선 (Multi-turn)"""
    try:
        return await service.refine_image(session_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Presets Endpoints
# =============================================================================


@router.get("/purposes", response_model=list[ImagePurposePresetResponse])
async def get_purpose_presets(
    service: ImageChatService = Depends(get_service),
):
    """이미지 용도 프리셋 목록"""
    return service.get_purpose_presets()

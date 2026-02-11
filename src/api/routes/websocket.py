"""
WebSocket Routes

실시간 채팅 WebSocket 엔드포인트
세션/메시지 DB 저장 및 Shopify 이미지 업로드 지원
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.modules.gemini_image import GeminiImageService
from src.modules.shopify_files import ShopifyFilesService
from src.schemas.image_chat import ContentType, ImagePurpose, MessageRole, StylePreset
from src.storage.database import AsyncSessionLocal
from src.storage.models import GeneratedMarketingImage, ImageChatMessage, ImageChatSession

router = APIRouter(tags=["websocket"])

# 활성 연결 관리
active_connections: dict[str, WebSocket] = {}


async def save_message(
    db: AsyncSession,
    session_id: str,
    role: MessageRole,
    content_type: ContentType,
    text_content: Optional[str] = None,
    image_url: Optional[str] = None,
    generation_time_ms: Optional[int] = None,
    generation_metadata: Optional[dict] = None,
) -> ImageChatMessage:
    """메시지를 DB에 저장"""
    message = ImageChatMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role=role.value,
        content_type=content_type.value,
        text_content=text_content,
        image_url=image_url,
        generation_time_ms=generation_time_ms,
        generation_metadata=generation_metadata,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def update_session_counts(
    db: AsyncSession,
    session_id: str,
    messages_added: int = 0,
    images_added: int = 0,
    final_image_url: Optional[str] = None,
):
    """세션 카운트 업데이트"""
    result = await db.execute(
        select(ImageChatSession).where(ImageChatSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session:
        session.messages_count += messages_added
        session.images_generated += images_added
        if final_image_url:
            session.final_image_url = final_image_url
        await db.commit()


@router.websocket("/ws/image-chat/{session_id}")
async def image_chat_websocket(
    websocket: WebSocket,
    session_id: str,
):
    """
    실시간 이미지 채팅 WebSocket

    메시지 타입:
    - chat: 텍스트 대화
    - generate: 이미지 생성 요청
    - refine: 이미지 개선 요청

    응답 타입:
    - message: 텍스트 응답
    - image: 이미지 생성 완료
    - status: 상태 업데이트
    - error: 에러 발생
    """
    await websocket.accept()
    active_connections[session_id] = websocket

    settings = get_settings()

    # Gemini 서비스 초기화
    gemini_service = None
    if settings.gemini_api_key:
        gemini_service = GeminiImageService(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        )

    # Shopify 서비스 초기화
    shopify_service = None
    if settings.shopify_store_url and settings.shopify_client_id and settings.shopify_client_secret:
        shopify_service = ShopifyFilesService(
            store_url=settings.shopify_store_url,
            client_id=settings.shopify_client_id,
            client_secret=settings.shopify_client_secret,
        )

    try:
        # 연결 성공 메시지
        await websocket.send_json({
            "type": "status",
            "content": "연결되었습니다.",
            "data": {"session_id": session_id},
            "timestamp": datetime.utcnow().isoformat(),
        })

        while True:
            # 클라이언트 메시지 수신
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type", "chat")
            content = message.get("content", "")
            msg_data = message.get("data", {})

            # 용도와 스타일 파싱
            purpose_str = msg_data.get("purpose", "sns_instagram_square")
            style_str = msg_data.get("style")

            try:
                purpose = ImagePurpose(purpose_str)
            except ValueError:
                purpose = ImagePurpose.SNS_INSTAGRAM_SQUARE

            style = None
            if style_str:
                try:
                    style = StylePreset(style_str)
                except ValueError:
                    pass

            if not gemini_service:
                await websocket.send_json({
                    "type": "error",
                    "content": "GEMINI_API_KEY가 설정되지 않았습니다.",
                    "timestamp": datetime.utcnow().isoformat(),
                })
                continue

            try:
                async with AsyncSessionLocal() as db:
                    # 통합 대화 모드 (converse) - 기본값
                    # 기존 chat/generate/refine도 호환성 유지
                    if msg_type in ("converse", "chat", "generate", "refine"):
                        await websocket.send_json({
                            "type": "status",
                            "content": "생각 중...",
                            "timestamp": datetime.utcnow().isoformat(),
                        })

                        # 사용자 메시지 저장
                        await save_message(
                            db=db,
                            session_id=session_id,
                            role=MessageRole.USER,
                            content_type=ContentType.TEXT,
                            text_content=content,
                        )

                        # 이전 이미지 URL 조회 (이미지 수정 컨텍스트용)
                        previous_image_url = None
                        previous_image_result = await db.execute(
                            select(ImageChatMessage)
                            .where(ImageChatMessage.session_id == session_id)
                            .where(ImageChatMessage.content_type == ContentType.IMAGE.value)
                            .order_by(ImageChatMessage.created_at.desc())
                            .limit(1)
                        )
                        previous_image_msg = previous_image_result.scalar_one_or_none()
                        if previous_image_msg:
                            previous_image_url = previous_image_msg.image_url

                        # 통합 대화 API 호출
                        response = await gemini_service.converse(
                            session_id=session_id,
                            message=content,
                            purpose=purpose,
                            style=style,
                            previous_image_url=previous_image_url,
                        )

                        # 이미지가 생성된 경우
                        image_url = None
                        if response.image:
                            if not shopify_service:
                                raise ValueError("Shopify 서비스가 설정되지 않았습니다.")

                            await websocket.send_json({
                                "type": "status",
                                "content": "이미지 저장 중...",
                                "timestamp": datetime.utcnow().isoformat(),
                            })

                            uploaded = await shopify_service.upload_base64_image(
                                base64_data=response.image.image_base64,
                                filename=f"trdst-{session_id[:8]}-{uuid.uuid4().hex[:8]}.png",
                                mime_type=response.image.mime_type,
                                alt=f"TRDST 마케팅 이미지: {content[:50]}",
                            )
                            image_url = uploaded.url

                            # 이미지 레코드 저장
                            assistant_msg = await save_message(
                                db=db,
                                session_id=session_id,
                                role=MessageRole.ASSISTANT,
                                content_type=ContentType.IMAGE,
                                text_content=response.text,
                                image_url=image_url,
                                generation_time_ms=response.generation_time_ms,
                                generation_metadata={
                                    "prompt_used": response.image.prompt_used,
                                    "model_used": response.image.model_used,
                                    "width": response.image.width,
                                    "height": response.image.height,
                                },
                            )

                            image_record = GeneratedMarketingImage(
                                id=str(uuid.uuid4()),
                                session_id=session_id,
                                message_id=assistant_msg.id,
                                image_url=image_url,
                                width=response.image.width,
                                height=response.image.height,
                                format=response.image.mime_type.split("/")[-1] if "/" in response.image.mime_type else "png",
                                prompt_used=response.image.prompt_used,
                                model_used=response.image.model_used,
                                image_purpose=purpose.value,
                            )
                            db.add(image_record)
                            await db.commit()

                            # 세션 카운트 업데이트
                            await update_session_counts(
                                db, session_id,
                                messages_added=2,
                                images_added=1,
                                final_image_url=image_url,
                            )

                            # 혼합 응답 (텍스트 + 이미지)
                            await websocket.send_json({
                                "type": "mixed",
                                "content": response.text,
                                "image_url": image_url,
                                "data": {
                                    "prompt_used": response.image.prompt_used,
                                    "model_used": response.image.model_used,
                                    "width": response.image.width,
                                    "height": response.image.height,
                                    "generation_time_ms": response.generation_time_ms,
                                },
                                "timestamp": datetime.utcnow().isoformat(),
                            })
                        else:
                            # 텍스트만 응답
                            await save_message(
                                db=db,
                                session_id=session_id,
                                role=MessageRole.ASSISTANT,
                                content_type=ContentType.TEXT,
                                text_content=response.text,
                                generation_time_ms=response.generation_time_ms,
                            )

                            await update_session_counts(db, session_id, messages_added=2)

                            await websocket.send_json({
                                "type": "message",
                                "content": response.text,
                                "data": {
                                    "generation_time_ms": response.generation_time_ms,
                                },
                                "timestamp": datetime.utcnow().isoformat(),
                            })

                    else:
                        await websocket.send_json({
                            "type": "error",
                            "content": f"알 수 없는 메시지 타입: {msg_type}",
                            "timestamp": datetime.utcnow().isoformat(),
                        })

            except Exception as e:
                logger.error(f"WebSocket 처리 오류: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "content": f"오류 발생: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat(),
                })

    except WebSocketDisconnect:
        # 연결 종료
        if session_id in active_connections:
            del active_connections[session_id]
        if gemini_service:
            gemini_service.clear_session(session_id)

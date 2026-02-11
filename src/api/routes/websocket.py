"""
WebSocket Routes

실시간 채팅 WebSocket 엔드포인트
세션/메시지 DB 저장 및 Shopify 이미지 업로드 지원
"""

import json
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.modules.gemini_image import GeminiImageService
from src.modules.shopify_files import ShopifyFilesService
from src.schemas.image_chat import ContentType, ImagePurpose, MessageRole, StylePreset
from src.storage.database import async_session_maker
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
    if settings.shopify_store_url and settings.shopify_access_token:
        shopify_service = ShopifyFilesService(
            store_url=settings.shopify_store_url,
            access_token=settings.shopify_access_token,
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
                async with async_session_maker() as db:
                    if msg_type == "chat":
                        # 텍스트 대화
                        await websocket.send_json({
                            "type": "status",
                            "content": "응답 생성 중...",
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

                        response = await gemini_service.chat(
                            session_id=session_id,
                            message=content,
                            purpose=purpose,
                            generate_image=False,
                            style=style,
                        )

                        # 어시스턴트 응답 저장
                        await save_message(
                            db=db,
                            session_id=session_id,
                            role=MessageRole.ASSISTANT,
                            content_type=ContentType.TEXT,
                            text_content=response.text,
                            generation_time_ms=response.generation_time_ms,
                        )

                        # 세션 카운트 업데이트
                        await update_session_counts(db, session_id, messages_added=2)

                        await websocket.send_json({
                            "type": "message",
                            "content": response.text,
                            "data": {
                                "generation_time_ms": response.generation_time_ms,
                            },
                            "timestamp": datetime.utcnow().isoformat(),
                        })

                    elif msg_type == "generate":
                        # 이미지 생성
                        await websocket.send_json({
                            "type": "status",
                            "content": "이미지 생성 중...",
                            "timestamp": datetime.utcnow().isoformat(),
                        })

                        # 사용자 메시지 저장
                        await save_message(
                            db=db,
                            session_id=session_id,
                            role=MessageRole.USER,
                            content_type=ContentType.TEXT,
                            text_content=f"[이미지 생성] {content}",
                        )

                        generated = await gemini_service.generate_image(
                            prompt=content,
                            purpose=purpose,
                            style=style,
                            session_id=session_id,
                        )

                        # Shopify에 업로드하거나 base64 사용
                        if shopify_service:
                            await websocket.send_json({
                                "type": "status",
                                "content": "이미지 저장 중...",
                                "timestamp": datetime.utcnow().isoformat(),
                            })

                            try:
                                uploaded = await shopify_service.upload_base64_image(
                                    base64_data=generated.image_base64,
                                    filename=f"trdst-{session_id[:8]}-{uuid.uuid4().hex[:8]}.png",
                                    mime_type=generated.mime_type,
                                    alt=f"TRDST 마케팅 이미지: {content[:50]}",
                                )
                                image_url = uploaded.url
                            except Exception as e:
                                # Shopify 업로드 실패 시 base64 사용
                                print(f"Shopify 업로드 실패: {e}")
                                image_url = f"data:{generated.mime_type};base64,{generated.image_base64}"
                        else:
                            image_url = f"data:{generated.mime_type};base64,{generated.image_base64}"

                        # 어시스턴트 응답 저장
                        assistant_msg = await save_message(
                            db=db,
                            session_id=session_id,
                            role=MessageRole.ASSISTANT,
                            content_type=ContentType.IMAGE,
                            text_content="이미지가 생성되었습니다.",
                            image_url=image_url,
                            generation_time_ms=generated.generation_time_ms,
                            generation_metadata={
                                "prompt_used": generated.prompt_used,
                                "model_used": generated.model_used,
                                "width": generated.width,
                                "height": generated.height,
                            },
                        )

                        # 이미지 레코드 저장
                        image_record = GeneratedMarketingImage(
                            id=str(uuid.uuid4()),
                            session_id=session_id,
                            message_id=assistant_msg.id,
                            image_url=image_url,
                            width=generated.width,
                            height=generated.height,
                            format=generated.mime_type.split("/")[-1] if "/" in generated.mime_type else "png",
                            prompt_used=generated.prompt_used,
                            model_used=generated.model_used,
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

                        await websocket.send_json({
                            "type": "image",
                            "content": "이미지가 생성되었습니다.",
                            "image_url": image_url,
                            "data": {
                                "prompt_used": generated.prompt_used,
                                "model_used": generated.model_used,
                                "width": generated.width,
                                "height": generated.height,
                                "generation_time_ms": generated.generation_time_ms,
                            },
                            "timestamp": datetime.utcnow().isoformat(),
                        })

                    elif msg_type == "refine":
                        # 이미지 개선
                        await websocket.send_json({
                            "type": "status",
                            "content": "이미지 개선 중...",
                            "timestamp": datetime.utcnow().isoformat(),
                        })

                        # 사용자 메시지 저장
                        await save_message(
                            db=db,
                            session_id=session_id,
                            role=MessageRole.USER,
                            content_type=ContentType.TEXT,
                            text_content=f"[이미지 개선] {content}",
                        )

                        generated = await gemini_service.refine_image(
                            session_id=session_id,
                            feedback=content,
                            purpose=purpose,
                        )

                        # Shopify에 업로드하거나 base64 사용
                        if shopify_service:
                            await websocket.send_json({
                                "type": "status",
                                "content": "이미지 저장 중...",
                                "timestamp": datetime.utcnow().isoformat(),
                            })

                            try:
                                uploaded = await shopify_service.upload_base64_image(
                                    base64_data=generated.image_base64,
                                    filename=f"trdst-{session_id[:8]}-{uuid.uuid4().hex[:8]}.png",
                                    mime_type=generated.mime_type,
                                    alt=f"TRDST 마케팅 이미지 (개선): {content[:50]}",
                                )
                                image_url = uploaded.url
                            except Exception as e:
                                print(f"Shopify 업로드 실패: {e}")
                                image_url = f"data:{generated.mime_type};base64,{generated.image_base64}"
                        else:
                            image_url = f"data:{generated.mime_type};base64,{generated.image_base64}"

                        # 어시스턴트 응답 저장
                        assistant_msg = await save_message(
                            db=db,
                            session_id=session_id,
                            role=MessageRole.ASSISTANT,
                            content_type=ContentType.IMAGE,
                            text_content="이미지가 개선되었습니다.",
                            image_url=image_url,
                            generation_time_ms=generated.generation_time_ms,
                            generation_metadata={
                                "prompt_used": generated.prompt_used,
                                "model_used": generated.model_used,
                                "width": generated.width,
                                "height": generated.height,
                            },
                        )

                        # 이미지 레코드 저장
                        image_record = GeneratedMarketingImage(
                            id=str(uuid.uuid4()),
                            session_id=session_id,
                            message_id=assistant_msg.id,
                            image_url=image_url,
                            width=generated.width,
                            height=generated.height,
                            format=generated.mime_type.split("/")[-1] if "/" in generated.mime_type else "png",
                            prompt_used=generated.prompt_used,
                            model_used=generated.model_used,
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

                        await websocket.send_json({
                            "type": "image",
                            "content": "이미지가 개선되었습니다.",
                            "image_url": image_url,
                            "data": {
                                "prompt_used": generated.prompt_used,
                                "model_used": generated.model_used,
                                "width": generated.width,
                                "height": generated.height,
                                "generation_time_ms": generated.generation_time_ms,
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

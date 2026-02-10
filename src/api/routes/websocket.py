"""
WebSocket Routes

실시간 채팅 WebSocket 엔드포인트
"""

import json
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.config import get_settings
from src.modules.gemini_image import GeminiImageService
from src.schemas.image_chat import ImagePurpose, StylePreset

router = APIRouter(tags=["websocket"])

# 활성 연결 관리
active_connections: dict[str, WebSocket] = {}


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
                if msg_type == "chat":
                    # 텍스트 대화
                    await websocket.send_json({
                        "type": "status",
                        "content": "응답 생성 중...",
                        "timestamp": datetime.utcnow().isoformat(),
                    })

                    response = await gemini_service.chat(
                        session_id=session_id,
                        message=content,
                        purpose=purpose,
                        generate_image=False,
                        style=style,
                    )

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

                    generated = await gemini_service.generate_image(
                        prompt=content,
                        purpose=purpose,
                        style=style,
                        session_id=session_id,
                    )

                    image_url = f"data:{generated.mime_type};base64,{generated.image_base64}"

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

                    generated = await gemini_service.refine_image(
                        session_id=session_id,
                        feedback=content,
                        purpose=purpose,
                    )

                    image_url = f"data:{generated.mime_type};base64,{generated.image_base64}"

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

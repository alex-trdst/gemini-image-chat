"""
Image Chat Service

마케팅 이미지 채팅 비즈니스 로직
세션 관리, 메시지 저장, Gemini API 호출 orchestration
"""

import uuid
from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.modules.gemini_image import GeminiImageService
from src.schemas.image_chat import (
    IMAGE_PURPOSE_PRESETS,
    ChatMessageCreate,
    ContentType,
    GenerateImageRequest,
    ImageChatMessageResponse,
    ImageChatSessionCreate,
    ImageChatSessionDetailResponse,
    ImageChatSessionResponse,
    ImagePurpose,
    ImagePurposePresetResponse,
    MessageRole,
    RefineImageRequest,
    SessionStatus,
    StylePreset,
)
from src.storage.models import GeneratedMarketingImage, ImageChatMessage, ImageChatSession


class ImageChatService:
    """이미지 채팅 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        settings = get_settings()
        self._gemini_service: Optional[GeminiImageService] = None

        if settings.gemini_api_key:
            self._gemini_service = GeminiImageService(
                api_key=settings.gemini_api_key,
                model=settings.gemini_model,
            )

    @property
    def gemini_service(self) -> GeminiImageService:
        """Gemini 서비스 반환 (API 키 필요)"""
        if not self._gemini_service:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
        return self._gemini_service

    # =========================================================================
    # Session Management
    # =========================================================================

    async def create_session(
        self,
        data: ImageChatSessionCreate,
    ) -> ImageChatSessionResponse:
        """세션 생성"""
        session_id = str(uuid.uuid4())

        session = ImageChatSession(
            id=session_id,
            title=data.title,
            image_purpose=data.image_purpose.value,
            status=SessionStatus.ACTIVE.value,
            style_preset=data.style_preset.value if data.style_preset else None,
            brand_guidelines=data.brand_guidelines,
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return ImageChatSessionResponse.model_validate(session)

    async def get_session(
        self,
        session_id: str,
    ) -> Optional[ImageChatSessionDetailResponse]:
        """세션 상세 조회 (메시지 포함)"""
        result = await self.db.execute(
            select(ImageChatSession).where(ImageChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        # 메시지 조회
        messages_result = await self.db.execute(
            select(ImageChatMessage)
            .where(ImageChatMessage.session_id == session_id)
            .order_by(ImageChatMessage.created_at)
        )
        messages = messages_result.scalars().all()

        return ImageChatSessionDetailResponse(
            id=session.id,
            title=session.title,
            image_purpose=session.image_purpose,
            status=SessionStatus(session.status),
            style_preset=session.style_preset,
            final_image_url=session.final_image_url,
            messages_count=session.messages_count,
            images_generated=session.images_generated,
            total_tokens_used=session.total_tokens_used,
            created_at=session.created_at,
            updated_at=session.updated_at,
            messages=[ImageChatMessageResponse.model_validate(m) for m in messages],
        )

    async def list_sessions(
        self,
        limit: int = 20,
        offset: int = 0,
        status: Optional[SessionStatus] = None,
    ) -> tuple[list[ImageChatSessionResponse], int]:
        """세션 목록 조회"""
        query = select(ImageChatSession)

        if status:
            query = query.where(ImageChatSession.status == status.value)

        # 총 개수
        count_query = select(ImageChatSession)
        if status:
            count_query = count_query.where(ImageChatSession.status == status.value)
        count_result = await self.db.execute(count_query)
        total = len(count_result.scalars().all())

        # 페이지네이션
        query = query.order_by(desc(ImageChatSession.created_at)).limit(limit).offset(offset)
        result = await self.db.execute(query)
        sessions = result.scalars().all()

        return [ImageChatSessionResponse.model_validate(s) for s in sessions], total

    async def delete_session(self, session_id: str) -> bool:
        """세션 삭제"""
        result = await self.db.execute(
            select(ImageChatSession).where(ImageChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return False

        # 관련 메시지 삭제
        messages_result = await self.db.execute(
            select(ImageChatMessage).where(ImageChatMessage.session_id == session_id)
        )
        messages = messages_result.scalars().all()
        for msg in messages:
            await self.db.delete(msg)

        # 관련 이미지 삭제
        images_result = await self.db.execute(
            select(GeneratedMarketingImage).where(
                GeneratedMarketingImage.session_id == session_id
            )
        )
        images = images_result.scalars().all()
        for img in images:
            await self.db.delete(img)

        # 세션 삭제
        await self.db.delete(session)
        await self.db.commit()

        # Gemini 세션 히스토리 삭제
        if self._gemini_service:
            self._gemini_service.clear_session(session_id)

        return True

    # =========================================================================
    # Chat & Message
    # =========================================================================

    async def send_message(
        self,
        session_id: str,
        data: ChatMessageCreate,
    ) -> ImageChatMessageResponse:
        """메시지 전송 (텍스트 대화)"""
        # 세션 확인
        result = await self.db.execute(
            select(ImageChatSession).where(ImageChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError(f"세션을 찾을 수 없습니다: {session_id}")

        # 사용자 메시지 저장
        await self._save_message(
            session_id=session_id,
            role=MessageRole.USER,
            content_type=ContentType.TEXT,
            text_content=data.content,
        )

        # Gemini 채팅 응답 생성
        purpose = ImagePurpose(session.image_purpose)
        style = StylePreset(session.style_preset) if session.style_preset else None

        response = await self.gemini_service.chat(
            session_id=session_id,
            message=data.content,
            purpose=purpose,
            generate_image=False,
            style=style,
        )

        # 어시스턴트 응답 저장
        assistant_message = await self._save_message(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content_type=ContentType.TEXT,
            text_content=response.text,
            tokens_used=response.tokens_used,
            generation_time_ms=response.generation_time_ms,
        )

        # 세션 업데이트
        session.messages_count += 2
        session.total_tokens_used += response.tokens_used
        await self.db.commit()

        return ImageChatMessageResponse.model_validate(assistant_message)

    async def _save_message(
        self,
        session_id: str,
        role: MessageRole,
        content_type: ContentType,
        text_content: Optional[str] = None,
        image_url: Optional[str] = None,
        image_thumbnail_url: Optional[str] = None,
        tokens_used: int = 0,
        generation_time_ms: Optional[int] = None,
        generation_metadata: Optional[dict] = None,
    ) -> ImageChatMessage:
        """메시지 저장"""
        message = ImageChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role.value,
            content_type=content_type.value,
            text_content=text_content,
            image_url=image_url,
            image_thumbnail_url=image_thumbnail_url,
            tokens_used=tokens_used,
            generation_time_ms=generation_time_ms,
            generation_metadata=generation_metadata,
        )

        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        return message

    # =========================================================================
    # Image Generation
    # =========================================================================

    async def generate_image(
        self,
        session_id: str,
        data: GenerateImageRequest,
    ) -> ImageChatMessageResponse:
        """이미지 생성"""
        # 세션 확인
        result = await self.db.execute(
            select(ImageChatSession).where(ImageChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError(f"세션을 찾을 수 없습니다: {session_id}")

        # 사용자 요청 메시지 저장
        await self._save_message(
            session_id=session_id,
            role=MessageRole.USER,
            content_type=ContentType.TEXT,
            text_content=f"[이미지 생성 요청] {data.prompt}",
        )

        # 이미지 생성
        purpose = ImagePurpose(session.image_purpose)
        style = data.style_preset or (
            StylePreset(session.style_preset) if session.style_preset else None
        )

        generated = await self.gemini_service.generate_image(
            prompt=data.prompt,
            purpose=purpose,
            style=style,
            session_id=session_id,
        )

        # 이미지를 Data URL로 변환 (실제 프로덕션에서는 R2/S3에 업로드)
        image_url = f"data:{generated.mime_type};base64,{generated.image_base64}"

        # 어시스턴트 응답 메시지 저장
        message = await self._save_message(
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

        # 생성된 이미지 레코드 저장
        image_record = GeneratedMarketingImage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            message_id=message.id,
            image_url=image_url,
            width=generated.width,
            height=generated.height,
            format=generated.mime_type.split("/")[-1] if "/" in generated.mime_type else "png",
            prompt_used=generated.prompt_used,
            model_used=generated.model_used,
            image_purpose=session.image_purpose,
        )
        self.db.add(image_record)

        # 세션 업데이트
        session.messages_count += 2
        session.images_generated += 1
        session.final_image_url = image_url
        await self.db.commit()
        await self.db.refresh(message)

        return ImageChatMessageResponse.model_validate(message)

    async def refine_image(
        self,
        session_id: str,
        data: RefineImageRequest,
    ) -> ImageChatMessageResponse:
        """이미지 개선"""
        # 세션 확인
        result = await self.db.execute(
            select(ImageChatSession).where(ImageChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError(f"세션을 찾을 수 없습니다: {session_id}")

        # 사용자 피드백 메시지 저장
        await self._save_message(
            session_id=session_id,
            role=MessageRole.USER,
            content_type=ContentType.TEXT,
            text_content=f"[이미지 개선 요청] {data.feedback}",
        )

        # 이미지 개선
        purpose = ImagePurpose(session.image_purpose)

        generated = await self.gemini_service.refine_image(
            session_id=session_id,
            feedback=data.feedback,
            purpose=purpose,
        )

        # 이미지를 Data URL로 변환
        image_url = f"data:{generated.mime_type};base64,{generated.image_base64}"

        # 어시스턴트 응답 메시지 저장
        message = await self._save_message(
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
                "refined_from": data.image_id,
            },
        )

        # 생성된 이미지 레코드 저장
        image_record = GeneratedMarketingImage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            message_id=message.id,
            image_url=image_url,
            width=generated.width,
            height=generated.height,
            format=generated.mime_type.split("/")[-1] if "/" in generated.mime_type else "png",
            prompt_used=generated.prompt_used,
            model_used=generated.model_used,
            image_purpose=session.image_purpose,
        )
        self.db.add(image_record)

        # 세션 업데이트
        session.messages_count += 2
        session.images_generated += 1
        session.final_image_url = image_url
        await self.db.commit()
        await self.db.refresh(message)

        return ImageChatMessageResponse.model_validate(message)

    # =========================================================================
    # Purpose Presets
    # =========================================================================

    def get_purpose_presets(self) -> list[ImagePurposePresetResponse]:
        """이미지 용도 프리셋 목록 반환"""
        return [
            ImagePurposePresetResponse(
                id=purpose.value,
                name=preset["name"],
                ratio=preset["ratio"],
                width=preset.get("width"),
                height=preset.get("height"),
                description=preset["description"],
            )
            for purpose, preset in IMAGE_PURPOSE_PRESETS.items()
        ]

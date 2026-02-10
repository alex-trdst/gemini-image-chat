"""
Database Models

이미지 채팅 관련 데이터 모델
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.storage.database import Base


class ImageChatSession(Base):
    """마케팅 이미지 채팅 세션"""

    __tablename__ = "image_chat_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    image_purpose: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # sns_instagram, sns_facebook, banner_web, etc.
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False
    )  # active, completed, archived
    style_preset: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # modern, minimal, vibrant, etc.
    brand_guidelines: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)

    # 생성된 최종 이미지
    final_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 메타데이터
    messages_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    images_generated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )


class ImageChatMessage(Base):
    """이미지 채팅 메시지"""

    __tablename__ = "image_chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("image_chat_sessions.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant
    content_type: Mapped[str] = mapped_column(String(20), nullable=False)  # text, image, mixed

    # 콘텐츠
    text_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_thumbnail_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Gemini API 메타데이터
    generation_metadata: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generation_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )


class GeneratedMarketingImage(Base):
    """생성된 마케팅 이미지"""

    __tablename__ = "generated_marketing_images"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("image_chat_sessions.id"), nullable=False
    )
    message_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("image_chat_messages.id"), nullable=False
    )

    # 이미지 URL
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 이미지 메타데이터
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    format: Mapped[str] = mapped_column(String(10), default="png", nullable=False)

    # 생성 정보
    prompt_used: Mapped[str] = mapped_column(Text, nullable=False)
    model_used: Mapped[str] = mapped_column(String(50), nullable=False)
    image_purpose: Mapped[str] = mapped_column(String(50), nullable=False)
    generation_cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # 사용 여부
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_exported: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

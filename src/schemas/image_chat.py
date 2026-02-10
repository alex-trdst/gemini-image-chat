"""
이미지 채팅 Pydantic 스키마

Gemini 기반 마케팅 이미지 생성 채팅 서비스용 스키마 정의
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


class ImagePurpose(str, Enum):
    """이미지 용도"""

    SNS_INSTAGRAM_SQUARE = "sns_instagram_square"  # 1:1 (1080x1080)
    SNS_INSTAGRAM_PORTRAIT = "sns_instagram_portrait"  # 4:5 (1080x1350)
    SNS_FACEBOOK = "sns_facebook"  # 1.91:1 (1200x630)
    BANNER_WEB = "banner_web"  # 3:1 (1920x640)
    BANNER_MOBILE = "banner_mobile"  # 2:1 (800x400)
    PRODUCT_SHOWCASE = "product_showcase"  # 1:1 (1000x1000)
    EMAIL_HEADER = "email_header"  # 3:1 (600x200)
    CUSTOM = "custom"  # 사용자 정의


class StylePreset(str, Enum):
    """스타일 프리셋"""

    MODERN = "modern"
    MINIMAL = "minimal"
    VIBRANT = "vibrant"
    LUXURY = "luxury"
    PLAYFUL = "playful"
    PROFESSIONAL = "professional"
    NATURAL = "natural"
    TECH = "tech"


class SessionStatus(str, Enum):
    """세션 상태"""

    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class MessageRole(str, Enum):
    """메시지 역할"""

    USER = "user"
    ASSISTANT = "assistant"


class ContentType(str, Enum):
    """콘텐츠 유형"""

    TEXT = "text"
    IMAGE = "image"
    MIXED = "mixed"


# =============================================================================
# Image Purpose Presets (용도별 설정)
# =============================================================================


IMAGE_PURPOSE_PRESETS = {
    ImagePurpose.SNS_INSTAGRAM_SQUARE: {
        "name": "Instagram 정사각형",
        "ratio": "1:1",
        "width": 1080,
        "height": 1080,
        "description": "Instagram 피드용 정사각형 이미지",
    },
    ImagePurpose.SNS_INSTAGRAM_PORTRAIT: {
        "name": "Instagram 세로형",
        "ratio": "4:5",
        "width": 1080,
        "height": 1350,
        "description": "Instagram 피드용 세로형 이미지",
    },
    ImagePurpose.SNS_FACEBOOK: {
        "name": "Facebook 공유",
        "ratio": "1.91:1",
        "width": 1200,
        "height": 630,
        "description": "Facebook 공유 및 광고용 이미지",
    },
    ImagePurpose.BANNER_WEB: {
        "name": "웹 배너",
        "ratio": "3:1",
        "width": 1920,
        "height": 640,
        "description": "웹사이트 메인 배너용 이미지",
    },
    ImagePurpose.BANNER_MOBILE: {
        "name": "모바일 배너",
        "ratio": "2:1",
        "width": 800,
        "height": 400,
        "description": "모바일 웹/앱 배너용 이미지",
    },
    ImagePurpose.PRODUCT_SHOWCASE: {
        "name": "제품 쇼케이스",
        "ratio": "1:1",
        "width": 1000,
        "height": 1000,
        "description": "제품 상세페이지용 이미지",
    },
    ImagePurpose.EMAIL_HEADER: {
        "name": "이메일 헤더",
        "ratio": "3:1",
        "width": 600,
        "height": 200,
        "description": "이메일 마케팅 헤더 이미지",
    },
    ImagePurpose.CUSTOM: {
        "name": "사용자 정의",
        "ratio": "custom",
        "width": None,
        "height": None,
        "description": "사용자가 직접 크기 지정",
    },
}


# =============================================================================
# Request Schemas
# =============================================================================


class ImageChatSessionCreate(BaseModel):
    """세션 생성 요청"""

    title: Optional[str] = Field(None, max_length=200, description="세션 제목")
    image_purpose: ImagePurpose = Field(..., description="이미지 용도")
    style_preset: Optional[StylePreset] = Field(None, description="스타일 프리셋")
    brand_guidelines: Optional[dict] = Field(None, description="브랜드 가이드라인")


class ChatMessageCreate(BaseModel):
    """채팅 메시지 생성 요청"""

    content: str = Field(..., min_length=1, max_length=2000, description="메시지 내용")
    reference_image_url: Optional[str] = Field(None, description="참조 이미지 URL")


class GenerateImageRequest(BaseModel):
    """이미지 생성 요청"""

    prompt: str = Field(..., min_length=1, max_length=1000, description="이미지 생성 프롬프트")
    style_preset: Optional[StylePreset] = Field(None, description="스타일 프리셋")
    reference_image_url: Optional[str] = Field(None, description="참조 이미지 URL")
    custom_width: Optional[int] = Field(None, ge=256, le=4096, description="사용자 정의 너비")
    custom_height: Optional[int] = Field(None, ge=256, le=4096, description="사용자 정의 높이")


class RefineImageRequest(BaseModel):
    """이미지 개선 요청"""

    feedback: str = Field(..., min_length=1, max_length=500, description="개선 피드백")
    image_id: str = Field(..., description="개선할 이미지 ID")


# =============================================================================
# Response Schemas
# =============================================================================


class ImageChatMessageResponse(BaseModel):
    """채팅 메시지 응답"""

    id: str
    session_id: str
    role: MessageRole
    content_type: ContentType
    text_content: Optional[str] = None
    image_url: Optional[str] = None
    image_thumbnail_url: Optional[str] = None
    tokens_used: int = 0
    generation_time_ms: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ImageChatSessionResponse(BaseModel):
    """세션 응답"""

    id: str
    title: Optional[str] = None
    image_purpose: str
    status: SessionStatus
    style_preset: Optional[str] = None
    final_image_url: Optional[str] = None
    messages_count: int = 0
    images_generated: int = 0
    total_tokens_used: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ImageChatSessionDetailResponse(ImageChatSessionResponse):
    """세션 상세 응답 (메시지 포함)"""

    messages: list[ImageChatMessageResponse] = []


class GeneratedImageResponse(BaseModel):
    """생성된 이미지 응답"""

    id: str
    session_id: str
    message_id: str
    image_url: str
    thumbnail_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    format: str = "png"
    prompt_used: str
    model_used: str
    image_purpose: str
    generation_cost_usd: float = 0.0
    is_selected: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class ImagePurposePresetResponse(BaseModel):
    """이미지 용도 프리셋 응답"""

    id: str
    name: str
    ratio: str
    width: Optional[int] = None
    height: Optional[int] = None
    description: str


class SessionListResponse(BaseModel):
    """세션 목록 응답"""

    sessions: list[ImageChatSessionResponse]
    total: int
    limit: int
    offset: int


# =============================================================================
# WebSocket Schemas
# =============================================================================


class WebSocketMessage(BaseModel):
    """WebSocket 메시지"""

    type: str  # chat, generate, refine, status, error
    content: Optional[str] = None
    data: Optional[dict] = None


class WebSocketResponse(BaseModel):
    """WebSocket 응답"""

    type: str  # message, image, status, error
    content: Optional[str] = None
    image_url: Optional[str] = None
    data: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

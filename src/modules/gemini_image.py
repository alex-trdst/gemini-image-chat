"""
Gemini Image Service

Google Gemini API를 사용한 마케팅 이미지 생성 서비스
gemini-3-pro-image-preview (Nano Banana Pro) 모델 사용
Multi-turn 대화 지원으로 이미지 개선(refine) 가능
"""

import base64
import time
from dataclasses import dataclass
from typing import Optional

from google import genai
from google.genai import types

from src.schemas.image_chat import IMAGE_PURPOSE_PRESETS, ImagePurpose, StylePreset


@dataclass
class GeneratedImage:
    """생성된 이미지 정보"""

    image_data: bytes  # 이미지 바이너리 데이터
    image_base64: str  # Base64 인코딩된 이미지
    mime_type: str  # 이미지 MIME 타입 (image/png, image/jpeg)
    prompt_used: str  # 사용된 프롬프트
    model_used: str  # 사용된 모델명
    generation_time_ms: int  # 생성 소요 시간 (ms)
    width: Optional[int] = None
    height: Optional[int] = None


@dataclass
class ChatResponse:
    """채팅 응답"""

    text: Optional[str] = None
    image: Optional[GeneratedImage] = None
    tokens_used: int = 0
    generation_time_ms: int = 0


# 용도별 aspect ratio 매핑
PURPOSE_ASPECT_RATIOS = {
    ImagePurpose.SNS_INSTAGRAM_SQUARE: "1:1",
    ImagePurpose.SNS_INSTAGRAM_PORTRAIT: "9:16",  # 4:5에 가장 가까운 지원 비율
    ImagePurpose.SNS_FACEBOOK: "16:9",
    ImagePurpose.BANNER_WEB: "16:9",
    ImagePurpose.BANNER_MOBILE: "16:9",
    ImagePurpose.PRODUCT_SHOWCASE: "1:1",
    ImagePurpose.EMAIL_HEADER: "16:9",
    ImagePurpose.CUSTOM: "1:1",
}


class GeminiImageService:
    """Gemini 이미지 생성 서비스 (gemini-3-pro-image-preview)"""

    def __init__(self, api_key: str, model: str = "gemini-3-pro-image-preview"):
        """
        Args:
            api_key: Google AI API 키
            model: 사용할 모델명 (기본: gemini-3-pro-image-preview)
        """
        self.client = genai.Client(api_key=api_key)
        self.model = model

        # 세션별 채팅 히스토리 저장 (Multi-turn 지원)
        self._chat_sessions: dict[str, list[types.Content]] = {}

    def _get_aspect_ratio(self, purpose: ImagePurpose) -> str:
        """용도별 aspect ratio 반환"""
        return PURPOSE_ASPECT_RATIOS.get(purpose, "1:1")

    def _build_purpose_prompt(self, purpose: ImagePurpose, base_prompt: str) -> str:
        """용도별 프롬프트 최적화"""
        preset = IMAGE_PURPOSE_PRESETS.get(purpose, {})
        width = preset.get("width")
        height = preset.get("height")

        # 용도별 스타일 힌트 추가
        purpose_hints = {
            ImagePurpose.SNS_INSTAGRAM_SQUARE: "eye-catching social media post, vibrant colors, engaging composition",
            ImagePurpose.SNS_INSTAGRAM_PORTRAIT: "vertical composition, mobile-optimized, scroll-stopping visual",
            ImagePurpose.SNS_FACEBOOK: "shareable content, clear message, professional look",
            ImagePurpose.BANNER_WEB: "wide banner format, clean layout, brand-focused, text space on sides",
            ImagePurpose.BANNER_MOBILE: "mobile-friendly, simple composition, high contrast",
            ImagePurpose.PRODUCT_SHOWCASE: "product-focused, clean background, professional lighting",
            ImagePurpose.EMAIL_HEADER: "simple, brand-aligned, minimal text space",
        }

        hint = purpose_hints.get(purpose, "")
        size_hint = f"Image dimensions: {width}x{height}px. " if width and height else ""

        return f"{size_hint}{hint}. {base_prompt}"

    def _build_style_prompt(self, style: Optional[StylePreset], base_prompt: str) -> str:
        """스타일 프리셋 프롬프트 추가"""
        if not style:
            return base_prompt

        style_hints = {
            StylePreset.MODERN: "modern aesthetic, clean lines, contemporary design",
            StylePreset.MINIMAL: "minimalist style, white space, simple elements",
            StylePreset.VIBRANT: "vibrant colors, energetic mood, bold visual",
            StylePreset.LUXURY: "luxury feel, premium quality, sophisticated elegance",
            StylePreset.PLAYFUL: "playful, fun, colorful, friendly vibe",
            StylePreset.PROFESSIONAL: "professional, corporate, trustworthy appearance",
            StylePreset.NATURAL: "natural tones, organic feel, earthy colors",
            StylePreset.TECH: "tech-focused, futuristic, digital aesthetic",
        }

        hint = style_hints.get(style, "")
        return f"{base_prompt}. Style: {hint}"

    async def generate_image(
        self,
        prompt: str,
        purpose: ImagePurpose,
        style: Optional[StylePreset] = None,
        session_id: Optional[str] = None,
    ) -> GeneratedImage:
        """
        이미지 생성 (gemini-3-pro-image-preview)

        Args:
            prompt: 이미지 생성 프롬프트
            purpose: 이미지 용도
            style: 스타일 프리셋 (선택)
            session_id: 세션 ID (Multi-turn용, 선택)

        Returns:
            GeneratedImage: 생성된 이미지 정보
        """
        start_time = time.time()

        # 프롬프트 최적화
        optimized_prompt = self._build_purpose_prompt(purpose, prompt)
        if style:
            optimized_prompt = self._build_style_prompt(style, optimized_prompt)

        # Aspect ratio 설정
        aspect_ratio = self._get_aspect_ratio(purpose)

        # 이미지 생성 요청 (gemini-3-pro-image-preview 형식)
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=optimized_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                ),
            ),
        )

        # 응답에서 이미지 추출
        image_data = None
        mime_type = "image/png"

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data
                mime_type = part.inline_data.mime_type
                break

        if not image_data:
            raise ValueError("이미지 생성에 실패했습니다. 응답에 이미지가 없습니다.")

        generation_time_ms = int((time.time() - start_time) * 1000)

        # 세션에 히스토리 저장 (Multi-turn 지원)
        if session_id:
            if session_id not in self._chat_sessions:
                self._chat_sessions[session_id] = []
            self._chat_sessions[session_id].append(
                types.Content(
                    role="user",
                    parts=[types.Part(text=optimized_prompt)],
                )
            )
            self._chat_sessions[session_id].append(
                types.Content(
                    role="model",
                    parts=[types.Part(inline_data=types.Blob(mime_type=mime_type, data=image_data))],
                )
            )

        # 용도별 크기 정보
        preset = IMAGE_PURPOSE_PRESETS.get(purpose, {})

        return GeneratedImage(
            image_data=image_data,
            image_base64=base64.b64encode(image_data).decode("utf-8"),
            mime_type=mime_type,
            prompt_used=optimized_prompt,
            model_used=self.model,
            generation_time_ms=generation_time_ms,
            width=preset.get("width"),
            height=preset.get("height"),
        )

    async def refine_image(
        self,
        session_id: str,
        feedback: str,
        purpose: ImagePurpose,
    ) -> GeneratedImage:
        """
        이미지 개선 (Multi-turn 대화)

        Args:
            session_id: 세션 ID
            feedback: 개선 피드백
            purpose: 이미지 용도

        Returns:
            GeneratedImage: 개선된 이미지 정보
        """
        start_time = time.time()

        # 기존 히스토리 가져오기
        history = self._chat_sessions.get(session_id, [])
        if not history:
            raise ValueError(f"세션 {session_id}의 히스토리가 없습니다. 먼저 이미지를 생성해주세요.")

        # 개선 요청 추가
        refine_prompt = f"Please modify the previous image based on this feedback: {feedback}"

        # Aspect ratio 설정
        aspect_ratio = self._get_aspect_ratio(purpose)

        # 히스토리와 함께 새 요청
        contents = history + [
            types.Content(
                role="user",
                parts=[types.Part(text=refine_prompt)],
            )
        ]

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                ),
            ),
        )

        # 응답에서 이미지 추출
        image_data = None
        mime_type = "image/png"

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data
                mime_type = part.inline_data.mime_type
                break

        if not image_data:
            raise ValueError("이미지 개선에 실패했습니다. 응답에 이미지가 없습니다.")

        generation_time_ms = int((time.time() - start_time) * 1000)

        # 히스토리 업데이트
        self._chat_sessions[session_id].append(
            types.Content(
                role="user",
                parts=[types.Part(text=refine_prompt)],
            )
        )
        self._chat_sessions[session_id].append(
            types.Content(
                role="model",
                parts=[types.Part(inline_data=types.Blob(mime_type=mime_type, data=image_data))],
            )
        )

        preset = IMAGE_PURPOSE_PRESETS.get(purpose, {})

        return GeneratedImage(
            image_data=image_data,
            image_base64=base64.b64encode(image_data).decode("utf-8"),
            mime_type=mime_type,
            prompt_used=refine_prompt,
            model_used=self.model,
            generation_time_ms=generation_time_ms,
            width=preset.get("width"),
            height=preset.get("height"),
        )

    async def chat(
        self,
        session_id: str,
        message: str,
        purpose: ImagePurpose,
        generate_image: bool = False,
        style: Optional[StylePreset] = None,
    ) -> ChatResponse:
        """
        채팅 메시지 처리 (텍스트 또는 이미지 생성)

        Args:
            session_id: 세션 ID
            message: 사용자 메시지
            purpose: 이미지 용도
            generate_image: 이미지 생성 여부
            style: 스타일 프리셋

        Returns:
            ChatResponse: 채팅 응답
        """
        start_time = time.time()

        if generate_image:
            # 이미지 생성 요청
            image = await self.generate_image(
                prompt=message,
                purpose=purpose,
                style=style,
                session_id=session_id,
            )
            return ChatResponse(
                image=image,
                generation_time_ms=image.generation_time_ms,
            )

        # 텍스트 대화 (이미지 관련 조언, 아이디어 등)
        history = self._chat_sessions.get(session_id, [])

        system_prompt = """You are a creative marketing image consultant.
Help users create effective marketing images by:
1. Understanding their goals and target audience
2. Suggesting visual concepts and compositions
3. Recommending colors, styles, and layouts
4. Providing feedback on their ideas

When the user is ready to generate an image, ask them to confirm and I will create it.
Respond in Korean."""

        contents = [types.Content(role="user", parts=[types.Part(text=system_prompt)])]
        contents.extend(history)
        contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT"],
            ),
        )

        text_response = response.text
        generation_time_ms = int((time.time() - start_time) * 1000)

        # 히스토리 업데이트
        if session_id not in self._chat_sessions:
            self._chat_sessions[session_id] = []
        self._chat_sessions[session_id].append(
            types.Content(role="user", parts=[types.Part(text=message)])
        )
        self._chat_sessions[session_id].append(
            types.Content(role="model", parts=[types.Part(text=text_response)])
        )

        return ChatResponse(
            text=text_response,
            generation_time_ms=generation_time_ms,
        )

    def clear_session(self, session_id: str) -> None:
        """세션 히스토리 삭제"""
        if session_id in self._chat_sessions:
            del self._chat_sessions[session_id]

    def get_session_history_length(self, session_id: str) -> int:
        """세션 히스토리 길이 반환"""
        return len(self._chat_sessions.get(session_id, []))

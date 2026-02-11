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


@dataclass
class ConversationResponse:
    """통합 대화 응답 (텍스트와 이미지가 함께 올 수 있음)"""

    text: Optional[str] = None
    image: Optional[GeneratedImage] = None
    generation_time_ms: int = 0
    should_generate: bool = False  # AI가 이미지 생성이 필요하다고 판단했는지


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

    # TRDST 브랜드 이미지 생성 가이드라인
    TRDST_BRAND_PROMPT = """Create a premium marketing image for TRDST brand.

TRDST Brand Guidelines:
- Premium high-end furniture and lighting brand
- Timeless elegance and sophisticated design
- Modern luxury with clean lines
- Warm, inviting atmosphere
- Professional interior styling

Visual Style Requirements:
- Neutral, warm color tones (cream, beige, charcoal, gold accents)
- Clean backgrounds that don't distract from the subject
- Professional studio or luxury lifestyle setting
- Subtle shadows and natural lighting effects
- Minimalist yet luxurious atmosphere
- High-quality, aspirational imagery

"""

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

        # TRDST 브랜드 프롬프트 + 사용자 프롬프트
        branded_prompt = f"{self.TRDST_BRAND_PROMPT}User Request: {prompt}"

        # 프롬프트 최적화
        optimized_prompt = self._build_purpose_prompt(purpose, branded_prompt)
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
        previous_image_url: Optional[str] = None,
    ) -> GeneratedImage:
        """
        이미지 개선 (Multi-turn 대화)

        Args:
            session_id: 세션 ID
            feedback: 개선 피드백
            purpose: 이미지 용도
            previous_image_url: 이전 이미지 URL (히스토리 없을 때 사용)

        Returns:
            GeneratedImage: 개선된 이미지 정보
        """
        import httpx

        start_time = time.time()

        # 이미지 개선은 항상 이전 이미지를 가져와서 새 요청으로 처리
        # (Gemini API의 thought_signature 요구사항 때문에 히스토리 사용 불가)
        previous_image_data = None
        previous_mime_type = "image/png"

        if previous_image_url:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(previous_image_url, timeout=30.0)
                    if response.status_code == 200:
                        previous_image_data = response.content
                        content_type = response.headers.get("content-type", "image/png")
                        previous_mime_type = content_type.split(";")[0].strip()
            except Exception as e:
                raise ValueError(f"이전 이미지를 불러오는데 실패했습니다: {e}")

        if not previous_image_data:
            raise ValueError(f"세션 {session_id}의 이전 이미지를 찾을 수 없습니다. 먼저 이미지를 생성해주세요.")

        # TRDST 브랜드 가이드라인을 유지하면서 개선 요청
        refine_prompt = f"""Please modify this image based on the feedback while maintaining TRDST brand guidelines:
- Premium, sophisticated aesthetic
- Neutral warm tones (cream, beige, charcoal, gold accents)
- Clean, minimalist yet luxurious atmosphere
- Professional quality imagery

Feedback: {feedback}"""

        # Aspect ratio 설정
        aspect_ratio = self._get_aspect_ratio(purpose)

        # 항상 이미지와 피드백을 함께 새 요청으로 전송 (히스토리 사용 안함)
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part(inline_data=types.Blob(
                        mime_type=previous_mime_type,
                        data=previous_image_data
                    )),
                    types.Part(text=refine_prompt),
                ],
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

        # 이미지 개선은 히스토리를 사용하지 않으므로 별도로 저장하지 않음
        # (각 개선 요청은 DB에서 이전 이미지를 가져와 독립적으로 처리)

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

        system_prompt = """You are a creative marketing image consultant for TRDST.

## About TRDST
TRDST is a premium brand specializing in high-end furniture and lighting.
Our aesthetic emphasizes:
- Timeless elegance and sophisticated design
- Premium materials and craftsmanship
- Modern luxury with clean lines
- Warm, inviting atmosphere
- Professional interior styling

## Your Role
Help TRDST team create stunning marketing images by:
1. Understanding campaign goals and target audience (luxury home enthusiasts, interior designers, architects)
2. Suggesting visual concepts that align with TRDST's premium brand identity
3. Recommending sophisticated color palettes, lighting, and compositions
4. Providing expert feedback on furniture/lighting photography concepts
5. Ensuring images convey quality, elegance, and aspiration

## Style Guidelines
- Prefer neutral, warm tones (cream, beige, charcoal, gold accents)
- Clean backgrounds that don't distract from products
- Professional studio or lifestyle setting
- Subtle shadows and natural lighting effects
- Minimalist yet luxurious atmosphere

When the user is ready to generate an image, ask them to confirm and I will create it.
Always respond in Korean."""

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

    async def converse(
        self,
        session_id: str,
        message: str,
        purpose: ImagePurpose,
        style: Optional[StylePreset] = None,
        previous_image_url: Optional[str] = None,
    ) -> ConversationResponse:
        """
        통합 대화 - AI가 자연스럽게 대화하며 필요시 이미지 생성

        대화를 통해 아이디어를 구체화하고, AI가 적절한 시점에
        자동으로 이미지를 생성합니다. Thinking mode를 활용해
        더 깊은 창의적 사고를 수행합니다.

        Args:
            session_id: 세션 ID
            message: 사용자 메시지
            purpose: 이미지 용도
            style: 스타일 프리셋 (선택)
            previous_image_url: 수정할 이전 이미지 URL (선택)

        Returns:
            ConversationResponse: 텍스트와/또는 이미지 응답
        """
        import httpx

        start_time = time.time()

        # 통합 시스템 프롬프트 - AI가 자연스럽게 대화를 이끌고 이미지 생성 시점 결정
        system_prompt = """You are a creative marketing image consultant and generator for TRDST, a premium furniture and lighting brand.

## Your Role
You help create stunning marketing images through natural conversation:
1. **Understand the vision**: Ask clarifying questions about goals, audience, and style
2. **Develop the concept**: Suggest ideas, discuss compositions, refine details
3. **Generate when ready**: When the concept is clear enough, generate the image

## When to Generate Images
Generate an image when:
- The user explicitly asks to create/generate an image
- The concept has been discussed and refined enough
- The user confirms they want to proceed with generation
- Keywords like "만들어", "생성해", "보여줘", "그려줘" appear

Do NOT generate images when:
- Still exploring initial ideas
- Need more clarification on requirements
- User is asking questions about possibilities

## TRDST Brand Guidelines
- Premium, high-end aesthetic
- Neutral warm tones (cream, beige, charcoal, gold accents)
- Clean, minimalist yet luxurious
- Professional studio or lifestyle settings
- Natural lighting, subtle shadows

## Response Format
- If NOT generating: Provide helpful text response in Korean
- If generating: Include both explanatory text AND the image

## Image Generation Instructions (when generating)
When you decide to generate an image, create it following:
- TRDST brand visual identity
- The discussed concept and requirements
- The selected purpose and style settings

Always respond in Korean. Be conversational, creative, and helpful."""

        # 용도/스타일 컨텍스트 추가
        purpose_hints = {
            ImagePurpose.SNS_INSTAGRAM_SQUARE: "Instagram 정사각형 포스트용 (1:1)",
            ImagePurpose.SNS_INSTAGRAM_PORTRAIT: "Instagram 세로형 포스트용 (9:16)",
            ImagePurpose.SNS_FACEBOOK: "Facebook 피드용 (16:9)",
            ImagePurpose.BANNER_WEB: "웹 배너용 (16:9 와이드)",
            ImagePurpose.BANNER_MOBILE: "모바일 배너용 (16:9)",
            ImagePurpose.PRODUCT_SHOWCASE: "제품 쇼케이스용 (1:1)",
            ImagePurpose.EMAIL_HEADER: "이메일 헤더용 (16:9)",
            ImagePurpose.CUSTOM: "커스텀 용도",
        }
        style_hints = {
            StylePreset.MODERN: "모던",
            StylePreset.MINIMAL: "미니멀",
            StylePreset.VIBRANT: "비비드",
            StylePreset.LUXURY: "럭셔리",
            StylePreset.PLAYFUL: "플레이풀",
            StylePreset.PROFESSIONAL: "프로페셔널",
            StylePreset.NATURAL: "자연스러운",
            StylePreset.TECH: "테크",
        }

        context_prompt = f"\n\n[Current Settings]\n- Purpose: {purpose_hints.get(purpose, purpose.value)}"
        if style:
            context_prompt += f"\n- Style: {style_hints.get(style, style.value)}"

        # 이전 이미지가 있으면 수정 모드
        previous_image_data = None
        previous_mime_type = "image/png"
        if previous_image_url:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(previous_image_url, timeout=30.0)
                    if response.status_code == 200:
                        previous_image_data = response.content
                        content_type = response.headers.get("content-type", "image/png")
                        previous_mime_type = content_type.split(";")[0].strip()
                context_prompt += "\n- Mode: 이전 이미지를 기반으로 수정/개선"
            except Exception as e:
                # 이미지 로드 실패해도 대화는 계속
                context_prompt += f"\n- Note: 이전 이미지 로드 실패 ({e})"

        # Aspect ratio
        aspect_ratio = self._get_aspect_ratio(purpose)

        # 히스토리 가져오기
        history = self._chat_sessions.get(session_id, [])

        # 요청 구성
        contents = []

        # 시스템 프롬프트 (첫 메시지로)
        contents.append(types.Content(
            role="user",
            parts=[types.Part(text=system_prompt + context_prompt)]
        ))

        # 히스토리 추가
        contents.extend(history)

        # 현재 사용자 메시지 구성
        user_parts = []

        # 이전 이미지가 있으면 함께 전송 (수정 요청)
        if previous_image_data:
            user_parts.append(types.Part(
                inline_data=types.Blob(
                    mime_type=previous_mime_type,
                    data=previous_image_data
                )
            ))

        user_parts.append(types.Part(text=message))
        contents.append(types.Content(role="user", parts=user_parts))

        # Gemini API 호출 - TEXT와 IMAGE 모두 허용
        # Thinking mode 활성화 (Gemini 3)
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                ),
                # Thinking mode for deeper reasoning (Gemini 3)
                thinking_config=types.ThinkingConfig(
                    thinking_budget=2048,  # 적당한 사고 깊이
                ),
            ),
        )

        # 응답 파싱 - 텍스트와 이미지 추출
        text_response = None
        image_data = None
        mime_type = "image/png"

        for part in response.candidates[0].content.parts:
            if part.text:
                if text_response:
                    text_response += "\n" + part.text
                else:
                    text_response = part.text
            elif part.inline_data is not None:
                image_data = part.inline_data.data
                mime_type = part.inline_data.mime_type

        generation_time_ms = int((time.time() - start_time) * 1000)

        # 히스토리 업데이트 - 텍스트만 저장 (이미지는 thought_signature 문제로 저장 안함)
        if session_id not in self._chat_sessions:
            self._chat_sessions[session_id] = []

        # 사용자 메시지 저장 (텍스트만)
        self._chat_sessions[session_id].append(
            types.Content(role="user", parts=[types.Part(text=message)])
        )

        # 모델 응답 저장 (텍스트만)
        if text_response:
            self._chat_sessions[session_id].append(
                types.Content(role="model", parts=[types.Part(text=text_response)])
            )

        # 결과 구성
        result = ConversationResponse(
            text=text_response,
            generation_time_ms=generation_time_ms,
            should_generate=image_data is not None,
        )

        # 이미지가 생성되었으면 포함
        if image_data:
            preset = IMAGE_PURPOSE_PRESETS.get(purpose, {})
            result.image = GeneratedImage(
                image_data=image_data,
                image_base64=base64.b64encode(image_data).decode("utf-8"),
                mime_type=mime_type,
                prompt_used=message,
                model_used=self.model,
                generation_time_ms=generation_time_ms,
                width=preset.get("width"),
                height=preset.get("height"),
            )

        return result

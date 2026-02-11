"""
TRDST 브랜드 가이드라인

이 파일에서 브랜드 가이드라인을 수정할 수 있습니다.
변경 후 서버를 재시작하면 적용됩니다.
"""

# 브랜드 기본 정보
BRAND_NAME = "TRDST"
BRAND_DESCRIPTION = "Premium high-end furniture and lighting brand"

# 브랜드 가치
BRAND_VALUES = [
    "Timeless elegance and sophisticated design",
    "Modern luxury with clean lines",
    "Warm, inviting atmosphere",
    "Professional interior styling",
    "Premium materials and craftsmanship",
]

# 컬러 팔레트
COLOR_PALETTE = {
    "primary": {
        "cream": "#F5F2ED",
        "beige": "#D4C5B5",
        "charcoal": "#2C2C2C",
    },
    "accent": {
        "gold": "#C9A962",
        "bronze": "#8B6914",
        "warm_white": "#FAF8F5",
    },
    "text": {
        "dark": "#2C2C2C",
        "light": "#F5F2ED",
        "muted": "#8A8A8A",
    },
}

# 타이포그래피 가이드라인
TYPOGRAPHY = {
    "primary": {
        "style": "Modern Didone/Didot serif",
        "characteristics": "High contrast, elegant hairline strokes",
        "usage": "Headlines, brand name, key messages",
    },
    "secondary": {
        "style": "Refined geometric sans-serif",
        "examples": ["Futura", "Avenir", "Proxima Nova"],
        "usage": "Body text, captions, UI elements",
    },
    "guidelines": [
        "Generous letter-spacing for luxury feel",
        "Thin, elegant weights for headlines",
        "High contrast between thick and thin strokes",
        "Clean, sophisticated appearance",
    ],
    "avoid": [
        "Bold/heavy weights",
        "Playful fonts",
        "Decorative scripts",
        "Condensed typefaces",
    ],
}

# 비주얼 스타일 가이드라인
VISUAL_STYLE = {
    "atmosphere": [
        "Minimalist yet luxurious",
        "Warm and inviting",
        "Aspirational and sophisticated",
    ],
    "lighting": [
        "Natural lighting preferred",
        "Subtle shadows",
        "Soft, diffused light",
        "Warm color temperature",
    ],
    "background": [
        "Clean, uncluttered backgrounds",
        "Neutral tones that don't distract",
        "Professional studio or luxury lifestyle settings",
    ],
    "composition": [
        "Balanced and harmonious",
        "Product-focused with breathing room",
        "Rule of thirds for lifestyle shots",
    ],
}

# 이미지 생성 시 사용할 프롬프트 (AI용)
def get_brand_prompt() -> str:
    """AI 이미지 생성에 사용할 브랜드 프롬프트 반환"""

    color_desc = ", ".join([
        f"{name} ({code})"
        for category in COLOR_PALETTE.values()
        for name, code in category.items()
    ])

    typography_desc = f"""
Typography Guidelines (if text is included):
- Primary Font Style: {TYPOGRAPHY['primary']['style']} - {TYPOGRAPHY['primary']['characteristics']}
- Secondary Font Style: {TYPOGRAPHY['secondary']['style']} ({', '.join(TYPOGRAPHY['secondary']['examples'])})
- Characteristics:
{chr(10).join(f'  * {g}' for g in TYPOGRAPHY['guidelines'])}
- Text Color: {COLOR_PALETTE['text']['dark']} or {COLOR_PALETTE['text']['light']} depending on background
- Avoid: {', '.join(TYPOGRAPHY['avoid'])}
"""

    return f"""Create a premium marketing image for {BRAND_NAME} brand.

{BRAND_NAME} Brand Guidelines:
- {BRAND_DESCRIPTION}
{chr(10).join(f'- {v}' for v in BRAND_VALUES)}

Visual Style Requirements:
- Color palette: {color_desc}
{chr(10).join(f'- {item}' for item in VISUAL_STYLE['atmosphere'])}
{chr(10).join(f'- {item}' for item in VISUAL_STYLE['lighting'])}
{chr(10).join(f'- {item}' for item in VISUAL_STYLE['background'])}

{typography_desc}
"""


def get_conversation_guidelines() -> str:
    """대화형 AI에서 사용할 브랜드 가이드라인 반환"""

    return f"""## {BRAND_NAME} Brand Guidelines
- Premium, high-end aesthetic
- Neutral warm tones (cream, beige, charcoal, gold accents)
- Clean, minimalist yet luxurious
- Professional studio or lifestyle settings
- Natural lighting, subtle shadows

## Typography Guidelines (when text is needed)
- Primary: {TYPOGRAPHY['primary']['style']} - {TYPOGRAPHY['primary']['characteristics']}
- Secondary: {TYPOGRAPHY['secondary']['style']} ({TYPOGRAPHY['secondary']['examples'][0]} style)
- Characteristics:
{chr(10).join(f'  * {g}' for g in TYPOGRAPHY['guidelines'][:3])}
- Colors: {COLOR_PALETTE['text']['dark']} or {COLOR_PALETTE['text']['light']}
- Avoid: {', '.join(TYPOGRAPHY['avoid'][:3])}"""

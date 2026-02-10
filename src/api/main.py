"""
Gemini Image Chat API Server

마케팅 이미지 생성 채팅 서비스 메인 API 서버
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import image_chat_router, websocket_router
from src.config import get_settings
from src.storage.database import init_db

# Static files directory
STATIC_DIR = Path(__file__).parent.parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클 관리"""
    settings = get_settings()

    # 데이터베이스 초기화
    try:
        init_db()
        print("[OK] Database initialized")
    except Exception as e:
        print(f"[WARN] Database init failed: {type(e).__name__}: {e}")

    # API 키 확인
    if settings.gemini_api_key:
        print(f"[OK] Gemini API configured (model: {settings.gemini_model})")
    else:
        print("[WARN] GEMINI_API_KEY not set - image generation will fail")

    print(f"[OK] Gemini Image Chat started on port {settings.port}")

    yield

    print("[OK] Gemini Image Chat stopped")


# FastAPI 앱 생성
app = FastAPI(
    title="Gemini Image Chat API",
    description="Gemini API 기반 마케팅 이미지 생성 채팅 서비스",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 제한 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(image_chat_router)
app.include_router(websocket_router)


@app.get("/health")
async def health():
    """헬스 체크"""
    settings = get_settings()
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": settings.app_env,
        "gemini_configured": bool(settings.gemini_api_key),
    }


@app.get("/api/info")
async def api_info():
    """API 정보"""
    return {
        "name": "Gemini Image Chat",
        "version": "0.1.0",
        "description": "마케팅 이미지 생성 채팅 서비스",
        "endpoints": {
            "sessions": "/api/image-chat/sessions",
            "purposes": "/api/image-chat/purposes",
            "websocket": "/ws/image-chat/{session_id}",
        },
    }


# Static file serving for SPA
if STATIC_DIR.exists():
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/")
    async def serve_index():
        """Serve index.html"""
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Frontend not found")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve SPA for all non-API routes"""
        if full_path.startswith("api/") or full_path.startswith("ws/") or full_path == "health":
            raise HTTPException(status_code=404, detail="Not found")

        static_file = STATIC_DIR / full_path
        if static_file.exists() and static_file.is_file():
            return FileResponse(static_file)

        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)

        raise HTTPException(status_code=404, detail="Not found")
else:

    @app.get("/")
    async def root():
        """루트 엔드포인트"""
        return {
            "name": "Gemini Image Chat",
            "version": "0.1.0",
            "status": "operational",
            "message": "Frontend not built. Access /api/info for API details.",
        }

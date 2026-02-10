"""API Routes"""

from src.api.routes.image_chat import router as image_chat_router
from src.api.routes.websocket import router as websocket_router

__all__ = ["image_chat_router", "websocket_router"]

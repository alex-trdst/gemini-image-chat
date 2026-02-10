"""API endpoint tests"""

import pytest


@pytest.mark.asyncio
async def test_health(client):
    """Health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_api_info(client):
    """API info endpoint"""
    response = await client.get("/api/info")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Gemini Image Chat"


@pytest.mark.asyncio
async def test_get_purposes(client):
    """Get purpose presets"""
    response = await client.get("/api/image-chat/purposes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 7  # 7가지 용도 프리셋


@pytest.mark.asyncio
async def test_list_sessions_empty(client):
    """List sessions when empty"""
    response = await client.get("/api/image-chat/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_create_session(client):
    """Create new session"""
    response = await client.post(
        "/api/image-chat/sessions",
        json={
            "title": "테스트 세션",
            "image_purpose": "sns_instagram_square",
            "style_preset": "modern",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "테스트 세션"
    assert data["image_purpose"] == "sns_instagram_square"
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_get_session(client):
    """Get session detail"""
    # Create session first
    create_response = await client.post(
        "/api/image-chat/sessions",
        json={"image_purpose": "banner_web"},
    )
    session_id = create_response.json()["id"]

    # Get session
    response = await client.get(f"/api/image-chat/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert "messages" in data


@pytest.mark.asyncio
async def test_delete_session(client):
    """Delete session"""
    # Create session first
    create_response = await client.post(
        "/api/image-chat/sessions",
        json={"image_purpose": "product_showcase"},
    )
    session_id = create_response.json()["id"]

    # Delete session
    response = await client.delete(f"/api/image-chat/sessions/{session_id}")
    assert response.status_code == 200

    # Verify deleted
    get_response = await client.get(f"/api/image-chat/sessions/{session_id}")
    assert get_response.status_code == 404

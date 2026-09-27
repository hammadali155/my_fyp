from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    payload = {
        "email": "learner@jawhar.org",
        "name": "Ibn Battuta",
        "password": "StrongPassword99!",
        "native_lang": "ar",
        "ui_lang": "ar",
        "level": "intermediate",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == "learner@jawhar.org"
    assert data["user"]["name"] == "Ibn Battuta"
    assert data["user"]["level"] == "intermediate"
    assert "tokens" in data
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, registered_user: dict):
    payload = {
        "email": "talib@example.com",
        "name": "Another Name",
        "password": "AnotherPassword123!",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, registered_user: dict):
    payload = {
        "email": "talib@example.com",
        "password": "SecurePassword123!",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "talib@example.com"
    assert "access_token" in data["tokens"]


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, registered_user: dict):
    payload = {
        "email": "talib@example.com",
        "password": "WrongPassword!",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_current_user_profile(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "talib@example.com"
    assert data["name"] == "Talib Ilm"
    assert data["streak_days"] == 0


@pytest.mark.asyncio
async def test_get_profile_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_profile(client: AsyncClient, auth_headers: dict[str, str]):
    update_data = {
        "name": "Talib Ilm Al-Arabi",
        "level": "intermediate",
        "learning_goal": "Quranic Tafsir",
    }
    response = await client.patch("/api/v1/auth/me", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Talib Ilm Al-Arabi"
    assert data["level"] == "intermediate"
    assert data["learning_goal"] == "Quranic Tafsir"


@pytest.mark.asyncio
async def test_refresh_token_rotation(client: AsyncClient, registered_user: dict):
    old_refresh = registered_user["tokens"]["refresh_token"]

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert response.status_code == 200
    new_tokens = response.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens

    # Attempting to use old refresh token again must fail (revoked by rotation)
    reused = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert reused.status_code == 401


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, registered_user: dict, auth_headers: dict[str, str]):
    refresh_token = registered_user["tokens"]["refresh_token"]

    logout_resp = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
        headers=auth_headers,
    )
    assert logout_resp.status_code == 200

    # Refresh after logout must fail
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 401

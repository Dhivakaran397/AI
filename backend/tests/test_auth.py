import pytest

@pytest.mark.asyncio
async def test_register(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "password": "pass",
        "full_name": "New User"
    })
    assert resp.status_code == 200
    assert resp.json()["email"] == "new@example.com"

@pytest.mark.asyncio
async def test_login(client, test_user):
    resp = await client.post("/api/v1/auth/login", data={
        "username": "test@example.com",
        "password": "password123"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()

@pytest.mark.asyncio
async def test_me(client, auth_token):
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"

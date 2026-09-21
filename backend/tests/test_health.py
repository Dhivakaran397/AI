import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_liveness_health(client):
    resp = await client.get("/api/v1/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_deep_readiness_health(client):
    # Mock redis to avoid requiring external redis during pytest
    with patch("app.core.redis.get_redis") as mock_get_redis:
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_get_redis.return_value = mock_redis

        resp = await client.get("/api/v1/healthz/deep")
        assert resp.status_code in [200, 503]
        data = resp.json()
        assert "status" in data
        assert "components" in data
        assert "database" in data["components"]

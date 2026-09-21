import pytest
from app.models.conversation import Conversation
from uuid import uuid4

@pytest.mark.asyncio
async def test_create_conversation(client, auth_token):
    resp = await client.post("/api/v1/chat/conversations", headers={"Authorization": f"Bearer {auth_token}"}, json={
        "title": "Test Chat",
        "mode": "CHAT"
    })
    assert resp.status_code == 200
    assert resp.json()["title"] == "Test Chat"

@pytest.mark.asyncio
async def test_list_conversations(client, auth_token, db_session, test_user):
    conv = Conversation(user_id=test_user.id, title="Test List", mode="CHAT")
    db_session.add(conv)
    await db_session.commit()

    resp = await client.get("/api/v1/chat/conversations", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_conversation_with_messages(client, auth_token, db_session, test_user):
    conv = Conversation(user_id=test_user.id, title="Test Detail", mode="CHAT")
    db_session.add(conv)
    await db_session.commit()

    resp = await client.get(f"/api/v1/chat/conversations/{conv.id}", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(conv.id)
    assert data["title"] == "Test Detail"
    assert "messages" in data
    assert isinstance(data["messages"], list)


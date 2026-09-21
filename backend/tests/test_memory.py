import pytest
from app.schemas.memory import MemoryCreate
from app.services.memory_service import MemoryService


@pytest.mark.asyncio
async def test_memory_crud_service(db_session, test_user):
    # 1. Create memory
    mem_in = MemoryCreate(
        content="Prefers Tailwind CSS and clean UI",
        type="PREFERENCE",
    )
    memory = await MemoryService.create_memory(db_session, test_user.id, mem_in)
    assert memory.id is not None
    assert memory.content == mem_in.content

    # 2. Retrieve memories
    memories = await MemoryService.get_memories(db_session, test_user.id)
    assert len(memories) >= 1
    assert any(m.content == mem_in.content for m in memories)

    # 3. Context Prompt Generation
    prompt = await MemoryService.get_system_context_prompt(db_session, test_user.id)
    assert "Prefers Tailwind CSS" in prompt

    # 4. Delete memory
    deleted = await MemoryService.delete_memory(db_session, test_user.id, memory.id)
    assert deleted is True

    remaining = await MemoryService.get_memories(db_session, test_user.id)
    assert not any(m.id == memory.id for m in remaining)


@pytest.mark.asyncio
async def test_memory_endpoints(client, auth_token):
    # 1. Create memory via API
    resp = await client.post(
        "/api/v1/memories",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "content": "User prefers strict TypeScript",
            "type": "PREFERENCE"
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["content"] == "User prefers strict TypeScript"
    memory_id = data["id"]

    # 2. List memories
    list_resp = await client.get(
        "/api/v1/memories",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) >= 1

    # 3. Delete memory
    del_resp = await client.delete(
        f"/api/v1/memories/{memory_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert del_resp.status_code == 200

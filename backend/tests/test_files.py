import pytest
from app.services.project_service import ProjectService
from app.schemas.project import ProjectCreate
from app.services.file_service import FileService


@pytest.mark.asyncio
async def test_file_service_operations(db_session, test_user):
    user_id = test_user.id
    # Create project
    proj = await ProjectService.create_project(
        db_session, user_id, ProjectCreate(name="Filesystem Test Project")
    )

    # 1. Write file
    f1 = await FileService.write_file(
        db_session,
        proj.id,
        "src/index.ts",
        "console.log('Hello World');\nexport const v = 1;\n",
    )
    assert f1.path == "src/index.ts"
    assert f1.file_type == "typescript"
    assert "Hello World" in f1.content

    # 2. Write second file in another folder
    await FileService.write_file(
        db_session,
        proj.id,
        "README.md",
        "# Project Readme\nWelcome to DAI workspace.\n",
    )

    # 3. Get directory tree
    tree = await FileService.get_file_tree(db_session, proj.id)
    assert len(tree) == 2  # 'src' folder and 'README.md'
    src_node = next((n for n in tree if n.name == "src"), None)
    assert src_node is not None
    assert src_node.is_directory is True
    assert len(src_node.children) == 1
    assert src_node.children[0].name == "index.ts"

    # 4. Edit file (targeted replace)
    edited = await FileService.edit_file(
        db_session,
        proj.id,
        "src/index.ts",
        target_content="export const v = 1;",
        replacement_content="export const v = 2;\nexport const name = 'DAI';",
    )
    assert "v = 2" in edited.content
    assert "name = 'DAI'" in edited.content

    # 5. Check Diff
    diff = await FileService.get_diff(db_session, proj.id, "src/index.ts")
    assert diff is not None
    assert "-export const v = 1;" in diff.diff_unified
    assert "+export const v = 2;" in diff.diff_unified

    # 6. Revert File
    reverted = await FileService.revert_file(db_session, proj.id, "src/index.ts")
    assert reverted is not None
    assert "export const v = 1;" in reverted.content

    # 7. Search Code
    matches = await FileService.search_code(db_session, proj.id, "Welcome to DAI")
    assert len(matches) == 1
    assert matches[0].path == "README.md"
    assert matches[0].line_number == 2

    # 8. Delete File
    deleted = await FileService.delete_file(db_session, proj.id, "src/index.ts")
    assert deleted is True

    tree_after = await FileService.get_file_tree(db_session, proj.id)
    # Only README.md left
    assert len(tree_after) == 1
    assert tree_after[0].name == "README.md"


@pytest.mark.asyncio
async def test_file_api_endpoints(client, auth_token, db_session, test_user):
    # Create project
    proj = await ProjectService.create_project(
        db_session, test_user.id, ProjectCreate(name="API File Test")
    )
    proj_id = str(proj.id)

    # 1. Write file via API
    write_resp = await client.post(
        f"/api/v1/projects/{proj_id}/files",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"path": "main.py", "content": "print('hello from api')\n"},
    )
    assert write_resp.status_code == 200
    assert write_resp.json()["path"] == "main.py"

    # 2. Read file via API
    read_resp = await client.get(
        f"/api/v1/projects/{proj_id}/files/content?path=main.py",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert read_resp.status_code == 200
    assert "hello from api" in read_resp.json()["content"]

    # 3. Tree API
    tree_resp = await client.get(
        f"/api/v1/projects/{proj_id}/files/tree",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert tree_resp.status_code == 200
    assert len(tree_resp.json()) == 1

    # 4. Edit file API
    edit_resp = await client.patch(
        f"/api/v1/projects/{proj_id}/files",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "path": "main.py",
            "target_content": "hello from api",
            "replacement_content": "hello from DAI agent",
        },
    )
    assert edit_resp.status_code == 200
    assert "hello from DAI agent" in edit_resp.json()["content"]

    # 5. Diff API
    diff_resp = await client.get(
        f"/api/v1/projects/{proj_id}/files/diff?path=main.py",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert diff_resp.status_code == 200
    assert "+print('hello from DAI agent')" in diff_resp.json()["diff_unified"]

    # 6. Revert API
    rev_resp = await client.post(
        f"/api/v1/projects/{proj_id}/files/revert?path=main.py",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert rev_resp.status_code == 200
    assert "hello from api" in rev_resp.json()["content"]

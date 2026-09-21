from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field

from app.ai.tools.base import BaseTool, ToolPermission
from app.services.file_service import FileService


# 1. Read File Tool
class ReadFileArgs(BaseModel):
    project_id: str = Field(..., description="UUID of the project")
    path: str = Field(..., description="Relative file path to read (e.g. 'src/index.ts')")


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read the exact content of a file from the project workspace."
    permission = ToolPermission.READ
    args_schema = ReadFileArgs

    async def execute(self, project_id: str, path: str, **kwargs: Any) -> dict[str, Any]:
        db = kwargs.get("db")
        if not db:
            return {"status": "error", "error": "Database session unavailable"}
        try:
            p_uuid = UUID(project_id)
        except ValueError:
            return {"status": "error", "error": f"Invalid project UUID: {project_id}"}

        file_res = await FileService.read_file(db, p_uuid, path)
        if not file_res:
            return {"status": "error", "error": f"File '{path}' not found."}

        return {
            "status": "success",
            "path": file_res.path,
            "content": file_res.content,
            "size": file_res.size,
            "file_type": file_res.file_type,
        }


# 2. Write File Tool
class WriteFileArgs(BaseModel):
    project_id: str = Field(..., description="UUID of the project")
    path: str = Field(..., description="Relative file path to write (e.g. 'src/app.py')")
    content: str = Field(..., description="Full source code content to write")


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Create or overwrite a file in the project workspace with full source code."
    permission = ToolPermission.WRITE
    args_schema = WriteFileArgs

    async def execute(self, project_id: str, path: str, content: str, **kwargs: Any) -> dict[str, Any]:
        db = kwargs.get("db")
        if not db:
            return {"status": "error", "error": "Database session unavailable"}
        try:
            p_uuid = UUID(project_id)
        except ValueError:
            return {"status": "error", "error": f"Invalid project UUID: {project_id}"}

        file_res = await FileService.write_file(db, p_uuid, path, content)
        return {
            "status": "success",
            "path": file_res.path,
            "size": file_res.size,
            "message": f"File '{file_res.path}' written successfully.",
        }


# 3. Edit File Tool (Targeted search & replace)
class EditFileArgs(BaseModel):
    project_id: str = Field(..., description="UUID of the project")
    path: str = Field(..., description="Relative file path to modify")
    target_content: str = Field(..., description="Exact snippet of existing code to replace")
    replacement_content: str = Field(..., description="Replacement snippet of new code")


class EditFileTool(BaseTool):
    name = "edit_file"
    description = "Modify an existing file by cleanly replacing an exact snippet with new code."
    permission = ToolPermission.WRITE
    args_schema = EditFileArgs

    async def execute(
        self, project_id: str, path: str, target_content: str, replacement_content: str, **kwargs: Any
    ) -> dict[str, Any]:
        db = kwargs.get("db")
        if not db:
            return {"status": "error", "error": "Database session unavailable"}
        try:
            p_uuid = UUID(project_id)
        except ValueError:
            return {"status": "error", "error": f"Invalid project UUID: {project_id}"}

        try:
            file_res = await FileService.edit_file(
                db, p_uuid, path, target_content, replacement_content
            )
            return {
                "status": "success",
                "path": file_res.path,
                "message": f"Successfully updated '{file_res.path}'.",
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


# 4. List Files Tool
class ListFilesArgs(BaseModel):
    project_id: str = Field(..., description="UUID of the project")


class ListFilesTool(BaseTool):
    name = "list_files"
    description = "List the complete file directory tree of a project workspace."
    permission = ToolPermission.READ
    args_schema = ListFilesArgs

    async def execute(self, project_id: str, **kwargs: Any) -> dict[str, Any]:
        db = kwargs.get("db")
        if not db:
            return {"status": "error", "error": "Database session unavailable"}
        try:
            p_uuid = UUID(project_id)
        except ValueError:
            return {"status": "error", "error": f"Invalid project UUID: {project_id}"}

        tree = await FileService.get_file_tree(db, p_uuid)
        return {"status": "success", "tree": [n.model_dump() for n in tree]}


# 5. Search Code Tool
class SearchCodeArgs(BaseModel):
    project_id: str = Field(..., description="UUID of the project")
    query: str = Field(..., description="Pattern or text string to search for")


class SearchCodeTool(BaseTool):
    name = "search_code"
    description = "Search across all source files in a project for a query string."
    permission = ToolPermission.READ
    args_schema = SearchCodeArgs

    async def execute(self, project_id: str, query: str, **kwargs: Any) -> dict[str, Any]:
        db = kwargs.get("db")
        if not db:
            return {"status": "error", "error": "Database session unavailable"}
        try:
            p_uuid = UUID(project_id)
        except ValueError:
            return {"status": "error", "error": f"Invalid project UUID: {project_id}"}

        matches = await FileService.search_code(db, p_uuid, query)
        return {
            "status": "success",
            "matches_count": len(matches),
            "matches": [m.model_dump() for m in matches[:50]],
        }


# 6. Revert File Tool
class RevertFileArgs(BaseModel):
    project_id: str = Field(..., description="UUID of the project")
    path: str = Field(..., description="Relative file path to revert to previous revision")


class RevertFileTool(BaseTool):
    name = "revert_file"
    description = "Roll back an edited file to its previous revision snapshot."
    permission = ToolPermission.WRITE
    args_schema = RevertFileArgs

    async def execute(self, project_id: str, path: str, **kwargs: Any) -> dict[str, Any]:
        db = kwargs.get("db")
        if not db:
            return {"status": "error", "error": "Database session unavailable"}
        try:
            p_uuid = UUID(project_id)
        except ValueError:
            return {"status": "error", "error": f"Invalid project UUID: {project_id}"}

        reverted = await FileService.revert_file(db, p_uuid, path)
        if not reverted:
            return {"status": "error", "error": "No revision history found to revert."}

        return {
            "status": "success",
            "path": reverted.path,
            "message": f"File '{reverted.path}' reverted successfully.",
        }

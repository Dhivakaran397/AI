import difflib
import os
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.document import ProjectFile
from app.models.revision import FileRevision
from app.schemas.file import (
    FileNode,
    FileContentResponse,
    FileDiffResponse,
    SearchResult,
)


def normalize_path(p: str) -> str:
    """Normalize file path to unix forward slashes without leading slash."""
    norm = p.replace("\\", "/").strip().lstrip("/")
    return norm


def infer_file_type(path: str) -> str:
    _, ext = os.path.splitext(path)
    ext = ext.lower().lstrip(".")
    if ext in {"ts", "tsx"}:
        return "typescript"
    elif ext in {"js", "jsx"}:
        return "javascript"
    elif ext == "py":
        return "python"
    elif ext in {"html", "htm"}:
        return "html"
    elif ext in {"css", "scss", "sass"}:
        return "css"
    elif ext == "json":
        return "json"
    elif ext in {"md", "markdown"}:
        return "markdown"
    elif ext in {"sql"}:
        return "sql"
    elif ext in {"sh", "bash"}:
        return "shell"
    elif ext in {"yml", "yaml"}:
        return "yaml"
    return "plaintext"


class FileService:
    @staticmethod
    async def get_file_tree(db: AsyncSession, project_id: UUID) -> list[FileNode]:
        """Build hierarchical directory tree from flat ProjectFile records."""
        query = select(ProjectFile).where(ProjectFile.project_id == project_id).order_by(ProjectFile.path.asc())
        result = await db.execute(query)
        files = list(result.scalars().all())

        root_children: list[FileNode] = []
        dir_map: dict[str, FileNode] = {}

        for f in files:
            parts = f.path.split("/")
            curr_path = ""

            # Ensure parent directories exist in tree
            parent_children = root_children
            for i, part in enumerate(parts[:-1]):
                curr_path = f"{curr_path}/{part}" if curr_path else part
                if curr_path not in dir_map:
                    dir_node = FileNode(
                        name=part,
                        path=curr_path,
                        is_directory=True,
                        size=0,
                        children=[],
                    )
                    dir_map[curr_path] = dir_node
                    parent_children.append(dir_node)
                parent_children = dir_map[curr_path].children

            # Add the leaf file
            leaf = FileNode(
                name=parts[-1],
                path=f.path,
                is_directory=False,
                size=f.size,
                children=[],
            )
            parent_children.append(leaf)

        return root_children

    @staticmethod
    async def read_file(db: AsyncSession, project_id: UUID, path: str) -> FileContentResponse | None:
        clean_path = normalize_path(path)
        query = select(ProjectFile).where(
            ProjectFile.project_id == project_id, ProjectFile.path == clean_path
        )
        res = await db.execute(query)
        pf = res.scalars().first()
        if not pf:
            return None

        # Check revisions
        rev_q = select(FileRevision).where(
            FileRevision.project_id == project_id, FileRevision.path == clean_path
        )
        rev_res = await db.execute(rev_q)
        has_revs = rev_res.scalars().first() is not None

        return FileContentResponse(
            path=pf.path,
            content=pf.content or "",
            size=pf.size,
            file_type=pf.file_type,
            has_revisions=has_revs,
            updated_at=pf.updated_at,
        )

    @staticmethod
    async def write_file(db: AsyncSession, project_id: UUID, path: str, content: str) -> FileContentResponse:
        clean_path = normalize_path(path)
        query = select(ProjectFile).where(
            ProjectFile.project_id == project_id, ProjectFile.path == clean_path
        )
        res = await db.execute(query)
        existing = res.scalars().first()

        file_type = infer_file_type(clean_path)
        content_size = len(content.encode("utf-8"))

        if existing:
            # Generate diff and store revision snapshot
            old_content = existing.content or ""
            diff_lines = list(
                difflib.unified_diff(
                    old_content.splitlines(keepends=True),
                    content.splitlines(keepends=True),
                    fromfile=f"a/{clean_path}",
                    tofile=f"b/{clean_path}",
                )
            )
            diff_text = "".join(diff_lines)

            revision = FileRevision(
                project_id=project_id,
                path=clean_path,
                previous_content=old_content,
                diff=diff_text,
            )
            db.add(revision)

            existing.content = content
            existing.size = content_size
            existing.file_type = file_type
            pf = existing
        else:
            pf = ProjectFile(
                project_id=project_id,
                path=clean_path,
                content=content,
                file_type=file_type,
                size=content_size,
            )
            db.add(pf)

        await db.commit()
        await db.refresh(pf)

        return FileContentResponse(
            path=pf.path,
            content=pf.content or "",
            size=pf.size,
            file_type=pf.file_type,
            has_revisions=existing is not None,
            updated_at=pf.updated_at,
        )

    @staticmethod
    async def edit_file(
        db: AsyncSession, project_id: UUID, path: str, target_content: str, replacement_content: str
    ) -> FileContentResponse:
        clean_path = normalize_path(path)
        query = select(ProjectFile).where(
            ProjectFile.project_id == project_id, ProjectFile.path == clean_path
        )
        res = await db.execute(query)
        existing = res.scalars().first()
        if not existing:
            raise ValueError(f"File '{clean_path}' does not exist.")

        curr = existing.content or ""
        if target_content not in curr:
            raise ValueError(f"Target snippet not found in '{clean_path}'.")

        new_content = curr.replace(target_content, replacement_content, 1)
        return await FileService.write_file(db, project_id, clean_path, new_content)

    @staticmethod
    async def delete_file(db: AsyncSession, project_id: UUID, path: str) -> bool:
        clean_path = normalize_path(path)
        # Delete exact file or any child if directory
        query = delete(ProjectFile).where(
            ProjectFile.project_id == project_id,
            (ProjectFile.path == clean_path) | (ProjectFile.path.startswith(clean_path + "/")),
        )
        res = await db.execute(query)
        await db.commit()
        return res.rowcount > 0

    @staticmethod
    async def get_diff(db: AsyncSession, project_id: UUID, path: str) -> FileDiffResponse | None:
        clean_path = normalize_path(path)
        # Get current content
        current = await FileService.read_file(db, project_id, clean_path)
        if not current:
            return None

        # Get latest revision
        rev_q = (
            select(FileRevision)
            .where(FileRevision.project_id == project_id, FileRevision.path == clean_path)
            .order_by(FileRevision.created_at.desc())
        )
        rev_res = await db.execute(rev_q)
        latest_rev = rev_res.scalars().first()

        if not latest_rev:
            return FileDiffResponse(
                path=clean_path,
                original_content=current.content,
                current_content=current.content,
                diff_unified="",
            )

        return FileDiffResponse(
            path=clean_path,
            original_content=latest_rev.previous_content,
            current_content=current.content,
            diff_unified=latest_rev.diff or "",
            revision_id=str(latest_rev.id),
        )

    @staticmethod
    async def revert_file(db: AsyncSession, project_id: UUID, path: str) -> FileContentResponse | None:
        clean_path = normalize_path(path)
        # Find latest revision
        rev_q = (
            select(FileRevision)
            .where(FileRevision.project_id == project_id, FileRevision.path == clean_path)
            .order_by(FileRevision.created_at.desc())
        )
        rev_res = await db.execute(rev_q)
        latest_rev = rev_res.scalars().first()
        if not latest_rev:
            return None

        # Restore previous content
        query = select(ProjectFile).where(
            ProjectFile.project_id == project_id, ProjectFile.path == clean_path
        )
        res = await db.execute(query)
        pf = res.scalars().first()
        if not pf:
            return None

        pf.content = latest_rev.previous_content
        pf.size = len(latest_rev.previous_content.encode("utf-8"))

        # Remove the latest revision
        await db.delete(latest_rev)
        await db.commit()
        await db.refresh(pf)

        return FileContentResponse(
            path=pf.path,
            content=pf.content or "",
            size=pf.size,
            file_type=pf.file_type,
            has_revisions=False,
            updated_at=pf.updated_at,
        )

    @staticmethod
    async def search_code(db: AsyncSession, project_id: UUID, query_str: str) -> list[SearchResult]:
        query = select(ProjectFile).where(ProjectFile.project_id == project_id)
        result = await db.execute(query)
        files = list(result.scalars().all())

        hits: list[SearchResult] = []
        lower_q = query_str.lower()

        for f in files:
            if not f.content:
                continue
            for line_idx, line in enumerate(f.content.splitlines(), start=1):
                if lower_q in line.lower():
                    hits.append(
                        SearchResult(
                            path=f.path,
                            line_number=line_idx,
                            line_content=line.strip(),
                        )
                    )
        return hits

from typing import Any
from app.ai.tools.base import BaseTool, ToolPermission
from app.ai.tools.builtin import (
    CalculateTool,
    GetCurrentTimeTool,
    SaveMemoryTool,
    WebSearchTool,
)
from app.ai.tools.project_tools import (
    CreateProjectTool,
    UpdateProjectStatusTool,
    CreateTaskTool,
    UpdateTaskStatusTool,
)
from app.ai.tools.code_tools import (
    ReadFileTool,
    WriteFileTool,
    EditFileTool,
    ListFilesTool,
    SearchCodeTool,
    RevertFileTool,
)
from app.ai.tools.execution_tools import (
    ExecuteCommandTool,
    ManageProcessTool,
)
from app.ai.tools.orchestrator_tools import (
    DelegateToAgentTool,
    RunSelfCorrectionTool,
)
from app.ai.tools.testing_tools import (
    GenerateTestsTool,
    RunTestSuiteTool,
    AnalyzeErrorTool,
)
from app.ai.tools.knowledge_tools import (
    SearchKnowledgeTool,
    IngestDocumentTool,
)
from app.ai.tools.image_tools import GenerateImageTool
from app.ai.tools.document_tools import GeneratePresentationTool, GenerateWordDocumentTool
from app.ai.tools.video_tools import GenerateVideoTool, GenerateCarouselTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        # Register built-ins
        self.register(GetCurrentTimeTool())
        self.register(CalculateTool())
        self.register(SaveMemoryTool())
        self.register(WebSearchTool())
        self.register(GenerateImageTool())
        self.register(GeneratePresentationTool())
        self.register(GenerateWordDocumentTool())
        self.register(GenerateVideoTool())
        self.register(GenerateCarouselTool())

        # Register Phase 3 project tools
        self.register(CreateProjectTool())
        self.register(UpdateProjectStatusTool())
        self.register(CreateTaskTool())
        self.register(UpdateTaskStatusTool())

        # Register Phase 4 coding agent tools
        self.register(ReadFileTool())
        self.register(WriteFileTool())
        self.register(EditFileTool())
        self.register(ListFilesTool())
        self.register(SearchCodeTool())
        self.register(RevertFileTool())

        # Register Phase 5 execution & process tools
        self.register(ExecuteCommandTool())
        self.register(ManageProcessTool())

        # Register Phase 6 multi-agent orchestrator tools
        self.register(DelegateToAgentTool())
        self.register(RunSelfCorrectionTool())

        # Register Phase 7 testing & debugging tools
        self.register(GenerateTestsTool())
        self.register(RunTestSuiteTool())
        self.register(AnalyzeErrorTool())

        # Register Phase 8 knowledge & document tools
        self.register(SearchKnowledgeTool())
        self.register(IngestDocumentTool())

    def register(self, tool: BaseTool) -> None:
        """Register a new tool instance."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        """Retrieve a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[BaseTool]:
        """Return all registered tool instances."""
        return list(self._tools.values())

    def get_openai_tools(self, allowed_permissions: list[ToolPermission] | None = None) -> list[dict[str, Any]]:
        """Export tool specifications formatted for OpenAI / OpenAI-compatible tool calling."""
        tools = []
        for tool in self._tools.values():
            if allowed_permissions is None or tool.permission in allowed_permissions:
                tools.append(tool.to_openai_tool())
        return tools

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        context: dict[str, Any] | None = None,
        allowed_permissions: list[ToolPermission] | None = None,
    ) -> dict[str, Any]:
        """Execute a tool safely after validating permissions."""
        tool = self.get(name)
        if not tool:
            return {"error": f"Tool '{name}' not found."}

        if allowed_permissions is not None and tool.permission not in allowed_permissions:
            return {
                "error": f"Permission denied for tool '{name}'. Required: {tool.permission.value}"
            }

        kwargs = {**arguments}
        if context:
            kwargs.update(context)

        try:
            result = await tool.execute(**kwargs)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Global registry instance
tool_registry = ToolRegistry()

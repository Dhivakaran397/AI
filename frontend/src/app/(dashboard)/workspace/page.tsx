"use client";

import { Suspense, useEffect, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { FileTree, type FileTreeNode } from "@/components/workspace/file-tree";
import { CodeEditor } from "@/components/workspace/code-editor";
import { MonacoDiffViewer } from "@/components/workspace/diff-viewer";
import { Terminal } from "@/components/workspace/terminal";
import { LivePreview } from "@/components/workspace/live-preview";
import { ProcessManager } from "@/components/workspace/process-manager";
import { TestRunner } from "@/components/testing/test-runner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { apiClient } from "@/lib/api-client";
import { streamChat } from "@/lib/sse";
import type {
  Project,
  FileContentResponse,
  FileDiffResponse,
  SearchResult,
} from "@/types";
import {
  Code2,
  FolderOpen,
  RefreshCw,
  Search,
  Bot,
  Sparkles,
  Loader2,
  FileCode,
  Send,
  AlertCircle,
  Terminal as TerminalIcon,
  Globe,
  Activity,
  Columns2,
  CheckCircle2,
  Download,
} from "lucide-react";
import Link from "next/link";

export default function WorkspacePage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      }
    >
      <WorkspaceContent />
    </Suspense>
  );
}

function WorkspaceContent() {
  const searchParams = useSearchParams();
  const initialProjectId = searchParams.get("projectId");

  // Project state
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>(
    initialProjectId || ""
  );

  // File tree and selection
  const [fileTree, setFileTree] = useState<FileTreeNode[]>([]);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<FileContentResponse | null>(
    null
  );

  // Diff Viewer
  const [diffData, setDiffData] = useState<FileDiffResponse | null>(null);
  const [isDiffMode, setIsDiffMode] = useState(false);
  const [activeTab, setActiveTab] = useState<
    "editor" | "terminal" | "preview" | "processes" | "qa" | "split"
  >("editor");

  // Loading states
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [loadingTree, setLoadingTree] = useState(false);
  const [loadingFile, setLoadingFile] = useState(false);

  // Search
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // Assistant Side-Drawer
  const [assistantOpen, setAssistantOpen] = useState(false);
  const [aiPrompt, setAiPrompt] = useState("");
  const [aiResponse, setAiResponse] = useState<string | null>(null);
  const [isAiBusy, setIsAiBusy] = useState(false);

  // Error feedback
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  // 1. Fetch available projects
  const fetchProjects = useCallback(async () => {
    try {
      setLoadingProjects(true);
      const res = await apiClient.get<Project[]>("/projects");
      setProjects(res);
      if (!selectedProjectId && res.length > 0) {
        setSelectedProjectId(res[0].id);
      }
    } catch (err: unknown) {
      console.error("Failed to load projects:", err);
    } finally {
      setLoadingProjects(false);
    }
  }, [selectedProjectId]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  // 2. Fetch File Tree when project changes
  const fetchFileTree = useCallback(async (projectId: string) => {
    try {
      setLoadingTree(true);
      setErrorMsg(null);
      const tree = await apiClient.get<FileTreeNode[]>(
        `/projects/${projectId}/files/tree`
      );
      setFileTree(tree);
    } catch (err: unknown) {
      console.error("Failed to load file tree:", err);
      setErrorMsg("Failed to load project files");
      setFileTree([]);
    } finally {
      setLoadingTree(false);
    }
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      fetchFileTree(selectedProjectId);
      setSelectedPath(null);
      setFileContent(null);
      setIsDiffMode(false);
      setDiffData(null);
    }
  }, [selectedProjectId, fetchFileTree]);

  // 3. Load file content
  const handleSelectFile = async (path: string) => {
    if (!selectedProjectId) return;
    try {
      setLoadingFile(true);
      setSelectedPath(path);
      setIsDiffMode(false);
      setDiffData(null);
      setErrorMsg(null);

      const res = await apiClient.get<FileContentResponse>(
        `/projects/${selectedProjectId}/files/content?path=${encodeURIComponent(
          path
        )}`
      );
      setFileContent(res);
    } catch (err: unknown) {
      console.error("Failed to load file content:", err);
      setErrorMsg(`Failed to open file: ${path}`);
    } finally {
      setLoadingFile(false);
    }
  };

  // 4. Save file
  const handleSaveFile = async (content: string) => {
    if (!selectedProjectId || !selectedPath) return;
    try {
      const res = await apiClient.post<FileContentResponse>(
        `/projects/${selectedProjectId}/files`,
        {
          path: selectedPath,
          content,
        }
      );
      setFileContent(res);
      // Refresh tree to update sizes
      await fetchFileTree(selectedProjectId);
    } catch (err: unknown) {
      console.error("Failed to save file:", err);
      setErrorMsg("Failed to save file");
      throw err;
    }
  };

  // 5. Create new file
  const handleCreateFile = async (path: string) => {
    if (!selectedProjectId) return;
    try {
      await apiClient.post<FileContentResponse>(
        `/projects/${selectedProjectId}/files`,
        {
          path,
          content: "",
        }
      );
      await fetchFileTree(selectedProjectId);
      await handleSelectFile(path);
    } catch (err: unknown) {
      console.error("Failed to create file:", err);
      setErrorMsg("Failed to create file");
    }
  };

  // 6. Delete file
  const handleDeleteFile = async (path: string) => {
    if (!selectedProjectId) return;
    if (!confirm(`Are you sure you want to delete ${path}?`)) return;

    try {
      await apiClient.delete(
        `/projects/${selectedProjectId}/files?path=${encodeURIComponent(path)}`
      );
      if (selectedPath === path) {
        setSelectedPath(null);
        setFileContent(null);
        setIsDiffMode(false);
      }
      await fetchFileTree(selectedProjectId);
    } catch (err: unknown) {
      console.error("Failed to delete file:", err);
      setErrorMsg("Failed to delete file");
    }
  };

  // 7. Toggle Diff View
  const handleToggleDiff = async () => {
    if (!selectedProjectId || !selectedPath) return;
    if (isDiffMode) {
      setIsDiffMode(false);
      return;
    }

    try {
      const diff = await apiClient.get<FileDiffResponse>(
        `/projects/${selectedProjectId}/files/diff?path=${encodeURIComponent(
          selectedPath
        )}`
      );
      setDiffData(diff);
      setIsDiffMode(true);
    } catch (err: unknown) {
      console.error("Failed to get diff:", err);
      setErrorMsg("No revision snapshot found to compare");
    }
  };

  // 8. Revert file
  const handleRevertFile = async () => {
    if (!selectedProjectId || !selectedPath) return;
    if (!confirm(`Revert ${selectedPath} to its previous revision?`)) return;

    try {
      const res = await apiClient.post<FileContentResponse>(
        `/projects/${selectedProjectId}/files/revert`,
        { path: selectedPath }
      );
      setFileContent(res);
      setIsDiffMode(false);
      setDiffData(null);
      await fetchFileTree(selectedProjectId);
    } catch (err: unknown) {
      console.error("Failed to revert file:", err);
      setErrorMsg("Failed to revert file");
      throw err;
    }
  };

  // 9. Search Codebase
  const handleSearchCode = async () => {
    if (!selectedProjectId || !searchQuery.trim()) return;
    try {
      setIsSearching(true);
      const results = await apiClient.get<SearchResult[]>(
        `/projects/${selectedProjectId}/files/search?query=${encodeURIComponent(
          searchQuery.trim()
        )}`
      );
      setSearchResults(results);
    } catch (err: unknown) {
      console.error("Search failed:", err);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  // 10. AI Coding Assistant action
  const handleAskAssistant = async () => {
    if (!aiPrompt.trim() || !selectedProjectId) return;
    const promptText = aiPrompt.trim();
    try {
      setIsAiBusy(true);
      setAiResponse(null);
      setAiPrompt("");

      // 1. Create conversation with agent
      const conv = await apiClient.post<{ id: string }>("/chat/conversations", {
        title: `Workspace: ${selectedPath || promptText.slice(0, 30)}`,
        mode: "BUILD",
      });

      // 2. Supply context from open file or project
      let promptWithContext = promptText;
      if (selectedPath && fileContent?.content) {
        promptWithContext = `You are assisting with the project "${selectedProject?.name || "App"}".\nCurrently open file: ${selectedPath}\n\nFile Content:\n\`\`\`\n${fileContent.content.slice(0, 3000)}\n\`\`\`\n\nUser Question: ${promptText}`;
      } else if (selectedProject) {
        promptWithContext = `Project: ${selectedProject.name}\nDescription: ${selectedProject.description || "Web application"}\nStatus: ${selectedProject.status}\n\nUser Question: ${promptText}`;
      }

      setAiResponse("DAI Assistant is thinking...");

      // 3. Stream real response from AI
      streamChat(
        conv.id,
        promptWithContext,
        "BUILD",
        {
          onContent: (content) => {
            setAiResponse(content);
          },
          onEnd: (fullContent) => {
            setAiResponse(fullContent || "Response completed.");
            setIsAiBusy(false);
          },
          onError: (err) => {
            console.error("AI assistant stream error:", err);
            setAiResponse(err || "Unable to reach AI agent. Please try again.");
            setIsAiBusy(false);
          },
        }
      );
    } catch (err: unknown) {
      console.error("AI assistant request failed:", err);
      setAiResponse("Unable to reach AI agent. Please try again.");
      setIsAiBusy(false);
    }
  };

  // 11. Download Project ZIP for VS Code
  const handleDownloadProject = async () => {
    if (!selectedProjectId) return;
    try {
      setIsDownloading(true);
      setErrorMsg(null);
      const safeName = selectedProject?.name
        ? `${selectedProject.name.toLowerCase().replace(/[^a-z0-9]/g, "_")}.zip`
        : "project.zip";
      await apiClient.downloadFile(`/projects/${selectedProjectId}/download`, safeName);
    } catch (err: unknown) {
      console.error("Failed to download project:", err);
      setErrorMsg("Failed to download project ZIP archive");
    } finally {
      setIsDownloading(false);
    }
  };

  const selectedProject = projects.find((p) => p.id === selectedProjectId);

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Workspace Header Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b bg-background shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Code2 className="h-5 w-5 text-primary" />
            <span className="font-semibold text-sm">DAI Studio IDE</span>
          </div>

          <div className="h-4 w-px bg-border mx-1" />

          {/* Project Dropdown */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Project:</span>
            {loadingProjects ? (
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            ) : projects.length === 0 ? (
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">No projects yet</span>
                <Link href="/projects">
                  <Button size="sm" variant="outline" className="h-7 text-xs">
                    Create Project
                  </Button>
                </Link>
              </div>
            ) : (
              <Select
                value={selectedProjectId || ""}
                onValueChange={(val) => val && setSelectedProjectId(val)}
              >
                <SelectTrigger className="h-7 min-w-[180px] max-w-[260px] text-xs">
                  <SelectValue placeholder="Select a project" />
                </SelectTrigger>
                <SelectContent>
                  {projects.map((proj) => (
                    <SelectItem key={proj.id} value={proj.id} className="text-xs">
                      {proj.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}

            {selectedProject && (
              <Badge variant="outline" className="text-[10px] uppercase font-mono px-1.5 py-0">
                {selectedProject.status}
              </Badge>
            )}
          </div>

          <div className="h-4 w-px bg-border mx-1" />

          {/* View Mode Switcher Tabs */}
          {selectedProjectId && (
            <div className="flex items-center rounded-lg border bg-muted/40 p-0.5">
              <button
                onClick={() => setActiveTab("editor")}
                className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors ${
                  activeTab === "editor"
                    ? "bg-background text-foreground shadow-xs"
                    : "text-muted-foreground hover:text-foreground"
                }`}
                title="Code Editor"
              >
                <Code2 className="h-3.5 w-3.5" />
                <span className="hidden md:inline">Editor</span>
              </button>
              <button
                onClick={() => setActiveTab("terminal")}
                className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors ${
                  activeTab === "terminal"
                    ? "bg-background text-foreground shadow-xs"
                    : "text-muted-foreground hover:text-foreground"
                }`}
                title="Controlled Terminal"
              >
                <TerminalIcon className="h-3.5 w-3.5" />
                <span className="hidden md:inline">Terminal</span>
              </button>
              <button
                onClick={() => setActiveTab("preview")}
                className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors ${
                  activeTab === "preview"
                    ? "bg-background text-foreground shadow-xs"
                    : "text-muted-foreground hover:text-foreground"
                }`}
                title="Live Project Preview"
              >
                <Globe className="h-3.5 w-3.5" />
                <span className="hidden md:inline">Preview</span>
              </button>
              <button
                onClick={() => setActiveTab("processes")}
                className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors ${
                  activeTab === "processes"
                    ? "bg-background text-foreground shadow-xs"
                    : "text-muted-foreground hover:text-foreground"
                }`}
                title="Background Processes"
              >
                <Activity className="h-3.5 w-3.5" />
                <span className="hidden md:inline">Processes</span>
              </button>
              <button
                onClick={() => setActiveTab("qa")}
                className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors ${
                  activeTab === "qa"
                    ? "bg-background text-foreground shadow-xs"
                    : "text-muted-foreground hover:text-foreground"
                }`}
                title="QA & Automated Testing"
              >
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span className="hidden md:inline">QA & Tests</span>
              </button>
              <button
                onClick={() => setActiveTab("split")}
                className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors ${
                  activeTab === "split"
                    ? "bg-background text-foreground shadow-xs"
                    : "text-muted-foreground hover:text-foreground"
                }`}
                title="Split View: Code + Terminal"
              >
                <Columns2 className="h-3.5 w-3.5" />
                <span className="hidden lg:inline">Split</span>
              </button>
            </div>
          )}
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {selectedProjectId && (
            <>
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs gap-1.5 border-primary/30 hover:border-primary text-foreground"
                onClick={handleDownloadProject}
                disabled={isDownloading}
                title="Download complete project folder as ZIP for VS Code"
              >
                {isDownloading ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
                ) : (
                  <Download className="h-3.5 w-3.5 text-primary" />
                )}
                <span className="hidden sm:inline font-medium">Download ZIP</span>
              </Button>

              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs gap-1.5"
                onClick={() => setSearchOpen(true)}
              >
                <Search className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Search Code</span>
              </Button>

              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-muted-foreground hover:text-foreground"
                onClick={() => selectedProjectId && fetchFileTree(selectedProjectId)}
                disabled={loadingTree}
                title="Refresh File Tree"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${loadingTree ? "animate-spin" : ""}`} />
              </Button>
            </>
          )}

          <Button
            variant={assistantOpen ? "default" : "outline"}
            size="sm"
            className="h-7 text-xs gap-1.5"
            onClick={() => setAssistantOpen(!assistantOpen)}
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">DAI Assistant</span>
          </Button>
        </div>
      </div>

      {/* Error Alert Bar */}
      {errorMsg && (
        <div className="flex items-center justify-between px-4 py-1.5 bg-destructive/10 border-b border-destructive/20 text-destructive text-xs shrink-0">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button
            onClick={() => setErrorMsg(null)}
            className="text-xs hover:underline font-semibold"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Main IDE Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Explorer Pane */}
        <div className="w-64 border-r border-border h-full shrink-0 flex flex-col bg-sidebar">
          {selectedProjectId ? (
            <FileTree
              nodes={fileTree}
              selectedPath={selectedPath}
              onSelectFile={handleSelectFile}
              onCreateFile={handleCreateFile}
              onDeleteFile={handleDeleteFile}
            />
          ) : (
            <div className="p-6 text-center text-xs text-muted-foreground flex flex-col items-center justify-center h-full">
              <FolderOpen className="h-8 w-8 text-muted-foreground/50 mb-2" />
              <span>Select a project above to inspect files</span>
            </div>
          )}
        </div>

        {/* Center Pane: Switches between Editor, Terminal, Live Preview, Processes, or Split */}
        <div className="flex-1 h-full min-w-0 flex flex-col bg-background overflow-hidden">
          {activeTab === "terminal" && selectedProjectId ? (
            <Terminal
              projectId={selectedProjectId}
              projectName={selectedProject?.name}
            />
          ) : activeTab === "preview" && selectedProjectId ? (
            <LivePreview
              projectId={selectedProjectId}
              projectName={selectedProject?.name}
              onLaunchDevServer={() => setActiveTab("processes")}
            />
          ) : activeTab === "processes" && selectedProjectId ? (
            <ProcessManager
              projectId={selectedProjectId}
              projectName={selectedProject?.name}
            />
          ) : activeTab === "qa" && selectedProjectId ? (
            <TestRunner projectId={selectedProjectId} />
          ) : activeTab === "split" && selectedProjectId ? (
            <div className="flex-1 flex flex-col md:flex-row h-full overflow-hidden">
              {/* Left/Top Half: Code Editor */}
              <div className="flex-1 min-w-0 h-1/2 md:h-full border-b md:border-b-0 md:border-r border-border overflow-hidden">
                {fileContent && selectedPath ? (
                  <CodeEditor
                    path={selectedPath}
                    initialContent={fileContent.content}
                    fileType={fileContent.file_type}
                    hasRevisions={fileContent.has_revisions}
                    onSave={handleSaveFile}
                    onToggleDiff={handleToggleDiff}
                    onRevert={handleRevertFile}
                  />
                ) : (
                  <div className="flex flex-col items-center justify-center h-full gap-2 text-muted-foreground p-4 text-center">
                    <FileCode className="h-8 w-8 text-muted-foreground/50" />
                    <span className="text-xs">Select a file from the explorer</span>
                  </div>
                )}
              </div>

              {/* Right/Bottom Half: Terminal */}
              <div className="flex-1 min-w-0 h-1/2 md:h-full overflow-hidden">
                <Terminal
                  projectId={selectedProjectId}
                  projectName={selectedProject?.name}
                />
              </div>
            </div>
          ) : (
            /* Default: Full Code Editor / Diff Viewer */
            loadingFile ? (
              <div className="flex flex-col items-center justify-center h-full gap-2 text-muted-foreground">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
                <span className="text-xs font-mono">Loading {selectedPath}...</span>
              </div>
            ) : isDiffMode && diffData ? (
              <MonacoDiffViewer
                path={diffData.path}
                originalContent={diffData.original_content}
                currentContent={diffData.current_content}
                fileType={fileContent?.file_type || "plaintext"}
                onClose={() => setIsDiffMode(false)}
                onRevert={handleRevertFile}
              />
            ) : fileContent && selectedPath ? (
              <CodeEditor
                path={selectedPath}
                initialContent={fileContent.content}
                fileType={fileContent.file_type}
                hasRevisions={fileContent.has_revisions}
                onSave={handleSaveFile}
                onToggleDiff={handleToggleDiff}
                onRevert={handleRevertFile}
              />
            ) : (
              <div className="flex flex-col items-center justify-center h-full gap-3 text-muted-foreground p-8 text-center">
                <div className="p-4 rounded-full bg-muted">
                  <FileCode className="h-10 w-10 text-muted-foreground/70" />
                </div>
                <h3 className="font-semibold text-foreground text-sm">No File Open</h3>
                <p className="text-xs text-muted-foreground max-w-sm">
                  Select a file from the explorer on the left or create a new one to begin editing with Monaco.
                </p>
              </div>
            )
          )}
        </div>

        {/* Right DAI Assistant Drawer */}
        {assistantOpen && (
          <div className="w-80 border-l border-border h-full shrink-0 flex flex-col bg-card/60 backdrop-blur">
            <div className="flex items-center justify-between p-3 border-b">
              <div className="flex items-center gap-1.5 text-xs font-semibold">
                <Bot className="h-4 w-4 text-primary" />
                <span>DAI Autonomous Agent</span>
              </div>
              <button
                onClick={() => setAssistantOpen(false)}
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-auto p-3 space-y-3 text-xs">
              <div className="rounded-lg bg-muted/60 p-3 text-muted-foreground leading-relaxed">
                <p className="font-medium text-foreground mb-1">Context Aware Agent</p>
                {selectedPath ? (
                  <p>
                    Currently targeting: <code className="text-primary font-mono">{selectedPath}</code>.
                    You can ask DAI to refactor code, generate unit tests, or find bugs.
                  </p>
                ) : (
                  <p>Open a file in the workspace to supply context to the autonomous coding agent.</p>
                )}
              </div>

              {aiResponse && (
                <div className="rounded-lg border border-primary/20 bg-primary/5 p-3 leading-relaxed max-h-[380px] overflow-auto font-mono text-xs">
                  <p className="font-semibold text-primary mb-1 font-sans">DAI Response</p>
                  <div className="text-foreground/90 whitespace-pre-wrap">{aiResponse}</div>
                </div>
              )}
            </div>

            <div className="p-3 border-t bg-background">
              <div className="relative">
                <Input
                  placeholder={
                    selectedPath
                      ? `Ask DAI to modify or inspect ${selectedPath.split("/").pop()}...`
                      : "Ask DAI about your project..."
                  }
                  value={aiPrompt}
                  onChange={(e) => setAiPrompt(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleAskAssistant();
                    }
                  }}
                  disabled={isAiBusy}
                  className="pr-10 text-xs h-9"
                />
                <Button
                  size="icon"
                  className="absolute right-1 top-1 h-7 w-7"
                  onClick={handleAskAssistant}
                  disabled={isAiBusy || !aiPrompt.trim()}
                >
                  {isAiBusy ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Send className="h-3.5 w-3.5" />
                  )}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Code Search Dialog */}
      <Dialog open={searchOpen} onOpenChange={setSearchOpen}>
        <DialogContent className="sm:max-w-[550px] max-h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>Search Codebase</DialogTitle>
            <DialogDescription>
              Fast text search across all files in {selectedProject?.name || "the project"}.
            </DialogDescription>
          </DialogHeader>

          <div className="flex gap-2 py-2">
            <Input
              placeholder="Search symbol, function, or text..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSearchCode();
              }}
              autoFocus
              className="text-xs"
            />
            <Button size="sm" onClick={handleSearchCode} disabled={isSearching || !searchQuery.trim()}>
              {isSearching ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "Search"}
            </Button>
          </div>

          <div className="flex-1 overflow-auto max-h-[350px] space-y-1 font-mono text-xs border rounded-md p-2 bg-muted/20">
            {searchResults.length === 0 ? (
              <div className="p-6 text-center text-muted-foreground">
                {isSearching ? "Searching codebase..." : "No search results to display."}
              </div>
            ) : (
              searchResults.map((result, idx) => (
                <div
                  key={idx}
                  onClick={() => {
                    handleSelectFile(result.path);
                    setSearchOpen(false);
                  }}
                  className="p-2 rounded hover:bg-muted cursor-pointer transition-colors border-b last:border-0 border-border/40"
                >
                  <div className="flex items-center justify-between text-primary font-semibold mb-0.5">
                    <span className="truncate">{result.path}</span>
                    <span className="text-[10px] text-muted-foreground font-normal">
                      Line {result.line_number}
                    </span>
                  </div>
                  <pre className="text-muted-foreground overflow-x-auto whitespace-pre-wrap line-clamp-2">
                    {result.line_content}
                  </pre>
                </div>
              ))
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}


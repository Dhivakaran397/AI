"use client";

import { Suspense, useEffect, useState, useCallback, useMemo } from "react";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { apiClient } from "@/lib/api-client";
import type { Project, FileNode } from "@/types";
import {
  Files,
  FileCode,
  FolderOpen,
  Search,
  ExternalLink,
  Plus,
  Trash2,
  HardDrive,
  Code2,
  Layers,
  Loader2,
} from "lucide-react";
import Link from "next/link";

interface FlatFileItem {
  name: string;
  path: string;
  size: number;
  extension: string;
}

function flattenTree(nodes: FileNode[]): FlatFileItem[] {
  const list: FlatFileItem[] = [];
  function traverse(items: FileNode[]) {
    for (const item of items) {
      if (item.is_directory) {
        if (item.children) traverse(item.children);
      } else {
        const parts = item.name.split(".");
        const ext = parts.length > 1 ? parts.pop()!.toLowerCase() : "txt";
        list.push({
          name: item.name,
          path: item.path,
          size: item.size,
          extension: ext,
        });
      }
    }
  }
  traverse(nodes);
  return list;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export default function FilesPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      }
    >
      <FilesContent />
    </Suspense>
  );
}

function FilesContent() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [fileTree, setFileTree] = useState<FileNode[]>([]);
  const [filterQuery, setFilterQuery] = useState("");
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [loadingTree, setLoadingTree] = useState(false);

  // Create file dialog
  const [createOpen, setCreateOpen] = useState(false);
  const [newFilePath, setNewFilePath] = useState("");
  const [creating, setCreating] = useState(false);

  // 1. Fetch projects
  const fetchProjects = useCallback(async () => {
    try {
      setLoadingProjects(true);
      const res = await apiClient.get<Project[]>("/projects");
      setProjects(res);
      if (res.length > 0 && !selectedProjectId) {
        setSelectedProjectId(res[0].id);
      }
    } catch (err) {
      console.error("Failed to load projects:", err);
    } finally {
      setLoadingProjects(false);
    }
  }, [selectedProjectId]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  // 2. Fetch File Tree
  const fetchTree = useCallback(async (projectId: string) => {
    try {
      setLoadingTree(true);
      const tree = await apiClient.get<FileNode[]>(`/projects/${projectId}/files/tree`);
      setFileTree(tree);
    } catch (err) {
      console.error("Failed to load file tree:", err);
      setFileTree([]);
    } finally {
      setLoadingTree(false);
    }
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      fetchTree(selectedProjectId);
    }
  }, [selectedProjectId, fetchTree]);

  // Flattened files list
  const flatFiles = useMemo(() => flattenTree(fileTree), [fileTree]);

  const filteredFiles = useMemo(() => {
    if (!filterQuery.trim()) return flatFiles;
    const q = filterQuery.toLowerCase();
    return flatFiles.filter(
      (f) => f.path.toLowerCase().includes(q) || f.name.toLowerCase().includes(q)
    );
  }, [flatFiles, filterQuery]);

  // Stats
  const totalSize = useMemo(
    () => flatFiles.reduce((acc, f) => acc + f.size, 0),
    [flatFiles]
  );

  const handleCreateFile = async () => {
    if (!selectedProjectId || !newFilePath.trim()) return;
    try {
      setCreating(true);
      await apiClient.post(`/projects/${selectedProjectId}/files`, {
        path: newFilePath.trim(),
        content: "",
      });
      setNewFilePath("");
      setCreateOpen(false);
      await fetchTree(selectedProjectId);
    } catch (err) {
      console.error("Failed to create file:", err);
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteFile = async (path: string) => {
    if (!selectedProjectId) return;
    if (!confirm(`Delete ${path}? This action is permanent.`)) return;

    try {
      await apiClient.delete(
        `/projects/${selectedProjectId}/files?path=${encodeURIComponent(path)}`
      );
      await fetchTree(selectedProjectId);
    } catch (err) {
      console.error("Failed to delete file:", err);
    }
  };

  const selectedProject = projects.find((p) => p.id === selectedProjectId);

  return (
    <>
      <Header title="Project Files" />

      <div className="flex-1 overflow-auto p-6 space-y-6">
        {/* Project Selector & Actions Bar */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-muted-foreground">Project:</span>
            {loadingProjects ? (
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            ) : projects.length === 0 ? (
              <span className="text-sm text-muted-foreground">No projects found</span>
            ) : (
              <Select
                value={selectedProjectId || ""}
                onValueChange={(val) => val && setSelectedProjectId(val)}
              >
                <SelectTrigger className="w-56 h-9 text-xs">
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
          </div>

          {selectedProjectId && (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="h-9 gap-1.5"
                onClick={() => setCreateOpen(true)}
              >
                <Plus className="h-4 w-4" />
                New File
              </Button>

              <Link href={`/workspace?projectId=${selectedProjectId}`}>
                <Button size="sm" className="h-9 gap-1.5">
                  <Code2 className="h-4 w-4" />
                  Open in IDE Workspace
                </Button>
              </Link>
            </div>
          )}
        </div>

        {/* Overview Stats Cards */}
        {selectedProjectId && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-xs font-medium text-muted-foreground">
                  Total Files
                </CardTitle>
                <Files className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{flatFiles.length}</div>
                <p className="text-xs text-muted-foreground mt-1">Files in virtual filesystem</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-xs font-medium text-muted-foreground">
                  Storage Used
                </CardTitle>
                <HardDrive className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatBytes(totalSize)}</div>
                <p className="text-xs text-muted-foreground mt-1">Total source code size</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-xs font-medium text-muted-foreground">
                  Project Status
                </CardTitle>
                <Layers className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-xl font-bold font-mono">
                  {selectedProject?.status || "UNKNOWN"}
                </div>
                <p className="text-xs text-muted-foreground mt-1">Lifecycle phase</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Filter Input */}
        {selectedProjectId && (
          <div className="flex items-center gap-3">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Filter files by name or path..."
                value={filterQuery}
                onChange={(e) => setFilterQuery(e.target.value)}
                className="pl-8 text-xs h-9"
              />
            </div>
            <span className="text-xs text-muted-foreground">
              Showing {filteredFiles.length} of {flatFiles.length} files
            </span>
          </div>
        )}

        {/* Files Table / List */}
        <div className="rounded-lg border bg-card">
          {loadingTree ? (
            <div className="flex flex-col items-center justify-center p-12 gap-2 text-muted-foreground">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
              <span className="text-xs">Loading project files...</span>
            </div>
          ) : !selectedProjectId ? (
            <div className="flex flex-col items-center justify-center p-12 gap-2 text-muted-foreground">
              <FolderOpen className="h-8 w-8 text-muted-foreground/50" />
              <span className="text-sm font-medium">Select a project to inspect files</span>
            </div>
          ) : filteredFiles.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 gap-3 text-muted-foreground">
              <FileCode className="h-10 w-10 text-muted-foreground/50" />
              <div className="text-center">
                <h4 className="text-sm font-semibold text-foreground">No files found</h4>
                <p className="text-xs mt-1">
                  {filterQuery
                    ? `No files match "${filterQuery}"`
                    : "This project has no source files yet. Create one or let DAI build it."}
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="h-8 text-xs gap-1.5"
                onClick={() => setCreateOpen(true)}
              >
                <Plus className="h-3.5 w-3.5" />
                Create First File
              </Button>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {filteredFiles.map((file) => (
                <div
                  key={file.path}
                  className="flex items-center justify-between p-3.5 hover:bg-muted/40 transition-colors"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <FileCode className="h-4 w-4 text-primary shrink-0" />
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-mono font-medium text-foreground truncate">
                          {file.name}
                        </span>
                        <Badge
                          variant="outline"
                          className="text-[10px] uppercase font-mono px-1 py-0"
                        >
                          {file.extension}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground font-mono truncate mt-0.5">
                        {file.path}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <span className="text-xs text-muted-foreground font-mono hidden sm:inline">
                      {formatBytes(file.size)}
                    </span>

                    <div className="flex items-center gap-1.5">
                      <Link href={`/workspace?projectId=${selectedProjectId}`}>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-foreground"
                          title="Open in Workspace"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </Button>
                      </Link>

                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-destructive"
                        onClick={() => handleDeleteFile(file.path)}
                        title="Delete file"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Create File Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="sm:max-w-[420px]">
          <DialogHeader>
            <DialogTitle>Create New File</DialogTitle>
            <DialogDescription>
              Specify the relative file path for project {selectedProject?.name}.
            </DialogDescription>
          </DialogHeader>

          <div className="py-2">
            <Input
              placeholder="e.g. src/components/button.tsx or README.md"
              value={newFilePath}
              onChange={(e) => setNewFilePath(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleCreateFile();
              }}
              autoFocus
              className="text-xs"
            />
          </div>

          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleCreateFile}
              disabled={creating || !newFilePath.trim()}
            >
              {creating ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" /> : null}
              Create File
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}


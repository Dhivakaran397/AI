"use client";

import { useState } from "react";
import { ChevronRight, ChevronDown, File, Folder, FolderOpen, Plus, Trash2, FilePlus, FolderPlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { FileNode } from "@/types/api";

export interface FileTreeNode {
  name: string;
  path: string;
  is_directory: boolean;
  size: number;
  children: FileTreeNode[];
}

interface FileTreeProps {
  nodes: FileTreeNode[];
  selectedPath: string | null;
  onSelectFile: (path: string) => void;
  onCreateFile: (path: string) => void;
  onDeleteFile: (path: string) => void;
}

export function FileTree({
  nodes,
  selectedPath,
  onSelectFile,
  onCreateFile,
  onDeleteFile,
}: FileTreeProps) {
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newFilePath, setNewFilePath] = useState("");

  const handleCreate = () => {
    if (!newFilePath.trim()) return;
    onCreateFile(newFilePath.trim());
    setNewFilePath("");
    setCreateDialogOpen(false);
  };

  return (
    <div className="flex flex-col h-full bg-sidebar border-r border-sidebar-border select-none">
      <div className="flex items-center justify-between p-3 border-b border-sidebar-border">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Explorer
        </span>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 text-muted-foreground hover:text-foreground"
          onClick={() => setCreateDialogOpen(true)}
          title="New File"
        >
          <FilePlus className="h-3.5 w-3.5" />
        </Button>
      </div>

      <div className="flex-1 overflow-auto p-1.5 space-y-0.5 font-mono text-xs">
        {nodes.length === 0 ? (
          <div className="p-4 text-center text-xs text-muted-foreground">
            No files in project. Click &quot;+&quot; to create one.
          </div>
        ) : (
          nodes.map((node) => (
            <TreeItem
              key={node.path}
              node={node}
              level={0}
              selectedPath={selectedPath}
              onSelectFile={onSelectFile}
              onDeleteFile={onDeleteFile}
            />
          ))
        )}
      </div>

      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>Create New File</DialogTitle>
            <DialogDescription>
              Enter file path (e.g. <code>src/index.ts</code> or <code>README.md</code>)
            </DialogDescription>
          </DialogHeader>
          <div className="py-2">
            <Input
              placeholder="e.g. src/app/page.tsx"
              value={newFilePath}
              onChange={(e) => setNewFilePath(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleCreate();
              }}
              autoFocus
            />
          </div>
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setCreateDialogOpen(false)}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleCreate} disabled={!newFilePath.trim()}>
              Create File
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function TreeItem({
  node,
  level,
  selectedPath,
  onSelectFile,
  onDeleteFile,
}: {
  node: FileTreeNode;
  level: number;
  selectedPath: string | null;
  onSelectFile: (path: string) => void;
  onDeleteFile: (path: string) => void;
}) {
  const [expanded, setExpanded] = useState(true);
  const isSelected = selectedPath === node.path;

  if (node.is_directory) {
    return (
      <div>
        <button
          onClick={() => setExpanded(!expanded)}
          style={{ paddingLeft: `${level * 12 + 6}px` }}
          className="flex items-center gap-1.5 w-full py-1 text-left rounded hover:bg-sidebar-accent transition-colors group text-muted-foreground hover:text-foreground"
        >
          {expanded ? (
            <ChevronDown className="h-3 w-3 shrink-0" />
          ) : (
            <ChevronRight className="h-3 w-3 shrink-0" />
          )}
          {expanded ? (
            <FolderOpen className="h-3.5 w-3.5 text-primary shrink-0" />
          ) : (
            <Folder className="h-3.5 w-3.5 text-primary shrink-0" />
          )}
          <span className="truncate">{node.name}</span>
        </button>

        {expanded && node.children && (
          <div className="space-y-0.5">
            {node.children.map((child) => (
              <TreeItem
                key={child.path}
                node={child}
                level={level + 1}
                selectedPath={selectedPath}
                onSelectFile={onSelectFile}
                onDeleteFile={onDeleteFile}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div
      style={{ paddingLeft: `${level * 12 + 18}px` }}
      className={`flex items-center justify-between group py-1 pr-1.5 rounded cursor-pointer transition-colors ${
        isSelected
          ? "bg-primary text-primary-foreground font-medium"
          : "hover:bg-sidebar-accent text-foreground"
      }`}
      onClick={() => onSelectFile(node.path)}
    >
      <div className="flex items-center gap-1.5 min-w-0 flex-1">
        <File className="h-3.5 w-3.5 shrink-0 opacity-70" />
        <span className="truncate">{node.name}</span>
      </div>

      <button
        onClick={(e) => {
          e.stopPropagation();
          onDeleteFile(node.path);
        }}
        className={`opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-black/10 transition-opacity ${
          isSelected ? "text-primary-foreground" : "text-muted-foreground hover:text-destructive"
        }`}
        title="Delete file"
      >
        <Trash2 className="h-3 w-3" />
      </button>
    </div>
  );
}

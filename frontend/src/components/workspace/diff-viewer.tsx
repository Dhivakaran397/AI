"use client";

import { useState } from "react";
import { DiffEditor } from "@monaco-editor/react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RotateCcw, X, Loader2 } from "lucide-react";

interface DiffViewerProps {
  path: string;
  originalContent: string;
  currentContent: string;
  fileType: string;
  onClose: () => void;
  onRevert: () => Promise<void>;
}

export function MonacoDiffViewer({
  path,
  originalContent,
  currentContent,
  fileType,
  onClose,
  onRevert,
}: DiffViewerProps) {
  const { theme } = useTheme();
  const [reverting, setReverting] = useState(false);

  const handleRevert = async () => {
    try {
      setReverting(true);
      await onRevert();
      onClose();
    } finally {
      setReverting(false);
    }
  };

  const monacoLanguage = fileType === "plaintext" ? "text" : fileType;

  return (
    <div className="flex flex-col h-full bg-background border-r border-border">
      {/* Diff Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b bg-muted/40 font-mono text-xs">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-foreground">Diff: {path}</span>
          <Badge variant="outline" className="text-[10px] uppercase font-mono px-1.5 py-0">
            Original (Left) vs Current (Right)
          </Badge>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="destructive"
            size="sm"
            className="h-7 text-xs gap-1"
            onClick={handleRevert}
            disabled={reverting}
          >
            {reverting ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <RotateCcw className="h-3 w-3" />
            )}
            Revert to Original
          </Button>

          <Button variant="ghost" size="sm" className="h-7 text-xs gap-1" onClick={onClose}>
            <X className="h-3 w-3" />
            Close Diff
          </Button>
        </div>
      </div>

      {/* Diff Editor */}
      <div className="flex-1 w-full overflow-hidden">
        <DiffEditor
          height="100%"
          language={monacoLanguage}
          theme={theme === "dark" ? "vs-dark" : "light"}
          original={originalContent}
          modified={currentContent}
          options={{
            fontSize: 13,
            lineNumbers: "on",
            readOnly: true,
            automaticLayout: true,
            renderSideBySide: true,
          }}
        />
      </div>
    </div>
  );
}

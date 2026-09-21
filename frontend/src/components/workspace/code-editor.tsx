"use client";

import { useEffect, useState } from "react";
import Editor, { useMonaco } from "@monaco-editor/react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Save, GitCompare, RotateCcw, Check, Loader2 } from "lucide-react";

interface CodeEditorProps {
  path: string;
  initialContent: string;
  fileType: string;
  hasRevisions: boolean;
  onSave: (content: string) => Promise<void>;
  onToggleDiff: () => void;
  onRevert: () => Promise<void>;
}

export function CodeEditor({
  path,
  initialContent,
  fileType,
  hasRevisions,
  onSave,
  onToggleDiff,
  onRevert,
}: CodeEditorProps) {
  const { theme } = useTheme();
  const [content, setContent] = useState(initialContent);
  const [isDirty, setIsDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [reverting, setReverting] = useState(false);

  useEffect(() => {
    setContent(initialContent);
    setIsDirty(false);
  }, [initialContent, path]);

  const handleSave = async () => {
    try {
      setSaving(true);
      await onSave(content);
      setIsDirty(false);
    } finally {
      setSaving(false);
    }
  };

  const handleRevert = async () => {
    try {
      setReverting(true);
      await onRevert();
    } finally {
      setReverting(false);
    }
  };

  const monacoLanguage = fileType === "plaintext" ? "text" : fileType;

  return (
    <div className="flex flex-col h-full bg-background border-r border-border">
      {/* Editor Header Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b bg-muted/40 font-mono text-xs">
        <div className="flex items-center gap-2 min-w-0">
          <span className="font-semibold text-foreground truncate">{path}</span>
          {isDirty && (
            <span className="h-2 w-2 rounded-full bg-amber-500 shrink-0" title="Unsaved changes" />
          )}
          <Badge variant="outline" className="text-[10px] uppercase font-mono px-1.5 py-0">
            {fileType}
          </Badge>
        </div>

        <div className="flex items-center gap-1.5">
          {hasRevisions && (
            <>
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs gap-1"
                onClick={onToggleDiff}
                title="Compare with previous version"
              >
                <GitCompare className="h-3 w-3" />
                Diff View
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs gap-1 text-muted-foreground hover:text-foreground"
                onClick={handleRevert}
                disabled={reverting}
                title="Roll back to previous revision"
              >
                {reverting ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <RotateCcw className="h-3 w-3" />
                )}
                Revert
              </Button>
            </>
          )}

          <Button
            size="sm"
            className="h-7 text-xs gap-1.5"
            onClick={handleSave}
            disabled={!isDirty || saving}
          >
            {saving ? <Loader2 className="h-3 w-3 animate-spin" /> : <Save className="h-3 w-3" />}
            Save
          </Button>
        </div>
      </div>

      {/* Monaco Editor Container */}
      <div className="flex-1 w-full overflow-hidden">
        <Editor
          height="100%"
          language={monacoLanguage}
          theme={theme === "dark" ? "vs-dark" : "light"}
          value={content}
          onChange={(val) => {
            setContent(val || "");
            setIsDirty((val || "") !== initialContent);
          }}
          options={{
            fontSize: 13,
            lineNumbers: "on",
            minimap: { enabled: true },
            scrollBeyondLastLine: false,
            wordWrap: "on",
            tabSize: 2,
            automaticLayout: true,
          }}
        />
      </div>
    </div>
  );
}

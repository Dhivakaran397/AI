"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api-client";
import type { TestGenerateResponse } from "@/types";
import {
  Sparkles,
  Loader2,
  CheckCircle2,
  AlertCircle,
  FileCode,
  Save,
} from "lucide-react";

interface TestGeneratorModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectId: string;
  onGenerated?: () => void;
}

export function TestGeneratorModal({
  open,
  onOpenChange,
  projectId,
  onGenerated,
}: TestGeneratorModalProps) {
  const [filePath, setFilePath] = useState<string>("src/calculator.py");
  const [framework, setFramework] = useState<"pytest" | "jest" | "vitest">("pytest");
  const [instructions, setInstructions] = useState<string>("");
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [result, setResult] = useState<TestGenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!filePath.trim()) {
      setError("Please specify a source file path.");
      return;
    }

    setIsGenerating(true);
    setError(null);
    setResult(null);
    setSavedMessage(null);

    try {
      const res = await apiClient.post<TestGenerateResponse>(
        `/api/v1/projects/${projectId}/tests/generate`,
        {
          file_path: filePath.trim(),
          framework,
          extra_instructions: instructions.trim() || undefined,
        }
      );
      setResult(res);
    } catch (err: any) {
      setError(err?.message || "Failed to generate tests");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSaveToFiles = async () => {
    if (!result) return;
    setIsSaving(true);
    setError(null);

    try {
      await apiClient.post(`/api/v1/projects/${projectId}/files/write`, {
        path: result.test_file_path,
        content: result.test_code,
      });
      setSavedMessage(`Saved test file to '${result.test_file_path}' successfully.`);
      if (onGenerated) onGenerated();
    } catch (err: any) {
      setError(err?.message || "Failed to save test file");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <DialogTitle>Generate Automated Test Suite</DialogTitle>
              <DialogDescription>
                DAI QA Agent inspects contracts, dependencies, and edge cases to synthesize tests.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-2 space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Target Source File
              </label>
              <Input
                value={filePath}
                onChange={(e) => setFilePath(e.target.value)}
                placeholder="e.g. src/auth/service.py or components/button.tsx"
                disabled={isGenerating}
                className="font-mono text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Test Framework
              </label>
              <select
                value={framework}
                onChange={(e) => setFramework(e.target.value as any)}
                disabled={isGenerating}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
              >
                <option value="pytest">Pytest (Python)</option>
                <option value="jest">Jest (TS/JS)</option>
                <option value="vitest">Vitest (TS/JS)</option>
              </select>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Extra Testing Requirements (Optional)
            </label>
            <textarea
              rows={2}
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder="e.g. Test edge cases like empty arrays, expired tokens, and network timeouts"
              disabled={isGenerating}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-xs shadow-sm focus:outline-none focus:ring-1 focus:ring-ring resize-none"
            />
          </div>

          {error && (
            <div className="flex items-center gap-2 rounded-lg bg-destructive/10 p-3 text-xs text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {savedMessage && (
            <div className="flex items-center gap-2 rounded-lg bg-emerald-500/10 p-3 text-xs text-emerald-600 border border-emerald-500/20">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              <span>{savedMessage}</span>
            </div>
          )}

          <Button
            onClick={handleGenerate}
            disabled={isGenerating || !filePath.trim()}
            className="w-full"
          >
            {isGenerating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Synthesizing Test Cases...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4 text-emerald-400" /> Generate Test Suite
              </>
            )}
          </Button>

          {/* Generated Result */}
          {result && (
            <div className="mt-3 space-y-3 rounded-xl border border-border/60 bg-muted/20 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileCode className="h-4 w-4 text-emerald-500" />
                  <span className="font-mono text-xs font-semibold">{result.test_file_path}</span>
                </div>
                <Badge variant="outline" className="text-[11px] font-mono">
                  ~{result.test_count_estimated} test cases
                </Badge>
              </div>

              <pre className="max-h-56 overflow-y-auto rounded-md bg-black/90 p-3 font-mono text-[11px] text-zinc-300">
                {result.test_code}
              </pre>

              <Button
                onClick={handleSaveToFiles}
                disabled={isSaving}
                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                {isSaving ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Writing to Virtual Filesystem...
                  </>
                ) : (
                  <>
                    <Save className="mr-2 h-4 w-4" /> Save to {result.test_file_path}
                  </>
                )}
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

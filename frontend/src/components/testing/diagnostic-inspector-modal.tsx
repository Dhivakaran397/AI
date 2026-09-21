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
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api-client";
import type { ErrorTraceAnalysisResponse, ApplyPatchResponse } from "@/types";
import {
  Bug,
  CheckCircle2,
  AlertCircle,
  Code2,
  FileCode,
  Loader2,
  Sparkles,
} from "lucide-react";

interface DiagnosticInspectorModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectId: string;
  initialTrace?: string;
  onPatchApplied?: () => void;
}

export function DiagnosticInspectorModal({
  open,
  onOpenChange,
  projectId,
  initialTrace = "",
  onPatchApplied,
}: DiagnosticInspectorModalProps) {
  const [trace, setTrace] = useState<string>(initialTrace);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [isApplying, setIsApplying] = useState<boolean>(false);
  const [diagnosis, setDiagnosis] = useState<ErrorTraceAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [applyResult, setApplyResult] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!trace.trim()) return;
    setIsAnalyzing(true);
    setError(null);
    setApplyResult(null);

    try {
      const res = await apiClient.post<ErrorTraceAnalysisResponse>(
        `/api/v1/projects/${projectId}/debug/analyze`,
        { raw_trace: trace.trim() }
      );
      setDiagnosis(res);
    } catch (err: any) {
      setError(err?.message || "Failed to analyze error trace");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleApplyPatch = async () => {
    if (!diagnosis || !diagnosis.culprit_file || !diagnosis.suggested_fix) return;
    setIsApplying(true);
    setError(null);

    try {
      const res = await apiClient.post<ApplyPatchResponse>(
        `/api/v1/projects/${projectId}/debug/apply-patch`,
        {
          file_path: diagnosis.culprit_file,
          patched_content: diagnosis.suggested_fix,
          description: `Auto-patch for ${diagnosis.error_type}: ${diagnosis.error_message}`,
        }
      );
      setApplyResult(res.message);
      if (onPatchApplied) onPatchApplied();
    } catch (err: any) {
      setError(err?.message || "Failed to apply diagnostic patch");
    } finally {
      setIsApplying(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-500/10 text-rose-600">
              <Bug className="h-5 w-5" />
            </div>
            <div>
              <DialogTitle>AI Error Diagnostic & Patch Inspector</DialogTitle>
              <DialogDescription>
                Isolate failure frames, diagnose root causes, and preview surgical code diffs.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Stack trace input / viewer */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Error Log / Traceback
            </label>
            <textarea
              rows={4}
              value={trace}
              onChange={(e) => setTrace(e.target.value)}
              placeholder="Paste stack trace or select a failed test..."
              className="w-full rounded-md border border-input bg-black/80 p-2 font-mono text-xs text-zinc-200 shadow-sm focus:outline-none focus:ring-1 focus:ring-ring resize-none"
            />
          </div>

          <Button
            onClick={handleAnalyze}
            disabled={isAnalyzing || !trace.trim()}
            className="w-full"
            variant="outline"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Isolating Culprit & Root Cause...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4 text-indigo-500" /> Diagnose Failure
              </>
            )}
          </Button>

          {error && (
            <div className="flex items-center gap-2 rounded-lg bg-destructive/10 p-3 text-xs text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {applyResult && (
            <div className="flex items-center gap-2 rounded-lg bg-emerald-500/10 p-3 text-xs text-emerald-600 border border-emerald-500/20">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              <span>{applyResult}</span>
            </div>
          )}

          {/* Diagnosis Results */}
          {diagnosis && (
            <div className="space-y-3 rounded-xl border border-border/60 bg-muted/20 p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Badge variant="destructive" className="font-mono text-xs">
                    {diagnosis.error_type}
                  </Badge>
                  {diagnosis.culprit_file && (
                    <span className="flex items-center text-xs font-mono text-muted-foreground">
                      <FileCode className="mr-1 h-3.5 w-3.5" />
                      {diagnosis.culprit_file}
                      {diagnosis.culprit_line ? `:${diagnosis.culprit_line}` : ""}
                    </span>
                  )}
                </div>
              </div>

              {/* Diagnosis text */}
              <div className="rounded-lg border border-border/40 bg-background/90 p-3 text-xs">
                <p className="font-semibold text-foreground mb-1">Diagnosis</p>
                <p className="text-muted-foreground leading-relaxed">{diagnosis.diagnosis}</p>
              </div>

              {/* Code context */}
              {diagnosis.surrounding_code && (
                <div className="space-y-1">
                  <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                    Culprit Code Context
                  </p>
                  <pre className="rounded-md bg-black/90 p-2.5 font-mono text-[11px] text-zinc-300 overflow-x-auto">
                    {diagnosis.surrounding_code}
                  </pre>
                </div>
              )}

              {/* Suggested Diff */}
              {diagnosis.suggested_diff && (
                <div className="space-y-1">
                  <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                    Suggested Patch Diff
                  </p>
                  <pre className="rounded-md bg-zinc-950 p-2.5 font-mono text-[11px] text-emerald-400 overflow-x-auto max-h-48">
                    {diagnosis.suggested_diff}
                  </pre>
                </div>
              )}

              {/* Apply Patch Action */}
              {diagnosis.suggested_fix && diagnosis.culprit_file && (
                <Button
                  onClick={handleApplyPatch}
                  disabled={isApplying}
                  className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
                >
                  {isApplying ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Committing Patch to Filesystem...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="mr-2 h-4 w-4" /> Apply Patch to {diagnosis.culprit_file}
                    </>
                  )}
                </Button>
              )}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

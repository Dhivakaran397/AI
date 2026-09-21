"use client";

import { useState, useEffect } from "react";
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
import type { SelfHealResponse, Project } from "@/types";
import {
  Wrench,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Bug,
  Code2,
  Terminal,
} from "lucide-react";

interface SelfHealModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projects: Project[];
  selectedProjectId?: string;
  onComplete?: () => void;
}

export function SelfHealModal({
  open,
  onOpenChange,
  projects,
  selectedProjectId,
  onComplete,
}: SelfHealModalProps) {
  const [projectId, setProjectId] = useState<string>(selectedProjectId || "");
  const [testCommand, setTestCommand] = useState<string>("pytest");
  const [maxRetries, setMaxRetries] = useState<number>(3);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SelfHealResponse | null>(null);

  useEffect(() => {
    if (open) {
      if (selectedProjectId && projects.some((p) => p.id === selectedProjectId)) {
        setProjectId(selectedProjectId);
      } else if (projects.length > 0) {
        setProjectId((prev) => (prev && projects.some((p) => p.id === prev) ? prev : projects[0].id));
      } else {
        setProjectId("");
      }
    }
  }, [open, selectedProjectId, projects]);

  const handleRun = async () => {
    if (!projectId) {
      setError("Please select a project.");
      return;
    }

    setError(null);
    setIsRunning(true);
    setResult(null);

    try {
      const response = await apiClient.post<SelfHealResponse>(
        "/agents/self-heal",
        {
          project_id: projectId,
          test_command: testCommand.trim() || "pytest",
          max_retries: maxRetries,
        }
      );
      setResult(response);
      if (onComplete) onComplete();
    } catch (err: any) {
      setError(err?.message || "Self-healing pipeline failed");
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-500/10 text-rose-600">
              <Wrench className="h-5 w-5" />
            </div>
            <div>
              <DialogTitle>Autonomous Self-Healing Loop</DialogTitle>
              <DialogDescription>
                Debugger and Coder diagnose failures, apply surgical fixes, and re-run tests until green.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Target Project
            </label>
            <select
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              disabled={isRunning}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.status})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-2 space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Verification Command
              </label>
              <Input
                value={testCommand}
                onChange={(e) => setTestCommand(e.target.value)}
                placeholder="pytest"
                disabled={isRunning}
                className="font-mono text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Max Retries
              </label>
              <Input
                type="number"
                min={1}
                max={5}
                value={maxRetries}
                onChange={(e) => setMaxRetries(parseInt(e.target.value) || 3)}
                disabled={isRunning}
              />
            </div>
          </div>

          {error && (
            <div className="flex items-center gap-2 rounded-lg bg-destructive/10 p-3 text-xs text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <Button
            onClick={handleRun}
            disabled={isRunning}
            className="w-full bg-rose-600 hover:bg-rose-700 text-white"
          >
            {isRunning ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Diagnosing & Healing Codebase...
              </>
            ) : (
              <>
                <Wrench className="mr-2 h-4 w-4" /> Run Autonomous Self-Healing Loop
              </>
            )}
          </Button>

          {result && (
            <div className="mt-4 space-y-3 rounded-xl border border-border/60 bg-muted/20 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold">Healing Result</span>
                  <Badge variant="outline" className="font-mono text-xs">
                    {result.iterations} iterations
                  </Badge>
                </div>
                {result.resolved ? (
                  <Badge className="bg-emerald-500/10 text-emerald-600 border-emerald-500/20">
                    <CheckCircle2 className="mr-1 h-3 w-3" /> Resolved
                  </Badge>
                ) : (
                  <Badge variant="destructive">
                    <AlertCircle className="mr-1 h-3 w-3" /> Unresolved
                  </Badge>
                )}
              </div>

              {result.diagnosis && (
                <div className="rounded-lg border border-border/40 bg-background/80 p-2.5 text-xs">
                  <div className="flex items-center gap-1.5 font-semibold text-rose-600 dark:text-rose-400 mb-1">
                    <Bug className="h-3.5 w-3.5" />
                    <span>Debugger Diagnosis</span>
                  </div>
                  <p className="text-muted-foreground">{result.diagnosis}</p>
                </div>
              )}

              {result.patches_applied && result.patches_applied.length > 0 && (
                <div className="rounded-lg border border-border/40 bg-background/80 p-2.5 text-xs">
                  <div className="flex items-center gap-1.5 font-semibold text-emerald-600 dark:text-emerald-400 mb-1">
                    <Code2 className="h-3.5 w-3.5" />
                    <span>Patches Applied by Coder</span>
                  </div>
                  <ul className="list-disc pl-4 space-y-0.5 text-muted-foreground">
                    {result.patches_applied.map((patch, idx) => (
                      <li key={idx}>{patch}</li>
                    ))}
                  </ul>
                </div>
              )}

              {result.final_output && (
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-[11px] font-semibold text-muted-foreground">
                    <Terminal className="h-3 w-3" /> Output
                  </div>
                  <pre className="max-h-32 overflow-y-auto rounded-md bg-black/80 p-2 font-mono text-[11px] text-zinc-200">
                    {result.final_output}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

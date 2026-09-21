"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
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
import type { TeamOrchestrationResponse, OrchestrationStep, Project } from "@/types";
import {
  Users,
  Sparkles,
  Loader2,
  CheckCircle2,
  Clock,
  FileCode,
  AlertCircle,
  ArrowRight,
} from "lucide-react";

interface OrchestrationModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projects: Project[];
  selectedProjectId?: string;
  onComplete?: () => void;
}

export function OrchestrationModal({
  open,
  onOpenChange,
  projects,
  selectedProjectId,
  onComplete,
}: OrchestrationModalProps) {
  const [projectId, setProjectId] = useState<string>(selectedProjectId || "");
  const [goal, setGoal] = useState<string>("");
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TeamOrchestrationResponse | null>(null);

  useEffect(() => {
    if (open) {
      let activeId = "";
      if (selectedProjectId && projects.some((p) => p.id === selectedProjectId)) {
        activeId = selectedProjectId;
      } else if (projects.length > 0) {
        activeId = projects[0].id;
      }
      setProjectId(activeId);

      const selProj = projects.find((p) => p.id === activeId);
      if (selProj?.description && (!goal || goal.trim() === ".")) {
        setGoal(selProj.description);
      }
    }
  }, [open, selectedProjectId, projects]);

  const handleRun = async () => {
    const selProj = projects.find((p) => p.id === projectId);
    const effectiveGoal = goal.trim() && goal.trim() !== "." ? goal.trim() : (selProj?.description || "");

    if (!projectId) {
      setError("Please select a project.");
      return;
    }
    if (!effectiveGoal) {
      setError("Please enter a goal or feature description.");
      return;
    }

    setError(null);
    setIsRunning(true);
    setResult(null);

    try {
      const response = await apiClient.post<TeamOrchestrationResponse>(
        "/agents/orchestrate",
        {
          project_id: projectId,
          goal: effectiveGoal,
        }
      );
      setResult(response);
      if (onComplete) onComplete();
    } catch (err: any) {
      setError(err?.message || "Failed to orchestrate team");
    } finally {
      setIsRunning(false);
    }
  };

  const getStepStatusBadge = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return (
          <Badge className="bg-emerald-500/10 text-emerald-600 border-emerald-500/20">
            <CheckCircle2 className="mr-1 h-3 w-3" /> Completed
          </Badge>
        );
      case "RUNNING":
        return (
          <Badge className="bg-blue-500/10 text-blue-600 border-blue-500/20">
            <Loader2 className="mr-1 h-3 w-3 animate-spin" /> In Progress
          </Badge>
        );
      case "FAILED":
        return (
          <Badge variant="destructive">
            <AlertCircle className="mr-1 h-3 w-3" /> Failed
          </Badge>
        );
      default:
        return (
          <Badge variant="secondary">
            <Clock className="mr-1 h-3 w-3" /> Pending
          </Badge>
        );
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-600">
              <Users className="h-5 w-5" />
            </div>
            <div>
              <DialogTitle>Dispatch Autonomous Agent Team</DialogTitle>
              <DialogDescription>
                Lead Orchestrator, Architect, Coder, Tester, and Reviewer coordinate to implement your goal.
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
              onChange={(e) => {
                const newId = e.target.value;
                setProjectId(newId);
                const sel = projects.find((p) => p.id === newId);
                if (sel?.description && (!goal || goal.trim() === ".")) {
                  setGoal(sel.description);
                }
              }}
              disabled={isRunning}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
            >
              {projects.length === 0 ? (
                <option value="">No projects available (Create a project first)</option>
              ) : (
                projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.status})
                  </option>
                ))
              )}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Feature Goal / Requirement
            </label>
            <textarea
              rows={3}
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="e.g. Create a simple, clean, and modern home page using HTML and CSS"
              disabled={isRunning}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring resize-none"
            />
            <div className="flex flex-wrap gap-1.5 pt-1">
              <span className="text-[10px] text-muted-foreground self-center">Quick fill:</span>
              {[
                "Build initial HTML and CSS website layout",
                "Create responsive navigation and hero section",
                "Implement project requirements from description",
              ].map((suggestion, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setGoal(suggestion)}
                  className="text-[11px] px-2 py-0.5 rounded-md bg-muted hover:bg-muted/80 text-foreground transition-colors border border-border/60"
                >
                  + {suggestion}
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div className="flex items-center gap-2 rounded-lg bg-destructive/10 p-3 text-xs text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {(!projectId || !goal.trim()) && !isRunning && (
            <p className="text-xs text-amber-500/90 flex items-center gap-1.5">
              <span>⚠️</span>
              {!projectId
                ? "Please select a target project."
                : "Type what you want the agents to build, or click a quick-fill chip above."}
            </p>
          )}

          <Button
            onClick={handleRun}
            disabled={isRunning || !goal.trim() || !projectId}
            className="w-full"
          >
            {isRunning ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Orchestrating Team Pipeline...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" /> Start Multi-Agent Pipeline
              </>
            )}
          </Button>

          {/* Results Visualizer */}
          {result && (
            <div className="mt-4 space-y-4 rounded-xl border border-border/60 bg-muted/20 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-semibold">Pipeline Result</h4>
                  <p className="text-xs text-muted-foreground">{result.summary}</p>
                </div>
                <Badge className="bg-emerald-500/10 text-emerald-600 border-emerald-500/20">
                  {result.status}
                </Badge>
              </div>

              {/* Execution Steps */}
              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Agent Pipeline Steps
                </p>
                <div className="space-y-2">
                  {result.steps.map((step: OrchestrationStep, idx: number) => (
                    <div
                      key={step.step_id || idx}
                      className="rounded-lg border border-border/40 bg-background/80 p-3 text-xs shadow-sm"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[11px] font-bold text-muted-foreground">
                            0{idx + 1}
                          </span>
                          <span className="font-semibold">{step.agent_name}</span>
                          <Badge variant="outline" className="text-[10px] font-mono">
                            {step.agent_type}
                          </Badge>
                        </div>
                        {getStepStatusBadge(step.status)}
                      </div>
                      <p className="mt-1 text-muted-foreground">{step.action}</p>
                      {step.output_summary && (
                        <p className="mt-1 text-[11px] text-foreground font-mono bg-muted/40 p-1.5 rounded">
                          {step.output_summary}
                        </p>
                      )}
                      {step.artifacts && step.artifacts.length > 0 && (
                        <div className="mt-2 flex flex-wrap items-center gap-1">
                          <span className="text-[10px] text-muted-foreground">Artifacts:</span>
                          {step.artifacts.map((art, aIdx) => (
                            <Badge key={aIdx} variant="secondary" className="text-[10px]">
                              <FileCode className="mr-1 h-2.5 w-2.5" />
                              {art}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Created Files */}
              {result.created_files && result.created_files.length > 0 && (
                <div className="pt-2 border-t border-border/40">
                  <p className="text-xs font-semibold text-muted-foreground mb-1.5">
                    Files Created in Virtual Filesystem:
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {result.created_files.map((file) => (
                      <Badge key={file} variant="outline" className="font-mono text-[11px]">
                        <FileCode className="mr-1 h-3 w-3 text-emerald-500" />
                        {file}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Direct Action: Open in Workspace IDE */}
              <div className="pt-3 border-t border-border/60 flex items-center justify-between gap-3 bg-primary/5 p-3 rounded-lg border border-primary/20">
                <div className="text-xs">
                  <p className="font-semibold text-foreground">Project Pipeline Finished</p>
                  <p className="text-muted-foreground text-[11px]">
                    Autonomous agents compiled code and tests. Jump into Workspace IDE to preview and run.
                  </p>
                </div>
                <Link href={`/workspace?projectId=${projectId}`}>
                  <Button
                    size="sm"
                    className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90 h-8 text-xs font-semibold shrink-0"
                    onClick={() => onOpenChange(false)}
                  >
                    <span>Open in Workspace</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Button>
                </Link>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

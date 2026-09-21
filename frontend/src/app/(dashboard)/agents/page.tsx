"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { AgentCard } from "@/components/agents/agent-card";
import { OrchestrationModal } from "@/components/agents/orchestration-modal";
import { SelfHealModal } from "@/components/agents/self-heal-modal";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { apiClient } from "@/lib/api-client";
import type { Agent, AgentRun, Project } from "@/types";
import {
  Users,
  Sparkles,
  Wrench,
  Bot,
  RefreshCw,
  Loader2,
  CheckCircle2,
  Clock,
  AlertCircle,
  Play,
  Activity,
} from "lucide-react";

export default function AgentsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      }
    >
      <AgentsContent />
    </Suspense>
  );
}

function AgentsContent() {
  const searchParams = useSearchParams();
  const queryProjectId = searchParams.get("projectId") || "";
  const autoOpen = searchParams.get("autoOpen") === "true";

  const [agents, setAgents] = useState<Agent[]>([]);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Modals state
  const [orchestrationOpen, setOrchestrationOpen] = useState<boolean>(false);
  const [selfHealOpen, setSelfHealOpen] = useState<boolean>(false);

  // Single agent dispatch modal
  const [dispatchAgent, setDispatchAgent] = useState<Agent | null>(null);
  const [singleTask, setSingleTask] = useState<string>("");
  const [singleProjectId, setSingleProjectId] = useState<string>(queryProjectId);
  const [singleRunning, setSingleRunning] = useState<boolean>(false);
  const [singleResult, setSingleResult] = useState<AgentRun | null>(null);
  const [singleError, setSingleError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [agentsData, runsData, projectsData] = await Promise.all([
        apiClient.get<Agent[]>("/agents").catch((err) => {
          console.warn("Could not load agents", err);
          return [];
        }),
        apiClient.get<AgentRun[]>("/agents/runs/history").catch((err) => {
          console.warn("Could not load agent runs", err);
          return [];
        }),
        apiClient.get<Project[]>("/projects").catch((err) => {
          console.warn("Could not load projects", err);
          return [];
        }),
      ]);
      setAgents(agentsData || []);
      setRuns(runsData || []);
      setProjects(projectsData || []);
      if (projectsData && projectsData.length > 0) {
        setSingleProjectId((prev) => prev || projectsData[0].id);
      }
    } catch (err) {
      console.error("Failed to load agent data", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (queryProjectId) {
      setSingleProjectId(queryProjectId);
      if (autoOpen) {
        setOrchestrationOpen(true);
      }
    }
  }, [queryProjectId, autoOpen]);

  const handleSingleDispatch = async () => {
    if (!dispatchAgent) return;
    if (!singleProjectId) {
      setSingleError("Please select a project.");
      return;
    }
    if (!singleTask.trim()) {
      setSingleError("Please describe the task for this agent.");
      return;
    }

    setSingleRunning(true);
    setSingleError(null);
    setSingleResult(null);

    try {
      const run = await apiClient.post<AgentRun>("/agents/runs", {
        agent_id: dispatchAgent.id,
        project_id: singleProjectId,
        input_data: { task: singleTask.trim() },
      });
      setSingleResult(run);
      fetchData();
    } catch (err: any) {
      setSingleError(err?.message || "Failed to execute agent run");
    } finally {
      setSingleRunning(false);
    }
  };

  return (
    <>
      <Header title="Autonomous Agent Roster" />
      <div className="flex-1 space-y-6 overflow-auto p-6">
        {/* Top Control Bar */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-tight">Specialized Agent Team</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              8 role-specific autonomous agents collaborating with shared context and self-healing pipelines.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchData()}
              disabled={loading}
            >
              <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (projects.length === 0) {
                  fetchData();
                }
                setSelfHealOpen(true);
              }}
              className="border-rose-500/30 text-rose-600 hover:bg-rose-500/10 dark:text-rose-400"
            >
              <Wrench className="mr-1.5 h-3.5 w-3.5" />
              Self-Healing Loop
            </Button>
            <Button
              size="sm"
              onClick={() => {
                if (projects.length === 0) {
                  fetchData();
                }
                setOrchestrationOpen(true);
              }}
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              <Sparkles className="mr-1.5 h-3.5 w-3.5" />
              Dispatch Team Pipeline
            </Button>
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-600">
                <Users className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Active Roster</p>
                <p className="text-lg font-bold">{agents.length || 8} Agents</p>
              </div>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600">
                <CheckCircle2 className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Completed Runs</p>
                <p className="text-lg font-bold">
                  {runs.filter((r) => r.status === "COMPLETED").length}
                </p>
              </div>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-500/10 text-blue-600">
                <Activity className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Total Executions</p>
                <p className="text-lg font-bold">{runs.length}</p>
              </div>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-purple-500/10 text-purple-600">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Orchestration DAG</p>
                <p className="text-lg font-bold">Linear & Branching</p>
              </div>
            </div>
          </Card>
        </div>

        {/* 8 Agent Cards Grid */}
        <div className="space-y-3">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
            Specialized Roles & Capabilities
          </h3>
          {loading && agents.length === 0 ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {agents.map((agent) => (
                <AgentCard
                  key={agent.id}
                  agent={agent}
                  onDispatch={(a) => {
                    setDispatchAgent(a);
                    setSingleTask("");
                    setSingleResult(null);
                    setSingleError(null);
                  }}
                />
              ))}
            </div>
          )}
        </div>

        {/* Recent Runs History Table */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              Recent Agent Activity
            </h3>
            <span className="text-xs text-muted-foreground font-mono">
              {runs.length} runs recorded
            </span>
          </div>

          <Card className="overflow-hidden">
            <CardContent className="p-0">
              {runs.length === 0 ? (
                <div className="py-12 text-center text-xs text-muted-foreground">
                  No agent runs recorded yet. Click &quot;Dispatch Team Pipeline&quot; or dispatch an individual agent above.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-muted/50 border-b border-border text-muted-foreground">
                      <tr>
                        <th className="p-3">Agent</th>
                        <th className="p-3">Type</th>
                        <th className="p-3">Task Summary</th>
                        <th className="p-3">Status</th>
                        <th className="p-3">Started</th>
                        <th className="p-3">Completed</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/60 font-mono">
                      {runs.map((run) => (
                        <tr key={run.id} className="hover:bg-muted/20">
                          <td className="p-3 font-medium font-sans text-foreground">
                            {run.agent_name || "Specialist Agent"}
                          </td>
                          <td className="p-3">
                            <Badge variant="outline" className="text-[10px]">
                              {run.agent_type || "SPECIALIST"}
                            </Badge>
                          </td>
                          <td className="p-3 max-w-xs truncate text-muted-foreground font-sans">
                            {run.input_data?.task || JSON.stringify(run.input_data)}
                          </td>
                          <td className="p-3">
                            <Badge
                              className={`text-[10px] ${
                                run.status === "COMPLETED"
                                  ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
                                  : run.status === "RUNNING"
                                  ? "bg-blue-500/10 text-blue-600 border-blue-500/20"
                                  : run.status === "FAILED"
                                  ? "bg-rose-500/10 text-rose-600 border-rose-500/20"
                                  : "bg-muted text-muted-foreground"
                              }`}
                            >
                              {run.status}
                            </Badge>
                          </td>
                          <td className="p-3 text-muted-foreground text-[11px]">
                            {run.started_at ? new Date(run.started_at).toLocaleTimeString() : "-"}
                          </td>
                          <td className="p-3 text-muted-foreground text-[11px]">
                            {run.completed_at
                              ? new Date(run.completed_at).toLocaleTimeString()
                              : "-"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Team Orchestration Modal */}
      <OrchestrationModal
        open={orchestrationOpen}
        onOpenChange={setOrchestrationOpen}
        projects={projects}
        selectedProjectId={queryProjectId || singleProjectId || undefined}
        onComplete={fetchData}
      />

      {/* Self-Healing Loop Modal */}
      <SelfHealModal
        open={selfHealOpen}
        onOpenChange={setSelfHealOpen}
        projects={projects}
        onComplete={fetchData}
      />

      {/* Single Agent Task Dispatch Modal */}
      <Dialog open={Boolean(dispatchAgent)} onOpenChange={(open) => !open && setDispatchAgent(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Dispatch {dispatchAgent?.name}</DialogTitle>
            <DialogDescription>
              Assign a direct task to {dispatchAgent?.name} ({dispatchAgent?.type}).
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Target Project
              </label>
              <select
                value={singleProjectId}
                onChange={(e) => setSingleProjectId(e.target.value)}
                disabled={singleRunning}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.status})
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Task Description
              </label>
              <textarea
                rows={3}
                value={singleTask}
                onChange={(e) => setSingleTask(e.target.value)}
                placeholder="e.g. Audit security of authentication endpoints and check for CORS vulnerabilities"
                disabled={singleRunning}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring resize-none"
              />
            </div>

            {singleError && (
              <div className="flex items-center gap-2 rounded-lg bg-destructive/10 p-3 text-xs text-destructive">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{singleError}</span>
              </div>
            )}

            <Button
              onClick={handleSingleDispatch}
              disabled={singleRunning || !singleTask.trim()}
              className="w-full"
            >
              {singleRunning ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Running Specialist...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" /> Run Task
                </>
              )}
            </Button>

            {singleResult && (
              <div className="mt-3 rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-3 text-xs text-emerald-700 dark:text-emerald-300">
                <div className="flex items-center gap-1.5 font-semibold">
                  <CheckCircle2 className="h-4 w-4" /> Run {singleResult.status}
                </div>
                <p className="mt-1 font-mono text-[11px]">
                  {singleResult.output_data?.output || "Task completed successfully."}
                </p>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

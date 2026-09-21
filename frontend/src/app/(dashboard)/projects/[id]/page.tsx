"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiClient } from "@/lib/api-client";
import {
  FolderKanban,
  CheckCircle2,
  Circle,
  Clock,
  AlertCircle,
  Plus,
  MessageSquare,
  Activity,
  ArrowRight,
  Loader2,
  Trash2,
  GitBranch,
  Download,
} from "lucide-react";
import { toast } from "sonner";
import type { ProjectDetail, Task, TaskPriority, TaskStatus, ProjectStatus } from "@/types/project";

const PIPELINE_STAGES: ProjectStatus[] = [
  "IDEA",
  "PLANNING",
  "BUILDING",
  "TESTING",
  "DEBUGGING",
  "REVIEW",
  "COMPLETED",
];

const PRIORITY_BADGES: Record<TaskPriority, string> = {
  LOW: "bg-zinc-500/10 text-zinc-500 border-zinc-500/20",
  MEDIUM: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  HIGH: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  CRITICAL: "bg-rose-500/10 text-rose-500 border-rose-500/20",
};

export default function ProjectWorkspacePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);

  // New task dialog state
  const [taskDialogOpen, setTaskDialogOpen] = useState(false);
  const [taskTitle, setTaskTitle] = useState("");
  const [taskDesc, setTaskDesc] = useState("");
  const [taskPriority, setTaskPriority] = useState<TaskPriority>("MEDIUM");
  const [taskSubmitting, setTaskSubmitting] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const fetchProject = async () => {
    try {
      setLoading(true);
      const data = await apiClient.get<ProjectDetail>(`/projects/${id}`);
      setProject(data);
    } catch {
      toast.error("Failed to load project details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProject();
  }, [id]);

  const handleStatusChange = async (newStatus: string) => {
    if (!project) return;
    try {
      const updated = await apiClient.patch<ProjectDetail>(`/projects/${id}`, {
        status: newStatus,
      });
      setProject({ ...project, status: updated.status });
      toast.success(`Project moved to ${newStatus}`);
    } catch {
      toast.error("Failed to update status");
    }
  };

  const handleCreateTask = async () => {
    if (!taskTitle.trim() || !project) return;
    try {
      setTaskSubmitting(true);
      const newTask = await apiClient.post<Task>("/tasks", {
        project_id: id,
        title: taskTitle.trim(),
        description: taskDesc.trim() || null,
        priority: taskPriority,
      });
      setProject({
        ...project,
        tasks: [...project.tasks, newTask],
        task_count: project.task_count + 1,
      });
      setTaskTitle("");
      setTaskDesc("");
      setTaskDialogOpen(false);
      toast.success("Task added to project");
    } catch {
      toast.error("Failed to create task");
    } finally {
      setTaskSubmitting(false);
    }
  };

  const handleDownloadProject = async () => {
    if (!project) return;
    try {
      setDownloading(true);
      const safeName = `${project.name.toLowerCase().replace(/[^a-z0-9]/g, "_")}.zip`;
      await apiClient.downloadFile(`/projects/${project.id}/download`, safeName);
      toast.success("Project ZIP downloaded successfully!");
    } catch {
      toast.error("Failed to download project archive");
    } finally {
      setDownloading(false);
    }
  };

  const handleTaskStatusToggle = async (taskId: string, currentStatus: TaskStatus) => {
    if (!project) return;
    const nextStatus: TaskStatus = currentStatus === "DONE" ? "TODO" : "DONE";
    try {
      await apiClient.patch<Task>(`/tasks/${taskId}`, {
        status: nextStatus,
      });

      const updatedTasks = project.tasks.map((t) =>
        t.id === taskId ? { ...t, status: nextStatus } : t
      );
      const completedCount = updatedTasks.filter((t) => t.status === "DONE").length;

      setProject({
        ...project,
        tasks: updatedTasks,
        completed_task_count: completedCount,
      });
    } catch {
      toast.error("Failed to update task status");
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    if (!project) return;
    try {
      await apiClient.delete(`/tasks/${taskId}`);
      const remaining = project.tasks.filter((t) => t.id !== taskId);
      setProject({
        ...project,
        tasks: remaining,
        task_count: project.task_count - 1,
        completed_task_count: remaining.filter((t) => t.status === "DONE").length,
      });
      toast.success("Task removed");
    } catch {
      toast.error("Failed to delete task");
    }
  };

  if (loading) {
    return (
      <>
        <Header title="Project Workspace" />
        <div className="flex items-center justify-center py-24">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </>
    );
  }

  if (!project) {
    return (
      <>
        <Header title="Project Workspace" />
        <div className="p-8 text-center">
          <p className="text-muted-foreground">Project not found.</p>
        </div>
      </>
    );
  }

  const currentStageIndex = PIPELINE_STAGES.indexOf(project.status);
  const tags = (project.tech_stack?.tags as string[]) || [];

  return (
    <>
      <Header title={project.name} />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Top Bar with Status and Actions */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b">
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold tracking-tight">{project.name}</h1>
                <Badge variant="outline" className="text-xs font-mono">
                  {project.status}
                </Badge>
              </div>
              {project.description && (
                <p className="text-sm text-muted-foreground mt-1 max-w-2xl">{project.description}</p>
              )}
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <Select value={project.status} onValueChange={(v) => v && handleStatusChange(v)}>
                <SelectTrigger className="w-36 h-9 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PIPELINE_STAGES.map((stage) => (
                    <SelectItem key={stage} value={stage}>
                      {stage}
                    </SelectItem>
                  ))}
                  <SelectItem value="FAILED">FAILED</SelectItem>
                </SelectContent>
              </Select>

              <Button
                size="sm"
                variant="outline"
                className="gap-1.5 h-9"
                onClick={handleDownloadProject}
                disabled={downloading}
                title="Download complete project folder for VS Code"
              >
                {downloading ? (
                  <Loader2 className="h-4 w-4 animate-spin text-primary" />
                ) : (
                  <Download className="h-4 w-4 text-primary" />
                )}
                <span>Download ZIP</span>
              </Button>

              <Link href={`/workspace?projectId=${project.id}`}>
                <Button size="sm" variant="outline" className="gap-1.5 h-9">
                  Open IDE
                </Button>
              </Link>

              <Button
                size="sm"
                variant="default"
                className="gap-1.5 h-9"
                onClick={() => {
                  const prompt = encodeURIComponent(
                    `Let's work on project "${project.name}". Current status: ${project.status}. Description: ${project.description || "N/A"}. What are our next steps?`
                  );
                  router.push(`/chat?prompt=${prompt}`);
                }}
              >
                <MessageSquare className="h-4 w-4" />
                Discuss with DAI
              </Button>
            </div>
          </div>

          {/* Autonomous Pipeline Step Visualizer */}
          <div className="bg-card border rounded-xl p-4 space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Project Lifecycle Pipeline
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2">
              {PIPELINE_STAGES.map((stage, idx) => {
                const isPassed = currentStageIndex > idx;
                const isCurrent = currentStageIndex === idx;

                return (
                  <div
                    key={stage}
                    className={`flex items-center gap-2 p-2 rounded-lg border text-xs font-mono transition-colors ${
                      isCurrent
                        ? "bg-primary/10 border-primary text-primary font-semibold"
                        : isPassed
                        ? "bg-muted/40 border-muted text-muted-foreground"
                        : "opacity-40 border-dashed"
                    }`}
                  >
                    {isPassed ? (
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                    ) : isCurrent ? (
                      <Clock className="h-3.5 w-3.5 text-primary shrink-0 animate-pulse" />
                    ) : (
                      <Circle className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                    )}
                    <span className="truncate">{stage}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Workspace Tabs */}
          <Tabs defaultValue="tasks" className="w-full">
            <TabsList className="grid w-full grid-cols-3 max-w-md">
              <TabsTrigger value="tasks">Tasks ({project.tasks.length})</TabsTrigger>
              <TabsTrigger value="overview">Overview & Tech</TabsTrigger>
              <TabsTrigger value="activity">Activity Log</TabsTrigger>
            </TabsList>

            {/* Tasks Tab */}
            <TabsContent value="tasks" className="space-y-4 pt-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-semibold">Development Tasks</h3>
                  <p className="text-xs text-muted-foreground">
                    Actionable sub-tasks generated for this project.
                  </p>
                </div>

                <Dialog open={taskDialogOpen} onOpenChange={setTaskDialogOpen}>
                  <DialogTrigger render={<Button size="sm" className="gap-1.5" />}>
                    <Plus className="h-4 w-4" />
                    Add Task
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-[500px] max-h-[90vh] flex flex-col">
                    <DialogHeader className="shrink-0">
                      <DialogTitle>Add Project Task</DialogTitle>
                      <DialogDescription>Define a task item for DAI or yourself to execute.</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-3 py-2 overflow-y-auto flex-1 pr-1 max-h-[60vh]">
                      <div className="space-y-1">
                        <label className="text-xs font-medium">Task Title</label>
                        <Input
                          placeholder="e.g. Implement user registration API"
                          value={taskTitle}
                          onChange={(e) => setTaskTitle(e.target.value)}
                        />
                      </div>
                      <div className="space-y-1">
                        <label className="text-xs font-medium">Description</label>
                        <Textarea
                          placeholder="Acceptance criteria or implementation details..."
                          value={taskDesc}
                          onChange={(e) => setTaskDesc(e.target.value)}
                          rows={3}
                        />
                      </div>
                      <div className="space-y-1">
                        <label className="text-xs font-medium">Priority</label>
                        <Select
                          value={taskPriority}
                          onValueChange={(v) => v && setTaskPriority(v as TaskPriority)}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="LOW">Low</SelectItem>
                            <SelectItem value="MEDIUM">Medium</SelectItem>
                            <SelectItem value="HIGH">High</SelectItem>
                            <SelectItem value="CRITICAL">Critical</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setTaskDialogOpen(false)}>
                        Cancel
                      </Button>
                      <Button
                        onClick={handleCreateTask}
                        disabled={!taskTitle.trim() || taskSubmitting}
                      >
                        {taskSubmitting && <Loader2 className="h-4 w-4 animate-spin mr-1" />}
                        Save Task
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>

              {project.tasks.length === 0 ? (
                <div className="p-8 text-center border border-dashed rounded-xl bg-muted/20">
                  <p className="text-sm text-muted-foreground mb-3">No tasks created yet.</p>
                  <Button size="sm" variant="outline" onClick={() => setTaskDialogOpen(true)}>
                    <Plus className="h-4 w-4 mr-1" /> Add first task
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  {project.tasks.map((task) => (
                    <Card
                      key={task.id}
                      className={`transition-colors ${
                        task.status === "DONE" ? "bg-muted/30 opacity-75" : ""
                      }`}
                    >
                      <CardContent className="p-3.5 flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          <button
                            onClick={() => handleTaskStatusToggle(task.id, task.status)}
                            className="text-muted-foreground hover:text-primary transition-colors shrink-0"
                          >
                            {task.status === "DONE" ? (
                              <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                            ) : (
                              <Circle className="h-5 w-5" />
                            )}
                          </button>
                          <div className="min-w-0 flex-1">
                            <p
                              className={`text-sm font-medium line-clamp-1 ${
                                task.status === "DONE" ? "line-through text-muted-foreground" : ""
                              }`}
                            >
                              {task.title}
                            </p>
                            {task.description && (
                              <p className="text-xs text-muted-foreground line-clamp-1 mt-0.5">
                                {task.description}
                              </p>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          <Badge
                            variant="outline"
                            className={`text-[10px] font-mono border ${
                              PRIORITY_BADGES[task.priority] || PRIORITY_BADGES.MEDIUM
                            }`}
                          >
                            {task.priority}
                          </Badge>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7 text-muted-foreground hover:text-destructive"
                            onClick={() => handleDeleteTask(task.id)}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-4 pt-3">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Tech Stack & Infrastructure</CardTitle>
                  <CardDescription>Configured libraries, frameworks, and architecture tags.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {tags.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {tags.map((tag, idx) => (
                        <Badge key={idx} variant="secondary" className="px-2.5 py-1 text-xs font-mono">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No specific tech stack defined.</p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Activity Tab */}
            <TabsContent value="activity" className="space-y-3 pt-3">
              {project.recent_activities.length === 0 ? (
                <p className="text-sm text-muted-foreground p-4 text-center">No activity recorded yet.</p>
              ) : (
                project.recent_activities.map((act) => (
                  <Card key={act.id}>
                    <CardContent className="p-3.5 flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2.5">
                        <Activity className="h-4 w-4 text-primary" />
                        <div>
                          <p className="font-medium">{act.title}</p>
                          {act.description && (
                            <p className="text-muted-foreground mt-0.5">{act.description}</p>
                          )}
                        </div>
                      </div>
                      <span className="text-muted-foreground font-mono">
                        {new Date(act.created_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </CardContent>
                  </Card>
                ))
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </>
  );
}

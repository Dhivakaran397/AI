"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import Link from "next/link";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { apiClient } from "@/lib/api-client";
import { CheckSquare, CheckCircle2, Circle, Trash2, Loader2, ArrowUpRight, FolderKanban, Plus } from "lucide-react";
import { toast } from "sonner";
import type { Task, TaskPriority, TaskStatus, Project } from "@/types/project";

const PRIORITY_BADGES: Record<TaskPriority, string> = {
  LOW: "bg-zinc-500/10 text-zinc-500 border-zinc-500/20",
  MEDIUM: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  HIGH: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  CRITICAL: "bg-rose-500/10 text-rose-500 border-rose-500/20",
};

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Create Task State
  const [createOpen, setCreateOpen] = useState(false);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [taskTitle, setTaskTitle] = useState("");
  const [taskDesc, setTaskDesc] = useState("");
  const [taskPriority, setTaskPriority] = useState<TaskPriority>("MEDIUM");
  const [submitting, setSubmitting] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [tasksData, projectsData] = await Promise.all([
        apiClient.get<Task[]>("/tasks").catch(() => []),
        apiClient.get<Project[]>("/projects").catch(() => []),
      ]);
      setTasks(tasksData || []);
      setProjects(projectsData || []);
      if (projectsData && projectsData.length > 0 && !selectedProjectId) {
        setSelectedProjectId(projectsData[0].id);
      }
    } catch {
      toast.error("Failed to load tasks");
    } finally {
      setLoading(false);
    }
  }, [selectedProjectId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreateTask = async () => {
    if (!taskTitle.trim() || !selectedProjectId) {
      toast.error("Task title and project are required");
      return;
    }
    try {
      setSubmitting(true);
      const newTask = await apiClient.post<Task>("/tasks", {
        project_id: selectedProjectId,
        title: taskTitle.trim(),
        description: taskDesc.trim() || null,
        priority: taskPriority,
      });
      setTasks([newTask, ...tasks]);
      setTaskTitle("");
      setTaskDesc("");
      setCreateOpen(false);
      toast.success("Task created successfully!");
    } catch {
      toast.error("Failed to create task");
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleStatus = async (taskId: string, currentStatus: TaskStatus) => {
    const nextStatus: TaskStatus = currentStatus === "DONE" ? "TODO" : "DONE";
    try {
      await apiClient.patch<Task>(`/tasks/${taskId}`, { status: nextStatus });
      setTasks(tasks.map((t) => (t.id === taskId ? { ...t, status: nextStatus } : t)));
      toast.success(nextStatus === "DONE" ? "Task marked as complete" : "Task moved to To Do");
    } catch {
      toast.error("Failed to update task");
    }
  };

  const handleDelete = async (taskId: string) => {
    try {
      await apiClient.delete(`/tasks/${taskId}`);
      setTasks(tasks.filter((t) => t.id !== taskId));
      toast.success("Task deleted");
    } catch {
      toast.error("Failed to delete task");
    }
  };

  const filteredTasks = useMemo(() => {
    if (statusFilter === "ALL") return tasks;
    return tasks.filter((t) => t.status === statusFilter);
  }, [tasks, statusFilter]);

  return (
    <>
      <Header title="Tasks" />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-5xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                <CheckSquare className="h-6 w-6 text-primary" />
                Tasks Board
              </h1>
              <p className="text-muted-foreground mt-1 text-sm">
                Track and execute autonomous tasks across all active software projects.
              </p>
            </div>
            <Button
              size="sm"
              onClick={() => setCreateOpen(true)}
              className="bg-indigo-600 hover:bg-indigo-700 text-white shrink-0"
            >
              <Plus className="mr-1.5 h-4 w-4" /> Create Task
            </Button>
          </div>

          {/* Filter Tabs */}
          <Tabs value={statusFilter} onValueChange={setStatusFilter} className="w-full">
            <TabsList className="grid w-full grid-cols-5 max-w-lg">
              <TabsTrigger value="ALL">All ({tasks.length})</TabsTrigger>
              <TabsTrigger value="TODO">To Do</TabsTrigger>
              <TabsTrigger value="IN_PROGRESS">In Progress</TabsTrigger>
              <TabsTrigger value="DONE">Done</TabsTrigger>
              <TabsTrigger value="BLOCKED">Blocked</TabsTrigger>
            </TabsList>
          </Tabs>

          {/* Tasks List */}
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : filteredTasks.length === 0 ? (
            <div className="p-12 text-center border border-dashed rounded-xl bg-muted/20 space-y-2">
              <CheckSquare className="h-8 w-8 text-muted-foreground mx-auto" />
              <p className="text-sm font-semibold">No tasks found</p>
              <p className="text-xs text-muted-foreground">
                Tasks created within your project workspaces will appear here.
              </p>
            </div>
          ) : (
            <div className="space-y-2.5">
              {filteredTasks.map((task) => (
                <Card
                  key={task.id}
                  className={`transition-colors hover:shadow-xs ${
                    task.status === "DONE" ? "bg-muted/30 opacity-75" : ""
                  }`}
                >
                  <CardContent className="p-4 flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3.5 flex-1 min-w-0">
                      <button
                        onClick={() => handleToggleStatus(task.id, task.status)}
                        className="text-muted-foreground hover:text-primary transition-colors shrink-0"
                        title={task.status === "DONE" ? "Mark incomplete" : "Mark complete"}
                      >
                        {task.status === "DONE" ? (
                          <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                        ) : (
                          <Circle className="h-5 w-5" />
                        )}
                      </button>

                      <div className="min-w-0 flex-1 space-y-0.5">
                        <p
                          className={`text-sm font-medium line-clamp-1 ${
                            task.status === "DONE" ? "line-through text-muted-foreground" : ""
                          }`}
                        >
                          {task.title}
                        </p>
                        {task.description && (
                          <p className="text-xs text-muted-foreground line-clamp-1">
                            {task.description}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2.5 shrink-0">
                      <Badge
                        variant="outline"
                        className={`text-[10px] font-mono border ${
                          PRIORITY_BADGES[task.priority] || PRIORITY_BADGES.MEDIUM
                        }`}
                      >
                        {task.priority}
                      </Badge>

                      <Link href={`/projects/${task.project_id}`} title="Go to Project">
                        <Button variant="ghost" size="icon" className="h-7 w-7">
                          <ArrowUpRight className="h-3.5 w-3.5 text-muted-foreground" />
                        </Button>
                      </Link>

                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-muted-foreground hover:text-destructive"
                        onClick={() => handleDelete(task.id)}
                        title="Delete task"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Create Task Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Create Project Task</DialogTitle>
            <DialogDescription>
              Add a new actionable task, feature, or bug fix to a project workspace.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Target Project
              </label>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-xs shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Task Title
              </label>
              <Input
                value={taskTitle}
                onChange={(e) => setTaskTitle(e.target.value)}
                placeholder="e.g. Implement user profile settings"
                className="text-xs"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Description (Optional)
              </label>
              <Textarea
                rows={3}
                value={taskDesc}
                onChange={(e) => setTaskDesc(e.target.value)}
                placeholder="Details or acceptance criteria..."
                className="text-xs resize-none"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Priority
              </label>
              <select
                value={taskPriority}
                onChange={(e) => setTaskPriority(e.target.value as TaskPriority)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-xs shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
              >
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="CRITICAL">Critical</option>
              </select>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCreateOpen(false)}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleCreateTask}
              disabled={submitting || !taskTitle.trim()}
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              {submitting ? (
                <>
                  <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> Creating...
                </>
              ) : (
                "Create Task"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

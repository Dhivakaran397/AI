"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
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
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiClient } from "@/lib/api-client";
import { FolderKanban, Plus, Trash2, Loader2, ArrowRight, CheckCircle2, Clock, Download, Sparkles, Code2 } from "lucide-react";
import { toast } from "sonner";
import type { Project, ProjectStatus } from "@/types/project";

const STATUS_CONFIG: Record<ProjectStatus, { label: string; color: string }> = {
  IDEA: { label: "Idea", color: "bg-blue-500/10 text-blue-500 border-blue-500/20" },
  PLANNING: { label: "Planning", color: "bg-purple-500/10 text-purple-500 border-purple-500/20" },
  BUILDING: { label: "Building", color: "bg-amber-500/10 text-amber-500 border-amber-500/20" },
  TESTING: { label: "Testing", color: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20" },
  DEBUGGING: { label: "Debugging", color: "bg-orange-500/10 text-orange-500 border-orange-500/20" },
  REVIEW: { label: "Review", color: "bg-indigo-500/10 text-indigo-500 border-indigo-500/20" },
  COMPLETED: { label: "Completed", color: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" },
  FAILED: { label: "Failed", color: "bg-rose-500/10 text-rose-500 border-rose-500/20" },
};

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState("ALL");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [techStackInput, setTechStackInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const data = await apiClient.get<Project[]>("/projects");
      setProjects(data);
    } catch {
      toast.error("Failed to load projects");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreate = async () => {
    if (!name.trim()) return;
    try {
      setSubmitting(true);
      const techStack = techStackInput
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);

      const created = await apiClient.post<Project>("/projects", {
        name: name.trim(),
        description: description.trim() || null,
        tech_stack: techStack.length > 0 ? { tags: techStack } : null,
      });

      setProjects([created, ...projects]);
      setName("");
      setDescription("");
      setTechStackInput("");
      setDialogOpen(false);
      toast.success(`Project '${created.name}' initialized! Opening Agents Compiler...`);
      router.push(`/agents?projectId=${created.id}&autoOpen=true`);
    } catch {
      toast.error("Failed to create project");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string, projectName: string) => {
    try {
      await apiClient.delete(`/projects/${id}`);
      setProjects(projects.filter((p) => p.id !== id));
      toast.success(`Project '${projectName}' removed`);
    } catch {
      toast.error("Failed to delete project");
    }
  };

  const handleDownload = async (id: string, projectName: string) => {
    try {
      setDownloadingId(id);
      const safeName = `${projectName.toLowerCase().replace(/[^a-z0-9]/g, "_")}.zip`;
      await apiClient.downloadFile(`/projects/${id}/download`, safeName);
      toast.success(`Project '${projectName}' downloaded as ZIP`);
    } catch {
      toast.error(`Failed to download project '${projectName}'`);
    } finally {
      setDownloadingId(null);
    }
  };

  const filteredProjects = useMemo(() => {
    if (selectedStatus === "ALL") return projects;
    return projects.filter((p) => p.status === selectedStatus);
  }, [projects, selectedStatus]);

  return (
    <>
      <Header title="Projects" />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Top Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                <FolderKanban className="h-6 w-6 text-primary" />
                Project Workspaces
              </h1>
              <p className="text-muted-foreground mt-1 text-sm">
                Autonomous software projects tracked from conception to completed deployment.
              </p>
            </div>

            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger render={<Button className="gap-2 shrink-0" />}>
                <Plus className="h-4 w-4" />
                New Project
              </DialogTrigger>
              <DialogContent className="sm:max-w-[550px] max-h-[90vh] flex flex-col">
                <DialogHeader className="shrink-0">
                  <DialogTitle>Create New Project</DialogTitle>
                  <DialogDescription>
                    Describe your software idea. DAI will initialize the project state machine and generate initial tasks.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-3 overflow-y-auto flex-1 pr-1 max-h-[60vh]">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Project Name</label>
                    <Input
                      placeholder="e.g. AI Documentation Generator"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Description & Scope</label>
                    <Textarea
                      placeholder="What should this project build? Target features, requirements, or architecture..."
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      rows={5}
                      className="max-h-[220px] overflow-y-auto"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Tech Stack (comma separated)</label>
                    <Input
                      placeholder="e.g. Next.js, FastAPI, PostgreSQL, Tailwind"
                      value={techStackInput}
                      onChange={(e) => setTechStackInput(e.target.value)}
                    />
                  </div>
                </div>
                <DialogFooter className="pt-3 border-t mt-auto shrink-0 flex items-center justify-end gap-2">
                  <Button variant="outline" onClick={() => setDialogOpen(false)} disabled={submitting}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreate} disabled={!name.trim() || submitting} className="gap-2">
                    {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
                    Initialize Project
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {/* Filter Tabs */}
          <Tabs value={selectedStatus} onValueChange={setSelectedStatus} className="w-full">
            <TabsList className="grid w-full grid-cols-6 max-w-2xl">
              <TabsTrigger value="ALL">All ({projects.length})</TabsTrigger>
              <TabsTrigger value="IDEA">Idea</TabsTrigger>
              <TabsTrigger value="PLANNING">Planning</TabsTrigger>
              <TabsTrigger value="BUILDING">Building</TabsTrigger>
              <TabsTrigger value="REVIEW">Review</TabsTrigger>
              <TabsTrigger value="COMPLETED">Completed</TabsTrigger>
            </TabsList>
          </Tabs>

          {/* Project Grid */}
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : filteredProjects.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center border border-dashed rounded-xl bg-muted/20">
              <FolderKanban className="h-10 w-10 text-muted-foreground mb-3" />
              <h3 className="text-base font-semibold">No projects found</h3>
              <p className="text-sm text-muted-foreground max-w-sm mt-1 mb-4">
                {selectedStatus === "ALL"
                  ? "Start by creating your first autonomous project workspace."
                  : `No projects currently in ${selectedStatus.toLowerCase()} status.`}
              </p>
              <Button variant="outline" size="sm" className="gap-2" onClick={() => setDialogOpen(true)}>
                <Plus className="h-4 w-4" />
                New Project
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredProjects.map((project) => {
                const statusInfo = STATUS_CONFIG[project.status] || STATUS_CONFIG.IDEA;
                const progressPct =
                  project.task_count > 0
                    ? Math.round((project.completed_task_count / project.task_count) * 100)
                    : 0;

                const tags = (project.tech_stack?.tags as string[]) || [];

                return (
                  <Card
                    key={project.id}
                    className="flex flex-col justify-between hover:shadow-md transition-shadow group relative overflow-hidden"
                  >
                    <CardContent className="p-5 space-y-3 flex-1 flex flex-col justify-between">
                      <div className="space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <h3 className="font-semibold text-base group-hover:text-primary transition-colors line-clamp-1">
                            {project.name}
                          </h3>
                          <Badge variant="outline" className={`text-[10px] font-mono border ${statusInfo.color}`}>
                            {statusInfo.label}
                          </Badge>
                        </div>

                        {project.description && (
                          <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                            {project.description}
                          </p>
                        )}

                        {tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 pt-1">
                            {tags.slice(0, 3).map((tag, idx) => (
                              <span
                                key={idx}
                                className="text-[10px] px-1.5 py-0.5 bg-muted rounded font-mono text-muted-foreground"
                              >
                                {tag}
                              </span>
                            ))}
                            {tags.length > 3 && (
                              <span className="text-[10px] px-1 bg-muted rounded text-muted-foreground">
                                +{tags.length - 3}
                              </span>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Progress & Footer */}
                      <div className="space-y-3 pt-3 border-t border-border/50">
                        <div className="space-y-1">
                          <div className="flex justify-between text-[11px] text-muted-foreground font-mono">
                            <span>Tasks Progress</span>
                            <span>
                              {project.completed_task_count} / {project.task_count} ({progressPct}%)
                            </span>
                          </div>
                          <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                            <div
                              className="h-full bg-primary transition-all duration-300 rounded-full"
                              style={{ width: `${progressPct}%` }}
                            />
                          </div>
                        </div>

                        <div className="flex items-center justify-between pt-1 text-xs">
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 text-muted-foreground hover:text-foreground"
                              onClick={(e) => {
                                e.preventDefault();
                                handleDownload(project.id, project.name);
                              }}
                              disabled={downloadingId === project.id}
                              title="Download project ZIP for VS Code"
                            >
                              {downloadingId === project.id ? (
                                <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
                              ) : (
                                <Download className="h-3.5 w-3.5" />
                              )}
                            </Button>

                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 text-muted-foreground hover:text-destructive"
                              onClick={(e) => {
                                e.preventDefault();
                                handleDelete(project.id, project.name);
                              }}
                              title="Delete project"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </div>

                          <div className="flex items-center gap-1.5">
                            <Link href={`/agents?projectId=${project.id}&autoOpen=true`}>
                              <Button
                                size="sm"
                                variant="default"
                                className="gap-1 h-7 text-xs bg-indigo-600 hover:bg-indigo-700 text-white font-medium px-2.5"
                                title="Run Autonomous AI Agents to compile code"
                              >
                                <Sparkles className="h-3 w-3" />
                                <span>Compile</span>
                              </Button>
                            </Link>

                            <Link href={`/workspace?projectId=${project.id}`}>
                              <Button
                                size="sm"
                                variant="outline"
                                className="gap-1 h-7 text-xs px-2.5"
                                title="Open Workspace IDE and Live Preview"
                              >
                                <Code2 className="h-3 w-3" />
                                <span>Workspace</span>
                              </Button>
                            </Link>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

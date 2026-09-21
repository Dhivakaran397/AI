"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api-client";
import { FolderKanban, ArrowRight } from "lucide-react";
import type { Project } from "@/types/project";

export function RecentProjects() {
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    apiClient
      .get<Project[]>("/projects")
      .then((data) => setProjects(data.slice(0, 3)))
      .catch(() => {});
  }, []);

  return (
    <Card>
      <CardHeader className="pb-3 flex flex-row items-center justify-between">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <FolderKanban className="h-4 w-4" />
          Recent Projects
        </CardTitle>
        <Link href="/projects" className="text-xs text-muted-foreground hover:text-primary transition-colors flex items-center gap-1">
          View all <ArrowRight className="h-3 w-3" />
        </Link>
      </CardHeader>
      <CardContent>
        {projects.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No projects yet. Create your first project to get started.
          </p>
        ) : (
          <div className="space-y-2">
            {projects.map((p) => (
              <Link
                key={p.id}
                href={`/projects/${p.id}`}
                className="flex items-center justify-between p-2 rounded-lg hover:bg-muted/50 transition-colors border border-transparent hover:border-border/50 text-xs"
              >
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-foreground truncate">{p.name}</p>
                  <p className="text-[11px] text-muted-foreground">
                    {p.completed_task_count} / {p.task_count} tasks done
                  </p>
                </div>
                <Badge variant="outline" className="text-[10px] font-mono shrink-0 ml-2">
                  {p.status}
                </Badge>
              </Link>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

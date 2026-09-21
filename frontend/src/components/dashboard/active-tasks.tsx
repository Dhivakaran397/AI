"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api-client";
import { CheckSquare, ArrowRight } from "lucide-react";
import type { Task } from "@/types/project";

export function ActiveTasks() {
  const [tasks, setTasks] = useState<Task[]>([]);

  useEffect(() => {
    apiClient
      .get<Task[]>("/tasks?status=TODO")
      .then((data) => setTasks(data.slice(0, 3)))
      .catch(() => {});
  }, []);

  return (
    <Card>
      <CardHeader className="pb-3 flex flex-row items-center justify-between">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <CheckSquare className="h-4 w-4" />
          Active Tasks
        </CardTitle>
        <Link href="/tasks" className="text-xs text-muted-foreground hover:text-primary transition-colors flex items-center gap-1">
          View all <ArrowRight className="h-3 w-3" />
        </Link>
      </CardHeader>
      <CardContent>
        {tasks.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No active tasks. Tasks will appear here when created in projects.
          </p>
        ) : (
          <div className="space-y-2">
            {tasks.map((t) => (
              <div
                key={t.id}
                className="flex items-center justify-between p-2 rounded-lg bg-muted/30 text-xs"
              >
                <p className="font-medium text-foreground truncate flex-1 min-w-0 pr-2">
                  {t.title}
                </p>
                <Badge variant="outline" className="text-[10px] font-mono shrink-0">
                  {t.priority}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

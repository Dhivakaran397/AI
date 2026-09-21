"use client";

import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/layout/header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import {
  Activity as ActivityIcon,
  Zap,
  MessageSquare,
  FolderKanban,
  CheckSquare,
  FileCode,
  Sparkles,
  Wrench,
  Loader2,
  RefreshCw,
  Clock,
  Layers,
} from "lucide-react";

interface ActivityItem {
  id: string;
  type: string;
  title: string;
  description?: string;
  project_id?: string;
  created_at?: string;
  metadata_?: Record<string, any>;
}

const typeIcons: Record<string, any> = {
  PROJECT_CREATED: FolderKanban,
  PROJECT_UPDATED: FolderKanban,
  TASK_CREATED: CheckSquare,
  TASK_COMPLETED: CheckSquare,
  DOCUMENT_INGESTED: Layers,
  FILE_CREATED: FileCode,
  FILE_UPDATED: FileCode,
  AGENT_RUN: Sparkles,
  TEST_RUN: Wrench,
  SELF_HEAL: Wrench,
  system: Zap,
  info: MessageSquare,
};

export default function ActivityPage() {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("ALL");

  const fetchActivities = useCallback(async () => {
    setLoading(true);
    try {
      const endpoint = filter === "ALL" ? "/api/v1/activities" : `/api/v1/activities?type=${filter}`;
      const data = await apiClient.get<ActivityItem[]>(endpoint);
      setActivities(data || []);
    } catch (err) {
      console.error("Failed to load activity stream:", err);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchActivities();
  }, [fetchActivities]);

  const filterTabs = [
    { label: "All Activity", value: "ALL" },
    { label: "Documents & RAG", value: "DOCUMENT_INGESTED" },
    { label: "Projects", value: "PROJECT_CREATED" },
    { label: "Tasks", value: "TASK_CREATED" },
  ];

  return (
    <>
      <Header title="Activity Stream" />
      <div className="flex-1 overflow-auto p-6 space-y-6">
        {/* Top Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-tight">System & Project Audit Stream</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Chronological ledger of project state changes, task updates, knowledge ingestion, and agent runs.
            </p>
          </div>

          <Button
            size="sm"
            variant="outline"
            onClick={fetchActivities}
            disabled={loading}
            className="text-xs"
          >
            <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh Log
          </Button>
        </div>

        {/* Filter Chips */}
        <div className="flex flex-wrap items-center gap-2">
          {filterTabs.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setFilter(tab.value)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                filter === tab.value
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:text-foreground"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Timeline Feed */}
        <div className="space-y-3">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : activities.length === 0 ? (
            <Card className="p-8 text-center text-xs text-muted-foreground">
              No activity records found matching the current filter.
            </Card>
          ) : (
            activities.map((act) => {
              const IconComp = typeIcons[act.type] || ActivityIcon;
              return (
                <Card key={act.id} className="transition-all hover:bg-muted/10">
                  <CardContent className="flex items-start justify-between gap-3 p-4">
                    <div className="flex items-start gap-3 min-w-0">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted text-primary">
                        <IconComp className="h-4 w-4" />
                      </div>
                      <div className="min-w-0 space-y-0.5">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-semibold text-foreground truncate">
                            {act.title}
                          </p>
                          <Badge variant="outline" className="text-[10px] font-mono">
                            {act.type}
                          </Badge>
                        </div>
                        {act.description && (
                          <p className="text-xs text-muted-foreground leading-relaxed">
                            {act.description}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0 text-xs text-muted-foreground font-mono">
                      <Clock className="h-3 w-3" />
                      <span>
                        {act.created_at ? new Date(act.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "Just now"}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              );
            })
          )}
        </div>
      </div>
    </>
  );
}

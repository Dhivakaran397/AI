"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/api-client";
import { Activity as ActivityIcon, ArrowRight } from "lucide-react";
import type { Activity } from "@/types/api";

export function ActivityFeed() {
  const [activities, setActivities] = useState<Activity[]>([]);

  useEffect(() => {
    apiClient
      .get<Activity[]>("/activities")
      .then((data) => setActivities(data.slice(0, 3)))
      .catch(() => {});
  }, []);

  return (
    <Card>
      <CardHeader className="pb-3 flex flex-row items-center justify-between">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <ActivityIcon className="h-4 w-4" />
          AI Activity
        </CardTitle>
        <Link href="/activity" className="text-xs text-muted-foreground hover:text-primary transition-colors flex items-center gap-1">
          View all <ArrowRight className="h-3 w-3" />
        </Link>
      </CardHeader>
      <CardContent>
        {activities.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No activity yet. DAI&apos;s actions will be logged here.
          </p>
        ) : (
          <div className="space-y-2">
            {activities.map((a) => (
              <div key={a.id} className="flex items-center justify-between p-2 rounded-lg bg-muted/30 text-xs">
                <div className="min-w-0 flex-1 pr-2">
                  <p className="font-medium text-foreground truncate">{a.title}</p>
                  {a.description && (
                    <p className="text-[11px] text-muted-foreground truncate">{a.description}</p>
                  )}
                </div>
                <span className="text-[10px] text-muted-foreground shrink-0 font-mono">
                  {new Date(a.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

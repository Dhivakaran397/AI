"use client";

import { Header } from "@/components/layout/header";
import { Greeting } from "@/components/dashboard/greeting";
import { AIInput } from "@/components/dashboard/ai-input";
import { QuickPrompts } from "@/components/dashboard/quick-prompts";
import { RecentProjects } from "@/components/dashboard/recent-projects";
import { RecentChats } from "@/components/dashboard/recent-chats";
import { ActiveTasks } from "@/components/dashboard/active-tasks";
import { ActivityFeed } from "@/components/dashboard/activity-feed";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();

  return (
    <>
      <Header title="Home" />
      <div className="flex-1 overflow-auto">
        <div className="max-w-5xl mx-auto p-6 space-y-8">
          {/* Greeting & CTA */}
          <div className="flex items-start justify-between">
            <Greeting />
            <Button
              onClick={() => router.push("/projects")}
              className="gap-2"
            >
              <Plus className="h-4 w-4" />
              New Project
            </Button>
          </div>

          {/* Main AI Input */}
          <AIInput />

          {/* Quick Prompts */}
          <QuickPrompts />

          {/* Dashboard Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <RecentProjects />
            <RecentChats />
            <ActiveTasks />
            <ActivityFeed />
          </div>
        </div>
      </div>
    </>
  );
}

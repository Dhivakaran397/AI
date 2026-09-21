"use client";

import { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Agent } from "@/types";
import {
  Crown,
  Boxes,
  Search,
  Code2,
  CheckCircle2,
  Bug,
  ShieldCheck,
  FileText,
  Bot,
  Play,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

interface AgentCardProps {
  agent: Agent;
  onDispatch?: (agent: Agent) => void;
}

const iconMap: Record<string, any> = {
  Crown,
  Boxes,
  Search,
  Code2,
  CheckCircle: CheckCircle2,
  Bug,
  ShieldCheck,
  FileText,
};

const colorClasses: Record<string, { bg: string; text: string; border: string }> = {
  indigo: { bg: "bg-indigo-500/10 dark:bg-indigo-500/20", text: "text-indigo-600 dark:text-indigo-400", border: "border-indigo-500/30" },
  blue: { bg: "bg-blue-500/10 dark:bg-blue-500/20", text: "text-blue-600 dark:text-blue-400", border: "border-blue-500/30" },
  cyan: { bg: "bg-cyan-500/10 dark:bg-cyan-500/20", text: "text-cyan-600 dark:text-cyan-400", border: "border-cyan-500/30" },
  emerald: { bg: "bg-emerald-500/10 dark:bg-emerald-500/20", text: "text-emerald-600 dark:text-emerald-400", border: "border-emerald-500/30" },
  amber: { bg: "bg-amber-500/10 dark:bg-amber-500/20", text: "text-amber-600 dark:text-amber-400", border: "border-amber-500/30" },
  rose: { bg: "bg-rose-500/10 dark:bg-rose-500/20", text: "text-rose-600 dark:text-rose-400", border: "border-rose-500/30" },
  purple: { bg: "bg-purple-500/10 dark:bg-purple-500/20", text: "text-purple-600 dark:text-purple-400", border: "border-purple-500/30" },
  teal: { bg: "bg-teal-500/10 dark:bg-teal-500/20", text: "text-teal-600 dark:text-teal-400", border: "border-teal-500/30" },
};

export function AgentCard({ agent, onDispatch }: AgentCardProps) {
  const [showPrompt, setShowPrompt] = useState(false);
  const IconComponent = agent.icon && iconMap[agent.icon] ? iconMap[agent.icon] : Bot;
  const theme = (agent.color && colorClasses[agent.color]) || {
    bg: "bg-muted",
    text: "text-foreground",
    border: "border-border",
  };

  const capabilityKeys = Object.entries(agent.capabilities || {})
    .filter(([_, active]) => Boolean(active))
    .map(([key]) => key.replace(/_/g, " "));

  return (
    <Card className={`relative flex flex-col justify-between transition-all hover:shadow-md border ${theme.border}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-3">
            <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${theme.bg} ${theme.text}`}>
              <IconComponent className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-base font-semibold">{agent.name}</CardTitle>
              <Badge variant="outline" className="mt-0.5 text-xs font-mono">
                {agent.type}
              </Badge>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <span
              className={`h-2 w-2 rounded-full ${
                agent.is_active ? "bg-emerald-500 animate-pulse" : "bg-muted-foreground"
              }`}
            />
            <span className="text-[11px] text-muted-foreground">
              {agent.is_active ? "Ready" : "Inactive"}
            </span>
          </div>
        </div>
        <CardDescription className="pt-2 text-xs leading-relaxed line-clamp-2">
          {agent.description}
        </CardDescription>
      </CardHeader>

      <CardContent className="flex-1 space-y-3 pb-3">
        <div className="flex flex-wrap gap-1">
          {capabilityKeys.slice(0, 4).map((cap) => (
            <span
              key={cap}
              className="rounded-md bg-muted/60 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground"
            >
              {cap}
            </span>
          ))}
          {capabilityKeys.length > 4 && (
            <span className="rounded-md bg-muted/30 px-1.5 py-0.5 text-[10px] text-muted-foreground">
              +{capabilityKeys.length - 4} more
            </span>
          )}
        </div>

        {showPrompt && (
          <div className="rounded-lg bg-muted/40 p-2.5 text-xs text-muted-foreground font-mono leading-relaxed border border-border/50">
            {agent.system_prompt}
          </div>
        )}
      </CardContent>

      <CardFooter className="flex items-center justify-between pt-0 border-t border-border/40 py-2.5">
        <Button
          variant="ghost"
          size="sm"
          className="h-7 px-2 text-xs text-muted-foreground hover:text-foreground"
          onClick={() => setShowPrompt(!showPrompt)}
        >
          {showPrompt ? (
            <>
              Hide Prompt <ChevronUp className="ml-1 h-3.5 w-3.5" />
            </>
          ) : (
            <>
              View Prompt <ChevronDown className="ml-1 h-3.5 w-3.5" />
            </>
          )}
        </Button>

        {onDispatch && (
          <Button
            size="sm"
            className="h-7 text-xs"
            onClick={() => onDispatch(agent)}
          >
            <Play className="mr-1 h-3 w-3" /> Dispatch
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}

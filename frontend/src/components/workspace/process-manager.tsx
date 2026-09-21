"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { apiClient } from "@/lib/api-client";
import type { ProcessInfo, ProcessLogResponse } from "@/types";
import {
  Activity,
  Play,
  Square,
  FileText,
  RefreshCw,
  Loader2,
  AlertCircle,
  Plus,
} from "lucide-react";

interface ProcessManagerProps {
  projectId: string;
  projectName?: string;
}

export function ProcessManager({ projectId, projectName }: ProcessManagerProps) {
  const [processes, setProcesses] = useState<ProcessInfo[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isStarting, setIsStarting] = useState<boolean>(false);
  const [newCommand, setNewCommand] = useState<string>("");
  const [newPort, setNewPort] = useState<string>("");

  // Logs dialog
  const [logsOpen, setLogsOpen] = useState<boolean>(false);
  const [selectedProcess, setSelectedProcess] = useState<ProcessInfo | null>(null);
  const [logs, setLogs] = useState<{ line: string; stream: string; timestamp: string }[]>([]);
  const [loadingLogs, setLoadingLogs] = useState<boolean>(false);

  const fetchProcesses = useCallback(async () => {
    try {
      const res = await apiClient.get<ProcessInfo[]>(
        `/projects/${projectId}/processes`
      );
      setProcesses(res);
    } catch (err) {
      console.error("Failed to load processes:", err);
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchProcesses();
    const interval = setInterval(fetchProcesses, 4000);
    return () => clearInterval(interval);
  }, [fetchProcesses]);

  const handleStartProcess = async () => {
    if (!newCommand.trim()) return;
    try {
      setIsStarting(true);
      await apiClient.post<ProcessInfo>(`/projects/${projectId}/processes`, {
        command: newCommand.trim(),
        port: newPort ? parseInt(newPort, 10) : undefined,
      });
      setNewCommand("");
      setNewPort("");
      await fetchProcesses();
    } catch (err) {
      console.error("Failed to start process:", err);
    } finally {
      setIsStarting(false);
    }
  };

  const handleStopProcess = async (processId: string) => {
    try {
      await apiClient.post(`/projects/${projectId}/processes/${processId}/stop`, {});
      await fetchProcesses();
    } catch (err) {
      console.error("Failed to stop process:", err);
    }
  };

  const handleViewLogs = async (proc: ProcessInfo) => {
    setSelectedProcess(proc);
    setLogsOpen(true);
    try {
      setLoadingLogs(true);
      const res = await apiClient.get<ProcessLogResponse>(
        `/projects/${projectId}/processes/${proc.process_id}/logs?limit=150`
      );
      setLogs(res.logs);
    } catch (err) {
      console.error("Failed to load logs:", err);
      setLogs([]);
    } finally {
      setLoadingLogs(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-background border-r border-border overflow-hidden">
      {/* Header Bar */}
      <div className="flex items-center justify-between px-3 py-2 border-b bg-muted/30 shrink-0">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-primary" />
          <span className="font-semibold text-xs text-foreground">
            Background Processes: {projectName || "project"}
          </span>
          <Badge variant="outline" className="text-[10px] px-1.5 py-0 font-mono">
            {processes.filter((p) => p.status === "RUNNING").length} Active
          </Badge>
        </div>

        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-muted-foreground hover:text-foreground"
          onClick={() => fetchProcesses()}
          title="Refresh processes"
        >
          <RefreshCw className="h-3.5 w-3.5" />
        </Button>
      </div>

      {/* Start New Process Input Bar */}
      <div className="p-3 border-b bg-muted/10 shrink-0">
        <div className="flex items-center gap-2">
          <Input
            placeholder="Command (e.g. npm run dev, python -m http.server 8000)..."
            value={newCommand}
            onChange={(e) => setNewCommand(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleStartProcess();
            }}
            className="text-xs h-8 font-mono flex-1"
          />
          <Input
            placeholder="Port (optional)"
            value={newPort}
            onChange={(e) => setNewPort(e.target.value)}
            type="number"
            className="text-xs h-8 font-mono w-24"
          />
          <Button
            size="sm"
            className="h-8 text-xs gap-1.5"
            onClick={handleStartProcess}
            disabled={isStarting || !newCommand.trim()}
          >
            {isStarting ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Play className="h-3.5 w-3.5" />
            )}
            Launch
          </Button>
        </div>
      </div>

      {/* Process List */}
      <div className="flex-1 overflow-auto p-3 space-y-2">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center p-8 gap-2 text-muted-foreground">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <span className="text-xs">Loading active processes...</span>
          </div>
        ) : processes.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-8 text-center text-muted-foreground gap-2">
            <Activity className="h-8 w-8 text-muted-foreground/40" />
            <span className="text-xs">No background processes running.</span>
            <span className="text-[11px]">
              Use the launcher above to start dev servers or background workers.
            </span>
          </div>
        ) : (
          processes.map((proc) => (
            <div
              key={proc.process_id}
              className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-muted/30 transition-colors"
            >
              <div className="min-w-0 space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-semibold text-foreground truncate">
                    {proc.command}
                  </span>
                  <Badge
                    variant={proc.status === "RUNNING" ? "default" : "secondary"}
                    className={`text-[10px] uppercase font-mono px-1.5 py-0 ${
                      proc.status === "RUNNING"
                        ? "bg-emerald-500/15 text-emerald-500 hover:bg-emerald-500/20"
                        : "text-muted-foreground"
                    }`}
                  >
                    {proc.status}
                  </Badge>
                  {proc.port && (
                    <Badge variant="outline" className="text-[10px] font-mono px-1.5 py-0 text-primary">
                      Port {proc.port}
                    </Badge>
                  )}
                </div>

                <div className="flex items-center gap-3 text-[11px] text-muted-foreground font-mono">
                  <span>PID: {proc.pid ?? "N/A"}</span>
                  <span>Logs: {proc.logs_count} lines</span>
                  <span>Started: {new Date(proc.started_at).toLocaleTimeString()}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 text-xs gap-1"
                  onClick={() => handleViewLogs(proc)}
                >
                  <FileText className="h-3 w-3" />
                  Logs
                </Button>

                {proc.status === "RUNNING" && (
                  <Button
                    variant="destructive"
                    size="sm"
                    className="h-7 text-xs gap-1"
                    onClick={() => handleStopProcess(proc.process_id)}
                  >
                    <Square className="h-3 w-3" />
                    Stop
                  </Button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Process Logs Dialog */}
      <Dialog open={logsOpen} onOpenChange={setLogsOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[80vh] flex flex-col bg-[#0d1117] text-[#c9d1d9] border-[#30363d]">
          <DialogHeader>
            <DialogTitle className="text-sm font-mono text-[#f0f6fc]">
              Process Logs: {selectedProcess?.command}
            </DialogTitle>
            <DialogDescription className="text-xs text-[#8b949e] font-mono">
              PID {selectedProcess?.pid ?? "N/A"} • Status: {selectedProcess?.status}
            </DialogDescription>
          </DialogHeader>

          <div className="flex-1 overflow-auto max-h-[450px] p-3 rounded bg-black/40 border border-[#30363d] font-mono text-xs space-y-1">
            {loadingLogs ? (
              <div className="p-8 text-center text-[#8b949e] flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                <span>Loading output stream...</span>
              </div>
            ) : logs.length === 0 ? (
              <div className="p-8 text-center text-[#8b949e]">
                No logs recorded yet for this process.
              </div>
            ) : (
              logs.map((log, idx) => (
                <div
                  key={idx}
                  className={`leading-relaxed whitespace-pre-wrap break-all ${
                    log.stream === "stderr" ? "text-[#ff7b72]" : "text-[#c9d1d9]"
                  }`}
                >
                  <span className="text-[#8b949e] mr-2 select-none text-[10px]">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                  {log.line}
                </div>
              ))
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

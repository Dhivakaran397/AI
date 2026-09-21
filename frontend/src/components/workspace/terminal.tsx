"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api-client";
import type { CommandExecutionResponse } from "@/types";
import {
  Terminal as TerminalIcon,
  Play,
  Trash2,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  CornerDownLeft,
} from "lucide-react";

interface TerminalProps {
  projectId: string;
  projectName?: string;
}

interface CommandHistoryItem {
  id: string;
  command: string;
  response: CommandExecutionResponse | null;
  isRunning: boolean;
  timestamp: string;
}

const PRESET_COMMANDS = [
  "python src/main.py",
  "python -m http.server 3000",
  "pytest",
  "dir",
  "npm run dev",
];

export function Terminal({ projectId, projectName }: TerminalProps) {
  const [history, setHistory] = useState<CommandHistoryItem[]>([
    {
      id: "initial",
      command: "echo 'DAI Controlled Terminal initialized. Type a command or click a preset below.'",
      response: {
        command: "echo 'DAI Controlled Terminal initialized. Type a command or click a preset below.'",
        exit_code: 0,
        stdout: "DAI Controlled Terminal ready for project workspace.",
        stderr: "",
        duration_ms: 5,
        timed_out: false,
        status: "success",
      },
      isRunning: false,
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);
  const [inputCommand, setInputCommand] = useState("");
  const [isExecuting, setIsExecuting] = useState(false);
  const [historyIndex, setHistoryIndex] = useState<number | null>(null);
  const [sentCommands, setSentCommands] = useState<string[]>([]);

  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  const handleRunCommand = async (cmdToRun?: string) => {
    const cmd = (cmdToRun !== undefined ? cmdToRun : inputCommand).trim();
    if (!cmd || isExecuting) return;

    const itemId = Math.random().toString(36).substring(7);
    const now = new Date().toLocaleTimeString();

    // Add to history as running
    setHistory((prev) => [
      ...prev,
      {
        id: itemId,
        command: cmd,
        response: null,
        isRunning: true,
        timestamp: now,
      },
    ]);

    setSentCommands((prev) => [...prev, cmd]);
    setHistoryIndex(null);
    setInputCommand("");
    setIsExecuting(true);

    try {
      const res = await apiClient.post<CommandExecutionResponse>(
        `/projects/${projectId}/execute`,
        {
          command: cmd,
          timeout_seconds: 60,
        }
      );

      setHistory((prev) =>
        prev.map((item) =>
          item.id === itemId
            ? { ...item, isRunning: false, response: res }
            : item
        )
      );
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Failed to execute command";
      setHistory((prev) =>
        prev.map((item) =>
          item.id === itemId
            ? {
                ...item,
                isRunning: false,
                response: {
                  command: cmd,
                  exit_code: 1,
                  stdout: "",
                  stderr: errorMsg,
                  duration_ms: 0,
                  timed_out: false,
                  status: "failed",
                  error: errorMsg,
                },
              }
            : item
        )
      );
    } finally {
      setIsExecuting(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleRunCommand();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (sentCommands.length === 0) return;
      const nextIdx =
        historyIndex === null
          ? sentCommands.length - 1
          : Math.max(0, historyIndex - 1);
      setHistoryIndex(nextIdx);
      setInputCommand(sentCommands[nextIdx]);
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      if (historyIndex === null) return;
      const nextIdx = historyIndex + 1;
      if (nextIdx >= sentCommands.length) {
        setHistoryIndex(null);
        setInputCommand("");
      } else {
        setHistoryIndex(nextIdx);
        setInputCommand(sentCommands[nextIdx]);
      }
    }
  };

  const clearTerminal = () => {
    setHistory([]);
  };

  return (
    <div className="flex flex-col h-full bg-[#0d1117] text-[#c9d1d9] font-mono text-xs overflow-hidden">
      {/* Terminal Toolbar */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-[#161b22] border-b border-[#30363d] shrink-0">
        <div className="flex items-center gap-2">
          <TerminalIcon className="h-3.5 w-3.5 text-emerald-400" />
          <span className="font-semibold text-xs text-[#f0f6fc]">
            Terminal: {projectName || "project"}
          </span>
          <Badge
            variant="outline"
            className="text-[10px] px-1.5 py-0 border-[#30363d] text-muted-foreground"
          >
            Sandboxed
          </Badge>
        </div>

        <div className="flex items-center gap-1.5">
          <Button
            variant="ghost"
            size="sm"
            className="h-6 text-[11px] text-[#8b949e] hover:text-[#f0f6fc] hover:bg-[#21262d] gap-1 px-2"
            onClick={clearTerminal}
            title="Clear terminal buffer"
          >
            <Trash2 className="h-3 w-3" />
            Clear
          </Button>
        </div>
      </div>

      {/* Preset Command Quick Chips */}
      <div className="flex items-center gap-1.5 px-3 py-1.5 bg-[#161b22]/50 border-b border-[#30363d]/60 overflow-x-auto shrink-0 scrollbar-none">
        <span className="text-[10px] uppercase text-[#8b949e] font-semibold tracking-wider shrink-0">
          Presets:
        </span>
        {PRESET_COMMANDS.map((preset) => (
          <button
            key={preset}
            onClick={() => handleRunCommand(preset)}
            disabled={isExecuting}
            className="px-2 py-0.5 rounded bg-[#21262d] hover:bg-[#30363d] text-[11px] text-[#58a6ff] hover:text-white transition-colors shrink-0 disabled:opacity-50"
          >
            {preset}
          </button>
        ))}
      </div>

      {/* Terminal Output Area */}
      <div className="flex-1 overflow-auto p-3 space-y-3 font-mono leading-relaxed select-text">
        {history.map((item) => (
          <div key={item.id} className="space-y-1">
            {/* Command Header */}
            <div className="flex items-center gap-2 text-[#58a6ff]">
              <span className="text-emerald-400 font-bold select-none">dai@workspace:~$</span>
              <span className="font-bold text-[#f0f6fc]">{item.command}</span>
              <span className="text-[10px] text-[#8b949e] ml-auto select-none">
                {item.timestamp}
              </span>
            </div>

            {/* Running Indicator */}
            {item.isRunning && (
              <div className="flex items-center gap-2 text-amber-400 text-xs py-1">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                <span>Executing in sandbox...</span>
              </div>
            )}

            {/* Output */}
            {item.response && (
              <div className="pl-3 border-l-2 border-[#30363d] space-y-1">
                {item.response.stdout && (
                  <pre className="text-[#c9d1d9] whitespace-pre-wrap break-all font-mono">
                    {item.response.stdout}
                  </pre>
                )}

                {item.response.stderr && (
                  <pre className="text-[#ff7b72] whitespace-pre-wrap break-all font-mono">
                    {item.response.stderr}
                  </pre>
                )}

                {/* Exit Code Badge & Duration */}
                <div className="flex items-center gap-3 pt-1 text-[11px] select-none">
                  {item.response.exit_code === 0 ? (
                    <span className="inline-flex items-center gap-1 text-emerald-400">
                      <CheckCircle2 className="h-3 w-3" />
                      Exit 0
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[#ff7b72]">
                      <XCircle className="h-3 w-3" />
                      Exit {item.response.exit_code} ({item.response.status})
                    </span>
                  )}
                  <span className="inline-flex items-center gap-1 text-[#8b949e]">
                    <Clock className="h-3 w-3" />
                    {item.response.duration_ms}ms
                  </span>
                </div>
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Terminal Input Prompt */}
      <div className="flex items-center gap-2 px-3 py-2 bg-[#161b22] border-t border-[#30363d] shrink-0">
        <span className="text-emerald-400 font-bold select-none text-xs">dai@workspace:~$</span>
        <Input
          ref={inputRef}
          value={inputCommand}
          onChange={(e) => setInputCommand(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            isExecuting
              ? "Command running in background..."
              : "Type shell command (e.g. npm test, ls -la)..."
          }
          disabled={isExecuting}
          className="flex-1 h-7 bg-transparent border-0 focus-visible:ring-0 text-xs font-mono text-[#f0f6fc] placeholder:text-[#8b949e] p-0"
        />
        <Button
          size="icon"
          className="h-6 w-6 bg-primary hover:bg-primary/90 text-primary-foreground"
          onClick={() => handleRunCommand()}
          disabled={isExecuting || !inputCommand.trim()}
          title="Run command (Enter)"
        >
          {isExecuting ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <CornerDownLeft className="h-3 w-3" />
          )}
        </Button>
      </div>
    </div>
  );
}

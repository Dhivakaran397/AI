"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { apiClient } from "@/lib/api-client";
import type { TestSuiteRunResult, TestCaseResult } from "@/types";
import { DiagnosticInspectorModal } from "./diagnostic-inspector-modal";
import { TestGeneratorModal } from "./test-generator-modal";
import {
  Play,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Clock,
  Wrench,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Terminal,
  FileCode,
} from "lucide-react";

interface TestRunnerProps {
  projectId: string;
}

export function TestRunner({ projectId }: TestRunnerProps) {
  const [command, setCommand] = useState<string>("pytest -v");
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<TestSuiteRunResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Expanded failure traces map
  const [expandedCases, setExpandedCases] = useState<Record<string, boolean>>({});

  // Inspector modal state
  const [inspectorOpen, setInspectorOpen] = useState<boolean>(false);
  const [selectedTrace, setSelectedTrace] = useState<string>("");

  // Generator modal state
  const [generatorOpen, setGeneratorOpen] = useState<boolean>(false);

  const handleRunTests = async () => {
    if (!command.trim()) return;
    setIsRunning(true);
    setError(null);

    try {
      const res = await apiClient.post<TestSuiteRunResult>(
        `/api/v1/projects/${projectId}/tests/run?command=${encodeURIComponent(command.trim())}`
      );
      setTestResult(res);
    } catch (err: any) {
      setError(err?.message || "Failed to execute tests");
    } finally {
      setIsRunning(false);
    }
  };

  const toggleExpand = (caseId: string) => {
    setExpandedCases((prev) => ({ ...prev, [caseId]: !prev[caseId] }));
  };

  const handleDiagnose = (trace: string) => {
    setSelectedTrace(trace);
    setInspectorOpen(true);
  };

  return (
    <div className="flex h-full flex-col space-y-4 overflow-y-auto p-4">
      {/* Control Bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-1 items-center gap-2 max-w-xl">
          <Input
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            placeholder="pytest -v or npm test"
            disabled={isRunning}
            className="font-mono text-xs"
          />
          <Button
            size="sm"
            onClick={handleRunTests}
            disabled={isRunning || !command.trim()}
            className="shrink-0 bg-indigo-600 hover:bg-indigo-700 text-white"
          >
            {isRunning ? (
              <>
                <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> Running...
              </>
            ) : (
              <>
                <Play className="mr-1.5 h-3.5 w-3.5" /> Run Test Suite
              </>
            )}
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => setGeneratorOpen(true)}
            className="text-xs border-emerald-500/30 text-emerald-600 hover:bg-emerald-500/10 dark:text-emerald-400"
          >
            <Sparkles className="mr-1.5 h-3.5 w-3.5" /> Generate Tests
          </Button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg bg-destructive/10 p-3 text-xs text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Summary KPI Cards */}
      {testResult && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          <Card className="p-3">
            <p className="text-[11px] font-medium text-muted-foreground">Total Tests</p>
            <p className="text-xl font-bold font-mono">{testResult.total_count}</p>
          </Card>
          <Card className="p-3 border-emerald-500/30 bg-emerald-500/5">
            <p className="text-[11px] font-medium text-emerald-600 dark:text-emerald-400">Passed</p>
            <p className="text-xl font-bold font-mono text-emerald-600 dark:text-emerald-400">
              {testResult.passed_count}
            </p>
          </Card>
          <Card className="p-3 border-rose-500/30 bg-rose-500/5">
            <p className="text-[11px] font-medium text-rose-600 dark:text-rose-400">Failed</p>
            <p className="text-xl font-bold font-mono text-rose-600 dark:text-rose-400">
              {testResult.failed_count}
            </p>
          </Card>
          <Card className="p-3">
            <p className="text-[11px] font-medium text-amber-600 dark:text-amber-400">Skipped</p>
            <p className="text-xl font-bold font-mono text-amber-600 dark:text-amber-400">
              {testResult.skipped_count}
            </p>
          </Card>
          <Card className="p-3">
            <p className="text-[11px] font-medium text-muted-foreground">Duration</p>
            <p className="text-xl font-bold font-mono">{(testResult.duration_ms / 1000).toFixed(2)}s</p>
          </Card>
        </div>
      )}

      {/* Test Cases Matrix */}
      {testResult && testResult.cases && testResult.cases.length > 0 && (
        <Card className="overflow-hidden border-border/60">
          <div className="border-b border-border bg-muted/40 p-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center justify-between">
            <span>Test Case Results</span>
            <span className="font-mono text-[11px] text-muted-foreground">
              Exit Code: {testResult.exit_code}
            </span>
          </div>
          <CardContent className="p-0 divide-y divide-border/60">
            {testResult.cases.map((testCase: TestCaseResult, idx: number) => {
              const caseKey = `${testCase.suite || ""}-${testCase.name}-${idx}`;
              const isExpanded = Boolean(expandedCases[caseKey]);
              const hasFailure = testCase.status === "FAILED";

              return (
                <div key={caseKey} className="p-3 hover:bg-muted/20 text-xs">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 overflow-hidden">
                      {testCase.status === "PASSED" ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                      ) : testCase.status === "FAILED" ? (
                        <AlertCircle className="h-4 w-4 text-rose-500 shrink-0" />
                      ) : (
                        <Clock className="h-4 w-4 text-amber-500 shrink-0" />
                      )}
                      <div className="truncate">
                        <span className="font-semibold font-mono text-foreground">
                          {testCase.name}
                        </span>
                        {testCase.suite && (
                          <span className="ml-2 font-mono text-[11px] text-muted-foreground">
                            ({testCase.suite})
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      {testCase.duration_ms && (
                        <span className="font-mono text-[11px] text-muted-foreground">
                          {testCase.duration_ms}ms
                        </span>
                      )}
                      <Badge
                        className={`text-[10px] ${
                          testCase.status === "PASSED"
                            ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
                            : testCase.status === "FAILED"
                            ? "bg-rose-500/10 text-rose-600 border-rose-500/20"
                            : "bg-amber-500/10 text-amber-600 border-amber-500/20"
                        }`}
                      >
                        {testCase.status}
                      </Badge>

                      {hasFailure && (
                        <>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-6 px-2 text-[11px] text-rose-600 hover:bg-rose-500/10"
                            onClick={() =>
                              handleDiagnose(testCase.failure_trace || testResult.raw_output)
                            }
                          >
                            <Wrench className="mr-1 h-3 w-3" /> Auto-Fix with DAI
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-6 w-6 p-0"
                            onClick={() => toggleExpand(caseKey)}
                          >
                            {isExpanded ? (
                              <ChevronUp className="h-3.5 w-3.5" />
                            ) : (
                              <ChevronDown className="h-3.5 w-3.5" />
                            )}
                          </Button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Expandable Trace */}
                  {hasFailure && isExpanded && (
                    <div className="mt-2 space-y-2 rounded-md bg-black/90 p-2.5 font-mono text-[11px] text-rose-300">
                      <pre className="overflow-x-auto whitespace-pre-wrap">
                        {testCase.failure_trace || testCase.error_message || "No failure trace captured."}
                      </pre>
                    </div>
                  )}
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}

      {/* Raw Output Terminal Accordion */}
      {testResult && testResult.raw_output && (
        <div className="space-y-1">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            <Terminal className="h-3.5 w-3.5" /> Raw Runner Terminal Output
          </div>
          <pre className="max-h-48 overflow-y-auto rounded-md bg-black/90 p-3 font-mono text-[11px] text-zinc-300">
            {testResult.raw_output}
          </pre>
        </div>
      )}

      {/* Diagnostic Inspector Modal */}
      <DiagnosticInspectorModal
        open={inspectorOpen}
        onOpenChange={setInspectorOpen}
        projectId={projectId}
        initialTrace={selectedTrace}
        onPatchApplied={handleRunTests}
      />

      {/* Test Generator Modal */}
      <TestGeneratorModal
        open={generatorOpen}
        onOpenChange={setGeneratorOpen}
        projectId={projectId}
        onGenerated={handleRunTests}
      />
    </div>
  );
}

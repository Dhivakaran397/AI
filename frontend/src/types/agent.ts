export type AgentType =
  | "ORCHESTRATOR"
  | "ARCHITECT"
  | "RESEARCHER"
  | "CODER"
  | "TESTER"
  | "DEBUGGER"
  | "REVIEWER"
  | "DOCS";

export type AgentRunStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";

export interface Agent {
  id: string;
  name: string;
  type: AgentType;
  description?: string;
  system_prompt: string;
  capabilities: Record<string, boolean>;
  is_active: boolean;
  icon?: string;
  color?: string;
}

export interface AgentRun {
  id: string;
  agent_id: string;
  agent_name?: string;
  agent_type?: AgentType;
  project_id?: string;
  conversation_id?: string;
  status: AgentRunStatus;
  input_data: Record<string, any>;
  output_data?: Record<string, any>;
  error?: string;
  started_at?: string;
  completed_at?: string;
}

export interface OrchestrationStep {
  step_id: string;
  agent_type: AgentType;
  agent_name: string;
  action: string;
  status: AgentRunStatus;
  input_summary: string;
  output_summary?: string;
  artifacts: string[];
  duration_ms?: number;
}

export interface TeamOrchestrationRequest {
  project_id: string;
  goal: string;
}

export interface TeamOrchestrationResponse {
  project_id: string;
  goal: string;
  status: "COMPLETED" | "FAILED" | "IN_PROGRESS";
  summary: string;
  steps: OrchestrationStep[];
  created_files: string[];
}

export interface SelfHealRequest {
  project_id: string;
  test_command?: string;
  max_retries?: number;
}

export interface SelfHealResponse {
  project_id: string;
  test_command: string;
  initial_passed: boolean;
  resolved: boolean;
  iterations: number;
  diagnosis?: string;
  patches_applied: string[];
  final_output: string;
}

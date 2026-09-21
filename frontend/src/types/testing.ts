export type TestStatus = "PASSED" | "FAILED" | "SKIPPED";

export interface TestCaseResult {
  name: string;
  suite?: string;
  status: TestStatus;
  duration_ms?: number;
  error_message?: string;
  failure_trace?: string;
}

export interface TestSuiteRunResult {
  project_id: string;
  command: string;
  total_count: number;
  passed_count: number;
  failed_count: number;
  skipped_count: number;
  duration_ms: number;
  cases: TestCaseResult[];
  raw_output: string;
  exit_code: number;
}

export interface TestGenerateRequest {
  file_path: string;
  framework?: "pytest" | "jest" | "vitest";
  extra_instructions?: string;
}

export interface TestGenerateResponse {
  target_file: string;
  test_file_path: string;
  test_code: string;
  framework: string;
  test_count_estimated: number;
}

export interface ErrorTraceAnalysisRequest {
  raw_trace: string;
  command?: string;
}

export interface ErrorTraceAnalysisResponse {
  error_type: string;
  error_message: string;
  culprit_file?: string;
  culprit_line?: number;
  surrounding_code?: string;
  diagnosis: string;
  suggested_diff?: string;
  suggested_fix?: string;
}

export interface ApplyPatchRequest {
  file_path: string;
  patched_content: string;
  description?: string;
}

export interface ApplyPatchResponse {
  file_path: string;
  revision_id?: string;
  success: boolean;
  message: string;
}

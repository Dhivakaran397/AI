// API types
export interface ApiError {
  detail: string;
  status_code?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Activity {
  id: string;
  type: string;
  title: string;
  description: string | null;
  project_id: string | null;
  created_at: string;
}

export interface FileNode {
  name: string;
  path: string;
  is_directory: boolean;
  size: number;
  children: FileNode[];
}

export interface FileWriteRequest {
  path: string;
  content: string;
}

export interface FileEditRequest {
  path: string;
  target_content: string;
  replacement_content: string;
}

export interface FileContentResponse {
  path: string;
  content: string;
  size: number;
  file_type: string;
  has_revisions: boolean;
  updated_at: string;
}

export interface FileDiffResponse {
  path: string;
  original_content: string;
  current_content: string;
  diff_unified: string;
  revision_id: string | null;
}

export interface SearchResult {
  path: string;
  line_number: number;
  line_content: string;
}

export interface CommandExecutionRequest {
  command: string;
  timeout_seconds?: number;
  working_dir?: string;
}

export interface CommandExecutionResponse {
  command: string;
  exit_code: number;
  stdout: string;
  stderr: string;
  duration_ms: number;
  timed_out: boolean;
  status: "success" | "failed" | "timeout" | "blocked";
  error?: string | null;
}

export interface ProcessStartRequest {
  command: string;
  port?: number;
}

export interface ProcessLogChunk {
  line: string;
  timestamp: string;
  stream: "stdout" | "stderr";
}

export interface ProcessInfo {
  process_id: string;
  project_id: string;
  command: string;
  pid: number | null;
  status: "RUNNING" | "STOPPED" | "FAILED";
  port: number | null;
  started_at: string;
  logs_count: number;
}

export interface ProcessLogResponse {
  process_id: string;
  logs: ProcessLogChunk[];
}

export interface PreviewUrlResponse {
  url: string | null;
  is_active: boolean;
  port: number | null;
}

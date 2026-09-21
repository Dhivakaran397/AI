// Project types
export type ProjectStatus =
  | "IDEA"
  | "PLANNING"
  | "BUILDING"
  | "TESTING"
  | "DEBUGGING"
  | "REVIEW"
  | "COMPLETED"
  | "FAILED";

export type TaskStatus =
  | "TODO"
  | "IN_PROGRESS"
  | "BLOCKED"
  | "REVIEW"
  | "DONE";

export type TaskPriority =
  | "LOW"
  | "MEDIUM"
  | "HIGH"
  | "CRITICAL";

export interface Task {
  id: string;
  project_id: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  assigned_agent: string | null;
  dependencies: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  status: ProjectStatus;
  tech_stack: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  task_count: number;
  completed_task_count: number;
}

export interface ProjectDetail extends Project {
  tasks: Task[];
  recent_activities: {
    id: string;
    type: string;
    title: string;
    description: string | null;
    project_id: string | null;
    created_at: string;
  }[];
}

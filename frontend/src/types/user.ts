// User types
export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface UserSettings {
  id: string;
  user_id: string;
  ai_provider: string;
  ai_model: string;
  theme: string;
  preferences: Record<string, unknown> | null;
  updated_at: string;
}

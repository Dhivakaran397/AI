// Chat types
export type ChatMode = "CHAT" | "RESEARCH" | "BUILD" | "AGENT" | "ANALYZE" | "IMAGE";
export type MessageRole = "USER" | "ASSISTANT" | "SYSTEM" | "TOOL";

export interface ChatAttachment {
  name: string;
  type: string;
  data?: string; // base64 data URL for images
  content?: string; // raw text for text/code/data
  size?: number;
}

export interface ToolCallRecord {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
  result?: Record<string, unknown>;
}

export interface MessageMetadata {
  tool_calls?: ToolCallRecord[];
  attachments?: ChatAttachment[];
  [key: string]: unknown;
}

export interface Conversation {
  id: string;
  title: string;
  mode: ChatMode;
  is_archived: boolean;
  project_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  mode: ChatMode | null;
  metadata_: MessageMetadata | null;
  created_at: string;
}

export interface ConversationWithMessages extends Conversation {
  messages: Message[];
}

export interface SendMessageRequest {
  content: string;
  mode?: ChatMode;
  attachments?: ChatAttachment[];
}

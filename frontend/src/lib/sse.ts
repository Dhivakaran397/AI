import { API_URL } from "./constants";

export interface SSECallbacks {
  onStart?: () => void;
  onContent?: (content: string) => void;
  onToolCallStart?: (toolCall: {
    id: string;
    name: string;
    arguments: Record<string, unknown>;
  }) => void;
  onToolCallResult?: (result: {
    tool_call_id: string;
    name: string;
    result: unknown;
  }) => void;
  onEnd?: (fullContent: string, metadata?: Record<string, unknown> | null) => void;
  onError?: (error: string) => void;
}

import type { ChatAttachment } from "@/types/chat";

export function streamChat(
  conversationId: string,
  content: string,
  mode: string,
  callbacks: SSECallbacks,
  signal?: AbortSignal,
  attachments?: ChatAttachment[]
): void {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("dai_token")
      : null;

  const url = `${API_URL}/chat/conversations/${conversationId}/messages`;

  fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ content, mode, attachments }),
    signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const err = await response.json().catch(() => ({
          detail: "Stream request failed",
        }));
        callbacks.onError?.(err.detail);
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        callbacks.onError?.("No response body");
        return;
      }

      const decoder = new TextDecoder();
      let fullContent = "";
      let metadata: Record<string, unknown> | null = null;
      let buffer = "";

      callbacks.onStart?.();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6).trim();
            if (data === "[DONE]") {
              callbacks.onEnd?.(fullContent, metadata);
              return;
            }

            try {
              const parsed = JSON.parse(data);
              if (parsed.type === "content_delta" && parsed.content) {
                fullContent += parsed.content;
                callbacks.onContent?.(fullContent);
              } else if (parsed.type === "tool_call_start" && parsed.tool_call) {
                callbacks.onToolCallStart?.(parsed.tool_call);
              } else if (parsed.type === "tool_call_result") {
                callbacks.onToolCallResult?.(parsed);
              } else if (parsed.type === "error") {
                callbacks.onError?.(parsed.message || "Stream error");
                return;
              } else if (parsed.type === "message_end") {
                if (parsed.metadata) {
                  metadata = parsed.metadata;
                }
                callbacks.onEnd?.(fullContent, metadata);
                return;
              }
            } catch {
              // Non-JSON data line, skip
            }
          }
        }
      }

      if (fullContent) {
        callbacks.onEnd?.(fullContent, metadata);
      }
    })
    .catch((err) => {
      if (err.name !== "AbortError") {
        callbacks.onError?.(err.message || "Stream connection failed");
      }
    });
}

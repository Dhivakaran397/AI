"use client";

import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatMessage } from "./chat-message";
import { useChatStore } from "@/stores/chat-store";
import { Zap } from "lucide-react";
import type { Message } from "@/types/chat";

interface ChatMessagesProps {
  messages: Message[];
  onEditMessage?: (messageId: string, newContent: string, resubmit?: boolean) => void;
  onDeleteMessage?: (messageId: string) => void;
}

export function ChatMessages({
  messages,
  onEditMessage,
  onDeleteMessage,
}: ChatMessagesProps) {
  const { isStreaming, streamingContent } = useChatStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, streamingContent]);

  if (messages.length === 0 && !isStreaming) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
        <div className="relative mb-4">
          <div className="absolute -inset-1 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 opacity-30 blur-sm" />
          <img
            src="/dai_logo.png"
            alt="DAI AI"
            className="relative h-20 w-20 rounded-full object-contain shadow-md"
          />
        </div>
        <h2 className="text-xl font-semibold mb-2">Start a conversation with DAI</h2>
        <p className="text-muted-foreground max-w-md">
          Ask DAI anything — get help with coding, research, analysis, or
          building projects.
        </p>
      </div>
    );
  }

  return (
    <div
      ref={scrollRef}
      className="flex-1 min-h-0 overflow-y-auto overscroll-contain px-2 py-4"
    >
      <div className="max-w-4xl mx-auto space-y-3">
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message}
            onEdit={onEditMessage}
            onDelete={onDeleteMessage}
          />
        ))}
        {isStreaming && streamingContent && (
          <ChatMessage
            message={{
              id: "streaming",
              conversation_id: "",
              role: "ASSISTANT",
              content: streamingContent,
              mode: null,
              metadata_: null,
              created_at: new Date().toISOString(),
            }}
            isStreaming
          />
        )}
      </div>
    </div>
  );
}

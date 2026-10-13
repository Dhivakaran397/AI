"use client";

import { useRouter, usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Plus, MessageSquare, Trash2 } from "lucide-react";
import { useState } from "react";
import type { Conversation } from "@/types/chat";

interface ChatSidebarProps {
  conversations: Conversation[];
  onNewChat: () => void;
  onDeleteConversation?: (convId: string) => void;
}

export function ChatSidebar({
  conversations,
  onNewChat,
  onDeleteConversation,
}: ChatSidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [confirmingId, setConfirmingId] = useState<string | null>(null);

  const handleDelete = (e: React.MouseEvent, convId: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (confirmingId === convId) {
      onDeleteConversation?.(convId);
      setConfirmingId(null);
    } else {
      setConfirmingId(convId);
    }
  };

  return (
    <div className="flex h-full w-64 flex-col border-r bg-muted/30">
      <div className="p-3">
        <Button
          onClick={onNewChat}
          className="w-full justify-start gap-2"
          variant="outline"
        >
          <Plus className="h-4 w-4" />
          New Chat
        </Button>
      </div>
      <ScrollArea className="flex-1 px-2">
        <div className="space-y-1 pb-2">
          {conversations.map((conv) => {
            const isActive = pathname === `/chat/${conv.id}`;
            const isConfirming = confirmingId === conv.id;

            return (
              <div
                key={conv.id}
                className="group relative flex items-center"
                onMouseLeave={() => {
                  if (isConfirming) setConfirmingId(null);
                }}
              >
                <button
                  type="button"
                  onClick={() => router.push(`/chat/${conv.id}`)}
                  className={cn(
                    "flex flex-1 items-center gap-2 rounded-lg px-3 py-2 pr-8 text-sm transition-colors overflow-hidden text-left cursor-pointer",
                    isActive
                      ? "bg-accent text-accent-foreground font-medium"
                      : "text-muted-foreground hover:bg-accent/50"
                  )}
                >
                  <MessageSquare className="h-4 w-4 shrink-0" />
                  <span className="truncate">{conv.title}</span>
                </button>

                {onDeleteConversation && (
                  <button
                    onClick={(e) => handleDelete(e, conv.id)}
                    className={cn(
                      "absolute right-2 flex items-center justify-center rounded p-1 text-xs transition-opacity",
                      isConfirming
                        ? "bg-destructive text-destructive-foreground px-1.5 py-0.5 text-[11px] font-medium"
                        : "opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                    )}
                    title={isConfirming ? "Click again to confirm delete" : "Delete chat"}
                  >
                    {isConfirming ? "Delete?" : <Trash2 className="h-3.5 w-3.5" />}
                  </button>
                )}
              </div>
            );
          })}
          {conversations.length === 0 && (
            <p className="px-3 py-6 text-center text-xs text-muted-foreground">
              No conversations yet
            </p>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

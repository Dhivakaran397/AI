"use client";

import { cn } from "@/lib/utils";
import { useChatStore } from "@/stores/chat-store";
import { CHAT_MODES } from "@/lib/constants";
import type { ChatMode } from "@/types/chat";

export function ModeSelector() {
  const { activeMode, setActiveMode } = useChatStore();

  return (
    <div className="flex items-center gap-1">
      {CHAT_MODES.map((mode) => (
        <button
          key={mode.value}
          onClick={() => setActiveMode(mode.value as ChatMode)}
          className={cn(
            "px-3 py-1 rounded-full text-xs font-medium transition-colors",
            activeMode === mode.value
              ? `${mode.color} text-white`
              : "bg-muted text-muted-foreground hover:bg-muted/80"
          )}
        >
          {mode.label}
        </button>
      ))}
    </div>
  );
}

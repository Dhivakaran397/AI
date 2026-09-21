import { create } from "zustand";
import type { ChatMode, Conversation, Message } from "@/types/chat";

interface ChatState {
  conversations: Conversation[];
  activeConversation: Conversation | null;
  messages: Message[];
  isStreaming: boolean;
  streamingContent: string;
  activeMode: ChatMode;
  abortController: AbortController | null;

  setConversations: (conversations: Conversation[]) => void;
  setActiveConversation: (conv: Conversation | null) => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  updateMessage: (messageId: string, content: string) => void;
  removeMessage: (messageId: string) => void;
  removeConversation: (convId: string) => void;
  setActiveMode: (mode: ChatMode) => void;
  setIsStreaming: (streaming: boolean) => void;
  setStreamingContent: (content: string) => void;
  setAbortController: (controller: AbortController | null) => void;
  stopStreaming: () => void;
  reset: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  activeConversation: null,
  messages: [],
  isStreaming: false,
  streamingContent: "",
  activeMode: "CHAT",
  abortController: null,

  setConversations: (conversations) => set({ conversations }),
  setActiveConversation: (conv) => set({ activeConversation: conv }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  updateMessage: (messageId, content) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === messageId ? { ...m, content } : m
      ),
    })),
  removeMessage: (messageId) =>
    set((state) => ({
      messages: state.messages.filter((m) => m.id !== messageId),
    })),
  removeConversation: (convId) =>
    set((state) => ({
      conversations: state.conversations.filter((c) => c.id !== convId),
      activeConversation:
        state.activeConversation?.id === convId ? null : state.activeConversation,
    })),
  setActiveMode: (mode) => set({ activeMode: mode }),
  setIsStreaming: (streaming) => set({ isStreaming: streaming }),
  setStreamingContent: (content) => set({ streamingContent: content }),
  setAbortController: (controller) => set({ abortController: controller }),

  stopStreaming: () => {
    const controller = get().abortController;
    if (controller) {
      controller.abort();
    }
    set({
      isStreaming: false,
      streamingContent: "",
      abortController: null,
    });
  },

  reset: () =>
    set({
      activeConversation: null,
      messages: [],
      isStreaming: false,
      streamingContent: "",
      abortController: null,
    }),
}));

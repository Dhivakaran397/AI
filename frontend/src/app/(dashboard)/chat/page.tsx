"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Header } from "@/components/layout/header";
import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { ChatMessages } from "@/components/chat/chat-messages";
import { ChatInput } from "@/components/chat/chat-input";
import { useChatStore } from "@/stores/chat-store";
import { apiClient } from "@/lib/api-client";
import { streamChat } from "@/lib/sse";
import type { Conversation, Message, ChatAttachment } from "@/types/chat";

export default function ChatPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const promptParam = searchParams.get("prompt");

  const {
    conversations,
    setConversations,
    messages,
    setMessages,
    activeConversation,
    setActiveConversation,
    activeMode,
    setIsStreaming,
    setStreamingContent,
    setAbortController,
    addMessage,
    updateMessage,
    removeMessage,
    removeConversation,
  } = useChatStore();

  const [loading, setLoading] = useState(true);

  // Load conversations
  useEffect(() => {
    const loadConversations = async () => {
      try {
        const data = await apiClient.get<Conversation[]>("/chat/conversations");
        setConversations(data);
      } catch {
        // silently handle - user may not have any conversations
      } finally {
        setLoading(false);
      }
    };
    loadConversations();
  }, [setConversations]);

  const handleNewChat = useCallback(async () => {
    try {
      const conv = await apiClient.post<Conversation>("/chat/conversations", {
        title: "New Conversation",
        mode: activeMode,
      });
      setConversations([conv, ...conversations]);
      setActiveConversation(conv);
      setMessages([]);
      router.push(`/chat/${conv.id}`);
    } catch {
      // Error creating conversation
    }
  }, [activeMode, conversations, setConversations, setActiveConversation, setMessages, router]);

  const handleDeleteConversation = useCallback(
    async (convId: string) => {
      try {
        await apiClient.delete(`/chat/conversations/${convId}`);
        removeConversation(convId);
        if (activeConversation?.id === convId) {
          setActiveConversation(null);
          setMessages([]);
          router.push("/chat");
        }
      } catch (err) {
        console.error("Failed to delete conversation", err);
      }
    },
    [activeConversation, removeConversation, setActiveConversation, setMessages, router]
  );

  const handleEditMessage = useCallback(
    async (messageId: string, newContent: string, resubmit?: boolean) => {
      const conv = activeConversation;
      if (!conv) return;
      try {
        await apiClient.put(
          `/chat/conversations/${conv.id}/messages/${messageId}`,
          { content: newContent }
        );
        updateMessage(messageId, newContent);
        if (resubmit) {
          handleSend(newContent);
        }
      } catch (err) {
        console.error("Failed to edit message", err);
      }
    },
    [activeConversation, updateMessage]
  );

  const handleDeleteMessage = useCallback(
    async (messageId: string) => {
      const conv = activeConversation;
      if (!conv) return;
      try {
        await apiClient.delete(
          `/chat/conversations/${conv.id}/messages/${messageId}`
        );
        removeMessage(messageId);
      } catch (err) {
        console.error("Failed to delete message", err);
      }
    },
    [activeConversation, removeMessage]
  );

  const handleSend = useCallback(
    async (content: string, attachments?: ChatAttachment[]) => {
      let conv = activeConversation;

      // Create conversation if none active
      if (!conv) {
        try {
          conv = await apiClient.post<Conversation>("/chat/conversations", {
            title: content.slice(0, 50) || (attachments?.[0]?.name ? `Attached: ${attachments[0].name}` : "New Chat"),
            mode: activeMode,
          });
          setConversations([conv, ...conversations]);
          setActiveConversation(conv);
          router.push(`/chat/${conv.id}`);
        } catch {
          return;
        }
      }

      // Add user message optimistically with attachments metadata
      const userMsg: Message = {
        id: crypto.randomUUID(),
        conversation_id: conv.id,
        role: "USER",
        content,
        mode: activeMode,
        metadata_: attachments && attachments.length > 0 ? { attachments } : null,
        created_at: new Date().toISOString(),
      };
      addMessage(userMsg);

      // Start streaming
      const controller = new AbortController();
      setAbortController(controller);
      setIsStreaming(true);
      setStreamingContent("");

      streamChat(
        conv.id,
        content,
        activeMode,
        {
          onContent: (fullContent) => {
            setStreamingContent(fullContent);
          },
          onEnd: (fullContent, metadata) => {
            setIsStreaming(false);
            setStreamingContent("");
            setAbortController(null);
            // Add assistant message
            const assistantMsg: Message = {
              id: crypto.randomUUID(),
              conversation_id: conv!.id,
              role: "ASSISTANT",
              content: fullContent,
              mode: activeMode,
              metadata_: (metadata as any) || null,
              created_at: new Date().toISOString(),
            };
            addMessage(assistantMsg);
          },
          onError: (error) => {
            setIsStreaming(false);
            setStreamingContent("");
            setAbortController(null);
            const errorMsg: Message = {
              id: crypto.randomUUID(),
              conversation_id: conv!.id,
              role: "ASSISTANT",
              content: `Error: ${error}`,
              mode: activeMode,
              metadata_: null,
              created_at: new Date().toISOString(),
            };
            addMessage(errorMsg);
          },
        },
        controller.signal,
        attachments
      );
    },
    [
      activeConversation,
      activeMode,
      conversations,
      setConversations,
      setActiveConversation,
      addMessage,
      setIsStreaming,
      setStreamingContent,
      setAbortController,
      router,
    ]
  );

  // Handle prompt from URL
  useEffect(() => {
    if (promptParam && !loading) {
      handleSend(promptParam);
      router.replace("/chat");
    }
  }, [promptParam, loading]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="flex flex-col h-full w-full overflow-hidden">
      <Header title="Chat" />
      <div className="flex flex-1 min-h-0 overflow-hidden">
        <ChatSidebar
          conversations={conversations}
          onNewChat={handleNewChat}
          onDeleteConversation={handleDeleteConversation}
        />
        <div className="flex flex-1 min-h-0 flex-col overflow-hidden">
          <ChatMessages
            messages={messages}
            onEditMessage={handleEditMessage}
            onDeleteMessage={handleDeleteMessage}
          />
          <ChatInput onSend={handleSend} />
        </div>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState, useCallback, use } from "react";
import { useRouter } from "next/navigation";
import { Header } from "@/components/layout/header";
import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { ChatMessages } from "@/components/chat/chat-messages";
import { ChatInput } from "@/components/chat/chat-input";
import { useChatStore } from "@/stores/chat-store";
import { apiClient } from "@/lib/api-client";
import { streamChat } from "@/lib/sse";
import { Loading } from "@/components/shared/loading";
import type { Message, Conversation, ConversationWithMessages, ChatAttachment } from "@/types/chat";

export default function ConversationPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const {
    conversations,
    setConversations,
    activeConversation,
    setActiveConversation,
    messages,
    setMessages,
    activeMode,
    addMessage,
    updateMessage,
    removeMessage,
    removeConversation,
    setIsStreaming,
    setStreamingContent,
    setAbortController,
  } = useChatStore();

  const [loading, setLoading] = useState(true);

  // Load conversations list for sidebar
  useEffect(() => {
    const loadConversations = async () => {
      try {
        const data = await apiClient.get<Conversation[]>("/chat/conversations");
        setConversations(data);
      } catch {
        // silently ignore
      }
    };
    loadConversations();
  }, [setConversations]);

  useEffect(() => {
    const loadConversation = async () => {
      try {
        const data = await apiClient.get<ConversationWithMessages>(
          `/chat/conversations/${id}`
        );
        setActiveConversation(data);
        setMessages(data.messages || []);
      } catch {
        // Error loading conversation
      } finally {
        setLoading(false);
      }
    };
    loadConversation();

    return () => {
      setActiveConversation(null);
      setMessages([]);
    };
  }, [id, setActiveConversation, setMessages]);

  const handleSend = useCallback(
    async (content: string, attachments?: ChatAttachment[]) => {
      const userMsg: Message = {
        id: crypto.randomUUID(),
        conversation_id: id,
        role: "USER",
        content,
        mode: activeMode,
        metadata_: attachments && attachments.length > 0 ? { attachments } : null,
        created_at: new Date().toISOString(),
      };
      addMessage(userMsg);

      const controller = new AbortController();
      setAbortController(controller);
      setIsStreaming(true);
      setStreamingContent("");

      streamChat(
        id,
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
            const assistantMsg: Message = {
              id: crypto.randomUUID(),
              conversation_id: id,
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
              conversation_id: id,
              role: "ASSISTANT",
              content: `Error: ${error}`,
              mode: null,
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
    [id, activeMode, addMessage, setIsStreaming, setStreamingContent, setAbortController]
  );

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
        if (id === convId) {
          router.push("/chat");
        }
      } catch (err) {
        console.error("Failed to delete conversation", err);
      }
    },
    [id, removeConversation, router]
  );

  const handleEditMessage = useCallback(
    async (messageId: string, newContent: string, resubmit?: boolean) => {
      try {
        await apiClient.put(
          `/chat/conversations/${id}/messages/${messageId}`,
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
    [id, updateMessage, handleSend]
  );

  const handleDeleteMessage = useCallback(
    async (messageId: string) => {
      try {
        await apiClient.delete(
          `/chat/conversations/${id}/messages/${messageId}`
        );
        removeMessage(messageId);
      } catch (err) {
        console.error("Failed to delete message", err);
      }
    },
    [id, removeMessage]
  );

  if (loading) {
    return (
      <>
        <Header title="Chat" />
        <Loading />
      </>
    );
  }

  return (
    <div className="flex flex-col h-full w-full overflow-hidden">
      <Header title={activeConversation?.title || "Chat"} />
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

"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ModeSelector } from "./mode-selector";
import { useChatStore } from "@/stores/chat-store";
import {
  Send,
  Square,
  Paperclip,
  Image as ImageIcon,
  FileText,
  FileSpreadsheet,
  FileCode,
  X,
} from "lucide-react";
import type { ChatAttachment } from "@/types/chat";

interface ChatInputProps {
  onSend: (content: string, attachments?: ChatAttachment[]) => void;
  disabled?: boolean;
  initialValue?: string;
}

export function ChatInput({ onSend, disabled, initialValue }: ChatInputProps) {
  const [value, setValue] = useState(initialValue || "");
  const [attachments, setAttachments] = useState<ChatAttachment[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const { isStreaming, stopStreaming, activeMode } = useChatStore();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const placeholder = "";

  useEffect(() => {
    if (initialValue) {
      setValue(initialValue);
    }
  }, [initialValue]);

  const processFiles = useCallback((files: FileList | File[]) => {
    Array.from(files).forEach((file) => {
      const isImage = file.type.startsWith("image/");
      const isText =
        file.type.startsWith("text/") ||
        file.name.endsWith(".md") ||
        file.name.endsWith(".json") ||
        file.name.endsWith(".csv") ||
        file.name.endsWith(".py") ||
        file.name.endsWith(".ts") ||
        file.name.endsWith(".js");

      const reader = new FileReader();

      if (isImage || file.type === "application/pdf") {
        reader.onload = () => {
          setAttachments((prev) => [
            ...prev,
            {
              name: file.name,
              type: file.type || "application/octet-stream",
              data: reader.result as string,
              size: file.size,
            },
          ]);
        };
        reader.readAsDataURL(file);
      } else if (isText) {
        reader.onload = () => {
          setAttachments((prev) => [
            ...prev,
            {
              name: file.name,
              type: file.type || "text/plain",
              content: reader.result as string,
              size: file.size,
            },
          ]);
        };
        reader.readAsText(file);
      } else {
        // Generic file as base64
        reader.onload = () => {
          setAttachments((prev) => [
            ...prev,
            {
              name: file.name,
              type: file.type || "application/octet-stream",
              data: reader.result as string,
              size: file.size,
            },
          ]);
        };
        reader.readAsDataURL(file);
      }
    });
  }, []);

  // Handle Clipboard Paste (Ctrl+V with image/file)
  const handlePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    const filesToProcess: File[] = [];
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.kind === "file") {
        const file = item.getAsFile();
        if (file) {
          filesToProcess.push(file);
        }
      }
    }

    if (filesToProcess.length > 0) {
      processFiles(filesToProcess);
    }
  };

  // Drag and Drop
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer?.files) {
      processFiles(e.dataTransfer.files);
    }
  };

  const removeAttachment = (idx: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleSubmit = () => {
    const textToSend = value.trim();
    if ((!textToSend && attachments.length === 0) || disabled) return;

    onSend(textToSend || (attachments.length > 0 ? `Uploaded ${attachments.length} attachment(s)` : ""), attachments);
    setValue("");
    setAttachments([]);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
    const textarea = e.target;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return "";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`shrink-0 z-10 border-t bg-background/95 backdrop-blur p-4 transition-colors ${
        isDragging ? "bg-primary/5 border-primary" : ""
      }`}
    >
      <div className="max-w-4xl mx-auto space-y-3">
        <ModeSelector />

        {/* Attachment preview chips tray */}
        {attachments.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 p-2 rounded-xl bg-muted/60 border border-border/40">
            {attachments.map((att, idx) => {
              const isImg = att.type.startsWith("image/") && att.data;
              return (
                <div
                  key={idx}
                  className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-background border border-border/60 shadow-sm text-xs group"
                >
                  {isImg ? (
                    <img
                      src={att.data}
                      alt={att.name}
                      className="h-6 w-6 rounded object-cover border border-border/40"
                    />
                  ) : att.name.endsWith(".csv") || att.name.endsWith(".xlsx") ? (
                    <FileSpreadsheet className="h-4 w-4 text-emerald-500" />
                  ) : att.name.endsWith(".py") || att.name.endsWith(".ts") || att.name.endsWith(".json") ? (
                    <FileCode className="h-4 w-4 text-blue-500" />
                  ) : (
                    <FileText className="h-4 w-4 text-primary" />
                  )}

                  <div className="flex flex-col max-w-[140px] truncate">
                    <span className="truncate font-medium">{att.name}</span>
                    <span className="text-[10px] text-muted-foreground">
                      {formatFileSize(att.size)}
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={() => removeAttachment(idx)}
                    className="h-4 w-4 rounded-full flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
              );
            })}
          </div>
        )}

        <div className="flex items-end gap-2">
          {/* File Picker Button */}
          <input
            type="file"
            ref={fileInputRef}
            multiple
            accept="image/*,.pdf,.doc,.docx,.pptx,.txt,.csv,.json,.md,.py,.js,.ts"
            className="hidden"
            onChange={(e) => {
              if (e.target.files) {
                processFiles(e.target.files);
              }
              e.target.value = "";
            }}
          />
          <Button
            type="button"
            variant="outline"
            size="icon"
            className="h-11 w-11 shrink-0 rounded-xl text-muted-foreground hover:text-foreground"
            onClick={() => fileInputRef.current?.click()}
            title="Attach images, documents, or files (or paste with Ctrl+V)"
          >
            <Paperclip className="h-4 w-4" />
          </Button>

          <Textarea
            ref={textareaRef}
            value={value}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            onPaste={handlePaste}
            placeholder={placeholder}
            className="min-h-[44px] max-h-[200px] resize-none rounded-xl"
            rows={1}
            disabled={isStreaming}
          />

          {isStreaming ? (
            <Button
              size="icon"
              variant="destructive"
              className="h-11 w-11 shrink-0 rounded-xl"
              onClick={stopStreaming}
            >
              <Square className="h-4 w-4" />
            </Button>
          ) : (
            <Button
              size="icon"
              className="h-11 w-11 shrink-0 rounded-xl"
              onClick={handleSubmit}
              disabled={(!value.trim() && attachments.length === 0) || disabled}
            >
              <Send className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

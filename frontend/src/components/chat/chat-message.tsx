"use client";

import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Copy,
  Check,
  Zap,
  User,
  Wrench,
  ChevronDown,
  ChevronRight,
  Download,
  ExternalLink,
  Maximize2,
  X,
  Image as ImageIcon,
  Sparkles,
  Presentation,
  FileText,
  FileCode,
  FileSpreadsheet,
  FileDown,
  Pencil,
  Trash2,
  Send,
  Film,
  Layers,
} from "lucide-react";
import { useState, useCallback, useEffect } from "react";
import type { Message, ToolCallRecord, ChatAttachment } from "@/types/chat";
import { VideoPlayerCard, type VideoData } from "./video-player-card";
import { SocialCarouselCard, type CarouselData } from "./social-carousel-card";

interface ChatMessageProps {
  message: Message;
  isStreaming?: boolean;
  onEdit?: (messageId: string, newContent: string, resubmit?: boolean) => void;
  onDelete?: (messageId: string) => void;
}

export function ChatMessage({
  message,
  isStreaming,
  onEdit,
  onDelete,
}: ChatMessageProps) {
  const isUser = message.role === "USER";
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(message.content);
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    setEditContent(message.content);
  }, [message.content]);

  const toolCalls = message.metadata_?.tool_calls as ToolCallRecord[] | undefined;
  const attachments = message.metadata_?.attachments as ChatAttachment[] | undefined;

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [message.content]);

  return (
    <div
      className={cn(
        "flex gap-3 px-4 py-3 group/row",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {!isUser && (
        <Avatar className="h-8 w-8 shrink-0 mt-0.5 border border-primary/20 shadow-sm">
          <AvatarImage src="/dai_logo.png" alt="DAI" className="object-contain" />
          <AvatarFallback className="bg-primary text-primary-foreground text-xs">
            <Zap className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}

      <div
        className={cn(
          "group relative max-w-[88%] md:max-w-[78%] rounded-2xl px-4 py-3 space-y-2.5 shadow-sm transition-all",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted/90 border border-border/40"
        )}
      >
        {/* Tool Calls Display */}
        {toolCalls && toolCalls.length > 0 && (
          <div className="space-y-1.5 pb-2 border-b border-border/40">
            {toolCalls.map((tc, idx) => (
              <ToolCallBadge key={tc.id || idx} toolCall={tc} />
            ))}
          </div>
        )}

        {/* User Attachments Display */}
        {isUser && attachments && attachments.length > 0 && (
          <div className="flex flex-wrap gap-2 pb-1">
            {attachments.map((att, idx) => {
              const isImg = att.type.startsWith("image/") && att.data;
              return (
                <div
                  key={idx}
                  className="rounded-xl overflow-hidden border border-white/20 bg-black/20 backdrop-blur max-w-xs"
                >
                  {isImg ? (
                    <img
                      src={att.data}
                      alt={att.name}
                      className="max-h-48 w-auto rounded object-cover"
                    />
                  ) : (
                    <div className="flex items-center gap-2 p-2 text-xs font-mono">
                      <FileText className="h-4 w-4" />
                      <span className="truncate max-w-[150px]">{att.name}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Message Content or Inline Edit */}
        {isEditing ? (
          <div className="space-y-2 min-w-[260px] sm:min-w-[320px]">
            <textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              className={cn(
                "w-full min-h-[80px] rounded-lg p-2.5 text-sm resize-y outline-none border focus:ring-1",
                isUser
                  ? "bg-black/30 border-white/30 text-white placeholder-white/50 focus:border-white/60 focus:ring-white/40"
                  : "bg-background border-border text-foreground focus:border-primary focus:ring-primary"
              )}
              autoFocus
            />
            <div className="flex items-center justify-end gap-1.5 text-xs">
              <Button
                variant="ghost"
                size="sm"
                className={cn(
                  "h-7 px-2.5 text-xs",
                  isUser ? "hover:bg-white/10 text-white/90" : ""
                )}
                onClick={() => {
                  setEditContent(message.content);
                  setIsEditing(false);
                }}
              >
                Cancel
              </Button>
              <Button
                variant="secondary"
                size="sm"
                className="h-7 px-2.5 text-xs font-medium"
                onClick={() => {
                  if (editContent.trim()) {
                    onEdit?.(message.id, editContent.trim(), false);
                    setIsEditing(false);
                  }
                }}
              >
                Save
              </Button>
              {isUser && onEdit && (
                <Button
                  size="sm"
                  className={cn(
                    "h-7 px-2.5 text-xs gap-1 font-medium",
                    isUser
                      ? "bg-white text-primary hover:bg-white/90 shadow-sm"
                      : ""
                  )}
                  onClick={() => {
                    if (editContent.trim()) {
                      onEdit(message.id, editContent.trim(), true);
                      setIsEditing(false);
                    }
                  }}
                >
                  <Send className="h-3 w-3" />
                  Save & Resubmit
                </Button>
              )}
            </div>
          </div>
        ) : (
          <div className="text-sm whitespace-pre-wrap break-words leading-relaxed">
            <MessageContent content={message.content} isUser={isUser} />
          </div>
        )}

        {/* Rich Tool Output Cards (Video & Carousel) */}
        {!isUser && toolCalls && toolCalls.length > 0 && (
          <div className="space-y-2 pt-1">
            {toolCalls.map((tc, idx) => {
              const res = (tc.result as any)?.result || tc.result;
              if (tc.name === "generate_video" && res?.video_url) {
                return <VideoPlayerCard key={tc.id || idx} video={res as VideoData} />;
              }
              if (tc.name === "generate_social_carousel" && res?.slides?.length) {
                return <SocialCarouselCard key={tc.id || idx} carousel={res as CarouselData} />;
              }
              return null;
            })}
          </div>
        )}

        {isStreaming && (
          <span className="inline-block w-1.5 h-4 bg-current animate-pulse ml-0.5" />
        )}

        {/* Delete Confirmation or Normal Footer */}
        {confirmDelete ? (
          <div className="flex items-center justify-between gap-3 pt-1.5 border-t border-border/40 text-xs">
            <span className={cn("font-medium", isUser ? "text-white/90" : "text-destructive")}>
              Delete this message?
            </span>
            <div className="flex items-center gap-1.5">
              <Button
                variant="ghost"
                size="sm"
                className={cn("h-6 px-2 text-xs", isUser ? "hover:bg-white/10 text-white" : "")}
                onClick={() => setConfirmDelete(false)}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                size="sm"
                className="h-6 px-2 text-xs"
                onClick={() => {
                  onDelete?.(message.id);
                  setConfirmDelete(false);
                }}
              >
                Delete
              </Button>
            </div>
          </div>
        ) : (
          <div
            className={cn(
              "flex items-center gap-2 mt-1.5 text-xs",
              isUser ? "text-primary-foreground/70" : "text-muted-foreground"
            )}
          >
            <span>
              {new Date(message.created_at).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>

            {/* Action buttons on hover */}
            {!isStreaming && !isEditing && (
              <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 group-hover/row:opacity-100 transition-opacity ml-auto">
                <Button
                  variant="ghost"
                  size="icon"
                  className={cn(
                    "h-6 w-6 rounded",
                    isUser
                      ? "text-white/70 hover:text-white hover:bg-white/15"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted"
                  )}
                  onClick={handleCopy}
                  title="Copy message"
                >
                  {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                </Button>

                {onEdit && isUser && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 rounded text-white/70 hover:text-white hover:bg-white/15"
                    onClick={() => {
                      setEditContent(message.content);
                      setIsEditing(true);
                    }}
                    title="Edit message"
                  >
                    <Pencil className="h-3 w-3" />
                  </Button>
                )}

                {onDelete && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className={cn(
                      "h-6 w-6 rounded",
                      isUser
                        ? "text-white/70 hover:text-destructive hover:bg-white/15"
                        : "text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                    )}
                    onClick={() => setConfirmDelete(true)}
                    title="Delete message"
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {isUser && (
        <Avatar className="h-8 w-8 shrink-0 mt-0.5">
          <AvatarFallback className="text-xs">
            <User className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  );
}

function ToolCallBadge({ toolCall }: { toolCall: ToolCallRecord }) {
  const [open, setOpen] = useState(false);
  const isImageTool = toolCall.name === "generate_image";
  const isPptTool = toolCall.name === "generate_presentation";
  const isWordTool = toolCall.name === "generate_word_document";
  const isVideoTool = toolCall.name === "generate_video";
  const isCarouselTool = toolCall.name === "generate_social_carousel";

  const resultObj = (toolCall.result as any)?.result || toolCall.result;
  const imageUrl = resultObj?.image_url;
  const fileUrl = resultObj?.file_url;
  const videoUrl = resultObj?.video_url;
  const carouselSlides = resultObj?.slides;

  return (
    <div className="text-xs">
      <div className="flex items-center gap-2 flex-wrap">
        <button
          onClick={() => setOpen(!open)}
          className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground font-mono bg-background/60 hover:bg-background px-2.5 py-1 rounded-md transition-colors border border-border/40"
        >
          {isImageTool ? (
            <Sparkles className="h-3.5 w-3.5 text-pink-500" />
          ) : isPptTool ? (
            <Presentation className="h-3.5 w-3.5 text-orange-500" />
          ) : isWordTool ? (
            <FileText className="h-3.5 w-3.5 text-blue-500" />
          ) : isVideoTool ? (
            <Film className="h-3.5 w-3.5 text-violet-500" />
          ) : isCarouselTool ? (
            <Layers className="h-3.5 w-3.5 text-pink-500" />
          ) : (
            <Wrench className="h-3 w-3 text-primary" />
          )}
          <span className="font-semibold">
            {isImageTool
              ? "AI Image Generator"
              : isPptTool
              ? "PowerPoint Deck Creator"
              : isWordTool
              ? "Word Document Creator"
              : isVideoTool
              ? "Text-to-Video Reel"
              : isCarouselTool
              ? "Social Media Carousel"
              : "Tool used"}
            :
          </span>
          <Badge
            variant="outline"
            className={cn(
              "px-1.5 py-0 text-[10px] font-mono",
              isImageTool && "bg-pink-500/10 text-pink-500 border-pink-500/30",
              isPptTool && "bg-orange-500/10 text-orange-500 border-orange-500/30",
              isWordTool && "bg-blue-500/10 text-blue-500 border-blue-500/30",
              isVideoTool && "bg-violet-500/10 text-violet-400 border-violet-500/30",
              isCarouselTool && "bg-pink-500/10 text-pink-400 border-pink-500/30"
            )}
          >
            {toolCall.name}
          </Badge>
          {open ? <ChevronDown className="h-3 w-3 ml-1" /> : <ChevronRight className="h-3 w-3 ml-1" />}
        </button>

        {imageUrl && (
          <a
            href={imageUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-[11px] text-pink-500 hover:text-pink-400 underline font-medium"
          >
            <ImageIcon className="h-3 w-3" />
            <span>View Image</span>
          </a>
        )}

        {videoUrl && (
          <a
            href={videoUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-[11px] text-violet-400 hover:text-violet-300 underline font-medium"
          >
            <Film className="h-3 w-3" />
            <span>Watch Video</span>
          </a>
        )}

        {carouselSlides && carouselSlides.length > 0 && (
          <span className="flex items-center gap-1 text-[11px] text-pink-400 font-medium">
            <Layers className="h-3 w-3" />
            <span>{carouselSlides.length} Slides</span>
          </span>
        )}

        {fileUrl && (
          <a
            href={fileUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={cn(
              "flex items-center gap-1 text-[11px] font-medium underline",
              isPptTool ? "text-orange-500 hover:text-orange-400" : "text-blue-500 hover:text-blue-400"
            )}
          >
            <Download className="h-3 w-3" />
            <span>Download {isPptTool ? ".pptx" : ".docx"}</span>
          </a>
        )}
      </div>

      {open && (
        <div className="mt-2 p-3 rounded-lg bg-background/90 border border-border/40 text-[11px] font-mono space-y-2">
          <div>
            <span className="text-muted-foreground font-semibold">Arguments: </span>
            <code>{JSON.stringify(toolCall.arguments, null, 2)}</code>
          </div>
          {toolCall.result && (
            <div>
              <span className="text-muted-foreground font-semibold">Result: </span>
              <code>{JSON.stringify(toolCall.result, null, 2)}</code>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ImageCard({ src, alt }: { src: string; alt: string }) {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);
  const [isZoomed, setIsZoomed] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

  const cleanTitle = alt || "AI Generated Visual";

  const handleDownload = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsDownloading(true);
    try {
      const resp = await fetch(src, { mode: "cors" });
      if (!resp.ok) throw new Error("Network fetch failed");
      const blob = await resp.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      const safeName = cleanTitle.replace(/[^a-z0-9]/gi, "_").toLowerCase().slice(0, 32);
      link.download = `${safeName || "ai_generated_visual"}.jpg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    } catch {
      window.open(src, "_blank");
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <>
      <div className="my-3 overflow-hidden rounded-xl border border-border/60 bg-card/60 backdrop-blur shadow-md max-w-lg transition-all hover:border-primary/40 hover:shadow-lg group">
        <div
          onClick={() => !error && setIsZoomed(true)}
          className="relative min-h-[260px] max-h-[460px] bg-muted/40 flex items-center justify-center overflow-hidden cursor-pointer"
        >
          {!loaded && !error && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2.5 bg-muted/60 text-muted-foreground text-xs animate-pulse">
              <div className="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
              <span className="font-medium">Generating high-res visual...</span>
            </div>
          )}

          {error ? (
            <div className="flex flex-col items-center justify-center p-6 text-center text-xs text-muted-foreground space-y-2">
              <ImageIcon className="h-8 w-8 text-muted-foreground/60" />
              <p>Unable to display image preview directly.</p>
              <Button
                variant="outline"
                size="sm"
                className="text-xs gap-1.5"
                onClick={(e) => {
                  e.stopPropagation();
                  window.open(src, "_blank");
                }}
              >
                <ExternalLink className="h-3 w-3" />
                Open External Link
              </Button>
            </div>
          ) : (
            <img
              src={src}
              alt={cleanTitle}
              loading="lazy"
              onLoad={() => setLoaded(true)}
              onError={() => setError(true)}
              className={cn(
                "w-full h-auto max-h-[460px] object-cover transition-all duration-300 group-hover:scale-[1.01]",
                !loaded && "opacity-0"
              )}
            />
          )}

          {loaded && !error && (
            <div className="absolute top-2.5 right-2.5 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity bg-black/60 backdrop-blur-md p-1 rounded-lg">
              <Button
                size="icon"
                variant="ghost"
                className="h-7 w-7 text-white hover:bg-white/20 hover:text-white"
                onClick={handleDownload}
                title="Download full-resolution image"
                disabled={isDownloading}
              >
                <Download className="h-3.5 w-3.5" />
              </Button>
              <Button
                size="icon"
                variant="ghost"
                className="h-7 w-7 text-white hover:bg-white/20 hover:text-white"
                onClick={(e) => {
                  e.stopPropagation();
                  window.open(src, "_blank");
                }}
                title="Open in new tab"
              >
                <ExternalLink className="h-3.5 w-3.5" />
              </Button>
              <Button
                size="icon"
                variant="ghost"
                className="h-7 w-7 text-white hover:bg-white/20 hover:text-white"
                onClick={() => setIsZoomed(true)}
                title="Zoom view"
              >
                <Maximize2 className="h-3.5 w-3.5" />
              </Button>
            </div>
          )}
        </div>

        <div className="px-3.5 py-2.5 bg-background/80 border-t border-border/40 flex items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-1.5 truncate">
            <Sparkles className="h-3 w-3 text-pink-500 shrink-0" />
            <span className="font-medium text-foreground/90 truncate">{cleanTitle}</span>
          </div>
          <Button
            size="sm"
            variant="ghost"
            onClick={handleDownload}
            className="h-7 px-2 text-xs text-muted-foreground hover:text-foreground shrink-0 gap-1"
          >
            <Download className="h-3 w-3" />
            <span>Download</span>
          </Button>
        </div>
      </div>

      {isZoomed && (
        <div
          className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200"
          onClick={() => setIsZoomed(false)}
        >
          <div
            className="relative max-w-5xl max-h-[90vh] flex flex-col items-center"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="absolute -top-10 right-0 flex items-center gap-2">
              <Button
                size="sm"
                variant="secondary"
                onClick={handleDownload}
                className="h-8 text-xs gap-1.5 bg-white/20 hover:bg-white/30 text-white border-0"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Save Image</span>
              </Button>
              <Button
                size="icon"
                variant="secondary"
                onClick={() => setIsZoomed(false)}
                className="h-8 w-8 rounded-full bg-white/20 hover:bg-white/30 text-white border-0"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <img
              src={src}
              alt={cleanTitle}
              className="max-w-full max-h-[85vh] object-contain rounded-lg shadow-2xl"
            />
            <p className="mt-3 text-white/80 text-xs font-medium tracking-wide text-center">
              {cleanTitle}
            </p>
          </div>
        </div>
      )}
    </>
  );
}

function DocumentCard({ href, title }: { href: string; title: string }) {
  const isPpt = href.endsWith(".pptx") || title.toLowerCase().includes("presentation") || title.toLowerCase().includes("pptx");
  const isWord = href.endsWith(".docx") || title.toLowerCase().includes("document") || title.toLowerCase().includes(".docx");

  const cleanTitle = title
    .replace(/^📥?\s*Download\s*(?:Presentation|Document|PPTX|DOCX)?:?\s*/i, "")
    .replace(/\.(pptx|docx|pdf)$/i, "");

  return (
    <div className="my-3 p-3.5 rounded-xl border border-border/60 bg-background/80 hover:border-border transition-all shadow-sm max-w-md flex items-center justify-between gap-3 group">
      <div className="flex items-center gap-3 min-w-0">
        <div
          className={cn(
            "h-10 w-10 rounded-lg flex items-center justify-center shrink-0 shadow-inner",
            isPpt
              ? "bg-gradient-to-br from-orange-500 to-amber-600 text-white"
              : isWord
              ? "bg-gradient-to-br from-blue-600 to-cyan-600 text-white"
              : "bg-gradient-to-br from-emerald-600 to-teal-600 text-white"
          )}
        >
          {isPpt ? (
            <Presentation className="h-5 w-5" />
          ) : isWord ? (
            <FileText className="h-5 w-5" />
          ) : (
            <FileDown className="h-5 w-5" />
          )}
        </div>

        <div className="min-w-0">
          <div className="flex items-center gap-1.5">
            <Badge
              variant="outline"
              className={cn(
                "px-1.5 py-0 text-[9px] font-bold tracking-wider uppercase",
                isPpt
                  ? "bg-orange-500/10 text-orange-500 border-orange-500/30"
                  : isWord
                  ? "bg-blue-500/10 text-blue-500 border-blue-500/30"
                  : "bg-emerald-500/10 text-emerald-500 border-emerald-500/30"
              )}
            >
              {isPpt ? "PPTX DECK" : isWord ? "WORD DOC" : "DOCUMENT"}
            </Badge>
          </div>
          <p className="font-semibold text-xs text-foreground truncate mt-0.5">
            {cleanTitle || "Generated Document"}
          </p>
        </div>
      </div>

      <a
        href={href}
        download
        target="_blank"
        rel="noopener noreferrer"
        className={cn(
          "px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shrink-0 shadow-sm",
          isPpt
            ? "bg-orange-500 hover:bg-orange-600 text-white"
            : isWord
            ? "bg-blue-600 hover:bg-blue-700 text-white"
            : "bg-emerald-600 hover:bg-emerald-700 text-white"
        )}
      >
        <Download className="h-3.5 w-3.5" />
        <span>Download</span>
      </a>
    </div>
  );
}

function MessageContent({ content, isUser }: { content: string; isUser?: boolean }) {
  const pattern = /(```[\s\S]*?```|!\[[^\]]*\]\([^)]+\)|\[[^\]]+\]\([^)]+\)|`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g;
  const parts = content.split(pattern);

  return (
    <>
      {parts.map((part, i) => {
        if (!part) return null;

        // Code block
        if (part.startsWith("```") && part.endsWith("```")) {
          const lines = part.slice(3, -3);
          const firstNewline = lines.indexOf("\n");
          const code = firstNewline > -1 ? lines.slice(firstNewline + 1) : lines;
          return (
            <pre
              key={i}
              className="my-2.5 rounded-xl bg-background/60 border border-border/40 p-3.5 overflow-x-auto text-xs font-mono"
            >
              <code>{code}</code>
            </pre>
          );
        }

        // Markdown Image: ![alt](url)
        const imgMatch = part.match(/^!\[([^\]]*)\]\(([^)]+)\)$/);
        if (imgMatch) {
          const altText = imgMatch[1];
          const imgSrc = imgMatch[2];
          return <ImageCard key={i} src={imgSrc} alt={altText} />;
        }

        // Markdown Link: [text](url)
        const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
        if (linkMatch) {
          const linkText = linkMatch[1];
          const linkHref = linkMatch[2];

          // Check if link is a video (.mp4 or /static/videos/)
          const isVideoLink = linkHref.includes(".mp4") || linkHref.includes("/static/videos/");
          if (isVideoLink) {
            return (
              <VideoPlayerCard
                key={i}
                video={{
                  video_url: linkHref,
                  title: linkText.replace(/^🎬?\s*(?:Watch\s*\/?\s*Download\s*Video:?\s*)?/i, ""),
                }}
              />
            );
          }

          // Check if link is a generated document (.pptx, .docx, .pdf, or Download Document)
          const isDocLink =
            linkHref.includes(".pptx") ||
            linkHref.includes(".docx") ||
            linkHref.includes(".pdf") ||
            linkText.toLowerCase().includes("download") ||
            linkText.toLowerCase().includes("presentation") ||
            linkText.toLowerCase().includes("document");

          if (isDocLink) {
            return <DocumentCard key={i} href={linkHref} title={linkText} />;
          }

          return (
            <a
              key={i}
              href={linkHref}
              target="_blank"
              rel="noopener noreferrer"
              className={cn(
                "underline underline-offset-2 font-medium transition-colors inline-flex items-center gap-0.5",
                isUser ? "text-white hover:text-white/80" : "text-primary hover:text-primary/80"
              )}
            >
              {linkText}
              <ExternalLink className="h-3 w-3 inline ml-0.5" />
            </a>
          );
        }

        // Inline code
        if (part.startsWith("`") && part.endsWith("`")) {
          return (
            <code
              key={i}
              className="rounded bg-background/40 px-1.5 py-0.5 text-xs font-mono border border-border/30"
            >
              {part.slice(1, -1)}
            </code>
          );
        }

        // Bold
        if (part.startsWith("**") && part.endsWith("**")) {
          return <strong key={i} className="font-semibold">{part.slice(2, -2)}</strong>;
        }

        // Italic
        if (part.startsWith("*") && part.endsWith("*")) {
          return <em key={i}>{part.slice(1, -1)}</em>;
        }

        return <span key={i}>{part}</span>;
      })}
    </>
  );
}

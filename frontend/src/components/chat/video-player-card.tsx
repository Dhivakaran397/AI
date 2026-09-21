"use client";

import { useState, useRef } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Film,
  Download,
  ExternalLink,
  Maximize2,
  X,
  Layers,
  Copy,
  Check,
} from "lucide-react";

export interface VideoScene {
  headline: string;
  subtitle?: string;
  duration?: number;
}

export interface VideoData {
  video_id?: string;
  title?: string;
  format?: "reels_vertical" | "landscape_16_9" | string;
  duration?: number;
  scenes_count?: number;
  video_url: string;
  download_url?: string;
  scenes?: VideoScene[];
}

interface VideoPlayerCardProps {
  video: VideoData;
  className?: string;
}

export function VideoPlayerCard({ video, className }: VideoPlayerCardProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isZoomed, setIsZoomed] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [showScenes, setShowScenes] = useState(false);
  const [copied, setCopied] = useState(false);
  const [hasError, setHasError] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const isVertical = video.format !== "landscape_16_9";
  const title = video.title || "AI Generated Video";
  const durationText = video.duration ? `${Math.round(video.duration)}s` : "Video";
  const scenesCount = video.scenes?.length || video.scenes_count || 0;

  const handleDownload = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsDownloading(true);
    try {
      const resp = await fetch(video.video_url);
      if (!resp.ok) throw new Error("Download failed");
      const blob = await resp.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      const safeName = title.replace(/[^a-z0-9]/gi, "_").toLowerCase().slice(0, 32);
      link.download = `${safeName || "ai_video"}.mp4`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch {
      window.open(video.video_url, "_blank");
    } finally {
      setIsDownloading(false);
    }
  };

  const handleCopyLink = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(video.video_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <>
      <div
        className={cn(
          "my-3 overflow-hidden rounded-2xl border border-border/60 bg-card/75 backdrop-blur-md shadow-lg transition-all hover:border-primary/40 group",
          isVertical ? "max-w-sm" : "max-w-xl",
          className
        )}
      >
        {/* Header Bar */}
        <div className="px-3.5 py-2.5 bg-background/80 border-b border-border/40 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center text-white shrink-0 shadow-sm">
              <Film className="h-3.5 w-3.5" />
            </div>
            <div className="min-w-0">
              <p className="font-semibold text-xs text-foreground truncate">{title}</p>
              <div className="flex items-center gap-1.5 mt-0.5">
                <Badge
                  variant="outline"
                  className="px-1.5 py-0 text-[9px] font-mono bg-violet-500/10 text-violet-400 border-violet-500/30 uppercase"
                >
                  {isVertical ? "9:16 Reel" : "16:9 Landscape"}
                </Badge>
                <span className="text-[10px] text-muted-foreground font-mono">
                  {durationText}
                </span>
                {scenesCount > 0 && (
                  <span className="text-[10px] text-muted-foreground font-mono">
                    • {scenesCount} scenes
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1 shrink-0">
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7 text-muted-foreground hover:text-foreground"
              onClick={handleCopyLink}
              title="Copy video link"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
            </Button>
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7 text-muted-foreground hover:text-foreground"
              onClick={() => setIsZoomed(true)}
              title="Fullscreen preview"
            >
              <Maximize2 className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>

        {/* Video Player Display */}
        <div
          className={cn(
            "relative bg-black flex items-center justify-center overflow-hidden",
            isVertical ? "aspect-[9/16] max-h-[460px]" : "aspect-video"
          )}
        >
          {hasError ? (
            <div className="flex flex-col items-center justify-center p-6 text-center text-xs text-muted-foreground space-y-2">
              <Film className="h-8 w-8 text-violet-400/60" />
              <p>Video ready to play or download</p>
              <Button
                variant="outline"
                size="sm"
                className="text-xs gap-1.5"
                onClick={() => window.open(video.video_url, "_blank")}
              >
                <ExternalLink className="h-3 w-3" />
                Open in New Tab
              </Button>
            </div>
          ) : (
            <video
              ref={videoRef}
              src={video.video_url}
              playsInline
              controls
              preload="metadata"
              onError={() => setHasError(true)}
              className="w-full h-full object-contain"
            />
          )}

          {/* Controls overlay overlaying top-right for quick actions */}
          <div className="absolute top-2.5 right-2.5 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity bg-black/60 backdrop-blur-md p-1 rounded-lg pointer-events-auto">
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7 text-white hover:bg-white/20"
              onClick={handleDownload}
              title="Download MP4"
              disabled={isDownloading}
            >
              <Download className="h-3.5 w-3.5" />
            </Button>
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7 text-white hover:bg-white/20"
              onClick={(e) => {
                e.stopPropagation();
                window.open(video.video_url, "_blank");
              }}
              title="Open video in new tab"
            >
              <ExternalLink className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>

        {/* Bottom Actions & Scenes Accordion */}
        <div className="px-3.5 py-2.5 bg-background/90 border-t border-border/40 space-y-2 text-xs">
          <div className="flex items-center justify-between gap-2">
            <Button
              size="sm"
              variant="default"
              onClick={handleDownload}
              disabled={isDownloading}
              className="h-7 px-3 text-xs bg-violet-600 hover:bg-violet-700 text-white font-medium gap-1.5 shadow-sm"
            >
              <Download className="h-3.5 w-3.5" />
              <span>{isDownloading ? "Saving..." : "Download MP4"}</span>
            </Button>

            {video.scenes && video.scenes.length > 0 && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setShowScenes(!showScenes)}
                className="h-7 px-2 text-xs text-muted-foreground hover:text-foreground gap-1"
              >
                <Layers className="h-3.5 w-3.5 text-violet-400" />
                <span>Scenes ({video.scenes.length})</span>
              </Button>
            )}
          </div>

          {/* Scenes Breakdown Drawer */}
          {showScenes && video.scenes && video.scenes.length > 0 && (
            <div className="mt-2 pt-2 border-t border-border/40 space-y-1.5 animate-in fade-in-50 duration-200">
              <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                Storyline & Scenes
              </p>
              <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                {video.scenes.map((sc, idx) => (
                  <div
                    key={idx}
                    className="p-2 rounded-lg bg-muted/40 border border-border/30 flex items-start gap-2 text-xs"
                  >
                    <span className="font-mono text-[10px] text-violet-400 font-bold px-1.5 py-0.5 rounded bg-violet-500/10 shrink-0">
                      {idx + 1}
                    </span>
                    <div className="min-w-0">
                      <p className="font-medium text-foreground truncate">{sc.headline}</p>
                      {sc.subtitle && (
                        <p className="text-muted-foreground text-[11px] line-clamp-2 mt-0.5">
                          {sc.subtitle}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Fullscreen Video Modal */}
      {isZoomed && (
        <div
          className="fixed inset-0 z-50 bg-black/95 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200"
          onClick={() => setIsZoomed(false)}
        >
          <div
            className="relative max-w-4xl max-h-[92vh] flex flex-col items-center"
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
                <span>Download MP4</span>
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
            <video
              src={video.video_url}
              playsInline
              controls
              autoPlay
              className={cn(
                "rounded-xl shadow-2xl max-h-[85vh] object-contain",
                isVertical ? "aspect-[9/16] max-w-sm" : "aspect-video max-w-4xl"
              )}
            />
            <p className="mt-3 text-white/80 text-xs font-medium tracking-wide text-center">
              {title}
            </p>
          </div>
        </div>
      )}
    </>
  );
}

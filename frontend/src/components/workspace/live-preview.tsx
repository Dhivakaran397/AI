"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api-client";
import type { PreviewUrlResponse, ProcessInfo, FileContentResponse } from "@/types";
import {
  Monitor,
  Tablet,
  Smartphone,
  RotateCw,
  ExternalLink,
  Play,
  Loader2,
  Globe,
  AlertCircle,
  Wifi,
  WifiOff,
} from "lucide-react";

interface LivePreviewProps {
  projectId: string;
  projectName?: string;
  onLaunchDevServer?: () => void;
}

type ViewportMode = "desktop" | "tablet" | "mobile";

export function LivePreview({
  projectId,
  projectName,
  onLaunchDevServer,
}: LivePreviewProps) {
  const [viewport, setViewport] = useState<ViewportMode>("desktop");
  const [url, setUrl] = useState<string>("");
  const [isActive, setIsActive] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isStartingServer, setIsStartingServer] = useState<boolean>(false);
  const [reloadKey, setReloadKey] = useState<number>(0);
  const [customUrl, setCustomUrl] = useState<string>("");
  const [htmlDoc, setHtmlDoc] = useState<string | null>(null);

  const iframeRef = useRef<HTMLIFrameElement>(null);

  const fetchHtmlDoc = useCallback(async () => {
    try {
      const res = await apiClient.get<FileContentResponse | null>(
        `/projects/${projectId}/files/content?path=index.html&optional=true`
      );
      if (res && res.content) {
        setHtmlDoc(res.content);
      } else {
        setHtmlDoc(null);
      }
    } catch {
      setHtmlDoc(null);
    }
  }, [projectId]);

  const checkPreviewStatus = useCallback(async () => {
    try {
      const res = await apiClient.get<PreviewUrlResponse>(
        `/projects/${projectId}/preview/url`
      );
      if (res.is_active && res.url) {
        setIsActive(true);
        setUrl(res.url);
        if (!customUrl) setCustomUrl(res.url);
      } else {
        setIsActive(false);
      }
    } catch (err) {
      console.error("Failed to check preview status:", err);
      setIsActive(false);
    } finally {
      setIsLoading(false);
    }
  }, [projectId, customUrl]);

  useEffect(() => {
    checkPreviewStatus();
    fetchHtmlDoc();
    const interval = setInterval(checkPreviewStatus, 5000);
    return () => clearInterval(interval);
  }, [checkPreviewStatus, fetchHtmlDoc, reloadKey]);

  const handleStartDevServer = async () => {
    try {
      setIsStartingServer(true);
      await apiClient.post<ProcessInfo>(`/projects/${projectId}/processes`, {
        command: "npm run dev",
        port: 3000,
      });
      setTimeout(checkPreviewStatus, 1500);
      if (onLaunchDevServer) onLaunchDevServer();
    } catch (err) {
      console.error("Failed to start dev server:", err);
    } finally {
      setIsStartingServer(false);
    }
  };

  const handleReload = () => {
    setReloadKey((prev) => prev + 1);
  };

  const isHtmlPreview = !isActive && Boolean(htmlDoc);
  const activeUrl = customUrl || url;
  const displayUrl = isHtmlPreview
    ? "index.html (Live HTML Preview)"
    : activeUrl || "Dev server offline";

  const handleOpenExternal = () => {
    if (isHtmlPreview && htmlDoc) {
      const blob = new Blob([htmlDoc], { type: "text/html" });
      const blobUrl = URL.createObjectURL(blob);
      window.open(blobUrl, "_blank");
    } else if (activeUrl) {
      window.open(activeUrl, "_blank");
    }
  };

  return (
    <div className="flex flex-col h-full bg-background border-r border-border overflow-hidden">
      {/* Preview Header & Controls */}
      <div className="flex items-center justify-between px-3 py-2 border-b bg-muted/30 shrink-0 gap-2">
        {/* Left: Status & URL Bar */}
        <div className="flex items-center gap-2 flex-1 max-w-xl min-w-0">
          <div
            className="flex items-center gap-1.5 shrink-0"
            title={isActive ? "Dev server active" : isHtmlPreview ? "Static HTML preview active" : "Dev server offline"}
          >
            {isActive || isHtmlPreview ? (
              <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            ) : (
              <span className="flex h-2 w-2 rounded-full bg-muted-foreground/50" />
            )}
            <Badge
              variant="outline"
              className={`text-[10px] px-1.5 py-0 font-mono ${
                isActive || isHtmlPreview
                  ? "text-emerald-500 border-emerald-500/30"
                  : "text-muted-foreground"
              }`}
            >
              {isActive ? "LIVE SERVER" : isHtmlPreview ? "HTML PREVIEW" : "OFFLINE"}
            </Badge>
          </div>

          <div className="relative flex-1 min-w-0">
            <Globe className="absolute left-2 top-2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              value={customUrl ? customUrl : displayUrl}
              onChange={(e) => setCustomUrl(e.target.value)}
              placeholder="http://localhost:3000"
              className="h-7 pl-7 pr-7 text-xs font-mono bg-background"
            />
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-0.5 top-0.5 h-6 w-6 text-muted-foreground hover:text-foreground"
              onClick={handleReload}
              title="Refresh preview"
            >
              <RotateCw className="h-3 w-3" />
            </Button>
          </div>
        </div>

        {/* Right: Viewport Controls & External Open */}
        <div className="flex items-center gap-1 shrink-0">
          <div className="flex items-center rounded-md border p-0.5 bg-background">
            <Button
              variant={viewport === "desktop" ? "secondary" : "ghost"}
              size="icon"
              className="h-6 w-6"
              onClick={() => setViewport("desktop")}
              title="Desktop View (100%)"
            >
              <Monitor className="h-3 w-3" />
            </Button>
            <Button
              variant={viewport === "tablet" ? "secondary" : "ghost"}
              size="icon"
              className="h-6 w-6"
              onClick={() => setViewport("tablet")}
              title="Tablet View (768px)"
            >
              <Tablet className="h-3 w-3" />
            </Button>
            <Button
              variant={viewport === "mobile" ? "secondary" : "ghost"}
              size="icon"
              className="h-6 w-6"
              onClick={() => setViewport("mobile")}
              title="Mobile View (375px)"
            >
              <Smartphone className="h-3 w-3" />
            </Button>
          </div>

          <Button
            variant="outline"
            size="icon"
            className="h-7 w-7 text-muted-foreground hover:text-foreground"
            onClick={handleOpenExternal}
            disabled={!isActive && !htmlDoc}
            title="Open preview in new browser tab"
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* Main Preview Container */}
      <div className="flex-1 bg-muted/20 overflow-auto flex items-center justify-center p-4">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center gap-2 text-muted-foreground">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <span className="text-xs">Checking preview server...</span>
          </div>
        ) : !isActive && !htmlDoc ? (
          <div className="flex flex-col items-center justify-center max-w-sm text-center p-6 rounded-xl border bg-card/80 backdrop-blur shadow-sm space-y-4">
            <div className="p-3 rounded-full bg-muted">
              <WifiOff className="h-8 w-8 text-muted-foreground" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-foreground">
                No Active Dev Server
              </h4>
              <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                Launch a local development server for {projectName || "your project"} to inspect your app in real time with responsive viewport toggles.
              </p>
            </div>

            <Button
              size="sm"
              className="text-xs gap-1.5"
              onClick={handleStartDevServer}
              disabled={isStartingServer}
            >
              {isStartingServer ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Play className="h-3.5 w-3.5" />
              )}
              Start Dev Server (npm run dev)
            </Button>
          </div>
        ) : (
          <div
            className={`h-full transition-all duration-300 flex flex-col items-center justify-center ${
              viewport === "desktop"
                ? "w-full"
                : viewport === "tablet"
                ? "w-[768px] max-w-full rounded-lg border shadow-lg overflow-hidden bg-background my-auto h-[95%]"
                : "w-[375px] max-w-full rounded-2xl border-4 border-muted-foreground/30 shadow-2xl overflow-hidden bg-background my-auto h-[95%]"
            }`}
          >
            {viewport !== "desktop" && (
              <div className="w-full bg-muted py-1 px-3 text-[10px] text-muted-foreground flex items-center justify-between border-b shrink-0 font-mono">
                <span>{viewport === "tablet" ? "iPad Mini (768 × 1024)" : "iPhone (375 × 812)"}</span>
                <span className="truncate max-w-[150px]">{isHtmlPreview ? "index.html" : activeUrl}</span>
              </div>
            )}
            <iframe
              ref={iframeRef}
              key={`${reloadKey}-${isHtmlPreview ? "html" : "url"}`}
              src={isHtmlPreview ? undefined : activeUrl}
              srcDoc={isHtmlPreview && htmlDoc ? htmlDoc : undefined}
              title="Live Project Preview"
              className="w-full flex-1 border-0 bg-background"
              sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
            />
          </div>
        )}
      </div>
    </div>
  );
}

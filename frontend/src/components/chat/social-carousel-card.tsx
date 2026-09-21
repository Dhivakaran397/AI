"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Layers,
  ChevronLeft,
  ChevronRight,
  Download,
  ExternalLink,
  Maximize2,
  X,
  Share2,
  Copy,
  Check,
  Sparkles,
  CheckCircle2,
} from "lucide-react";

export interface CarouselSlide {
  slide_number: number;
  title: string;
  description: string;
  bullet_points?: string[];
  image_url: string;
}

export interface CarouselData {
  carousel_id?: string;
  title?: string;
  platform?: "instagram" | "linkedin" | string;
  total_slides?: number;
  slides: CarouselSlide[];
  preview_image_url?: string;
}

interface SocialCarouselCardProps {
  carousel: CarouselData;
  className?: string;
}

export function SocialCarouselCard({ carousel, className }: SocialCarouselCardProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isZoomed, setIsZoomed] = useState(false);
  const [isDownloadingAll, setIsDownloadingAll] = useState(false);
  const [copied, setCopied] = useState(false);

  const slides = carousel.slides || [];
  const currentSlide = slides[currentIndex] || slides[0];
  const total = slides.length;
  const title = carousel.title || "Social Media Carousel";
  const platform = carousel.platform || "instagram";

  if (!slides || slides.length === 0) {
    return null;
  }

  const prevSlide = () => {
    setCurrentIndex((prev) => (prev > 0 ? prev - 1 : total - 1));
  };

  const nextSlide = () => {
    setCurrentIndex((prev) => (prev < total - 1 ? prev + 1 : 0));
  };

  const handleDownloadSingle = async (url: string, slideNum: number) => {
    try {
      const resp = await fetch(url);
      if (!resp.ok) throw new Error("Fetch failed");
      const blob = await resp.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      const safeTitle = title.replace(/[^a-z0-9]/gi, "_").toLowerCase().slice(0, 24);
      link.download = `${safeTitle}_slide_${slideNum}.jpg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    } catch {
      window.open(url, "_blank");
    }
  };

  const handleDownloadAll = async () => {
    setIsDownloadingAll(true);
    try {
      for (let i = 0; i < slides.length; i++) {
        await handleDownloadSingle(slides[i].image_url, slides[i].slide_number || i + 1);
        // Small pause between multiple downloads so browser doesn't block them
        await new Promise((r) => setTimeout(r, 280));
      }
    } finally {
      setIsDownloadingAll(false);
    }
  };

  const handleCopyLink = () => {
    if (currentSlide?.image_url) {
      navigator.clipboard.writeText(currentSlide.image_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <>
      <div
        className={cn(
          "my-3 overflow-hidden rounded-2xl border border-border/60 bg-card/75 backdrop-blur-md shadow-lg transition-all hover:border-primary/40 max-w-md group",
          className
        )}
      >
        {/* Header Bar */}
        <div className="px-3.5 py-2.5 bg-background/80 border-b border-border/40 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-pink-500 to-rose-600 flex items-center justify-center text-white shrink-0 shadow-sm">
              <Layers className="h-3.5 w-3.5" />
            </div>
            <div className="min-w-0">
              <p className="font-semibold text-xs text-foreground truncate">{title}</p>
              <div className="flex items-center gap-1.5 mt-0.5">
                <Badge
                  variant="outline"
                  className={cn(
                    "px-1.5 py-0 text-[9px] font-mono uppercase",
                    platform === "linkedin"
                      ? "bg-blue-500/10 text-blue-400 border-blue-500/30"
                      : "bg-pink-500/10 text-pink-400 border-pink-500/30"
                  )}
                >
                  {platform} Carousel
                </Badge>
                <span className="text-[10px] text-muted-foreground font-mono">
                  Slide {currentIndex + 1} of {total}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1 shrink-0">
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7 text-muted-foreground hover:text-foreground"
              onClick={handleCopyLink}
              title="Copy slide link"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
            </Button>
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7 text-muted-foreground hover:text-foreground"
              onClick={() => setIsZoomed(true)}
              title="Zoom view"
            >
              <Maximize2 className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>

        {/* Swipeable / Navigable Slide View */}
        <div className="relative aspect-square bg-muted/40 overflow-hidden flex items-center justify-center select-none">
          <img
            src={currentSlide.image_url}
            alt={currentSlide.title || `Slide ${currentIndex + 1}`}
            className="w-full h-full object-cover transition-all duration-300"
            onClick={() => setIsZoomed(true)}
          />

          {/* Navigation Arrows */}
          {total > 1 && (
            <>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  prevSlide();
                }}
                className="absolute left-2.5 top-1/2 -translate-y-1/2 h-8 w-8 rounded-full bg-black/60 hover:bg-black/80 text-white backdrop-blur flex items-center justify-center transition-all opacity-80 hover:opacity-100 hover:scale-105 shadow-md"
                aria-label="Previous slide"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  nextSlide();
                }}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 h-8 w-8 rounded-full bg-black/60 hover:bg-black/80 text-white backdrop-blur flex items-center justify-center transition-all opacity-80 hover:opacity-100 hover:scale-105 shadow-md"
                aria-label="Next slide"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </>
          )}

          {/* Top-right quick actions */}
          <div className="absolute top-2.5 right-2.5 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity bg-black/60 backdrop-blur-md p-1 rounded-lg">
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7 text-white hover:bg-white/20"
              onClick={(e) => {
                e.stopPropagation();
                handleDownloadSingle(currentSlide.image_url, currentIndex + 1);
              }}
              title="Download this slide"
            >
              <Download className="h-3.5 w-3.5" />
            </Button>
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7 text-white hover:bg-white/20"
              onClick={(e) => {
                e.stopPropagation();
                window.open(currentSlide.image_url, "_blank");
              }}
              title="Open slide in new tab"
            >
              <ExternalLink className="h-3.5 w-3.5" />
            </Button>
          </div>

          {/* Slide Indicator Dots */}
          {total > 1 && (
            <div className="absolute bottom-3 left-0 right-0 flex items-center justify-center gap-1.5 pointer-events-none">
              <div className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-black/60 backdrop-blur-md pointer-events-auto">
                {slides.map((_, idx) => (
                  <button
                    key={idx}
                    onClick={(e) => {
                      e.stopPropagation();
                      setCurrentIndex(idx);
                    }}
                    className={cn(
                      "h-1.5 rounded-full transition-all duration-200",
                      idx === currentIndex ? "w-4 bg-white" : "w-1.5 bg-white/40 hover:bg-white/70"
                    )}
                    aria-label={`Go to slide ${idx + 1}`}
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Current Slide Details Panel */}
        <div className="px-3.5 py-2.5 bg-background/90 border-t border-border/40 space-y-2 text-xs">
          <div className="space-y-1">
            <div className="flex items-center justify-between gap-2">
              <span className="font-semibold text-foreground truncate">
                {currentSlide.title || `Slide ${currentIndex + 1}`}
              </span>
              <span className="font-mono text-[10px] text-muted-foreground shrink-0">
                {currentIndex + 1} / {total}
              </span>
            </div>
            {currentSlide.description && (
              <p className="text-muted-foreground text-[11px] leading-relaxed line-clamp-2">
                {currentSlide.description}
              </p>
            )}
          </div>

          {/* Bullet points if any */}
          {currentSlide.bullet_points && currentSlide.bullet_points.length > 0 && (
            <div className="pt-1.5 border-t border-border/30 space-y-1">
              {currentSlide.bullet_points.map((pt, pIdx) => (
                <div key={pIdx} className="flex items-start gap-1.5 text-[11px] text-foreground/85">
                  <CheckCircle2 className="h-3 w-3 text-pink-500 shrink-0 mt-0.5" />
                  <span className="line-clamp-1">{pt}</span>
                </div>
              ))}
            </div>
          )}

          {/* Action Buttons */}
          <div className="pt-1.5 border-t border-border/40 flex items-center justify-between gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleDownloadSingle(currentSlide.image_url, currentIndex + 1)}
              className="h-7 px-2.5 text-xs text-foreground/80 hover:text-foreground gap-1.5"
            >
              <Download className="h-3 w-3" />
              <span>Download Slide</span>
            </Button>

            <Button
              size="sm"
              variant="default"
              onClick={handleDownloadAll}
              disabled={isDownloadingAll}
              className="h-7 px-3 text-xs bg-pink-600 hover:bg-pink-700 text-white font-medium gap-1.5 shadow-sm"
            >
              <Download className="h-3 w-3" />
              <span>{isDownloadingAll ? "Saving..." : `Download All (${total})`}</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Fullscreen Zoom Modal */}
      {isZoomed && (
        <div
          className="fixed inset-0 z-50 bg-black/95 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200"
          onClick={() => setIsZoomed(false)}
        >
          <div
            className="relative max-w-2xl max-h-[92vh] flex flex-col items-center"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="absolute -top-10 right-0 flex items-center gap-2">
              <Button
                size="sm"
                variant="secondary"
                onClick={() => handleDownloadSingle(currentSlide.image_url, currentIndex + 1)}
                className="h-8 text-xs gap-1.5 bg-white/20 hover:bg-white/30 text-white border-0"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Save Slide {currentIndex + 1}</span>
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

            <div className="relative flex items-center justify-center">
              <img
                src={currentSlide.image_url}
                alt={currentSlide.title}
                className="max-w-full max-h-[80vh] object-contain rounded-xl shadow-2xl"
              />

              {total > 1 && (
                <>
                  <button
                    onClick={prevSlide}
                    className="absolute left-3 top-1/2 -translate-y-1/2 h-10 w-10 rounded-full bg-black/70 hover:bg-black text-white flex items-center justify-center shadow-lg"
                  >
                    <ChevronLeft className="h-5 w-5" />
                  </button>
                  <button
                    onClick={nextSlide}
                    className="absolute right-3 top-1/2 -translate-y-1/2 h-10 w-10 rounded-full bg-black/70 hover:bg-black text-white flex items-center justify-center shadow-lg"
                  >
                    <ChevronRight className="h-5 w-5" />
                  </button>
                </>
              )}
            </div>

            <p className="mt-3 text-white/80 text-xs font-medium tracking-wide text-center">
              {currentSlide.title} — Slide {currentIndex + 1} of {total}
            </p>
          </div>
        </div>
      )}
    </>
  );
}

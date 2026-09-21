"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Send } from "lucide-react";

export function AIInput() {
  const [value, setValue] = useState("");
  const router = useRouter();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!value.trim()) return;
    // Navigate to chat with the prompt
    const encoded = encodeURIComponent(value.trim());
    router.push(`/chat?prompt=${encoded}`);
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <Input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Ask DAI anything or describe what you want to build..."
        className="h-14 pr-14 text-base rounded-xl bg-muted/50 border-muted-foreground/20 focus-visible:ring-primary/30"
      />
      <Button
        type="submit"
        size="icon"
        className="absolute right-2 top-1/2 -translate-y-1/2 h-10 w-10 rounded-lg"
        disabled={!value.trim()}
      >
        <Send className="h-4 w-4" />
      </Button>
    </form>
  );
}

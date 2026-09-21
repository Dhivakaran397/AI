"use client";

import { useRouter } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { EXAMPLE_PROMPTS } from "@/lib/constants";

export function QuickPrompts() {
  const router = useRouter();

  const handleClick = (prompt: string) => {
    const encoded = encodeURIComponent(prompt);
    router.push(`/chat?prompt=${encoded}`);
  };

  return (
    <div className="flex flex-wrap gap-2">
      {EXAMPLE_PROMPTS.map((prompt) => (
        <Badge
          key={prompt}
          variant="secondary"
          className="cursor-pointer hover:bg-accent transition-colors py-1.5 px-3 text-sm font-normal"
          onClick={() => handleClick(prompt)}
        >
          {prompt}
        </Badge>
      ))}
    </div>
  );
}

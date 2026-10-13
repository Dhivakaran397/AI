"use client";

import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { ThemeToggle } from "./theme-toggle";
import { InstallPwaButton } from "./install-pwa-button";
import { Button } from "@/components/ui/button";
import { RotateCw } from "lucide-react";

interface HeaderProps {
  title?: string;
}

export function Header({ title }: HeaderProps) {
  return (
    <header className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
      <SidebarTrigger className="-ml-1" />
      <Separator orientation="vertical" className="mr-2 h-4" />
      {title && (
        <h1 className="text-sm font-medium">{title}</h1>
      )}
      <div className="ml-auto flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-muted-foreground hover:text-foreground cursor-pointer"
          onClick={() => window.location.reload()}
          title="Reload Window (Ctrl+R)"
        >
          <RotateCw className="h-4 w-4" />
        </Button>
        <InstallPwaButton />
        <ThemeToggle />
      </div>
    </header>
  );
}

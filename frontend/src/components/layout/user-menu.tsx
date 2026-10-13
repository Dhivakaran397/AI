"use client";

import { useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import {
  SignInButton,
  SignUpButton,
  UserButton,
  useUser,
} from "@clerk/nextjs";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { SidebarMenuButton } from "@/components/ui/sidebar";
import { Moon, Sun, Settings, ChevronUp, LogIn, UserPlus } from "lucide-react";
import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api-client";

export function UserMenu() {
  const { user, isLoaded, isSignedIn } = useUser();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const { theme, resolvedTheme, setTheme } = useTheme();

  useEffect(() => {
    setMounted(true);
  }, []);

  const currentTheme = mounted ? resolvedTheme || theme || "dark" : "dark";
  const isDark = currentTheme === "dark";

  const handleToggleTheme = () => {
    const next = isDark ? "light" : "dark";
    setTheme(next);
    apiClient.put("/api/v1/settings", { theme: next }).catch(() => {});
  };

  const fullName = user?.fullName || user?.username || "DAI User";
  const email = user?.primaryEmailAddress?.emailAddress || "";
  const initials = fullName
    ? fullName
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "U";

  return (
    <div className="w-full">
      {isSignedIn ? (
        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <SidebarMenuButton
                size="lg"
                className="data-[state=open]:bg-sidebar-accent w-full"
              />
            }
          >
            <Avatar className="h-8 w-8">
              {user?.imageUrl ? (
                <AvatarImage src={user.imageUrl} alt={fullName} />
              ) : null}
              <AvatarFallback className="text-xs bg-primary/20 text-primary">
                {initials}
              </AvatarFallback>
            </Avatar>
            <div className="flex flex-col gap-0.5 leading-none group-data-[collapsible=icon]:hidden text-left min-w-0">
              <span className="font-medium text-sm truncate">{fullName}</span>
              <span className="text-xs text-muted-foreground truncate">
                {email}
              </span>
            </div>
            <ChevronUp className="ml-auto h-4 w-4 group-data-[collapsible=icon]:hidden shrink-0" />
          </DropdownMenuTrigger>
          <DropdownMenuContent side="top" align="start" className="w-56">
            <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
              Clerk Account
            </div>
            <div className="p-2 border-b border-border/50 flex items-center gap-3">
              <UserButton
                appearance={{
                  elements: {
                    userButtonAvatarBox: "h-9 w-9",
                  },
                }}
              />
              <div className="flex flex-col min-w-0">
                <span className="text-xs font-medium truncate">{fullName}</span>
                <span className="text-[10px] text-muted-foreground truncate">
                  Manage profile
                </span>
              </div>
            </div>
            <DropdownMenuItem onClick={handleToggleTheme}>
              {isDark ? (
                <Sun className="mr-2 h-4 w-4 text-amber-400" />
              ) : (
                <Moon className="mr-2 h-4 w-4 text-indigo-500" />
              )}
              {isDark ? "Light Mode" : "Dark Mode"}
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => router.push("/settings")}>
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ) : (
        <div className="flex flex-col gap-2 p-2 group-data-[collapsible=icon]:p-0">
          <SignInButton mode="modal">
            <Button size="sm" className="w-full justify-start gap-2 h-8 text-xs">
              <LogIn className="h-3.5 w-3.5" />
              <span className="group-data-[collapsible=icon]:hidden">Sign In</span>
            </Button>
          </SignInButton>
          <SignUpButton mode="modal">
            <Button
              size="sm"
              variant="outline"
              className="w-full justify-start gap-2 h-8 text-xs group-data-[collapsible=icon]:hidden"
            >
              <UserPlus className="h-3.5 w-3.5" />
              <span>Create Account</span>
            </Button>
          </SignUpButton>
        </div>
      )}
    </div>
  );
}

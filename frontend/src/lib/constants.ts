import {
  Home,
  MessageSquare,
  FolderKanban,
  Layout,
  Bot,
  BookOpen,
  CheckSquare,
  Files,
  Brain,
  Activity,
  Settings,
  type LucideIcon,
} from "lucide-react";
import type { ChatMode } from "@/types/chat";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface NavItem {
  title: string;
  href: string;
  icon: LucideIcon;
  badge?: string;
}

export const NAV_ITEMS: NavItem[] = [
  { title: "Home", href: "/", icon: Home },
  { title: "Chat", href: "/chat", icon: MessageSquare },
  { title: "Projects", href: "/projects", icon: FolderKanban },
  { title: "Agents", href: "/agents", icon: Bot },
  { title: "Workspace", href: "/workspace", icon: Layout },
  { title: "Knowledge", href: "/knowledge", icon: BookOpen },
  { title: "Tasks", href: "/tasks", icon: CheckSquare },
  { title: "Files", href: "/files", icon: Files },
  { title: "Memory", href: "/memory", icon: Brain },
  { title: "Activity", href: "/activity", icon: Activity },
  { title: "Settings", href: "/settings", icon: Settings },
];

export const CHAT_MODES: { value: ChatMode; label: string; color: string }[] = [
  { value: "CHAT", label: "Chat", color: "bg-blue-500" },
  { value: "IMAGE", label: "Image", color: "bg-pink-500" },
  { value: "RESEARCH", label: "Research", color: "bg-purple-500" },
  { value: "BUILD", label: "Build", color: "bg-green-500" },
  { value: "AGENT", label: "Agent", color: "bg-orange-500" },
  { value: "ANALYZE", label: "Analyze", color: "bg-cyan-500" },
];

export const EXAMPLE_PROMPTS = [
  "Build me a website",
  "Create an AI application",
  "Research this topic",
  "Analyze this file",
  "Fix my project",
  "Create a business plan",
  "Explain this concept",
  "Start a new project",
];

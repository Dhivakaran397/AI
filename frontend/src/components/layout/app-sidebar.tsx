"use client";

import { useRouter, usePathname } from "next/navigation";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarSeparator,
} from "@/components/ui/sidebar";
import { Badge } from "@/components/ui/badge";
import { NAV_ITEMS } from "@/lib/constants";
import { Zap } from "lucide-react";
import { UserMenu } from "./user-menu";

export function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <Sidebar collapsible="icon" variant="sidebar">
      <SidebarHeader className="p-4">
        <button
          type="button"
          onClick={() => router.push("/")}
          className="flex items-center gap-2 group-data-[collapsible=icon]:justify-center text-left bg-transparent border-none p-0 cursor-pointer outline-none"
        >
          <img
            src="/dai_logo.png"
            alt="DAI Logo"
            className="h-8 w-8 rounded-full object-contain shadow-sm"
          />
          <span className="text-lg font-bold group-data-[collapsible=icon]:hidden">
            DAI
          </span>
        </button>
      </SidebarHeader>
      <SidebarSeparator />
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {NAV_ITEMS.map((item) => {
                const isActive =
                  pathname === item.href ||
                  (item.href !== "/" && pathname.startsWith(item.href));
                return (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton
                      onClick={() => router.push(item.href)}
                      isActive={isActive}
                      tooltip={item.title}
                      className="cursor-pointer"
                    >
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                      {item.badge && (
                        <Badge
                          variant="secondary"
                          className="ml-auto text-[10px] px-1.5 py-0"
                        >
                          {item.badge}
                        </Badge>
                      )}
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <UserMenu />
      </SidebarFooter>
    </Sidebar>
  );
}

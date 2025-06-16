"use client"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Settings, MessageSquare, Search, FileText, Pin, Home, ChevronLeft, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"

interface SidebarProps {
  activeView: string
  setActiveView: (view: string) => void
  collapsed: boolean
  setCollapsed: (collapsed: boolean) => void
}

export function Sidebar({ activeView, setActiveView, collapsed, setCollapsed }: SidebarProps) {
  // Empty pinned digests - no data available
  const pinnedDigests: any[] = []

  const menuItems = [
    { id: "digest", label: "Digest Viewer", icon: Home, badge: null },
    { id: "settings", label: "Settings", icon: Settings, badge: null },
    { id: "search", label: "Search", icon: Search, badge: null },
    { id: "notion", label: "Notion Sync", icon: FileText, badge: "New" },
    { id: "feedback", label: "Feedback", icon: MessageSquare, badge: null },
  ]

  return (
    <div
      className={cn(
        "fixed left-0 top-0 h-full glass-card transition-all duration-300 z-50",
        collapsed ? "w-16" : "w-64",
      )}
    >
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="p-4 border-b border-white/20">
          <div className="flex items-center justify-between">
            {!collapsed && <h1 className="text-xl font-bold accent-text">Meetings</h1>}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setCollapsed(!collapsed)}
              className="hover:bg-white/20"
              aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
            </Button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {menuItems.map((item) => (
            <Button
              key={item.id}
              variant={activeView === item.id ? "secondary" : "ghost"}
              className={cn(
                "w-full justify-start hover:bg-white/20 transition-colors",
                collapsed ? "px-2" : "px-4",
                activeView === item.id && "bg-blue-600/20 text-blue-600 dark:text-blue-400",
              )}
              onClick={() => setActiveView(item.id)}
              aria-label={item.label}
            >
              <item.icon className={cn("h-4 w-4", collapsed ? "" : "mr-3")} />
              {!collapsed && (
                <>
                  <span className="flex-1 text-left">{item.label}</span>
                  {item.badge && (
                    <Badge variant="secondary" className="ml-2 text-xs">
                      {item.badge}
                    </Badge>
                  )}
                </>
              )}
            </Button>
          ))}
        </nav>

        {/* Pinned Digests - Empty State */}
        {!collapsed && (
          <div className="p-4 border-t border-white/20">
            <div className="flex items-center mb-3">
              <Pin className="h-4 w-4 mr-2 text-yellow-500" />
              <span className="text-sm font-medium">Pinned</span>
            </div>
            <div className="text-center py-4">
              <Pin className="h-8 w-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
              <p className="text-xs text-gray-500 dark:text-gray-400">No pinned digests yet</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

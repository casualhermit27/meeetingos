"use client"

import { useState } from "react"
import { Sidebar } from "@/components/sidebar"
import { TopBar } from "@/components/top-bar"
import { DigestViewer } from "@/components/digest-viewer"
import { SettingsPanel } from "@/components/settings-panel"
import { FeedbackInterface } from "@/components/feedback-interface"
import { SearchInterface } from "@/components/search-interface"
import { NotionViewer } from "@/components/notion-viewer"

export function Dashboard() {
  const [activeView, setActiveView] = useState("digest")
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const renderActiveView = () => {
    switch (activeView) {
      case "settings":
        return <SettingsPanel />
      case "feedback":
        return <FeedbackInterface />
      case "search":
        return <SearchInterface />
      case "notion":
        return <NotionViewer />
      default:
        return <DigestViewer />
    }
  }

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-gray-950 relative overflow-hidden">
      {/* Subtle background pattern */}
      <div className="absolute inset-0 bg-blue-50/30 dark:bg-blue-950/10 pointer-events-none" />

      <Sidebar
        activeView={activeView}
        setActiveView={setActiveView}
        collapsed={sidebarCollapsed}
        setCollapsed={setSidebarCollapsed}
      />

      <div
        className={`flex-1 flex flex-col transition-all duration-300 ${sidebarCollapsed ? "ml-16" : "ml-64"} relative z-10`}
      >
        <TopBar onToggleSidebar={() => setSidebarCollapsed(!sidebarCollapsed)} onViewChange={setActiveView} />

        <main className="flex-1 overflow-auto p-8 custom-scrollbar">{renderActiveView()}</main>
      </div>
    </div>
  )
}

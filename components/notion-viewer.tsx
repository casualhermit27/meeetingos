"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { useToast } from "@/hooks/use-toast"
import { FileText, ExternalLink, Loader2, CheckCircle, AlertCircle, RefreshCw, Download } from "lucide-react"

export function NotionViewer() {
  const { toast } = useToast()
  const [connected, setConnected] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [viewMode, setViewMode] = useState<"notion" | "markdown">("markdown")
  const [syncing, setSyncing] = useState(false)

  const handleConnect = async () => {
    setConnecting(true)
    // Simulate OAuth flow
    await new Promise((resolve) => setTimeout(resolve, 2000))
    setConnected(true)
    setConnecting(false)
    toast({
      title: "Connected to Notion",
      description: "Your workspace has been successfully linked.",
    })
  }

  const handleSync = async () => {
    setSyncing(true)
    await new Promise((resolve) => setTimeout(resolve, 1500))
    setSyncing(false)
    toast({
      title: "Sync completed",
      description: "Latest meeting data has been synced to Notion.",
    })
  }

  // Empty notion pages - no data available
  const mockNotionPages: any[] = []

  const emptyMarkdownContent = `# Daily Digest - January 16, 2025

## Meeting Summary

*No meetings recorded yet. Connect your integrations to start capturing meeting data.*

## Action Items

*Action items will appear here once meetings are processed.*

## Next Steps
- Connect your Zoom, Slack, or Google Calendar
- Upload your first meeting recording
- Review generated summaries and action items`

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Refined header */}
      <div className="text-center space-y-3">
        <h1 className="text-4xl font-light accent-text">Notion Integration</h1>
        <p className="text-xl text-gray-600 dark:text-gray-400 font-light">Sync meeting digests with your workspace</p>
      </div>

      {/* Enhanced connection status */}
      <div className="floating-card p-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <div className="p-4 rounded-2xl bg-gray-50 dark:bg-gray-800">
              <FileText className="h-8 w-8 text-gray-600 dark:text-gray-400" />
            </div>
            <div className="space-y-2">
              <h2 className="text-2xl font-medium text-gray-900 dark:text-gray-100">Notion Workspace</h2>
              <p className="text-gray-600 dark:text-gray-400">Connect your workspace to sync meeting data</p>
              {connected && (
                <div className="space-y-1">
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">Workspace: Company Team</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Ready to sync content</p>
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <Badge
              variant={connected ? "default" : "secondary"}
              className={`px-4 py-2 rounded-full font-medium ${
                connected
                  ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                  : "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
              }`}
            >
              {connected ? <CheckCircle className="h-4 w-4 mr-2" /> : <AlertCircle className="h-4 w-4 mr-2" />}
              {connected ? "Connected" : "Not Connected"}
            </Badge>

            <div className="flex space-x-3">
              {connected && (
                <Button
                  variant="outline"
                  onClick={handleSync}
                  disabled={syncing}
                  className="px-6 py-3 rounded-xl border-2 hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:border-blue-300 dark:hover:border-blue-600 transition-all duration-300"
                >
                  {syncing ? (
                    <>
                      <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                      Syncing...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="h-5 w-5 mr-2" />
                      Sync Now
                    </>
                  )}
                </Button>
              )}
              <Button
                onClick={handleConnect}
                disabled={connecting || connected}
                className={`px-6 py-3 rounded-xl transition-all duration-300 ${
                  connected
                    ? "bg-gray-200 text-gray-500 cursor-not-allowed"
                    : "bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl"
                }`}
              >
                {connecting ? (
                  <>
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                    Connecting...
                  </>
                ) : connected ? (
                  "Connected"
                ) : (
                  "Connect Notion"
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Enhanced view toggle */}
      <div className="floating-card p-8">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <h3 className="text-xl font-medium text-gray-900 dark:text-gray-100">View Mode</h3>
            <p className="text-gray-600 dark:text-gray-400">Choose how you want to view your meeting digests</p>
          </div>

          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-3">
              <Switch
                checked={viewMode === "notion"}
                onCheckedChange={(checked) => setViewMode(checked ? "notion" : "markdown")}
                disabled={!connected}
                className="data-[state=checked]:bg-blue-600"
              />
              <Label className="text-base font-medium text-gray-900 dark:text-gray-100">
                {viewMode === "notion" ? "Notion View" : "Markdown View"}
              </Label>
            </div>
            <Badge variant="outline" className="px-3 py-1 rounded-full border-gray-300 dark:border-gray-600">
              {viewMode === "notion" ? "Live Notion Pages" : "Formatted Text"}
            </Badge>
          </div>
        </div>
      </div>

      {/* Enhanced content display */}
      {viewMode === "notion" && connected ? (
        <div className="space-y-6">
          <h2 className="text-2xl font-medium text-gray-900 dark:text-gray-100">Synced Notion Pages</h2>
          {mockNotionPages.length === 0 ? (
            <div className="floating-card p-12">
              <div className="text-center space-y-4">
                <div className="w-16 h-16 mx-auto rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                  <FileText className="h-8 w-8 text-gray-400" />
                </div>
                <div>
                  <h3 className="text-xl font-medium text-gray-900 dark:text-gray-100 mb-2">No synced pages yet</h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    Pages will appear here once you have meeting content to sync to Notion.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {mockNotionPages.map((page) => (
                <div key={page.id} className="floating-card p-8 hover:shadow-2xl transition-all duration-500 group">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="p-3 rounded-2xl bg-gray-100 dark:bg-gray-800 group-hover:scale-110 transition-transform duration-300">
                        <FileText className="h-6 w-6 text-gray-600 dark:text-gray-400" />
                      </div>
                      <div className="space-y-1">
                        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                          {page.title}
                        </h3>
                        <p className="text-gray-600 dark:text-gray-400">Last modified: {page.lastModified}</p>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      className="px-6 py-3 rounded-xl border-2 hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:border-blue-300 dark:hover:border-blue-600 transition-all duration-300"
                    >
                      <ExternalLink className="h-5 w-5 mr-2" />
                      Open in Notion
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="floating-card overflow-hidden">
          <div className="flex items-center justify-between p-8 border-b border-gray-200/50 dark:border-gray-700/50">
            <div className="space-y-1">
              <h2 className="text-2xl font-medium text-gray-900 dark:text-gray-100">Meeting Digest</h2>
              <p className="text-gray-600 dark:text-gray-400">
                Formatted view of your meeting summaries and action items
              </p>
            </div>
            <Button
              variant="outline"
              className="px-6 py-3 rounded-xl border-2 hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:border-blue-300 dark:hover:border-blue-600 transition-all duration-300"
              disabled={mockNotionPages.length === 0}
            >
              <Download className="h-5 w-5 mr-2" />
              Export
            </Button>
          </div>
          <div className="p-8">
            <div className="prose dark:prose-invert max-w-none prose-lg">
              <pre className="whitespace-pre-wrap leading-relaxed text-gray-700 dark:text-gray-300 bg-gray-50/50 dark:bg-gray-800/50 rounded-2xl p-6 border border-gray-200/50 dark:border-gray-700/50">
                {emptyMarkdownContent}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* Enhanced integration settings */}
      {connected && (
        <div className="floating-card p-8">
          <div className="space-y-6">
            <div>
              <h3 className="text-2xl font-medium text-gray-900 dark:text-gray-100 mb-2">Sync Settings</h3>
              <p className="text-gray-600 dark:text-gray-400">Configure how meeting data is synced to Notion</p>
            </div>

            <div className="space-y-6">
              {[
                {
                  title: "Auto-sync new meetings",
                  description: "Automatically create Notion pages for new meetings",
                  defaultChecked: true,
                },
                {
                  title: "Include action items",
                  description: "Add action items as tasks in Notion",
                  defaultChecked: true,
                },
                {
                  title: "Sync recordings",
                  description: "Include links to meeting recordings",
                  defaultChecked: false,
                },
              ].map((setting, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between py-4 border-b border-gray-200/50 dark:border-gray-700/50 last:border-b-0"
                >
                  <div className="space-y-1">
                    <h4 className="text-lg font-medium text-gray-900 dark:text-gray-100">{setting.title}</h4>
                    <p className="text-gray-600 dark:text-gray-400">{setting.description}</p>
                  </div>
                  <Switch defaultChecked={setting.defaultChecked} className="data-[state=checked]:bg-blue-600" />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

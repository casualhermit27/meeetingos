"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/hooks/use-toast"
import { Calendar, MessageSquare, Video, CheckCircle, AlertCircle, Save, Loader2 } from "lucide-react"

export function SettingsPanel() {
  const { toast } = useToast()
  const [saving, setSaving] = useState(false)
  const [settings, setSettings] = useState({
    notifications: true,
    digestTime: "09:00",
    zoomPath: "~/Zoom",
    integrations: {
      zoom: { connected: true, status: "Connected" },
      slack: { connected: false, status: "Not Connected" },
      calendar: { connected: true, status: "Connected" },
    },
  })

  const handleSave = async () => {
    setSaving(true)
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000))
    setSaving(false)
    toast({
      title: "Settings saved",
      description: "Your preferences have been updated successfully.",
    })
  }

  const handleConnect = (integration: string) => {
    // Simulate OAuth flow
    toast({
      title: `Connecting to ${integration}...`,
      description: "Opening OAuth flow in new window.",
    })
  }

  const integrations = [
    {
      id: "zoom",
      name: "Zoom",
      description: "Connect to sync meeting recordings and transcripts",
      icon: Video,
      color: "blue",
    },
    {
      id: "slack",
      name: "Slack",
      description: "Get notifications and feedback in your workspace",
      icon: MessageSquare,
      color: "purple",
    },
    {
      id: "calendar",
      name: "Google Calendar",
      description: "Sync meeting schedules and create follow-up events",
      icon: Calendar,
      color: "green",
    },
  ]

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header with better typography */}
      <div className="text-center space-y-3">
        <h1 className="text-4xl font-light accent-text">Settings</h1>
        <p className="text-lg text-gray-600 dark:text-gray-400 font-light">Configure your workspace preferences</p>
      </div>

      {/* Integrations with refined cards */}
      <div className="space-y-6">
        <h2 className="text-2xl font-light text-gray-800 dark:text-gray-200 mb-6">Integrations</h2>
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
          {integrations.map((integration) => {
            const config = settings.integrations[integration.id as keyof typeof settings.integrations]
            const Icon = integration.icon

            return (
              <div
                key={integration.id}
                className="floating-card p-8 hover:shadow-3xl transition-all duration-500 group"
              >
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div
                      className={`p-4 rounded-2xl bg-${integration.color}-50 dark:bg-${integration.color}-900/20 group-hover:scale-110 transition-transform duration-300`}
                    >
                      <Icon className={`h-8 w-8 text-${integration.color}-600 dark:text-${integration.color}-400`} />
                    </div>
                    <Badge
                      variant={config.connected ? "default" : "secondary"}
                      className={`px-4 py-2 rounded-full font-medium ${config.connected ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" : "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"}`}
                    >
                      {config.connected ? (
                        <CheckCircle className="h-4 w-4 mr-2" />
                      ) : (
                        <AlertCircle className="h-4 w-4 mr-2" />
                      )}
                      {config.status}
                    </Badge>
                  </div>

                  <div className="space-y-2">
                    <h3 className="text-xl font-medium text-gray-900 dark:text-gray-100">{integration.name}</h3>
                    <p className="text-gray-600 dark:text-gray-400 leading-relaxed">{integration.description}</p>
                  </div>

                  <Button
                    onClick={() => handleConnect(integration.name)}
                    variant={config.connected ? "outline" : "default"}
                    className={`w-full py-3 rounded-xl font-medium transition-all duration-300 ${
                      config.connected
                        ? "border-2 hover:bg-gray-50 dark:hover:bg-gray-800"
                        : "bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl"
                    }`}
                    disabled={config.connected}
                  >
                    {config.connected ? "Connected" : "Connect"}
                  </Button>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Preferences with cleaner design */}
      <div className="space-y-6">
        <h2 className="text-2xl font-light text-gray-800 dark:text-gray-200">Preferences</h2>
        <div className="floating-card p-8 space-y-8">
          {/* Notifications */}
          <div className="flex items-center justify-between py-4 border-b border-gray-200/50 dark:border-gray-700/50 last:border-b-0">
            <div className="space-y-2">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Notifications</h3>
              <p className="text-gray-600 dark:text-gray-400">Receive alerts for action items and new recordings</p>
            </div>
            <Switch
              checked={settings.notifications}
              onCheckedChange={(checked) => setSettings((prev) => ({ ...prev, notifications: checked }))}
              className="data-[state=checked]:bg-blue-600"
            />
          </div>

          {/* Digest Time */}
          <div className="space-y-4 py-4 border-b border-gray-200/50 dark:border-gray-700/50 last:border-b-0">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Daily Digest Time</h3>
            <Select
              value={settings.digestTime}
              onValueChange={(value) => setSettings((prev) => ({ ...prev, digestTime: value }))}
            >
              <SelectTrigger className="w-full h-12 rounded-xl border-2 border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50">
                <SelectValue placeholder="Select delivery time" />
              </SelectTrigger>
              <SelectContent className="rounded-xl border-2 bg-white/90 dark:bg-gray-900/90 backdrop-blur-xl">
                <SelectItem value="08:00" className="rounded-lg">
                  8:00 AM
                </SelectItem>
                <SelectItem value="09:00" className="rounded-lg">
                  9:00 AM
                </SelectItem>
                <SelectItem value="10:00" className="rounded-lg">
                  10:00 AM
                </SelectItem>
                <SelectItem value="17:00" className="rounded-lg">
                  5:00 PM
                </SelectItem>
                <SelectItem value="18:00" className="rounded-lg">
                  6:00 PM
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Zoom Path */}
          <div className="space-y-4 py-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Zoom Recordings Path</h3>
            <Input
              value={settings.zoomPath}
              onChange={(e) => setSettings((prev) => ({ ...prev, zoomPath: e.target.value }))}
              placeholder="e.g., ~/Zoom"
              className="h-12 rounded-xl border-2 border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 focus:border-blue-500 dark:focus:border-blue-400"
            />
            <p className="text-sm text-gray-500 dark:text-gray-400">Specify where Zoom saves your recordings locally</p>
          </div>
        </div>
      </div>

      {/* Action buttons with better spacing */}
      <div className="flex justify-center space-x-6 pt-8">
        <Button
          variant="outline"
          className="px-8 py-3 rounded-xl border-2 hover:bg-gray-50 dark:hover:bg-gray-800 transition-all duration-300"
        >
          Reset Defaults
        </Button>
        <Button
          onClick={handleSave}
          disabled={saving}
          className="px-8 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl transition-all duration-300 min-w-[140px]"
        >
          {saving ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="mr-2 h-5 w-5" />
              Save Settings
            </>
          )}
        </Button>
      </div>
    </div>
  )
}

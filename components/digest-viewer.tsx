"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { useToast } from "@/hooks/use-toast"
import {
  Play,
  ChevronDown,
  ChevronUp,
  CalendarIcon,
  Download,
  Pin,
  MessageSquare,
  Share,
  Filter,
  Edit3,
  CheckCircle,
  Plus,
} from "lucide-react"

export function DigestViewer() {
  const { toast } = useToast()
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    recordings: true,
    summary: true,
    actions: true,
  })
  const [pinnedDigests, setPinnedDigests] = useState<string[]>([])
  const [comments, setComments] = useState<Record<string, string>>({})
  const [newComment, setNewComment] = useState("")

  // Empty arrays for data
  const recordings: any[] = []
  const actionItems: any[] = []

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }))
  }

  const togglePin = (digestId: string) => {
    setPinnedDigests((prev) => (prev.includes(digestId) ? prev.filter((id) => id !== digestId) : [...prev, digestId]))
    toast({
      title: pinnedDigests.includes(digestId) ? "Unpinned" : "Pinned",
      description: "Digest updated in sidebar",
    })
  }

  const handleExport = (format: "pdf" | "csv") => {
    toast({
      title: `Exporting as ${format.toUpperCase()}...`,
      description: "Your download will start shortly.",
    })
  }

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href)
    toast({
      title: "Link copied",
      description: "Share link copied to clipboard",
    })
  }

  const addComment = (digestId: string) => {
    if (newComment.trim()) {
      setComments((prev) => ({
        ...prev,
        [digestId]: newComment,
      }))
      setNewComment("")
      toast({
        title: "Comment added",
        description: "Your comment has been saved",
      })
    }
  }

  const EmptyState = ({
    icon: Icon,
    title,
    description,
    actionText,
    onAction,
  }: {
    icon: any
    title: string
    description: string
    actionText?: string
    onAction?: () => void
  }) => (
    <div className="text-center py-12">
      <div className="w-16 h-16 mx-auto rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
        <Icon className="h-8 w-8 text-gray-400" />
      </div>
      <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">{title}</h3>
      <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">{description}</p>
      {actionText && onAction && (
        <Button onClick={onAction} className="bg-blue-600 hover:bg-blue-700 text-white">
          <Plus className="h-4 w-4 mr-2" />
          {actionText}
        </Button>
      )}
    </div>
  )

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Refined header */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-4xl font-light accent-text">Daily Digest</h1>
          <p className="text-xl text-gray-600 dark:text-gray-400 font-light">January 16, 2025</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button
            variant="ghost"
            size="sm"
            className="rounded-xl px-4 py-2 hover:bg-white/50 dark:hover:bg-gray-800/50"
            disabled={recordings.length === 0 && actionItems.length === 0}
          >
            <Filter className="h-4 w-4 mr-2" />
            Filter
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="rounded-xl px-4 py-2 hover:bg-white/50 dark:hover:bg-gray-800/50"
            onClick={() => togglePin("today")}
            disabled={recordings.length === 0 && actionItems.length === 0}
          >
            <Pin className={`h-4 w-4 mr-2 ${pinnedDigests.includes("today") ? "text-yellow-500" : ""}`} />
            Pin
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="rounded-xl px-4 py-2 hover:bg-white/50 dark:hover:bg-gray-800/50"
            onClick={handleShare}
            disabled={recordings.length === 0 && actionItems.length === 0}
          >
            <Share className="h-4 w-4 mr-2" />
            Share
          </Button>
          <Select
            onValueChange={(value) => handleExport(value as "pdf" | "csv")}
            disabled={recordings.length === 0 && actionItems.length === 0}
          >
            <SelectTrigger className="w-32 rounded-xl border-2 bg-white/50 dark:bg-gray-800/50">
              <Download className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Export" />
            </SelectTrigger>
            <SelectContent className="rounded-xl bg-white/90 dark:bg-gray-900/90 backdrop-blur-xl">
              <SelectItem value="pdf" className="rounded-lg">
                Export PDF
              </SelectItem>
              <SelectItem value="csv" className="rounded-lg">
                Export CSV
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Timeline with enhanced cards */}
      <div className="space-y-8">
        {/* Recordings Section */}
        <div className="floating-card overflow-hidden">
          <Collapsible open={expandedSections.recordings} onOpenChange={() => toggleSection("recordings")}>
            <CollapsibleTrigger asChild>
              <div className="cursor-pointer p-8 hover:bg-white/30 dark:hover:bg-gray-800/30 transition-all duration-300">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="p-3 rounded-2xl bg-blue-50 dark:bg-blue-900/20">
                      <Play className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <h2 className="text-2xl font-medium text-gray-900 dark:text-gray-100">Meeting Recordings</h2>
                      <p className="text-gray-600 dark:text-gray-400 mt-1">Recent meeting recordings and transcripts</p>
                    </div>
                    <Badge
                      variant="secondary"
                      className="ml-4 px-3 py-1 rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                    >
                      {recordings.length}
                    </Badge>
                  </div>
                  {expandedSections.recordings ? (
                    <ChevronUp className="h-6 w-6 text-gray-400" />
                  ) : (
                    <ChevronDown className="h-6 w-6 text-gray-400" />
                  )}
                </div>
              </div>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="px-8 pb-8">
                {recordings.length === 0 ? (
                  <EmptyState
                    icon={Play}
                    title="No recordings yet"
                    description="Your meeting recordings will appear here once you start connecting your integrations and uploading content."
                    actionText="Upload Recording"
                    onAction={() => toast({ title: "Upload feature", description: "Recording upload coming soon!" })}
                  />
                ) : (
                  <div className="grid gap-6 md:grid-cols-2">
                    {recordings.map((recording) => (
                      <div
                        key={recording.id}
                        className="minimal-card p-6 hover:shadow-2xl transition-all duration-500 group"
                      >
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex-1 space-y-2">
                            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                              {recording.title}
                            </h3>
                            <p className="text-gray-600 dark:text-gray-400">
                              {recording.date} • {recording.duration}
                            </p>
                          </div>
                          <Button
                            size="sm"
                            className="ml-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl transition-all duration-300"
                          >
                            <Play className="h-4 w-4" />
                          </Button>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {recording.participants.map((participant: string, index: number) => (
                            <Badge
                              key={index}
                              variant="outline"
                              className="text-xs px-3 py-1 rounded-full border-gray-300 dark:border-gray-600"
                            >
                              {participant}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CollapsibleContent>
          </Collapsible>
        </div>

        {/* Summary Section */}
        <div className="floating-card overflow-hidden">
          <Collapsible open={expandedSections.summary} onOpenChange={() => toggleSection("summary")}>
            <CollapsibleTrigger asChild>
              <div className="cursor-pointer p-8 hover:bg-white/30 dark:hover:bg-gray-800/30 transition-all duration-300">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="p-3 rounded-2xl bg-purple-50 dark:bg-purple-900/20">
                      <MessageSquare className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                    </div>
                    <div>
                      <h2 className="text-2xl font-medium text-gray-900 dark:text-gray-100">Meeting Summary</h2>
                      <p className="text-gray-600 dark:text-gray-400 mt-1">Key insights and decisions</p>
                    </div>
                  </div>
                  {expandedSections.summary ? (
                    <ChevronUp className="h-6 w-6 text-gray-400" />
                  ) : (
                    <ChevronDown className="h-6 w-6 text-gray-400" />
                  )}
                </div>
              </div>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="px-8 pb-8">
                <EmptyState
                  icon={MessageSquare}
                  title="No summaries yet"
                  description="Meeting summaries with key discussion points and decisions will be automatically generated from your recordings."
                />
              </div>
            </CollapsibleContent>
          </Collapsible>
        </div>

        {/* Action Items Section with refined table */}
        <div className="floating-card overflow-hidden">
          <Collapsible open={expandedSections.actions} onOpenChange={() => toggleSection("actions")}>
            <CollapsibleTrigger asChild>
              <div className="cursor-pointer p-8 hover:bg-white/30 dark:hover:bg-gray-800/30 transition-all duration-300">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="p-3 rounded-2xl bg-green-50 dark:bg-green-900/20">
                      <CheckCircle className="h-6 w-6 text-green-600 dark:text-green-400" />
                    </div>
                    <div>
                      <h2 className="text-2xl font-medium text-gray-900 dark:text-gray-100">Action Items</h2>
                      <p className="text-gray-600 dark:text-gray-400 mt-1">Tasks and follow-ups</p>
                    </div>
                    <Badge
                      variant="secondary"
                      className="ml-4 px-3 py-1 rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                    >
                      {actionItems.length}
                    </Badge>
                  </div>
                  {expandedSections.actions ? (
                    <ChevronUp className="h-6 w-6 text-gray-400" />
                  ) : (
                    <ChevronDown className="h-6 w-6 text-gray-400" />
                  )}
                </div>
              </div>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="px-8 pb-8">
                {actionItems.length === 0 ? (
                  <EmptyState
                    icon={CheckCircle}
                    title="No action items yet"
                    description="Action items and tasks will be automatically extracted from your meeting recordings and summaries."
                    actionText="Add Action Item"
                    onAction={() =>
                      toast({ title: "Add action item", description: "Manual action item creation coming soon!" })
                    }
                  />
                ) : (
                  <div className="bg-white/30 dark:bg-gray-800/30 rounded-2xl overflow-hidden border border-gray-200/50 dark:border-gray-700/50">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-gray-200/50 dark:border-gray-700/50 bg-gray-50/50 dark:bg-gray-800/50">
                          <TableHead className="font-medium text-gray-900 dark:text-gray-100 py-4">Task</TableHead>
                          <TableHead className="font-medium text-gray-900 dark:text-gray-100 py-4">Owner</TableHead>
                          <TableHead className="font-medium text-gray-900 dark:text-gray-100 py-4">Status</TableHead>
                          <TableHead className="font-medium text-gray-900 dark:text-gray-100 py-4">Due Date</TableHead>
                          <TableHead className="font-medium text-gray-900 dark:text-gray-100 py-4">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {actionItems.map((item) => (
                          <TableRow
                            key={item.id}
                            className="border-gray-200/50 dark:border-gray-700/50 hover:bg-white/50 dark:hover:bg-gray-800/50 transition-colors"
                          >
                            <TableCell className="py-4">
                              <div>
                                <p className="font-medium text-gray-900 dark:text-gray-100">{item.task}</p>
                                {item.linkedTasks.length > 0 && (
                                  <div className="flex flex-wrap gap-1 mt-2">
                                    {item.linkedTasks.map((task: string, index: number) => (
                                      <Badge key={index} variant="outline" className="text-xs px-2 py-1 rounded-full">
                                        {task}
                                      </Badge>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </TableCell>
                            <TableCell className="py-4 text-gray-700 dark:text-gray-300">{item.owner}</TableCell>
                            <TableCell className="py-4">
                              <div className="flex items-center space-x-2">
                                <CheckCircle className="h-4 w-4 text-green-500" />
                                <Badge className="bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400 px-3 py-1 rounded-full font-medium">
                                  {item.status.replace("-", " ")}
                                </Badge>
                              </div>
                            </TableCell>
                            <TableCell className="py-4 text-gray-700 dark:text-gray-300">{item.dueDate}</TableCell>
                            <TableCell className="py-4">
                              <div className="flex items-center space-x-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="rounded-xl border-2 hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:border-blue-300 dark:hover:border-blue-600"
                                >
                                  <CalendarIcon className="h-4 w-4 mr-1" />
                                  Schedule
                                </Button>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  className="rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800"
                                >
                                  <Edit3 className="h-4 w-4" />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </div>
            </CollapsibleContent>
          </Collapsible>
        </div>

        {/* Comments Section */}
        <div className="floating-card p-8">
          <div className="flex items-center space-x-4 mb-6">
            <div className="p-3 rounded-2xl bg-orange-50 dark:bg-orange-900/20">
              <MessageSquare className="h-6 w-6 text-orange-600 dark:text-orange-400" />
            </div>
            <h2 className="text-2xl font-medium text-gray-900 dark:text-gray-100">Comments</h2>
          </div>

          <div className="space-y-6">
            <div className="space-y-4">
              <Textarea
                placeholder="Share your thoughts on this digest..."
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                className="resize-none rounded-2xl border-2 border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 focus:border-blue-500 dark:focus:border-blue-400 min-h-[100px]"
                rows={4}
                disabled={recordings.length === 0 && actionItems.length === 0}
              />
              <div className="flex justify-end">
                <Button
                  onClick={() => addComment("today")}
                  disabled={!newComment.trim() || (recordings.length === 0 && actionItems.length === 0)}
                  className="px-6 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl transition-all duration-300"
                >
                  Add Comment
                </Button>
              </div>
            </div>

            {comments["today"] && (
              <div className="border-t border-gray-200/50 dark:border-gray-700/50 pt-6">
                <div className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-medium text-sm">
                      Y
                    </div>
                    <div>
                      <span className="font-medium text-gray-900 dark:text-gray-100">You</span>
                      <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">just now</span>
                    </div>
                  </div>
                  <p className="text-gray-700 dark:text-gray-300 ml-11 leading-relaxed">{comments["today"]}</p>
                </div>
              </div>
            )}

            {recordings.length === 0 && actionItems.length === 0 && (
              <div className="text-center py-8 border-t border-gray-200/50 dark:border-gray-700/50">
                <MessageSquare className="h-12 w-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                <p className="text-gray-500 dark:text-gray-400">
                  Comments will appear here once you have meeting content to discuss.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

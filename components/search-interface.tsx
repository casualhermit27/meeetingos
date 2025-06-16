"use client"

import { useState, useEffect } from "react"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Search, Filter } from "lucide-react"

export function SearchInterface() {
  const [query, setQuery] = useState("")
  const [filter, setFilter] = useState("all")
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  // Empty mock results - no data available
  const mockResults: any[] = []

  useEffect(() => {
    if (query.length > 2) {
      setLoading(true)
      // Simulate search delay
      const timer = setTimeout(() => {
        // Always return empty results since we have no data
        setResults([])
        setLoading(false)
      }, 300)

      return () => clearTimeout(timer)
    } else {
      setResults([])
    }
  }, [query, filter])

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Refined header */}
      <div className="text-center space-y-3">
        <h1 className="text-4xl font-light accent-text">Search</h1>
        <p className="text-xl text-gray-600 dark:text-gray-400 font-light">
          Find meetings, summaries, and action items
        </p>
      </div>

      {/* Enhanced search controls */}
      <div className="floating-card p-8">
        <div className="flex flex-col md:flex-row gap-6">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <Input
              placeholder="Search meetings, summaries, action items..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-12 h-14 text-lg rounded-2xl border-2 border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 focus:border-blue-500 dark:focus:border-blue-400 transition-all duration-300"
              autoFocus
            />
          </div>
          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger className="w-full md:w-48 h-14 rounded-2xl border-2 border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50">
              <Filter className="h-5 w-5 mr-2" />
              <SelectValue placeholder="Filter by type" />
            </SelectTrigger>
            <SelectContent className="rounded-2xl bg-white/90 dark:bg-gray-900/90 backdrop-blur-xl border-2">
              <SelectItem value="all" className="rounded-xl">
                All Results
              </SelectItem>
              <SelectItem value="recording" className="rounded-xl">
                Recordings
              </SelectItem>
              <SelectItem value="summary" className="rounded-xl">
                Summaries
              </SelectItem>
              <SelectItem value="action" className="rounded-xl">
                Action Items
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Enhanced search results */}
      {query.length > 2 && (
        <div className="space-y-6">
          {loading ? (
            <div className="floating-card p-12">
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent"></div>
                <span className="ml-4 text-lg text-gray-600 dark:text-gray-400">Searching...</span>
              </div>
            </div>
          ) : (
            <div className="floating-card p-12">
              <div className="text-center space-y-4">
                <div className="w-16 h-16 mx-auto rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                  <Search className="h-8 w-8 text-gray-400" />
                </div>
                <div>
                  <h3 className="text-xl font-medium text-gray-900 dark:text-gray-100 mb-2">
                    No content to search yet
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    Start by connecting your integrations and uploading meeting recordings to build your searchable
                    content library.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Enhanced search tips */}
      {query.length <= 2 && (
        <div className="floating-card p-8">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-medium text-gray-900 dark:text-gray-100 mb-2">Search Tips</h2>
            <p className="text-gray-600 dark:text-gray-400">Get better results with these techniques</p>
          </div>

          <div className="grid gap-8 md:grid-cols-2">
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">What you can search for:</h3>
              <ul className="space-y-3 text-gray-700 dark:text-gray-300">
                <li className="flex items-center">
                  <div className="w-2 h-2 rounded-full bg-blue-500 mr-3"></div>
                  Meeting titles and content
                </li>
                <li className="flex items-center">
                  <div className="w-2 h-2 rounded-full bg-purple-500 mr-3"></div>
                  Action item descriptions
                </li>
                <li className="flex items-center">
                  <div className="w-2 h-2 rounded-full bg-green-500 mr-3"></div>
                  Participant names
                </li>
                <li className="flex items-center">
                  <div className="w-2 h-2 rounded-full bg-orange-500 mr-3"></div>
                  Meeting summaries
                </li>
              </ul>
            </div>

            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Search examples:</h3>
              <div className="space-y-3">
                {['"budget planning"', '"John Doe action items"', '"Q4 roadmap"', '"design team meeting"'].map(
                  (example) => (
                    <button
                      key={example}
                      onClick={() => setQuery(example.replace(/"/g, ""))}
                      className="block w-full text-left px-4 py-2 rounded-xl bg-white dark:bg-gray-800 hover:bg-blue-50 dark:hover:bg-blue-900/20 border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600 transition-colors text-gray-700 dark:text-gray-300"
                    >
                      {example}
                    </button>
                  ),
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

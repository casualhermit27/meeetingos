"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/hooks/use-toast"
import { Star, Send, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

export function FeedbackInterface() {
  const { toast } = useToast()
  const [rating, setRating] = useState(0)
  const [hoveredRating, setHoveredRating] = useState(0)
  const [feedback, setFeedback] = useState("")
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async () => {
    if (rating === 0) {
      toast({
        title: "Rating required",
        description: "Please provide a rating before submitting.",
        variant: "destructive",
      })
      return
    }

    setSubmitting(true)

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000))

    setSubmitting(false)
    setRating(0)
    setFeedback("")

    toast({
      title: "Feedback submitted",
      description: "Thank you for your feedback! We appreciate your input.",
    })
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Refined header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-light accent-text">Share Your Feedback</h1>
        <p className="text-xl text-gray-600 dark:text-gray-400 font-light">
          Help us create a better meeting experience
        </p>
      </div>

      {/* Main feedback card */}
      <div className="floating-card p-10">
        <div className="space-y-8">
          {/* Star Rating */}
          <div className="text-center space-y-6">
            <div>
              <h2 className="text-2xl font-medium text-gray-900 dark:text-gray-100 mb-2">Rate Your Experience</h2>
              <p className="text-gray-600 dark:text-gray-400">
                How would you rate the meeting digest and action item tracking?
              </p>
            </div>

            <div className="flex items-center justify-center space-x-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  className="p-2 rounded-full transition-all duration-300 hover:bg-white/50 dark:hover:bg-gray-800/50 hover:scale-110 focus:outline-none focus:ring-4 focus:ring-blue-500/20"
                  onClick={() => setRating(star)}
                  onMouseEnter={() => setHoveredRating(star)}
                  onMouseLeave={() => setHoveredRating(0)}
                  aria-label={`Rate ${star} star${star !== 1 ? "s" : ""}`}
                >
                  <Star
                    className={cn(
                      "h-10 w-10 transition-all duration-300",
                      hoveredRating >= star || rating >= star
                        ? "fill-yellow-400 text-yellow-400 drop-shadow-lg"
                        : "text-gray-300 dark:text-gray-600 hover:text-yellow-300",
                    )}
                  />
                </button>
              ))}
            </div>

            {rating > 0 && (
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-2xl p-4">
                <p className="text-gray-700 dark:text-gray-300 font-medium">
                  {rating === 1 && "We'd love to hear how we can improve"}
                  {rating === 2 && "Thanks for the feedback - we'll work on it"}
                  {rating === 3 && "Good to know - any specific suggestions?"}
                  {rating === 4 && "Great! What made it work well for you?"}
                  {rating === 5 && "Fantastic! We're thrilled you love it"}
                </p>
              </div>
            )}
          </div>

          {/* Feedback Text */}
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">Tell us more</h3>
              <p className="text-gray-600 dark:text-gray-400">
                Share your thoughts, suggestions, or any issues you encountered
              </p>
            </div>

            <Textarea
              placeholder="Your feedback helps us improve the experience for everyone..."
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              className="min-h-[120px] resize-none rounded-2xl border-2 border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 focus:border-blue-500 dark:focus:border-blue-400 text-base leading-relaxed"
              maxLength={500}
            />

            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-500 dark:text-gray-400">Optional but appreciated</span>
              <span className="text-gray-500 dark:text-gray-400">{feedback.length}/500</span>
            </div>
          </div>

          {/* Submit Button */}
          <div className="text-center pt-4">
            <Button
              onClick={handleSubmit}
              disabled={submitting || rating === 0}
              className="px-12 py-4 text-lg rounded-2xl bg-blue-600 hover:bg-blue-700 text-white shadow-xl hover:shadow-2xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <>
                  <Loader2 className="mr-3 h-5 w-5 animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  <Send className="mr-3 h-5 w-5" />
                  Submit Feedback
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Quick Feedback Options */}
      <div className="floating-card p-8">
        <div className="text-center mb-6">
          <h3 className="text-xl font-medium text-gray-900 dark:text-gray-100 mb-2">Quick Feedback</h3>
          <p className="text-gray-600 dark:text-gray-400">Or tap any of these common topics</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            "Meeting summaries are helpful",
            "Action items are clear",
            "Integration works well",
            "Interface is intuitive",
            "Notifications are timely",
            "Export features are useful",
          ].map((option) => (
            <Button
              key={option}
              variant="outline"
              className="h-auto p-4 text-left whitespace-normal rounded-2xl border-2 border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all duration-300"
              onClick={() => {
                toast({
                  title: "Thanks for the quick feedback!",
                  description: `"${option}" - noted!`,
                })
              }}
            >
              <span className="text-sm font-medium">{option}</span>
            </Button>
          ))}
        </div>
      </div>

      {/* Contact Information */}
      <div className="text-center">
        <div className="inline-block bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 rounded-2xl p-6">
          <p className="text-gray-600 dark:text-gray-400 mb-2">Need immediate help or have a specific issue?</p>
          <p>
            <a
              href="mailto:support@meetings.app"
              className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium transition-colors"
            >
              support@meetings.app
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}

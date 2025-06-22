"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Play, Download, Clock, CheckCircle, AlertCircle, Video, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { config, type VideoJobStatus, type VideoQuality } from "@/lib/config"

interface VideoJob extends VideoJobStatus {}

interface VideoPanelProps {
  file: File | null
  isVisible: boolean
  onVideoGenerated?: (jobId: string) => void
}

export default function VideoPanel({ file, isVisible, onVideoGenerated }: VideoPanelProps) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [currentJob, setCurrentJob] = useState<VideoJob | null>(null)
  const [quality, setQuality] = useState<VideoQuality>("low_quality")
  const [error, setError] = useState<string | null>(null)

  // Poll for job status updates
  useEffect(() => {
    if (!currentJob || currentJob.status === "completed" || currentJob.status === "failed") {
      return
    }

    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${config.VIDEO_API_URL}/jobs/${currentJob.job_id}`)
        if (response.ok) {
          const updatedJob = await response.json()
          setCurrentJob(updatedJob)
          
          if (updatedJob.status === "completed" && onVideoGenerated) {
            onVideoGenerated(updatedJob.job_id)
          }
        }
      } catch (error) {
        console.error("Error polling job status:", error)
      }
    }, 2000) // Poll every 2 seconds

    return () => clearInterval(pollInterval)
  }, [currentJob, onVideoGenerated])

  const generateVideo = async () => {
    if (!file) return

    setIsGenerating(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append("file", file)
      formData.append("quality", quality)

      const response = await fetch(`${config.VIDEO_API_URL}/generate-video-upload`, {
        method: "POST",
        body: formData,
      })

      if (response.ok) {
        const result = await response.json()
        setCurrentJob({
          job_id: result.job_id,
          status: "pending",
          created_at: new Date().toISOString(),
          quality,
          pdf_path: result.file_path,
          original_filename: file.name
        })
      } else {
        const errorData = await response.json()
        setError(errorData.detail || "Failed to start video generation")
      }
    } catch (error) {
      console.error("Error generating video:", error)
      setError("Network error. Please check your connection and try again.")
    } finally {
      setIsGenerating(false)
    }
  }

  const downloadVideo = async () => {
    if (!currentJob || currentJob.status !== "completed") return

    try {
      const response = await fetch(`${config.VIDEO_API_URL}/download/${currentJob.job_id}`)
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement("a")
        a.href = url
        a.download = `video_${currentJob.job_id}.mp4`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } else {
        setError("Failed to download video")
      }
    } catch (error) {
      console.error("Error downloading video:", error)
      setError("Failed to download video")
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "pending":
        return <Clock className="w-4 h-4 text-yellow-500" />
      case "processing":
        return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />
      case "completed":
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case "failed":
        return <AlertCircle className="w-4 h-4 text-red-500" />
      default:
        return null
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending":
        return "bg-yellow-100 text-yellow-800"
      case "processing":
        return "bg-blue-100 text-blue-800"
      case "completed":
        return "bg-green-100 text-green-800"
      case "failed":
        return "bg-red-100 text-red-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  if (!isVisible) return null

  return (
    <Card className="border-0 shadow-xl bg-white/80 backdrop-blur-sm">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <div className="p-2 bg-gradient-to-r from-purple-100 to-pink-100 rounded-lg">
            <Video className="w-5 h-5 text-purple-600" />
          </div>
          Video Generation
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {!currentJob ? (
          <>
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium text-slate-700 mb-2 block">
                  Video Quality
                </label>
                <Select value={quality} onValueChange={setQuality}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low_quality">Low Quality (Fast)</SelectItem>
                    <SelectItem value="medium_quality">Medium Quality</SelectItem>
                    <SelectItem value="high_quality">High Quality (Slow)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button
                onClick={generateVideo}
                disabled={!file || isGenerating}
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
              >
                {isGenerating ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Starting Generation...
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <Play className="w-4 h-4" />
                    Generate Video
                  </div>
                )}
              </Button>
            </div>

            <div className="text-xs text-slate-500 bg-slate-50 p-3 rounded-lg">
              <strong>Note:</strong> Video generation creates an educational video from your PDF using AI. 
              This process may take several minutes depending on document complexity and quality settings.
            </div>
          </>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {getStatusIcon(currentJob.status)}
                <span className="font-medium capitalize">{currentJob.status}</span>
              </div>
              <Badge className={getStatusColor(currentJob.status)}>
                {currentJob.status.toUpperCase()}
              </Badge>
            </div>

            <div className="space-y-2 text-sm text-slate-600">
              <div><strong>Job ID:</strong> {currentJob.job_id.slice(0, 8)}...</div>
              <div><strong>Quality:</strong> {currentJob.quality.replace('_', ' ')}</div>
              <div><strong>Started:</strong> {new Date(currentJob.created_at).toLocaleTimeString()}</div>
              {currentJob.completed_at && (
                <div><strong>Completed:</strong> {new Date(currentJob.completed_at).toLocaleTimeString()}</div>
              )}
            </div>

            {currentJob.status === "processing" && (
              <div className="bg-blue-50 p-3 rounded-lg">
                <p className="text-blue-800 text-sm">
                  🎬 Generating video clips and assembling final video...
                </p>
              </div>
            )}

            {currentJob.status === "completed" && (
              <div className="space-y-2">
                <Button
                  onClick={() => onVideoGenerated?.(currentJob.job_id)}
                  className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Play Video
                </Button>
                <Button
                  onClick={downloadVideo}
                  variant="outline"
                  className="w-full"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download Video
                </Button>
              </div>
            )}

            {currentJob.status === "failed" && currentJob.error && (
              <div className="bg-red-50 p-3 rounded-lg">
                <p className="text-red-800 text-sm">
                  <strong>Error:</strong> {currentJob.error}
                </p>
              </div>
            )}

            <Button
              onClick={() => {
                setCurrentJob(null)
                setError(null)
              }}
              variant="outline"
              className="w-full"
            >
              Generate New Video
            </Button>
          </div>
        )}

        {error && (
          <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
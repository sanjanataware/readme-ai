"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Video, Play, Download, Trash2, RefreshCw, Clock, CheckCircle, AlertCircle, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { config, type VideoJobStatus } from "@/lib/config"

interface VideoLibraryProps {
  onVideoSelect?: (job: VideoJobStatus) => void
  refreshTrigger?: number
}

export default function VideoLibrary({ onVideoSelect, refreshTrigger }: VideoLibraryProps) {
  const [jobs, setJobs] = useState<VideoJobStatus[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchJobs = async () => {
    try {
      setError(null)
      const response = await fetch(`${config.VIDEO_API_URL}/jobs`)
      if (response.ok) {
        const data = await response.json()
        // Sort by creation date, newest first
        const sortedJobs = data.jobs.sort((a: VideoJobStatus, b: VideoJobStatus) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        )
        setJobs(sortedJobs)
      } else {
        setError("Failed to fetch video library")
      }
    } catch (error) {
      console.error("Error fetching jobs:", error)
      setError("Network error. Please check your connection.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchJobs()
  }, [refreshTrigger])

  const deleteJob = async (jobId: string) => {
    try {
      const response = await fetch(`${config.VIDEO_API_URL}/jobs/${jobId}`, {
        method: "DELETE",
      })
      
      if (response.ok) {
        setJobs(jobs.filter(job => job.job_id !== jobId))
      } else {
        setError("Failed to delete video")
      }
    } catch (error) {
      console.error("Error deleting job:", error)
      setError("Failed to delete video")
    }
  }

  const downloadVideo = async (job: VideoJobStatus) => {
    try {
      const response = await fetch(`${config.VIDEO_API_URL}/download/${job.job_id}`)
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement("a")
        a.href = url
        a.download = `video_${job.job_id}.mp4`
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

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString()
  }

  const getFileName = (job: VideoJobStatus) => {
    if (job.original_filename) {
      return job.original_filename.replace('.pdf', '')
    }
    return `Video ${job.job_id.slice(0, 8)}`
  }

  if (loading) {
    return (
      <Card className="border-0 shadow-xl bg-white/80 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <div className="p-2 bg-gradient-to-r from-indigo-100 to-purple-100 rounded-lg">
              <Video className="w-5 h-5 text-indigo-600" />
            </div>
            Video Library
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="w-6 h-6 animate-spin text-slate-400" />
            <span className="ml-2 text-slate-600">Loading videos...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-0 shadow-xl bg-white/80 backdrop-blur-sm">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-gradient-to-r from-indigo-100 to-purple-100 rounded-lg">
              <Video className="w-5 h-5 text-indigo-600" />
            </div>
            Video Library ({jobs.length})
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchJobs}
            className="h-8 w-8 p-0"
          >
            <RefreshCw className="w-4 h-4" />
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {error && (
          <div className="flex items-center gap-3 p-3 bg-red-50 border border-red-200 rounded-lg">
            <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        {jobs.length === 0 ? (
          <div className="text-center py-8">
            <Video className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500">No videos generated yet</p>
            <p className="text-sm text-slate-400">Upload a PDF and generate your first video!</p>
          </div>
        ) : (
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {jobs.map((job) => (
              <div
                key={job.job_id}
                className="border border-slate-200 rounded-lg p-3 hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <FileText className="w-4 h-4 text-slate-500 flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-sm text-slate-800 truncate">
                        {getFileName(job)}
                      </p>
                      <p className="text-xs text-slate-500">
                        {formatDate(job.created_at)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    {getStatusIcon(job.status)}
                    <Badge variant="outline" className={`text-xs ${getStatusColor(job.status)}`}>
                      {job.status}
                    </Badge>
                  </div>
                </div>

                <div className="flex items-center gap-1 text-xs text-slate-500 mb-3">
                  <span>Quality: {job.quality.replace('_', ' ')}</span>
                  <span>•</span>
                  <span>ID: {job.job_id.slice(0, 8)}...</span>
                </div>

                {job.error && (
                  <div className="text-xs text-red-600 mb-2 p-2 bg-red-50 rounded border">
                    {job.error}
                  </div>
                )}

                <div className="flex gap-1">
                  {job.status === "completed" && (
                    <>
                      <Button
                        size="sm"
                        onClick={() => onVideoSelect?.(job)}
                        className="flex-1 h-7 text-xs bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700"
                      >
                        <Play className="w-3 h-3 mr-1" />
                        Play
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => downloadVideo(job)}
                        className="h-7 px-2"
                      >
                        <Download className="w-3 h-3" />
                      </Button>
                    </>
                  )}
                  
                  {job.status === "processing" && (
                    <div className="flex-1 text-center text-xs text-blue-600 py-1">
                      Processing...
                    </div>
                  )}
                  
                  {job.status === "pending" && (
                    <div className="flex-1 text-center text-xs text-yellow-600 py-1">
                      Waiting to start...
                    </div>
                  )}

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => deleteJob(job.job_id)}
                    className="h-7 px-2 text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
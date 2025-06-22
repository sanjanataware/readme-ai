"use client"

import type React from "react"
import { useState, useRef, useEffect } from "react"
import { X, Download, Maximize2, Minimize2, Volume2, VolumeX, Play, Pause } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { config, type VideoJobStatus } from "@/lib/config"

interface VideoPlayerProps {
  job: VideoJobStatus | null
  onClose: () => void
}

export default function VideoPlayer({ job, onClose }: VideoPlayerProps) {
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [videoError, setVideoError] = useState(false)
  const [videoUrl, setVideoUrl] = useState<string | null>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!job) {
      setVideoUrl(null)
      return
    }

    // Create blob URL for the video
    const fetchVideo = async () => {
      try {
        setVideoError(false)
        const response = await fetch(`${config.VIDEO_API_URL}/download/${job.job_id}`)
        if (response.ok) {
          const blob = await response.blob()
          const url = URL.createObjectURL(blob)
          setVideoUrl(url)
        } else {
          setVideoError(true)
        }
      } catch (error) {
        console.error("Error loading video:", error)
        setVideoError(true)
      }
    }

    fetchVideo()

    // Cleanup function to revoke the blob URL
    return () => {
      if (videoUrl) {
        URL.revokeObjectURL(videoUrl)
      }
    }
  }, [job])

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }

    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange)
  }, [])

  const toggleFullscreen = async () => {
    if (!containerRef.current) return

    try {
      if (!isFullscreen) {
        await containerRef.current.requestFullscreen()
      } else {
        await document.exitFullscreen()
      }
    } catch (error) {
      console.error("Error toggling fullscreen:", error)
    }
  }

  const togglePlayPause = () => {
    if (!videoRef.current) return

    if (isPlaying) {
      videoRef.current.pause()
    } else {
      videoRef.current.play()
    }
  }

  const toggleMute = () => {
    if (!videoRef.current) return

    videoRef.current.muted = !videoRef.current.muted
    setIsMuted(videoRef.current.muted)
  }

  const downloadVideo = async () => {
    if (!job) return

    try {
      const response = await fetch(`${config.VIDEO_API_URL}/download/${job.job_id}`)
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement("a")
        a.href = url
        a.download = `${job.original_filename?.replace('.pdf', '') || 'video'}_${job.job_id.slice(0, 8)}.mp4`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      }
    } catch (error) {
      console.error("Error downloading video:", error)
    }
  }

  const handleVideoLoad = () => {
    setVideoError(false)
  }

  const handleVideoError = () => {
    setVideoError(true)
  }

  const handlePlay = () => setIsPlaying(true)
  const handlePause = () => setIsPlaying(false)

  if (!job) return null

  const getFileName = () => {
    if (job.original_filename) {
      return job.original_filename.replace('.pdf', '')
    }
    return `Video ${job.job_id.slice(0, 8)}`
  }

  return (
    <div 
      ref={containerRef}
      className={`${isFullscreen ? 'fixed inset-0 z-50 bg-black' : ''}`}
    >
      <Card className={`border-0 shadow-2xl bg-white/95 backdrop-blur-sm ${isFullscreen ? 'h-full rounded-none' : ''}`}>
        <CardHeader className={`${isFullscreen ? 'text-white' : ''}`}>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2 min-w-0">
              <div className="text-sm font-medium truncate">
                {getFileName()}
              </div>
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={downloadVideo}
                className={`h-8 w-8 p-0 ${isFullscreen ? 'text-white hover:bg-white/20' : ''}`}
              >
                <Download className="w-4 h-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleFullscreen}
                className={`h-8 w-8 p-0 ${isFullscreen ? 'text-white hover:bg-white/20' : ''}`}
              >
                {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className={`h-8 w-8 p-0 ${isFullscreen ? 'text-white hover:bg-white/20' : ''}`}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className={`${isFullscreen ? 'h-full flex flex-col' : ''} p-0`}>
          <div className={`relative bg-black ${isFullscreen ? 'flex-1' : 'aspect-video'}`}>
            {videoError ? (
              <div className="absolute inset-0 flex items-center justify-center text-white">
                <div className="text-center">
                  <div className="text-lg mb-2">Unable to load video</div>
                  <div className="text-sm text-gray-300">The video file may be corrupted or unavailable</div>
                </div>
              </div>
            ) : videoUrl ? (
              <>
                <video
                  ref={videoRef}
                  src={videoUrl}
                  className="w-full h-full"
                  controls={false}
                  onLoadedData={handleVideoLoad}
                  onError={handleVideoError}
                  onPlay={handlePlay}
                  onPause={handlePause}
                  onClick={togglePlayPause}
                />
                
                {/* Custom Controls Overlay */}
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={togglePlayPause}
                        className="h-8 w-8 p-0 text-white hover:bg-white/20"
                      >
                        {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                      </Button>
                      
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={toggleMute}
                        className="h-8 w-8 p-0 text-white hover:bg-white/20"
                      >
                        {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                      </Button>
                    </div>
                    
                    <div className="text-white text-sm">
                      Quality: {job.quality.replace('_', ' ')}
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="absolute inset-0 flex items-center justify-center text-white">
                <div className="text-center">
                  <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                  <div className="text-sm">Loading video...</div>
                </div>
              </div>
            )}
          </div>
          
          {!isFullscreen && (
            <div className="p-4 space-y-2">
              <div className="flex items-center justify-between text-sm text-slate-600">
                <span>Created: {new Date(job.created_at).toLocaleString()}</span>
                <span>Quality: {job.quality.replace('_', ' ')}</span>
              </div>
              
              {job.completed_at && (
                <div className="text-xs text-slate-500">
                  Completed: {new Date(job.completed_at).toLocaleString()}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
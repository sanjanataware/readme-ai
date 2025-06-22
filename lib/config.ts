export const config = {
  // FastAPI server URL - change this to match your server location
  VIDEO_API_URL: process.env.NEXT_PUBLIC_VIDEO_API_URL || "http://localhost:8000",
} as const

export type VideoQuality = "low_quality" | "medium_quality" | "high_quality"

export interface VideoJobStatus {
  job_id: string
  status: "pending" | "processing" | "completed" | "failed"
  created_at: string
  completed_at?: string
  error?: string
  video_path?: string
  pdf_path?: string
  quality: string
  original_filename?: string
}
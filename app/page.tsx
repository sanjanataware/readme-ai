"use client"

import type React from "react"

import { useState } from "react"
import { Upload, FileText, Brain, Sparkles, AlertCircle, CheckCircle, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { config, type VideoJobStatus } from "@/lib/config"
import QuizPanel from "./components/quiz-panel"
import ConceptsDisplay from "./components/concepts-display"
import VideoPanel from "./components/video-panel"
import VideoLibrary from "./components/video-library"
import VideoPlayer from "./components/video-player"

interface QuizQuestion {
  question: string
  options: string[]
  correctAnswer: number
  concept: string
}

interface Concept {
  title: string
  summary: string
  citations: string[]
  importance: string
}

interface AnalysisResult {
  concepts: Concept[]
  questions: QuizQuestion[]
}

export default function ResearchAnalyzer() {
  const [file, setFile] = useState<File | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [isFallbackData, setIsFallbackData] = useState(false)
  const [selectedVideo, setSelectedVideo] = useState<VideoJobStatus | null>(null)
  const [refreshLibrary, setRefreshLibrary] = useState(0)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files[0] && files[0].type === "application/pdf") {
      setFile(files[0])
      setError(null)
      setAnalysis(null)
      setSuccessMessage(null)
      setIsFallbackData(false)
    } else if (files && files[0]) {
      setError("Please select a PDF file")
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const files = e.dataTransfer.files
    if (files && files[0]) {
      if (files[0].type === "application/pdf") {
        setFile(files[0])
        setError(null)
        setAnalysis(null)
        setSuccessMessage(null)
        setIsFallbackData(false)
      } else {
        setError("Please select a PDF file")
      }
    }
  }

  const analyzeDocument = async () => {
    if (!file) return

    setIsAnalyzing(true)
    setError(null)
    setSuccessMessage(null)
    setIsFallbackData(false)

    try {
      const formData = new FormData()
      formData.append("pdf", file)

      const response = await fetch("/api/analyze", {
        method: "POST",
        body: formData,
      })

      if (response.ok) {
        const result = await response.json()
        setAnalysis(result)

        // Check if we got fallback data
        if (result.concepts?.[0]?.title === "Research Document Analysis") {
          setIsFallbackData(true)
          setError(
            "Analysis completed with sample data. The AI had difficulty processing this specific document. You can still explore the interface with the sample content below.",
          )
        } else {
          setSuccessMessage(
            `Successfully analyzed "${file.name}" and extracted ${result.concepts?.length || 0} concepts and ${result.questions?.length || 0} quiz questions!`,
          )
        }
      } else {
        // Even if response is not ok, try to get the data
        try {
          const result = await response.json()
          if (result.concepts && result.questions) {
            setAnalysis(result)
            setIsFallbackData(true)
            setError("Analysis completed with sample data due to processing issues.")
          } else {
            throw new Error("No valid data received")
          }
        } catch {
          setError("Analysis failed. Please try again with a different document.")
        }
      }
    } catch (error) {
      console.error("Error analyzing document:", error)
      setError("Network error. Please check your connection and try again.")
    } finally {
      setIsAnalyzing(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="p-3 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl">
              <Brain className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              README.ai
            </h1>
          </div>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            Transform research papers into interactive learning experiences with AI-powered concept extraction and quiz
            generation
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Upload Area */}
          <div className="lg:col-span-2">
            <Card className="border-0 shadow-xl bg-white/80 backdrop-blur-sm">
              <CardContent className="p-8">
                {!file ? (
                  <div
                    className={`border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 cursor-pointer ${
                      dragActive
                        ? "border-blue-500 bg-blue-50"
                        : "border-slate-300 hover:border-blue-400 hover:bg-slate-50"
                    }`}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                    onClick={() => document.getElementById("file-upload")?.click()}
                  >
                    <div className="flex flex-col items-center gap-4">
                      <div className="p-4 bg-gradient-to-r from-blue-100 to-indigo-100 rounded-full">
                        <Upload className="w-12 h-12 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="text-xl font-semibold text-slate-800 mb-2">Upload Research Paper</h3>
                        <p className="text-slate-600 mb-4">Drag and drop your PDF file here, or click to browse</p>
                        <input
                          type="file"
                          accept=".pdf,application/pdf"
                          onChange={handleFileSelect}
                          className="hidden"
                          id="file-upload"
                        />
                        <Button
                          type="button"
                          className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                          onClick={(e) => {
                            e.stopPropagation()
                            document.getElementById("file-upload")?.click()
                          }}
                        >
                          Choose File
                        </Button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-6">
                    <div className="flex items-center gap-4 p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200">
                      <FileText className="w-8 h-8 text-green-600" />
                      <div className="flex-1">
                        <h3 className="font-semibold text-green-800">{file.name}</h3>
                        <p className="text-sm text-green-600">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setFile(null)
                          setError(null)
                          setAnalysis(null)
                          setSuccessMessage(null)
                          setIsFallbackData(false)
                        }}
                        className="text-green-700 border-green-300 hover:bg-green-100"
                      >
                        Remove
                      </Button>
                    </div>

                    <div className="flex gap-3">
                      <Button
                        onClick={analyzeDocument}
                        disabled={isAnalyzing}
                        className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 h-12 text-lg"
                      >
                        {isAnalyzing ? (
                          <div className="flex items-center gap-2">
                            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            Analyzing Document...
                          </div>
                        ) : (
                          <div className="flex items-center gap-2">
                            <Sparkles className="w-5 h-5" />
                            Analyze with AI
                          </div>
                        )}
                      </Button>

                      {analysis && (
                        <Button
                          onClick={analyzeDocument}
                          disabled={isAnalyzing}
                          variant="outline"
                          className="h-12 px-4"
                          title="Re-analyze document"
                        >
                          <RefreshCw className="w-5 h-5" />
                        </Button>
                      )}
                    </div>

                    {/* Status Messages */}
                    {successMessage && (
                      <div className="flex items-center gap-3 p-4 bg-green-50 border border-green-200 rounded-lg">
                        <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
                        <p className="text-green-800">{successMessage}</p>
                      </div>
                    )}

                    {error && (
                      <div className="flex items-center gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg">
                        <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0" />
                        <p className="text-amber-800">{error}</p>
                      </div>
                    )}

                    {isFallbackData && (
                      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <p className="text-blue-800 text-sm">
                          <strong>Demo Mode:</strong> You're viewing sample data to explore the interface. Try uploading
                          a different research paper for better results.
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Concepts Display */}
            {analysis && <ConceptsDisplay concepts={analysis.concepts} />}
          </div>

          {/* Side Panels */}
          <div className="lg:col-span-1 space-y-6">
            <VideoPanel 
              file={file} 
              isVisible={!!file} 
              onVideoGenerated={(jobId) => {
                setRefreshLibrary(prev => prev + 1)
                // Find and select the completed video
                fetch(`${config.VIDEO_API_URL}/jobs/${jobId}`)
                  .then(res => res.json())
                  .then(job => {
                    if (job.status === "completed") {
                      setSelectedVideo(job)
                    }
                  })
                  .catch(console.error)
              }} 
            />
            <VideoLibrary 
              onVideoSelect={setSelectedVideo}
              refreshTrigger={refreshLibrary}
            />
            <QuizPanel questions={analysis?.questions || []} isVisible={!!analysis} />
          </div>
        </div>
      </div>
      
      {/* Video Player Overlay */}
      {selectedVideo && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-4xl">
            <VideoPlayer 
              job={selectedVideo} 
              onClose={() => setSelectedVideo(null)} 
            />
          </div>
        </div>
      )}
    </div>
  )
}

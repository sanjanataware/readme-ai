# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

README.ai is a Next.js 15 application that transforms research papers into interactive learning experiences. It uses AI (Anthropic Claude) to extract key concepts from uploaded PDF documents and generates quiz questions for interactive learning. The app is deployed on Vercel and synced with v0.dev.

## Common Commands

### Development
- `pnpm dev` - Start development server
- `pnpm build` - Build for production  
- `pnpm start` - Start production server
- `pnpm lint` - Run ESLint

### Package Management
- Uses `pnpm` as package manager (not npm/yarn)
- `pnpm install` - Install dependencies

## Architecture

### Core Components
- **Main App**: `app/page.tsx` - Primary upload and analysis interface with drag/drop PDF upload
- **API Route**: `app/api/analyze/route.ts` - Handles PDF processing using Anthropic Claude API
- **Quiz Panel**: `app/components/quiz-panel.tsx` - Interactive quiz interface
- **Concepts Display**: `app/components/concepts-display.tsx` - Shows extracted concepts
- **Video Panel**: `app/components/video-panel.tsx` - Video generation interface with job tracking
- **Video Library**: `app/components/video-library.tsx` - Lists all generated videos with management options
- **Video Player**: `app/components/video-player.tsx` - In-app video player with fullscreen support

### Key Features
- PDF upload with drag/drop support
- AI-powered concept extraction using Claude 3.5 Sonnet
- Quiz generation with multiple choice questions
- **Video generation from PDFs using external FastAPI server**
- **Video library with in-app playback and management**
- **Full-featured video player with fullscreen mode**
- Job tracking with real-time status updates
- Video deletion and download capabilities
- Fallback data when AI processing fails
- Responsive design with Tailwind CSS

### Tech Stack
- **Framework**: Next.js 15 with App Router
- **AI**: Anthropic Claude API (@ai-sdk/anthropic)
- **UI**: Radix UI components with custom styling
- **Styling**: Tailwind CSS with custom design system
- **Forms**: React Hook Form with Zod validation
- **Icons**: Lucide React

### Configuration Notes
- TypeScript and ESLint errors are ignored during builds (see next.config.mjs)
- Uses pnpm workspace configuration
- Custom path mapping: `@/*` points to root directory
- Dark mode support configured in Tailwind
- **Video API URL configured in `lib/config.ts` (defaults to localhost:8000)**

### Data Models
```typescript
interface Concept {
  title: string
  summary: string
  citations: string[]
  importance: string
}

interface QuizQuestion {
  question: string
  options: string[]
  correctAnswer: number
  concept: string
}

interface VideoJobStatus {
  job_id: string
  status: "pending" | "processing" | "completed" | "failed"
  created_at: string
  completed_at?: string
  error?: string
  video_path?: string
  quality: "low_quality" | "medium_quality" | "high_quality"
}
```

## Important Notes

### API Key Security
- **CRITICAL**: The Anthropic API key is currently hardcoded in `app/api/analyze/route.ts:8-10`
- This should be moved to environment variables immediately for security
- Use `ANTHROPIC_API_KEY` environment variable instead

### Error Handling
- API route includes robust fallback data when AI processing fails
- Frontend handles both successful AI responses and fallback scenarios
- Graceful degradation ensures app remains functional even with AI failures

### Video Generation Integration
- **External FastAPI server required** for video generation functionality
- Server must be running on configured URL (default: localhost:8000)
- Supports three quality levels: low_quality, medium_quality, high_quality
- Real-time job tracking with automatic status polling
- **Complete video library management**: view, play, download, delete videos
- **In-app video player** with custom controls, fullscreen mode, and overlay UI
- Automatic refresh of video library when new videos are generated
- Video streaming using blob URLs for secure in-app playback

### Deployment
- App is deployed on Vercel and synced with v0.dev
- Automatic deployments from this repository
- Images are unoptimized for deployment compatibility
- **Video generation requires separate FastAPI server deployment**
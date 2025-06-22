from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Optional
from video_gen.gen import generate_complete_video
from video_gen.config_gen import generate_video_config
from video_gen.github_extract import GitHubExtractor

app = FastAPI(title="Video Generation API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# JSON file to store job status
JOBS_FILE = "jobs.json"

class VideoRequest(BaseModel):
    pdf_path: Optional[str] = None
    use_base64: bool = True
    quality: str = "low_quality"  # low_quality, medium_quality, high_quality

class VideoRequestWithUpload(BaseModel):
    quality: str = "low_quality"

class GitHubExtractRequest(BaseModel):
    pdf_path: Optional[str] = None
    fetch_readmes: bool = True
    simplify_readmes: bool = True

class JobStatus(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None
    video_path: Optional[str] = None
    pdf_path: Optional[str] = None
    video_name: Optional[str] = None

class RenameVideoRequest(BaseModel):
    video_name: str

def load_jobs() -> Dict[str, Dict]:
    """Load jobs from JSON file"""
    if os.path.exists(JOBS_FILE):
        try:
            with open(JOBS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_jobs(jobs: Dict[str, Dict]):
    """Save jobs to JSON file"""
    with open(JOBS_FILE, 'w') as f:
        json.dump(jobs, f, indent=2)

def update_job_status(job_id: str, status: str, **kwargs):
    """Update job status in JSON file"""
    jobs = load_jobs()
    if job_id in jobs:
        jobs[job_id]["status"] = status
        if status == "completed":
            jobs[job_id]["completed_at"] = datetime.now().isoformat()
        for key, value in kwargs.items():
            jobs[job_id][key] = value
        save_jobs(jobs)

async def process_video_generation(job_id: str, pdf_path: str, use_base64: bool, quality: str):
    """Background task to generate video"""
    try:
        update_job_status(job_id, "processing")
        
        # Step 1: Generate video configuration
        print(f"Job {job_id}: Generating video config from PDF...")
        response = generate_video_config(pdf_path, use_base64)
        config_text = response.content[0].text
        
        # Parse the JSON config
        try:
            config = json.loads(config_text)
        except json.JSONDecodeError:
            # Try to extract JSON from text if it's wrapped
            import re
            json_match = re.search(r'\{.*\}', config_text, re.DOTALL)
            if json_match:
                config = json.loads(json_match.group())
            else:
                raise ValueError("Could not parse JSON from config response")
        
        clips = config.get("clips", [])
        if not clips:
            raise ValueError("No clips found in configuration")
        
        # Step 2: Generate video
        print(f"Job {job_id}: Generating {len(clips)} clips...")
        output_path = f"outputs/video_{job_id}.mp4"
        os.makedirs("outputs", exist_ok=True)
        
        final_video = await generate_complete_video(clips, output_path, quality)
        
        # Update job as completed
        update_job_status(job_id, "completed", video_path=final_video)
        print(f"Job {job_id}: Completed successfully!")
        
    except Exception as e:
        error_msg = str(e)
        print(f"Job {job_id}: Failed with error: {error_msg}")
        update_job_status(job_id, "failed", error=error_msg)

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload PDF file"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Create uploads directory
    os.makedirs("uploads", exist_ok=True)
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_path = f"uploads/{file_id}_{file.filename}"
    
    # Save uploaded file
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    return {"file_id": file_id, "file_path": file_path, "filename": file.filename}

@app.post("/generate-video")
async def generate_video(request: VideoRequest, background_tasks: BackgroundTasks):
    """Start video generation job with PDF path"""
    
    if not request.pdf_path:
        raise HTTPException(status_code=400, detail="PDF path is required")
    
    # Check if PDF exists
    if not request.pdf_path.startswith('http') and not os.path.exists(request.pdf_path):
        raise HTTPException(status_code=400, detail="PDF file not found")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Create job record
    job_data = {
        "job_id": job_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "pdf_path": request.pdf_path,
        "quality": request.quality,
        "video_name": None
    }
    
    jobs = load_jobs()
    jobs[job_id] = job_data
    save_jobs(jobs)
    
    # Start background task
    background_tasks.add_task(
        process_video_generation,
        job_id,
        request.pdf_path,
        request.use_base64,
        request.quality
    )
    
    return {"job_id": job_id, "status": "pending", "message": "Video generation started"}

@app.post("/generate-video-upload")
async def generate_video_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    quality: str = "low_quality"
):
    """Upload PDF and start video generation in one step"""
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Create uploads directory
    os.makedirs("uploads", exist_ok=True)
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_path = f"uploads/{file_id}_{file.filename}"
    
    # Save uploaded file
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Create job record
    job_data = {
        "job_id": job_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "pdf_path": file_path,
        "quality": quality,
        "original_filename": file.filename,
        "video_name": None
    }
    
    jobs = load_jobs()
    jobs[job_id] = job_data
    save_jobs(jobs)
    
    # Start background task
    background_tasks.add_task(
        process_video_generation,
        job_id,
        file_path,
        True,  # use_base64 = True for uploaded files
        quality
    )
    
    return {
        "job_id": job_id, 
        "status": "pending", 
        "message": "PDF uploaded, video generation started",
        "file_path": file_path
    }

@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job status"""
    jobs = load_jobs()
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]

@app.get("/jobs")
async def list_jobs():
    """List all jobs"""
    jobs = load_jobs()
    return {"jobs": list(jobs.values())}

@app.get("/download/{job_id}")
async def download_video(job_id: str):
    """Download generated video"""
    jobs = load_jobs()
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Video not ready yet")
    
    video_path = job.get("video_path")
    if not video_path or not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        video_path,
        media_type='video/mp4',
        filename=f"video_{job_id}.mp4"
    )

@app.put("/jobs/{job_id}/rename")
async def rename_video(job_id: str, request: RenameVideoRequest):
    """Rename a video"""
    jobs = load_jobs()
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Update video name
    jobs[job_id]["video_name"] = request.video_name
    save_jobs(jobs)
    
    return {"message": "Video renamed successfully", "video_name": request.video_name}

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete job and associated files"""
    jobs = load_jobs()
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    # Delete video file if it exists
    if job.get("video_path") and os.path.exists(job["video_path"]):
        os.remove(job["video_path"])
    
    # Remove from jobs
    del jobs[job_id]
    save_jobs(jobs)
    
    return {"message": "Job deleted successfully"}

@app.post("/extract-github")
async def extract_github_repos(request: GitHubExtractRequest):
    """Extract GitHub repository links from PDF"""
    
    if not request.pdf_path:
        raise HTTPException(status_code=400, detail="PDF path is required")
    
    # Check if PDF exists
    if not request.pdf_path.startswith('http') and not os.path.exists(request.pdf_path):
        raise HTTPException(status_code=400, detail="PDF file not found")
    
    try:
        extractor = GitHubExtractor()
        result = extractor.process_pdf(
            request.pdf_path,
            fetch_readmes=request.fetch_readmes,
            simplify_readmes=request.simplify_readmes
        )
        
        return {
            "github_links": result["github_links"],
            "readmes_count": len(result["readmes"]),
            "readmes": result["readmes"] if request.fetch_readmes else {},
            "simplified_readmes": result["simplified_readmes"] if request.simplify_readmes else {}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GitHub extraction failed: {str(e)}")

@app.post("/extract-github-upload")
async def extract_github_upload(
    file: UploadFile = File(...),
    fetch_readmes: bool = True,
    simplify_readmes: bool = True
):
    """Upload PDF and extract GitHub repositories"""
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Create uploads directory
    os.makedirs("uploads", exist_ok=True)
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_path = f"uploads/{file_id}_{file.filename}"
    
    # Save uploaded file
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    try:
        extractor = GitHubExtractor()
        result = extractor.process_pdf(
            file_path,
            fetch_readmes=fetch_readmes,
            simplify_readmes=simplify_readmes
        )
        
        return {
            "github_links": result["github_links"],
            "readmes_count": len(result["readmes"]),
            "readmes": result["readmes"] if fetch_readmes else {},
            "simplified_readmes": result["simplified_readmes"] if simplify_readmes else {},
            "file_path": file_path
        }
        
    except Exception as e:
        # Clean up uploaded file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"GitHub extraction failed: {str(e)}")

@app.get("/")
async def root():
    """API info"""
    return {
        "message": "Video Generation API",
        "endpoints": {
            "POST /upload-pdf": "Upload PDF file only",
            "POST /generate-video": "Start video generation with PDF path",
            "POST /generate-video-upload": "Upload PDF and start generation",
            "POST /extract-github": "Extract GitHub repositories from PDF path",
            "POST /extract-github-upload": "Upload PDF and extract GitHub repositories",
            "GET /jobs/{job_id}": "Get job status",
            "GET /jobs": "List all jobs",
            "GET /download/{job_id}": "Download video",
            "PUT /jobs/{job_id}/rename": "Rename video",
            "DELETE /jobs/{job_id}": "Delete job"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True, debug=True)
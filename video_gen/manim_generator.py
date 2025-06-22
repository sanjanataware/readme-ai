import asyncio
import subprocess
import os
import tempfile
import json
from typing import List, Dict, Any
from pathlib import Path


async def generate_manim_video(code: str, output_dir: str = "output", clip_name: str = None, quality: str = "medium_quality") -> str:
    """
    Generate a video from Manim code asynchronously.
    
    Args:
        code: The Manim Python code to execute
        output_dir: Directory to save the output video
        clip_name: Optional name for the clip file
        quality: Manim quality setting (low_quality, medium_quality, high_quality)
        
    Returns:
        Path to the generated video file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate a unique filename if not provided
    if not clip_name:
        clip_name = f"clip_{hash(code) % 10000}"
    
    # Create temporary Python file with the Manim code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        # Always include default imports
        full_code = "from manim import *\nimport numpy as np\n\n" + code
        temp_file.write(full_code)
        temp_file_path = temp_file.name
    
    try:
        # Run Manim command asynchronously
        cmd = [
            "manim",
            temp_file_path,
            "-o", output_dir,
            "--media_dir", output_dir,
            "-v", "WARNING",  # Reduce verbosity
            f"-q{quality[0]}"  # Quality flag: -ql (low), -qm (medium), -qh (high)
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            print(f"Warning: Manim execution failed for clip {clip_name}: {stderr.decode()}")
            # Return None instead of raising exception to continue with other clips
            return None
        
        # Find the generated video file - look for the final rendered video
        # Manim typically creates the final video in videos/quality/SceneName.mp4
        video_files = list(Path(output_dir).glob("**/*.mp4"))
        if not video_files:
            print(f"Warning: No video file was generated for clip {clip_name}")
            return None
        
        # Filter out partial files (they usually contain "partial" in the name)
        final_videos = [f for f in video_files if "partial" not in str(f)]
        
        if not final_videos:
            print(f"Warning: No final video file found for clip {clip_name}, using latest available")
            final_videos = video_files
        
        # Return the most recently created final video file
        latest_video = max(final_videos, key=os.path.getctime)
        print(f"Selected video file: {latest_video}")
        return str(latest_video)
        
    finally:
        # Clean up temporary file
        os.unlink(temp_file_path)


async def generate_manim_clips(clips_config: List[Dict[str, Any]], output_dir: str = "output", quality: str = "medium_quality") -> List[str]:
    """
    Generate multiple Manim clips concurrently.
    
    Args:
        clips_config: List of clip configurations with 'code' and optional 'voice_over'
        output_dir: Directory to save output videos
        quality: Manim quality setting (low_quality, medium_quality, high_quality)
        
    Returns:
        List of paths to generated video files
    """
    manim_clips = [clip for clip in clips_config if clip.get('type') == 'manim' and clip.get('code')]
    
    tasks = []
    for i, clip in enumerate(manim_clips):
        clip_name = f"manim_clip_{i:03d}"
        task = generate_manim_video(clip['code'], output_dir, clip_name, quality)
        tasks.append(task)
    
    # Execute all Manim generations concurrently
    video_paths = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle any exceptions and filter out None results
    successful_paths = []
    for i, result in enumerate(video_paths):
        if isinstance(result, Exception):
            print(f"Error generating clip {i}: {result}")
        elif result is not None:
            successful_paths.append(result)
    
    return successful_paths


async def main():
    """Example usage"""
    # Example clip configuration
    sample_clips = [
        {
            "type": "manim",
            "code": """
from manim import *

class SimpleScene(Scene):
    def construct(self):
        text = Text("Hello, Manim!")
        self.play(Write(text))
        self.wait(1)
""",
            "voice_over": "Welcome to our mathematical visualization"
        }
    ]
    
    video_paths = await generate_manim_clips(sample_clips)
    print(f"Generated videos: {video_paths}")


if __name__ == "__main__":
    asyncio.run(main())
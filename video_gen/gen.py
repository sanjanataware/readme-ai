import asyncio
import subprocess
import os
import json
import time
from typing import List, Dict, Any
from pathlib import Path
try:
    from .manim_generator import generate_manim_clips
except ImportError:
    from manim_generator import generate_manim_clips
try:
    from .voice_gen import generate_voice
except ImportError:
    from voice_gen import generate_voice
from google import genai
from google.genai import types

from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()


async def generate_veo_clip(prompt: str, output_dir: str, clip_name: str) -> str:
    """
    Generate a video clip using Google's Veo API.
    
    Args:
        prompt: Description for the Veo API
        output_dir: Directory to save the output
        clip_name: Name for the clip file
        
    Returns:
        Path to generated video file
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{clip_name}.mp4")
    
    try:
        # Initialize Veo client
        MODEL = "veo-2.0-generate-001"
        api_key = os.getenv("GOOG_API_KEY", "AIzaSyAnQaiid06gc6Nr6U1yXyDLE4b0Nx2DysI")
        client = genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=api_key
        )
        
        video_config = types.GenerateVideosConfig(
            person_generation="dont_allow",
            aspect_ratio="16:9",
            number_of_videos=1,
            duration_seconds=5,
        )
        
        print(f"Generating Veo clip: {clip_name}")
        operation = client.models.generate_videos(
            model=MODEL,
            prompt=prompt,
            config=video_config,
        )
        
        # Wait for generation to complete
        while not operation.done:
            print(f"Veo clip {clip_name} still generating...")
            await asyncio.sleep(10)  # Use async sleep
            operation = client.operations.get(operation)
        
        result = operation.result
        if not result:
            print(f"Error generating Veo clip: {clip_name}")
            return await _create_placeholder_video(output_path)
        
        generated_videos = result.generated_videos
        if not generated_videos or len(generated_videos) < 1:
            print(f"No videos generated for Veo clip: {clip_name}")
            return await _create_placeholder_video(output_path)
        
        vid = generated_videos[0]
        print(f"Veo video generated: {vid.video.uri}")
        
        # Download and save the video
        print("Downloading Veo video...")
        client.files.download(file=vid.video)
        vid.video.save(output_path)
        print(f"Veo clip saved to: {output_path}")
        
        # Verify the file exists and has content
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"Veo clip file verified: {output_path} ({file_size} bytes)")
            
            # Check if it's actually a video with ffprobe
            probe_cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", output_path]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            
            if probe_result.returncode == 0:
                import json as json_module
                probe_data = json_module.loads(probe_result.stdout)
                streams = probe_data.get('streams', [])
                video_streams = [s for s in streams if s.get('codec_type') == 'video']
                
                if video_streams:
                    duration = float(video_streams[0].get('duration', 0))
                    fps = video_streams[0].get('r_frame_rate', '0/1')
                    print(f"Veo video info: duration={duration}s, fps={fps}")
                    
                    if duration < 1.0:
                        print(f"WARNING: Veo video duration is very short: {duration}s")
                    
                    # Re-encode to ensure compatibility
                    temp_path = output_path + ".temp.mp4"
                    reencode_cmd = [
                        "ffmpeg", "-y", "-i", output_path,
                        "-c:v", "libx264", "-c:a", "aac",
                        "-pix_fmt", "yuv420p", "-r", "30",
                        "-movflags", "+faststart",
                        temp_path
                    ]
                    
                    reencode_result = subprocess.run(reencode_cmd, capture_output=True, text=True)
                    if reencode_result.returncode == 0:
                        # Replace original with re-encoded version
                        os.replace(temp_path, output_path)
                        print(f"Re-encoded Veo clip for compatibility")
                    else:
                        print(f"WARNING: Failed to re-encode Veo clip: {reencode_result.stderr}")
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                else:
                    print("WARNING: No video streams found in Veo file")
            else:
                print(f"WARNING: Could not probe Veo video: {probe_result.stderr}")
        else:
            print(f"ERROR: Veo clip file not found: {output_path}")
            return await _create_placeholder_video(output_path)
        
        return output_path
        
    except Exception as e:
        print(f"Error generating Veo clip {clip_name}: {e}")
        return await _create_placeholder_video(output_path)


async def _create_placeholder_video(output_path: str) -> str:
    """Create a placeholder video when Veo generation fails."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "color=black:size=1920x1080:duration=5",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        output_path
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    await process.communicate()
    return output_path


def combine_video_with_audio_sync(video_path: str, audio_path: str, output_path: str) -> str:
    """
    Synchronously combine video with audio using MoviePy.
    """
    print(f"Combining video: {video_path} with audio: {audio_path}")
    
    # First verify both files exist
    if not os.path.exists(video_path):
        print(f"ERROR: Video file not found: {video_path}")
        return video_path
    if not os.path.exists(audio_path):
        print(f"ERROR: Audio file not found: {audio_path}")
        return video_path
    
    try:
        from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, ImageClip
        
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)
        
        print(f"Video duration: {video.duration}s, Audio duration: {audio.duration}s")
        
        # If audio is longer than video, extend video by freezing last frame
        if audio.duration > video.duration:
            extra_duration = audio.duration - video.duration
            print(f"Audio is {extra_duration}s longer - freezing last frame")
            
            # Get the last frame and create a still image clip
            last_frame = video.get_frame(video.duration - 0.01)  # Get frame just before end
            still_clip = ImageClip(last_frame, duration=(extra_duration + 0.1))  # Add a small buffer
            
            # Concatenate original video with still frame
            extended_video = concatenate_videoclips([video, still_clip])
            final_video = extended_video.with_audio(audio)
        else:
            # Audio is shorter or same length, just combine
            final_video = video.with_audio(audio)
        
        final_video.write_videofile(output_path)
        
        # Clean up
        video.close()
        audio.close()
        final_video.close()
        if 'extended_video' in locals():
            extended_video.close()
        
        print(f"Success! Combined video created: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"ERROR: MoviePy failed: {e}")
        # Clean up on error
        try:
            if 'video' in locals():
                video.close()
            if 'audio' in locals():
                audio.close()
            if 'final_video' in locals():
                final_video.close()
        except:
            pass
        return video_path


async def combine_video_with_audio(video_path: str, audio_path: str, output_path: str) -> str:
    """
    Async wrapper for combining video with audio.
    """
    # Run sync function in thread pool to avoid blocking
    return await asyncio.get_event_loop().run_in_executor(
        None, 
        combine_video_with_audio_sync,
        video_path,
        audio_path,
        output_path
    )


async def render_all_clips(clips_config: List[Dict[str, Any]], output_dir: str = "clips", quality: str = "medium_quality") -> List[str]:
    """
    Render all clips (Manim and Veo) sequentially to maintain order.
    
    Args:
        clips_config: List of clip configurations
        output_dir: Directory to save all clips
        quality: Manim quality setting (low_quality, medium_quality, high_quality)
        
    Returns:
        List of paths to all generated video files in order
    """
    os.makedirs(output_dir, exist_ok=True)
    
    clip_paths = []
    
    for i, clip in enumerate(clips_config):
        clip_name = f"clip_{i:03d}"
        print(f"Processing clip {i+1}/{len(clips_config)}: {clip.get('type', 'unknown')}")
        
        try:
            video_path = None
            
            # Generate video clip
            if clip.get('type') == 'manim' and clip.get('code'):
                print(f"Generating Manim clip {i}...")
                video_path = await generate_manim_video_single(clip['code'], output_dir, clip_name, quality)
                if not video_path:
                    video_path = await _create_placeholder_video(f"{output_dir}/placeholder_{i:03d}.mp4")
                    print(f"✗ Clip {i}: Manim failed, using placeholder")
                else:
                    print(f"✓ Clip {i} video: {video_path}")
                    
            elif clip.get('type') == 'veo' and clip.get('prompt'):
                print(f"Generating Veo clip {i}...")
                video_path = await generate_veo_clip(clip['prompt'], output_dir, clip_name)
                if not video_path:
                    video_path = await _create_placeholder_video(f"{output_dir}/placeholder_{i:03d}.mp4")
                    print(f"✗ Clip {i}: Veo failed, using placeholder")
                else:
                    print(f"✓ Clip {i} video: {video_path}")
            else:
                print(f"Skipping clip {i}: invalid type or missing content")
                video_path = await _create_placeholder_video(f"{output_dir}/placeholder_{i:03d}.mp4")
                print(f"✗ Clip {i}: Skipped, using placeholder")
            
            # Generate voiceover if provided
            if clip.get('voice_over') and video_path:
                print(f"Generating voiceover for clip {i}...")
                try:
                    audio_path = f"{output_dir}/audio_{clip_name}.wav"
                    await generate_voice(clip['voice_over'], audio_path, voice_id="morgan")
                    
                    # Combine video with audio
                    final_path = f"{output_dir}/final_{clip_name}.mp4"
                    combined_path = await combine_video_with_audio(video_path, audio_path, final_path)
                    clip_paths.append(combined_path)
                    print(f"✓ Clip {i} with audio: {combined_path}")
                    
                    # Keep audio files for debugging
                    print(f"Audio file saved: {audio_path}")
                        
                except Exception as e:
                    print(f"Warning: Voice generation failed for clip {i}: {e}")
                    clip_paths.append(video_path)
                    print(f"✓ Clip {i} (no audio): {video_path}")
            else:
                # No voiceover, use video as-is
                clip_paths.append(video_path)
                print(f"✓ Clip {i} (no audio): {video_path}")
                
        except Exception as e:
            print(f"Error processing clip {i}: {e}")
            placeholder_path = await _create_placeholder_video(f"{output_dir}/placeholder_{i:03d}.mp4")
            clip_paths.append(placeholder_path)
            print(f"✗ Clip {i}: Exception, using placeholder")
    
    print(f"All clips processed. Final order: {[f'clip_{i}' for i in range(len(clip_paths))]}")
    return clip_paths


async def generate_manim_video_single(code: str, output_dir: str, clip_name: str, quality: str = "medium_quality") -> str:
    """
    Generate a single Manim video (extracted from generate_manim_clips for better parallelization).
    """
    try:
        from .manim_generator import generate_manim_video
    except ImportError:
        from manim_generator import generate_manim_video
    return await generate_manim_video(code, output_dir, clip_name, quality)


def stitch_videos(video_paths: List[str], output_path: str = "final_video.mp4") -> str:
    """
    Stitch multiple video files together using MoviePy.
    
    Args:
        video_paths: List of paths to video files to concatenate
        output_path: Path for the final stitched video
        
    Returns:
        Path to the final video file
    """

    print(video_paths)

    if not video_paths:
        raise ValueError("No video paths provided for stitching")
    
    try:
        from moviepy import VideoFileClip, concatenate_videoclips
        import warnings
        
        print("Loading video clips...")
        clips = []
        for i, path in enumerate(video_paths):
            if os.path.exists(path):
                try:
                    # Suppress warnings about truncated frames
                    with warnings.catch_warnings():
                        warnings.filterwarnings("ignore", category=UserWarning, message=".*bytes wanted but.*")
                        clip = VideoFileClip(path)
                    
                    # Validate the clip
                    if clip.duration is None or clip.duration <= 0:
                        print(f"Warning: Clip {path} has invalid duration, skipping")
                        clip.close()
                        continue
                    
                    # Check if the clip can be read properly by trying to get the first frame
                    try:
                        _ = clip.get_frame(0)
                    except Exception as e:
                        print(f"Warning: Clip {path} cannot be read properly, skipping: {e}")
                        clip.close()
                        continue
                    
                    clips.append(clip)
                    print(f"Loaded clip {i}: {path} (duration: {clip.duration}s)")
                    
                except Exception as e:
                    print(f"Warning: Failed to load clip {path}: {e}")
            else:
                print(f"Warning: Skipping missing file: {path}")
        
        if not clips:
            raise ValueError("No valid video clips could be loaded")
        
        print(f"Concatenating {len(clips)} clips...")
        
        # Normalize all clips to consistent properties for chain method
        normalized_clips = []
        target_fps = 30
        target_size = (1920, 1080)  # HD resolution
        
        for i, clip in enumerate(clips):
            print(f"Normalizing clip {i}: {clip.size} @ {clip.fps}fps")
            # Resize and set consistent fps
            normalized_clip = clip.resized(target_size).with_fps(target_fps)
            normalized_clips.append(normalized_clip)
        
        # Use chain method with normalized clips
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning, message=".*bytes wanted but.*")
            final_clip = concatenate_videoclips(normalized_clips, method="chain")
        
        print(f"Writing final video to: {output_path}")
        # Write with specific parameters for better compatibility
        final_clip.write_videofile(
            output_path, 
            # codec="libx264", 
            # audio_codec="aac",
            # fps=30,  # Force consistent framerate
            # preset="medium",
            # ffmpeg_params=["-pix_fmt", "yuv420p"]  # Ensure compatibility
        )
        
        # Clean up resources
        final_clip.close()
        for clip in clips:
            try:
                clip.close()
            except:
                pass
        for clip in normalized_clips:
            try:
                clip.close()
            except:
                pass
        
        print(f"Successfully stitched {len(clips)} clips into {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error stitching videos with MoviePy: {e}")
        # Clean up any open clips on error
        if 'clips' in locals():
            for clip in clips:
                try:
                    clip.close()
                except:
                    pass
        raise


async def generate_complete_video(clips_config: List[Dict[str, Any]], output_path: str = "final_video.mp4", quality: str = "medium_quality") -> str:
    """
    Generate all clips and stitch them together into a complete video.
    
    Args:
        clips_config: List of clip configurations
        output_path: Path for the final video
        quality: Manim quality setting (low_quality, medium_quality, high_quality)
        
    Returns:
        Path to the final video file
    """
    print("Rendering all clips...")
    clip_paths = await render_all_clips(clips_config, quality=quality)
    
    if not clip_paths:
        raise RuntimeError("No clips were successfully generated")
    
    print(f"Generated {len(clip_paths)} clips, stitching together...")
    final_path = stitch_videos(clip_paths, output_path)
    
    print(f"Final video saved to: {final_path}")
    return final_path


async def main():
    """Example usage"""
    # Load configuration from JSON file
    with open("video_config0.json", "r") as f:
        config = json.load(f)
    
    clips = config.get("clips", [])
    final_video = await generate_complete_video(clips, quality="low_quality")
    print(f"Complete video generated: {final_video}")


if __name__ == "__main__":
    asyncio.run(main())

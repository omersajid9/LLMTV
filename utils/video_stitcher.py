"""
Video Stitcher for LLMTV
Uses MoviePy to stitch together video segments with the full audio track.
"""

from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
from typing import List
from pathlib import Path


def stitch_videos(
    video_paths: List[str],
    audio_path: str,
    song_duration: float,
    output_path: str = "downloads/final_video.mp4"
) -> str:
    """
    Stitch together video segments with the full audio track.
    
    Args:
        video_paths: List of video file paths in order
        audio_path: Path to the full MP3 audio file
        song_duration: Duration of the song in seconds
        output_path: Path to save the final video
    
    Returns:
        Path to the final video file
    """
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load all video clips
        clips = []
        total_video_duration = 0
        
        for i, video_path in enumerate(video_paths):
            clip = VideoFileClip(video_path)
            
            # Calculate how much of this clip we need
            remaining_duration = song_duration - total_video_duration
            
            if remaining_duration <= 0:
                # We have enough video already
                clip.close()
                break
            
            if clip.duration > remaining_duration:
                # Trim the last clip to match song duration exactly
                clip = clip.subclip(0, remaining_duration)
            
            clips.append(clip)
            total_video_duration += clip.duration
        
        # Concatenate all video clips
        print("Concatenating video clips...")
        final_video = concatenate_videoclips(clips, method="compose")
        
        # Load the full audio
        print("Adding audio track...")
        audio = AudioFileClip(audio_path)
        
        # Set the audio of the concatenated video
        final_video = final_video.set_audio(audio)
        
        # Ensure video duration matches audio duration
        if final_video.duration > audio.duration:
            final_video = final_video.subclip(0, audio.duration)
        
        # Export the final video
        print("Exporting final video...")
        final_video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            preset="medium"
        )
        
        # Clean up
        for clip in clips:
            clip.close()
        audio.close()
        final_video.close()
        
        return output_path
    
    except Exception as e:
        raise Exception(f"Failed to stitch videos: {str(e)}")


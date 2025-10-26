"""
Music Generator for LLMTV
Uses Replicate's Minimax Music-1.5 model to create music from lyrics.
"""

import replicate
import os
from pathlib import Path
from .cache_manager import get_cache_key, get_cached_file, save_file_to_cache


def generate_music(lyrics: str, style_prompt: str, output_path: str = "downloads/song.mp3", use_cache: bool = True) -> tuple[str, float]:
    """
    Generate music from lyrics using Replicate's Minimax Music-1.5 model.
    
    Args:
        lyrics: Formatted lyrics string with structure tags
        style_prompt: Music style/genre description
        output_path: Path to save the generated MP3 file
        use_cache: Whether to use cached results if available
    
    Returns:
        Tuple of (file_path, duration_seconds)
    """
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Check cache first
    if use_cache:
        cache_key = get_cache_key("music", lyrics, style_prompt)
        cached_file = get_cached_file(cache_key, "mp3")
        if cached_file:
            print(f"✅ Using cached music file")
            # Copy from cache to output path
            import shutil
            shutil.copy(cached_file, output_path)
            # Get duration
            from moviepy.editor import AudioFileClip
            audio = AudioFileClip(output_path)
            duration = audio.duration
            audio.close()
            return output_path, duration
    
    try:
        # Call Replicate's Minimax Music-1.5 model
        output = replicate.run(
            "minimax/music-1.5",
            input={
                "lyrics": lyrics,
                "prompt": style_prompt,
                "bitrate": 256000,
                "sample_rate": 44100,
                "audio_format": "mp3"
            }
        )
        
        # Write the audio file to disk
        with open(output_path, "wb") as file:
            file.write(output.read())
        
        # Get duration using moviepy
        from moviepy.editor import AudioFileClip
        audio = AudioFileClip(output_path)
        duration = audio.duration
        audio.close()
        
        # Save to cache
        if use_cache:
            cache_key = get_cache_key("music", lyrics, style_prompt)
            save_file_to_cache(cache_key, output_path, "mp3")
        
        return output_path, duration
    
    except Exception as e:
        raise Exception(f"Failed to generate music: {str(e)}")


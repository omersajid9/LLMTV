"""
Transcriber for LLMTV
Uses Replicate's Incredibly Fast Whisper to transcribe audio with timestamps
and maps transcript chunks to 8-second video segments.
"""

import replicate
import math
from typing import List, Tuple
from .cache_manager import get_cache_key, get_cached_result, save_to_cache


def transcribe_audio(audio_path: str, use_cache: bool = True) -> dict:
    """
    Transcribe audio file using Replicate's Incredibly Fast Whisper.
    
    Args:
        audio_path: Path to the MP3 audio file
        use_cache: Whether to use cached results if available
    
    Returns:
        Dictionary with 'text' and 'chunks' (list of {text, timestamp})
    """
    
    # Check cache first
    if use_cache:
        # Use file content hash for cache key since audio files are large
        import hashlib
        with open(audio_path, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        cache_key = get_cache_key("transcription", file_hash)
        cached = get_cached_result(cache_key, "json")
        if cached:
            print(f"✅ Using cached transcription")
            return cached
    
    try:
        # Open the audio file and create a file object
        with open(audio_path, "rb") as audio_file:
            output = replicate.run(
                "vaibhavs10/incredibly-fast-whisper:3ab86df6c8f54c11309d4d1f930ac292bad43ace52d10c80d87eb258b3c9f79c",
                input={
                    "audio": audio_file,
                    "batch_size": 64
                }
            )
        
        # Save to cache
        if use_cache:
            import hashlib
            with open(audio_path, "rb") as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            cache_key = get_cache_key("transcription", file_hash)
            save_to_cache(cache_key, output, "json")
        
        return output
    
    except Exception as e:
        raise Exception(f"Failed to transcribe audio: {str(e)}")


def map_to_video_segments(transcription: dict, song_duration: float) -> List[Tuple[float, float, str]]:
    """
    Map transcript chunks to 8-second video segments.
    
    For each 8-second window, collect all overlapping transcript chunks
    and combine their lyrics as the video prompt for that segment.
    
    Args:
        transcription: Output from transcribe_audio with 'chunks'
        song_duration: Total duration of the song in seconds
    
    Returns:
        List of tuples: (start_time, end_time, lyrics_text)
    """
    
    chunks = transcription.get("chunks", [])
    if not chunks:
        # Fallback: use full text if no chunks
        full_text = transcription.get("text", "")
        num_segments = math.ceil(song_duration / 8)
        return [(i * 8, min((i + 1) * 8, song_duration), full_text) for i in range(num_segments)]
    
    # Calculate number of 8-second segments needed
    num_segments = math.ceil(song_duration / 8)
    video_segments = []
    
    for i in range(num_segments):
        segment_start = i * 8
        segment_end = min((i + 1) * 8, song_duration)
        
        # Find all transcript chunks that overlap with this 8-second window
        overlapping_lyrics = []
        
        for chunk in chunks:
            timestamp = chunk.get("timestamp", [None, None])
            chunk_start, chunk_end = timestamp
            
            # Skip chunks with invalid timestamps
            if chunk_start is None or chunk_end is None:
                continue
            
            # Check if chunk overlaps with current segment
            if chunk_start < segment_end and chunk_end > segment_start:
                overlapping_lyrics.append(chunk["text"].strip())
        
        # Combine overlapping lyrics
        segment_lyrics = " ".join(overlapping_lyrics) if overlapping_lyrics else transcription.get("text", "")
        
        video_segments.append((segment_start, segment_end, segment_lyrics))
    
    return video_segments


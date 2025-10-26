"""
Video Generator for LLMTV
Uses Google VEO3 API to generate 8-second video clips for each segment.
"""

import time
from google import genai
from pathlib import Path
from typing import List, Tuple
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from .cache_manager import get_cache_key, get_cached_file, save_file_to_cache


def generate_video_segment(client, lyrics_prompt: str, segment_index: int, genre: str = None, output_dir: str = "videos", use_cache: bool = True) -> str:
    """
    Generate a single 8-second video segment using VEO3.
    
    Args:
        client: Google GenAI client instance
        lyrics_prompt: Raw lyrics text for this segment
        segment_index: Index of the segment (for naming)
        genre: Music genre/style description for visual context
        output_dir: Directory to save video segments
        use_cache: Whether to use cached results if available
    
    Returns:
        Path to the generated video file
    """
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    output_path = f"{output_dir}/segment_{segment_index:03d}.mp4"
    
    # Construct enhanced VEO3 prompt
    if genre:
        veo3_prompt = f"create a short music video with this genre: {genre} visualizing these lyrics: {lyrics_prompt}"
    else:
        veo3_prompt = f"create a short music video visualizing these lyrics: {lyrics_prompt}"
    
    # Check cache first (include genre in cache key for different visual styles)
    if use_cache:
        cache_key = get_cache_key("video", veo3_prompt, segment_index)
        cached_file = get_cached_file(cache_key, "mp4")
        if cached_file:
            print(f"✅ Using cached video for segment {segment_index}")
            # Copy from cache to output path
            import shutil
            shutil.copy(cached_file, output_path)
            return output_path
    
    try:
        # Generate video using VEO3 with retry logic
        # Requires google-genai>=1.3.0
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                print(f"Segment {segment_index}: Attempt {attempt + 1}/{max_retries} - Starting video generation...")
                
                op = client.models.generate_videos(
                    model="veo-3.1-fast-generate-preview",
                    prompt=veo3_prompt,
                )
                
                # Poll until operation is complete (with timeout)
                max_poll_time = 600  # 10 minutes max per segment
                poll_start = time.time()
                poll_count = 0
                
                while not op.done:
                    elapsed = time.time() - poll_start
                    if elapsed > max_poll_time:
                        raise TimeoutError(f"Video generation exceeded {max_poll_time}s timeout")
                    
                    time.sleep(10)
                    poll_count += 1
                    if poll_count % 6 == 0:  # Every minute
                        print(f"Segment {segment_index}: Still generating... ({elapsed:.0f}s elapsed)")
                    
                    op = client.operations.get(op)
                
                print(f"Segment {segment_index}: Video generation complete!")
                break  # Success, exit retry loop
                
            except AttributeError as e:
                raise Exception(
                    "The google-genai package needs to be updated. "
                    "Please run: pip install --upgrade google-genai>=1.3.0"
                )
            except (TimeoutError, requests.exceptions.Timeout, OSError) as e:
                if attempt < max_retries - 1:
                    print(f"Segment {segment_index}: Timeout on attempt {attempt + 1}, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise Exception(f"Failed after {max_retries} attempts: {str(e)}")
        
        # Download the generated video with retry logic
        download_retries = 3
        for download_attempt in range(download_retries):
            try:
                print(f"Segment {segment_index}: Downloading video...")
                base_video = op.response.generated_videos[0]
                client.files.download(file=base_video.video)
                base_video.video.save(output_path)
                print(f"Segment {segment_index}: Download complete!")
                break
            except (TimeoutError, requests.exceptions.Timeout, OSError) as e:
                if download_attempt < download_retries - 1:
                    print(f"Segment {segment_index}: Download failed, retrying...")
                    time.sleep(5)
                else:
                    raise Exception(f"Failed to download video after {download_retries} attempts: {str(e)}")
        
        # Save to cache
        if use_cache:
            cache_key = get_cache_key("video", veo3_prompt, segment_index)
            save_file_to_cache(cache_key, output_path, "mp4")
        
        return output_path
    
    except Exception as e:
        raise Exception(f"Failed to generate video segment {segment_index}: {str(e)}")


def generate_all_videos(
    video_segments: List[Tuple[float, float, str]], 
    genre: str = None,
    output_dir: str = "videos", 
    use_cache: bool = True,
    max_workers: int = 4
) -> List[str]:
    """
    Generate all video segments for the music video in parallel.
    
    Args:
        video_segments: List of (start_time, end_time, lyrics_text) tuples
        genre: Music genre/style description for visual context
        output_dir: Directory to save video segments
        use_cache: Whether to use cached results if available
        max_workers: Maximum number of parallel video generations (default: 4)
    
    Returns:
        List of video file paths in order
    """
    
    # Initialize Google GenAI client
    client = genai.Client()
    
    # Dictionary to store results by index to maintain order
    video_results = {}
    
    print(f"\n🎥 Generating {len(video_segments)} video segments in parallel (max {max_workers} concurrent)...")
    
    # Define a worker function that includes the segment index
    def generate_segment_worker(segment_data):
        index, (start_time, end_time, lyrics) = segment_data
        try:
            video_path = generate_video_segment(
                client=client,
                lyrics_prompt=lyrics,
                segment_index=index,
                genre=genre,
                output_dir=output_dir,
                use_cache=use_cache
            )
            return (index, video_path, None)  # (index, path, error)
        except Exception as e:
            return (index, None, str(e))
    
    # Use ThreadPoolExecutor for parallel generation
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(generate_segment_worker, (i, segment)): i 
            for i, segment in enumerate(video_segments)
        }
        
        # Process completed tasks with progress bar
        with tqdm(total=len(video_segments), desc="Generating videos") as pbar:
            for future in as_completed(futures):
                index, video_path, error = future.result()
                
                if error:
                    print(f"\n❌ Failed to generate segment {index}: {error}")
                    raise Exception(f"Failed to generate segment {index}: {error}")
                
                video_results[index] = video_path
                pbar.update(1)
    
    # Return video paths in the correct order
    video_paths = [video_results[i] for i in range(len(video_segments))]
    
    print(f"✅ All {len(video_paths)} video segments generated successfully!")
    return video_paths


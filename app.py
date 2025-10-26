"""
LLMTV - AI Music Video Generator
Main Streamlit application that orchestrates the entire pipeline.
"""

import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv

# Import utility functions
from utils.llm_handler import generate_lyrics, generate_music_style_prompt
from utils.music_generator import generate_music
from utils.transcriber import transcribe_audio, map_to_video_segments
from utils.video_generator import generate_all_videos
from utils.video_stitcher import stitch_videos
from utils.cache_manager import clear_cache

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="LLMTV - AI Music Video Generator",
    page_icon="🎵",
    layout="centered"
)

# Create output directories
Path("downloads").mkdir(exist_ok=True)
Path("videos").mkdir(exist_ok=True)
Path("temp").mkdir(exist_ok=True)
Path("cache").mkdir(exist_ok=True)

# Title and description
st.title("🎵 LLMTV - AI Music Video Generator")
st.markdown("Generate complete music videos automatically from a simple prompt!")

# Cache controls in sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    use_cache = st.checkbox("Enable caching", value=True, help="Cache API results to speed up development")
    
    if st.button("🗑️ Clear Cache", help="Delete all cached results"):
        clear_cache()
        st.success("Cache cleared!")
        st.rerun()
    
    st.divider()
    st.caption("Caching speeds up debugging by storing expensive API results")

st.divider()

# Input form
with st.form("video_form"):
    concept_prompt = st.text_input(
        "Enter your video concept/prompt",
        placeholder="e.g., A song about cats taking over the world",
        help="Describe what you want your music video to be about"
    )
    
    style_description = st.text_area(
        "Music style/genre description (optional)",
        placeholder="e.g., Upbeat pop with electronic beats, catchy chorus",
        help="Describe the musical style you want. Leave blank for default."
    )
    
    model_choice = st.selectbox(
        "LLM Model for lyrics generation",
        options=[
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "anthropic/claude-3-5-sonnet-20241022",
            "anthropic/claude-3-5-haiku-20241022",
            "gemini/gemini-2.0-flash-exp",
            "gemini/gemini-1.5-pro",
            "gemini/gemini-1.5-flash"
        ],
        index=0
    )
    
    submit_button = st.form_submit_button("🎬 Generate Music Video", type="primary", use_container_width=True)

# Process the generation
if submit_button:
    if not concept_prompt:
        st.error("Please enter a video concept/prompt!")
    else:
        try:
            # Initialize session state for storing outputs
            if 'generated_lyrics' not in st.session_state:
                st.session_state.generated_lyrics = None
            if 'audio_path' not in st.session_state:
                st.session_state.audio_path = None
            if 'final_video_path' not in st.session_state:
                st.session_state.final_video_path = None
            
            # Step 1: Generate Lyrics
            with st.status("🎤 Step 1: Generating lyrics...", expanded=True) as status:
                st.write("Using AI to write song lyrics based on your prompt...")
                
                lyrics = generate_lyrics(concept_prompt, model=model_choice, use_cache=use_cache)
                st.session_state.generated_lyrics = lyrics
                
                st.success("✅ Lyrics generated!")
                st.code(lyrics, language=None)
                status.update(label="🎤 Step 1: Lyrics generated!", state="complete")
            
            # Step 2: Generate Music
            with st.status("🎹 Step 2: Creating music...", expanded=True) as status:
                st.write("Generating music from lyrics using Replicate's Minimax Music-1.5...")
                
                style_prompt = generate_music_style_prompt(concept_prompt, style_description)
                st.write(f"**Style:** {style_prompt}")
                
                audio_path, song_duration = generate_music(lyrics, style_prompt, use_cache=use_cache)
                st.session_state.audio_path = audio_path
                st.session_state.song_duration = song_duration
                
                st.success(f"✅ Music generated! Duration: {song_duration:.1f} seconds")
                st.audio(audio_path)
                status.update(label="🎹 Step 2: Music created!", state="complete")
            
            # Step 3: Transcribe with Timestamps
            with st.status("📝 Step 3: Transcribing with timestamps...", expanded=True) as status:
                st.write("Using Whisper to transcribe and timestamp the lyrics...")
                
                transcription = transcribe_audio(audio_path, use_cache=use_cache)
                st.success("✅ Transcription complete!")
                
                # Map to video segments
                video_segments = map_to_video_segments(transcription, song_duration)
                st.session_state.video_segments = video_segments
                
                st.write(f"**Mapped to {len(video_segments)} video segments**")
                
                status.update(label="📝 Step 3: Transcription complete!", state="complete")
            
            # Display transcript segments outside status context
            st.subheader("📋 Video Segments Preview")
            for i, (start, end, lyrics_text) in enumerate(video_segments):
                with st.expander(f"Segment {i+1}: {start:.1f}s - {end:.1f}s"):
                    st.write(lyrics_text)
            
            # Step 4: Generate Videos
            with st.status("🎥 Step 4: Generating videos...", expanded=True) as status:
                st.write(f"Creating {len(video_segments)} video segments using Google VEO3...")
                st.info("⚡ Generating videos in parallel (4 concurrent) - this is much faster!")
                
                # Estimate time
                estimated_time_parallel = max(5, len(video_segments) * 6 / 4)  # Rough estimate with 4 workers
                st.write(f"⏱️ Estimated time: ~{estimated_time_parallel:.0f} minutes")
                
                # Generate all videos in parallel
                try:
                    video_paths = generate_all_videos(
                        video_segments=video_segments,
                        genre=style_prompt,
                        output_dir="videos",
                        use_cache=use_cache,
                        max_workers=4  # Adjust this based on API rate limits
                    )
                    
                    st.session_state.video_paths = video_paths
                    st.success(f"✅ Generated {len(video_paths)} video segments!")
                    status.update(label="🎥 Step 4: Videos generated!", state="complete")
                    
                except Exception as e:
                    st.error(f"Failed to generate videos: {str(e)}")
                    raise
            
            # Step 5: Stitch Final Video
            with st.status("🎬 Step 5: Stitching final video...", expanded=True) as status:
                st.write("Combining all video segments with the full audio track...")
                
                final_video_path = stitch_videos(
                    video_paths=video_paths,
                    audio_path=audio_path,
                    song_duration=song_duration,
                    output_path="downloads/final_video.mp4"
                )
                st.session_state.final_video_path = final_video_path
                
                st.success("✅ Final video complete!")
                status.update(label="🎬 Step 5: Video stitched!", state="complete")
            
            # Display final video
            st.divider()
            st.subheader("🎉 Your Music Video is Ready!")
            st.video(final_video_path)
            
            # Download button
            with open(final_video_path, "rb") as file:
                st.download_button(
                    label="📥 Download Video",
                    data=file,
                    file_name="llmtv_music_video.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
        
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            st.exception(e)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>Made with ❤️ using Streamlit, LiteLLM, Replicate, and Google VEO3</p>
    <p><small>⚠️ Video generation can take 20-40 minutes for a 30-second song</small></p>
</div>
""", unsafe_allow_html=True)


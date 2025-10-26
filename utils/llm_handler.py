"""
LLM Handler for LLMTV
Uses LiteLLM to generate structured lyrics from a user prompt.
"""

from litellm import completion
import os
from .cache_manager import get_cache_key, get_cached_result, save_to_cache


def generate_lyrics(prompt: str, model: str = "openai/gpt-4o", use_cache: bool = True) -> str:
    """
    Generate structured lyrics from a user prompt using LiteLLM.
    
    Args:
        prompt: User's concept/prompt for the song
        model: LiteLLM model identifier (e.g., "openai/gpt-4o", "anthropic/claude-3-5-sonnet-20241022")
        use_cache: Whether to use cached results if available
    
    Returns:
        Formatted lyrics string with [Intro], [Verse], [Chorus] tags
    """
    
    # Check cache first
    if use_cache:
        cache_key = get_cache_key("lyrics", prompt, model)
        cached = get_cached_result(cache_key, "text")
        if cached:
            print(f"✅ Using cached lyrics")
            return cached
    
    system_prompt = """You are a creative lyricist. Generate engaging song lyrics based on the user's prompt.

CRITICAL: Keep lyrics under 550 characters total (will be truncated at 599).

Format your output with structure tags like:
[Intro]
lyrics here

[Verse]
lyrics here

[Chorus]
lyrics here

Keep verses concise and catchy. Make the song between 30-60 seconds when performed.
Only output the lyrics with tags, no additional commentary."""

    try:
        response = completion(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Write song lyrics about: {prompt}"}
            ],
            temperature=0.8,
        )
        
        lyrics = response.choices[0].message.content.strip()
        
        # Truncate to 599 characters for music generation API limit
        lyrics = lyrics[:599]
        
        # Save to cache
        if use_cache:
            cache_key = get_cache_key("lyrics", prompt, model)
            save_to_cache(cache_key, lyrics, "text")
        
        return lyrics
    
    except Exception as e:
        raise Exception(f"Failed to generate lyrics: {str(e)}")


def generate_music_style_prompt(concept: str, style_description: str = None) -> str:
    """
    Generate a music style prompt for the music generation model.
    
    Args:
        concept: User's video concept
        style_description: Optional music style/genre description
    
    Returns:
        Formatted style prompt string
    """
    
    if style_description:
        return style_description
    
    # Default to a general catchy style
    return "Catchy pop song with modern production, upbeat tempo, clear vocals"


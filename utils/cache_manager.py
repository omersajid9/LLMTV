"""
Cache Manager for LLMTV
Handles caching of expensive API calls to speed up development and debugging.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Optional, Any


CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)


def get_cache_key(*args, **kwargs) -> str:
    """
    Generate a cache key from function arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        MD5 hash of the arguments
    """
    cache_string = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
    return hashlib.md5(cache_string.encode()).hexdigest()


def get_cached_result(cache_key: str, result_type: str = "json") -> Optional[Any]:
    """
    Retrieve cached result if it exists.
    
    Args:
        cache_key: Cache key identifier
        result_type: Type of result ("json", "file", "text")
    
    Returns:
        Cached result or None if not found
    """
    cache_file = CACHE_DIR / f"{cache_key}.{result_type}"
    
    if not cache_file.exists():
        return None
    
    if result_type == "json":
        with open(cache_file, "r") as f:
            return json.load(f)
    elif result_type == "text":
        with open(cache_file, "r") as f:
            return f.read()
    elif result_type == "file":
        # Return the path to the cached file
        return str(cache_file)
    
    return None


def save_to_cache(cache_key: str, result: Any, result_type: str = "json") -> None:
    """
    Save result to cache.
    
    Args:
        cache_key: Cache key identifier
        result: Result to cache
        result_type: Type of result ("json", "file", "text")
    """
    cache_file = CACHE_DIR / f"{cache_key}.{result_type}"
    
    if result_type == "json":
        with open(cache_file, "w") as f:
            json.dump(result, f)
    elif result_type == "text":
        with open(cache_file, "w") as f:
            f.write(result)
    elif result_type == "file":
        # For files, we assume result is the path to copy from
        import shutil
        shutil.copy(result, cache_file)


def get_cached_file(cache_key: str, extension: str) -> Optional[str]:
    """
    Get cached file path if it exists.
    
    Args:
        cache_key: Cache key identifier
        extension: File extension (e.g., "mp3", "mp4")
    
    Returns:
        Path to cached file or None if not found
    """
    cache_file = CACHE_DIR / f"{cache_key}.{extension}"
    return str(cache_file) if cache_file.exists() else None


def save_file_to_cache(cache_key: str, source_path: str, extension: str) -> str:
    """
    Save a file to cache.
    
    Args:
        cache_key: Cache key identifier
        source_path: Path to the source file
        extension: File extension (e.g., "mp3", "mp4")
    
    Returns:
        Path to the cached file
    """
    import shutil
    cache_file = CACHE_DIR / f"{cache_key}.{extension}"
    shutil.copy(source_path, cache_file)
    return str(cache_file)


def clear_cache() -> None:
    """Clear all cached files."""
    import shutil
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
        CACHE_DIR.mkdir(exist_ok=True)


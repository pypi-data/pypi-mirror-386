"""Reading progress management for the Lue eBook reader."""

import os
import json
import re
import glob
from . import config


def get_progress_file_path(book_title):
    """
    Generate the file path for storing reading progress.
    
    Args:
        book_title: Title of the book
        
    Returns:
        str: Full path to the progress file
    """
    safe_title = re.sub(r'[^A-Za-z0-9]+', '', book_title)
    return os.path.join(config.PROGRESS_FILE_DIR, f"{safe_title}.progress.json")

def load_progress(progress_file):
    """
    Load basic reading progress from file.
    
    Args:
        progress_file: Path to the progress file
        
    Returns:
        tuple: (chapter_idx, paragraph_idx, sentence_idx)
    """
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                return data.get("c", 0), data.get("p", 0), data.get("s", 0)
            except json.JSONDecodeError:
                return 0, 0, 0
    return 0, 0, 0

def load_extended_progress(progress_file):
    """
    Load extended reading progress including UI state.
    
    Args:
        progress_file: Path to the progress file
        
    Returns:
        dict: Progress data with reading position and UI state
    """
    default_progress = {
        "c": 0, "p": 0, "s": 0,
        "scroll_offset": 0,
        "tts_enabled": True,
        "auto_scroll_enabled": True,
        "manual_scroll_anchor": None,
        "playback_speed": 1.0
    }
    
    if not os.path.exists(progress_file):
        return default_progress
        
    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {
                "c": data.get("c", 0),
                "p": data.get("p", 0), 
                "s": data.get("s", 0),
                "scroll_offset": data.get("scroll_offset", 0),
                "tts_enabled": data.get("tts_enabled", True),
                "auto_scroll_enabled": data.get("auto_scroll_enabled", True),
                "manual_scroll_anchor": data.get("manual_scroll_anchor", None),
                "playback_speed": data.get("playback_speed", 1.0)
            }
    except (json.JSONDecodeError, IOError):
        return default_progress

def save_progress(progress_file, chapter_idx, paragraph_idx, sentence_idx):
    """
    Save basic reading progress to file.
    
    Args:
        progress_file: Path to the progress file
        chapter_idx: Current chapter index
        paragraph_idx: Current paragraph index
        sentence_idx: Current sentence index
    """
    progress = {"c": chapter_idx, "p": paragraph_idx, "s": sentence_idx}
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2)

def save_extended_progress(progress_file, chapter_idx, paragraph_idx, sentence_idx, 
                          scroll_offset, tts_enabled, auto_scroll_enabled, manual_scroll_anchor=None, original_file_path=None, playback_speed=1.0):
    """
    Save extended reading progress including UI state.
    
    Args:
        progress_file: Path to the progress file
        chapter_idx: Current chapter index
        paragraph_idx: Current paragraph index
        sentence_idx: Current sentence index
        scroll_offset: Current scroll position
        tts_enabled: Whether TTS is enabled
        auto_scroll_enabled: Whether auto-scroll is enabled
        manual_scroll_anchor: Manual scroll anchor position (optional)
        original_file_path: Original path to the eBook file (optional)
    """
    progress = {
        "c": chapter_idx,
        "p": paragraph_idx, 
        "s": sentence_idx,
        "scroll_offset": float(scroll_offset),
        "tts_enabled": bool(tts_enabled),
        "auto_scroll_enabled": bool(auto_scroll_enabled),
        "playback_speed": float(playback_speed)
    }
    if manual_scroll_anchor:
        progress["manual_scroll_anchor"] = manual_scroll_anchor
    if original_file_path:
        progress["original_file_path"] = original_file_path
        
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2)

def validate_and_set_progress(chapters, progress_file, c, p, s):
    """
    Validate reading progress against document structure.
    
    Args:
        chapters: Document chapters structure
        progress_file: Path to progress file (for cleanup if invalid)
        c: Chapter index to validate
        p: Paragraph index to validate
        s: Sentence index to validate
        
    Returns:
        tuple: Valid (chapter_idx, paragraph_idx, sentence_idx)
    """
    try:
        paragraph = chapters[c][p]
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        _ = sentences[s]  # Test if sentence exists
        return c, p, s
    except IndexError:
        # Invalid progress, reset to beginning
        if os.path.exists(progress_file):
            os.remove(progress_file)
        return 0, 0, 0

def find_most_recent_book():
    """
    Find the most recently updated progress file and return the original file path.
    
    Returns:
        str or None: Path to the most recently read book, or None if no books found
    """
    progress_files = glob.glob(os.path.join(config.PROGRESS_FILE_DIR, "*.progress.json"))
    
    if not progress_files:
        return None
    
    # Find the most recently modified progress file
    most_recent_file = max(progress_files, key=os.path.getmtime)
    
    try:
        with open(most_recent_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            original_path = data.get("original_file_path")
            
            # Check if the original file still exists
            if original_path and os.path.exists(original_path):
                return original_path
                
    except (json.JSONDecodeError, IOError):
        pass
    
    return None
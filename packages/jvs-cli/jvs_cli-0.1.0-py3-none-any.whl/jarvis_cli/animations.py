from typing import List


class StatusIndicator:
    """Simple dot indicators for different states"""
    RUNNING = "·"
    COMPLETE = "·"
    ERROR = "·"
    

def get_status_text(status: str, theme_color: str) -> str:
    """Get formatted status indicator with color
    
    Args:
        status: Status type (running, complete, error)
        theme_color: Rich color string for the dot
        
    Returns:
        Formatted status string
    """
    dot = StatusIndicator.RUNNING
    return f"[{theme_color}]{dot}[/{theme_color}]"


def typewriter_effect_chunks(text: str, chunk_size: int = 3) -> List[str]:
    """Split text into chunks for typewriter effect

    Args:
        text: Text to split
        chunk_size: Number of characters per chunk

    Returns:
        List of progressively longer text chunks
    """
    if not text:
        return []

    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[:i + chunk_size])

    if chunks and chunks[-1] != text:
        chunks.append(text)

    return chunks

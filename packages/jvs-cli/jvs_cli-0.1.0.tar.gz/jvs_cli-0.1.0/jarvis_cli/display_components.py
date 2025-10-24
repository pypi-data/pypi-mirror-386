# Simplified display components for serial event stream
# Most components removed - simple serial printing is used instead

from dataclasses import dataclass
from typing import Optional

@dataclass
class PhaseStatus:
    """Simple phase status data class"""
    name: str
    status: str = "pending"
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    details: str = ""

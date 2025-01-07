from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

@dataclass
class WebResourceConfig:
    url: str
    interval: int
    pattern: Optional[str] = None

    @staticmethod
    def validate_interval(interval: int) -> bool:
        return 5 <= interval <= 300
    
@dataclass
class ResultRecord:
    url: str
    timestamp: datetime
    response_time: float
    status_code: Optional[int]
    re_pattern_found: Optional[bool]
    error_message: Optional[str]

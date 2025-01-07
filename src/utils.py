import logging
import re
import requests
from datetime import datetime, UTC
from typing import Optional
from .models import ResultRecord

def get_logger(mod_name):
    """
    To use this, do logger = get_module_logger(__name__)
    """
    logger = logging.getLogger(mod_name)
    handler = logging.FileHandler("monitoring.log", mode="a", encoding="utf-8")
    formatter = logging.Formatter(
        "{asctime} [{name}] {levelname} {message}",
        style="{",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

def monitor_resource(url: str, pattern: Optional[str]) -> ResultRecord:
    logger = get_logger("monitor")
    logger.debug(f"Monitor resource {url} with re pattern {pattern}")
    start_time = datetime.now(UTC)
    try:
        response = requests.get(url)
        re_match = None
        if pattern:
            re_match = bool(re.match(pattern, response.text))
        return ResultRecord(
                url=url,
                timestamp=start_time,
                response_time=response.elapsed.total_seconds(),
                status_code=response.status_code,
                re_pattern_found=re_match,
                error_message=None
            )
    except Exception as e:
        logger.error(f"Exception occured during {url} check {e}")
        return ResultRecord(
                url=url,
                timestamp=start_time,
                response_time=None,
                status_code=None,
                re_pattern_found=None,
                error_message=str(e)
            )

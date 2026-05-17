"""
api.py
claude.ai 내부 API를 호출해 사용량 데이터를 가져옵니다.
"""

import urllib.request
import urllib.error
import json
import time

import logger
from auth import get_valid_token

_log = logger.get("api")


API_URL = "https://api.anthropic.com/api/oauth/usage"


def fetch_usage() -> dict | None:
    """
    사용량 데이터를 반환합니다.
    실패 시 None 반환.

    응답 예시 키:
        five_hour, seven_day, seven_day_sonnet,
        extra_usage, ... (Anthropic이 추가하는 필드는 자동 표시)
    각 quota 객체: { "used": int, "limit": int, "reset_at": str (ISO8601) }
    """
    token = get_valid_token()
    if not token:
        return None

    req = urllib.request.Request(
        API_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "claude-code/1.0",
            "anthropic-beta": "oauth-2025-04-20",
        },
    )
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        _log.info("GET /api/oauth/usage → 200 (%dms)", (time.monotonic() - t0) * 1000)
        return data
    except urllib.error.HTTPError as e:
        _log.error("GET /api/oauth/usage → HTTP %d: %s (%dms)", e.code, e.reason, (time.monotonic() - t0) * 1000)
        if e.code == 429:
            raise
        return None
    except Exception as e:
        _log.error("GET /api/oauth/usage → %s: %s", type(e).__name__, e)
        return None

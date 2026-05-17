"""
auth.py
~/.claude/credentials.json 에서 OAuth 토큰을 읽고,
만료 시 Anthropic OAuth 엔드포인트로 직접 갱신합니다.
"""

import json
import time
import urllib.request
import urllib.error
from pathlib import Path

import logger
_log = logger.get("auth")


OAUTH_TOKEN_URL = "https://console.anthropic.com/v1/oauth/token"
# Claude Code의 공개 OAuth client_id (Anthropic이 변경 시 갱신 필요)
CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"

# 인증 상태: "ok" | "reauth_needed" | "no_credentials" | "no_refresh_token" | "transient"
_last_status = "ok"


def get_auth_status() -> str:
    """마지막 토큰 획득/갱신 시도 결과. UI에서 재로그인 안내용으로 사용."""
    return _last_status


CREDENTIALS_PATHS = [
    Path.home() / ".claude" / ".credentials.json",
    Path.home() / ".claude" / "credentials.json",
    Path(str(Path.home() / "AppData" / "Roaming" / "Claude" / "credentials.json")),
]


def _find_credentials_file() -> Path | None:
    for path in CREDENTIALS_PATHS:
        if path.exists():
            return path
    # CLAUDE_CONFIG_DIR 환경변수 지원
    import os
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    if config_dir:
        p = Path(config_dir) / "credentials.json"
        if p.exists():
            return p
    return None


def load_token() -> str | None:
    """credentials.json에서 액세스 토큰을 읽어 반환합니다."""
    path = _find_credentials_file()
    if not path:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        # 구조: {"claudeAiOauthAccount": {..., "accessToken": "...", "expiresAt": ...}}
        account = data.get("claudeAiOauth") or data.get("claudeAiOauthAccount") or data.get("oauthAccount") or {}
        return account.get("accessToken")
    except Exception:
        return None


def is_token_expired() -> bool:
    """토큰이 만료됐는지 확인합니다 (만료 60초 전부터 갱신 시도)."""
    path = _find_credentials_file()
    if not path:
        return True
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        account = data.get("claudeAiOauth") or data.get("claudeAiOauthAccount") or data.get("oauthAccount") or {}
        expires_at = account.get("expiresAt", 0)
        remaining = (expires_at / 1000) - time.time()
        if remaining < 60:
            _log.debug("token expired (remaining=%.0fs)", remaining)
        return remaining < 60
    except Exception:
        return True


def refresh_token() -> bool:
    """OAuth refresh_token으로 새 access token을 받아 credentials.json에 기록합니다."""
    global _last_status
    path = _find_credentials_file()
    if not path:
        _last_status = "no_credentials"
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        _last_status = "no_credentials"
        return False
    account = data.get("claudeAiOauth") or data.get("claudeAiOauthAccount") or data.get("oauthAccount")
    if not account:
        _last_status = "no_credentials"
        return False

    rt = account.get("refreshToken")
    if not rt:
        _log.error("no refreshToken in credentials.json")
        _last_status = "no_refresh_token"
        return False

    body = json.dumps({
        "grant_type": "refresh_token",
        "refresh_token": rt,
        "client_id": CLIENT_ID,
    }).encode("utf-8")
    req = urllib.request.Request(
        OAUTH_TOKEN_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "claude-code/1.0",
        },
        method="POST",
    )
    _log.info("refreshing token...")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            err_body = ""
        _last_status = "reauth_needed" if e.code in (400, 401) else "transient"
        _log.error("refresh failed HTTP %d: %s %s → status=%s", e.code, e.reason, err_body[:120], _last_status)
        return False
    except Exception as e:
        _last_status = "transient"
        _log.error("refresh error: %s: %s", type(e).__name__, e)
        return False

    # 새 토큰을 기존 구조 보존하며 머지 (scopes/subscriptionType/rateLimitTier 등 유지)
    account["accessToken"] = payload["access_token"]
    if payload.get("refresh_token"):
        account["refreshToken"] = payload["refresh_token"]
    account["expiresAt"] = int(time.time() * 1000) + int(payload.get("expires_in", 3600)) * 1000

    # 원자적 쓰기 (temp → replace)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)
    expires_in = int(payload.get("expires_in", 3600))
    _log.info("token refreshed — expires in %ds", expires_in)
    _last_status = "ok"
    return True


def get_valid_token() -> str | None:
    """만료 여부 확인 후 유효한 토큰을 반환합니다."""
    global _last_status
    if is_token_expired():
        refresh_token()  # _last_status 자체 갱신
    else:
        # 토큰이 유효 → 이전에 reauth_needed 등으로 떨어졌어도 복구
        _last_status = "ok"
    return load_token()

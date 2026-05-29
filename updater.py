"""
updater.py
GitHub Releases API를 통한 업데이트 확인.
"""

import json
import re
import urllib.request
import urllib.error

import logger

_log = logger.get("updater")

GITHUB_REPO = "Sayh0/ullmananamazzi"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
RELEASE_PAGE = f"https://github.com/{GITHUB_REPO}/releases/latest"


def _parse_version(tag: str) -> tuple[int, ...] | None:
    """'v1.3.2' 또는 '1.3.2' → (1, 3, 2)"""
    m = re.match(r"v?(\d+(?:\.\d+)*)", tag)
    if not m:
        return None
    return tuple(int(x) for x in m.group(1).split("."))


def check_update(current_version: str) -> str | None:
    """최신 릴리스 버전이 current_version보다 높으면 태그 문자열 반환, 아니면 None."""
    try:
        req = urllib.request.Request(
            RELEASES_URL,
            headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "ullmananamazzi"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        tag = data.get("tag_name", "")
        latest = _parse_version(tag)
        current = _parse_version(current_version)

        if latest and current and latest > current:
            _log.info("update available: %s → %s", current_version, tag)
            return tag

        return None
    except Exception as e:
        _log.debug("update check failed: %s", e)
        return None

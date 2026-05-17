# Changelog

## 2026-05-17

### Fixed

- **OAuth 토큰 자동 갱신 복구** (`auth.py`)
  Claude Code v2.1.141부터 `claude auth refresh` 서브커맨드가 제거되어 위젯이 만료 토큰을 갱신하지 못하고 무한 401을 받던 문제 수정.
  CLI 호출을 제거하고 `credentials.json`의 `refreshToken`으로 `https://console.anthropic.com/v1/oauth/token`에 직접 OAuth refresh를 보내도록 변경.
  - client_id: Claude Code 공개 값 사용 (`9d1c250a-e61b-44d9-88ed-5944d1962f5e`)
  - 응답으로 받은 새 `accessToken`/`refreshToken`(회전 가능)/`expiresAt`를 기존 파일 구조(`scopes`, `subscriptionType`, `rateLimitTier` 등) 보존하며 atomic write(temp → replace)로 저장.

- **Cloudflare 1010 차단 회피** (`auth.py`)
  Python `urllib` 기본 User-Agent(`Python-urllib/3.x`)가 Cloudflare에 의해 403/1010으로 차단되던 문제.
  OAuth refresh 요청에 `User-Agent: claude-code/1.0` 헤더 추가 (기존 `api.py`와 동일한 UA).

### Added

- **재로그인 필요 상태 감지 및 UI 안내** (`auth.py`, `overlay.py`, `popup.html`, `main.py`)
  refresh 실패 사유를 4가지로 분류해 위젯이 사용자에게 명확히 안내하도록 함.
  - `reauth_needed`: refresh 응답이 HTTP 400/401 → refreshToken 자체가 무효
  - `no_credentials`: `~/.claude/.credentials.json` 파일 없음
  - `no_refresh_token`: 파일은 있으나 `refreshToken` 필드 비어있음
  - `transient`: 네트워크/5xx/403/timeout 등 일시적 문제 (재시도 대상)

  앞 세 상태일 때 위젯 본문에 **"재로그인 필요 — `claude` → `/login`"** 안내가 빨간 글씨로 표시됨.
  `transient`는 기존 동작 그대로 (`Update failed` + 흐림 처리).

  공개 API:
  - `auth.get_auth_status() -> str`
  - `OverlayWindow.mark_stale(reason: str | None = None)`
  - JS `markStale(reason)`

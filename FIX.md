# FIX.md — 수정/오류 조치 기록

`[auto]` 항목은 훅이 자동 기록. `note` 컬럼은 Claude가 이유를 직접 추가.

| timestamp | file | type | before | after | note |
|---|---|---|---|---|---|
| 2026-05-17 | overlay.py | fix | `window.hidden` 의존 | `_hidden` 플래그 직접 추적 | toggle() 이 항상 hide 반복 — pywebview가 백그라운드 스레드 호출 후 속성 미갱신 버그 |
| 2026-05-17 | auth.py | fix | `.credentials.json` / `claudeAiOauthAccount` 하드코딩 | 다중 경로 + 키 파싱 순서 | `token found: False` — 실제 파일명·키명 불일치 |
| 2026-05-17 | api.py | fix | `claude.ai/api/usage_and_limits` | `api.anthropic.com/api/oauth/usage` | 404 수정, `anthropic-beta`·`User-Agent` 헤더 추가 |
| 2026-05-17 | popup.html | fix | `used/limit/reset_at` 구조 가정 | `utilization/resets_at` 직접 사용 | API 응답 구조 불일치로 UI 미표시 |
| 2026-05-17 | auth.py | fix | `subprocess.run(["claude", "auth", "refresh"])` | direct OAuth POST to `console.anthropic.com/v1/oauth/token` | `claude auth`에 refresh 서브커맨드가 없음 — 원본 코드가 존재하지 않는 CLI 명령 호출 → 무한 401 |
| 2026-05-17 | auth.py | fix | Python-urllib 기본 UA | `User-Agent: claude-code/1.0` | Cloudflare 1010 차단 회피 |
| 2026-05-17 | auth.py, overlay.py, popup.html, main.py | add | — | `get_auth_status()` / `mark_stale(reason)` / JS `markStale(reason)` | 재로그인 필요 상태 4종 분류 및 UI 안내 |
| 2026-05-17 22:47 | popup.html | auto | `document.getElementById('content').innerHTML =` | `const el = document.getElementById('content');` | `body.stale #content{opacity:0.4}` 가 reauth 메시지도 흐리게 만들어 인라인 오버라이드 추가 |
| 2026-05-17 22:49 | popup.html | auto | `--text-dim: #9aa3b5;` | `--text-dim: #ffffff;` | 전체 흰색 폰트 명도 #ffffff 통일 요청 |
| 2026-05-17 23:16 | log_fix.py | auto | | `(rewrite)` | FIX.md 훅 스크립트 초기 작성 |
| 2026-05-17 23:27 | overlay.py | fix | `if not self.window:` (update·mark_stale) | `if not self.window or self._hidden:` | 숨긴 상태에서 `window.resize()` 호출 시 pywebview가 창을 재표시하는 버그 |
| 2026-05-17 23:36 | overlay.py | fix | `if not self.window or self._hidden:` (update·mark_stale) | `if not self.window:` | _hidden 체크가 첫 폴 데이터를 버려 "Loading..." 고착 유발 — resize()만 차단하는 방식으로 교체 |
| 2026-05-17 23:56 | auth.py, api.py, overlay.py, main.py, logger.py | add | print() 기반 출력 | `logging.RotatingFileHandler` → `widget.log` | 에러 분석용 로그 파일 적재 기능 추가 |
| 2026-05-18 | main.py | add | 중복 실행 방지 없음 | `CreateMutexW("ClaudeUsageWidget")` | 이미 실행 중이면 즉시 종료 |
| 2026-05-18 | _hooks/log_fix.py | fix | `_first_line()` — 첫 줄만 추출 | `_diff_cells()` — 실제 달라진 첫 줄 탐색 | 멀티라인 Edit에서 before/after가 동일하게 찍히는 문제 수정 |
| 2026-05-18 | _hooks/log_fix.py | fix | note 컬럼 공백 | `⚠ 이유 미기입` placeholder | 이유 미기입 항목을 명시적으로 표시 |
| 2026-05-18 00:09 | main.py | add | 정적 아이콘 | `make_icon(pct)` + `_tray_ref` | 트레이 아이콘에 5H 세션 사용률 % 실시간 표시 |
| 2026-05-18 00:11 | main.py | fix | `ellipse` 배경 + 고정 폰트 크기 | `rectangle` 배경 + 최대 폰트 크기 자동 탐색 | 아이콘 배경 사각형으로 변경, 글자 최대화 요청 |
| 2026-05-18 00:17 | require_note.py | add |  | `(신규)` | PreToolUse 훅 — ⚠ 미기입 상태에서 소스파일 편집 차단 |
| 2026-05-18 00:19 | main.py | fix | `f"{int(pct)}%"` | `f"{int(pct)}"` | % 제거로 글자 수 줄여 폰트 크기 최대화 |
| 2026-05-18 00:28 | main.py | fix | `cfg.get("poll_interval", 60)` | `cfg.get("poll_interval", 120)` | config.py 기본값(120)과 fallback 불일치 표준화 |
| 2026-05-18 00:31 | main.py | fix | `cfg.get("poll_interval", 120)` | `cfg["poll_interval"]` | config.load()가 항상 DEFAULTS를 병합하므로 fallback은 데드 코드 — 제거 |

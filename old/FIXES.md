# Bug Fixes

## 1. 위젯 창 토글 안 됨

**증상:** 트레이 아이콘 좌클릭 시 창이 표시되지 않음.

**원인:** `pywebview`의 `window.hidden` 속성이 pystray 백그라운드 스레드에서 `hide()`를 호출한 후 업데이트되지 않는 버그. `toggle()`이 항상 `hidden=False`로 인식해서 `show()` 대신 `hide()`만 반복 호출.

**수정:** `window.hidden`에 의존하지 않고 `OverlayWindow._hidden` 플래그로 직접 상태를 추적.

---

## 2. API 인증 실패 (credentials 경로/키 불일치)

**증상:** `token found: False` — 토큰을 읽지 못해 API 호출 불가.

**원인:**
- 파일명: `credentials.json`을 찾았으나 실제 파일은 `.credentials.json`
- JSON 키: `claudeAiOauthAccount`를 읽었으나 실제 키는 `claudeAiOauth`

**수정 (`auth.py`):**
- `CREDENTIALS_PATHS`에 `.credentials.json` 경로 추가 (기존 경로는 fallback으로 유지)
- 키 파싱 순서: `claudeAiOauth` → `claudeAiOauthAccount` → `oauthAccount`

---

## 3. API 엔드포인트 404

**증상:** `HTTP 404: Not Found` — 사용량 데이터를 가져오지 못함.

**원인:** `https://claude.ai/api/usage_and_limits`는 존재하지 않는 엔드포인트.

**수정 (`api.py`):**
- URL: `https://api.anthropic.com/api/oauth/usage`
- 헤더 추가: `anthropic-beta: oauth-2025-04-20`, `User-Agent: claude-code/1.0`

참고: [jens-duttke/usage-monitor-for-claude](https://github.com/jens-duttke/usage-monitor-for-claude)

---

## 4. UI 데이터 구조 불일치

**증상:** API는 성공하지만 위젯에 아무것도 표시되지 않음.

**원인:** `popup.html`이 `{ used, limit, reset_at }` 구조를 기대했으나 실제 API 응답은 `{ utilization, resets_at }` 구조.

**수정 (`popup.html`):**
- `quotaRow()`: `used/limit`으로 퍼센트 계산 → `utilization` 직접 사용, `reset_at` → `resets_at`
- `extraUsageRow()`: `enabled`/`used` → `is_enabled`/`used_credits`/`monthly_limit`/`utilization`

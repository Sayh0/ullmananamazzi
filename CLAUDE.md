# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude.ai 구독 사용량(5시간 세션, 주간 한도)을 실시간 모니터링하는 Windows 트레이 위젯. Python + pywebview로 구현.

## Commands

```bash
# 실행
pip install -r requirements.txt
python main.py

# EXE 빌드
pip install pyinstaller
python build.py
# 결과: dist/ullmananamazzi/ 폴더
```

테스트 프레임워크 없음. 수동 테스트로 검증.

## Architecture

**스레딩 모델**: pywebview가 메인 스레드 점유 (블로킹). pystray 트레이 아이콘과 API 폴링은 각각 daemon 스레드.

**데이터 흐름**: `auth.py`(토큰 로드/갱신) → `api.py`(사용량 API 호출) → `overlay.py`(JS eval로 UI 전달) → `popup.html`(렌더링)

**모듈 역할**:
- `main.py` — 진입점. 트레이 아이콘 빌드, 폴링 루프, 단일 인스턴스 락(Windows Mutex)
- `auth.py` — `~/.claude/.credentials.json`에서 OAuth 토큰 읽기. 만료 60초 전 자동 갱신 (직접 OAuth 엔드포인트 호출). 상태: ok/reauth_needed/no_credentials/no_refresh_token/transient
- `api.py` — `api.anthropic.com/api/oauth/usage` 폴링. 429 에러만 re-raise (폴링 루프에서 5분 대기)
- `overlay.py` — pywebview 창 관리. `updateData()`, `markStale()`, `setMode()` JS 함수 호출로 UI 갱신
- `config.py` — config.json 읽기/저장 + Windows 레지스트리 자동시작 설정
- `logger.py` — RotatingFileHandler (512KB x 3). 네임스페이스: `widget.*`
- `popup.html` — 위젯 UI. Simple/Detailed 모드. `pywebview.api`로 Python 콜백

**외부 의존성**: pywebview, pystray, Pillow. 네트워크는 urllib 표준 라이브러리만 사용.

**비공식 API 주의**: `api.anthropic.com/api/oauth/usage`는 공식 API가 아니며 언제든 변경될 수 있음. CLIENT_ID(`9d1c250a-...`)도 Claude Code의 공개값이므로 Anthropic 변경 시 `auth.py` 업데이트 필요.

## Behavioral Guidelines

Reduce common LLM coding mistakes. Bias toward caution over speed.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
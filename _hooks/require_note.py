"""PreToolUse hook: FIX.md에 미기입 note가 있으면 소스파일 편집을 차단."""
import sys
import json
from pathlib import Path

FIX_MD = Path(__file__).parent.parent / "FIX.md"
PLACEHOLDER = "⚠ 이유 미기입"
SOURCE_EXTS = {".py", ".html", ".js"}


def main():
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        return

    tool = data.get("tool_name", "")
    if tool not in ("Edit", "Write"):
        return

    file_path = data.get("tool_input", {}).get("file_path", "")

    # FIX.md 편집은 허용 (note 채우는 중)
    if Path(file_path).name == "FIX.md":
        return

    # 소스파일 편집만 검사
    if Path(file_path).suffix not in SOURCE_EXTS:
        return

    if not FIX_MD.exists():
        return

    if PLACEHOLDER in FIX_MD.read_text(encoding="utf-8"):
        print(f"FIX.md에 '{PLACEHOLDER}' 항목이 있습니다. note를 채운 뒤 편집하세요.", file=sys.stderr)
        sys.exit(1)


main()

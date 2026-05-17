"""PostToolUse hook: Edit/Write 발생 시 FIX.md 표에 행 자동 추가."""
import sys
import json
import datetime
from pathlib import Path

SOURCE_EXTS = {".py", ".html", ".js"}
FIX_MD = Path(__file__).parent.parent / "FIX.md"
TABLE_HEADER = "| timestamp | file | type | before | after | note |"


def _fmt(line: str, limit: int = 80) -> str:
    line = line.strip().replace("|", "\\|")
    if len(line) > limit:
        line = line[:limit] + "…"
    return f"`{line}`" if line else ""


def _diff_cells(old: str, new: str) -> tuple[str, str]:
    """old/new 에서 실제로 달라진 첫 번째 줄 쌍을 반환."""
    old_lines = old.strip().splitlines()
    new_lines = new.strip().splitlines()
    for o, n in zip(old_lines, new_lines):
        if o.strip() != n.strip():
            return _fmt(o), _fmt(n)
    # 길이만 다른 경우 (순수 추가/삭제)
    longer = old_lines if len(old_lines) > len(new_lines) else new_lines
    idx = min(len(old_lines), len(new_lines))
    extra = _fmt(longer[idx]) if idx < len(longer) else ""
    if len(old_lines) > len(new_lines):
        return extra, ""
    return "", extra


def main():
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        return

    tool = data.get("tool_name", "")
    inp = data.get("tool_input", {})
    file_path = inp.get("file_path", "")

    if tool not in ("Edit", "Write"):
        return
    if Path(file_path).suffix not in SOURCE_EXTS:
        return

    name = Path(file_path).name
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    if tool == "Edit":
        before, after = _diff_cells(inp.get("old_string", ""), inp.get("new_string", ""))
    else:
        before, after = "", "`(rewrite)`"

    row = f"| {ts} | {name} | auto | {before} | {after} | ⚠ 이유 미기입 |"

    text = FIX_MD.read_text(encoding="utf-8") if FIX_MD.exists() else ""

    if TABLE_HEADER not in text:
        text = text.rstrip() + f"\n\n{TABLE_HEADER}\n|---|---|---|---|---|---|\n"

    FIX_MD.write_text(text.rstrip() + "\n" + row + "\n", encoding="utf-8")


main()

"""
config.py
config.json 읽기/저장. 키 없으면 기본값 사용.
"""

import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"

DEFAULTS = {
    "always_on_top_overlay": False,   # True: 상시 오버레이 / False: 트레이 클릭 시 팝업
    "start_with_windows": False,      # 윈도우 시작 시 자동 실행
    "display_mode": "simple",         # "simple" | "detailed"
    "poll_interval": 120,             # API 폴링 간격 (초)
    "overlay_x": 20,                  # 오버레이 위치 X
    "overlay_y": 20,                  # 오버레이 위치 Y
}


def load() -> dict:
    if CONFIG_PATH.exists():
        try:
            saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return {**DEFAULTS, **saved}
        except Exception:
            pass
    return dict(DEFAULTS)


def save(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def set_start_with_windows(enabled: bool) -> None:
    """레지스트리를 통해 윈도우 시작 시 자동 실행을 설정합니다."""
    import sys
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "ullmananamazzi"
        exe_path = sys.executable if getattr(sys, "frozen", False) else f'"{sys.executable}" "{Path(__file__).parent / "main.py"}"'

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, str(exe_path))
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
    except Exception as e:
        print(f"[config] 자동 시작 설정 실패: {e}")

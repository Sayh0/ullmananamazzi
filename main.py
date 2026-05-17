"""
main.py
Claude Usage Widget - 진입점
트레이 아이콘 + 폴링 루프 + 오버레이 창 통합
"""

import sys
import threading
import time
from pathlib import Path

import config
import api
import auth
import logger
from overlay import OverlayWindow

logger.setup()
_log = logger.get("main")


def _acquire_instance_lock():
    import ctypes
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "ClaudeUsageWidget")
    if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        _log.warning("already running — exiting duplicate instance")
        sys.exit(0)
    return mutex  # GC 방지용 — 프로세스 종료까지 유지


def main():
    _lock = _acquire_instance_lock()
    _log.info("widget started pid=%d python=%s", __import__("os").getpid(), sys.version.split()[0])
    cfg = config.load()
    overlay = OverlayWindow(cfg, on_mode_change=lambda mode: config.save(cfg))

    # ── 트레이 아이콘 이미지 생성 ────────────────────────────
    _tray_ref = [None]  # poll_loop에서 아이콘 갱신용 참조

    def make_icon(pct: float | None = None) -> "Image.Image":
        from PIL import Image, ImageDraw, ImageFont
        SIZE, PAD = 64, 3
        img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        if pct is None:
            bg, text = (80, 80, 80, 255), "--"
        elif pct >= 100:
            bg, text = (224, 92, 92, 255), "!!"
        else:
            bg, text = (217, 119, 87, 255), f"{int(pct)}"

        draw.rectangle([0, 0, SIZE - 1, SIZE - 1], fill=bg)

        # 들어갈 수 있는 최대 폰트 크기 탐색
        font = None
        for font_path in ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"]:
            try:
                for size in range(48, 8, -1):
                    f = ImageFont.truetype(font_path, size)
                    bb = draw.textbbox((0, 0), text, font=f)
                    if (bb[2] - bb[0]) <= SIZE - PAD * 2 and (bb[3] - bb[1]) <= SIZE - PAD * 2:
                        font = f
                        break
                if font:
                    break
            except Exception:
                pass
        if font is None:
            font = ImageFont.load_default()

        bb = draw.textbbox((0, 0), text, font=font)
        x = (SIZE - (bb[2] - bb[0])) / 2 - bb[0]
        y = (SIZE - (bb[3] - bb[1])) / 2 - bb[1]
        draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
        return img

    # ── 폴링 스레드 ──────────────────────────────────────────
    def poll_loop():
        while True:
            try:
                data = api.fetch_usage()
                if data:
                    overlay.update(data)
                    pct = (data.get("five_hour") or {}).get("utilization")
                    if _tray_ref[0] and pct is not None:
                        _tray_ref[0].icon = make_icon(pct)
                    _log.debug("poll ok — five_hour utilization=%.1f%%", pct or 0)
                else:
                    status = auth.get_auth_status()
                    overlay.mark_stale(status)
                    if _tray_ref[0]:
                        _tray_ref[0].icon = make_icon(None)
                    _log.warning("poll returned no data — auth_status=%s", status)
                time.sleep(cfg["poll_interval"])
            except Exception as e:
                status = auth.get_auth_status()
                overlay.mark_stale(status)
                _log.error("poll exception — %s: %s — sleeping 300s", type(e).__name__, e)
                time.sleep(300)  # 429 등 오류 시 5분 대기

    poll_thread = threading.Thread(target=poll_loop, daemon=True)
    poll_thread.start()

    # ── 트레이 아이콘 ────────────────────────────────────────
    def build_tray():
        import pystray

        def on_toggle(icon, item):
            if cfg.get("always_on_top_overlay"):
                overlay.toggle()
            else:
                overlay.toggle()

        def on_overlay_toggle(icon, item):
            enabled = not cfg.get("always_on_top_overlay", False)
            cfg["always_on_top_overlay"] = enabled
            overlay.set_on_top(enabled)
            config.save(cfg)

        def on_startup_toggle(icon, item):
            enabled = not cfg.get("start_with_windows", False)
            cfg["start_with_windows"] = enabled
            config.set_start_with_windows(enabled)
            config.save(cfg)

        def on_mode_simple(icon, item):
            cfg["display_mode"] = "simple"
            overlay.update_mode("simple")
            config.save(cfg)

        def on_mode_detailed(icon, item):
            cfg["display_mode"] = "detailed"
            overlay.update_mode("detailed")
            config.save(cfg)

        def on_quit(icon, item):
            config.save(cfg)
            icon.stop()
            if overlay.window:
                overlay.window.destroy()
            sys.exit(0)

        menu = pystray.Menu(
            pystray.MenuItem("Show / Hide", on_toggle, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Always on Top",
                on_overlay_toggle,
                checked=lambda item: cfg.get("always_on_top_overlay", False),
            ),
            pystray.MenuItem(
                "Start with Windows",
                on_startup_toggle,
                checked=lambda item: cfg.get("start_with_windows", False),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Display Mode", pystray.Menu(
                pystray.MenuItem(
                    "Simple",
                    on_mode_simple,
                    checked=lambda item: cfg.get("display_mode") == "simple",
                    radio=True,
                ),
                pystray.MenuItem(
                    "Detailed",
                    on_mode_detailed,
                    checked=lambda item: cfg.get("display_mode") == "detailed",
                    radio=True,
                ),
            )),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", on_quit),
        )

        icon = pystray.Icon("ClaudeUsage", make_icon(), "Claude Usage", menu)
        return icon

    tray_icon = build_tray()
    _tray_ref[0] = tray_icon

    # pystray를 백그라운드 스레드에서 실행 (pywebview가 메인 스레드 필요)
    tray_thread = threading.Thread(target=tray_icon.run, daemon=True)
    tray_thread.start()

    # webview 준비 완료 후 호출되는 콜백 (별도 스레드에서 실행됨)
    def on_ready():
        if cfg.get("always_on_top_overlay", False):
            overlay.show()

    # 오버레이를 메인 스레드에서 실행 (블로킹)
    overlay.start(on_ready=on_ready)


if __name__ == "__main__":
    main()

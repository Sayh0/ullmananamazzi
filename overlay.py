"""
overlay.py
pywebview를 사용해 팝업 또는 상시 오버레이 창을 관리합니다.
"""

import json
import sys
import threading
from pathlib import Path

import logger
_log = logger.get("overlay")


def _resource(filename: str) -> Path:
    """PyInstaller EXE 번들 여부에 관계없이 올바른 리소스 경로 반환."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / filename
    return Path(__file__).parent / filename


HTML_PATH = _resource("popup.html")


class OverlayWindow:
    def __init__(self, cfg: dict, on_mode_change=None):
        self.cfg = cfg
        self.on_mode_change = on_mode_change
        self.window = None
        self._webview = None
        self._lock = threading.Lock()
        self._hidden = False

    def _import_webview(self):
        import webview
        return webview

    def start(self, on_ready=None):
        """오버레이 창을 시작합니다. 블로킹 호출 — 메인 스레드에서 실행하세요."""
        webview = self._import_webview()

        always_on_top = self.cfg.get("always_on_top_overlay", False)
        x = self.cfg.get("overlay_x", 20)
        y = self.cfg.get("overlay_y", 20)

        self._webview = webview
        # 항상 숨긴 상태로 시작 — on_ready에서 always_on_top 시 표시
        self._hidden = True

        self.window = webview.create_window(
            title="Claude Usage",
            url=str(HTML_PATH.resolve()),
            width=200,
            height=160,
            x=x,
            y=y,
            resizable=False,
            frameless=True,
            on_top=always_on_top,
            transparent=False,
            background_color="#0d0f12",
            hidden=True,
            js_api=self._make_api(),
        )

        # 작업 표시줄에서 숨기기
        self.window.events.shown += self._hide_from_taskbar

        # 창 이동 시 위치 저장
        self.window.events.moved += self._on_moved

        webview.start(debug=False, func=on_ready, gui="edgechromium")

    def _make_api(self):
        """JS에서 pywebview.api.xxx() 로 호출 가능한 API 객체."""
        overlay = self

        class Api:
            def set_mode(self, mode: str):
                overlay.cfg["display_mode"] = mode
                if overlay.on_mode_change:
                    overlay.on_mode_change(mode)

            def resize(self, height: int):
                if overlay.window and not overlay._hidden:
                    overlay.window.resize(200, int(height))

            def close(self):
                overlay.hide()

        return Api()

    def _hide_from_taskbar(self):
        """WS_EX_TOOLWINDOW 스타일 적용으로 작업 표시줄에서 숨김."""
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            GWL_EXSTYLE = -20
            WS_EX_TOOLWINDOW = 0x00000080
            WS_EX_APPWINDOW = 0x00040000

            # EnumWindows로 현재 프로세스의 창 찾기
            pid = __import__("os").getpid()
            found_hwnd = []

            @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
            def enum_cb(hwnd, _):
                wnd_pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(wnd_pid))
                if wnd_pid.value == pid and user32.IsWindowVisible(hwnd):
                    found_hwnd.append(hwnd)
                return True

            user32.EnumWindows(enum_cb, 0)

            for hwnd in found_hwnd:
                style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                style = (style | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW
                user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
                # 변경 적용을 위해 숨겼다 다시 표시
                user32.ShowWindow(hwnd, 0)  # SW_HIDE
                user32.ShowWindow(hwnd, 5)  # SW_SHOW

            _log.info("hide_from_taskbar: applied to %d window(s)", len(found_hwnd))
        except Exception as e:
            _log.warning("hide_from_taskbar failed: %s", e)

    def _on_moved(self, x, y):
        self.cfg["overlay_x"] = x
        self.cfg["overlay_y"] = y

    def update(self, data: dict):
        """사용량 데이터를 UI에 전달합니다."""
        if not self.window:
            return
        payload = json.dumps(data, ensure_ascii=False)
        mode = self.cfg.get("display_mode", "simple")
        interval = self.cfg.get("poll_interval", 60)
        js = f"updateData({payload}, '{mode}', {interval});"
        try:
            self.window.evaluate_js(js)
        except Exception as e:
            _log.error("JS eval error: %s", e)

    def mark_stale(self, reason: str | None = None):
        """데이터 갱신 실패 시 UI를 흐리게 표시합니다.

        reason: auth.get_auth_status() 반환값을 전달하면 UI가 재로그인 안내 등으로 분기.
        """
        if not self.window:
            return
        arg = json.dumps(reason) if reason is not None else "null"
        try:
            self.window.evaluate_js(f"markStale({arg});")
        except Exception:
            pass

    def show(self):
        """팝업 모드: 창을 표시합니다."""
        if self.window:
            try:
                self.window.show()
                self._hidden = False
                self._hide_from_taskbar()
            except Exception:
                pass

    def hide(self):
        """팝업 모드: 창을 숨깁니다."""
        if self.window:
            try:
                self.window.hide()
                self._hidden = True
            except Exception:
                pass

    def toggle(self):
        """팝업 모드: 토글."""
        if self.window:
            if self._hidden:
                self.show()
            else:
                self.hide()

    def update_mode(self, mode: str):
        """표시 모드(simple/detailed)를 UI에 반영합니다."""
        if not self.window:
            return
        try:
            self.window.evaluate_js(f"setMode('{mode}', false);")
        except Exception as e:
            print(f"[overlay] update_mode error: {e}")

    def set_animation(self, enabled: bool):
        """Clawd 애니메이션 표시 여부를 변경합니다."""
        if not self.window:
            return
        try:
            self.window.evaluate_js(f"setAnimation({str(enabled).lower()});")
        except Exception:
            pass

    def set_on_top(self, enabled: bool):
        """항상 위 표시 여부를 변경합니다."""
        self.cfg["always_on_top_overlay"] = enabled
        if self.window:
            try:
                self.window.on_top = enabled
            except Exception:
                pass

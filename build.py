"""
build.py
PyInstaller로 단일 EXE를 생성합니다.

사용법:
    pip install pyinstaller
    python build.py
"""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent


def build():
    args = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                        # 단일 EXE
        "--windowed",                       # 콘솔 창 숨김
        "--name", "ullmananamazzi",
        "--add-data", f"{HERE / 'popup.html'};.",   # HTML을 EXE에 번들
        "--hidden-import", "pystray._win32",
        "--hidden-import", "PIL._tkinter_finder",
        "main.py",
    ]

    print("Building EXE...")
    result = subprocess.run(args, cwd=HERE)

    if result.returncode == 0:
        exe = HERE / "dist" / "ullmananamazzi.exe"
        print(f"\nDone: {exe}")
        print("  dist/ullmananamazzi.exe 를 원하는 곳에 복사해서 실행하세요.")
    else:
        print("\nBuild failed")
        sys.exit(1)


if __name__ == "__main__":
    build()

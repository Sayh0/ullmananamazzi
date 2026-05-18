"""
build.py
PyInstaller로 EXE를 생성합니다.

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
        "--onedir",                         # 폴더 배포 (즉시 실행)
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
        out = HERE / "dist" / "ullmananamazzi"
        print(f"\nDone: {out}")
        print("  dist/ullmananamazzi/ 폴더를 배포하세요. 안의 ullmananamazzi.exe를 실행합니다.")
    else:
        print("\nBuild failed")
        sys.exit(1)


if __name__ == "__main__":
    build()

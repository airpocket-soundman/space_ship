"""ブラウザ版(Pyxel Web Launcher の play=)用に、ゲーム一式を 1 つの .pyxapp にまとめる。

python tools/build_pyxapp.py  → web/starx.pyxapp
run= でリポジトリのファイルを 1 つずつ読むより、1 回のダウンロードで済むぶん起動が速い。
main に push すると GitHub Actions(.github/workflows/build-pyxapp.yml)が作り直してコミットする。
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "starx.pyxapp"


def main():
    with tempfile.TemporaryDirectory() as tmp:
        # 遊ぶのに必要なものだけを入れる
        app_dir = Path(tmp) / OUT.stem
        app_dir.mkdir()
        shutil.copy(ROOT / "main.py", app_dir)
        shutil.copytree(ROOT / "game", app_dir / "game", ignore=shutil.ignore_patterns("__pycache__"))
        # 会話の挿絵(illustrations)は、ゲームでまだ表示していないので入れない(大きいので Web 版が重くなる)
        shutil.copytree(ROOT / "assets", app_dir / "assets",
                        ignore=shutil.ignore_patterns("*.py", "__pycache__", "illustrations"))
        subprocess.run([sys.executable, "-m", "pyxel", "package", str(app_dir), str(app_dir / "main.py")],
                       cwd=tmp, check=True, stdout=subprocess.DEVNULL)
        OUT.parent.mkdir(exist_ok=True)
        shutil.copy(Path(tmp) / OUT.name, OUT)
    print(f"{OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()

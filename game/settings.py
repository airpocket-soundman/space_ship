"""起動設定(言語と画面サイズ)の保存と、設定を変えたときの起動し直し。

Pyxel は起動後に画面サイズを変えられないので、画面サイズを変えたら起動し直す。
- パソコン: ~/.pyxel/airpocket/starx/settings.json に保存し、新しいプロセスで起動し直す
- ブラウザ(Pyxel Web): ブラウザの localStorage に保存し、URL に ?screen=...&lang=... を付けて読み込み直す
"""

import json
import subprocess
import sys
from pathlib import Path

KEY = "starx_settings"
MAIN = Path(__file__).resolve().parent.parent / "main.py"


def _js():
    try:
        import js  # Pyxel の Web 版(Pyodide)のときだけある

        return js
    except ImportError:
        return None


def is_web():
    return _js() is not None


def _path():
    # pyxel.user_data_dir("airpocket", "starx") と同じ場所(Pyxel の起動前にも使えるよう直接組み立てる)
    return Path.home() / ".pyxel" / "airpocket" / "starx" / "settings.json"


def load():
    """保存した {"screen": ..., "lang": ...}。なければ None。"""
    try:
        js = _js()
        text = js.localStorage.getItem(KEY) if js else (_path().read_text(encoding="utf-8") if _path().exists() else None)
        return json.loads(str(text)) if text else None
    except Exception:
        return None


def save(screen, lang):
    text = json.dumps({"screen": screen, "lang": lang})
    try:
        js = _js()
        if js:
            js.localStorage.setItem(KEY, text)
        else:
            _path().parent.mkdir(parents=True, exist_ok=True)
            _path().write_text(text, encoding="utf-8")
    except Exception:
        pass


def relaunch(screen, lang):
    """選んだ画面サイズ・言語で起動し直す。"""
    import pyxel

    js = _js()
    if js:
        params = js.URLSearchParams.new(js.location.search)
        params.set("screen", screen)
        params.set("lang", lang)
        js.location.search = "?" + str(params.toString())
        return
    subprocess.Popen([sys.executable, str(MAIN), screen, lang], cwd=str(MAIN.parent))
    pyxel.quit()

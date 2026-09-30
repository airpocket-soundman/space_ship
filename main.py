import sys

from game import i18n, ui
from game.app import App
from game.missions import MISSIONS


def options():
    """画面サイズ・言語・開始ステージ。コマンドラインか、ブラウザで動くときは URL の ?screen=...&lang=... から読む。"""
    args = sys.argv[1:]
    try:
        import js  # Pyxel の Web 版(Pyodide)のときだけある
        from urllib.parse import parse_qs

        query = parse_qs(str(js.location.search).lstrip("?"))
        args = [v[0] for k, v in query.items() if k in ("screen", "lang", "stage")] + args
    except ImportError:
        pass
    screen = next((a for a in args if a in ui.SCREENS), "640x480")
    lang = next((a for a in args if a in i18n.LANGS), "ja")
    stage = next((a for a in args if a in MISSIONS), None)
    return screen, lang, stage


if __name__ == "__main__":
    # python main.py 720x720 en  のように画面サイズと言語を選べる(既定は 640x480・日本語)
    # python main.py 3-1  のようにステージを付けると、そのステージから始まる(動作確認用)
    screen, lang, stage = options()
    App(screen=screen, lang=lang, stage=stage).run()

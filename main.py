import sys

from game import i18n, settings, ui
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
    screen = next((a for a in args if a in ui.SCREENS), None)
    lang = next((a for a in args if a in i18n.LANGS), None)
    stage = next((a for a in args if a in MISSIONS), None)
    saved = settings.load() or {}
    setup = screen is None and "screen" not in saved  # 何も決まっていなければ、選ぶ画面から
    screen = screen or saved.get("screen") or "320x240"
    lang = lang or saved.get("lang") or "ja"
    if screen not in ui.SCREENS or lang not in i18n.LANGS:
        screen, lang, setup = "320x240", "ja", True
    return screen, lang, stage, setup


if __name__ == "__main__":
    # 初回は 320x240 で言語と画面サイズを選ぶ画面が出る(選んだ設定は保存され、次から使われる)
    # python main.py 720x720 en  のように画面サイズと言語を指定すると、それで起動する
    # python main.py 3-1  のようにステージを付けると、そのステージから始まる(動作確認用)
    screen, lang, stage, setup = options()
    App(screen=screen, lang=lang, stage=stage, setup=setup and not stage).run()

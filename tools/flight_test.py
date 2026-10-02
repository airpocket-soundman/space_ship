"""飛行パートだけを確かめる: ステージをメニューから選んで、すぐに飛ぶ。

python tools/flight_test.py [640x480|720x720|360x360|320x240] [ja|en] [mute]

メニュー:  ↑↓ でステージを選ぶ / SPACE・Z・Enter で飛ぶ / ←→ で「点検あり・なし」を切り替える / ESC で終了
飛行中:    Q でメニューに戻る(飛行の操作はゲーム本体と同じ)
飛行が終わると(SPACE で続ける)、結果をメニューに書いて戻る。会社画面やセーブは通らない。
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pyxel  # noqa: E402

from game import audio, i18n, state, ui  # noqa: E402
from game.i18n import tr  # noqa: E402
from game.missions import MISSIONS, OPENING, ORDER  # noqa: E402
from game.scene_dock import DockScene  # noqa: E402
from game.scene_mission import MissionScene  # noqa: E402
from game.state import GameState  # noqa: E402

KIND = {"ascent": "上昇", "orbit": "軌道投入", "reentry": "再突入", "dock": "接近", "hop": "ホップ",
        "landing": "着陸", "recover": "打上+着陸"}
OPENING = "open"  # メニューの先頭: オープニングの飛行(操作説明つき、必ず爆発する)


class MenuScene:
    def __init__(self, app):
        self.app = app
        self.frame = 0
        audio.bgm(None)
        audio.engine(0)

    def update(self):
        self.frame += 1
        app = self.app
        n = len(app.items)
        if ui.up_p():
            app.sel = (app.sel - 1) % n
        if ui.down_p():
            app.sel = (app.sel + 1) % n
        if ui.left_p() or ui.right_p():
            app.state.inspected = not app.state.inspected
        if ui.confirm():
            app.launch(app.items[app.sel])

    def draw(self):
        app = self.app
        pyxel.cls(ui.NAVY)
        small, K = ui.COMPACT, ui.K  # 720x720 は文字が 2 倍なので、詰めた配置を 2 倍に
        fs = 10 if small else 12
        lh = (11 if ui.TINY else 14 if small else 18) * K
        m = (6 if small else 20) * K
        y = (4 if ui.TINY else 8) * K
        ui.text(m, y, "飛行テスト", ui.YELLOW, size=fs)
        insp = "点検あり" if app.state.inspected else "点検なし"
        ui.text(ui.W - m - ui.text_width(f"←→ {tr(insp)}", fs), y, f"←→ {tr(insp)}",
                ui.LIME if app.state.inspected else ui.WHITE, size=fs)
        y += lh + (2 if ui.TINY else 6) * K
        for i, item in enumerate(app.items):
            sel = i == app.sel
            if sel:
                pyxel.rect(m - 3 * K, y - 2 * K, ui.W - (m - 3 * K) * 2, lh, ui.DBLUE)
            if item == OPENING:
                label = tr("オープニング(必ず爆発する)")
                kind = tr("上昇")
            else:
                mdef = MISSIONS[item]
                label = tr(mdef.title)
                kind = tr(KIND[mdef.kind])
            ui.text(m, y, label, ui.WHITE if sel else ui.GRAY, size=fs)
            kx = ui.W * (0.42 if small else 0.45)
            if not ui.TINY:
                ui.text(kx, y, kind, ui.CYAN if sel else ui.DBLUE, size=fs)
            res = app.results.get(item)
            if res:
                col = ui.LIME if res.startswith(("S", "A", "B", "C")) and len(res) == 1 else ui.RED
                text = tr("成功 ") + res if len(res) == 1 else res
                if ui.text_width(text, 10) > ui.W * 0.4:  # 長い失敗の理由は収まらないので短く
                    text = tr("失敗")
                w = ui.text_width(text, 10)
                ui.text(ui.W - m - w, y + (fs - 10) * K, text, col, size=10)
            y += lh
        hint = "↑↓ 選ぶ  SPACE 飛ぶ  飛行中 Q でメニュー  ESC 終了"
        if y + 4 * K < ui.H - 12 * K:
            ui.text(m, ui.H - 14 * K, hint, ui.GRAY, size=10)


class FlightTestApp:
    """飛行シーンが必要とする分だけを持つ、ゲーム本体(App)の代わり。"""

    def __init__(self, screen, lang, mute):
        ui.set_screen(screen)
        i18n.set_lang(lang)
        state.ENABLED = False  # セーブはしない
        audio.MUTE = mute
        pyxel.init(ui.W, ui.H, title="StarX flight test", fps=60, quit_key=pyxel.KEY_ESCAPE)
        ui.load_fonts()
        audio.setup()
        self.state = GameState()
        self.items = [OPENING] + [m.id for m in ORDER]
        self.sel = 1
        self.results = {}  # 項目 → 最後の結果(ランク or 失敗の理由)
        self.current = None
        self.scene = MenuScene(self)

    def run(self):
        pyxel.run(self.update, self.draw)

    def update(self):
        if not isinstance(self.scene, MenuScene) and pyxel.btnp(pyxel.KEY_Q):
            self.to_menu()
            return
        self.scene.update()

    def draw(self):
        self.scene.draw()

    def launch(self, item):
        self.current = item
        if item == OPENING:
            self.scene = MissionScene(self, OPENING, cold_open=True)
            return
        mdef = MISSIONS[item]
        self.scene = DockScene(self, mdef) if mdef.kind == "dock" else MissionScene(self, mdef)

    def to_menu(self):
        audio.engine(0)
        self.scene = MenuScene(self)

    # ---- 飛行シーンから呼ばれる ----
    def finish_mission(self, run):
        self.results[self.current] = run.rank() if run.result == "success" else tr(run.fail_reason)
        self.to_menu()

    def after_cold_open(self):
        self.results[OPENING] = tr("爆発(予定どおり)")
        self.to_menu()


if __name__ == "__main__":
    args = sys.argv[1:]
    screen = next((a for a in args if a in ui.SCREENS), "640x480")
    lang = next((a for a in args if a in i18n.LANGS), "ja")
    FlightTestApp(screen, lang, mute="mute" in args).run()

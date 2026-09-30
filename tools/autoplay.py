"""ゲームを自動操作してスクリーンショットを撮る(動作確認用)。

python tools/autoplay.py [640x480|720x720|360x360|320x240] [ja|en] [--quick]  → tools/shots/<画面サイズ>[_en]/*.png
タイトル → オープニングの飛行(操作説明・爆発) → 「4年前」 → キックオフ・プロローグ → 点検 → 打上
→ Ch1-1 を自動操縦 → リザルト → 工場 まで進める。オープニングの画面は 00_*.png。
"""

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pyxel  # noqa: E402
from PIL import Image  # noqa: E402

from game import i18n, ui  # noqa: E402
from game.app import App  # noqa: E402
from game.scene_misc import CaptionScene, ResultScene, TitleScene  # noqa: E402
from game.scene_mission import MissionScene  # noqa: E402
from game.scene_office import OfficeScene  # noqa: E402

SCREEN = next((a for a in sys.argv[1:] if a in ui.SCREENS), "640x480")
LANG = next((a for a in sys.argv[1:] if a in i18n.LANGS), "ja")
OUT = ROOT / "tools" / "shots" / (SCREEN + ("" if LANG == "ja" else f"_{LANG}"))
OUT.mkdir(parents=True, exist_ok=True)
QUICK = "--quick" in sys.argv


def capture(name):
    w, h = pyxel.width, pyxel.height
    pal = list(pyxel.colors)
    img = Image.new("RGB", (w, h))
    px = img.load()
    scr = pyxel.screen
    for y in range(h):
        for x in range(w):
            c = pal[scr.pget(x, y)]
            px[x, y] = (c >> 16 & 255, c >> 8 & 255, c & 255)
    img.save(OUT / f"{name}.png")
    print("shot", name, flush=True)


class Bot:
    def __init__(self):
        self.held = set()
        self.tap_keys = set()
        self.step = "title"
        self.t = 0
        self.shots = set()
        self.queue = []  # オフィスで押すキーの列

    def tap(self, key):
        pyxel.set_btn(key, True)
        self.tap_keys.add(key)

    def hold(self, key, on):
        if on and key not in self.held:
            pyxel.set_btn(key, True)
            self.held.add(key)
        elif not on and key in self.held:
            pyxel.set_btn(key, False)
            self.held.discard(key)

    def shot_once(self, name):
        if name not in self.shots:
            self.shots.add(name)
            self.pending = name

    def __call__(self, app, phase):
        if phase == "draw":
            name = getattr(self, "pending", None)
            if name:
                capture(name)
                self.pending = None
            return
        for k in list(self.tap_keys):
            pyxel.set_btn(k, False)
        self.tap_keys.clear()
        self.t += 1
        sc = app.scene

        if isinstance(sc, TitleScene):
            if self.t == 40:
                self.shot_once("01_title")
            if QUICK and self.t == 50:
                import game.title_earth as te
                sc.earth.theta += 0.5
                self.shot_once("01b_title_day")
            if QUICK and self.t == 58:
                sc.earth.theta += 1.3
                self.shot_once("01c_title_night")
            if QUICK and self.t == 70:
                pyxel.quit()
            if self.t == 60:
                self.tap(pyxel.KEY_SPACE)
            return

        if isinstance(sc, OfficeScene):
            if not sc.dlg.active:
                if "03_office_menu" not in self.shots:
                    self.shot_once("03_office_menu")
                    self.queue = ([pyxel.KEY_RIGHT] * 1 + [pyxel.KEY_SPACE]  # 点検
                                  + ["wait"] + [pyxel.KEY_RIGHT] * 2 + [pyxel.KEY_SPACE])  # 打上
                    return
                if "09_office_after" in self.shots or app.state.flights:
                    self.shot_once("09_office_after")
                    if self.t % 90 == 0:
                        pyxel.quit()
                    return
                if self.t % 12 == 0 and self.queue:
                    k = self.queue.pop(0)
                    if k != "wait":
                        self.tap(k)
                return
            if self.t % 10 == 0:
                if "02_office_dialog" not in self.shots and sc.dlg.index == 3 and sc.dlg.waiting():
                    self.shot_once("02_office_dialog")
                    return
                if app.state.flights and "09_office_after" not in self.shots and sc.dlg.waiting():
                    self.shot_once("09_office_after")
                    return
                self.tap(pyxel.KEY_SPACE)
                if QUICK and "02_office_dialog" in self.shots:
                    pyxel.quit()
            return

        if isinstance(sc, CaptionScene):
            if sc.frame == 60:
                self.shot_once("00_caption")
            if sc.frame == 70:
                self.tap(pyxel.KEY_SPACE)
            return

        if isinstance(sc, MissionScene) and sc.cold_open:
            # オープニング: 操作説明の場面を撮りながら普通に飛ばす(途中で必ず爆発する)
            v = sc.v
            if sc.phase == "count" and sc.count < 3:
                self.shot_once("00_open_count")
            if sc.phase == "ready":
                self.shot_once("00_open_ignite")
                if self.t % 30 == 0:
                    self.tap(pyxel.KEY_SPACE)
            if sc.phase == "flight":
                err = v.theta + 1.2 * v.omega
                self.hold(pyxel.KEY_LEFT, err > math.radians(0.8))
                self.hold(pyxel.KEY_RIGHT, err < -math.radians(0.8))
                self.hold(pyxel.KEY_UP, v.throttle_cmd < 1.0)
                if 4 < v.t < 4.1:
                    self.shot_once("00_open_throttle")
                if sc.run.fire_active:
                    self.shot_once("00_open_fire")
            if sc.phase == "end":
                for k in list(self.held):
                    self.hold(k, False)
                if sc.end_timer == 70:
                    self.shot_once("00_open_end")
                if sc.end_timer == 90:
                    self.tap(pyxel.KEY_SPACE)
            return

        if isinstance(sc, MissionScene):
            run, v = sc.run, sc.v
            if sc.phase == "count" and sc.count < 3:
                self.shot_once("04_countdown")
            if sc.phase == "ready":
                self.tap(pyxel.KEY_SPACE)
            if sc.phase == "flight":
                err = v.theta + 1.2 * v.omega
                self.hold(pyxel.KEY_LEFT, err > math.radians(0.8))
                self.hold(pyxel.KEY_RIGHT, err < -math.radians(0.8))
                fire = run.fire_active and v.t - run.fire_at > 0.6
                self.hold(pyxel.KEY_DOWN, fire)
                self.hold(pyxel.KEY_UP, not run.fire_active and v.throttle_cmd < 1.0)
                if 1.5 < v.t < 1.6:
                    self.shot_once("05_liftoff")
                if 18 < v.t < 18.1:
                    self.shot_once("06_ascent")
                if run.fire_active and v.t - run.fire_at > 1.5:
                    self.shot_once("07_fire")
                if 40 < v.t < 40.1:
                    self.shot_once("08_high")
            if sc.phase == "end":
                for k in list(self.held):
                    self.hold(k, False)
                if sc.end_timer == 70:
                    self.shot_once("10_end")
                if sc.end_timer == 90:
                    self.tap(pyxel.KEY_SPACE)
            return

        if isinstance(sc, ResultScene):
            if sc.frame == 40:
                self.shot_once("11_result")
            if sc.frame == 60:
                self.tap(pyxel.KEY_SPACE)
            return


if __name__ == "__main__":
    App(hook=Bot(), screen=SCREEN, lang=LANG).run()

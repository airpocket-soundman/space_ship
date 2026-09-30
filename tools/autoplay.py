"""ゲームを自動操作してスクリーンショットを撮る(動作確認用)。

python tools/autoplay.py [640x480|720x720|360x360|320x240] [ja|en] [--quick]  → tools/shots/<画面サイズ>[_en]/*.png
    タイトル → オープニングの飛行(操作説明・爆発) → 「4年前」 → キックオフ・プロローグ → 点検 → 打上
    → Ch1-1 を自動操縦 → リザルト → 工場 まで進める。オープニングの画面は 00_*.png。

python tools/autoplay.py 3-3 [画面サイズ] [言語] [--fast] [--inspect]  → tools/shots/<画面サイズ>[_en]/3-3_*.png
    そのステージだけを、会社画面 → 打上 → 自動操縦 → リザルト → 会社画面 まで進める。
    自動操縦は tools/sim_check.py と同じもの。--fast は 6 倍速(待ち時間を縮める)、--inspect は点検してから飛ぶ。
    最後に、1 フレームの処理時間とパーティクルの数を出す。

自動操作のあいだは音を鳴らさない(鳴らしたいときは --sound)。セーブもしない。
"""

import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import pyxel  # noqa: E402
from PIL import Image  # noqa: E402

import sim_check  # noqa: E402
from game import audio, i18n, state, ui  # noqa: E402
from game.app import App  # noqa: E402
from game.missions import MISSIONS  # noqa: E402
from game.scene_dock import DockScene  # noqa: E402
from game.scene_misc import CaptionScene, ResultScene, TitleScene  # noqa: E402
from game.scene_mission import MissionScene  # noqa: E402
from game.scene_office import OfficeScene  # noqa: E402

SCREEN = next((a for a in sys.argv[1:] if a in ui.SCREENS), "640x480")
LANG = next((a for a in sys.argv[1:] if a in i18n.LANGS), "ja")
STAGE = next((a for a in sys.argv[1:] if a in MISSIONS), None)
OUT = ROOT / "tools" / "shots" / (SCREEN + ("" if LANG == "ja" else f"_{LANG}"))
OUT.mkdir(parents=True, exist_ok=True)
QUICK = "--quick" in sys.argv
state.ENABLED = False  # 自動操作では、遊んでいるセーブを上書きしない
audio.MUTE = "--sound" not in sys.argv  # 自動操作では音を鳴らさない(--sound を付けたときだけ鳴らす)
FAST = 6 if "--fast" in sys.argv else 1
INSPECT = "--inspect" in sys.argv


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


class StageBot(Bot):
    """1 つのステージを、会社画面から自動操縦で最後まで進める。"""

    def __init__(self, stage):
        super().__init__()
        self.stage = stage
        self.pilot = None
        self.n = 0  # 撮った枚数
        self.last_shot = -999
        self.flown = False
        self.peak = 0  # パーティクルの最大数
        self.prev = None

    def snap(self, label):
        self.n += 1
        self.pending = f"{self.stage}_{self.n:02d}_{label}"

    def __call__(self, app, phase):
        if phase == "draw":
            return super().__call__(app, phase)
        for k in list(self.tap_keys):
            pyxel.set_btn(k, False)
        self.tap_keys.clear()
        self.t += 1
        sc = app.scene

        if isinstance(sc, OfficeScene):
            for k in list(self.held):
                self.hold(k, False)
            if sc.dlg.active:
                if self.flown and "after" not in self.shots and sc.dlg.waiting() and sc.dlg.index == 0:
                    self.shots.add("after")
                    self.snap("office_after")
                    return
                if self.t % (6 * FAST) == 0:
                    self.tap(pyxel.KEY_SPACE)
                return
            if self.flown:
                if "end" not in self.shots:
                    self.shots.add("end")
                    self.snap("office_end")
                    self.quit_at = self.t + 10 * FAST
                elif self.t >= self.quit_at:
                    self.report(app)
                    pyxel.quit()
                return
            if "office" not in self.shots:
                self.shots.add("office")
                self.snap("office")
                self.queue = (([pyxel.KEY_RIGHT, pyxel.KEY_SPACE, "wait", pyxel.KEY_RIGHT, pyxel.KEY_RIGHT]
                               if INSPECT else [pyxel.KEY_RIGHT] * 3) + ["wait", pyxel.KEY_SPACE])
                return
            if self.t % (12 * FAST) == 0 and self.queue:
                k = self.queue.pop(0)
                if k != "wait":
                    self.tap(k)
            return

        if isinstance(sc, DockScene):
            run = sc.run
            if sc.phase == "flight":
                d = run.dist
                spd = min(2.5, 0.9 + math.sqrt(run.ACCEL * max(0.0, d - run.ZONE - 4))) if d > run.ZONE \
                    else min(0.9, 0.08 * d + 0.05)
                if d < run.BOX * 0.5:
                    spd = 0.0
                wx, wy = -run.x / max(d, 0.01) * spd, -run.y / max(d, 0.01) * spd
                self.hold(pyxel.KEY_RIGHT, wx - run.vx > 0.04)
                self.hold(pyxel.KEY_LEFT, wx - run.vx < -0.04)
                self.hold(pyxel.KEY_UP, wy - run.vy > 0.04)
                self.hold(pyxel.KEY_DOWN, wy - run.vy < -0.04)
                if self.t - self.last_shot > 60 * 20:
                    self.last_shot = self.t
                    self.snap("dock")
            self.finish(sc)
            return

        if isinstance(sc, MissionScene):
            run = sc.run
            self.peak = max(self.peak, sc.parts.count())
            if sc.phase == "count" and sc.count < 1.0 and "count" not in self.shots:
                self.shots.add("count")
                self.snap("count")
            if sc.phase == "ready":
                # SPACE を 1 フレームだけ押したことにする(早回しでは同じ押下が何度も読まれるので、直接呼ぶ)
                run.space()
                sc.phase = "flight"
            if sc.phase == "flight":
                if self.pilot is None:
                    self.pilot = sim_check.make_pilot(run)
                steer, thr = self.pilot()
                self.hold(pyxel.KEY_RIGHT, steer > 0)
                self.hold(pyxel.KEY_LEFT, steer < 0)
                self.hold(pyxel.KEY_UP, thr > 0)
                self.hold(pyxel.KEY_DOWN, thr < 0)
                # 場面が変わったとき(点火・停止・段の切り替わり・早送り)と、一定時間ごとに撮る
                key = (run.phase, run.stage_no, run.v.engine_on, run.warp > 1, run.in_orbit)
                if key != self.prev and self.t - self.last_shot > 45:
                    self.prev = key
                    self.last_shot = self.t
                    self.shot_at = self.t + 50  # 変わった少しあとを撮る
                if getattr(self, "shot_at", None) == self.t:
                    self.snap(f"{run.phase}_t{run.v.t:.0f}")
                elif self.t - self.last_shot > 60 * 25:
                    self.last_shot = self.t
                    self.snap(f"{run.phase}_t{run.v.t:.0f}")
            self.finish(sc)
            return

        if isinstance(sc, ResultScene):
            self.flown = True
            if sc.frame >= 40 and "result" not in self.shots:
                self.shots.add("result")
                self.snap("result")
            elif sc.frame >= 60 and "result" in self.shots:
                self.tap(pyxel.KEY_SPACE)

    def report(self, app):
        """1 フレームの処理時間と、パーティクルの数。"""
        for k, v in self.cost.items():
            if v:
                v.sort()
                print(f"{k:6}: 平均 {sum(v) / len(v) * 1000:.2f} ms  99% {v[int(len(v) * 0.99)] * 1000:.2f} ms  "
                      f"最大 {v[-1] * 1000:.2f} ms")
        print("パーティクルの最大数", self.peak, " 結果", app.state.flights[-1] if app.state.flights else None,
              flush=True)

    def finish(self, sc):
        if sc.phase != "end":
            return
        for k in list(self.held):
            self.hold(k, False)
        if sc.end_timer >= 70 and "banner" not in self.shots:
            self.shots.add("banner")
            self.snap("end")
        elif sc.end_timer >= 90 and "banner" in self.shots:
            self.tap(pyxel.KEY_SPACE)


def run_stage():
    bot = StageBot(STAGE)
    app = App(hook=bot, screen=SCREEN, lang=LANG, stage=STAGE)
    cost = bot.cost = {"update": [], "draw": []}

    # 飛行画面だけを計る(スクリーンショットを撮るフレームは除く)
    def update():
        for _ in range(FAST):
            t0 = time.perf_counter()
            app.update()
            if isinstance(app.scene, (MissionScene, DockScene)):
                cost["update"].append(time.perf_counter() - t0)

    def draw():
        shot = getattr(bot, "pending", None)
        t0 = time.perf_counter()
        app.draw()
        if isinstance(app.scene, (MissionScene, DockScene)) and not shot:
            cost["draw"].append(time.perf_counter() - t0)

    pyxel.run(update, draw)


if __name__ == "__main__":
    if STAGE:
        run_stage()
    else:
        App(hook=Bot(), screen=SCREEN, lang=LANG).run()

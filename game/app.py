"""ゲーム本体とシーン切り替え。"""

import pyxel

from . import audio, i18n, script, ui
from .portraits import Portraits
from .missions import MISSIONS
from .scene_misc import CaptionScene, GameOverScene, ResultScene, TitleScene
from .scene_mission import MissionScene
from .scene_office import OfficeScene
from .state import GameState


class App:
    def __init__(self, hook=None, screen="640x480", lang="ja"):
        ui.set_screen(screen)
        i18n.set_lang(lang)
        pyxel.init(ui.W, ui.H, title="StarX", fps=60, quit_key=pyxel.KEY_ESCAPE)
        ui.load_fonts()
        audio.setup()
        self.portraits = Portraits()
        self.state = GameState()
        self.scene = TitleScene(self)
        self.hook = hook
        self.frame = 0

    def run(self):
        pyxel.run(self.update, self.draw)

    def update(self):
        self.frame += 1
        if self.hook:
            self.hook(self, "update")
        self.scene.update()

    def draw(self):
        self.scene.draw()
        if self.hook:
            self.hook(self, "draw")

    # ---- シーン遷移 ----
    def to_title(self):
        self.scene = TitleScene(self)

    def new_game(self):
        """いきなり初飛行から始める(操作説明つき。途中で必ず爆発する)。"""
        self.state = GameState()
        self.scene = MissionScene(self, MISSIONS["1-1"], cold_open=True)

    def after_cold_open(self):
        """爆発のあと「4年前——」の字幕を出し、創業の日から物語を始める。"""
        audio.engine(0)
        self.scene = CaptionScene(self, script.FLASHBACK, self.start_story)

    def start_story(self):
        self.scene = OfficeScene(self, script.KICKOFF + script.PROLOGUE, party=len(script.KICKOFF))

    def start_mission(self, mdef):
        self.scene = MissionScene(self, mdef)

    def finish_mission(self, run):
        audio.engine(0)
        st = self.state
        st.rockets -= 1
        st.inspected = False
        st.ap = 0
        tlm = run.telemetry()
        rep = run.m.rep_success if run.result == "success" else -3
        st.tlm += tlm
        st.reputation = max(0, st.reputation + rep)
        if run.result == "success":
            st.cleared.add(run.m.id)
        st.flights.append({"mission": run.m.id, "result": run.result, "rank": run.rank(),
                           "reason": run.fail_reason, "max_alt": run.max_alt})
        self.scene = ResultScene(self, run, {"tlm": tlm, "rep": rep})

    def back_to_office_after(self, run):
        if run.result == "success":
            lines = list(script.RESULT_SUCCESS_1_1)
        else:
            reason = run.fail_reason
            key = "fire" if "火災" in reason else "aero" if "分解" in reason else "tilt" if "姿勢" in reason else "other"
            lines = list(script.RESULT_FAIL_1_1[key])
            st = self.state
            if key in ("fire", "aero") and "rud" not in st.seen:
                st.seen.add("rud")
                lines += script.RESULT_RUD
            if st.rockets <= 0:
                lines += script.RESULT_FAIL_COMMON
            recent = [f["result"] for f in st.flights[-3:]]
            if recent == ["fail"] * 3 and "comeback" not in st.seen:
                st.seen.add("comeback")
                st.funds += script.COMEBACK_FUNDS
                lines += script.COMEBACK
        lines.append(("sara", "打ち上げで今月は手一杯。「待機」で次の月へ進めましょう。"))
        self.scene = OfficeScene(self, lines)

    def game_over(self):
        self.scene = GameOverScene(self, script.GAME_OVER)

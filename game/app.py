"""ゲーム本体とシーン切り替え。"""

import pyxel

from . import script, ui
from .portraits import Portraits
from .scene_misc import GameOverScene, ResultScene, TitleScene
from .scene_mission import MissionScene
from .scene_office import OfficeScene
from .state import GameState


class App:
    def __init__(self, hook=None, screen="640x480"):
        ui.set_screen(screen)
        pyxel.init(ui.W, ui.H, title="StarX", fps=60, quit_key=pyxel.KEY_ESCAPE)
        ui.load_fonts()
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
        self.state = GameState()
        self.scene = OfficeScene(self, script.PROLOGUE)

    def start_mission(self, mdef):
        self.scene = MissionScene(self, mdef)

    def finish_mission(self, run):
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
            if self.state.rockets <= 0:
                lines += script.RESULT_FAIL_COMMON
        lines.append(("sara", "打ち上げで今月は手一杯。「待機」で次の月へ進めましょう。"))
        self.scene = OfficeScene(self, lines)

    def game_over(self):
        self.scene = GameOverScene(self, script.GAME_OVER)

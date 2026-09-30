"""ゲーム本体とシーン切り替え。"""

import pyxel

from . import audio, i18n, script, state, ui
from .i18n import trf
from .portraits import Portraits
from .missions import MISSIONS, ORDER, next_stage
from .scene_dock import DockScene
from .scene_misc import CaptionScene, GameOverScene, ResultScene, TitleScene
from .scene_mission import MissionScene
from .scene_office import OfficeScene
from .state import GameState


class App:
    def __init__(self, hook=None, screen="640x480", lang="ja", stage=None):
        """stage: 動作確認用。そのステージの直前の状態から、会社画面で始める。"""
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
        if stage:
            self.jump(stage)

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

    def continue_game(self):
        """セーブしたところから続ける。セーブがなければ False。"""
        st = state.load()
        if st is None:
            return False
        self.state = st
        self.scene = OfficeScene(self)
        return True

    def jump(self, stage):
        """動作確認用: そのステージまでを済ませたことにして、会社画面から始める。"""
        state.ENABLED = False  # 遊んでいるセーブを上書きしない
        st = self.state = GameState()
        ids = [m.id for m in ORDER]
        st.stage = stage
        st.cleared = set(ids[:ids.index(stage)])
        st.funds = 150.0
        st.rockets = {"eagle1": 0, "eagle9": 0, "hopper": 0}
        st.rockets[st.craft] = 1
        self.scene = OfficeScene(self, list(script.INTRO.get(stage, [])))

    def after_cold_open(self):
        """爆発のあと「4年前——」の字幕を出し、創業の日から物語を始める。"""
        audio.engine(0)
        self.scene = CaptionScene(self, script.FLASHBACK, self.start_story)

    def start_story(self):
        self.scene = OfficeScene(self, script.KICKOFF + script.PROLOGUE, party=len(script.KICKOFF))

    def start_mission(self, mdef):
        self.scene = DockScene(self, mdef) if mdef.kind == "dock" else MissionScene(self, mdef)

    def finish_mission(self, run):
        audio.engine(0)
        self.scene = ResultScene(self, run, self.state.record_flight(run))

    def back_to_office_after(self, run, summary):
        st, m = self.state, run.m
        if run.result == "success":
            lines = list(script.SUCCESS[m.id]) if summary["first"] else []
            if summary["funds"]:
                lines.append(("sara", trf("{funds:.0f}M$ が入ったわ。", funds=summary["funds"])))
            if summary["recovered"]:
                lines.append(("maya", "1段目を回収したわ。次の Eagle 9 は、整備だけで安く作れる。"))
            nxt = next_stage(m.id)
            if summary["first"] and nxt:
                st.stage = nxt
                st.inspected = False
                lines += script.INTRO.get(nxt, [])
                if st.ready() <= 0 and not st.building_now():
                    cost, months = st.build_cost()
                    lines.append(("maya", trf("{name} は「製造」で用意して({cost:.0f}M$・{months}ヶ月)。",
                                              name=st.craft_name, cost=cost, months=months)))
            elif summary["first"]:
                st.finished = True
                lines += script.ENDING
        else:
            if run.saved:
                lines = list(script.SAVED)
            else:
                hint = next(text for key, text in script.FAIL_HINTS if key in run.fail_reason)
                lines = [("maya", hint)]
            if st.ready() <= 0 and not st.building_now():
                cost, months = st.build_cost()
                lines.append(("sara", trf("機体がないわ。「製造」で {name} を用意して({cost:.0f}M$・{months}ヶ月)。",
                                          name=st.craft_name, cost=cost, months=months)))
            recent = [f["result"] for f in st.flights[-3:]]
            if recent == ["fail"] * 3 and "comeback" not in st.seen:
                st.seen.add("comeback")
                st.funds += script.COMEBACK_FUNDS
                lines += script.COMEBACK
        lines.append(("sara", "今月はもう手一杯。「待機」で次の月へ。"))
        self.scene = OfficeScene(self, lines)

    def game_over(self):
        self.scene = GameOverScene(self, script.GAME_OVER)


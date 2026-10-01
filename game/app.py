"""ゲーム本体とシーン切り替え。"""

import pyxel

from . import audio, i18n, script, state, story, ui
from .portraits import Portraits
from .missions import MISSIONS, ORDER
from .scene_dock import DockScene
from .scene_misc import CaptionScene, GameOverScene, ResultScene, TitleScene
from .scene_mission import MissionScene
from .scene_office import OfficeScene
from .scene_setup import SetupScene
from .state import GameState


class App:
    def __init__(self, hook=None, screen="640x480", lang="ja", stage=None, setup=False):
        """stage: 動作確認用。そのステージの直前の状態から、会社画面で始める。
        setup: 言語と画面サイズを選ぶ画面から始める(初回の起動)。"""
        ui.set_screen(screen)
        i18n.set_lang(lang)
        pyxel.init(ui.W, ui.H, title="StarX", fps=60, quit_key=pyxel.KEY_ESCAPE)
        ui.load_fonts()
        audio.setup()
        self.portraits = Portraits()
        self.state = GameState()
        self.scene = SetupScene(self) if setup else TitleScene(self)
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

    def open_setup(self):
        self.scene = SetupScene(self, from_title=True)

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
        self.scene = OfficeScene(self, story.after_flight(self.state, run, summary))

    def game_over(self):
        self.scene = GameOverScene(self, script.GAME_OVER)


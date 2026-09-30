"""シナリオの進行を、画面なし・文字だけで確かめる(Pyxel は不要)。

python tools/story_check.py              最初から。セリフを読み、会社のコマンドを番号で選んで進める
python tools/story_check.py 2-1          そのステージの直前から始める
python tools/story_check.py en           英語で表示する
python tools/story_check.py --auto       自動で最後まで進める(製造 → 点検 → 打上、打上は必ず成功)。全セリフの通し読み用
python tools/story_check.py --step       セリフを 1 行ずつ Enter で送る

会社のコマンドと、飛行のあとの会話はゲーム本体と同じ処理(game/story.py)を使う。
飛行(ACT パート)は「成功 / 失敗(理由を選ぶ)」を選ぶだけで済ませる。
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from game import i18n, script, story  # noqa: E402
from game.i18n import tr  # noqa: E402
from game.missions import MISSIONS, ORDER  # noqa: E402
from game.script import NAMES  # noqa: E402
from game.state import CRAFTS, GameState  # noqa: E402

# 飛行の結果として選べる失敗の理由: (理由, 機体を失うか)。理由の文言は missions.py / docking.py と同じ
FAILS = {
    "ascent": [("火災でエンジンが爆発", True), ("迎角が大きすぎて空中分解", True),
               ("姿勢を失ったため飛行中断(自爆)", True), ("燃料切れ", True)],
    "orbit": [("火災でエンジンが爆発", True), ("迎角が大きすぎて空中分解", True), ("残った推力で1段目が追突", True),
              ("燃料切れ(軌道に届かず)", True), ("回転が残ったまま放出(投入失敗)", True)],
    "reentry": [("再突入角が浅すぎて、大気に弾かれた", True), ("深く入りすぎて、加熱で燃え尽きた", True),
                ("速すぎるところで開いて、パラシュートが破れた", True), ("着水が速すぎて、カプセルが壊れた", True)],
    "dock": [("速すぎる接近。ステーションが中止を命じた", True), ("ステーションに衝突", True), ("時間切れ", True)],
    "hop": [("降下が速すぎて、脚が折れた(硬着陸)", True), ("横に流れたまま接地して転倒", True),
            ("高さ 100 m に届かないまま着地", False)],
    "landing": [("減速が足りず、再突入で機体が分解", True), ("降下が速すぎて、脚が折れた(硬着陸)", True),
                ("台船を外して海に落ちた", True)],
    "recover": [("分離が早すぎて、2段目が軌道に届かない", True), ("減速が足りず、再突入で機体が分解", True),
                ("降下が速すぎて、脚が折れた(硬着陸)", True), ("台船を外して海に落ちた", True),
                ("パッドを外して着地", True)],
}


class Run:
    """飛行の結果だけを持つ、MissionRun の代わり。"""

    def __init__(self, m, result, reason="", lost=True, saved=False, rank="A", delivered=False):
        self.m = m
        self.result = result
        self.fail_reason = reason
        self.vehicle_lost = lost
        self.saved = saved
        self._rank = rank if result == "success" else "-"
        # 着陸系で、荷物を届けたあとの失敗なら代金が入る(state.record_flight が見る)
        self.phase = "descent" if delivered else "s1"
        self.max_alt = 0.0

    def rank(self):
        return self._rank

    def telemetry(self):
        return self.m.tlm_success if self.result == "success" else 10 + (self.m.tlm_success - 10) // 2


class Checker:
    def __init__(self, auto=False, step=False):
        self.auto = auto
        self.step = step
        self.st = GameState()

    # ---- 表示 ----
    def say(self, lines):
        for speaker, body in lines:
            name = tr(NAMES.get(speaker, speaker)) if speaker else ""
            text = f"  {name}「{tr(body)}」" if name else f"  ({tr(body)})"
            print(text)
            if self.step and not self.auto:
                input()

    def status(self):
        st = self.st
        m = MISSIONS[st.stage]
        build = f" (+{st.building_now()} {tr('製造中')})" if st.building_now() else ""
        print()
        print(f"[{st.date_str()}] {tr(m.title)} / {tr('資金')} {st.funds:.1f}M$ / {tr('評判')} {st.reputation} / "
              f"AP {st.ap}/{st.ap_max} / {st.craft_name} {st.ready()}{build}"
              + (f" / {tr('点検')}済" if st.inspected else ""))

    def choose(self, title, options, auto_pick=0):
        """番号で選ぶ。options は表示する文字列の並び。q で終了。"""
        print(f"  -- {title}")
        for i, text in enumerate(options, 1):
            print(f"    {i}. {text}")
        if self.auto:
            print(f"    > {auto_pick + 1}")
            return auto_pick
        while True:
            ans = input("    > ").strip()
            if ans.lower() in ("q", "quit", "exit"):
                raise SystemExit(0)
            if ans.isdigit() and 1 <= int(ans) <= len(options):
                return int(ans) - 1
            print("    番号を入力してください(q で終了)")

    # ---- 進行 ----
    def opening(self):
        print("== オープニング: Eagle 1 の初飛行(操作説明つき。途中で必ず爆発する) ==")
        for line in script.FLASHBACK:
            print(f"  {tr(line)}")
        self.say(script.KICKOFF + script.PROLOGUE)

    def jump(self, stage):
        st = self.st
        ids = [m.id for m in ORDER]
        st.stage = stage
        st.cleared = set(ids[:ids.index(stage)])
        st.funds = 150.0
        st.rockets = {"eagle1": 0, "eagle9": 0, "hopper": 0}
        st.rockets[st.craft] = 1
        print(f"== {tr(MISSIONS[stage].title)} の直前から ==")
        self.say(script.INTRO.get(stage, []))

    def auto_command(self):
        """--auto のときの会社の動き: 機体がなければ製造、あれば点検して打上、どちらもできなければ待機。"""
        st = self.st
        if st.ready() <= 0:
            if not st.building_now() and st.ap > 0 and st.funds >= st.build_cost()[0]:
                return "build"
            return "wait"
        if not st.inspected and st.ap > 0:
            return "inspect"
        return "launch"

    def office(self):
        st = self.st
        self.status()
        keys = [k for k, _, _ in story.COMMANDS]
        if self.auto:
            key = self.auto_command()
            print(f"  -- コマンド > {tr(dict((k, n) for k, n, _ in story.COMMANDS)[key])}")
        else:
            opts = [f"{tr(name)}(AP{ap}) {story.describe(st, k)}" if ap else f"{tr(name)} {story.describe(st, k)}"
                    for k, name, ap in story.COMMANDS]
            key = keys[self.choose("コマンド", opts)]
        lines, then = story.command(st, key)
        self.say(lines)
        if then == "launch":
            self.flight()
        elif then == "game_over":
            self.say(script.GAME_OVER)
            return False
        return True

    def flight(self):
        st = self.st
        m = MISSIONS[st.stage]
        print(f"== 飛行: {tr(m.title)} — {tr(m.goal)} ==")
        opts = [f"成功(ランク {r})" for r in "SABC"]
        fails = FAILS[m.kind]
        opts += [f"失敗: {tr(reason)}" for reason, _ in fails]
        if m.gimmick == "anomaly":
            opts.append("失敗: " + tr("機体は分解。カプセルは脱出して無事"))
        pick = self.choose("結果", opts, auto_pick=0)
        landing = m.kind in ("landing", "recover")
        if pick < 4:
            run = Run(m, "success", rank="SABC"[pick])
        elif pick < 4 + len(fails):
            reason, lost = fails[pick - 4]
            # 回収系で、分離より後の失敗なら荷物は届いている
            delivered = landing and not reason.startswith("分離")
            run = Run(m, "fail", reason, lost, delivered=delivered)
        else:
            run = Run(m, "fail", "機体は分解。カプセルは脱出して無事", saved=True)
        summary = st.record_flight(run)
        name = CRAFTS[m.craft][0]
        craft = ("機体は無事" if summary["kept"] else "1段目を回収" if summary["recovered"] else f"{name} -1")
        print(f"  [結果] {'成功' if run.result == 'success' else '失敗'}  資金 +{summary['funds']:.0f}M$  "
              f"評判 {summary['rep']:+d}  テレメトリ +{summary['tlm']}  {craft}")
        self.say(story.after_flight(st, run, summary))

    def play(self, stage=None):
        if stage:
            self.jump(stage)
        else:
            self.opening()
        turns = 0
        while not self.st.finished:
            if not self.office():
                print("== GAME OVER ==")
                return
            turns += 1
            if self.auto and turns > 2000:
                print("== 進まなくなったので止めます ==")
                return
        print("== いま遊べる最後のステージまで終わりました ==")


def main():
    args = sys.argv[1:]
    sys.stdout.reconfigure(encoding="utf-8")
    lang = next((a for a in args if a in i18n.LANGS), "ja")
    i18n.set_lang(lang)
    stage = next((a for a in args if a in MISSIONS), None)
    checker = Checker(auto="--auto" in args, step="--step" in args)
    try:
        checker.play(stage)
    except (EOFError, KeyboardInterrupt):
        print()


if __name__ == "__main__":
    main()

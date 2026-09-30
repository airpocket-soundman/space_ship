"""会社の状態(資金・評判・月など)。"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from .i18n import trf
from .missions import MISSIONS

# 機体の種類: 名前、製造費 [M$]、製造にかかる月数
CRAFTS = {
    "eagle1": ("Eagle 1", 7.0, 2),
    "eagle9": ("Eagle 9", 25.0, 2),
    "hopper": ("Hopper", 5.0, 1),
}
REFURBISH_COST = 8.0  # 回収した1段目を整備して、もう一度 Eagle 9 に仕立てる費用 [M$]
REFURBISH_MONTHS = 1
SUPPLY_INCOME = 4.0  # 補給の定期便(Ch2-3 のあと)で毎月入る代金 [M$]

SAVE_KEYS = ("year", "month", "funds", "reputation", "tlm", "ap", "rockets", "building", "inspected", "stage",
             "cleared", "best", "recovered", "last_fundraise", "flights", "seen", "finished")


@dataclass
class GameState:
    year: int = 5  # 物語は創業の日の 4 年後、初飛行の直前から始まる
    month: int = 3
    funds: float = 100.0  # M$
    reputation: int = 10
    tlm: int = 0
    ap_max: int = 3
    ap: int = 3
    staff: int = 0
    fixed_cost: float = 3.0
    rockets: dict = field(default_factory=lambda: {"eagle1": 1, "eagle9": 0, "hopper": 0})  # 打ち上げ可能な機体
    building: list = field(default_factory=list)  # 製造中: [機体の種類, 残り月数]
    inspected: bool = False
    stage: str = "1-1"
    cleared: set = field(default_factory=set)
    best: dict = field(default_factory=dict)  # ステージごとの最高ランク
    recovered: int = 0  # 回収して手元にある1段目
    last_fundraise: int = -99
    flights: list = field(default_factory=list)  # 飛行記録(のちのディーロン AI 用)
    seen: set = field(default_factory=set)  # 一度だけ出すエピソードのうち、もう出したもの
    finished: bool = False  # いま遊べる最後のステージまで終えた

    INSPECT_COST = 0.5

    @property
    def month_index(self):
        return (self.year - 1) * 12 + self.month

    @property
    def craft(self):
        """いまのステージで使う機体の種類。"""
        return MISSIONS[self.stage].craft

    @property
    def craft_name(self):
        return CRAFTS[self.craft][0]

    def build_cost(self):
        """いま製造するときの (費用, 月数)。回収した1段目があれば、整備だけで済む。"""
        if self.craft == "eagle9" and self.recovered > 0:
            return REFURBISH_COST, REFURBISH_MONTHS
        _, cost, months = CRAFTS[self.craft]
        return cost, months

    def ready(self):
        """いまのステージの機体が何機あるか。"""
        return self.rockets.get(self.craft, 0)

    def building_now(self):
        return sum(1 for c, _ in self.building if c == self.craft)

    def record_flight(self, run):
        """飛行の結果を会社の状態に反映する。リザルト画面に出す内訳を返す。"""
        m = run.m
        ok = run.result == "success"
        first = ok and m.id not in self.cleared
        # 機体: Hopper は無事に降りれば手元に残る。Eagle 9 は、着陸に成功すれば1段目だけが残る
        kept = m.craft == "hopper" and (ok or not run.vehicle_lost)
        if not kept:
            self.rockets[m.craft] = max(0, self.rockets.get(m.craft, 0) - 1)
        recovered = ok and m.reusable and m.craft == "eagle9"
        if recovered:
            self.recovered += 1
        self.inspected = False
        self.ap = 0
        tlm = run.telemetry()
        rep = m.rep_success if ok else 0 if run.saved else -3
        self.tlm += tlm
        self.reputation = max(0, min(100, self.reputation + rep))
        # お金: 荷物を届けた代金(着陸に失敗しても入る)と、初めて成功したときの報酬
        delivered = ok or getattr(run, "phase", "") == "descent"
        funds = (m.income if delivered else 0.0) + (m.reward if first else 0.0)
        self.funds += funds
        if ok:
            self.cleared.add(m.id)
            order = "CBAS"
            if order.find(run.rank()) > order.find(self.best.get(m.id, "")):
                self.best[m.id] = run.rank()
        self.flights.append({"mission": m.id, "result": run.result, "rank": run.rank(),
                             "reason": run.fail_reason, "max_alt": run.max_alt})
        return {"tlm": tlm, "rep": rep, "funds": funds, "kept": kept, "recovered": recovered, "first": first}

    def fundraise_amount(self):
        """いま調達できる額 [M$]。評判が高いほど多い。"""
        return round(3 + self.reputation * 0.15, 1)

    def date_str(self):
        return trf("創業{year}年目 {month}月", year=self.year, month=self.month)

    def next_month(self):
        """月を進める。発生した出来事の会話行を返す。"""
        lines = []
        self.funds -= self.fixed_cost
        lines.append(("sara", trf("今月の固定費 {cost:.1f}M$ を払ったわ。残りは {funds:.1f}M$。",
                                  cost=self.fixed_cost, funds=self.funds)))
        if "2-3" in self.cleared:
            self.funds += SUPPLY_INCOME
            lines.append(("sara", trf("補給の定期便の代金が {income:.0f}M$ 入ったわ。", income=SUPPLY_INCOME)))
        remain = []
        for craft, months in self.building:
            if months <= 1:
                self.rockets[craft] = self.rockets.get(craft, 0) + 1
                lines.append(("maya", trf("{name} が完成したわ。いつでも飛ばせる。", name=CRAFTS[craft][0])))
            else:
                remain.append([craft, months - 1])
        self.building = remain
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self.ap = self.ap_max
        cost, _ = self.build_cost()
        if self.funds < cost + self.fixed_cost and self.funds >= 0:
            lines.append(("sara", "……資金が危ないわ。次の失敗は、会社の終わりかもしれない。"))
        return lines

    # ---- セーブ ----
    def to_json(self):
        data = {k: getattr(self, k) for k in SAVE_KEYS}
        data["cleared"] = sorted(self.cleared)
        data["seen"] = sorted(self.seen)
        return json.dumps(data, ensure_ascii=False)

    @classmethod
    def from_json(cls, text):
        data = json.loads(text)
        st = cls()
        for k in SAVE_KEYS:
            if k in data:
                setattr(st, k, data[k])
        st.cleared = set(st.cleared)
        st.seen = set(st.seen)
        if st.stage not in MISSIONS:
            st.stage = "1-1"
        return st


def save_path():
    """セーブファイルの場所。作れなければ None(ブラウザ版など)。"""
    try:
        import pyxel

        return Path(pyxel.user_data_dir("airpocket", "starx")) / "save.json"
    except Exception:
        return None


ENABLED = True  # 動作確認用の起動(ステージ指定・自動操作)では、遊んでいるセーブを上書きしない


def save(state):
    path = save_path() if ENABLED else None
    if path is None:
        return False
    try:
        path.write_text(state.to_json(), encoding="utf-8")
        return True
    except Exception:
        return False


def load():
    """セーブした状態を読む。なければ None。"""
    path = save_path()
    try:
        if path is None or not path.exists():
            return None
        return GameState.from_json(path.read_text(encoding="utf-8"))
    except Exception:
        return None

"""会社の状態(資金・評判・月など)。"""

from dataclasses import dataclass, field

from .i18n import trf


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
    rockets: int = 1  # 打ち上げ可能な Eagle 1
    building: list = field(default_factory=list)  # 製造中の残り月数
    inspected: bool = False
    stage: str = "1-1"
    cleared: set = field(default_factory=set)
    last_fundraise: int = -99
    flights: list = field(default_factory=list)  # 飛行記録(のちのディーロン AI 用)
    seen: set = field(default_factory=set)  # 一度だけ出すエピソードのうち、もう出したもの

    ROCKET_COST = 7.0
    ROCKET_MONTHS = 2
    INSPECT_COST = 0.5

    @property
    def month_index(self):
        return (self.year - 1) * 12 + self.month

    def date_str(self):
        return trf("創業{year}年目 {month}月", year=self.year, month=self.month)

    def next_month(self):
        """月を進める。発生した出来事の会話行を返す。"""
        lines = []
        self.funds -= self.fixed_cost
        lines.append(("sara", trf("今月の固定費 {cost:.1f}M$ を払ったわ。残りは {funds:.1f}M$。",
                                  cost=self.fixed_cost, funds=self.funds)))
        done = 0
        remain = []
        for m in self.building:
            if m <= 1:
                done += 1
            else:
                remain.append(m - 1)
        self.building = remain
        if done:
            self.rockets += done
            lines.append(("maya", trf("Eagle 1 が{n}機、完成したわ。いつでも飛ばせる。", n=done)))
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self.ap = self.ap_max
        if self.funds < self.ROCKET_COST + self.fixed_cost and self.funds >= 0:
            lines.append(("sara", "……資金が危ないわ。次の失敗は、会社の終わりかもしれない。"))
        return lines

"""ミッション定義と判定(Pyxel に依存しない)。"""

import math
from dataclasses import dataclass

from .i18n import trf
from .physics import EAGLE1, Vehicle


@dataclass
class Window:
    label: str
    lo: float
    hi: float
    unit: str

    def ok(self, v):
        return self.lo <= v <= self.hi


@dataclass
class Waypoint:
    name: str
    altitude: float  # この高度を通過した瞬間に判定する
    windows: dict  # key -> Window


@dataclass
class MissionDef:
    id: str
    title: str
    goal: str
    vehicle: object
    waypoint: Waypoint
    time_limit: float
    fire_chance: float
    fire_chance_inspected: float
    tlm_success: int
    rep_success: int


CH1_1 = MissionDef(
    id="1-1",
    title="Ch1-1 初飛行",
    goal="高度 10 km を突破せよ",
    vehicle=EAGLE1,
    waypoint=Waypoint(
        name="WP1",
        altitude=10_000.0,
        windows={
            "t": Window("時刻", 40.0, 80.0, "s"),
            "vy": Window("垂直速度", 250.0, 500.0, "m/s"),
            "vx": Window("水平速度", -100.0, 100.0, "m/s"),
            "ang": Window("傾き", -10.0, 10.0, "°"),
        },
    ),
    time_limit=150.0,
    fire_chance=0.8,
    fire_chance_inspected=0.25,
    tlm_success=40,
    rep_success=10,
)

MISSIONS = {"1-1": CH1_1}


class MissionRun:
    """1 回の飛行の進行と判定を持つ。"""

    AOA_LIMIT = math.radians(12.0)
    Q_LIMIT = 12_000.0
    TILT_LIMIT = math.radians(45.0)
    DOOMED_FIRE_AT = 27.0  # オープニングの飛行で火災が起きる時刻 [s]

    def __init__(self, mdef, inspected=False, seed=None, doomed=False):
        """doomed: オープニングの飛行。決まった時刻に火災が起き、何をしても爆発する。"""
        self.m = mdef
        self.v = Vehicle(mdef.vehicle)
        if seed is not None:
            self.v.rng.seed(seed)
        rng = self.v.rng
        chance = mdef.fire_chance_inspected if inspected else mdef.fire_chance
        self.fire_at = rng.uniform(22.0, 34.0) if rng.random() < chance else None
        self.doomed = doomed
        if doomed:
            self.fire_at = self.DOOMED_FIRE_AT
        self.fire_active = False
        self.fire_done = False
        self.fire_time = 0.0
        self.heat = 0.0
        self.stress = 0.0
        self.max_alt = 0.0
        self.max_q = 0.0
        self.maxq_announced = False
        self.result = None  # None / "success" / "fail"
        self.fail_reason = ""
        self.wp_values = None
        self.events = []  # (種類, 文言) の通知キュー

    def emit(self, kind, text):
        self.events.append((kind, text))

    def step(self, dt, steer=0, throttle_input=0):
        if self.result is not None:
            return
        v = self.v
        v.step(dt, steer, throttle_input)
        self.max_alt = max(self.max_alt, v.y)

        # 最大動圧の通知
        if v.q > self.max_q:
            self.max_q = v.q
        elif not self.maxq_announced and self.max_q > 8_000 and v.q < self.max_q * 0.97:
            self.maxq_announced = True
            self.emit("info", "最大動圧を通過")

        # 火災イベント
        if self.fire_at is not None and not self.fire_done and v.t >= self.fire_at and v.engine_on:
            if not self.fire_active:
                self.fire_active = True
                self.emit("warn", "エンジン区画で火災! 出力を最低まで絞れ!")
            self.fire_time += dt
            over = (v.throttle - v.p.min_throttle) / (1.0 - v.p.min_throttle)
            if self.doomed:  # 絞っても消えない
                self.heat += 30.0 * dt
            elif over > 0.08:
                self.heat += (4.0 + 22.0 * over) * dt
            else:
                self.heat = max(0.0, self.heat - 6.0 * dt)
            if self.heat >= 100.0:
                return self.fail("火災でエンジンが爆発")
            if self.fire_time >= 12.0:
                self.fire_active = False
                self.fire_done = True
                self.emit("info", "消火を確認。出力を戻してよし")

        # 空力による分解
        if abs(v.aoa) > self.AOA_LIMIT and v.q > self.Q_LIMIT:
            self.stress += dt
            if self.stress > 0.6:
                return self.fail("迎角が大きすぎて空中分解")
        else:
            self.stress = max(0.0, self.stress - dt)

        if v.lifted_off and abs(v.theta) > self.TILT_LIMIT:
            return self.fail("姿勢を失ったため飛行中断(自爆)")
        if v.lifted_off and v.y < 0:
            return self.fail("墜落")
        if v.lifted_off and v.prop <= 0 and v.y < self.m.waypoint.altitude:
            return self.fail("燃料切れ")
        if v.t > self.m.time_limit:
            return self.fail("時間切れ")

        wp = self.m.waypoint
        if v.y >= wp.altitude and self.wp_values is None:
            self.wp_values = {
                "t": v.t,
                "vy": v.vy,
                "vx": v.vx,
                "ang": math.degrees(v.theta),
            }
            self.result = "success"
            self.emit("good", trf("{name} 通過! 高度 {alt:.0f} km を突破", name=wp.name, alt=wp.altitude / 1000))

    def fail(self, reason):
        self.result = "fail"
        self.fail_reason = reason
        self.emit("bad", reason)

    def window_status(self):
        """現在値が各窓に入っているか(HUD 表示用)。"""
        v = self.v
        cur = {"t": v.t, "vy": v.vy, "vx": v.vx, "ang": math.degrees(v.theta)}
        return {k: (cur[k], w.ok(cur[k])) for k, w in self.m.waypoint.windows.items()}

    def rank(self):
        if self.result != "success":
            return "-"
        hits = sum(1 for k, w in self.m.waypoint.windows.items() if w.ok(self.wp_values[k]))
        return {4: "S", 3: "A", 2: "B"}.get(hits, "C")

    def telemetry(self):
        if self.result == "success":
            return self.m.tlm_success
        # 失敗しても到達した高度に応じてデータが取れる
        return int(10 + 30 * min(1.0, self.max_alt / self.m.waypoint.altitude))

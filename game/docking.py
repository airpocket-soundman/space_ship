"""近接操作(Ch2-3): カプセルをステーションの把持点で止める(Pyxel に依存しない)。

座標はステーションの把持点を原点にした相対位置 [m]。x は軌道の進行方向、y は上(地球と反対側)。
軌道上なので、まっすぐには進まない(上に出ると遅れ、前に出ると上へ曲がる)。
"""

import math
import random

from .i18n import trf

N = 0.0032  # 軌道の角速度 [rad/s](高度 120 km の円軌道)


class DockRun:
    ACCEL = 0.2  # スラスターの加速度 [m/s^2]
    FUEL = 80.0  # 噴射できる時間 [s]
    BOX = 2.0  # 把持できる範囲(把持点からの距離)[m]
    HOLD_SPEED = 0.15  # 把持できる相対速度 [m/s]
    HOLD_TIME = 3.0  # この時間だけ止まっていればアームがつかむ [s]
    ZONE = 40.0  # 接近禁止ゾーンの半径 [m]。この中は速度制限がある
    ZONE_SPEED = 1.2  # ゾーンの中で許される速度 [m/s]
    STATION = (6.0, -6.0, 46.0, 6.0)  # ステーション本体(ぶつかる範囲): x0, y0, x1, y1

    def __init__(self, mdef, inspected=False, seed=None, doomed=False):
        self.m = mdef
        rng = random.Random(seed)
        self.x = -rng.uniform(150.0, 190.0)
        self.y = rng.uniform(-50.0, 50.0)
        self.vx = rng.uniform(0.6, 1.2)
        self.vy = rng.uniform(-0.4, 0.4)
        self.fuel = self.FUEL
        self.t = 0.0
        self.hold = 0.0
        self.zone_stress = 0.0
        self.thrust = (0, 0)  # いま噴いている向き(描画用)
        self.result = None
        self.fail_reason = ""
        self.events = []
        self.final = None
        self.vehicle_lost = True
        self.saved = False
        self.max_alt = 0.0
        self.closest = math.hypot(self.x, self.y)

    def emit(self, kind, text):
        self.events.append((kind, text))

    @property
    def speed(self):
        return math.hypot(self.vx, self.vy)

    @property
    def dist(self):
        return math.hypot(self.x, self.y)

    def step(self, dt, ix=0, iy=0):
        """ix, iy: -1 / 0 / +1(←→ と ↓↑)"""
        if self.result is not None:
            return
        self.t += dt
        if self.fuel <= 0:
            ix = iy = 0
        n = (1 if ix else 0) + (1 if iy else 0)
        self.fuel = max(0.0, self.fuel - dt * n)
        self.thrust = (ix, iy)
        ax = ix * self.ACCEL + 2 * N * self.vy
        ay = iy * self.ACCEL - 2 * N * self.vx + 3 * N * N * self.y
        self.vx += ax * dt
        self.vy += ay * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.closest = min(self.closest, self.dist)

        x0, y0, x1, y1 = self.STATION
        if x0 <= self.x <= x1 and y0 <= self.y <= y1:
            return self.fail("ステーションに衝突")
        if self.dist < self.ZONE and self.speed > self.ZONE_SPEED:
            self.zone_stress += dt
            if self.zone_stress > 1.0:
                return self.fail("速すぎる接近。ステーションが中止を命じた")
        else:
            self.zone_stress = 0.0
        if self.dist > 600:
            return self.fail("ステーションから離れすぎた")
        if self.t > self.m.time_limit:
            return self.fail("時間切れ")
        if self.dist <= self.BOX and self.speed <= self.HOLD_SPEED:
            self.hold += dt
            if self.hold >= self.HOLD_TIME:
                self.final = {"speed": self.speed, "dist": self.dist, "t": self.t, "fuel": self.fuel / self.FUEL}
                self.result = "success"
                self.emit("good", "アームがカプセルをつかんだ! 到着")
        else:
            self.hold = 0.0

    def fail(self, reason):
        self.result = "fail"
        self.fail_reason = reason
        self.emit("bad", reason)

    # ---- 表示用(MissionRun と同じ形) ----
    def prompt(self):
        if self.result is None and self.dist <= self.BOX and self.speed <= self.HOLD_SPEED:
            return "そのまま止まれ"
        return ""

    def rows(self):
        lim = self.ZONE_SPEED if self.dist < self.ZONE else 9.9
        return [
            ("距離", f"~{self.BOX:.0f}m", f"{self.dist:.1f}", self.dist <= self.BOX),
            ("相対速度", f"~{self.HOLD_SPEED:.2f}", f"{self.speed:.2f}", self.speed <= self.HOLD_SPEED),
            ("接近速度", f"~{self.ZONE_SPEED:.1f}", f"{self.speed:.2f}", self.speed <= lim),
            ("保持", f"{self.HOLD_TIME:.0f} s", f"{self.hold:.1f}", self.hold > 0),
        ]

    def report(self):
        f = self.final
        return [
            ("相対速度", trf("{v:.2f} m/s 以下", v=0.08), f"{f['speed']:.2f} m/s" if f else "---",
             bool(f and f["speed"] <= 0.08)),
            ("ずれ", trf("{d:.0f} m 以内", d=1.0), f"{f['dist']:.1f} m" if f else "---",
             bool(f and f["dist"] <= 1.0)),
            ("時間", trf("{t:.0f} s 以内", t=120.0), f"{f['t']:.0f} s" if f else "---",
             bool(f and f["t"] <= 120.0)),
            ("残り燃料", trf("{p:.0f}% 以上", p=40.0), f"{f['fuel'] * 100:.0f}%" if f else "---",
             bool(f and f["fuel"] >= 0.4)),
        ]

    def report_head(self):
        return "接近の記録"

    def rank(self):
        if self.result != "success":
            return "-"
        miss = sum(1 for r in self.report() if not r[3])
        return {0: "S", 1: "A", 2: "B"}.get(miss, "C")

    def telemetry(self):
        if self.result == "success":
            return self.m.tlm_success
        return int(10 + (self.m.tlm_success - 10) * 0.75 * max(0.0, 1.0 - self.closest / 170.0))

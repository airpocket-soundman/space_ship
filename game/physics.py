"""ロケットの飛行物理(Pyxel に依存しない)。

座標系: x は東向き[m]、y は高度[m](上向き)。
姿勢 theta は鉛直からの傾き[rad]。正で東(右)に傾く。
"""

import math
import random
from dataclasses import dataclass, field

G0 = 9.80665
EARTH_R = 6_371_000.0
RHO0 = 1.225
SCALE_H = 8_500.0
P0 = 101_325.0


@dataclass
class VehicleParams:
    name: str
    dry_mass: float  # 推進剤を除いた全質量 [kg](上段・ペイロード込み)
    prop_mass: float  # 1段目の推進剤 [kg]
    thrust_sl: float  # 海面推力 [N]
    thrust_vac: float  # 真空推力 [N]
    isp_sl: float
    isp_vac: float
    length: float  # 全長 [m]
    diameter: float
    min_throttle: float = 0.7
    throttle_rate: float = 0.6  # 目標スロットルの変化速度 [1/s]
    throttle_lag: float = 1.0  # 実スロットルの応答時定数 [s]
    gimbal_max: float = math.radians(3.0)
    gimbal_lag: float = 0.5  # ノズルの応答時定数 [s]
    inertia_factor: float = 3.0  # 慣性モーメントの割増(操縦感の調整用)
    rcs_accel: float = math.radians(1.2)  # スラスターの角加速度 [rad/s^2]
    rcs_fuel: float = 30.0  # スラスター噴射可能時間 [s]
    ang_damping: float = 0.02  # 角速度の減衰 [1/s]
    aero_instability: float = 0.6  # 空力的な不安定さ(大きいほど倒れやすい)
    ignitions: int = 1  # 点火できる回数
    drag_cd: float = 0.35


EAGLE1 = VehicleParams(
    name="Eagle 1",
    dry_mass=6_000.0,
    prop_mass=21_000.0,
    thrust_sl=450_000.0,
    thrust_vac=490_000.0,
    isp_sl=255.0,
    isp_vac=300.0,
    length=21.0,
    diameter=1.7,
)


@dataclass
class Vehicle:
    p: VehicleParams
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    theta: float = 0.0
    omega: float = 0.0
    throttle_cmd: float = 1.0
    throttle: float = 0.0
    gimbal: float = 0.0
    engine_on: bool = False
    ignitions_left: int = 0
    prop: float = 0.0
    rcs_fuel: float = 0.0
    lifted_off: bool = False
    t: float = 0.0  # 点火からの経過時間
    rcs_firing: int = 0
    gust: float = 0.0
    rng: random.Random = field(default_factory=random.Random)

    def __post_init__(self):
        self.prop = self.p.prop_mass
        self.rcs_fuel = self.p.rcs_fuel
        self.ignitions_left = self.p.ignitions

    # ---- 状態量 ----
    @property
    def mass(self):
        return self.p.dry_mass + self.prop

    @property
    def speed(self):
        return math.hypot(self.vx, self.vy)

    @property
    def density(self):
        return RHO0 * math.exp(-max(self.y, 0.0) / SCALE_H)

    @property
    def q(self):
        """動圧 [Pa]"""
        return 0.5 * self.density * self.speed ** 2

    @property
    def aoa(self):
        """迎角 [rad](機体軸と速度ベクトルのなす角)"""
        if self.speed < 30:
            return 0.0
        vel_angle = math.atan2(self.vx, self.vy)
        d = self.theta - vel_angle
        return (d + math.pi) % (2 * math.pi) - math.pi

    def thrust_now(self):
        if not self.engine_on or self.prop <= 0:
            return 0.0
        pr = self.density / RHO0
        full = self.p.thrust_vac + (self.p.thrust_sl - self.p.thrust_vac) * pr
        return full * self.throttle

    # ---- 操作 ----
    def ignite(self):
        if self.engine_on or self.ignitions_left <= 0 or self.prop <= 0:
            return False
        self.engine_on = True
        self.ignitions_left -= 1
        self.throttle = 0.0
        self.throttle_cmd = max(self.throttle_cmd, self.p.min_throttle)
        return True

    def cutoff(self):
        self.engine_on = False

    # ---- 1 ステップ ----
    def step(self, dt, steer=0, throttle_input=0):
        """steer: -1(左) / 0 / +1(右)、throttle_input: -1 / 0 / +1"""
        p = self.p
        if self.engine_on:
            self.t += dt

        # スロットル(目標 → 実値は一次遅れ)
        self.throttle_cmd += throttle_input * p.throttle_rate * dt
        self.throttle_cmd = min(1.0, max(p.min_throttle, self.throttle_cmd))
        target = self.throttle_cmd if self.engine_on else 0.0
        self.throttle += (target - self.throttle) * min(1.0, dt / p.throttle_lag)

        # ジンバル(一次遅れ)
        g_target = steer * p.gimbal_max if self.engine_on else 0.0
        self.gimbal += (g_target - self.gimbal) * min(1.0, dt / p.gimbal_lag)

        thrust = self.thrust_now()
        m = self.mass
        inertia = m * p.length ** 2 / 12.0 * p.inertia_factor
        arm = p.length * 0.5

        # 角加速度: ジンバル + スラスター + 空力 + 突風
        alpha = thrust * math.sin(self.gimbal) * arm / inertia
        self.rcs_firing = 0
        if steer != 0 and self.rcs_fuel > 0:
            alpha += steer * p.rcs_accel
            self.rcs_fuel = max(0.0, self.rcs_fuel - dt)
            self.rcs_firing = steer
        if self.lifted_off:
            alpha += p.aero_instability * (self.q / 20_000.0) * math.sin(self.aoa) * 0.05
            self.gust += (self.rng.gauss(0, 1) * 1.2 - self.gust * 0.5) * dt
            alpha += self.gust * math.radians(1.5) * min(1.0, self.density / RHO0 * 1.5)
        self.omega += alpha * dt
        self.omega *= 1.0 - p.ang_damping * dt

        # 力: 推力(ジンバル分だけ機体軸から逆向きに傾く)+ 重力 + 抗力
        dir_angle = self.theta - self.gimbal
        ax = thrust * math.sin(dir_angle) / m
        ay = thrust * math.cos(dir_angle) / m
        r = EARTH_R + max(self.y, 0.0)
        g = G0 * (EARTH_R / r) ** 2
        ay -= g - self.vx ** 2 / r  # 遠心力の近似
        v = self.speed
        if v > 0:
            area = math.pi * (p.diameter / 2) ** 2
            drag = 0.5 * self.density * v * v * p.drag_cd * area
            ax -= drag * self.vx / v / m
            ay -= drag * self.vy / v / m

        # 推進剤の消費
        if thrust > 0:
            pr = self.density / RHO0
            isp = p.isp_vac + (p.isp_sl - p.isp_vac) * pr
            self.prop = max(0.0, self.prop - thrust / (isp * G0) * dt)
            if self.prop <= 0:
                self.engine_on = False

        # 発射台に固定されている間
        if not self.lifted_off:
            if ay > 0.05:
                self.lifted_off = True
            else:
                self.vx = self.vy = 0.0
                self.omega = 0.0
                return

        self.vx += ax * dt
        self.vy += ay * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.theta += self.omega * dt

"""ロケットの飛行物理(Pyxel に依存しない)。

座標系: x は東向きの地表距離[m]、y は高度[m](上向き)。
姿勢 theta は鉛直からの傾き[rad]。正で東(右)に傾く。
惑星は地球と同じ大きさ(半径 6371 km、軌道速度は約 7.8 km/s)。
時間は常に TIME_SCALE 倍で進める(画面には出さない)。機体の向き・回転・ノズル・スロットル操作だけは
画面の時間で進めるので、何倍で進めても操縦の手応えは変わらない。
"""

import math
import random
from dataclasses import dataclass, field

G0 = 9.80665
PLANET_R = 6_371_000.0
MU = G0 * PLANET_R ** 2
RHO0 = 1.225
SCALE_H = 7_000.0  # 空気の濃さが 1/e になる高さ(実際の大気に近くなる値)
ATMO_TOP = 100_000.0  # これより上は真空とみなす(軌道が空気で落ちてこない)
TIME_SCALE = 3  # 物理を実時間の何倍で進めるか
P0 = 101_325.0


@dataclass
class VehicleParams:
    """1 段ぶんの諸元。"""

    name: str
    dry_mass: float  # この段の推進剤を除いた質量 [kg]
    prop_mass: float  # 推進剤 [kg]
    thrust_sl: float  # 海面推力 [N]
    thrust_vac: float  # 真空推力 [N]
    isp_sl: float
    isp_vac: float
    length: float  # この段の長さ [m]
    diameter: float
    min_throttle: float = 0.7
    throttle_rate: float = 0.6  # 目標スロットルの変化速度 [1/s]
    throttle_lag: float = 1.0  # 実スロットルの応答時定数 [s]
    cutoff_lag: float = 0.8  # 停止してから推力が消えるまでの時定数 [s]
    gimbal_max: float = math.radians(3.0)
    gimbal_lag: float = 0.5  # ノズルの応答時定数 [s]
    inertia_factor: float = 3.0  # 慣性モーメントの割増(操縦感の調整用)
    rcs_accel: float = math.radians(1.2)  # スラスターの角加速度 [rad/s^2]
    rcs_fuel: float = 30.0  # スラスター噴射可能時間 [s]
    rcs_trans_accel: float = 0.6  # スラスターで機体の横へ平行移動するときの加速度 [m/s^2]
    ang_damping: float = 0.02  # 角速度の減衰 [1/s]
    aero_instability: float = 0.6  # 空力的な不安定さ(大きいほど倒れやすい)
    ignitions: int = 1  # 点火できる回数
    drag_cd: float = 0.35
    fin_auth: float = 0.0  # グリッドフィンの効き(動圧 20 kPa のときの角加速度 [rad/s^2])
    style: str = "eagle1"  # 描き方(scene_mission / rocket_art)


def apsides(y, vx, vy):
    """高度・水平速度・垂直速度から (近地点高度, 遠地点高度) [m] を求める。脱出するなら遠地点は inf。"""
    r = PLANET_R + y
    eps = (vx * vx + vy * vy) / 2 - MU / r
    h = r * vx
    if eps >= 0:
        rp = h * h / MU / 2 if h else 0.0  # 放物線の近似
        return rp - PLANET_R, math.inf
    a = -MU / (2 * eps)
    e = math.sqrt(max(0.0, 1 + 2 * eps * h * h / (MU * MU)))
    return a * (1 - e) - PLANET_R, a * (1 + e) - PLANET_R


def circular_speed(y):
    return math.sqrt(MU / (PLANET_R + y))


def time_to_apoapsis(y, vx, vy):
    """遠地点までの時間 [s]。もう過ぎている(下降中)か、軌道が閉じていなければ None。"""
    if vy <= 0:
        return None
    r = PLANET_R + y
    eps = (vx * vx + vy * vy) / 2 - MU / r
    if eps >= 0:
        return None
    a = -MU / (2 * eps)
    h = r * vx
    e = math.sqrt(max(0.0, 1 + 2 * eps * h * h / (MU * MU)))
    if e < 1e-6:
        return 0.0
    E = math.acos(max(-1.0, min(1.0, (1 - r / a) / e)))
    return (math.pi - (E - e * math.sin(E))) / math.sqrt(MU / a ** 3)


@dataclass
class Vehicle:
    p: VehicleParams
    upper: list = field(default_factory=list)  # 上に載っている段(下から順)
    payload: float = 0.0  # いちばん上の荷物 [kg]
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
    launched: bool = False  # 最初の点火を済ませたか
    t: float = 0.0  # 最初の点火からの経過時間
    rcs_firing: int = 0
    rcs_translate: int = 0  # 平行移動のスラスターの向き(機体から見て +1 右 / -1 左)
    gust: float = 0.0
    wind: float = 0.0  # 横風 [m/s](東向きが正)
    engine_frac: float = 1.0  # 使うエンジンの割合(回収のときは 9 基のうち 3 基だけ、など)
    fins: bool = False  # グリッドフィンを開いているか
    drag_mult: float = 1.0  # パラシュートなどによる抗力の倍率
    torque_bias: float = 0.0  # 故障や揺れによる外乱の角加速度 [rad/s^2]
    time_scale: float = TIME_SCALE  # 物理を実時間の何倍で進めているか(操縦と回転を画面の時間で進めるのに使う)
    rng: random.Random = field(default_factory=random.Random)

    def __post_init__(self):
        self.prop = self.p.prop_mass
        self.rcs_fuel = self.p.rcs_fuel
        self.ignitions_left = self.p.ignitions

    # ---- 状態量 ----
    @property
    def upper_mass(self):
        return sum(s.dry_mass + s.prop_mass for s in self.upper) + self.payload

    @property
    def mass(self):
        return self.p.dry_mass + self.prop + self.upper_mass

    @property
    def length(self):
        """いま飛んでいる機体全体の長さ [m]。"""
        return self.p.length + sum(s.length for s in self.upper)

    @property
    def speed(self):
        return math.hypot(self.vx, self.vy)

    @property
    def density(self):
        if self.y >= ATMO_TOP:
            return 0.0
        return RHO0 * math.exp(-max(self.y, 0.0) / SCALE_H)

    @property
    def air_speed(self):
        return math.hypot(self.vx - self.wind, self.vy)

    @property
    def q(self):
        """動圧 [Pa]"""
        return 0.5 * self.density * self.air_speed ** 2

    @property
    def aoa(self):
        """迎角 [rad](機体軸と、空気に対する速度ベクトルのなす角)"""
        if self.air_speed < 30:
            return 0.0
        vel_angle = math.atan2(self.vx - self.wind, self.vy)
        d = self.theta - vel_angle
        return (d + math.pi) % (2 * math.pi) - math.pi

    @property
    def aoa_tail(self):
        """尾部(エンジン側)を先にして落ちるときの迎角 [rad]。0 なら真後ろ向きに落ちている。"""
        a = self.aoa
        return a - math.copysign(math.pi, a) if a else math.pi

    def apsides(self):
        return apsides(self.y, self.vx, self.vy)

    def full_thrust(self):
        pr = self.density / RHO0
        return (self.p.thrust_vac + (self.p.thrust_sl - self.p.thrust_vac) * pr) * self.engine_frac

    def thrust_now(self):
        """エンジンを止めた直後(燃料切れを含む)も、スロットルが落ちきるまでは推力が残る。"""
        return self.full_thrust() * self.throttle

    # ---- 操作 ----
    def ignite(self):
        if self.engine_on or self.ignitions_left <= 0 or self.prop <= 0:
            return False
        self.engine_on = True
        self.launched = True
        self.ignitions_left -= 1
        self.throttle_cmd = max(self.throttle_cmd, self.p.min_throttle)
        return True

    def cutoff(self):
        self.engine_on = False

    def separate(self, keep_lower=False):
        """段を切り離す。切り離されて飛んでいく側の状態を返す(描画用)。

        keep_lower=False: 下の段を捨て、上の段で飛び続ける。
        keep_lower=True: 上の段と荷物を送り出し、下の段(回収する1段目)を操縦し続ける。
        """
        if not self.upper:
            return None
        L = self.p.length
        gone = dict(x=self.x, y=self.y, vx=self.vx, vy=self.vy, theta=self.theta, omega=self.omega)
        if keep_lower:
            gone.update(params=self.upper[0], upper=self.upper[1:], lower=False,
                        x=self.x + math.sin(self.theta) * L, y=self.y + math.cos(self.theta) * L)
            self.upper = []
            self.payload = 0.0
            return gone
        gone.update(params=self.p, upper=[], lower=True)
        self.x += math.sin(self.theta) * L
        self.y += math.cos(self.theta) * L
        self.p = self.upper[0]
        self.upper = self.upper[1:]
        self.prop = self.p.prop_mass
        self.rcs_fuel = self.p.rcs_fuel
        self.ignitions_left = self.p.ignitions
        self.engine_on = False
        self.throttle = 0.0
        self.throttle_cmd = 1.0
        self.gimbal = 0.0
        self.engine_frac = 1.0
        return gone

    # ---- 1 ステップ ----
    def step(self, dt, steer=0, throttle_input=0, translate=0):
        """steer: -1(左) / 0 / +1(右)、throttle_input: -1 / 0 / +1
        translate: スラスターで機体の横(機軸と直角)へ押す向き。+1 で機体から見て右、-1 で左。"""
        p = self.p
        if self.launched:
            self.t += dt
        cdt = dt / self.time_scale  # 画面の時間(操縦と回転はこちらで進める)

        # スロットル(目標 → 実値は一次遅れ)
        self.throttle_cmd += throttle_input * p.throttle_rate * cdt
        self.throttle_cmd = min(1.0, max(p.min_throttle, self.throttle_cmd))
        if self.engine_on:
            self.throttle += (self.throttle_cmd - self.throttle) * min(1.0, dt / p.throttle_lag)
        else:
            self.throttle -= self.throttle * min(1.0, dt / p.cutoff_lag)

        # ジンバル(一次遅れ)
        g_target = steer * p.gimbal_max if self.engine_on else 0.0
        self.gimbal += (g_target - self.gimbal) * min(1.0, cdt / p.gimbal_lag)

        thrust = self.thrust_now()
        m = self.mass
        L = self.length
        inertia = m * L ** 2 / 12.0 * p.inertia_factor
        arm = L * 0.5

        # 角加速度: ジンバル + スラスター + グリッドフィン + 空力 + 突風 + 外乱
        alpha = thrust * math.sin(self.gimbal) * arm / inertia
        self.rcs_firing = 0
        if steer != 0 and self.rcs_fuel > 0:
            alpha += steer * p.rcs_accel
            self.rcs_fuel = max(0.0, self.rcs_fuel - cdt)
            self.rcs_firing = steer
        if self.lifted_off:
            q = self.q
            if self.fins and steer != 0:
                alpha += steer * p.fin_auth * min(1.5, q / 20_000.0)
            alpha += p.aero_instability * (q / 20_000.0) * math.sin(self.aoa) * 0.05
            self.gust += (self.rng.gauss(0, 1) * 1.2 - self.gust * 0.5) * cdt
            alpha += self.gust * math.radians(1.5) * min(1.0, self.density / RHO0 * 1.5)
            alpha += self.torque_bias
        self.omega += alpha * cdt
        self.omega *= 1.0 - p.ang_damping * cdt

        # 力: 推力(ジンバル分だけ機体軸から逆向きに傾く)+ 重力 + 抗力
        dir_angle = self.theta - self.gimbal
        ax = thrust * math.sin(dir_angle) / m
        ay = thrust * math.cos(dir_angle) / m
        r = PLANET_R + max(self.y, 0.0)
        g = MU / (r * r)
        ay -= g - self.vx ** 2 / r  # 水平速度が軌道速度に届くと重力が打ち消される
        ax -= self.vx * self.vy / r  # 高く上がると水平速度が落ちる(角運動量の保存)
        rvx = self.vx - self.wind
        v = math.hypot(rvx, self.vy)
        if v > 0:
            area = math.pi * (p.diameter / 2) ** 2
            drag = 0.5 * self.density * v * v * p.drag_cd * area * self.drag_mult
            ax -= drag * rvx / v / m
            ay -= drag * self.vy / v / m

        # スラスターによる平行移動(機体の横向きに押す。回転はさせない)
        self.rcs_translate = 0
        if translate and self.rcs_fuel > 0 and self.lifted_off:
            a = translate * p.rcs_trans_accel
            ax += a * math.cos(self.theta)  # 機体から見た右は (cos θ, -sin θ)
            ay -= a * math.sin(self.theta)
            self.rcs_fuel = max(0.0, self.rcs_fuel - cdt)
            self.rcs_translate = translate

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
        self.x += self.vx * dt * PLANET_R / r
        self.y += self.vy * dt
        self.theta += self.omega * cdt

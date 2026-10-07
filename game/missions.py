"""ミッション定義と判定(Pyxel に依存しない)。

ミッションの種類(kind):
  ascent  ある高度を通過する(Ch1-1, 1-2)
  orbit   段を分離し、軌道に乗せて荷物を放出する
  recover 打ち上げて段を分離し、1段目を着陸させる(2段目は自動で軌道へ)
  landing 降下中の1段目を着陸させる
  hop     試験機 Hopper で跳んで着陸する
  reentry カプセルを軌道から降ろして着水させる
  dock    カプセルをステーションの把持点に止める(判定は docking.py)
"""

import copy
import math
from dataclasses import dataclass

from .i18n import trf
from .physics import G0, MU, PLANET_R, SCALE_H, TIME_SCALE, time_to_apoapsis
from .vehicles import EAGLE1, EAGLE9_S1R, HOPPER, PHOENIX, Rocket, eagle1, eagle9


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
class Orbit:
    """投入する軌道と、荷物を放出するときの条件。"""

    pe_lo: float  # 近地点の下限 [m]
    ap_hi: float  # 遠地点の上限 [m]
    ap_lo: float = 0.0  # 遠地点の下限 [m](高い軌道へ送るとき)
    att_tol: float = 20.0  # 放出時の姿勢: 水平(進行方向)からのずれ [°]
    rate_tol: float = 3.0  # 放出時の角速度 [°/s]
    release_time: float = 30.0  # 軌道に入ってから放出するまでの制限時間 [s]
    prop_bonus: float = 0.08  # これだけ推進剤を残すと高評価
    time_bonus: float = 330.0  # この時刻までに放出すると高評価 [s]


@dataclass
class Sep:
    """段分離の条件。"""

    auto: bool = False  # 自動で分離する(Ch1-2)
    tail: float = 0.08  # 残った推力がこの割合より小さくなってから分離する
    rate_max: float = 4.0  # 分離できる角速度の上限 [°/s]
    alt_lo: float = 0.0  # 回収のとき: 2段目が軌道に届くために必要な分離高度 [m]
    speed_lo: float = 0.0  # 同じく分離速度 [m/s]


@dataclass
class GuideWP:
    """軌道へ上がる途中の目安(時刻ごとの、垂直速度と水平速度の範囲)。評価には入れず、画面に出すだけ。"""

    t: float  # 打ち上げからの時刻 [s]
    vy_lo: float
    vy_hi: float
    vx_lo: float
    vx_hi: float


@dataclass
class Landing:
    """着陸の目標と、耐えられる接地条件。"""

    site: str  # pad(地上)/ ship(台船)/ sea(海面ならどこでも)
    x: float = 0.0  # 目標の中心 [m]
    half_w: float = 15.0  # 目標の幅の半分 [m]
    vy_max: float = 6.0  # 接地の降下速度 [m/s]
    vx_max: float = 3.0  # 接地の横速度 [m/s]
    tilt_max: float = 10.0  # 接地の傾き [°]
    vy_good: float = 3.0  # これ以下なら高評価
    dist_good: float = 5.0  # 中心からこれ以内なら高評価 [m]
    hop_alt: float = 0.0  # Hopper: 到達しなければならない高さ [m]
    heave: float = 0.0  # 台船の上下の揺れ [m]
    period: float = 7.0  # 揺れの周期 [s]
    wind: float = 0.0  # 低空の横風の強さ [m/s]
    q_limit: float = 0.0  # 降下中に耐えられる動圧 [Pa](0 なら制限なし)
    place: bool = False  # 分離したときの落下予想点に台船を置く
    deck: float = 0.0  # 甲板の高さ [m]


@dataclass
class Entry:
    """カプセルの再突入の条件。"""

    interface: float = 70_000.0  # 大気圏に入るとみなす高度 [m]
    fpa_lo: float = -4.0  # 再突入角のウィンドウ [°](これより深いと燃える)
    fpa_hi: float = -1.5  # (これより浅いと弾かれる)
    att_tol: float = 20.0  # 耐熱シールドを前に向ける許容 [°]
    chute_lo: float = 1_500.0  # パラシュートを開く高度のウィンドウ [m]
    chute_hi: float = 4_000.0
    chute_speed: float = 200.0  # これより速いと破れる [m/s]
    splash_max: float = 12.0  # 着水の速度 [m/s]


@dataclass
class MissionDef:
    id: str
    title: str
    goal: str
    kind: str
    rocket: Rocket
    craft: str = "eagle1"  # 会社で製造する機体の種類
    waypoint: Waypoint = None
    orbit: Orbit = None
    sep: Sep = None
    land: Landing = None
    entry: Entry = None
    start: dict = None  # 飛行の途中から始めるときの初期状態
    time_limit: float = 150.0
    time_scale: float = TIME_SCALE  # 物理を実時間の何倍で進めるか(オープニングは史実どおりの時刻に火災が起きるよう等倍)
    tilt_limit: float = 45.0  # これ以上傾くと飛行中断 [°](0 なら制限なし)
    can_cutoff: bool = False  # SPACE でエンジンを止められる
    fire_chance: float = 0.0
    fire_chance_inspected: float = 0.0
    gimmick: str = ""  # slosh(推進剤の揺れ)/ anomaly(タンク異常)/ engine_out(エンジン1基停止)
    gimmick_chance: float = 1.0
    gimmick_chance_inspected: float = 1.0
    # WP1 を通過して成功が決まったあとも飛び続ける打ち上げ(Ch1-1)。評価は WP1 の値だけ
    #   WP2: 分離。姿勢をこの窓({キー: Window})に入れて SPACE でエンジンを止め、推力が消えたら自動で分離
    #   WP3: 2段目でこの高さ [m] を目指すが、推進剤の偏りで姿勢を崩して必ず爆発する
    #   (史実: Falcon 1 の 2 号機。推進剤の揺れが止まらず、宇宙には届いたが軌道には届かなかった)
    sep_windows: dict = None
    wp3_alt: float = 0.0
    tlm_success: int = 40
    rep_success: int = 10
    reward: float = 0.0  # 初めて成功したときの報酬 [M$]
    income: float = 0.0  # 打ち上げるたびに入る代金 [M$]
    reusable: bool = False  # 着陸に成功すると機体が手元に残る
    guide: tuple = ()  # 軌道へ上がる途中の目安(GuideWP の並び)


# ---- Chapter 1: Eagle 1 ----
# オープニングの初飛行(ステージの並びには入らない。ゲームの最初に飛び、必ず火災で爆発する)
OPENING = MissionDef(
    id="opening",
    title="初飛行",
    goal="高度 10 km を突破せよ",
    kind="ascent",
    rocket=Rocket("Eagle 1", [EAGLE1]),
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
    time_scale=1,
    fire_chance=0.8,
    fire_chance_inspected=0.25,
    tlm_success=40,
    rep_success=10,
)

CH1_1 = MissionDef(
    id="1-1",
    title="Ch1-1 宇宙へ",
    goal="高度 100 km に到達せよ",
    kind="ascent",
    rocket=eagle1(1_000.0),
    waypoint=Waypoint(
        name="WP1",
        altitude=100_000.0,
        windows={
            "t": Window("時刻", 125.0, 175.0, "s"),
            "vy": Window("垂直速度", 1500.0, 2500.0, "m/s"),
            "ang": Window("傾き", -12.0, 12.0, "°"),
            "rate": Window("角速度", -2.0, 2.0, "°/s"),
        },
    ),
    sep=Sep(auto=True),
    time_limit=260.0,
    fire_chance=0.35,
    fire_chance_inspected=0.08,
    gimmick="slosh",
    can_cutoff=True,
    sep_windows={
        "ang": Window("傾き", -5.0, 5.0, "°"),
        "rate": Window("角速度", -0.5, 0.5, "°/s"),
    },
    wp3_alt=300_000.0,
    tlm_success=50,
    rep_success=12,
    reward=30.0,
)

CH1_2 = MissionDef(
    id="1-2",
    title="Ch1-2 相乗り便",
    goal="小型衛星を軌道に乗せよ",
    kind="orbit",
    rocket=eagle1(200.0, s2_scale=1.3),  # 初めての軌道なので、2段目に余裕を持たせる
    orbit=Orbit(pe_lo=300_000.0, ap_hi=800_000.0, att_tol=20.0, rate_tol=3.0, release_time=30.0),
    # 目安は、近地点 380 km・遠地点 700 km ほどに入る飛び方(2段目は推力が小さいので、上へ上がりながら加速する)
    guide=(GuideWP(200, 1_100, 1_800, 1_400, 2_300), GuideWP(400, 500, 1_200, 2_300, 3_800),
           GuideWP(600, -100, 600, 5_500, 7_900), GuideWP(800, -300, 300, 7_300, 7_900)),
    sep=Sep(),
    time_limit=3000.0,
    tilt_limit=135.0,
    can_cutoff=True,
    fire_chance=0.3,
    fire_chance_inspected=0.06,
    tlm_success=60,
    rep_success=12,
    reward=10.0,
)

CH1_3 = MissionDef(
    id="1-3",
    title="Ch1-3 最後の1機",
    goal="ダミー衛星を軌道に乗せよ",
    kind="orbit",
    rocket=eagle1(165.0),
    orbit=Orbit(pe_lo=550_000.0, ap_hi=750_000.0, att_tol=10.0, rate_tol=1.5, release_time=20.0),
    sep=Sep(),
    time_limit=6000.0,
    tilt_limit=135.0,
    can_cutoff=True,
    tlm_success=70,
    rep_success=20,
    reward=60.0,
)

CH1_4 = MissionDef(
    id="1-4",
    title="Ch1-4 最初の顧客",
    goal="観測衛星を円軌道に乗せよ",
    kind="orbit",
    rocket=eagle1(180.0),
    orbit=Orbit(pe_lo=650_000.0, ap_hi=750_000.0, att_tol=5.0, rate_tol=0.5, release_time=15.0),
    sep=Sep(),
    time_limit=6000.0,
    tilt_limit=135.0,
    can_cutoff=True,
    fire_chance=0.25,
    fire_chance_inspected=0.05,
    tlm_success=80,
    rep_success=20,
    reward=20.0,
)

# ---- Chapter 2: Eagle 9 + 貨物カプセル Phoenix ----
CH2_1 = MissionDef(
    id="2-1",
    title="Ch2-1 Eagle 9 初飛行",
    goal="試験カプセルを軌道に乗せよ",
    kind="orbit",
    rocket=eagle9(6_000.0, "capsule"),
    craft="eagle9",
    orbit=Orbit(pe_lo=100_000.0, ap_hi=220_000.0, att_tol=10.0, rate_tol=1.5, release_time=25.0),
    sep=Sep(),
    time_limit=600.0,
    tilt_limit=135.0,
    can_cutoff=True,
    fire_chance=0.3,
    fire_chance_inspected=0.06,
    tlm_success=80,
    rep_success=15,
    reward=50.0,
)

CH2_2 = MissionDef(
    id="2-2",
    title="Ch2-2 還ってきたカプセル",
    goal="カプセルを再突入させ、海に着水させよ",
    kind="reentry",
    rocket=Rocket("Phoenix", [PHOENIX], cargo="none"),
    craft="eagle9",
    entry=Entry(),
    start=dict(y=100_000.0, orbit=True, theta=math.pi / 2),
    time_limit=1500.0,
    tilt_limit=0.0,
    can_cutoff=True,
    tlm_success=80,
    rep_success=15,
    reward=50.0,
)

CH2_3 = MissionDef(
    id="2-3",
    title="Ch2-3 民間初の到着",
    goal="ステーションの把持点でカプセルを止めよ",
    kind="dock",
    rocket=Rocket("Phoenix", [PHOENIX], cargo="none"),
    craft="eagle9",
    time_limit=180.0,
    tilt_limit=0.0,
    tlm_success=80,
    rep_success=20,
    reward=60.0,
)

CH2_4 = MissionDef(
    id="2-4",
    title="Ch2-4 初の静止衛星",
    goal="通信衛星を遠地点 2000 km の軌道へ送れ",
    kind="orbit",
    rocket=eagle9(4_000.0),
    craft="eagle9",
    orbit=Orbit(pe_lo=80_000.0, ap_lo=1_800_000.0, ap_hi=2_200_000.0, att_tol=10.0, rate_tol=1.5,
                release_time=30.0, prop_bonus=0.04, time_bonus=380.0),
    sep=Sep(),
    time_limit=700.0,
    tilt_limit=135.0,
    can_cutoff=True,
    fire_chance=0.25,
    fire_chance_inspected=0.05,
    tlm_success=90,
    rep_success=15,
    reward=70.0,
)

CH2_5 = MissionDef(
    id="2-5",
    title="Ch2-5 定期便の試練",
    goal="補給カプセルを軌道に乗せよ",
    kind="orbit",
    rocket=eagle9(6_000.0, "capsule"),
    craft="eagle9",
    orbit=Orbit(pe_lo=100_000.0, ap_hi=200_000.0, att_tol=8.0, rate_tol=1.0, release_time=20.0),
    sep=Sep(),
    time_limit=600.0,
    tilt_limit=135.0,
    can_cutoff=True,
    gimmick="anomaly",
    gimmick_chance=0.75,
    gimmick_chance_inspected=0.1,
    tlm_success=90,
    rep_success=15,
    reward=60.0,
)

# ---- Chapter 3: 戻ってくるロケット ----
CH3_1 = MissionDef(
    id="3-1",
    title="Ch3-1 跳ねるバッタ",
    goal="100 m まで上がり、隣のパッドに降りよ",
    kind="hop",
    rocket=Rocket("Hopper", [HOPPER], cargo="none"),
    craft="hopper",
    land=Landing(site="pad", x=80.0, half_w=14.0, vy_max=5.0, vx_max=2.5, tilt_max=8.0,
                 vy_good=2.5, dist_good=5.0, hop_alt=100.0),
    time_limit=150.0,
    tilt_limit=60.0,
    can_cutoff=True,
    tlm_success=60,
    rep_success=8,
    reward=5.0,
    reusable=True,
)

_BOOSTER = Rocket("Eagle 9", [EAGLE9_S1R], cargo="none")

CH3_2 = MissionDef(
    id="3-2",
    title="Ch3-2 海面に立つ",
    goal="1段目を海面の上で静止させよ",
    kind="landing",
    rocket=_BOOSTER,
    craft="eagle9",
    land=Landing(site="sea", half_w=1e9, vy_max=6.0, vx_max=5.0, tilt_max=12.0, vy_good=3.0, q_limit=28_000.0),
    start=dict(y=52_000.0, vx=420.0, vy=-260.0, prop=6_000.0, booster=True),
    time_limit=260.0,
    tilt_limit=0.0,
    can_cutoff=True,
    tlm_success=70,
    rep_success=10,
    reward=10.0,
    income=22.0,
)

CH3_3 = MissionDef(
    id="3-3",
    title="Ch3-3 台船の試練",
    goal="1段目を洋上の台船に降ろせ",
    kind="landing",
    rocket=_BOOSTER,
    craft="eagle9",
    land=Landing(site="ship", half_w=28.0, vy_max=6.0, vx_max=5.0, tilt_max=12.0, vy_good=3.0, dist_good=8.0,
                 heave=1.0, wind=7.0, q_limit=28_000.0, place=True, deck=4.0),
    start=dict(y=52_000.0, vx=420.0, vy=-260.0, prop=6_000.0, booster=True),
    time_limit=260.0,
    tilt_limit=0.0,
    can_cutoff=True,
    tlm_success=80,
    rep_success=15,
    reward=15.0,
    income=22.0,
    reusable=True,
)

CH3_4 = MissionDef(
    id="3-4",
    title="Ch3-4 帰ってきた",
    goal="衛星を送り出し、1段目を発射場に戻せ",
    kind="recover",
    rocket=eagle9(2_500.0, recover=True),
    craft="eagle9",
    sep=Sep(alt_lo=22_000.0, speed_lo=850.0),
    land=Landing(site="pad", x=400.0, half_w=40.0, vy_max=6.0, vx_max=5.0, tilt_max=12.0, vy_good=3.0,
                 dist_good=10.0, q_limit=28_000.0),
    time_limit=520.0,
    tilt_limit=0.0,
    can_cutoff=True,
    tlm_success=100,
    rep_success=20,
    reward=20.0,
    income=22.0,
    reusable=True,
)

CH3_5 = MissionDef(
    id="3-5",
    title="Ch3-5 海の上の小さな島",
    goal="補給便を送り出し、1段目を台船に降ろせ",
    kind="recover",
    rocket=eagle9(6_000.0, "capsule", recover=True),
    craft="eagle9",
    sep=Sep(alt_lo=25_000.0, speed_lo=1_000.0),
    land=Landing(site="ship", half_w=28.0, vy_max=6.0, vx_max=5.0, tilt_max=12.0, vy_good=3.0, dist_good=8.0,
                 heave=1.0, wind=6.0, q_limit=28_000.0, place=True, deck=4.0),
    time_limit=520.0,
    tilt_limit=0.0,
    can_cutoff=True,
    tlm_success=100,
    rep_success=25,
    reward=20.0,
    income=28.0,
    reusable=True,
)

CH3_6 = MissionDef(
    id="3-6",
    title="Ch3-6 二度目の空",
    goal="回収した機体で商業衛星を軌道に乗せよ",
    kind="orbit",
    rocket=eagle9(5_000.0),
    craft="eagle9",
    orbit=Orbit(pe_lo=110_000.0, ap_hi=170_000.0, att_tol=8.0, rate_tol=1.0, release_time=20.0),
    sep=Sep(),
    time_limit=600.0,
    tilt_limit=135.0,
    can_cutoff=True,
    gimmick="engine_out",
    gimmick_chance=0.8,
    gimmick_chance_inspected=0.15,
    tlm_success=100,
    rep_success=25,
    reward=30.0,
    income=28.0,
)

ORDER = [CH1_1, CH1_2, CH1_3, CH1_4, CH2_1, CH2_2, CH2_3, CH2_4, CH2_5,
         CH3_1, CH3_2, CH3_3, CH3_4, CH3_5, CH3_6]
MISSIONS = {m.id: m for m in ORDER}


def next_stage(stage_id):
    """次のステージの id。最後なら None。"""
    i = [m.id for m in ORDER].index(stage_id)
    return ORDER[i + 1].id if i + 1 < len(ORDER) else None


def entry_angle(y, vx, vy, interface):
    """いまの軌道のまま大気圏(interface の高度)に入るときの再突入角 [°]。届かなければ None。"""
    r, ri = PLANET_R + y, PLANET_R + interface
    if r <= ri:
        return math.degrees(math.atan2(vy, abs(vx))) if vx else -90.0
    v2 = vx * vx + vy * vy + 2 * MU * (1 / ri - 1 / r)
    vt = r * vx / ri
    if v2 <= vt * vt:
        return None
    return -math.degrees(math.acos(max(-1.0, min(1.0, abs(vt) / math.sqrt(v2)))))


ENTRY_Q = 12_000.0  # 降下中、動圧がここまで上がったら再突入噴射を始める [Pa]
ENTRY_SPEED = 400.0  # 再突入噴射でここまで減速する [m/s]


class MissionRun:
    """1 回の飛行の進行と判定を持つ。"""

    AOA_LIMIT = math.radians(12.0)
    Q_LIMIT = 12_000.0
    DOOMED_FIRE_AT = 27.0  # オープニングの飛行で火災が起きる時刻 [s]
    SPACE_LINE = 100_000.0  # これより上は空気がなく、早送りできる
    RECOVERY_ENGINES = 3 / 9  # 戻りの噴射・再突入噴射に使うエンジンの割合(9 基のうち 3 基)
    LANDING_ENGINES = 0.134  # 着陸噴射は中央の 1 基だけ(最低出力でも、軽くなった機体はわずかに浮く)
    LANDING_ALT = 12_000.0  # これより下で点火すると着陸噴射になる

    def __init__(self, mdef, inspected=False, seed=None, doomed=False):
        """doomed: オープニングの飛行。決まった時刻に火災が起き、何をしても爆発する。"""
        self.m = mdef
        self.v = mdef.rocket.make()
        self.time_scale = mdef.time_scale
        self.v.time_scale = mdef.time_scale
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
        self.dropped = []  # 切り離した段(画面で描くために渡す)
        # 段・軌道・着陸
        self.stage_no = 1
        self.phase = "s1"  # s1 → s2 → release / descent / deorbit → entry → chute
        self.meco_told = False
        self.sep_wait = 0.0
        self.release_timer = 0.0
        self.in_orbit = False
        self.released = None  # 放出したときの値
        self.guide_values = {}  # 目安の時刻を過ぎたときの値 {時刻: (垂直速度, 水平速度)}
        self.sep_values = None  # 分離したときの値(回収)
        self.ship_x = mdef.land.x if mdef.land else 0.0
        self.pred_x = None  # 1段目の着地予想点 [m](噴射中は、計算にかかる時間のぶん先を読んだ値)
        self.pred_raw = None  # 最後に計算し終えた予想点と、その計算を始めた時刻、予想点の動く速さ
        self.ghost = None
        self.touch = None  # 接地したときの値
        self.apex = 0.0
        self.q_stress = 0.0
        self.vehicle_lost = True  # 失敗したとき機体を失うか(安全に降りた失敗なら False)
        self.tumble_t = None  # 2段目が揺れ始めてからの時間(wp3_alt のミッション)
        self.sep_t = None  # 分離した時刻
        self.wp2_values = None  # WP2(分離)のときの値
        self.tumble_warned = False
        self.end_note = ""  # 成功のあとに起きたこと(結果の画面に出す)
        self.lost_after_success = False  # 成功は決まったが、そのあと機体を失った
        self.saved = False  # 機体は失ったが、カプセルは救えた(Ch2-5)
        self.warp = 1  # 早送りの倍率
        self.steer_in = 0
        # 再突入
        self.entry_values = None
        self.chute_values = None
        self.peak_heat = 0.0
        # 故障・揺れ
        gc = mdef.gimmick_chance_inspected if inspected else mdef.gimmick_chance
        self.gimmick_on = bool(mdef.gimmick) and rng.random() < gc
        self.gimmick_at = rng.uniform(38.0, 55.0)
        self.slosh = 0.0  # 揺れの強さ [rad/s^2]
        self.slosh_phase = 0.0
        self.slosh_time = 0.0
        self.slosh_push = 0.0
        self.anomaly_left = None  # タンク異常: 分解までの残り秒数
        self.engine_out = False
        self._apply_start(mdef.start)

    # 揺れ: 強さの始めと終わり [rad/s^2]、強くなりきるまでの秒数、不規則な押され方の時定数、周期
    SLOSH = (math.radians(0.9), math.radians(2.7), 28.0, 2.8, 6.0)

    def _apply_start(self, start):
        if not start:
            return
        v = self.v
        v.lifted_off = v.launched = True
        v.y = start.get("y", 0.0)
        v.vx = start.get("vx", 0.0)
        v.vy = start.get("vy", 0.0)
        if start.get("orbit"):
            v.vx = math.sqrt(MU / (PLANET_R + v.y))
        if "prop" in start:
            v.prop = start["prop"]
        if start.get("booster"):  # 分離を終えて落ちてくる1段目
            self.phase = "descent"
            v.engine_frac = self.RECOVERY_ENGINES
            v.fins = True
            v.ignitions_left = 3  # 再突入噴射・着陸噴射と、やり直し 1 回
            v.theta = math.atan2(-v.vx, -v.vy)  # エンジンを進む向きに
            if self.m.land.place:
                self.ship_x = round(predict_touchdown(v) + v.rng.uniform(-150, 150))
        else:
            v.theta = start.get("theta", 0.0)
        if self.m.kind == "reentry":
            self.phase = "deorbit"

    def emit(self, kind, text):
        self.events.append((kind, text))

    # ---- プレイヤーの操作 ----
    def space(self):
        """SPACE: 点火。止められる機体なら、噴射中に押すと停止。"""
        v = self.v
        if self.result is not None:
            return
        if v.engine_on:
            if self.m.can_cutoff and v.throttle > 0.5:  # 点火の押し直しで、立ち上がる前に止めてしまわない
                v.cutoff()
                self.emit("info", "エンジン停止")
            return
        if self.phase == "chute" or self.anomaly_left is not None:
            return
        if self.m.sep and self.stage_no == 1 and v.upper and v.launched and not self.m.sep.auto \
                and self.m.kind != "recover" and self.phase == "s1":
            self.emit("warn", "先に Z で1段目を分離して")
            return
        first = not v.launched
        if v.ignite():
            self.emit("good", "点火!")
            if first and v.t > 0:  # 時刻はカウントダウン 0 から。点火までの待ちのぶん、故障の時刻を後ろへずらす
                if self.fire_at is not None:
                    self.fire_at += v.t
                self.gimmick_at += v.t
        elif v.ignitions_left <= 0:
            self.emit("warn", "もう点火できない")

    def z(self):
        """Z: 段分離 / 荷物の放出 / パラシュート。"""
        if self.result is not None:
            return
        v = self.v
        if self.anomaly_left is not None:
            self.saved = True
            self.vehicle_lost = True
            return self.fail("機体は分解。カプセルは脱出して無事")
        if self.m.kind == "reentry":
            return self._chute()
        if self.m.sep and self.stage_no == 1 and v.upper and v.launched:
            return self._separate()
        if self.m.kind == "orbit" and not v.upper and v.launched:
            return self._release()

    def _separate(self):
        v, sep = self.v, self.m.sep
        if v.engine_on:
            return self.fail("噴射中に分離して、1段目が追突")
        if v.throttle > sep.tail:
            return self.fail("残った推力で1段目が追突")
        if abs(math.degrees(v.omega)) > sep.rate_max:
            return self.fail("回転したまま分離して接触")
        if self.m.kind == "recover":
            self.sep_values = {"alt": v.y, "speed": v.speed}
            if v.y < sep.alt_lo or v.speed < sep.speed_lo:
                return self.fail("分離が早すぎて、2段目が軌道に届かない")
            self.dropped.append(v.separate(keep_lower=True))
            v.engine_frac = self.RECOVERY_ENGINES
            v.fins = True
            self.phase = "descent"
            if self.m.land.place:
                self.ship_x = round(predict_touchdown(v) + v.rng.uniform(-150, 150))
            self.emit("good", "分離成功。2段目は軌道へ向かった")
            self.emit("info", trf("1段目を連れて帰れ。点火はあと {n} 回", n=v.ignitions_left))
            return
        self.dropped.append(v.separate())
        self.stage_no = 2
        self.phase = "s2"
        self.emit("good", "1段分離。SPACE で2段目に点火")

    def _release(self):
        v, o = self.v, self.m.orbit
        if v.engine_on or v.throttle > 0.05:
            return self.fail("噴射中に放出して衝突")
        pe, ap = v.apsides()
        vals = {"pe": pe, "ap": ap, "att": math.degrees(v.theta) - 90.0, "rate": math.degrees(v.omega),
                "prop": v.prop / v.p.prop_mass, "t": v.t}
        self.released = vals
        if pe < o.pe_lo:
            return self.fail("近地点が低すぎて、荷物は大気圏に落ちた")
        if ap > o.ap_hi or ap < o.ap_lo:
            return self.fail("軌道が目標から外れたまま放出")
        if abs(vals["att"]) > o.att_tol:
            return self.fail("向きがずれたまま放出(投入失敗)")
        if abs(vals["rate"]) > o.rate_tol:
            return self.fail("回転が残ったまま放出(投入失敗)")
        self.result = "success"
        self.dropped.append(dict(x=v.x + math.sin(v.theta) * v.length, y=v.y + math.cos(v.theta) * v.length,
                                 vx=v.vx + math.sin(v.theta) * 2, vy=v.vy + math.cos(v.theta) * 2,
                                 theta=v.theta, omega=0.0, params=None, upper=[], lower=False,
                                 cargo=self.m.rocket.cargo, t=v.t))
        self.emit("good", "放出成功! 軌道投入を確認")

    def _chute(self):
        v, e = self.v, self.m.entry
        if self.phase != "entry":
            self.emit("warn", "パラシュートは大気圏に入ってから")
            return
        self.chute_values = {"alt": v.y, "speed": v.speed}
        if v.speed > e.chute_speed or v.y > e.chute_hi * 1.5:
            return self.fail("速すぎるところで開いて、パラシュートが破れた")
        v.drag_mult = 70.0
        self.phase = "chute"
        self.emit("good", "パラシュート展開")

    # ---- 1 ステップ ----
    def step(self, dt, steer=0, throttle_input=0, translate=0):
        if self.result is not None:
            return
        v, m = self.v, self.m
        self.steer_in = steer
        v.step(dt, steer, throttle_input, translate)
        self.max_alt = max(self.max_alt, v.y)
        for g in m.guide:  # 目安の時刻を過ぎたら、そのときの速さを残して知らせる
            if g.t not in self.guide_values and v.launched and v.t >= g.t and self.released is None:
                self.guide_values[g.t] = (v.vy, v.vx)
                ok = g.vy_lo <= v.vy <= g.vy_hi and g.vx_lo <= v.vx <= g.vx_hi
                self.emit("good" if ok else "info", trf("WP T+{t:.0f}: 垂直 {vy:.0f} / 水平 {vx:.0f} m/s",
                                                        t=g.t, vy=v.vy, vx=v.vx))
        self.apex = max(self.apex, v.y)

        # 最大動圧の通知
        if v.q > self.max_q:
            self.max_q = v.q
        elif not self.maxq_announced and self.max_q > 8_000 and v.q < self.max_q * 0.97 and self.phase == "s1":
            self.maxq_announced = True
            self.emit("info", "最大動圧を通過")

        # プレイヤーが対処する猶予(火災・故障・空中分解・放出など)は画面の時間 rt で数える
        rt = dt / self.time_scale
        if self._fire(rt) or self._gimmick(rt):
            return

        # 空力による分解(落ちてくる機体は、エンジン側を前に向けていればよい)
        tail_ok = self.phase in ("descent", "entry", "chute", "deorbit")
        aoa = min(abs(v.aoa), abs(v.aoa_tail)) if tail_ok else abs(v.aoa)
        # 短い2段目や、落ちてくる1段目は、長い機体よりも曲げに強い
        tough = 2.5 if self.stage_no >= 2 else 1.7 if tail_ok else 1.0
        if aoa > self.AOA_LIMIT * (2.0 if tail_ok else 1.0) and v.q > self.Q_LIMIT * tough and self.phase != "chute":
            self.stress += rt
            if self.stress > 0.6:
                return self.fail("迎角が大きすぎて空中分解")
        else:
            self.stress = max(0.0, self.stress - rt)

        if m.tilt_limit and v.lifted_off and abs(v.theta) > math.radians(m.tilt_limit):
            if self.tumble_t is not None:
                return self._s2_lost()
            return self.fail("姿勢を失ったため飛行中断(自爆)")
        if v.t > m.time_limit:
            return self.fail("時間切れ")

        step = getattr(self, "_step_" + m.kind)
        if step(dt):
            return
        if v.lifted_off and v.y < 0 and self.result is None:
            return self.fail("墜落")

    def _fire(self, dt):
        """1段目の故障。出力を絞って耐える。
        オープニングの初飛行は史実どおり燃料漏れの火災(絞っても消えない)。ほかはターボポンプの異常振動。"""
        v = self.v
        if self.fire_at is None or self.fire_done or self.stage_no != 1 or not v.engine_on or v.t < self.fire_at:
            if self.fire_active and not v.engine_on:  # エンジンを止めれば火も消える
                self.fire_active = False
                self.fire_done = True
            return False
        if not self.fire_active:
            self.fire_active = True
            self.emit("warn", "エンジン区画で火災! 出力を最低まで絞れ!" if self.doomed else
                      "ターボポンプに異常振動! 出力を最低まで絞れ!")
        self.fire_time += dt
        over = (v.throttle - v.p.min_throttle) / (1.0 - v.p.min_throttle)
        if self.doomed:  # 絞っても消えない
            self.heat += 30.0 * dt
        elif over > 0.08:
            self.heat += (4.0 + 22.0 * over) * dt
        else:
            self.heat = max(0.0, self.heat - 6.0 * dt)
        if self.heat >= 100.0:
            self.fail("火災でエンジンが爆発" if self.doomed else "ターボポンプが壊れてエンジンが爆発")
            return True
        if self.fire_time >= 12.0:
            self.fire_active = False
            self.fire_done = True
            self.emit("info", "振動が収まった。出力を戻してよし")
        return False

    def _gimmick(self, dt):
        v, g = self.v, self.m.gimmick
        if not self.gimmick_on:
            return False
        if g == "slosh":
            # 2段目の推進剤の揺れ。機体が不規則に左右へ押され、燃えるほど強くなる。逆に当てて支える
            if self.stage_no == 2 and v.engine_on:
                if self.slosh == 0.0 and v.prop < v.p.prop_mass * 0.9:
                    self.slosh = self.SLOSH[0]
                    self.emit("warn", "推進剤が揺れている! 逆に当てて姿勢を支えろ")
                if self.slosh > 0.0:
                    lo, hi, ramp, tau, period = self.SLOSH
                    self.slosh_time += dt
                    self.slosh = lo + (hi - lo) * min(1.0, self.slosh_time / ramp)
                    self.slosh_phase += math.tau / period * dt
                    self.slosh_push += -self.slosh_push / tau * dt + v.rng.gauss(0, 1) * math.sqrt(2 * dt / tau)
                    v.torque_bias = self.slosh * (0.45 * math.sin(self.slosh_phase) + 0.55 * self.slosh_push)
            else:
                v.torque_bias = 0.0
        elif g == "anomaly":
            if self.anomaly_left is None:
                if self.stage_no == 1 and v.engine_on and v.t >= self.gimmick_at:
                    self.anomaly_left = 5.0
                    self.emit("warn", "2段タンクの圧力が異常! Z でカプセルを切り離せ!")
            else:
                self.anomaly_left -= dt
                if self.anomaly_left <= 0:
                    self.fail("2段タンクが破裂して空中分解")
                    return True
        elif g == "engine_out":
            if not self.engine_out and self.stage_no == 1 and v.engine_on and v.t >= self.gimmick_at - 12.0:
                self.engine_out = True
                v.engine_frac *= 8 / 9
                v.torque_bias = math.radians(0.9) * v.rng.choice((-1, 1))
                self.emit("warn", "エンジン1基停止! 機体が片側へ回る。当て続けて支えろ")
            if self.engine_out and self.stage_no != 1:
                v.torque_bias = 0.0
        return False

    # ---- 種類ごとの進行 ----
    def _auto_sep(self, dt):
        """自動の段分離(Ch1-2)。"""
        v, sep = self.v, self.m.sep
        if not (sep and sep.auto and self.stage_no == 1 and v.upper and v.launched and not v.engine_on):
            return
        if v.throttle <= sep.tail:
            if self.m.sep_windows:
                self._judge_wp2()
            self.dropped.append(v.separate())
            self.stage_no = 2
            self.phase = "s2"
            self.sep_t = v.t
            self.emit("good", "1段分離(自動)。SPACE で2段目に点火")

    def _judge_wp2(self):
        """WP2(分離)の判定。評価(ランク)には入れず、メッセージで知らせる。"""
        v = self.v
        if self.wp_values is None:
            self.emit("info", "WP2: WP1 より前に分離した")
            return
        now = self._wp_now()
        self.wp2_values = {k: now[k] for k in self.m.sep_windows}
        ok = all(w.ok(now[k]) for k, w in self.m.sep_windows.items())
        self.emit("good" if ok else "info", trf("WP2 分離: 高度 {alt:.0f} km 傾き {ang:+.1f}° 角速度 {rate:+.2f}°/s",
                                                alt=v.y / 1000, ang=now["ang"], rate=now["rate"]))

    def _step_ascent(self, dt):
        v, wp = self.v, self.m.waypoint
        self._auto_sep(dt)
        if v.lifted_off and v.prop <= 0 and not v.upper and v.y < wp.altitude:
            # 最後の段が燃え尽きた。惰性でも届かないなら失敗
            r = PLANET_R + v.y
            if v.vy <= 0 or v.y + v.vy ** 2 / (2 * MU / (r * r)) < wp.altitude:
                return self.fail("燃料切れ")
        if v.launched and v.vy < -50 and v.y < wp.altitude:
            return self.fail("高度が足りず落下")
        if self.wp_values is not None and self.m.wp3_alt:
            return self._tumble(dt)
        if v.y >= wp.altitude and self.wp_values is None:
            self.wp_values = self._wp_now()
            self.emit("good", trf("{name} 通過! 高度 {alt:.0f} km を突破", name=wp.name, alt=wp.altitude / 1000))
            if self.m.wp3_alt:  # 成功は決まり。飛行は続けて、分離(WP2)と WP3 を目指す
                if self.stage_no == 1:
                    self.emit("info", "次は WP2: 姿勢を整えて SPACE でエンジン停止。推力が消えたら自動で分離")
            else:
                self.result = "success"
        return False

    TUMBLE_RAMP = 4.0  # 推進剤の偏りが最大になるまで [s](画面の時間)
    TUMBLE_TIME = 15.0  # 念のための上限。ふつうはその前に迎角が大きくなって爆発する [s]
    TUMBLE_AOA = math.radians(20.0)  # 迎角がこれを超えると爆発する

    def _tumble(self, dt):
        """WP1 通過後の2段目: WP3 を目指して点火すると、推進剤が偏って姿勢を崩し、爆発する(必ず)。
        点火しないまま 15 秒たったときも、同じように揺れ始める。
        推進剤が偏ると姿勢の操作がだんだん効きすぎる(ピーキー)ようになり、当てすぎて迎角が大きくなると爆発する。"""
        v = self.v
        if self.stage_no != 2:
            return False
        rt = dt / self.time_scale
        if self.tumble_t is None:
            if not v.engine_on and v.t - self.sep_t < 15.0:
                return False
            self.tumble_t = 0.0
            self.slosh_phase = 0.0
            self.tumble_dir = v.rng.choice((-1.0, 1.0))  # 偏りで回される向き
            self.emit("warn", "2段目の推進剤が偏っている! 姿勢の効きが不安定")
        self.tumble_t += rt
        k = min(1.0, self.tumble_t / self.TUMBLE_RAMP)
        v.steer_gain = 1.0 + 9.0 * k  # 操作が効きすぎる(最後は 10 倍)
        self.slosh_phase += math.tau / (2.6 - 1.0 * k) * rt  # 偏った推進剤が揺れて、機体を振る
        # 偏りで重心がずれ、推力が機体を一方へ回そうとする。この力は時間とともに強まり、
        # 効きすぎる操作でも 8 秒ほどで支えきれなくなる。そこに揺れが重なる
        v.torque_bias = self.tumble_dir * math.radians(2.2 * self.tumble_t) +             math.radians(2.0 + 6.0 * k) * math.sin(self.slosh_phase)
        aoa = abs(v.aoa)
        if aoa > self.TUMBLE_AOA * 0.5 and not self.tumble_warned:
            self.tumble_warned = True
            self.emit("bad", "迎角が大きい! 姿勢を保てない!")
        # WP3 には届かせない(届きそうなら、そこで爆発させる)
        if (aoa > self.TUMBLE_AOA and self.tumble_t > 3.0) or self.tumble_t >= self.TUMBLE_TIME                 or v.y > self.m.wp3_alt - 20_000:
            return self._s2_lost()
        return False

    def _s2_lost(self):
        self.result = "success"
        self.lost_after_success = True
        self.end_note = "推進剤の偏りで迎角が大きくなりすぎ、2段目が爆発"
        self.emit("bad", self.end_note)
        return True

    def _wp_now(self):
        v = self.v
        return {"t": v.t, "vy": v.vy, "vx": v.vx, "ang": math.degrees(v.theta), "rate": math.degrees(v.omega)}

    def _meco_notice(self):
        v = self.v
        if self.stage_no == 1 and v.launched and not v.engine_on and not self.meco_told and v.upper:
            self.meco_told = True
            self.emit("info", "1段エンジン停止。推力が消えたら Z で分離")

    def _step_orbit(self, dt):
        v, o = self.v, self.m.orbit
        self.warp = 1
        self._meco_notice()
        if self.stage_no == 1:
            if v.launched and v.vy < -80:
                return self.fail("分離しないまま落下")
            return False
        pe, ap = v.apsides()
        ok = pe >= o.pe_lo and o.ap_lo <= ap <= o.ap_hi
        burning = v.engine_on or v.throttle > 0.05
        self.in_orbit = ok and not burning
        if v.y < 30_000 and v.vy < 0:
            return self.fail("軌道に届かず、大気圏に落下")
        if burning:
            self.release_timer = 0.0
            return False
        if ok:
            self.release_timer += dt / self.time_scale
            if self.release_timer > o.release_time:
                return self.fail("放出の時間切れ")
            return False
        self.release_timer = 0.0
        if v.launched and (v.prop <= 0 or v.ignitions_left <= 0):
            if pe >= 70_000:
                return self.fail("軌道が目標から外れた")
            return self.fail("燃料切れ(軌道に届かず)" if v.prop <= 0 else "点火回数を使い切った(軌道に届かず)")
        # 惰性飛行: 遠地点が近づくまで早送り
        tta = time_to_apoapsis(v.y, v.vx, v.vy)
        if v.y > self.SPACE_LINE and tta is not None and tta > 14 and self.steer_in == 0 \
                and v.ignitions_left < v.p.ignitions:
            # 地球の軌道は遠地点まで何十分もかかる。遠いうちは大きく早送りし、近づいたら倍率を落とす
            self.warp = 30 if tta > 120 else 6
        return False

    def _step_recover(self, dt):
        v = self.v
        self._meco_notice()
        if self.phase == "s1":
            if v.launched and v.vy < -80:
                return self.fail("分離しないまま落下")
            return False
        return self._step_landing(dt)

    def _step_hop(self, dt):
        v, land = self.v, self.m.land
        if v.lifted_off and v.y <= 0.0 and abs(v.x) < land.half_w and self.apex < 3.0:
            # 発射パッドの上で浮ききれずに戻った
            v.y = v.vy = v.vx = v.omega = 0.0
            v.lifted_off = False
            self.apex = 0.0
            return False
        return self._step_landing(dt)

    def tilt_deg(self):
        """鉛直からの傾き [°](-180〜180)。"""
        return (math.degrees(self.v.theta) + 180.0) % 360.0 - 180.0

    def deck_y(self):
        """着陸目標の表面の高さ [m]。"""
        land = self.m.land
        if not land or land.site != "ship":
            return 0.0
        return land.deck + land.heave * math.sin(math.tau * self.v.t / land.period)

    def _step_landing(self, dt):
        v, land = self.v, self.m.land
        if self.phase == "descent" and not v.engine_on and v.throttle < 0.02:
            low = v.y < self.LANDING_ALT and v.vy < 0
            v.engine_frac = self.LANDING_ENGINES if low else self.RECOVERY_ENGINES
        # 低空の横風(高度 4 km より下で強くなる)
        if land.wind:
            k = max(0.0, min(1.0, (4_000.0 - v.y) / 3_000.0))
            v.wind = land.wind * k * (0.7 + 0.3 * math.sin(v.t * 0.7))
        # 降下中の動圧: 再突入噴射で速度を落とさないと壊れる
        if land.q_limit and self.phase == "descent":
            if v.q > land.q_limit:
                self.q_stress += dt / self.time_scale
                if self.q_stress > 1.5:
                    return self.fail("減速が足りず、再突入で機体が分解")
            else:
                self.q_stress = max(0.0, self.q_stress - dt / self.time_scale)
        self.warp = 1
        if self.phase == "descent" and not v.engine_on and v.y > 36_000 and self.steer_in == 0                 and abs(v.omega) < math.radians(1.0):
            self.warp = 6  # 空気のないところを惰性で飛んでいるあいだは早送り
        if self.phase == "descent" and land.site != "sea":
            # 着地予想点を少しずつ計算する(1 回の計算を何フレームかに分ける)
            if self.ghost is None:
                self.ghost = Ghost(v)
                self.ghost.t0 = v.t
            if self.ghost.run(max(1, round(dt * 3600))):  # 1 フレームに 60 ステップ
                x, t0 = self.ghost.x, self.ghost.t0
                rate = 0.0
                if self.pred_raw and 0 < t0 - self.pred_raw[1] < 3.0:
                    rate = (x - self.pred_raw[0]) / (t0 - self.pred_raw[1])
                self.pred_raw = (x, t0, rate)
                self.ghost = None
            if self.pred_raw:
                # 噴射中は予想点が速く動く。計算を始めてからの時間のぶん、同じ速さで動いたとみなす
                x, t0, rate = self.pred_raw
                self.pred_x = x + rate * (v.t - t0) if v.engine_on else x
        if not v.lifted_off or v.vy > 0:
            return False
        on_target = abs(v.x - self.ship_x) <= land.half_w
        surface = self.deck_y() if on_target else 0.0
        if v.y > surface:
            return False
        # 接地
        v.y = surface
        self.touch = {"vy": -v.vy, "vx": abs(v.vx), "tilt": abs(self.tilt_deg()),
                      "dist": abs(v.x - self.ship_x), "prop": v.prop / v.p.prop_mass}
        t = self.touch
        soft = t["vy"] <= land.vy_max and t["vx"] <= land.vx_max and t["tilt"] <= land.tilt_max
        if land.hop_alt and self.apex < land.hop_alt and soft:
            self.vehicle_lost = False
            return self.fail("高さ 100 m に届かないまま着地")
        if not on_target:
            if land.site == "ship":
                return self.fail("台船を外して海に落ちた")
            self.vehicle_lost = not soft
            return self.fail("パッドを外して着地")
        if t["vy"] > land.vy_max:
            return self.fail("降下が速すぎて、脚が折れた(硬着陸)")
        if t["vx"] > land.vx_max:
            return self.fail("横に流れたまま接地して転倒")
        if t["tilt"] > land.tilt_max:
            return self.fail("傾いたまま接地して転倒")
        v.vx = v.vy = v.omega = 0.0
        v.cutoff()
        v.throttle = 0.0
        self.result = "success"
        self.emit("good", "着水成功! 海面で静止した" if land.site == "sea" else "着陸成功!")
        return True

    def stop_distance(self, frac=1.0, delay=0.0):
        """いまの速さから、出力 frac で噴いて止まるまでに落ちる距離 [m]。止まれないなら None。

        空気抵抗と、燃料が減って軽くなるぶんも数える(真下へ落ちているものとして 0.2 秒刻みで積分)。
        delay: 点火してから推力が立ち上がるまでの秒数(そのあいだは落ち続ける)。
        """
        v, p = self.v, self.v.p
        thrust = v.full_thrust() * frac
        m = v.mass
        if thrust / m - G0 <= 0.3:
            return None
        mdot = thrust / (p.isp_sl * G0)
        ka = 0.5 * p.drag_cd * math.pi * (p.diameter / 2) ** 2 * v.drag_mult
        spd, y, d, dt, t = v.speed, v.y, 0.0, 0.2, 0.0
        for _ in range(400):
            rho = 1.225 * math.exp(-max(y, 0.0) / SCALE_H)
            on = t >= delay
            a = (thrust / m if on else 0.0) - G0 + ka * rho * spd * spd / m
            if on and spd <= a * dt:
                return d + spd * spd / (2 * a)
            d += spd * dt - a * dt * dt / 2
            y -= spd * dt
            spd -= a * dt
            t += dt
            if on:
                m = max(p.dry_mass, m - mdot * dt)
        return d

    def stop_throttle(self, h):
        """高さ h [m] でちょうど止まるのに必要な出力(自動操縦の検証用)。"""
        lo, hi = 0.3, 1.6
        for _ in range(7):
            mid = (lo + hi) / 2
            d = self.stop_distance(mid)
            if d is None or d > h:
                lo = mid
            else:
                hi = mid
        return hi

    def burn_cue(self):
        """着陸噴射を始める高さの目安 [m](いま全開で噴けば、少し余裕を残して止まれる高さ)。"""
        v = self.v
        if v.vy >= 0:
            return None
        d = self.stop_distance(1.0, v.p.throttle_lag + 0.2)
        if d is None:
            return None
        return d * 1.2 + self.deck_y()

    def _step_reentry(self, dt):
        v, e = self.v, self.m.entry
        self.warp = 1
        if self.phase == "deorbit":
            fpa = entry_angle(v.y, v.vx, v.vy, e.interface)
            if v.y <= e.interface:
                fpa = math.degrees(math.atan2(v.vy, abs(v.vx)))
                att = math.degrees(v.aoa_tail)
                self.entry_values = {"fpa": fpa, "att": att}
                if fpa > e.fpa_hi:
                    return self.fail("再突入角が浅すぎて、大気に弾かれた")
                if abs(att) > e.att_tol:
                    return self.fail("耐熱シールドが前を向いていなかった")
                self.phase = "entry"
                self.emit("info", "大気圏に突入。耐熱シールドで耐える")
            elif not v.engine_on and v.throttle < 0.05:
                if fpa is None and (v.prop <= 0 or v.ignitions_left <= 0 or v.t > 240):
                    return self.fail("減速が足りず、軌道から降りられない")
                if fpa is not None and self.steer_in == 0 and abs(v.omega) < math.radians(0.4)                         and v.y > e.interface + 1_500:
                    self.warp = 20
        elif self.phase == "entry":
            # 加熱は空気の濃さと速さで決まり、深い角度で入るほど強くなる(ウィンドウの深い端でほぼ限界)
            fpa = self.entry_values["fpa"]
            depth = (e.fpa_hi - fpa) / (e.fpa_hi - e.fpa_lo)  # 0: 浅い端 / 1: 深い端
            k = 0.7 + 0.3 * depth if depth <= 1.0 else 1.0 + (depth - 1.0) * 0.7
            if abs(v.aoa_tail) > math.radians(35):
                k *= 3.0  # シールドが前を向いていない
            flux = math.sqrt(v.density / 1.225) * (v.speed / 2200.0) ** 3 * 3_850.0 * k
            self.heat += (flux - self.heat) * min(1.0, dt / 2.0)
            self.peak_heat = max(self.peak_heat, self.heat)
            if self.heat >= 100.0:
                return self.fail("深く入りすぎて、加熱で燃え尽きた")
            if self.steer_in == 0:
                self.warp = 6 if v.y > 12_000 else 3 if v.y > e.chute_hi + 1_500 else 1
        if self.phase == "chute" and v.speed < 25:
            self.warp = 20
        if v.y <= 0.0:
            spd = v.speed
            self.touch = {"speed": spd}
            v.y = 0.0
            if self.phase != "chute" or spd > e.splash_max:
                return self.fail("着水が速すぎて、カプセルが壊れた")
            v.vx = v.vy = v.omega = 0.0
            self.result = "success"
            self.emit("good", "着水成功! カプセルを回収する")
            return True
        return False

    def fail(self, reason):
        self.result = "fail"
        self.fail_reason = reason
        self.emit("bad", reason)
        return True

    # ---- 表示用 ----
    def prompt(self):
        """いま押すべきキーの案内(なければ空文字)。"""
        v, m = self.v, self.m
        if self.result is not None:
            return ""
        if self.anomaly_left is not None:
            return "Z: カプセル切り離し"
        if m.sep and self.stage_no == 1 and v.upper and v.launched and not v.engine_on and not m.sep.auto \
                and self.phase == "s1":
            return "Z: 段分離" if v.throttle <= m.sep.tail else "推力が消えるのを待て"
        if m.kind == "orbit" and self.stage_no == 2:
            if self.in_orbit:
                return "Z: 放出"
            if not v.engine_on and v.ignitions_left > 0 and v.prop > 0 and self.warp == 1:
                return "SPACE: 点火"
        if m.kind == "ascent" and self.stage_no == 2 and not v.engine_on and v.ignitions_left > 0:
            return "SPACE: 2段目点火"
        if m.kind == "reentry" and self.phase == "entry":
            e = m.entry
            if v.y < e.chute_hi and v.speed <= e.chute_speed:
                return "Z: パラシュート"
        return ""

    def _guide_wp3(self):
        """WP1(成功)→ WP2(分離)→ WP3 と飛ぶ打ち上げ(Ch1-1)の案内。"""
        v, m = self.v, self.m
        if self.tumble_t is not None:
            return 4, 4, "推進剤が偏って姿勢の効きがピーキー! ←→ は小さく当てろ"
        if self.stage_no == 1:
            if self.wp_values is None:
                return 1, 4, trf("まっすぐ上へ。WP1(高度 {alt:.0f} km)を通過すれば成功", alt=m.waypoint.altitude / 1000)
            if v.engine_on:
                w = m.sep_windows
                return 2, 4, trf("WP2: 傾き ±{a:.0f}°・角速度 ±{r:.1f}°/s に整えて、SPACE でエンジン停止",
                                 a=w["ang"].hi, r=w["rate"].hi)
            return 2, 4, "推力が消えたら自動で分離する"
        if not v.engine_on and v.ignitions_left == v.p.ignitions:
            return 3, 4, "SPACE で2段目に点火"
        return 4, 4, trf("WP3: 高度 {alt:.0f} km へ", alt=m.wp3_alt / 1000)

    def guide(self):
        """いまやることの案内: (何番目, 全部でいくつ, 文)。案内がないステージでは None。"""
        v, m = self.v, self.m
        if self.result is not None:
            return None
        if m.kind == "ascent":
            if not m.sep:
                return None
            if m.wp3_alt:
                return self._guide_wp3()
            if self.stage_no == 1:
                return 1, 3, "まっすぐ上へ。1段目は燃え尽きると自動で分離する"
            if not v.engine_on and v.ignitions_left == v.p.ignitions:
                return 2, 3, "SPACE で2段目に点火"
            return 3, 3, trf("←→ で揺れを抑えながら、高度 {alt:.0f} km へ", alt=m.waypoint.altitude / 1000)
        if m.kind == "orbit":
            o = m.orbit
            n = 6 if o.ap_lo else 5
            if self.stage_no == 1:
                if v.engine_on or not v.launched:
                    return 1, n, "右へ少しずつ倒しながら上昇。迎角は小さく保つ"
                return 2, n, "推力が消えたら Z で1段目を分離"
            if self.in_orbit:
                return n, n, "向きと角速度をウィンドウに入れて、Z で放出"
            pe, ap = v.apsides()
            if pe < o.pe_lo:
                if ap < o.pe_lo + 5_000 and (v.engine_on or v.ignitions_left == v.p.ignitions):
                    return 3, n, trf("SPACE で点火。右へ倒し、遠地点が {ap:.0f} km を超えたら SPACE で停止",
                                     ap=o.pe_lo / 1000 + 15)
                return 4, n, trf("遠地点の手前で右 90°(水平)に向けて SPACE。近地点が {pe:.0f} km を超えたら停止",
                                 pe=o.pe_lo / 1000)
            if o.ap_lo and ap < o.ap_lo:
                return 5, n, trf("水平のままもう一度 SPACE。遠地点が {lo:.0f}〜{hi:.0f} km に入ったら停止",
                                 lo=o.ap_lo / 1000, hi=o.ap_hi / 1000)
            return n - 1, n, "遠地点が高すぎる。後ろ向きに噴いて下げる"
        if m.kind == "reentry":
            e = m.entry
            if self.phase == "deorbit":
                fpa = entry_angle(v.y, v.vx, v.vy, e.interface)
                if fpa is not None and fpa <= e.fpa_hi and not v.engine_on:
                    return 3, 4, "耐熱シールドを前に向けたまま、突入を待つ"
                if abs(v.aoa_tail) > math.radians(15) and not v.engine_on:
                    return 1, 4, "←→ で機体を後ろ向き(進む向きと逆)に回して、止める"
                return 2, 4, "SPACE で噴射。再突入角がウィンドウに入ったら SPACE で停止"
            if self.phase == "entry":
                return 4, 4, "開傘の高度と速度が緑になったら Z でパラシュート"
            return 4, 4, "パラシュートで降下中。着水を待つ"
        land = m.land
        if m.kind == "hop":
            if v.engine_on and self.apex < 3:
                return 1, 3, "SPACE で離陸。右へ少し傾けて、隣のパッドへ向かう"
            if v.engine_on and v.vy > 0 and v.y + v.vy ** 2 / (2 * G0) < land.hop_alt + 5 and self.apex < land.hop_alt:
                return 1, 3, "SPACE で離陸。右へ少し傾けて、隣のパッドへ向かう"
            if v.engine_on and v.vy > 0:
                return 2, 3, trf("{alt:.0f} m に届く勢いが付いた。SPACE でエンジンを止める", alt=land.hop_alt)
            if not v.launched:
                return 1, 3, "SPACE で離陸。右へ少し傾けて、隣のパッドへ向かう"
            return 3, 3, "「噴射の目安」の線まで落ちたら SPACE。出力を合わせて、そっと降りる"
        first = 3 if m.kind == "recover" else 0
        n = first + (3 if m.kind == "recover" else 2)
        if m.kind == "recover" and self.phase == "s1":
            if v.engine_on or not v.launched:
                sep = m.sep
                if v.y >= sep.alt_lo and v.speed >= sep.speed_lo:
                    return 2, n, "分離の条件が緑になった。SPACE で停止して、戻る燃料を残す"
                return 1, n, "右へ少し倒しながら上昇。迎角は小さく保つ"
            return 3, n, "推力が消えたら Z で分離"
        if m.kind == "recover" and (v.vy > 0 or v.y > 36_000) and not v.engine_on:
            if land.site == "pad" and (self.pred_x is None or self.pred_x > self.ship_x + 2_000):
                return 4, n, "動圧が下がったら左へ向け、SPACE で戻りの噴射。着地予想が 0 に近づいたら停止"
            return 4, n, "エンジンを進む向きへ回す(迎角を 0 に)。宇宙では早送りになる"
        if m.kind == "recover" and v.engine_on and v.vy > 0:
            return 4, n, "着地予想が 0 に近づいたら SPACE で停止"
        if v.y > self.LANDING_ALT:
            return n - 1, n, trf("動圧が上がってきたら SPACE で再突入噴射。{v:.0f} m/s まで減速", v=ENTRY_SPEED)
        return n, n, "「噴射の目安」の線まで落ちたら SPACE。出力を合わせて、そっと降りる"

    def window_status(self):
        """現在値が各ウィンドウに入っているか(HUD 表示用)。"""
        cur = self._wp_now()
        return {k: (cur[k], w.ok(cur[k])) for k, w in self.m.waypoint.windows.items()}

    def hud_targets(self):
        """計器パネルの値の横に出す目標(WP): {"t" / "vy" / "vx" / "ang" / "rate": (下限, 上限)}。
        打ち上げのミッションはウェイポイントのウィンドウ(通過するまで)、軌道のミッションは次の目安の時刻の速さ。"""
        m = self.m
        if m.kind == "ascent" and self.wp_values is None:
            return {k: (w.lo, w.hi) for k, w in m.waypoint.windows.items()}
        if m.kind == "ascent" and m.sep_windows and self.stage_no == 1:  # WP2(分離)の窓
            return {k: (w.lo, w.hi) for k, w in m.sep_windows.items()}
        if m.kind == "ascent" and m.wp3_alt:  # WP3: 2段目で目指す高さ
            return {"alt": (m.wp3_alt, math.inf)}
        nxt = next((g for g in m.guide if g.t not in self.guide_values), None)
        if nxt is None or self.released is not None:
            return {}
        return {"t": (0, nxt.t), "vy": (nxt.vy_lo, nxt.vy_hi), "vx": (nxt.vx_lo, nxt.vx_hi)}

    def rows(self):
        """計器パネルの下のウィンドウに出す行: (ラベル, 範囲, 現在値, ウィンドウに入っているか)。"""
        v, m = self.v, self.m
        if m.kind == "ascent":
            wp = m.waypoint
            if self.wp_values is not None and m.wp3_alt:
                return []  # WP1 を通過したあとは、次の WP の値(hud_targets)を出す
            status = self.window_status() if self.wp_values is None else \
                {k: (self.wp_values[k], w.ok(self.wp_values[k])) for k, w in wp.windows.items()}
            return [(w.label, f"{w.lo:+.0f}~{w.hi:+.0f}", f"{status[k][0]:+.0f}", status[k][1])
                    for k, w in wp.windows.items()]
        if m.kind == "orbit" or (m.kind == "recover" and self.phase == "s1"):
            if self.stage_no == 1:
                sep = m.sep
                rows = []
                if sep.alt_lo:
                    rows.append(("分離高度", f"{sep.alt_lo / 1000:.0f}km~", f"{v.y / 1000:.1f}", v.y >= sep.alt_lo))
                    rows.append(("分離速度", f"{sep.speed_lo:.0f}~", f"{v.speed:.0f}", v.speed >= sep.speed_lo))
                rows.append(("残り推力", f"~{sep.tail * 100:.0f}%", f"{v.throttle * 100:.0f}%",
                             not v.engine_on and v.throttle <= sep.tail))
                rate = math.degrees(v.omega)
                rows.append(("角速度", f"±{sep.rate_max:.0f}", f"{rate:+.1f}", abs(rate) <= sep.rate_max))
                if m.kind == "recover":
                    rows.append(("推進剤", "", f"{v.prop / v.p.prop_mass * 100:.0f}%", True))
                return rows
            o = m.orbit
            if self.released:
                pe, ap = self.released["pe"], self.released["ap"]
            else:
                pe, ap = v.apsides()
            att = math.degrees(v.theta) - 90.0
            rate = math.degrees(v.omega)
            ap_txt = "---" if ap == math.inf else f"{ap / 1000:.0f}"
            ap_rng = f"{o.ap_lo / 1000:.0f}~{o.ap_hi / 1000:.0f}" if o.ap_lo else f"~{o.ap_hi / 1000:.0f}"
            rows = [
                ("近地点", f"{o.pe_lo / 1000:.0f}km~", f"{max(pe, -999_000) / 1000:.0f}", pe >= o.pe_lo),
                ("遠地点", ap_rng, ap_txt, o.ap_lo <= ap <= o.ap_hi),
                ("向き", f"±{o.att_tol:.0f}", f"{att:+.0f}", abs(att) <= o.att_tol),
                ("角速度", f"±{o.rate_tol:g}", f"{rate:+.1f}", abs(rate) <= o.rate_tol),
            ]
            if self.in_orbit:
                left = o.release_time - self.release_timer
                rows.append(("放出まで", "", f"{max(0.0, left):.0f} s", left > 5))
            else:
                tta = time_to_apoapsis(v.y, v.vx, v.vy)
                rows.append(("遠地点まで", "", "---" if tta is None else f"{tta:.0f} s", True))
            return rows
        if m.kind == "reentry":
            e = m.entry
            if self.phase == "deorbit":
                fpa = entry_angle(v.y, v.vx, v.vy, e.interface)
                att = math.degrees(v.aoa_tail)
                return [
                    ("再突入角", f"{e.fpa_lo:.1f}~{e.fpa_hi:.1f}", "---" if fpa is None else f"{fpa:+.1f}",
                     fpa is not None and e.fpa_lo <= fpa <= e.fpa_hi),
                    ("シールド", f"±{e.att_tol:.0f}", f"{att:+.0f}", abs(att) <= e.att_tol),
                    ("突入まで", "", f"{max(0.0, v.y - e.interface) / 1000:.0f} km", True),
                ]
            return [
                ("温度", "~100", f"{self.heat:.0f}", self.heat < 80),
                ("開傘高度", f"{e.chute_lo / 1000:.0f}~{e.chute_hi / 1000:.0f}km", f"{v.y / 1000:.1f}",
                 e.chute_lo <= v.y <= e.chute_hi),
                ("開傘速度", f"~{e.chute_speed:.0f}", f"{v.speed:.0f}", v.speed <= e.chute_speed),
                ("着水速度", f"~{e.splash_max:.0f}", f"{v.speed:.0f}", v.speed <= e.splash_max),
            ]
        # 着陸
        land = m.land
        t = self.touch
        if self.phase == "descent" and v.y > self.LANDING_ALT and not t:
            # 高いところ: 再突入噴射の判断に使う値
            q = v.q
            rows = [
                ("動圧", f"~{land.q_limit / 1000:.0f}kPa", f"{q / 1000:.1f}", q <= land.q_limit * 0.75),
                ("速度", f"~{ENTRY_SPEED:.0f}", f"{v.speed:.0f}", v.speed <= ENTRY_SPEED),
            ]
            if land.site != "sea":
                miss = None if self.pred_x is None else self.pred_x - self.ship_x
                rows.append(("着地予想", f"±{land.half_w:.0f}m", "---" if miss is None else f"{miss:+.0f}",
                             miss is not None and abs(miss) <= land.half_w))
            rows.append(("推進剤", "", f"{v.prop / v.p.prop_mass * 100:.0f}%", v.prop > 2_500))
            return rows
        vy = t["vy"] if t else -v.vy
        vxs = t["vx"] if t else abs(v.vx)
        tilt = t["tilt"] if t else abs(self.tilt_deg())
        rows = [
            ("降下速度", f"~{land.vy_max:.0f}", f"{vy:.1f}", vy <= land.vy_max),
            ("横速度", f"~{land.vx_max:.0f}", f"{vxs:.1f}", vxs <= land.vx_max),
            ("傾き", f"~{land.tilt_max:.0f}", f"{tilt:.1f}", tilt <= land.tilt_max),
        ]
        if land.site != "sea":
            d = v.x - self.ship_x
            rows.append(("目標まで", f"±{land.half_w:.0f}m", f"{-d:+.0f}", abs(d) <= land.half_w))
        if land.hop_alt:
            rows.append(("最高高度", f"{land.hop_alt:.0f}m~", f"{self.apex:.0f}", self.apex >= land.hop_alt))
        else:
            cue = self.burn_cue()
            if cue is not None and not v.engine_on and not t:
                rows.append(("噴射の目安", "", f"{cue:.0f} m", v.y - cue > 0))
        return rows

    def report(self):
        """リザルト画面の表: (ラベル, 目標, 実際の値, 達成したか)。達成の数でランクが決まる。"""
        m = self.m
        rows = []
        if m.kind == "ascent":
            for key, w in m.waypoint.windows.items():
                if self.wp_values:
                    val = self.wp_values[key]
                    rows.append((w.label, f"{w.lo:+.0f} ~ {w.hi:+.0f} {w.unit}",
                                 f"{val:+.1f}", w.ok(val)))
                else:
                    rows.append((w.label, f"{w.lo:+.0f} ~ {w.hi:+.0f} {w.unit}",
                                 "---", None))
        elif m.kind == "orbit":
            o, r = m.orbit, self.released
            ap_t = trf("{lo:.0f} ~ {hi:.0f} km", lo=o.ap_lo / 1000, hi=o.ap_hi / 1000) if o.ap_lo else \
                trf("{hi:.0f} km 以下", hi=o.ap_hi / 1000)
            rows = [
                ("近地点", trf("{lo:.0f} km 以上", lo=o.pe_lo / 1000), f"{r['pe'] / 1000:.0f} km" if r else "---",
                 r and r["pe"] >= o.pe_lo),
                ("遠地点", ap_t, (f"{r['ap'] / 1000:.0f} km" if r["ap"] != math.inf else "∞") if r else "---",
                 r and o.ap_lo <= r["ap"] <= o.ap_hi),
                ("放出の向き", trf("±{tol:.0f}°", tol=o.att_tol / 2), f"{r['att']:+.1f}°" if r else "---",
                 r and abs(r["att"]) <= o.att_tol / 2),
                ("残り推進剤", trf("{p:.0f}% 以上", p=o.prop_bonus * 100), f"{r['prop'] * 100:.0f}%" if r else "---",
                 r and r["prop"] >= o.prop_bonus),
                ("放出時刻", trf("T+{t:.0f} s まで", t=o.time_bonus), f"T+{r['t']:.0f} s" if r else "---",
                 r and r["t"] <= o.time_bonus),
            ]
        elif m.kind == "reentry":
            e, ev, cv, t = m.entry, self.entry_values, self.chute_values, self.touch
            mid = (e.fpa_lo + e.fpa_hi) / 2
            rows = [
                ("再突入角", trf("{lo:.1f} ~ {hi:.1f}°", lo=mid - 0.6, hi=mid + 0.6), f"{ev['fpa']:+.1f}°" if ev else "---",
                 ev and abs(ev["fpa"] - mid) <= 0.6),
                ("突入の向き", trf("±{tol:.0f}°", tol=e.att_tol / 2), f"{ev['att']:+.1f}°" if ev else "---",
                 ev and abs(ev["att"]) <= e.att_tol / 2),
                ("開傘高度", trf("{lo:.0f} ~ {hi:.0f} km", lo=e.chute_lo / 1000, hi=e.chute_hi / 1000),
                 f"{cv['alt'] / 1000:.1f} km" if cv else "---", cv and e.chute_lo <= cv["alt"] <= e.chute_hi),
                ("着水速度", trf("{v:.0f} m/s 以下", v=e.splash_max), f"{t['speed']:.1f} m/s" if t else "---",
                 t and t["speed"] <= e.splash_max),
            ]
        else:
            land, t = m.land, self.touch
            if m.kind == "recover":
                s, sv = m.sep, self.sep_values
                rows.append(("分離速度", trf("{v:.0f} m/s 以上", v=s.speed_lo), f"{sv['speed']:.0f} m/s" if sv else "---",
                             sv and sv["speed"] >= s.speed_lo))
            rows += [
                ("降下速度", trf("{v:.0f} m/s 以下", v=land.vy_good), f"{t['vy']:.1f} m/s" if t else "---",
                 t and t["vy"] <= land.vy_good),
                ("横速度", trf("{v:.0f} m/s 以下", v=land.vx_max / 2), f"{t['vx']:.1f} m/s" if t else "---",
                 t and t["vx"] <= land.vx_max / 2),
                ("傾き", trf("{a:.0f}° 以下", a=land.tilt_max / 2), f"{t['tilt']:.1f}°" if t else "---",
                 t and t["tilt"] <= land.tilt_max / 2),
            ]
            if land.site != "sea":
                rows.append(("ずれ", trf("{d:.0f} m 以内", d=land.dist_good), f"{t['dist']:.1f} m" if t else "---",
                             t and t["dist"] <= land.dist_good))
        return [(a, b, c, None if d is None else bool(d)) for a, b, c, d in rows]

    def report_head(self):
        """リザルト画面の表の見出し。"""
        m = self.m
        if m.kind == "ascent":
            wp = m.waypoint
            return trf("{name}(高度 {alt:.0f} km 通過時)", name=wp.name, alt=wp.altitude / 1000)
        return {"orbit": "軌道投入の記録", "reentry": "再突入の記録", "dock": "接近の記録"}.get(m.kind, "着陸の記録")

    def rank(self):
        if self.result != "success":
            return "-"
        rows = self.report()
        miss = sum(1 for r in rows if not r[3])
        return {0: "S", 1: "A", 2: "B"}.get(miss, "C")

    def progress(self):
        """どこまで進んだか(0〜1)。失敗したときのテレメトリに使う。"""
        m, v = self.m, self.v
        if m.kind == "ascent":
            return min(1.0, self.max_alt / m.waypoint.altitude)
        if m.kind == "orbit":
            if self.stage_no == 1:
                return min(0.4, self.max_alt / 100_000)
            return 0.5 + 0.5 * min(1.0, max(0.0, v.vx / 2200.0))
        if m.kind == "reentry":
            return {"deorbit": 0.2, "entry": 0.6, "chute": 0.9}[self.phase]
        if m.kind == "recover" and self.phase == "s1":
            return min(0.4, self.max_alt / 100_000)
        if m.kind == "hop":
            return min(1.0, self.apex / m.land.hop_alt)
        return 0.5 + 0.5 * min(1.0, max(0.0, 1.0 - v.y / 30_000))

    def telemetry(self):
        if self.result == "success":
            return self.m.tlm_success
        # 失敗しても、進んだところまでのデータが取れる
        return int(10 + (self.m.tlm_success - 10) * 0.75 * self.progress())


class Ghost:
    """1段目の着地予想点を、標準的な手順(再突入噴射 → 着陸噴射)で先回りして計算する。

    1 回の計算は数百ステップかかるので、run() を呼ぶたびに少しずつ進める。
    """

    def __init__(self, vehicle):
        v = self.v = copy.copy(vehicle)
        v.rng = copy.copy(vehicle.rng)
        v.upper = []
        v.payload = 0.0
        v.wind = 0.0
        v.torque_bias = 0.0
        # いま噴いているなら、その噴射が何のためかを引き継ぐ。stage 0: 再突入噴射の前 / 1: 噴射中 / 2: 惰性 / 3: 着陸噴射
        if v.engine_on:
            self.stage = 3 if v.engine_frac < 0.2 else 1 if v.vy < 0 else 0
        else:
            self.stage = 2 if v.vy < 0 and v.y < 20_000 and v.speed <= ENTRY_SPEED * 1.2 else 0
        self.x = None

    def run(self, steps):
        """steps だけ進める。着地まで計算し終えたら True。"""
        v = self.v
        for _ in range(steps):
            if v.speed > 1 and (self.stage or v.throttle < 0.01):
                v.theta = math.atan2(-v.vx, -v.vy)  # エンジンを進む向きに(分離直後は推力が消えてから)
            v.omega = v.gust = 0.0
            if v.vy < 0:
                if self.stage == 0 and (v.q > ENTRY_Q or v.y < 12_000):
                    self.stage = 1 if v.speed > ENTRY_SPEED else 2
                elif self.stage == 1 and v.speed < ENTRY_SPEED:
                    self.stage = 2
                elif self.stage == 2 and v.y < MissionRun.LANDING_ALT:
                    v.engine_frac = MissionRun.LANDING_ENGINES
                    a = v.full_thrust() * 0.9 / v.mass - G0 * 0.4  # 空気抵抗のぶんを少し足しておく
                    if a > 0.5 and v.y <= v.speed ** 2 / (2 * a):
                        self.stage = 3
            v.engine_on = self.stage in (1, 3) and v.prop > 0
            v.throttle_cmd = 1.0 if self.stage == 1 else 0.85
            # 空気のないところを惰性で飛んでいるあいだは、粗い刻みで進める
            v.step(0.5 if v.y > 45_000 and not v.engine_on and v.throttle < 0.01 else 0.1, 0, 0)
            if v.y <= 0 or (self.stage == 3 and v.speed < 3) or v.t > 3_000:
                self.x = v.x
                return True
        return False


def predict_touchdown(vehicle):
    """分離した1段目が、標準的な手順でまっすぐ降りたときの着地点の x [m]。"""
    g = Ghost(vehicle)
    for _ in range(100):
        if g.run(200):
            break
    return g.v.x

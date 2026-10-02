"""機体の諸元(Pyxel に依存しない)。

惑星は地球と同じ大きさ。数値は元ネタの機体(Falcon 1 / Falcon 9 など)に近づけた値。
"""

import math
from dataclasses import dataclass, replace

from .physics import Vehicle, VehicleParams


@dataclass
class Rocket:
    """打ち上げるときの組み合わせ(下の段から順)。"""

    name: str
    stages: list
    payload: float = 0.0  # 荷物 [kg]
    cargo: str = "fairing"  # 先端の描き方: fairing / capsule / none

    def make(self):
        return Vehicle(self.stages[0], upper=list(self.stages[1:]), payload=self.payload)


# ---- Eagle 1(小型・使い捨て) ----
# Ch1-1 の機体(1段目だけで 10 km を目指す試験飛行)
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

# 2 段式の Eagle 1(元ネタ: Falcon 1)。1段目(エンジン Hobby)は 150 秒ほどで燃え尽き、
# 推力の小さい2段目(エンジン Lanner)が 6 分かけて軌道まで運ぶ
EAGLE1_S1 = VehicleParams(
    name="Eagle 1",
    dry_mass=1_450.0,
    prop_mass=21_500.0,
    thrust_sl=360_000.0,
    thrust_vac=410_000.0,
    isp_sl=255.0,
    isp_vac=304.0,
    length=14.0,
    diameter=1.7,
)
EAGLE1_S2 = VehicleParams(
    name="Eagle 1 S2",
    dry_mass=430.0,
    prop_mass=4_300.0,
    thrust_sl=31_000.0,
    thrust_vac=31_000.0,
    isp_sl=340.0,
    isp_vac=340.0,
    length=7.0,
    diameter=1.7,
    min_throttle=0.5,
    throttle_lag=0.5,
    cutoff_lag=0.3,
    gimbal_max=math.radians(1.0),
    inertia_factor=10.0,
    rcs_fuel=240.0,  # 2段目の燃焼は長い(画面の時間で 2 分以上)ので、姿勢を直し続けても足りる量
    ang_damping=0.12,
    aero_instability=0.3,
    ignitions=3,
    style="eagle1_s2",
)


def eagle1(payload, s2_scale=1.0):
    """s2_scale: 2段目の推進剤を何倍にするか。推力も同じ倍率にする(重くなっても、上へ押し上げる力が落ちないように)。"""
    s2 = EAGLE1_S2
    if s2_scale != 1.0:
        s2 = replace(s2, prop_mass=s2.prop_mass * s2_scale, thrust_sl=s2.thrust_sl * s2_scale,
                     thrust_vac=s2.thrust_vac * s2_scale)
    return Rocket("Eagle 1", [EAGLE1_S1, s2], payload)


# ---- Eagle 9(中型。9 基のエンジン Hobby) ----
EAGLE9_S1 = VehicleParams(
    name="Eagle 9",
    dry_mass=6_500.0,
    prop_mass=46_000.0,
    thrust_sl=1_250_000.0,
    thrust_vac=1_360_000.0,
    isp_sl=205.0,
    isp_vac=236.0,
    length=30.0,
    diameter=3.7,
    gimbal_max=math.radians(4.0),
    gimbal_lag=0.6,
    aero_instability=0.9,
    style="eagle9",
)
EAGLE9_S2 = VehicleParams(
    name="Eagle 9 S2",
    dry_mass=2_500.0,
    prop_mass=9_400.0,
    thrust_sl=330_000.0,
    thrust_vac=330_000.0,
    isp_sl=330.0,
    isp_vac=330.0,
    length=9.0,
    diameter=3.7,
    min_throttle=0.5,
    throttle_lag=0.5,
    cutoff_lag=0.3,
    gimbal_max=math.radians(1.0),
    inertia_factor=10.0,
    rcs_fuel=60.0,
    ang_damping=0.12,
    aero_instability=0.3,
    ignitions=4,
    style="eagle9_s2",
)
# 回収型の1段目: 着陸脚とグリッドフィンを付け、何度も点火できる。
# 戻るための燃料を残せるよう、タンクを伸ばしてエンジンの推力も上げてある
EAGLE9_S1R = VehicleParams(
    name="Eagle 9",
    dry_mass=7_500.0,
    prop_mass=56_000.0,
    thrust_sl=1_500_000.0,
    thrust_vac=1_635_000.0,
    isp_sl=215.0,
    isp_vac=247.0,
    length=30.0,
    diameter=3.7,
    throttle_lag=0.6,
    gimbal_max=math.radians(4.0),
    gimbal_lag=0.6,
    rcs_accel=math.radians(3.0),
    rcs_fuel=90.0,
    ang_damping=0.05,
    aero_instability=0.9,
    ignitions=5,
    drag_cd=0.8,
    fin_auth=math.radians(5.0),
    style="eagle9r",
)


def eagle9(payload, cargo="fairing", recover=False):
    return Rocket("Eagle 9", [EAGLE9_S1R if recover else EAGLE9_S1, EAGLE9_S2], payload, cargo)


# ---- 貨物カプセル Phoenix(スラスター Ember で軌道を離れ、耐熱シールドを前にして再突入する) ----
PHOENIX = VehicleParams(
    name="Phoenix",
    dry_mass=4_200.0,
    prop_mass=600.0,
    thrust_sl=16_000.0,
    thrust_vac=16_000.0,
    isp_sl=300.0,
    isp_vac=300.0,
    length=5.0,
    diameter=3.7,
    min_throttle=1.0,
    throttle_lag=0.2,
    cutoff_lag=0.15,
    gimbal_max=0.0,
    inertia_factor=3.0,
    rcs_accel=math.radians(2.5),
    rcs_fuel=90.0,
    ang_damping=0.02,
    aero_instability=1.2,
    ignitions=5,
    drag_cd=1.3,
    style="phoenix",
)

# ---- 着陸試験機 Hopper ----
HOPPER = VehicleParams(
    name="Hopper",
    dry_mass=4_000.0,
    prop_mass=4_000.0,
    thrust_sl=120_000.0,
    thrust_vac=120_000.0,
    isp_sl=255.0,
    isp_vac=255.0,
    length=18.0,
    diameter=3.7,
    throttle_rate=0.8,
    throttle_lag=0.4,
    cutoff_lag=0.3,
    gimbal_max=math.radians(5.0),
    gimbal_lag=0.4,
    rcs_accel=math.radians(3.0),
    rcs_fuel=90.0,
    ang_damping=0.15,
    aero_instability=0.0,
    ignitions=5,
    drag_cd=0.8,
    style="hopper",
)

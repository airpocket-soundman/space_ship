"""Ch1-1 の物理とバランスをヘッドレスで確認する。

python tools/sim_check.py
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from game.missions import CH1_1, MissionRun  # noqa: E402

DT = 1 / 60


def run(policy, inspected=False, seed=0):
    run = MissionRun(CH1_1, inspected=inspected, seed=seed)
    run.v.ignite()
    steps = 0
    while run.result is None and steps < 60 * 200:
        steer, thr = policy(run)
        run.step(DT, steer, thr)
        steps += 1
    return run


def no_input(run):
    return 0, 0


def pilot(run, react=0.4):
    """人間っぽい操縦: 角度と角速度を見て左右キーを押し、火災なら出力を絞る。"""
    v = run.v
    err = v.theta + 1.2 * v.omega
    steer = 0
    if err > math.radians(0.8):
        steer = -1
    elif err < -math.radians(0.8):
        steer = 1
    thr = 0
    if run.fire_active and v.t - run.fire_at > react:
        thr = -1
    elif not run.fire_active and v.throttle_cmd < 1.0:
        thr = 1
    return steer, thr


def summary(name, runs):
    ok = [r for r in runs if r.result == "success"]
    print(f"{name}: success {len(ok)}/{len(runs)}")
    reasons = {}
    for r in runs:
        if r.result != "success":
            reasons[r.fail_reason] = reasons.get(r.fail_reason, 0) + 1
    if reasons:
        print("   fail:", reasons)
    for r in ok[:3]:
        print("   ", {k: round(v, 1) for k, v in r.wp_values.items()}, "rank", r.rank(),
              "maxQ", round(r.max_q), "fire", r.fire_at is not None)


if __name__ == "__main__":
    summary("no input", [run(no_input, seed=s) for s in range(20)])
    summary("pilot (react 0.4s)", [run(pilot, seed=s) for s in range(20)])
    summary("pilot (react 1.5s)", [run(lambda r: pilot(r, 1.5), seed=s) for s in range(20)])
    summary("pilot slow (react 3.0s)", [run(lambda r: pilot(r, 3.0), seed=s) for s in range(20)])
    summary("pilot inspected", [run(pilot, inspected=True, seed=s) for s in range(20)])

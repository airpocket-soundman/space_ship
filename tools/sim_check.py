"""全ステージの物理とバランスをヘッドレスで確認する。

python tools/sim_check.py            全ステージを自動操縦で 20 回ずつ飛ばす
python tools/sim_check.py 1-3 3-3    指定したステージだけ
python tools/sim_check.py 1-1 -v     Ch1-1 を操縦の上手さを変えて詳しく見る

自動操縦は「人が画面の数値を見てやる手順」をなぞったもの。雑な操縦(sloppy)でも
それなりに成功し、何もしなければ失敗する、という釣り合いを確かめるのに使う。
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from game.docking import DockRun  # noqa: E402
from game.missions import ENTRY_Q, ENTRY_SPEED, MISSIONS, ORDER, MissionRun, entry_angle  # noqa: E402
from game.physics import G0, time_to_apoapsis  # noqa: E402

DT = 1 / 120


def steer_to(v, target, deadband=0.8, lead=1.2):
    """目標の傾きへ向けて ←→ を押す(角度と角速度を見て、行き過ぎないように)。"""
    err = (v.theta - target + math.pi) % math.tau - math.pi + lead * v.omega
    if err > math.radians(deadband):
        return -1
    if err < -math.radians(deadband):
        return 1
    return 0


class Pilot:
    """1 フレームごとに (steer, thr) を返し、必要なら run.space() / run.z() を押す。"""

    def __init__(self, run, sloppy=0.0):
        self.run = run
        self.sloppy = sloppy  # 反応の遅れ [s]
        self.state = "start"
        self.mark = None

    def late(self, key, cond):
        """cond が成り立ってから sloppy 秒たったら True(人の反応の遅れ)。"""
        t = self.run.v.t
        marks = self.__dict__.setdefault("marks", {})
        if not cond:
            marks.pop(key, None)
            return False
        t0 = marks.setdefault(key, t)
        return t - t0 >= self.sloppy * self.run.time_scale  # 反応の遅れは画面の時間

    def thr_for_fire(self):
        run, v = self.run, self.run.v
        if run.fire_active and v.t - run.fire_at > (0.4 + self.sloppy) * run.time_scale:
            return -1
        if not run.fire_active and v.throttle_cmd < 1.0:
            return 1
        return 0


class AscentPilot(Pilot):
    """まっすぐ上がる(Ch1-1, 1-2)。"""

    def __call__(self):
        run, v = self.run, self.run.v
        if not v.launched:
            run.space()
        # WP1 のあとの分離(WP2): 姿勢が窓に入っていれば、エンジンを止める
        w = run.m.sep_windows
        if w and run.stage_no == 1 and run.wp_values is not None and v.engine_on:
            now = run._wp_now()
            if self.late("cut", all(win.ok(now[k]) for k, win in w.items())):
                run.space()
        if run.stage_no == 2 and not v.engine_on and v.ignitions_left == v.p.ignitions:
            if self.late("s2", True):
                run.space()
        db = 0.8 + 2.0 * self.sloppy
        return steer_to(v, 0.0, db), self.thr_for_fire()


class OrbitPilot(Pilot):
    """重力ターン → 分離 → 遠地点を目標の高さに保って噴く →(高い軌道は惰性で遠地点へ → 円にする)→ 放出。"""

    COAST_PE = 160_000.0  # 惰性飛行に入ってよい近地点(大気の上)

    def __init__(self, run, sloppy=0.0, tilt=45.0, p1=85.0, alt_scale=60_000.0):
        super().__init__(run, sloppy)
        self.tilt, self.p1, self.alt_scale = tilt, p1, alt_scale
        o = run.m.orbit
        self.park_ap = (o.pe_lo + min(o.ap_hi, o.pe_lo + 60_000)) / 2 if not o.ap_lo else 130_000.0
        self.park_pe = (o.pe_lo + 4_000) if not o.ap_lo else 90_000.0

    def s1_target(self):
        v = self.run.v
        des = math.radians(self.tilt) * min(1.0, max(0.0, (v.y - 800) / self.alt_scale)) ** 0.6
        if v.speed > 60 and v.q > 8_000:
            va = math.atan2(v.vx, v.vy)
            lim = math.radians(7)
            return min(max(des, va - lim), va + lim)
        return des

    def __call__(self):
        run, v, o = self.run, self.run.v, self.run.m.orbit
        if not v.launched:
            run.space()
        thr = self.thr_for_fire()
        if run.stage_no == 1:
            if run.anomaly_left is not None and self.late("abort", True):
                run.z()
            if not v.engine_on and v.launched and self.late("sep", v.throttle <= run.m.sep.tail):
                run.z()
            steer = steer_to(v, self.s1_target())
            if run.engine_out:
                steer = steer_to(v, self.s1_target(), 0.4)
            return steer, thr
        pe, ap = v.apsides()
        horiz = math.pi / 2
        if self.state == "start":
            if self.late("s2", True):
                run.space()
                self.state = "hold"
            return steer_to(v, math.radians(self.p1)), 1
        if self.state == "hold":
            # 2段目は推力が小さいので止めずに噴く。遠地点を目標の高さに保ちながらほぼ水平に噴き、近地点を上げる
            # (遠地点が低ければ機首を少し上げ、高すぎれば少し下げる)
            high = (o.pe_lo + o.ap_hi) / 2 > 400_000 and not o.ap_lo
            # 低い軌道は近地点の少し上、高い軌道は目標の幅の中ほど(噴いているあいだに伸びるぶん低め)を狙う
            target_ap = max((o.pe_lo + o.ap_hi) / 2 - 70_000, self.park_pe + 25_000) if high else self.park_pe + 20_000
            s = max(-0.5, min(0.6, (target_ap - ap) / 30_000))
            if self.late("cut2", pe >= self.park_pe):
                run.space()
                self.state = "gto" if o.ap_lo else "release"
            elif high and self.late("cut1", pe >= self.COAST_PE and ap >= target_ap - 15_000):
                # 高い軌道: 近地点が大気の上に出たら止め、遠地点まで惰性で上がって、そこで円にする
                run.space()
                self.state = "coast"
            return steer_to(v, horiz - math.asin(s)), (-1 if pe > self.park_pe - 60_000 else 1)
        if self.state == "coast":
            tta = time_to_apoapsis(v.y, v.vx, v.vy)
            aligned = abs(v.theta - horiz) < math.radians(6) and abs(v.omega) < math.radians(1)
            if tta is None or tta < 30 + self.sloppy * 3:
                run.space()
                self.state = "circ"
            return (0 if aligned else steer_to(v, horiz)), 0
        if self.state == "circ":
            # 遠地点で水平に噴き、近地点を目標まで上げる(落ち始めたら機首を少し上げる)
            s = max(-0.35, min(0.35, -v.vy / 120))
            if self.late("cut2", pe >= self.park_pe):
                run.space()
                self.state = "gto" if o.ap_lo else "release"
            return steer_to(v, horiz - math.asin(s)), (-1 if pe > self.park_pe - 60_000 else 1)
        if self.state == "gto":
            if not v.engine_on:
                if abs(v.theta - horiz) < math.radians(4) and self.late("gto", True):
                    run.space()
                return steer_to(v, horiz), 0
            target = (o.ap_lo + o.ap_hi) / 2
            if ap >= target - 60_000 * (1 + self.sloppy):
                run.space()
                self.state = "release"
            return steer_to(v, horiz), (-1 if ap > o.ap_lo * 0.6 else 1)
        # 放出: 水平に向けて回転を止める
        steer = steer_to(v, horiz, 0.5, 2.0)
        att = abs(math.degrees(v.theta) - 90)
        rate = abs(math.degrees(v.omega))
        if run.in_orbit and att <= o.att_tol * 0.5 and rate <= o.rate_tol * 0.6 and self.late("rel", True):
            run.z()
        return steer, 0


class LandingPilot(Pilot):
    """再突入噴射 → 着陸噴射(ホバースラム)。"""

    def __init__(self, run, sloppy=0.0):
        super().__init__(run, sloppy)
        self.entry_done = False

    def slam(self, dx, hop=False):
        """着陸噴射: 地表の少し上で止まるように出力を合わせ、横のずれを推力の向きで直す。"""
        run, v, land = self.run, self.run.v, self.run.m.land
        h = max(0.0, v.y - run.deck_y())
        a_full = v.full_thrust() / v.mass
        want = run.stop_throttle(h + 0.3) if v.vy < 0 else 0.0  # 地表のわずか下で止まるつもりで、そっと触れる
        thr = 1 if want > v.throttle_cmd + 0.02 else -1 if want < v.throttle_cmd - 0.02 else 0
        if v.vy > 1.0:
            run.space()  # 止まって浮き始めた。エンジンを切って落ち、もう一度噴く
        # 横のずれ: 着地までの残り時間で、目標の真上に横速度 0 で着くように推力を傾ける
        tgo = max(1.5, 2.0 * h / max(-v.vy, 1.0))
        lim = 0.2
        if land.site == "sea":
            ax = -v.vx / max(tgo * 0.5, 1.0)
        elif tgo > 3.0:
            ax = 6.0 * dx / (tgo * tgo) - 4.0 * v.vx / tgo
        else:  # 最後はまっすぐ立てて、横速度だけ消す
            ax = -v.vx / 0.8
            lim = 0.12
        if hop:  # 噴いている時間が短いので、位置と速度をまとめて直す
            ax = (0.12 * dx if h > 6 else 0.0) - 0.7 * v.vx
            lim = 0.25
        if want > 0.97:  # 止まるのに出力が足りなくなりそうなら、横のずれより減速を優先する
            lim = 0.06
        tilt = max(-lim, min(lim, ax / max(a_full * max(v.throttle, 0.3), 1.0)))
        return steer_to(v, tilt, 0.6), thr

    def slam_now(self):
        """着陸噴射を始めるときか(画面に出る「噴射の目安」の高さまで落ちたら点火する)。"""
        run, v = self.run, self.run.v
        cue = run.burn_cue()
        return cue is not None and v.y <= cue - v.speed * self.sloppy * 0.3

    def descend(self):
        run, v, land = self.run, self.run.v, self.run.m.land
        retro = math.atan2(-v.vx, -v.vy) if v.speed > 8 else 0.0
        dx = run.ship_x - v.x if land.site != "sea" else 0.0
        if v.engine_on:
            if not self.entry_done:
                # 再突入噴射: 着地予想点が目標に寄るように、推力を少し傾ける
                miss = run.ship_x - run.pred_x if land.site != "sea" and run.pred_x is not None else 0.0
                tilt = max(-0.2, min(0.2, 0.0006 * miss))
                # 予想点がまだ大きく外れているなら、燃料の許すかぎり噴き続けて寄せる
                more = abs(miss) > 80 and v.speed > 220 and v.prop > 3_200
                if v.speed < ENTRY_SPEED and not more:
                    run.space()
                    self.entry_done = True
                return steer_to(v, retro + tilt, 1.0), 1
            return self.slam(dx)
        # 惰性で降下中
        if v.vy < 0:
            if not self.entry_done and v.q > ENTRY_Q and v.speed > ENTRY_SPEED:
                if self.late("entry", True):
                    run.space()
            elif not self.entry_done and v.y < 12_000:
                self.entry_done = True
            if self.entry_done and v.ignitions_left > 0 and self.slam_now():
                run.space()
        return steer_to(v, retro, 1.5), 0

    def __call__(self):
        return self.descend()


class HopPilot(LandingPilot):
    """Hopper: 上がりながら横へ寄せ、エンジンを切って惰性で越え、落ちてきたところを噴いて止める。"""

    def __call__(self):
        run, v, land = self.run, self.run.v, self.run.m.land
        if not v.launched:
            run.space()
        dx = land.x - v.x
        a_full = v.full_thrust() / v.mass
        if self.state == "start":
            # 着地までの残り時間で目標に着く横速度を作る
            ax = 0.9 * (dx / 13.0 - v.vx)
            tilt = max(-0.2, min(0.2, ax / max(a_full * max(v.throttle, 0.3), 1.0)))
            if v.vy > 0 and v.y + v.vy * v.vy / (2 * G0) > land.hop_alt + 12:
                run.space()
                self.state = "coast"
            return steer_to(v, tilt, 0.6), 1
        if self.state == "coast":
            if run.apex >= land.hop_alt and self.slam_now():
                run.space()
                self.state = "land"
            return steer_to(v, 0.0, 0.6), 0
        if not v.engine_on:
            if v.ignitions_left > 0 and self.slam_now():
                run.space()
            return steer_to(v, 0.0, 0.6), 0
        return self.slam(dx, hop=True)


class RecoverPilot(LandingPilot):
    """打ち上げ → 早めにエンジンを止めて分離 →(発射場に戻るなら戻りの噴射)→ 着陸。"""

    def __init__(self, run, sloppy=0.0, tilt=50.0, keep=0.08, rtls=False):
        super().__init__(run, sloppy)
        self.tilt, self.keep, self.rtls = tilt, keep, rtls
        self.back_done = not rtls

    def __call__(self):
        run, v = self.run, self.run.v
        if not v.launched:
            run.space()
        if run.phase == "s1":
            if v.engine_on:
                sep = run.m.sep
                # 分離のウィンドウに入ったらすぐ止める(燃料を残す)。入らなくても keep まで減ったら止める
                ready = v.y >= sep.alt_lo * 1.03 and v.speed >= sep.speed_lo * 1.03
                if v.prop <= v.p.prop_mass * self.keep or self.late("meco", ready):
                    run.space()
            elif self.late("sep", v.throttle <= run.m.sep.tail):
                run.z()
            des = math.radians(self.tilt) * min(1.0, max(0.0, (v.y - 800) / 27_000)) ** 0.6
            if v.speed > 60 and v.q > 8_000:
                va = math.atan2(v.vx, v.vy)
                des = min(max(des, va - math.radians(7)), va + math.radians(7))
            return steer_to(v, des), self.thr_for_fire()
        if not self.back_done:
            # 戻りの噴射: 発射場のほうへ向けて、着地予想点が着陸場に来るまで噴く
            back = -math.pi / 2 + math.radians(12)
            if not v.engine_on:
                if v.q < 15_000 and abs((v.theta - back + math.pi) % math.tau - math.pi) < math.radians(8):
                    run.space()
                return (steer_to(v, back, 1.5) if v.q < 15_000 else 0), 1
            # 着地予想(いま止めたらどこに落ちるか)が着陸場まで戻ったら止める
            if run.pred_x is not None and self.late("back", run.pred_x <= run.ship_x + 40):
                run.space()
                self.back_done = True
            return steer_to(v, back, 1.0), 1
        return self.descend()


class ReentryPilot(Pilot):
    """後ろ向きにして減速 → 耐熱シールドを前にして突入 → パラシュート。"""

    def __call__(self):
        run, v, e = self.run, self.run.v, self.run.m.entry
        retro = math.atan2(-v.vx, -v.vy)
        steer = steer_to(v, retro, 1.0, 2.0)
        if run.phase == "deorbit":
            fpa = entry_angle(v.y, v.vx, v.vy, e.interface)
            mid = (e.fpa_lo + e.fpa_hi) / 2
            aligned = abs((v.theta - retro + math.pi) % math.tau - math.pi) < math.radians(5)
            if not v.engine_on:
                if (fpa is None or fpa > mid) and aligned and abs(v.omega) < math.radians(1):
                    run.space()
            elif fpa is not None and fpa <= mid + 0.15 * self.sloppy:
                run.space()
            if not v.engine_on and aligned and abs(v.omega) < math.radians(0.3):
                steer = 0
        elif run.phase == "entry":
            if v.y < (e.chute_lo + e.chute_hi) / 2 and v.speed <= e.chute_speed:
                run.z()
        return steer, 0


def make_pilot(run, sloppy=0.0, **kw):
    """そのステージの種類に合った自動操縦を作る。"""
    m = run.m
    cls = {"ascent": AscentPilot, "orbit": OrbitPilot, "landing": LandingPilot, "hop": HopPilot,
           "recover": RecoverPilot, "reentry": ReentryPilot}[m.kind]
    if m.kind == "recover":
        kw.setdefault("rtls", m.land.site == "pad")
        if m.land.site == "pad":
            kw.setdefault("tilt", 30.0)
    return cls(run, sloppy, **kw)


def fly(mid, sloppy=0.0, inspected=False, seed=0, idle=False, **kw):
    m = MISSIONS[mid]
    if m.kind == "dock":
        return fly_dock(m, sloppy, seed, idle)
    run = MissionRun(m, inspected=inspected, seed=seed)
    pilot = make_pilot(run, sloppy, **kw)
    wall = 0.0
    hold = max(1, int(sloppy * 60))  # 雑な操縦は、キーの押し替えが遅い
    n = 0
    steer = 0
    while run.result is None and wall < 1200:
        if idle:
            if not run.v.launched:
                run.space()
            steer, thr = 0, 0
        else:
            new, thr = pilot()
            if n % hold == 0:
                steer = new
        n += 1
        for _ in range(run.warp * round(run.time_scale)):
            run.step(DT, steer, thr)
        wall += DT
    run.wall = wall
    return run


def fly_dock(m, sloppy, seed, idle):
    run = DockRun(m, seed=seed)
    wall = 0.0
    while run.result is None and wall < 600:
        ix = iy = 0
        if not idle:
            # 把持点へ向かう速度を距離に合わせて決め、いまの速度との差を噴いて直す
            # ゾーンの手前で速度制限まで落とせるように、止まれる速さで近づく
            d = run.dist
            spd = min(2.5, 0.9 + math.sqrt(run.ACCEL * max(0.0, d - run.ZONE - 4))) if d > run.ZONE                 else min(0.9, 0.08 * d + 0.05)
            if d < run.BOX * 0.5:
                spd = 0.0
            wx = -run.x / max(d, 0.01) * spd
            wy = -run.y / max(d, 0.01) * spd
            tol = 0.04 + 0.1 * sloppy
            ix = 1 if wx - run.vx > tol else -1 if wx - run.vx < -tol else 0
            iy = 1 if wy - run.vy > tol else -1 if wy - run.vy < -tol else 0
        run.step(DT, ix, iy)
        wall += DT
    run.wall = wall
    return run


def summary(name, runs):
    ok = [r for r in runs if r.result == "success"]
    ranks = "".join(sorted(r.rank() for r in ok))
    wall = sum(r.wall for r in runs) / len(runs)
    print(f"  {name:<22} 成功 {len(ok):2}/{len(runs)}  ランク {ranks or '-':<20} 平均 {wall:4.0f} 秒")
    reasons = {}
    for r in runs:
        if r.result != "success":
            reasons[r.fail_reason or "(終わらない)"] = reasons.get(r.fail_reason or "(終わらない)", 0) + 1
    for k, n in reasons.items():
        print(f"      失敗 {n:2}: {k}")


def check(mid, n=20, verbose=False):
    m = MISSIONS[mid]
    print(f"{m.id} {m.title}({m.kind})")
    summary("操作なし", [fly(mid, idle=True, seed=s) for s in range(n)])
    summary("上手い操縦", [fly(mid, seed=s) for s in range(n)])
    summary("雑な操縦(0.5 秒遅れ)", [fly(mid, sloppy=0.5, seed=s) for s in range(n)])
    if m.fire_chance or m.gimmick in ("anomaly", "engine_out"):
        summary("上手い操縦 + 点検", [fly(mid, inspected=True, seed=s) for s in range(n)])
    if verbose:
        summary("雑な操縦(1.5 秒遅れ)", [fly(mid, sloppy=1.5, seed=s) for s in range(n)])
        for s in range(3):
            r = fly(mid, seed=s)
            print("      ", [(a, c, d) for a, _, c, d in r.report()], r.rank(), r.fail_reason)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ids = [a for a in sys.argv[1:] if a in MISSIONS] or [m.id for m in ORDER]
    for mid in ids:
        check(mid, verbose="-v" in sys.argv)

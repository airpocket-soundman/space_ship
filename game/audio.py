"""BGM と効果音(レトロゲーム風)。

チャンネル 0〜2 は BGM(0: メロディ / 1: 伴奏 / 2: ベース)、3 はエンジン音・効果音・会話の声に使う。
曲は下の楽譜(音名と長さの並び)から、起動時に Pyxel のサウンドへ組み立てる。
音の長さの単位は 1 ステップ。曲ごとに 1 ステップの長さ(speed、1/120 秒単位)を決める。
"""

import pyxel

SFX = 3  # 効果音のチャンネル

# ---- 楽譜からサウンドを作る ----


def build(events, tone, vol, decay=0.0, vib_from=None):
    """events: [(音名 or "r", ステップ数), ...] から notes / tones / volumes / effects の文字列を作る。

    decay: 伸ばす音をステップごとにどれだけ弱めるか(レトロなピコピコ感)。
    vib_from: このステップ数以上の長い音にはビブラートをかける。
    """
    notes, vols, effs = [], [], []
    for name, steps in events:
        for i in range(steps):
            notes.append(name)
            if name == "r":
                vols.append("0")
                effs.append("n")
                continue
            v = max(1, round(vol - decay * i))
            vols.append(str(v))
            effs.append("v" if vib_from and steps >= vib_from and i > 0 else "n")
    return " ".join(notes), tone, "".join(vols), "".join(effs)


def chord_arp(chords, pattern, steps_per_chord):
    """和音を分散和音(アルペジオ)にする。chords: [[音名...], ...]、pattern: 和音の何番目を鳴らすかの並び。"""
    out = []
    for ch in chords:
        for i in range(steps_per_chord):
            k = pattern[i % len(pattern)]
            out.append((ch[k] if k is not None else "r", 1))
    return out


# ---- 曲 ----
# オープニング(タイトル・最初の飛行): 宇宙開発の夜明け。ゆっくり上っていく旋律と、きらめく分散和音
OPENING_SPEED = 25  # 16 分音符ひとつ(約 72 BPM)
_open_chords = [  # 1 小節 16 ステップ
    ["c2", "e2", "g2", "d3"], ["b1", "d2", "g2", "d3"], ["a1", "c2", "e2", "b2"], ["f1", "a1", "c2", "e2"],
    ["e1", "g1", "c2", "g2"], ["f1", "a1", "c2", "g2"], ["d2", "f2", "a2", "c3"], ["g1", "c2", "d2", "g2"],
]
OPENING = [
    build([("e3", 8), ("g3", 4), ("a3", 4), ("b3", 12), ("a3", 4), ("c4", 8), ("b3", 4), ("a3", 4), ("b3", 16),
           ("g3", 8), ("e3", 4), ("g3", 4), ("a3", 8), ("c4", 8), ("d4", 8), ("c4", 4), ("b3", 4), ("d4", 12), ("r", 4)],
          "p", 5, decay=0.15, vib_from=8),
    build(chord_arp(_open_chords, [0, 1, 2, 3, 2, 1, 2, 3], 16), "s", 2, decay=0),
    build([(c[0].replace("2", "1") if c[0].endswith("2") else c[0], 16) for c in _open_chords], "t", 6, decay=0.2),
]

# マリアッチ(キックオフの場面): 3 拍子。ベースの「ブン」、ギターの「チャッチャッ」、トランペットの旋律
MARIACHI_SPEED = 20  # 8 分音符ひとつ(約 180 BPM の 3 拍子)
_D, _A7, _G = ("d2", "f#2", "a2"), ("c#2", "e2", "g2"), ("b1", "d2", "g2")
_bars = [_D, _D, _A7, _A7, _A7, _A7, _D, _D, _G, _G, _D, _D, _A7, _A7, _D, _D]
_bass = {_D: ("d1", "a0"), _A7: ("a0", "e1"), _G: ("g0", "d1")}
MARIACHI = [
    build([("a2", 2), ("d3", 2), ("f#3", 2), ("a3", 4), ("f#3", 2), ("g3", 2), ("e3", 2), ("c#3", 2), ("e3", 4), ("r", 2),
           ("c#3", 2), ("e3", 2), ("g3", 2), ("b3", 2), ("a3", 2), ("g3", 2), ("f#3", 2), ("a3", 2), ("f#3", 2),
           ("d3", 4), ("r", 2), ("b2", 2), ("d3", 2), ("g3", 2), ("b3", 4), ("a3", 2), ("a3", 2), ("f#3", 2), ("d3", 2),
           ("f#3", 4), ("e3", 2), ("e3", 2), ("g3", 2), ("b3", 2), ("c#4", 2), ("b3", 2), ("a3", 2), ("d4", 2), ("a3", 2),
           ("f#3", 2), ("d4", 4), ("r", 2)],
          "p", 6, decay=0.5, vib_from=4),
    # ギター: 2 拍目と 3 拍目に和音の 3 度と 5 度を刻む
    build([n for i, ch in enumerate(_bars) for n in (("r", 2), (ch[1], 1), (ch[2], 1), (ch[1], 1), (ch[2], 1))],
          "s", 3, decay=0),
    # ベース: 1 拍目に根音と 5 度を交互に
    build([n for i, ch in enumerate(_bars) for n in ((_bass[ch][i % 2], 2), ("r", 4))], "t", 7),
]

# 会社(ADV): 工場の昼下がり。のんびりした 4 拍子
ADV_SPEED = 36  # 8 分音符ひとつ(約 100 BPM)
_adv = [("f1", "a2", "c3"), ("d1", "f2", "a2"), ("a#0", "d2", "f2"), ("c1", "e2", "g2"),
        ("f1", "a2", "c3"), ("a0", "c2", "e2"), ("a#0", "d2", "f2"), ("c1", "e2", "a#2")]
ADV = [
    build([("a2", 2), ("c3", 2), ("a2", 2), ("g2", 2), ("f2", 4), ("d2", 4), ("d2", 2), ("f2", 2), ("a#2", 3), ("a2", 1),
           ("g2", 8), ("a2", 2), ("c3", 2), ("d3", 2), ("c3", 2), ("a2", 4), ("e2", 4), ("f2", 2), ("g2", 2), ("a2", 2),
           ("a#2", 2), ("g2", 4), ("e2", 2), ("c2", 2)],
          "p", 4, decay=0.3, vib_from=4),
    build([n for ch in _adv for n in (("r", 1), (ch[1], 1), ("r", 1), (ch[2], 1), ("r", 1), (ch[1], 1), ("r", 1), (ch[2], 1))],
          "s", 2),
    build([n for ch in _adv for n in ((ch[0], 3), (ch[0], 1), (ch[0], 2), ("r", 2))], "t", 6, decay=0.5),
]

SONGS = {"opening": (0, OPENING, OPENING_SPEED), "mariachi": (1, MARIACHI, MARIACHI_SPEED), "adv": (2, ADV, ADV_SPEED)}

# ---- 効果音 ----
S_ENGINE, S_EXPLODE, S_IGNITE = 12, 13, 14  # 0〜8 は曲
S_VOICE = 16  # ここから声(話者ごとに 4 個)

# 会話の声。話者ごとに (音色, 基準の音, 高さの揺れ)。"" は地の文で声なし
VOICES = {
    "dylon": ("s", "a1", [0, 2, -2, 3]),
    "maya": ("p", "e2", [0, 2, 4, -1]),
    "ken": ("p", "a2", [0, 3, 5, 7]),
    "sara": ("s", "d2", [0, 2, -1, 4]),
    "noah": ("t", "c3", [0, 7, 0, 5]),
    "grey": ("s", "f1", [0, 2, -2, 0]),
    "dylon_ai": ("t", "a1", [0, 12, 0, 7]),
}
_NOTE_NAMES = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]


def _shift(name, semis):
    """音名を半音 semis だけずらす。"""
    base = _NOTE_NAMES.index(name[:-1])
    n = int(name[-1]) * 12 + base + semis
    return f"{_NOTE_NAMES[n % 12]}{n // 12}"


_voice_slots = {}
_current = None  # 流れている BGM
_sfx_state = None  # チャンネル 3 で鳴らしているもの: "engine" / "sfx" / "voice" / None
_ready = False


def setup():
    """起動時に一度だけ、曲と効果音をサウンドに組み立てる。"""
    global _ready
    snd = 0
    for name, (mi, parts, speed) in SONGS.items():
        seqs = []
        for part in parts:
            pyxel.sounds[snd].set(*part, speed)
            seqs.append([snd])
            snd += 1
        pyxel.musics[mi].set(*(seqs + [[]] * (4 - len(seqs))))
    # エンジン: 低いノイズを細かく揺らして、ゴーッという音を作る
    pyxel.sounds[S_ENGINE].set("c1 a0 d1 g0 c1 b0 d1 a0", "n", "7", "n", 3)
    pyxel.sounds[S_EXPLODE].set("c3 a2 f2 d2 c2 a1 f1 d1 c1 a0 f0 c0", "n", "776655443321", "n", 7)
    pyxel.sounds[S_IGNITE].set("c0 d0 f0 a0 c1 d1", "n", "234567", "n", 4)
    slot = S_VOICE
    for who, (tone, base, shifts) in VOICES.items():
        _voice_slots[who] = []
        for s in shifts:
            pyxel.sounds[slot].set(_shift(base, s), tone, "5", "f", 4)
            _voice_slots[who].append(slot)
            slot += 1
    _ready = True


def bgm(name):
    """BGM を流す。同じ曲が流れていれば何もしない。None で止める。"""
    global _current
    if not _ready or name == _current:
        return
    _current = name
    for ch in range(3):
        pyxel.stop(ch)
    if name is not None:
        mi = SONGS[name][0]
        for ch, seq in enumerate(pyxel.musics[mi].seqs[:3]):
            if list(seq):
                pyxel.play(ch, list(seq), loop=True)


def engine(level):
    """エンジン音。level 0 で止め、0〜1 で音量を変える(推力に合わせる)。"""
    global _sfx_state
    if not _ready:
        return
    if level <= 0:
        if _sfx_state == "engine":
            pyxel.stop(SFX)
            _sfx_state = None
        return
    if _sfx_state != "engine" or pyxel.play_pos(SFX) is None:
        if _sfx_state == "sfx" and pyxel.play_pos(SFX) is not None:
            return  # 点火音などが鳴り終わるまで待つ
        pyxel.play(SFX, S_ENGINE, loop=True)
        _sfx_state = "engine"
    pyxel.channels[SFX].gain = 0.06 + 0.1 * min(1.0, level)


def sfx(snd):
    global _sfx_state
    if not _ready:
        return
    pyxel.channels[SFX].gain = 0.15
    pyxel.play(SFX, snd)
    _sfx_state = "sfx"


def explosion():
    sfx(S_EXPLODE)


def ignite():
    sfx(S_IGNITE)


def voice(speaker):
    """会話の文字送りに合わせて鳴らす短い声。話者ごとに高さと音色が違う。"""
    global _sfx_state
    if not _ready or speaker not in _voice_slots:
        return
    _sfx_state = "voice"
    pyxel.channels[SFX].gain = 0.08
    slots = _voice_slots[speaker]
    pyxel.play(SFX, slots[pyxel.rndi(0, len(slots) - 1)])

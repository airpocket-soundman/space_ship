"""シナリオの会話だけを、最初から最後まで通して出す(Pyxel は不要。選択肢なし)。

python tools/story_read.py          全部の打ち上げが成功したことにして、会話を順に出す
python tools/story_read.py 2-1      そのステージから出す
python tools/story_read.py en       英語で出す

出す順は、ゲームで全部 1 回で成功したときと同じ:
オープニング → 各ステージ(ブリーフィング → 成功したときの会話 → 次のステージへ進むときの会話)→ エンディング。
資金や製造の案内など、そのときの状況でプログラムが足す行は出さない。
ランチャー(tools/launcher.py)の「会話の通し読み」から動かすと、【画像 …】をクリックして挿絵(assets/illustrations/)を開ける。
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from game import i18n, script  # noqa: E402
from game.i18n import tr  # noqa: E402
from game.missions import MISSIONS, ORDER  # noqa: E402


def say(lines):
    for speaker, body in lines:
        if speaker == "image":
            print(f"  【画像 {body}: {script.IMAGES[body]}】")
        elif speaker:
            print(f"  {tr(script.NAMES.get(speaker, speaker))}「{tr(body)}」")
        else:
            print(f"  ({tr(body)})")


def heading(text):
    print()
    print(f"==== {text} ====")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    i18n.set_lang(next((a for a in args if a in i18n.LANGS), "ja"))
    start = next((a for a in args if a in MISSIONS), None)
    ids = [m.id for m in ORDER]

    if start is None:
        heading("オープニング")
        for line in script.FLASHBACK:
            print(f"  {tr(line)}")
        say(script.KICKOFF + script.PROLOGUE)

    for sid in ids[ids.index(start):] if start else ids:
        m = MISSIONS[sid]
        heading(tr(m.title))
        if sid == start:  # 途中から出すときは、そのステージへ進むときの会話から
            say(script.INTRO.get(sid, []))
        print("  -- ブリーフィング --")
        say(script.BRIEFING.get(sid, []))
        print("  -- 成功 --")
        say(script.SUCCESS.get(sid, []))
        print("  -- 失敗したとき(マヤの一言は失敗の理由で変わる) --")
        say(script.FAIL_CHEER[0] + script.FAIL_LINES.get(sid, []))
        nxt = ids[ids.index(sid) + 1] if ids.index(sid) + 1 < len(ids) else None
        if nxt and script.INTRO.get(nxt):
            print("  -- 次のステージへ --")
            say(script.INTRO[nxt])

    heading("同じステージで何度も失敗したとき(全ステージ共通)")
    for i, group in enumerate(script.FAIL_CHEER, 1):
        print(f"  -- {i} 回目の失敗(最初に出す) --")
        say(group)
    print("  -- 失敗したときの一言(マヤの一言のあとに出す。全ステージで使い回し、順にくり返す) --")
    say(script.FAIL_COMMENTS)
    print("  -- やり直しのブリーフィング(ディーロンの一言を替える。順にくり返す) --")
    say(script.BRIEFING_RETRY)

    heading("エンディング")
    say(script.ENDING)


if __name__ == "__main__":
    main()

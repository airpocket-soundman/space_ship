"""英語の訳が抜けている日本語の文言を探す。

python tools/check_i18n.py
game/*.py の文字列(ドキュメント文字列を除く)のうち、日本語を含むのに lang_en.EN にないものを出す。
日本語が入った f-string は訳せないので、trf() とテンプレートに書き換えるよう知らせる。
"""

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from game.lang_en import EN  # noqa: E402

JP = re.compile(r"[ぁ-んァ-ヶ一-龥]")
SKIP_FILES = {"i18n.py", "lang_en.py"}
# 画面には出さず、判定にだけ使う文言
LOGIC_ONLY = {"火災", "分解", "姿勢"}


def docstrings(tree):
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                ids.add(id(first.value))
    return ids


def main():
    problems = 0
    for path in sorted((ROOT / "game").glob("*.py")):
        if path.name in SKIP_FILES:
            continue
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src)
        docs = docstrings(tree)
        in_fstring = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.JoinedStr):
                for part in ast.walk(node):
                    in_fstring.add(id(part))
                seg = ast.get_source_segment(src, node)
                if JP.search(seg) and "raise" not in src.splitlines()[node.lineno - 1]:
                    print(f"{path.name}:{node.lineno}: f-string は訳せません → trf() にする: {seg}")
                    problems += 1
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
                continue
            if id(node) in docs or id(node) in in_fstring:
                continue
            s = node.value
            if not JP.search(s) or s in EN or s in LOGIC_ONLY:
                continue
            print(f"{path.name}:{node.lineno}: 訳がありません: {s!r}")
            problems += 1
    print("OK" if problems == 0 else f"{problems} 件")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

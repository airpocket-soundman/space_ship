"""表示言語の切り替え。

文言は日本語をそのままキーにして、英語のときだけ lang_en.EN の訳に差し替える。
ゲームの判定には日本語の文言をそのまま使い、表示する直前に訳す。
数値が入る文は、日本語のテンプレートを trf() に渡して訳してから埋める。
"""

from .lang_en import EN

LANGS = ("ja", "en")
LANG = "ja"


def set_lang(lang):
    global LANG
    if lang not in LANGS:
        raise ValueError(f"言語は {' / '.join(LANGS)} のどれか: {lang}")
    LANG = lang


def tr(s, ctx=None):
    """ctx を渡すと "ctx|文言" の訳を優先する(同じ日本語で訳し分けたいとき)。"""
    if LANG == "ja":
        return s
    if ctx is not None and f"{ctx}|{s}" in EN:
        return EN[f"{ctx}|{s}"]
    return EN.get(s, s)


def trf(template, *args, **kwargs):
    """テンプレートを訳してから値を埋める。"""
    return tr(template).format(*args, **kwargs)

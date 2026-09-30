"""会社画面のコマンドと、飛行のあとの会話(Pyxel に依存しない)。

ゲーム本体(scene_office / app)と、文字だけでシナリオを確かめる tools/story_check.py が同じ処理を使う。
"""

from . import script
from .i18n import tr, trf
from .missions import MISSIONS, next_stage

# 会社画面のコマンド: (キー, 名前, 使う AP)
COMMANDS = [
    ("build", "製造", 1),
    ("inspect", "点検", 1),
    ("fund", "調達", 1),
    ("launch", "打上", 0),
    ("wait", "待機", 0),
]


def describe(st, key):
    """コマンドの説明文(製造と打上は、いまのステージに合わせて変わる)。"""
    if key == "build":
        cost, months = st.build_cost()
        if st.craft == "eagle9" and st.recovered > 0:
            return trf("回収した1段目を整備して Eagle 9 にする({cost:.0f}M$・{months}ヶ月)", cost=cost, months=months)
        return trf("{name} を製造する({cost:.0f}M$・{months}ヶ月)", name=st.craft_name, cost=cost, months=months)
    if key == "inspect":
        return trf("次の打ち上げの故障を起きにくくする({cost}M$)", cost=st.INSPECT_COST)
    if key == "fund":
        return tr("資金を集める(3ヶ月に1回)")
    if key == "launch":
        m = MISSIONS[st.stage]
        return trf("{title}: {goal}(その月の残り AP をすべて使う)", title=tr(m.title), goal=tr(m.goal))
    return tr("次の月へ進む")


def _use_ap(st, n):
    if st.ap < n:
        return False
    st.ap -= n
    return True


def command(st, key):
    """コマンドを実行する。(会話の行, 次に起きること) を返す。

    次に起きること: None / "launch"(会話のあと打ち上げへ)/ "game_over"(会話のあと倒産)
    """
    busy = [("sara", "今月はもう動けないわ。「待機」して。")]
    if key == "build":
        if st.ready() + st.building_now() >= 2:
            return [("maya", "もう2機あるわ。置き場所がない。")], None
        cost, months = st.build_cost()
        if st.funds < cost:
            return [("sara", "製造するお金が足りないわ。")], None
        if not _use_ap(st, 1):
            return busy, None
        st.funds -= cost
        if st.craft == "eagle9" and st.recovered > 0:
            st.recovered -= 1
        st.building.append([st.craft, months])
        return [("maya", trf("{name} の製造を始めたわ。{months}ヶ月後に完成する。", name=st.craft_name, months=months))], None
    if key == "inspect":
        if st.inspected:
            return [("maya", "点検はもう済んでる。次の打ち上げまで有効よ。")], None
        if not _use_ap(st, 1):
            return busy, None
        st.funds -= st.INSPECT_COST
        st.inspected = True
        return [("maya", "機体を隅々まで見直した。故障はだいぶ起きにくくなるはず。")], None
    if key == "fund":
        if st.month_index - st.last_fundraise < 3:
            return [("sara", "調達は3ヶ月に1回までよ。")], None
        if not _use_ap(st, 1):
            return busy, None
        st.last_fundraise = st.month_index
        amount = st.fundraise_amount()
        st.funds += amount
        return [("sara", trf("{amount}M$ 集まったわ。", amount=amount))], None
    if key == "launch":
        if st.ready() <= 0:
            return [("maya", "機体がないわ。「製造」して。")], None
        lines = list(script.BRIEFING[st.stage])
        lines += script.BRIEFING_INSPECTED if st.inspected else script.BRIEFING_NOT_INSPECTED
        lines += script.BRIEFING_END
        return lines, "launch"
    # wait
    lines = st.next_month()
    return lines, ("game_over" if st.funds < 0 else None)


def after_flight(st, run, summary):
    """飛行のあと、会社に戻ったときの会話。成功したら次のステージへ進める。"""
    m = run.m
    if run.result == "success":
        lines = list(script.SUCCESS[m.id]) if summary["first"] else []
        if summary["funds"]:
            lines.append(("sara", trf("{funds:.0f}M$ が入ったわ。", funds=summary["funds"])))
        if summary["recovered"]:
            lines.append(("maya", "1段目を回収したわ。次の Eagle 9 は、整備だけで安く作れる。"))
        nxt = next_stage(m.id)
        if summary["first"] and nxt:
            st.stage = nxt
            st.inspected = False
            lines += script.INTRO.get(nxt, [])
            if st.ready() <= 0 and not st.building_now():
                cost, months = st.build_cost()
                lines.append(("maya", trf("{name} は「製造」で用意して({cost:.0f}M$・{months}ヶ月)。",
                                          name=st.craft_name, cost=cost, months=months)))
        elif summary["first"]:
            st.finished = True
            lines += script.ENDING
    else:
        if run.saved:
            lines = list(script.SAVED)
        else:
            hint = next(text for key, text in script.FAIL_HINTS if key in run.fail_reason)
            lines = [("maya", hint)]
        if st.ready() <= 0 and not st.building_now():
            cost, months = st.build_cost()
            lines.append(("sara", trf("機体がないわ。「製造」で {name} を用意して({cost:.0f}M$・{months}ヶ月)。",
                                      name=st.craft_name, cost=cost, months=months)))
        recent = [f["result"] for f in st.flights[-3:]]
        if recent == ["fail"] * 3 and "comeback" not in st.seen:
            st.seen.add("comeback")
            st.funds += script.COMEBACK_FUNDS
            lines += script.COMEBACK
    lines.append(("sara", "今月はもう手一杯。「待機」で次の月へ。"))
    return lines

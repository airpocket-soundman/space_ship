"""英語の訳。キーは画面に出す日本語の文言(数値が入る文は i18n.trf に渡すテンプレート)。"""

EN = {
    # ---- オープニング ----
    "Eagle 1 の初飛行。操縦するのは、あなただ。": "Eagle 1's first flight. You're the one flying it.",
    "SPACE で点火!": "Press SPACE to ignite!",
    "↑↓ でスロットル(推力)。このエンジンは 70% より下には絞れない。":
        "↑↓ sets the throttle. This engine can't go below 70%.",
    "←→ でノズルを振って姿勢を変える。傾いたら、反対に当てて戻す。":
        "←→ swings the nozzle to steer. If you tilt, counter-steer to come back.",
    "右の窓: 高度 10 km を通過するとき、この範囲に入っていれば高評価。":
        "The window on the right: be inside these ranges when you pass 10 km for a high rank.",
    "いい調子だ。そのまま、まっすぐ上へ!": "Looking good. Keep going, straight up!",
    "4年前——": "Four years earlier--",
    "すべては、家具もない部屋から始まった。": "It all began in a room without furniture.",

    # ---- 会話: キックオフ ----
    "……で、なんでマリアッチ?": "...So, why a mariachi band?",

    # ---- 会話: ブリーフィング ----
    "よし。俺が飛ばす。": "Right. I'm flying it.",

    # ---- 会話: 結果 ----
    "次は宇宙だ。": "Next stop: space.",
    "……もう払えるお金がないわ。": "...There's no money left to pay anyone.",

    # ---- 会話: 一度だけのエピソード ----
    "俺は絶対に諦めない。文字通り、絶対にだ。": "I will never give up. And I mean never.",

    # ---- 会社の状態 ----
    "創業{year}年目 {month}月": "Year {year}, Month {month}",
    "今月の固定費 {cost:.1f}M$ を払ったわ。残りは {funds:.1f}M$。":
        "Paid this month's fixed costs of {cost:.1f}M$. {funds:.1f}M$ left.",
    "Eagle 1 が{n}機、完成したわ。いつでも飛ばせる。": "{n} Eagle 1 finished. Ready to fly anytime.",
    "……資金が危ないわ。次の失敗は、会社の終わりかもしれない。":
        "...Our funds are running low. One more failure could end the company.",

    # ---- 会社画面 ----
    "製造": "Build",
    "点検": "Check",
    "調達": "Fund",
    "打上": "Launch",
    "待機": "Wait",
    "Eagle 1 を製造する({cost:.0f}M$・{months}ヶ月)": "Build an Eagle 1 ({cost:.0f}M$, {months} months)",
    "次の打ち上げの故障を起きにくくする({cost}M$)": "Make failures less likely on the next launch ({cost}M$)",
    "次の月へ進む": "Advance to next month",
    "製造するお金が足りないわ。": "We don't have enough money to build one.",
    "Eagle 1 の製造を始めたわ。{months}ヶ月後に完成する。":
        "Started building an Eagle 1. It'll be done in {months} months.",
    "点検はもう済んでる。次の打ち上げまで有効よ。": "Already inspected. It holds until the next launch.",
    "{amount}M$ 集まったわ。": "We raised {amount}M$.",
    "資金 {funds:6.1f}M$": "Funds {funds:6.1f}M$",
    "評判 {rep}": "Rep {rep}",
    "機体 {n}{build}": "Rockets {n}{build}",
    " 製造中{n}": " +{n} bldg",
    "製造中": "BUILDING",
    "【{label}】": "[{label}]",
    "←→ 選択 / SPACE・Z 決定": "←→ select / SPACE or Z confirm",

    # ---- 人物 ----
    "ディーロン": "Dylon",
    "マヤ": "Maya",
    "ケン": "Ken",
    "サラ": "Sara",
    "ノア": "Noah",
    "ディーロンAI": "Dylon AI",
    "グレイ": "Grey",
    "ドク・ヒューズ": "Doc Hughes",
    "ボルト": "Bolt",
    "ハシモト": "Hashimoto",
    "ミミ": "Mimi",
    "ゲンさん": "Gen",

    # ---- ミッション ----
    "Ch1-1 初飛行": "Ch1-1 First Flight",
    "高度 10 km を突破せよ": "Climb past 10 km",
    "時刻": "Time",
    "垂直速度": "V speed",
    "水平速度": "H speed",
    "傾き": "Tilt",
    "window|垂直速度": "V spd",  # 計器パネルの WP の表(幅が狭い)
    "window|水平速度": "H spd",
    "最大動圧を通過": "Passed max Q",
    "エンジン区画で火災! 出力を最低まで絞れ!": "Engine bay fire! Throttle down to minimum!",
    "消火を確認。出力を戻してよし": "Fire is out. Throttle back up.",
    "火災でエンジンが爆発": "Fire blew up the engine",
    "迎角が大きすぎて空中分解": "Broke up: angle of attack too high",
    "姿勢を失ったため飛行中断(自爆)": "Lost attitude: flight terminated",
    "墜落": "Crashed",
    "燃料切れ": "Out of fuel",
    "時間切れ": "Out of time",
    "{name} 通過! 高度 {alt:.0f} km を突破": "{name} passed! Climbed past {alt:.0f} km",

    # ---- 打ち上げ画面 ----
    "射場クリア。カウントダウン開始": "Range clear. Countdown started",
    "点火準備よし。SPACE で点火!": "Ready for ignition. Press SPACE!",
    "点火!": "Ignition!",
    "リフトオフ!": "Liftoff!",
    "SPACE 点火   ↑↓ スロットル   ←→ 姿勢": "SPACE ignite   ↑↓ throttle   ←→ steer",
    "SPACE点火 ↑↓出力 ←→姿勢": "SPACE:ign ↑↓thr ←→steer",
    "!! エンジン火災 !!": "!! ENGINE FIRE !!",
    "WP1 通過 ── ミッション成功": "WP1 PASSED - SUCCESS",
    "ミッション失敗": "MISSION FAILED",
    "ランク {rank}": "Rank {rank}",
    "SPACE で続ける": "SPACE to continue",
    "高度": "Altitude",
    "動圧": "Dyn. Q",
    "角速度": "Rot rate",
    "迎角": "AoA",
    "エンジン": "Engine",
    "燃焼中": "BURN",
    "engine|待機": "IDLE",
    "停止": "OFF",
    "{eng}  点火残 {n}": "{eng}  ignitions {n}",
    "{eng} 点火残{n}": "{eng} ign {n}",
    "スロットル": "Throttle",
    "出力": "Throttle",
    "推進剤": "Fuel",
    "ジンバル": "Gimbal",
    "温度": "Temp",
    "火災!": "FIRE!",
    "{name}  高度 {alt:.0f} km 通過時": "{name}  at {alt:.0f} km altitude",
    "{name} 高度{alt:.0f}km 通過時": "{name} at {alt:.0f} km",
    "窓に入るほどランクが上がる": "Hit windows to rank up",
    "窓に入るほどランクUP": "In window = rank up",

    # ---- リザルト ----
    "飛行結果": "Flight Result",
    "ミッション成功": "Mission Success",
    "{name}(高度 {alt:.0f} km 通過時)": "{name} (at {alt:.0f} km)",
    "窓 {lo:+.0f} ~ {hi:+.0f} {unit}": "window {lo:+.0f} ~ {hi:+.0f} {unit}",
    "最高高度 {alt:.2f} km": "Max alt {alt:.2f} km",
    "会社への影響": "Company impact",
    "テレメトリ +{tlm}": "Telemetry +{tlm}",
    "評判 {rep:+d}": "Reputation {rep:+d}",
    "機体 -1(Eagle 1 は使い捨て)": "Rocket -1 (Eagle 1 is expendable)",
    "SPACE で工場へ戻る": "SPACE: back to the factory",

    # ---- タイトル ----
    "セーブ機能は準備中です。": "Saving is coming soon.",
    "オプションは準備中です。": "Options are coming soon.",
    "STAR X  ─  ロケット経営 × 操縦ゲーム": "STAR X  -  rocket company & flight game",
    "企画・原案      airpocket-soundman": "Concept         airpocket-soundman",
    "プログラム      Claude": "Program         Claude",
    "エンジン        Pyxel": "Engine          Pyxel",
    "フォント        umplus(M+ / 東雲)": "Font            umplus (M+ / Shinonome)",
    "実在の宇宙企業へのオマージュ(パロディ)作品です。": "An homage (parody) to real space companies.",

    # ---- 会話(簡素化版) ----
    "創業の日。家具もない借りビルに、なぜかマリアッチ楽団。": "Founding day. A rented building with no furniture, and for some reason, a mariachi band.",
    "キックオフだ! 俺たちは火星に行くんだぞ!": "It's our kickoff! We're going to Mars!",
    "ロケットは高すぎる。材料費は値段の数パーセントだ。なら、自分で作る。":
        "Rockets cost too much. The materials are a few percent of the price. So we build our own.",
    "社員は片手で数えるほど。ここから全部が始まった。": "A handful of people. This is where it all began.",
    "4年後。太平洋の孤島、オメガ島の射場。": "Four years later. The launch site on Omega Island, alone in the Pacific.",
    "資金は 100M$。固定費は毎月 3M$ よ。": "We have 100M$. Fixed costs are 3M$ a month.",
    "Eagle 1 は組み上がってる。いつでも飛ばせるわ。": "Eagle 1 is assembled. It can fly anytime.",
    "飛行制御は私が——": "I can handle flight control--",
    "却下。俺が飛ばす。": "Denied. I'm flying it.",
    "【操作】←→ で選んで SPACE で決定。「点検」してから「打上」がおすすめ。":
        "[Controls] Choose with ←→ and confirm with SPACE. Try \"Check\" before \"Launch.\"",
    "目標は高度 10 km。窓に入って通過すれば、ランクが上がる。": "The goal is 10 km. Pass it inside the windows for a better rank.",
    "空気が濃いうちは傾けすぎないで。まっすぐ上へ。": "Don't tilt too much while the air is thick. Straight up.",
    "点検はしてない。火が出たら、すぐ出力を絞って。": "We didn't inspect it. If there's a fire, throttle down right away.",
    "燃料ラインは点検済みよ。": "The fuel lines are inspected.",
    "10 km 突破!! 見た!?": "Past 10 km!! Did you see that!?",
    "── デモ版はここまでです。続きは次のアップデートで。──": "-- That's the end of the demo. More in the next update. --",
    "原因を突き止めて、直してくれ。資金は俺が集める。": "Find the cause and fix it. I'll get the money.",
    "15M$ 集まったわ。……これが最後よ。": "We raised 15M$. ...This is the last chance.",
    "機体を失ったわ。「製造」で新しい Eagle 1 を作って(7M$・2ヶ月)。": "We lost the rocket. \"Build\" a new Eagle 1 (7M$, 2 months).",
    "燃料漏れで火が出た。次は「点検」してから飛ばしましょう。": "A fuel leak started a fire. \"Check\" the rocket before the next flight.",
    "空気が濃いところで傾きすぎて、機体が折れたの。まっすぐ、小さく当てて。":
        "It tilted too far in thick air and snapped. Keep it straight, use small inputs.",
    "傾きすぎて自爆したわ。回り始めたら、反対側に当てて止めるの。":
        "It tilted too far and self-destructed. When it starts turning, counter-steer to stop it.",
    "失敗はデータよ。次に活かしましょう。": "Failure is data. Let's use it next time.",
    "今月はもう手一杯。「待機」で次の月へ。": "That's all for this month. \"Wait\" to move on.",
    "資金を集める(3ヶ月に1回)": "Raise money (once every 3 months)",
    "打ち上げる(その月の残り AP をすべて使う)": "Launch (uses all remaining AP this month)",
    "燃料ラインを見直した。火災はだいぶ起きにくくなるはず。": "Went over the fuel lines. Fires should be much less likely.",
    "今月はもう動けないわ。「待機」して。": "We can't do more this month. \"Wait.\"",
    "もう2機あるわ。置き場所がない。": "We already have two. No room for more.",
    "調達は3ヶ月に1回までよ。": "Fundraising is once every 3 months.",
    "機体がないわ。「製造」して。": "No rocket. \"Build\" one.",
}

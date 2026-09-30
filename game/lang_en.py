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
    "創業の日。借りたばかりの工業用ビルには、まだ家具すら届いていない。":
        "Founding day. The industrial building we just rented doesn't even have furniture yet.",
    "あるのは、むき出しのカーペットとホワイトボードが一枚。そして、なぜかマリアッチ楽団。":
        "Just bare carpet and a single whiteboard. And, for some reason, a mariachi band.",
    "……で、なんでマリアッチ?": "...So, why a mariachi band?",
    "キックオフだ! 祝うのに理由はいらない。俺たちは火星に行くんだぞ!":
        "It's our kickoff! You don't need a reason to celebrate. We're going to Mars!",
    "家具より先にバンドを呼ぶ会社、はじめて見たわ。":
        "First company I've seen that booked a band before buying furniture.",
    "設計図もまだ一枚もないのにね。": "And we don't have a single blueprint yet.",
    "そもそも、なぜロケットを自社で作るのですか。既製品を買う選択肢もあったはずです。":
        "Why build our own rockets at all? Buying an existing one should have been an option.",
    "買いに行ったさ。北の大国まで、中古の大陸間ミサイルをな。":
        "I tried. I flew to the great northern power to buy used ICBMs.",
    "1基 800万ドルだと。しかも鼻で笑われて、追い返された。":
        "Eight million dollars apiece. And they laughed me out of the room.",
    "帰りの飛行機で、原材料の値段を全部計算した。アルミ、チタン、燃料……ロケットの値段のほんの数パーセントだった。":
        "On the flight home I priced out every raw material. Aluminum, titanium, fuel... "
        "just a few percent of what a rocket sells for.",
    "だったら自分たちで作ったほうが早い。そう思ったら、会社を作ってた。":
        "So it's faster to build them ourselves. Next thing I knew, I'd started a company.",
    "……キレて会社作る人、はじめて見た。": "...First time I've seen someone rage-quit into founding a company.",
    "社員は片手で数えるほど。ロケットも、実績もない。それでも、ここから全部が始まった。":
        "A handful of people. No rocket, no track record. Still, this is where it all began.",

    # ---- 会話: プロローグ ----
    "4年後。倉庫を改装した工場。机と溶接機、それに一台の中古ノートPC。":
        "Four years later. A converted warehouse. A desk, a welder, and one secondhand laptop.",
    "資本金は 100M$。それが全部。いい?":
        "We have 100M$ in capital. That's everything. Got it?",
    "軌道に届く小さなロケットを作る。いずれは、着陸して戻ってくるロケットを。":
        "We build a small rocket that can reach orbit. Someday, one that lands and comes back.",
    "つまり、爆発シーンは撮り放題ってことだね!":
        "So basically, unlimited explosion footage!",
    "飛行制御は私が担当できます。成功率の試算は——":
        "I can handle flight control. My estimate of the success rate is--",
    "却下。俺が飛ばす。宇宙船のパイロットになるのが夢なんだ。":
        "Denied. I'm flying it. Being a spaceship pilot is my dream.",
    "……はいはい。じゃあせめて、飛ばしやすい機体を作るわね。":
        "...Fine, fine. Then at least I'll build one that's easy to fly.",
    "Eagle 1 の1号機はもう組み上がってる。いつでも島の射場に運べるわ。":
        "The first Eagle 1 is already assembled. We can ship it to the island pad anytime.",
    "毎月 3M$ の固定費がかかるの。のんびりしてると、飛ぶ前にお金がなくなるわよ。":
        "Fixed costs are 3M$ a month. Take it easy and we'll be broke before we ever fly.",
    "【操作】←→ でコマンドを選び、SPACE / Z で決定。「打上」で初飛行へ。":
        "[Controls] Pick a command with ←→ and confirm with SPACE / Z. Choose \"Launch\" for the first flight.",

    "ところでさ、なんで Eagle(イーグル)なの?": "By the way, why \"Eagle\"?",
    "決まってるだろ。映画『スペース・ウォーズ』のミレニアム・イーグル号だ。":
        "Obviously. The Millennium Eagle from the movie \"Space Wars.\"",
    "……名前の由来まで宇宙オタクなのね。": "...Even the name is pure space nerd.",
    "射場は太平洋のど真ん中、クワゼラ環礁のオメガ島。本土じゃ打ち上げの許可が下りなかったの。":
        "The launch site is Omega Island on Kwazela Atoll, in the middle of the Pacific. "
        "We couldn't get a launch permit on the mainland.",
    "暑くて湿度はほぼ 100%。みんなプレハブ小屋に寝泊まりして、手で組み立ててる。":
        "It's hot, with nearly 100% humidity. Everyone sleeps in prefab huts and builds by hand.",
    "補給船が遅れると、食べるものもなくなるわ。覚悟しておいて。":
        "When the supply ship runs late, the food runs out too. Be ready for it.",
    "(大学の寮に片っ端から電話をかける)「ロケット会社を作った。世界を変えに来ないか?」":
        "(cold-calls every university dorm) \"I started a rocket company. Want to come change the world?\"",
    "……それ、完全に詐欺電話だよね。": "...That totally sounds like a scam call.",
    "ほとんど切られたけど、一人だけ本当に来たわ。寝る間も惜しんで働く、腕のいい若いエンジニアよ。":
        "Most of them hung up, but one actually came. A sharp young engineer who barely sleeps.",
    "来月から AP が 1 増える。": "AP goes up by 1 from next month.",
    "オメガ島への補給船が、また遅れている。": "The supply ship to Omega Island is late again.",
    "島のみんなから連絡! 食料が尽きて、ストライキだって!":
        "Message from the island! The food ran out, and they're on strike!",
    "今月は人手が足りないわ。AP が 1 減るわよ。": "We're short-handed this month. AP goes down by 1.",

    "今のロケットは、一回飛ばしたら海に捨てる。毎回ジャンボジェットを使い捨てて飛んでるようなもんだ。":
        "Rockets today get dumped in the ocean after one flight. It's like throwing away a jumbo jet every trip.",
    "ロケットの着陸は『嵐の中で鉛筆を投げ上げて、手のひらの上に立てる』ようなもの、と言われています。":
        "Landing a rocket is said to be like \"tossing a pencil into a storm and balancing it on your palm.\"",
    "だから面白いんだ。": "That's what makes it fun.",
    "その次は火星だ。地球と火星が近づく『窓』は、26ヶ月に一度しか来ない。":
        "Then Mars. The \"window\" when Earth and Mars line up only comes once every 26 months.",
    "最初の窓で無人機を着陸させ、次の窓で有人飛行。その後、100万人が暮らす都市を作るには——":
        "Land uncrewed ships in the first window, fly crew in the next. After that, to build a city of a million people--",
    "1回の窓に、何千機も飛ばせばいい。": "We just launch thousands of ships every window.",
    "……まずは宇宙まで行けるようになってからね。": "...Let's reach space first, shall we.",

    # ---- 会話: ブリーフィング ----
    "初飛行の目標は、高度 10 km の突破。WP1 と呼ぶわ。":
        "The goal of the first flight: climb past 10 km. We'll call it WP1.",
    "10 km を通過する瞬間に、時刻・垂直速度・水平速度・傾きを記録する。窓に入っていればランクが上がる。":
        "The moment you pass 10 km we record time, vertical speed, horizontal speed and tilt. "
        "Hit the windows and your rank goes up.",
    "SPACE で点火。↑↓ でスロットル。ただしこのエンジンは 70% より下には絞れない。":
        "SPACE to ignite. ↑↓ for throttle. But this engine can't go below 70%.",
    "←→ でノズルを振って姿勢を変える。回り始めたら反対に当てないと止まらないから気をつけて。":
        "←→ swings the nozzle to steer. Once it starts rotating, it won't stop until you counter-steer.",
    "空気が濃いところで横を向くと、機体が空気の力で折れる。まっすぐ上へ。":
        "Turn sideways in thick air and the airframe snaps. Straight up.",
    "注意: 1段目エンジンの点火は1回きりです。一度止めたら再点火できません。":
        "Caution: the first-stage engine ignites only once. Once it stops, it cannot be relit.",
    "……正直、燃料ラインの点検は間に合ってない。何かあったら、すぐ出力を絞って。":
        "...Honestly, we didn't get to inspect the fuel lines. If anything happens, throttle down right away.",
    "燃料ラインは全部点検したわ。それでも何かあったら、出力を絞って耐えて。":
        "I inspected every fuel line. If something still goes wrong, throttle down and hang on.",
    "よし。俺が飛ばす。": "Right. I'm flying it.",

    # ---- 会話: 結果 ----
    "10 km 突破!! 見た? 今の見た!?": "Past 10 km!! Did you see that? Did you SEE that!?",
    "エンジンも機体も、ちゃんと持った。データも取れたわ。":
        "The engine and the airframe both held up. And we got the data.",
    "……ほんの少しだけ、投資家に話せることができたわね。":
        "...We finally have a little something to tell the investors.",
    "次は宇宙だ。": "Next stop: space.",
    "── デモ版はここまでです。Ch1-2「宇宙へ」は次のアップデートで。──":
        "-- That's the end of the demo. Ch1-2 \"To Space\" comes in the next update. --",
    "このまま会社の経営を続けたり、もう一度打ち上げたりできます。":
        "You can keep running the company or launch again.",
    "……えーと、最高の映像が撮れました。": "...Uh, well, we got amazing footage.",
    "燃料ラインの継ぎ目から漏れて、エンジン区画が燃えた。点検していれば防げたかもしれない。":
        "A fuel line joint leaked and the engine bay caught fire. An inspection might have prevented it.",
    "失敗はデータよ。次は「点検」をしてから飛ばしましょう。":
        "Failure is data. Next time, let's \"Check\" the rocket before we fly.",
    "空中で……バラバラに……": "It just... came apart... in midair...",
    "空気が濃いところで傾きすぎたの。迎角が大きいと、機体が空気の力に負けて折れる。":
        "It tilted too far in thick air. With a big angle of attack, the air force snaps the airframe.",
    "失敗はデータよ。まっすぐ、小さく当てて。": "Failure is data. Keep it straight, use small inputs.",
    "機体が 45° 以上傾いたため、安全のため飛行を中断しました。":
        "The vehicle tilted beyond 45°, so the flight was terminated for safety.",
    "回り始めたら、反対側にも当てて止めるの。押しっぱなしはだめ。":
        "When it starts turning, counter-steer to stop it. Don't just hold the button.",
    "失敗はデータよ。何が起きたか、全部記録してある。": "Failure is data. Everything that happened is on record.",
    "機体は失ったわ。次を飛ばすには「製造」で新しい Eagle 1 を作らないと。7M$、2ヶ月よ。":
        "We lost the rocket. To fly again we need to \"Build\" a new Eagle 1. 7M$ and 2 months.",
    "……もう払えるお金がないわ。": "...There's no money left to pay anyone.",
    "工場は競売にかけられた。": "The factory went up for auction.",
    "でも、データは残った。": "But the data survived.",
    "打ち上げで今月は手一杯。「待機」で次の月へ進めましょう。":
        "The launch took up this whole month. Use \"Wait\" to move on to next month.",

    # ---- 会話: 一度だけのエピソード ----
    "ニュースじゃ『また失敗』って言われてるよ……": "The news is calling it \"another failure\"...",
    "当社の公式発表では『予定外の急速な分解』と表現します。":
        "Our official statement will call it a \"rapid unscheduled disassembly.\"",
    "限界まで攻めたから、最高のデータが取れた。大成功だ。":
        "We pushed it to the limit, so we got the best data possible. Huge success.",
    "3回連続の失敗。工場は重い空気に包まれていた。": "Three failures in a row. A heavy silence hung over the factory.",
    "全員、聞いてくれ。": "Everyone, listen up.",
    "俺は絶対に諦めない。文字通り、絶対にだ。": "I will never give up. And I mean never.",
    "なぜ失敗したのか、物理的な原因を突き止めろ。原因さえ分かれば直せる。":
        "Find the physical cause of the failure. Once we know the cause, we can fix it.",
    "4回目の打ち上げ資金は俺がなんとか集める。君たちはロケットを直してくれ。":
        "I'll find the money for a fourth launch somehow. You fix the rocket.",
    "……あの人、目が全然死んでない。むしろ燃えてる。": "...His eyes aren't dead at all. If anything, they're on fire.",
    "あれで弱気な顔されてたら、たぶん全員辞めてたね。": "If he'd looked even a little shaken, we'd probably all have quit.",
    "ディーロンが 15M$ かき集めてきたわ。……本当に、これが最後よ。":
        "Dylon scraped together 15M$. ...This really is the last chance.",
    "(投資家に)次の打ち上げは来月だ。俺たちは、戻ってくるロケットで宇宙を安くする。":
        "(to investors) Next launch is next month. We'll make space cheap with rockets that come back.",
    "……また守れない締め切りを言って。": "...Another deadline we can't possibly meet.",
    "俺のスケジュールは、すべてが物理法則の限界の速さで進んだ場合のものだ。遅れるのは君たちのせいだ。":
        "My schedule assumes everything goes perfectly, at the speed limit of physics. Any delay is on you.",
    "……聞かなかったことにするわ。": "...I'll pretend I didn't hear that.",

    # ---- 会社の状態 ----
    "創業{year}年目 {month}月": "Year {year}, Month {month}",
    "今月の固定費 {cost:.1f}M$ を払ったわ。残りは {funds:.1f}M$。":
        "Paid this month's fixed costs of {cost:.1f}M$. {funds:.1f}M$ left.",
    "Eagle 1 が{n}機、完成したわ。いつでも飛ばせる。": "{n} Eagle 1 finished. Ready to fly anytime.",
    "……資金が危ないわ。次の失敗は、会社の終わりかもしれない。":
        "...Our funds are running low. One more failure could end the company.",

    # ---- 会社画面 ----
    "開発": "R&D",
    "製造": "Build",
    "点検": "Check",
    "宣伝": "PR",
    "営業": "Sales",
    "調達": "Fund",
    "採用": "Hire",
    "打上": "Launch",
    "待機": "Wait",
    "研究で機体を扱いやすくする(準備中)": "Research to make the rocket easier to fly (coming soon)",
    "Eagle 1 を製造する({cost:.0f}M$・{months}ヶ月)": "Build an Eagle 1 ({cost:.0f}M$, {months} months)",
    "次の打ち上げの故障を起きにくくする({cost}M$)": "Make failures less likely on the next launch ({cost}M$)",
    "ケンに配信を頼んで評判を上げる。CEO の SNS は当たり外れあり":
        "Ask Ken to stream and raise reputation. The CEO's social posts are hit or miss",
    "顧客を探す": "Look for customers",
    "投資家にピッチして資金を集める(3ヶ月に1回)": "Pitch investors to raise money (once every 3 months)",
    "エンジニアを採用。AP +1、固定費 +0.5M$": "Hire an engineer. AP +1, fixed cost +0.5M$",
    "ミッションを選んで打ち上げる(その月の残り AP をすべて使う)":
        "Choose a mission and launch (uses all remaining AP this month)",
    "次の月へ進む": "Advance to next month",
    "今月はもう動けないわ。「待機」で次の月へ進めて。": "We can't do anything more this month. \"Wait\" to move on.",
    "研究メニューはまだ準備中よ。次のアップデートを待ってて。":
        "The research menu isn't ready yet. Wait for the next update.",
    "もう手元と製造中を合わせて2機ある。これ以上は置き場所がないわ。":
        "We already have two, counting the one being built. There's no room for more.",
    "製造するお金が足りないわ。": "We don't have enough money to build one.",
    "Eagle 1 の製造を始めたわ。{months}ヶ月後に完成する。":
        "Started building an Eagle 1. It'll be done in {months} months.",
    "点検はもう済んでる。次の打ち上げまで有効よ。": "Already inspected. It holds until the next launch.",
    "燃料ラインの継ぎ目とナットを全部見直した。これで火災の危険はだいぶ下がるはず。":
        "I went over every fuel line joint and nut. The fire risk should be much lower now.",
    "(SNS に投稿)「俺たちは火星に行く」": "(posts on social media) \"We're going to Mars.\"",
    "バズった! 評判がぐっと上がったよ!": "It went viral! Reputation shot up!",
    "(SNS に投稿)「ロケットなんて簡単だ」": "(posts on social media) \"Rockets are easy.\"",
    "……炎上してる。評判が下がったよ。": "...It's blowing up, and not in a good way. Reputation dropped.",
    "工場見学の配信をしたよ! 評判が {gain} 上がった。": "Streamed a factory tour! Reputation up by {gain}.",
    "どこも「まず飛んでから来てくれ」って。実績がないと話も聞いてもらえないわ。":
        "Everyone says \"come back after you've flown.\" No track record, no meetings.",
    "この前ピッチしたばかりよ。3ヶ月は空けないと、投資家も会ってくれない。":
        "We just pitched. Investors won't see us again for 3 months.",
    "(投資家に)俺たちは、戻ってくるロケットで宇宙を安くする。":
        "(to investors) We'll make space cheap with rockets that come back.",
    "{amount}M$ 集まったわ。": "We raised {amount}M$.",
    "今の工場じゃ、これ以上は人を置けないわ。": "This factory can't hold any more people.",
    "腕のいい溶接工を一人採用したわ。来月から AP が 1 増える。":
        "Hired a skilled welder. AP goes up by 1 from next month.",
    "固定費は月 {cost:.1f}M$ になったわよ。": "Fixed costs are now {cost:.1f}M$ a month.",
    "飛ばせる機体がないわ。「製造」で新しい Eagle 1 を作って。":
        "We have no rocket to fly. \"Build\" a new Eagle 1.",
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
}

# 挿絵プロンプト

会話の途中で出す挿絵(1枚絵)を作るためのプロンプト。**新しい挿絵が必要になったら、このファイルに追記する。**

## 置き場所と番号の決まり

| もの | 置き場所 |
|---|---|
| プロンプト | このファイル(`art/illustrations/prompts.md`) |
| できた絵 | `assets/illustrations/s<番号2桁>_<名前>.png`。枝番があれば `s<番号2桁>_<枝番>_<名前>.png`(例: 6-1 → `s06_1_rocket.png`) |
| 台本の印 | `game/script.py` の `IMAGES` に番号と説明を足し、出す位置に `("image", "番号")` の行を入れる |

- 番号は通し番号。いまの最後は 10。次の挿絵は **11** から(ステージが変わっても続けて振る)
- 1つの場面の中で絵を重ねる・差し替えるときは枝番(6-0, 6-1, …)
- 見出しは「### <番号>. <場面>(<出す位置>)」。下の「共通設定」を先頭に付けて使う
- 絵ができたら `assets/illustrations/` に置く。ランチャーの「会話の通し読み」で【画像 …】をクリックすると開ける
- 各依頼の見出しに状態の印を付ける。作ったら印を ✅ に変え、下の一覧も直す

## 依頼の一覧(状態)

印: ⬜ 未完了(作ってほしい) / 🔁 作り直し(理由を見て、もう一度作る) / 🟨 監査待ち(画像は保存済み) / ✅ 完了 / ➖ 作らない

**挿絵**

| 番号 | 内容 | 状態 | できた絵(`assets/illustrations/`) |
|---|---|---|---|
| 1 | 創業の日 | ✅ | `s01_kickoff.png` |
| 2 | オメガ島の射場・導入カット | ✅ | `s02_island.png` |
| 3 | 島流しのボヤキ | ✅ | `s03_breakroom.png` |
| 4 | 夢のような開発環境 | ✅ | `s04_teststand.png` |
| 5 | 資金の話 | ✅ | `s05_money.png` |
| 6-0 | Eagle 1 自慢: 射点の前の一同 | ✅ | `s06_0_team.png` |
| 6-1 | ウィンドウ: 全身 | ✅ | `s06_1_rocket.png` |
| 6-2 | ウィンドウ: エンジン | ✅ | `s06_2_engine.png` |
| 6-3 | ウィンドウ: タンクの溶接 | ✅ | `s06_3_weld.png` |
| 6-4 | ウィンドウ: 電子機器ベイ | ✅ | `s06_4_avionics.png` |
| 6-5 | ウィンドウ: スペック表示用 | ✅ | `s06_5_spec.png` |
| 7 | ディーロンが操縦する理由 | ✅ | `s07_reason.png` |
| 8 | 子供の頃の夢・回想 | ✅ | `s08_dream.png` |
| 9 | ノアの確認・伏線 | ✅ | `s09_noah.png` |
| 9-1 | モニターの「dylon_pilot_v0」 | ➖ 9 の絵にゲームが文字を重ねる | ― |
| 10 | 打ち上げ直前 | ✅ | `s10_prelaunch.png` |

**設定資料**(挿絵を作るときに渡す参照画像。下の「設定資料」の章)

- **ロケット(R1〜R6 と分離後)**: 正面・側面・上面・パースを **1 枚にまとめる**
- **場所(R7〜R9)**: 1 方向ずつ別ファイルで作る(側面 `_side` / 正面 `_front` / 上面 `_top` / パース `_persp` の 4 枚)。前に作った 1 枚版は、分けた絵を作るときの参照画像として使う

| 記号 | 内容 | 状態 | できた絵(`art/illustrations/ref/sheets/`) |
|---|---|---|---|
| R1 | Eagle 1 | ✅ | `r1_eagle1.png` |
| R2 | Eagle 9(使い捨て版と回収版) | ✅ | `r2_eagle9.png` |
| R3 | Eagle Heavy | ✅ | `r3_eagle_heavy.png` |
| R4 | Mega Booster + Space Ship | ✅ | `r4_mega_booster.png` |
| R5 | Hopper | ✅ 参照写真なしで作った | `r5_hopper.png` |
| R6 | Phoenix(カプセル) | ✅ | `r6_phoenix.png` |
| R7 | オメガ島の射場 | 1 枚版 ✅ / 1 方向ずつ ✅ | `r7_omega_island.png`(1 枚版)、`r7_omega_island_<向き>.png` |
| R8 | ミハシラの射場 | 1 枚版 ✅ / 1 方向ずつ ✅ 腕を開いた版と閉じた版で 4 枚ずつ | `r8_mihashira.png`(1 枚版)、`r8_mihashira_open_<向き>.png` / `r8_mihashira_closed_<向き>.png` |
| R9 | 台船 | 1 枚版 ✅ / 1 方向ずつ ✅ | `r9_droneship.png`(1 枚版)、`r9_droneship_<向き>.png` |
| R1-1 | Eagle 1 分離後(1段目 / 2段目) | ✅ | `r1_1_eagle1_separated.png` |
| R2-1 | Eagle 9 分離後(1段目 / 2段目 / フェアリング) | ✅ | `r2_1_eagle9_separated.png` |
| R2-2 | Eagle 9 着陸時の1段目(グリッドフィンと着陸脚を開いた形。側面・正面・上面・パース) | ✅ | `r2_2_eagle9_landing.png` |
| R3-1 | Eagle Heavy 分離後(サイドブースター / センターコア / 2段目) | ✅ | `r3_1_eagle_heavy_separated.png` |
| R4-1 | Mega Booster + Space Ship 分離後 | ➖ R4 に、それぞれ単体の図が入っている | ― |
| R6-1 | Phoenix 分離後(カプセル / トランク) | ➖ R6 に、それぞれ単体の図が入っている | ― |

**ADV 画面の部品**(会社画面。下の「ADV 画面の部品」の章。画面の型 A / B / C ごとに 1 枚ずつ)

| 記号 | 内容 | 状態 | できた絵(`assets/backgrounds/`) |
|---|---|---|---|
| B0 | 場面: 創業の日の借りオフィス(キックオフ) | ⬜ A / B / C | `b0_kickoff_<型>.png` |
| B1 | 場面: オメガ島の格納庫(Chapter 1・Eagle 1) | ⬜ A / B / C | `b1_hangar_omega_<型>.png` |
| B2 | 場面: 大きな組立工場(Chapter 2〜3・Eagle 9 / Hopper) | ⬜ A / B / C | `b2_factory_<型>.png` |
| U1 | 下の操作パネル(会話の窓とコマンドの後ろ) | ⬜ A / B / C | `u1_panel_<型>.png` |
| U2 | 上のステータス欄 | ⬜ A / B / C | `u2_status_<型>.png` |

---

## オープニング(シーン1〜10)

引き継ぎ資料 `space_ship_opening.md` の挿絵プロンプトを、今のゲームに合わせて直したもの。台本はゲームに入っている版(`game/script.py` の `KICKOFF` / `PROLOGUE` と、1-1・1-2 成功後の会話)。

合わせたこと:

- **絵柄**: アニメ調ではなく、ゲームと同じ**レトロなドット絵**(Pyxel 標準16色 + 減色・ディザ)
- **人物**: 今の会話用キャラ絵(`assets/portraits/`、胸から上)の見た目に合わせる。ノアは AI で、**顔がモニターの小型ロボット**
- **Eagle 1**: 史実の Falcon 1 に合わせる(全長 21m、直径 1.7m、2段式、白い細身の機体)
- **シーン1(創業の日)** はゲーム内にすでに絵がある(`game/kickoff.py`)。新しく描く場合も、この構図(マリアッチ4人・マラカスを振り上げるディーロン・右奥で手拍子する仲間)に合わせる

## 共通設定

**共通スタイル(全プロンプトの先頭に付ける)**
```
retro 16-bit pixel art, limited 16-color palette, ordered dithering, crisp pixels, no anti-aliasing, flat lighting with simple shading, 4:3 aspect ratio, original characters, video game scene
```

**パレット(生成後にこの16色へ減色すると、ゲームでそのまま使える)**
```
000000 2B335F 7E2072 19959C 8B4852 395C98 A9C1FF EEEEEE D4186C D38441 E9C35B 70C6A9 7696DE A3A3A3 FF9798 EDC7B0
```

**ネガティブプロンプト(対応しているAIのみ)**
```
anime, photorealistic, 3d render, smooth gradients, text, watermark, logo, signature, blurry, real person likeness, brand names
```

**キャラクター外見(今のキャラ絵より)**

| キャラ | 外見プロンプト |
|---|---|
| ディーロン | `Dylon: man in his late 30s, short messy dark brown hair, light stubble, tired but excited grin, plain dark navy T-shirt` |
| マヤ | `Maya: young woman, long black hair loosely tied back, sharp calm eyes, dark maroon work jacket over a dark shirt` |
| ケン | `Ken: young man, wild spiky orange-blond hair, huge grin, over-ear headphones with a boom microphone, blue T-shirt` |
| サラ | `Sara: woman with a brown bob haircut, skeptical tired expression, brown cardigan over a white collared blouse` |
| ノア | `Noah: small boxy robot whose head is an old CRT monitor showing a simple smiling cyan pixel face, short antenna, off-white metal body` |

ディーロンは実在の起業家に似せないよう、`original character` と `real person likeness` の除外を必ず付ける。

## プロンプト

### 1. 創業の日(シーン1) ✅
ゲーム内の絵(`game/kickoff.py`)を使う。描き直す場合:
```
[共通スタイル] [Dylon] [Ken] [Maya] [Sara] [Noah]
An empty rented office with white walls, fluorescent ceiling lights and bare gray carpet, no furniture, one whiteboard with "MARS" scribbled and a drawing of a red planet. A four-piece mariachi band in black suits with silver trouser studs and red bow ties plays guitars, a violin and a large guitarron. Dylon raises a maraca high and dances. Ken, Maya and Sara clap in the back, Noah the small robot stands beside them. Comedic, warm, hopeful.
```

### 2. オメガ島の射場・導入カット(シーン2 冒頭) ✅
```
[共通スタイル]
Side-view establishing shot of a tiny tropical island in the Pacific: a flat sandy launch site, a slender white two-stage rocket (21 m tall, 1.7 m wide, thin black band between stages) on a small pad beside a lattice service tower, a small gray hangar, a satellite dish, palm trees, a short pier with a small supply ship, turquoise sea, early morning sky. No people.
```

### 3. 島流しのボヤキ(シーン2 前半) ✅
```
[共通スタイル] [Ken] [Maya] [Sara] [Noah]
Break area next to the launch site at dusk: a makeshift table under a corrugated metal roof, instant noodle cups and coffee cans, a single string of light bulbs. Ken slumps on the table staring at the sea, Maya leans on a crate grinning, Sara stands with a tablet and a dry look, Noah the robot sits on a stool with its screen face showing a flat line mouth. The rocket in the distance against an orange sunset.
```

### 4. 夢のような開発環境(シーン2 後半) ✅
```
[共通スタイル] [Maya] [Noah]
Engine test stand on the island at night: a rocket engine fires horizontally with a bright orange flame and white steam. Maya watches with shining eyes, goggles on her forehead. Noah the robot stands beside her, its screen face showing scrolling graphs and a small smile.
```

### 5. 資金の話(シーン3) ✅
```
[共通スタイル] [Sara] [Dylon] [Ken]
Small control room with monitors and a whiteboard showing a hand-drawn line of money falling to zero over 33 months. Sara points at the graph, serious. Dylon sits backwards on a chair, smiling. Ken holds his head.
```

### 6. Eagle 1 自慢(シーン4・5)
拡大ウィンドウはゲーム側で重ねる。背景とウィンドウ内の絵を別に作る。

**6-0. 背景(射点の前の一同) ✅**
```
[共通スタイル] [Maya] [Noah] [Ken] [Sara] [Dylon]
View from behind the five characters at the foot of the launch pad. They stand together in the left foreground, seen from behind or a slight rear three-quarter angle, and face the slender white two-stage rocket on the pad AHEAD of them, beside its service tower. The rocket rises around the center of the left two-thirds of the image, clearly separate from the group. Maya is at the far left, her right arm stretched up and to the right so that her index finger points directly at the white rocket, not the service tower. Ken, Sara and Dylon tilt their heads up toward that same rocket. Noah turns the back of its CRT monitor head toward the viewer and faces the rocket with the group. Nobody faces the camera. Bright midday tropical light. Keep the right third of the image mostly empty sky for a UI window; nobody points or looks toward that empty area.
```
マヤの頭の高さはケンと同程度か少し低めにし、1人だけ大きく描かない。腕は2本だけ。右腕は肘を曲げ、手を自分の頭の近くに置いてロケットの方向を指す。長い一直線の腕にしない。左腕は画面左側の体の横に自然に下ろす。ケン側にもう1本下向きの腕を描かない。指す方向と5人全員の視線の先にはロケットを置く(塔や右の空いた部分を見ない)。5人は背中をカメラに向け、ロケットは5人の前方に置く。
ロケットの形は、設定資料 R1(Eagle 1)を参照画像として一緒に渡す。細い白い2段式で、細い黒い段間帯と底部のエンジン1基だけを描く。尾翼・補助ブースターは付けない。

**6-1. ウィンドウ: 全身 ✅**
```
[共通スタイル]
Side view of a slender white two-stage rocket, 21 m tall and 1.7 m wide, thin black interstage band, small nose fairing, standing on a launch pad, full body visible, faint blueprint grid behind. Plain composition for a small inset window.
```

**6-2. ウィンドウ: エンジン(Hobby) ✅**
```
[共通スタイル]
Close-up of a single kerosene and liquid oxygen rocket engine under the rocket: a bell nozzle, turbopump and pipes, heat-tinted metal in blue and bronze.
```

**6-3. ウィンドウ: タンクの溶接 ✅**
```
[共通スタイル]
Close-up of the rocket's aluminum tank, one smooth circular weld seam across the cylinder with a thin line of light running along it, small inspection marks next to the weld.
```

**6-4. ウィンドウ: 電子機器ベイ(ノア担当) ✅**
```
[共通スタイル]
Cutaway of the avionics bay under the nose fairing: three identical flight computer boxes side by side, neat wiring, small blue status lights, cool blue colors.
```

**6-5. ウィンドウ: スペック表示用 ✅**
```
[共通スタイル]
Side-view silhouette of the slender white two-stage rocket on a dark navy background with faint blueprint lines, empty space on the right for spec text.
```
スペック(全長 21m / 2段式 / 低軌道に最大 670kg)の文字はゲーム側で重ねる。

### 7. ディーロンが操縦する理由(シーン5) ✅
```
[共通スタイル] [Dylon] [Noah] [Maya]
Inside the control room, Dylon stands with one hand on a flight joystick on the console, determined. This is a ground control room inside a small prefab building on the tropical launch island, not a spaceship cockpit: the windows show the launch pad and the sea, never outer space or Earth from orbit. Noah the robot faces him from beside the monitors, its screen face showing a calm neutral expression. Maya leans on the wall behind, conflicted.
```

### 8. 子供の頃の夢・回想(シーン6) ✅
```
[共通スタイル] [young Dylon as a 9-year-old boy with messy dark brown hair]
Flashback: a small bedroom at night, a boy on the floor drawing a Mars colony map with crayons (domed cities, red sand roads, a tiny blue Earth in the sky). An old CRT TV in the corner shows a hero flying with a rocket pack, silhouette only. Rocket drawings on the walls. Warm sepia-tinted colors.
```
劇中の映画は架空の『ジェットパック・ヒーロー』。実在の映画のキャラやロゴが描かれないよう、シルエットだけにする。

### 9. ノアの確認・伏線(シーン7) ✅
```
[共通スタイル] [Noah] [Dylon]
Dim control room late at night, only monitor light. This is a ground control room inside a small prefab building on the tropical launch island, not a spaceship cockpit: the windows show the launch pad and the sea, never outer space or Earth from orbit. Noah the robot sits among screens of flight graphs and code, its screen face turned halfway toward Dylon, calm and unreadable. Dylon stands behind with hands in pockets, smiling confidently. On a small monitor in the corner, a neural network diagram glows faintly. Quiet, slightly ominous, cool blue tones.
```
「dylon_pilot_v0」の文字はゲーム側でモニターに重ねる。

### 10. 打ち上げ直前(シーン8) ✅
```
[共通スタイル]
The slender white two-stage rocket on the island launch pad at twilight, venting white vapor, floodlights on, the service tower beside it, the ocean behind, the first stars appearing. No people.
```

## ADV 画面の部品

会社画面(ADV パート)の見た目を、いまのプログラムで描いた絵からイラストに替える。
画面はいくつかの部分に分かれていて、**部分ごとに別の絵**にする。会話の窓・コマンドのボタン・文字・立ち絵・機体は、今までどおりゲームが上に描く。

### 画面の分け方

```
┌────────────────────────┐ ← y = 0
│ U2 ステータス欄(日付・資金など) │
├────────────────────────┤
│                                │
│ B 場面(格納庫・オフィスなど)  │
│ [立ち絵]           [機体]      │
│                                │
├────────────────────────┤ ← 場面の下の端
│ U1 下の操作パネル               │
│  ┌ 会話の窓 ───────────┐  │
│  └──────────────────┘  │
│  [製造][点検][打上][調達][待機] │
└────────────────────────┘ ← 画面の下の端
```

### 画面の型と、部分ごとの大きさ(ピクセル)

画面サイズは 4 種類あるが、絵は **3 つの型**で作る。360x360 は 720x720 とほぼ同じ並びを半分にしたもの(1 ピクセルの差だけ)なので、A の絵を半分に縮めて使う。

| 型 | 使う画面 | U2 ステータス欄 | B 場面 | U1 下の操作パネル |
|---|---|---|---|---|
| **A** | 720x720(と、半分にして 360x360) | 720 × 61 | **720 × 371** | 720 × 288 |
| **B** | 640x480 | 640 × 29 | **640 × 289** | 640 × 162 |
| **C** | 320x240 | 320 × 31 | **320 × 93** | 320 × 116 |

- 上から順に、すき間なく積む(A なら 61 + 371 + 288 = 720)
- **依頼する大きさは、表の 2 倍**(A の場面なら 1440 × 742)。ゲームが半分に縮めて使う。縦横の比はちょうど 2 倍に合わせる
- 型ごとに横と縦の比が違う(場面は A が 1.94:1、B が 2.21:1、C が 3.44:1)。切り抜きでごまかさず、**型ごとに構図を作る**

### U1 の中でゲームが描くもの(参考)

| 型 | 会話の窓 | コマンドのボタン(5 個を横に並べる) |
|---|---|---|
| A | 左右 12 の余白で幅 696、高さ 172(パネルの上から 24 の位置。名前の札が窓の上に 28 はみ出す) | パネルの上から 212、高さ 64 |
| B | 左右 16 の余白で幅 608、高さ 92(パネルの上から 12) | パネルの上から 114、高さ 36 |
| C | 左右 6 の余白で幅 308、高さ 70(パネルの上から 8) | パネルの上から 84、高さ 28 |

U1 は、窓とボタンの後ろに見える「台」や「壁」の絵。細かい模様は窓に隠れるので、**落ち着いた暗い色の、ほぼ一様な面**にする(机の天板、操作卓、暗い金属板など)。

### B 場面で、ゲームが上に重ねるもの(絵に描かないで、場所を空けておく)

位置は、型ごとの場面の絵の中のピクセル(表の 1 倍の大きさで書いた値。依頼する 2 倍の絵では 2 倍にする)。

| 重ねるもの | A(720 × 371) | B(640 × 289) | C(320 × 93) | 絵に描くもの |
|---|---|---|---|---|
| 床の線(床と壁の境目) | 上から 292 | 上から 219 | 上から 70 | ここに床と壁の境目をそろえる。ゲームはこの線の上に機体を立てる |
| 話している人の立ち絵 | 左 16〜144、上から 238〜366 | 左 24〜152、上から 153〜281 | 左 8〜72、上から 27〜91 | 隠れても困らない壁・机 |
| 機体と足場 | 左 495〜563(中心 529)、上から 78〜292 | 左 440〜500(中心 470)、上から 29〜219 | 左 198〜218(中心 208)、上から 9〜70 | **何も置かない**。奥に開いた扉と外の景色 |
| 開いた扉(機体の奥) | 左 405〜686 | 左 360〜610 | 左 173〜253 | 扉の中に外の景色 |
| ホワイトボードの文字 | 左 180〜349、上から 80〜181 | 左 160〜310、上から 30〜120 | 左 109〜157、上から 10〜39 | **何も書いていない白いホワイトボード** |

- C は縦がとても低い(93)。立ち絵が場面の高さのほとんどを覆うので、左側は単純な壁でよい
- 場面の絵に人物と文字は描かない(人物は立ち絵、文字はゲームが書く)
- B0(キックオフ)は格納庫ではないので、機体・扉・ホワイトボードの欄は使わない。床の線と立ち絵の位置だけ合わせる

### 共通スタイル

**場面(B0〜B2)の先頭に付ける。** `[幅]` `[高さ]` `[床]` は型ごとの依頼サイズ(2 倍)に置き換える。
```
retro 16-bit pixel art, limited 16-color palette, ordered dithering, crisp pixels, no anti-aliasing, flat lighting with simple shading, background for a visual-novel style game screen, exactly [幅]x[高さ] pixels, side view of an interior with a flat back wall, the floor line at [床] pixels from the top, no people, no text, no logos
```

| 型 | `[幅]x[高さ]` | `[床]` |
|---|---|---|
| A | 1440x742 | 584 |
| B | 1280x578 | 438 |
| C | 640x186 | 140 |

**U1・U2 の先頭に付ける。**
```
retro 16-bit pixel art, limited 16-color palette, crisp pixels, no anti-aliasing, a flat user-interface background strip for a game screen, exactly [幅]x[高さ] pixels, dark and calm colors, low contrast, simple texture, no text, no icons, no buttons, no people
```

### B0. 創業の日の借りオフィス ⬜
挿絵 1(`assets/illustrations/s01_kickoff.png`)を参照画像として渡し、同じ部屋を描く。キックオフの会話のあいだの場面。
```
[場面の共通スタイル]
An empty rented office on its first day: white walls, fluorescent ceiling lights, bare gray carpet, no furniture except one blank whiteboard on the wall. Leave the floor empty for the characters. Same room as the attached illustration.
```
マリアッチ楽団を絵に入れるかは、今の `game/kickoff.py` の動き(楽団が揺れる)を残すかで決める。入れない場合は、楽団はゲームが重ねる。

### B1. オメガ島の格納庫 ⬜
参照画像: 設定資料 R7(`ref/sheets/r7_omega_island.png`)、挿絵 2(`s02_island.png`)。Chapter 1(Eagle 1)の場面。
```
[場面の共通スタイル]
Inside a small gray metal hangar on a tiny tropical launch island, seen from the side. Corrugated metal back wall with a few work lights. On the right, a tall open hangar door from the floor up to near the ceiling, showing a bright tropical sky, palm trees and the turquoise sea outside; the floor in front of the door is empty (a rocket will be placed there by the game). On the upper left wall, a blank whiteboard. Lower left: a simple workbench with tools and a laptop. Concrete floor with yellow safety lines.
```
扉・ホワイトボード・空ける場所は、上の「ゲームが上に重ねるもの」の表の位置に合わせるよう、プロンプトに数字で書き足す(例: A なら `the open door spans x 810 to 1372, the whiteboard spans x 360 to 698 and y 160 to 362, keep x 990 to 1126 empty above the floor`)。

### B2. 大きな組立工場 ⬜
参照画像: 設定資料 R2(`ref/sheets/r2_eagle9.png`)、R5(`ref/sheets/r5_hopper.png`)、実物写真 `ref/real/falcon9_pad39a_vertical.jpg`。Chapter 2〜3(Eagle 9・Hopper)の場面。
```
[場面の共通スタイル]
Inside a large, clean rocket assembly factory, seen from the side: tall white walls, overhead crane rails, rows of ceiling lights, a polished gray floor with painted work zones. On the right, a very tall empty assembly bay with a huge open door showing the sky and a launch tower in the distance; the bay floor is empty (the game places an Eagle 9 or a Hopper there). On the upper left wall, a blank whiteboard. Lower left: engineering desks with monitors and a stack of engine parts.
```
B1 と同じく、扉・ホワイトボード・空ける場所の位置を数字で書き足す。

### U1. 下の操作パネル ⬜
会話の窓とコマンドのボタンの後ろ。どの場面でも共通。
```
[U1・U2 の共通スタイル]
The surface of a dark navy metal control desk seen from the front, with faint panel seams and a few small rivets near the edges, a thin lighter edge along the top border.
```

### U2. 上のステータス欄 ⬜
日付・資金・評判などの文字の後ろ。どの場面でも共通。文字が読めるよう、とても暗く平らにする。
```
[U1・U2 の共通スタイル]
A very dark navy horizontal header bar with a subtle metallic texture and a thin blue line along the bottom edge.
```

### ゲーム側の対応(絵がそろったら)

- 部分ごとの絵を読み込んで、型に合わせて置く(いまは `game/scene_office.py` の `draw_status()` / `draw_hangar()` と `game/kickoff.py` がプログラムで描いている)
- 依頼した 2 倍の絵を半分に縮め、ゲームのパレットに合わせて色を減らす
- 360x360 は A の絵をさらに半分にして使う
- ホワイトボードの文字・機体・足場・立ち絵・会話の窓・ボタンは、今までどおりゲームが上に描く

## 設定資料

挿絵の中の機体や場所の形がぶれないように、先に設定資料(参照画像)を作る。挿絵を作るときは、写っている機体・場所の設定資料を参照画像として一緒に渡す。

**設定資料の決まり(全部共通)**

- **背景なし**(透明、または真っ白)。地面・空・海・影・格子も描かない
- **ロケット(R1〜R6 と、その分離後)は 1 枚にまとめる**: 正面図・側面図・上面図を同じ縮尺で横に並べ、斜め上から見たパース図を右側か下に大きめに置く(下の「ロケットの共通スタイル」)
- **場所(R7〜R9)は 1 方向ずつ別ファイル**: 1 つにつき 4 枚(側面図 `_side` / 正面図 `_front` / 上面図 `_top` / パース図 `_persp`)。1 枚には 1 方向だけを描く(下の「場所の共通スタイル」)
  - 画像の大きさは 4 枚とも **1024 × 1024 px**。対象を真ん中に置き、まわりに少し余白を残す
  - 側面・正面・上面の 3 枚は**同じ縮尺**にする
  - **作る順番**: まず側面図を作る。正面図・上面図・パース図は、できた側面図を参照画像として一緒に渡して作る
  - 前に作った 1 枚版(`r<番号>_<名前>.png`)も参照画像として渡す
  - 版が 2 つあるもの(R8 の腕を開いた版と閉じた版)は、版ごとに 4 枚ずつ作る
- 文字・寸法線・ロゴ・旗・社名は入れない(大きさはプロンプトで伝える)
- 色は少なく、はっきり。挿絵と同じパレット(上の「共通設定」)の色を使う
- 本物の写真(`art/illustrations/ref/real/`、出典は同じ場所の `SOURCES.md`)を参照画像として一緒に渡す。形は写真に合わせ、マークや文字はまねしない
- できた絵は `art/illustrations/ref/sheets/` に、上の一覧のファイル名で置く。そろったら一覧と見出しの印を ✅ にする
- 段やブースターが分かれる機体は、**分かれたあとの設定資料も作る**(枝番 R1-1 など)。分離前の設定資料を必ず参照画像として一緒に渡し、形・色・太さ・縮尺をそろえる

**ロケットの共通スタイル(R1〜R6 と分離後のプロンプトの先頭に付ける)**
```
game design reference sheet, isolated on a plain white or transparent background, no background scenery, no ground, no sea, no sky, no shadows, orthographic front view, side view and top view drawn at the same scale and aligned side by side, plus one larger three-quarter perspective view from slightly above, clean flat colors with simple shading, crisp outlines, no text, no labels, no dimension lines, no logos, no flags
```

**場所の共通スタイル(R7〜R9 のプロンプトの先頭に付ける)**

`[向き]` のところを、作る絵に合わせて下の表の英語に置き換える。
```
game design reference image, a single view only, [向き], one object centered on a 1024x1024 canvas with a small margin, isolated on a plain white or transparent background, no background scenery, no ground, no sea, no sky, no shadows, clean flat colors with simple shading, crisp outlines, no text, no labels, no dimension lines, no logos, no flags, do not show any other views
```

| 向き | ファイル名 | `[向き]` に入れる英語 |
|---|---|---|
| 側面図 | `_side` | `orthographic side view (profile), camera level with the object, no perspective` |
| 正面図 | `_front` | `orthographic front view, camera level with the object, no perspective` |
| 上面図 | `_top` | `orthographic top view, looking straight down, no perspective` |
| パース図 | `_persp` | `three-quarter perspective view from slightly above` |

側面図以外を作るときは、プロンプトの最後に次を付けて、できた側面図を一緒に渡す。
```
Same object as the attached side view: keep exactly the same shapes, proportions, colors and markings. Use the same scale as the attached side view.
```

### R1. Eagle 1 ✅
参照写真: `falcon1_omelek_launch.jpg`, `falcon1_omelek_flight5.jpg`(元ネタ: Falcon 1)
```
[ロケットの共通スタイル]
A small two-stage orbital rocket, 21 m tall and 1.7 m in diameter (very slender). White body. First stage 14 m long with one kerosene/LOX engine and a dark bell nozzle. A thin black interstage band. Second stage 7 m long including a small pointed payload fairing on top. The second stage has the same shape whether attached or separated. No side boosters, no fins, no colored stripes.
```

### R2. Eagle 9 ✅
参照写真: `falcon9_pad39a_vertical.jpg`, `falcon9_landing_lz1.jpg`, `droneship_landing.jpg`(元ネタ: Falcon 9)
```
[ロケットの共通スタイル]
A medium two-stage rocket, 3.7 m in diameter: first stage 30 m with nine engines in a 3x3 grid at the base, black interstage, second stage 9 m, payload fairing on top. White body. Draw two versions: (A) expendable version, clean white; (B) reusable version with four landing legs folded along the base of the first stage and four lattice grid fins near the top of the first stage, slightly sooty. Also show version B's first stage alone with the legs deployed.
```

### R3. Eagle Heavy ✅
参照写真: `falcon_heavy_demo.jpg`(元ネタ: Falcon Heavy)
```
[ロケットの共通スタイル]
A heavy-lift rocket made of three Eagle 9 first stages side by side (a center core plus two side boosters, each 3.7 m wide), with one second stage and a payload fairing on the center core. Each core has nine engines, folded landing legs and grid fins. The two side boosters have conical white nose caps.
```

### R4. Mega Booster + Space Ship ✅
参照写真: `starship_full_stack.jpg`, `mechazilla_booster_return.jpg`(元ネタ: Super Heavy + Starship)
```
[ロケットの共通スタイル]
A super-heavy fully reusable two-stage rocket, about 120 m tall and 9 m in diameter, bare brushed stainless steel. Lower stage "Mega Booster": a tall steel cylinder with many engines at the base and four grid fins near the top. Upper stage "Space Ship": a steel body with black hexagonal heat-shield tiles on one side, two small forward flaps near the nose and two larger aft flaps. Draw the full stack, and each stage separately.
```
前方フラップは側面図でも幅のある台形の板として描く。ブースターのグリッドフィンは上端付近に付く独立した4枚の格子翼で、四角い枠の内側に格子を見せる。連続した輪や塔の腕の形にしない。

### R5. Hopper ✅
参照写真: `grasshopper.jpg`(**まだ取れていない**)(元ネタ: Grasshopper)
```
[ロケットの共通スタイル]
A rocket landing test vehicle: a single first stage 18 m tall and 3.7 m in diameter, gray and white, one engine at the bottom, four fixed spidery landing legs made of steel struts, and a short black dome cap on top instead of a payload.
```

### R6. Phoenix ✅
参照写真: `dragon_crs14.jpg`, `falcon9_pad39a_vertical.jpg`(元ネタ: Dragon)
```
[ロケットの共通スタイル]
A cargo space capsule 3.7 m wide: a white blunt cone with a black heat shield on the flat bottom, small round windows, small thruster ports around the side, a nose cap that opens. Below it, a white cylindrical cargo trunk with solar panels. Draw the capsule alone, and the capsule with the trunk.
```

### R7. オメガ島の射場 — 1枚版 ✅ / 1方向ずつ ⬜
参照写真: `omelek_aerial.jpg`, `falcon1_omelek_launch.jpg`, `falcon1_omelek_flight5.jpg`(元ネタ: クェゼリン環礁のオメレク島)
```
[場所の共通スタイル]
A tiny flat tropical coral island used as a small rocket launch site, shown as an isolated diorama cut out from the sea: a small launch pad with a lattice service tower, a small gray hangar, a prefab control building with windows facing the pad, a satellite dish, white fuel tanks, a short pier, a few palm trees on white sand. The island is only about 200 m across. The rocket on the pad must match the attached Eagle 1 reference sheet exactly: plain white, one thin black interstage band, no fins.
```
作り直しのときは、R1(`r1_eagle1.png`)も参照画像として一緒に渡す。

### R8. ミハシラの射場 — 1枚版 ✅ / 1方向ずつ ⬜
参照写真: `mechazilla_booster_return.jpg`, `starship_full_stack.jpg`(元ネタ: Starbase の発射塔メカジラ)。**塔だけが写った写真がまだ足りない**
```
[場所の共通スタイル]
A very tall steel launch-and-catch tower, about 145 m high, made of a square lattice frame, with two huge horizontal arms ("chopsticks") that slide up and down the tower and swing to catch a returning booster in mid-air. Beside the tower, a ring-shaped launch mount on six legs over a flame trench. Draw the arms both open and closed.
```

### R9. 台船 — 1枚版 ✅ / 1方向ずつ ⬜
参照写真: `droneship_jrti.png`, `droneship_landing.jpg`(元ネタ: SpaceX の ASDS)
```
[場所の共通スタイル]
An uncrewed ocean landing barge for rocket boosters, shown without water as an isolated object: a flat rectangular deck about 90 m by 50 m, dark gray with a large white circular landing target in the middle, low blast walls at both ends, thruster pods and small equipment containers at the corners.
```

### 分離後の設定資料

段やブースターが分かれたあとの姿。**分離前の設定資料(R1 など)を参照画像として必ず一緒に渡す。** 分離前の絵と見比べたときに、同じ機体だとわかるようにする。

- ロケットなので、1 枚にまとめる。部品ごとの正面・側面・上面・パースと、部品を元の重なり順に並べた図を 1 枚に入れる

**分離後の共通指示(各プロンプトの [ロケットの共通スタイル] のあとに付ける)**
```
This sheet shows the same vehicle as the attached reference sheet, after separation. Keep every part exactly identical to the reference sheet: same shapes, proportions, colors, markings, line style and the same scale. Draw each separated part on its own with front, side and top views plus one perspective view, and add one small view of the parts lined up in their original stacking order with small gaps between them, so the separation points are clear.
```

### R1-1. Eagle 1 分離後 ⬜
参照画像: `ref/sheets/r1_eagle1.png`(必ず)、`ref/real/falcon1_omelek_launch.jpg`
```
[ロケットの共通スタイル] [分離後の共通指示]
Eagle 1 split at the thin black interstage band. Part 1: the first stage (14 m), with the black interstage ring staying on top of the first stage as an open hollow ring, and the single main engine at the bottom. Part 2: the second stage with the small pointed payload fairing on top, and its own small upper-stage engine nozzle now visible at the bottom (it was hidden inside the interstage before separation).
```

### R2-1. Eagle 9 分離後 ⬜
参照画像: `ref/sheets/r2_eagle9.png`(必ず)、`ref/real/falcon9_landing_lz1.jpg`
```
[ロケットの共通スタイル] [分離後の共通指示]
Eagle 9 (reusable version) split at the black interstage. Part 1: the first stage with the black interstage on top as an open hollow ring, four grid fins near the top, folded landing legs and nine engines; also draw it with grid fins and legs deployed. Part 2: the second stage with one large dark vacuum-engine nozzle visible at the bottom, and the payload fairing on top. Part 3: the payload fairing split into its two clamshell halves, drifting apart.
```

### R3-1. Eagle Heavy 分離後 ⬜
参照画像: `ref/sheets/r3_eagle_heavy.png`(必ず)、`ref/sheets/r2_eagle9.png`
```
[ロケットの共通スタイル] [分離後の共通指示]
Eagle Heavy after separation. Part 1: the two side boosters on their own, each with its conical white nose cap, four grid fins and folded landing legs. Part 2: the center core with the black interstage on top as an open hollow ring, grid fins and legs, and the attachment points on both sides where the side boosters were connected. Part 3: the second stage with its vacuum-engine nozzle visible and the payload fairing on top. The side boosters and the center core must look like the Eagle 9 first stage.
```

## 補足

- 生成した絵は、上のパレットへ減色してから使う(ゲームは 16 色 + 一部の追加色)
- ゲームの表示に合わせるなら、会話シーンの絵は 640x480 の画面で上側 640x290 前後(会社画面の背景の範囲)

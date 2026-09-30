# StarX (space_ship)

Pyxel 製のロケット経営×操縦ゲーム。
[pyxel_sandbox](https://github.com/airpocket-soundman/pyxel_sandbox) の `rocket/rocket_thrast_control.py` をベースに開発。

企画書: https://airpocket-soundman.github.io/space_ship/

## ブラウザで遊ぶ

[企画書ページ](https://airpocket-soundman.github.io/space_ship/)の冒頭のリンクから、[Pyxel Web Launcher](https://kitao.github.io/pyxel/wasm/launcher/) でこのリポジトリの main ブランチにある `web/starx.pyxapp` を動かせます。
画面サイズと言語は URL の `screen` / `lang` で選びます(`main.py` が読む)。
`web/starx.pyxapp` はゲーム一式を 1 ファイルにまとめたもので、main に push すると GitHub Actions が作り直します(手元では `python tools/build_pyxapp.py`)。

```
https://kitao.github.io/pyxel/wasm/launcher/?play=airpocket-soundman/space_ship/main/web/starx&packages=numpy&gamepad=enabled&screen=720x720&lang=en
```

## 遊び方(ローカル)

```
pip install pyxel
python main.py
```

画面サイズは 4 種類あり、どれもその解像度で直接描いています(拡大ではない)。

```
python main.py 640x480   # 既定
python main.py 720x720   # RGB20SX など正方形の画面
python main.py 360x360   # 720x720 の画面に 2 倍で出す用(文字・立ち絵が小さめ)
python main.py 320x240   # 640x480 の画面に 2 倍で出す用
```

`en` を付けると英語版になります(例: `python main.py 720x720 en`)。

現在のデモは Chapter 1-1「初飛行」から Chapter 3-6「二度目の空」まで遊べます。
会社画面に戻るたびに自動でセーブされ、タイトルの CONTINUE で続きから遊べます。

ステージ名を付けると、そのステージの直前の状態から始まります(動作確認用。セーブはしない)。

```
python main.py 3-1          # Hopper の着陸試験から
python main.py 720x720 2-3  # 画面サイズ・言語と組み合わせてもよい
```

| 章 | ステージ | やること |
|---|---|---|
| Ch1 軌道へ(Eagle 1) | 1-1 〜 1-5 | 高度 10 km → 100 km → 段分離と軌道投入 → 衛星の放出 |
| Ch2 宇宙輸送を商売にする(Eagle 9 + Phoenix) | 2-1 〜 2-5 | 新しい機体で軌道へ / カプセルの再突入 / ステーションへの接近 / 高い軌道 / 異常時の切り離し |
| Ch3 戻ってくるロケット(Hopper / Eagle 9 回収型) | 3-1 〜 3-6 | ホバースラム / 海面で静止 / 台船に着陸 / 発射場に帰還 / 回収した機体の再使用 |

### 操作

| 画面 | キー | 動作 |
|---|---|---|
| 共通 | SPACE / Z / Enter | 決定・会話を進める |
| 会社(ADV) | ← → | コマンド選択 |
| 打ち上げ(ACT) | SPACE | 点火。Ch1-3 からは、噴射中に押すと停止(点火できる回数は機体ごとに決まっている) |
| | Z | 段分離 / 荷物の放出 / パラシュート / 異常時のカプセル切り離し |
| | ↑ ↓ | スロットル(70% より下には絞れない) |
| | ← → | 姿勢(噴射中はジンバル、停止中はスラスター、降下中はグリッドフィン) |
| 近接操作(Ch2-3) | ← → ↑ ↓ | スラスター(押した向きへ加速) |
| | ESC | 終了 |

飛行中は、画面の上に「手順」(いまやること)、右下の窓に目標の条件(緑なら満たしている)が出ます。
宇宙を惰性で飛んでいるあいだは、自動で早送りになります(キーを押すと等速に戻る)。

## 構成

| パス | 内容 |
|---|---|
| `main.py` | エントリ |
| `game/app.py` | シーン切り替え |
| `game/scene_office.py` | ADV(会社)画面 |
| `game/scene_mission.py` | ACT(打ち上げ)画面 |
| `game/scene_misc.py` | タイトル・リザルト・ゲームオーバー |
| `game/scene_dock.py` | ACT(ステーションへの接近)画面 |
| `game/physics.py` | 飛行物理(Pyxel 非依存)。惑星は実物の約 1/10 の大きさ |
| `game/vehicles.py` | 機体の諸元(Eagle 1 / Eagle 9 / Phoenix / Hopper) |
| `game/missions.py` | ミッション定義・判定(Pyxel 非依存) |
| `game/docking.py` | 近接操作の判定(Pyxel 非依存) |
| `game/particles.py` | 炎・煙・爆発などのパーティクル |
| `game/rocket_art.py` | 機体の絵(打ち上げ画面と格納庫で共通) |
| `game/state.py` | 会社の状態とセーブ |
| `game/script.py` | 会話スクリプト |
| `game/portraits.py` | 立ち絵の読み込み |
| `game/i18n.py` / `game/lang_en.py` | 言語の切り替えと英語の訳(日本語の文言がキー) |
| `assets/portraits/` | 立ち絵 PNG |
| `assets/rockets/` | 格納庫に立てる Eagle 9 の絵(画面サイズごと) |
| `assets/fonts/` | 日本語フォント(umplus) |
| `tools/sim_check.py` | 全ステージのバランスをヘッドレスで確認(自動操縦で 20 回ずつ飛ばす。`python tools/sim_check.py 3-3` でステージ指定) |
| `tools/autoplay.py` | 自動操作でスクリーンショットを撮る(`python tools/autoplay.py 720x720 en` で画面サイズ・言語を指定。`python tools/autoplay.py 3-3 --fast` でステージ指定) |
| `tools/check_i18n.py` | 英語の訳が抜けている文言を探す |
| `tools/make_portraits.py` | 以前の仮の立ち絵を生成(実行すると `assets/portraits/<id>.png` を上書きするので注意) |
| `tools/make_rockets.py` | `art/redesign_proposal/falcon9_720.png` から、格納庫用の Eagle 9 の絵(`assets/rockets/`)を作る |
| `tools/make_logo.py` | `art/starx_logo.webp` から画面サイズごとのタイトルロゴ(`assets/logo_<画面サイズ>.png`)と企画書用ロゴ(`docs/img/starx_logo.png`)を作る |
| `prototype/` | 元になったプロトタイプ |

## 立ち絵の仕様

`assets/portraits/<id>.png` を置き換えると、そのまま会話画面に反映されます。
いまの絵は `art/redesign_proposal/` の `<id>_128.png` / `<id>_64.png`(`export_portraits.py` で書き出したもの)です。

- サイズ: **128×128 px** か **64×64 px**。表示枠は 128×128(360x360 / 320x240 の画面では 64×64)で、枠に合わせて拡大・縮小する。
- 小さい画面用に描いた絵を使いたいときは、`assets/portraits/<id>_64.png`(64×64 px)を置く。あれば小さい画面ではそちらを使う。
- 形式: PNG。背景込みの四角い絵(透過なし)。
- 色: Pyxel 標準の 16 色に合わせる。それ以外の色は読み込み時に近い色へ置き換わる。

  `000000 2B335F 7E2072 19959C 8B4852 395C98 A9C1FF EEEEEE D4186C D38441 E9C35B 70C6A9 7696DE A3A3A3 FF9798 EDC7B0`

- ファイル名(id):

  | id | 人物 | id | 人物 |
  |---|---|---|---|
  | `dylon` | ディーロン・マスク | `grey` | グレイ |
  | `maya` | マヤ・ホシノ | `doc_hughes` | ドク・ヒューズ |
  | `ken` | ケン・ドウジマ | `bolt` | ボルト |
  | `sara` | サラ・カネダ | `hashimoto` | ハシモト |
  | `noah` | ノア | `mimi` | ミミ |
  | `dylon_ai` | ディーロン AI | `gen` | ゲンさん |

## フォント

`assets/fonts/umplus_j10r.bdf` / `umplus_j12r.bdf` は Pyxel のサンプルに同梱されている umplus フォント(M+ フォント・東雲フォントをもとにした BDF フォント)です。

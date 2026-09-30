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

現在のデモは Chapter 1-1「初飛行」まで遊べます。

### 操作

| 画面 | キー | 動作 |
|---|---|---|
| 共通 | SPACE / Z / Enter | 決定・会話を進める |
| 会社(ADV) | ← → | コマンド選択 |
| 打ち上げ(ACT) | SPACE | 点火(Eagle 1 の1段目は1回だけ) |
| | ↑ ↓ | スロットル(70% より下には絞れない) |
| | ← → | 姿勢(ジンバル + スラスター) |
| | ESC | 終了 |

## 構成

| パス | 内容 |
|---|---|
| `main.py` | エントリ |
| `game/app.py` | シーン切り替え |
| `game/scene_office.py` | ADV(会社)画面 |
| `game/scene_mission.py` | ACT(打ち上げ)画面 |
| `game/scene_misc.py` | タイトル・リザルト・ゲームオーバー |
| `game/physics.py` | 飛行物理(Pyxel 非依存) |
| `game/missions.py` | ミッション定義・判定(Pyxel 非依存) |
| `game/state.py` | 会社の状態 |
| `game/script.py` | 会話スクリプト |
| `game/portraits.py` | 立ち絵の読み込み |
| `game/i18n.py` / `game/lang_en.py` | 言語の切り替えと英語の訳(日本語の文言がキー) |
| `assets/portraits/` | 立ち絵 PNG |
| `assets/fonts/` | 日本語フォント(umplus) |
| `tools/sim_check.py` | Ch1-1 のバランスをヘッドレスで確認 |
| `tools/autoplay.py` | 自動操作でスクリーンショットを撮る(`python tools/autoplay.py 720x720 en` で画面サイズ・言語を指定) |
| `tools/check_i18n.py` | 英語の訳が抜けている文言を探す |
| `tools/make_portraits.py` | 仮の立ち絵を生成 |
| `tools/make_logo.py` | `art/starx_logo.png` から画面サイズごとのタイトルロゴ(`assets/logo_<画面サイズ>.png`)と企画書用ロゴ(`docs/img/starx_logo.png`)を作る |
| `prototype/` | 元になったプロトタイプ |

## 立ち絵の仕様

`assets/portraits/<id>.png` を置き換えると、そのまま会話画面に反映されます。

- サイズ: **128×128 px** か **64×64 px**。表示枠は 128×128(360x360 の画面では 64×64)で、枠に合わせて拡大・縮小する。
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

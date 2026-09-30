# StarX (space_ship)

Pyxel 製のロケット経営×操縦ゲーム。
[pyxel_sandbox](https://github.com/airpocket-soundman/pyxel_sandbox) の `rocket/rocket_thrast_control.py` をベースに開発。

企画書: https://airpocket-soundman.github.io/space_ship/

## 遊び方(ローカル)

```
pip install pyxel
python main.py
```

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
| `assets/portraits/` | 立ち絵 PNG |
| `assets/fonts/` | 日本語フォント(umplus) |
| `tools/sim_check.py` | Ch1-1 のバランスをヘッドレスで確認 |
| `tools/autoplay.py` | 自動操作でスクリーンショットを撮る |
| `tools/make_portraits.py` | 仮の立ち絵を生成 |
| `prototype/` | 元になったプロトタイプ |

## 立ち絵の仕様

`assets/portraits/<id>.png` を置き換えると、そのまま会話画面に反映されます。

- サイズ: **128×128 px**(等倍表示)。64×64 でも可(2倍に拡大して表示)。
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

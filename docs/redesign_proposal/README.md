# StarX グラフィック再デザイン案

ゲーム本体は変更していません。このフォルダの PNG は**追加の提案素材**です。既存の `assets/portraits/` とタイトル画面の画像はそのままです。

## 収録物

| ファイル | 内容 | 想定用途 |
| --- | --- | --- |
| `_contact_sheet.png` | 新しい全12人の一覧 | 絵柄・色・人物の識別性をまとめて確認 |
| `<人物ID>.png`（12枚） | 64×64 px、Pyxel標準16色、RGB、不透明 | 会話用の個別素材。既存の人物IDに対応 |
| `rocket_silhouette_study.png` | Eagle 1、再使用型、Starship型の側面形状 | 機体デザインの方向づけ |
| `office_screen_proposal.png` | 640×480 px の会社画面案 | 背景と人物・UIの組み合わせ見本 |
| `launch_screen_proposal.png` | 640×480 px の打ち上げ画面案 | 射場、ロケット、計器の組み合わせ見本 |
| `generate_portraits.py` / `generate_scenes.py` | 元絵を生成する編集可能なソース | 色・形・位置を変えた案の再作成 |

## 現状の作りと変更案

- **人物**：`game/portraits.py` が `assets/portraits/<id>.png` を最大128 pxで読み込みます。既存12枚は `tools/make_portraits.py` が64×64 pxで生成。球体の陰影と細かなディザ、共通の顔立ちが主体です。新案は32×32ドットで輪郭・服・髪型・小物を描き分け、64×64に整数倍で拡大しました。輪郭と影を整理し、小さい画面での読みやすさを優先しています。
- **会社背景**：`game/scene_office.py` の `draw_hangar()` で壁、開いた扉、海、机、ホワイトボード、機体をPyxel図形で毎フレーム描画しています。静的な背景画像ファイルはありません。画面案では格納庫の奥行きを壁・梁・扉枠・海の面で表現し、前景の道具と機体を分離しました。最終実装では背景だけを画像化し、会話枠や状態表示は既存UIに合わせて重ねるのが自然です。
- **打ち上げ背景**：`game/scene_mission.py` の `draw_sky()`、`draw_clouds()`、`draw_ground()` が高度に連動した空、雲、海、島、発射台を描きます。`draw_rocket()` は機体角度とジンバル角を使って回転する図形です。静止画への単純な置換では高度変化と回転を失うため、画面案は色・形の設計見本です。実装時は空と地表を別レイヤーにし、ロケットは角度に合わせて描画・回転できる素材に分けてください。
- **タイトル**：変更対象外です。

## ロケット形状の根拠と使い分け

- **Eagle 1**：物語の初期機体。小型で細い二段式、単発エンジン、段間の黒い帯、白い円筒の左側ハイライトと右側影。現状の細い白棒から、読める機体へ発展させる案です。SpaceXの初期小型機 Falcon 1 の立ち位置を参考にした架空機で、実機のコピーではありません。
- **再使用型**：Falcon 9 に着想。細長い二段構成、1段上端付近のグリッドフィン、下部の着陸脚、白い胴体と黒い段間。脚とフィンは初期Eagle 1には付けず、技術の進歩を視覚化します。SpaceXの[公式Falcon 9解説](https://new.spacex.com/vehicles/falcon-9)と[機体図を含む公式ユーザーガイド](https://www.spacex.com/assets/media/falcon-users-guide-2025-05-09.pdf)を参照しました。
- **Starship型**：後期の別系統案。太いステンレス色の船体、片面の黒い耐熱タイル、前後のフラップを区別しました。Super Heavyを含む全機体ではなく**上段の宇宙船の形状案**です。[SpaceX公式Starship解説](https://new.spacex.com/vehicles/starship)と[Starbase公式資料](https://www.spacex.com/vehicles/starship/assets/media/Starbase%20Overview.pdf)を参照しました。

`rocket_silhouette_study.png` はシルエットの比較用で、3機の縦横比はゲーム内の読みやすさに合わせたものです。厳密な縮尺図ではありません。実装用には背景・炎・機体を切り離した素材を、この方向から作り込む想定です。

## 試す場合

人物PNGは現在の読み込み仕様と同じ寸法・色です。好きな案を選び、**既存画像のバックアップを残して**同名のファイルとして配置すれば表示確認できます。画面案とロケット比較図は設計資料で、そのままゲーム画面を置換する画像ではありません。

再生成：`python art/redesign_proposal/generate_portraits.py` および `python art/redesign_proposal/generate_scenes.py`。Pillow が必要です。

# StarX グラフィック再デザイン案

ゲーム本体は変更していません。このフォルダの PNG は**追加の提案素材**です。既存の `assets/portraits/` とタイトル画面の画像はそのままです。**720×720を基準デザイン**とし、先に作った640×480案は初期ラフとして保存しています。

## 収録物

| ファイル | 内容 | 想定用途 |
| --- | --- | --- |
| `character_faces_concept_720_v5.png` | 現行の12人の顔デザイン基準 | **全員正面向き**。90年代洋画系ゲーム風の、普通で少しコミカルな社員たち |
| `character_faces_concept_720_v4.png` / `character_faces_concept_720_v3.png` / `character_faces_concept_720_v2.png` / `character_faces_concept_720.png` | 以前の顔案 | 比較・検討用の旧案 |
| `characters_720_sheet.png` / `<人物ID>_720.png`（12枚） | 720画面用の128×128 px人物PNG | 会話枠の128×128枠に対応するドット絵試作 |
| `office_screen_720.png` / `launch_screen_720.png` | 720×720 px の会社・打ち上げ画面案 | 正方形画面の構図とUI配置の基準 |
| `starship_v3_detail.png` / `rocket_silhouette_study_v3.png` | 2026年のStarship V3を参照した修正案 | 耐熱タイル側とステンレス側、フラップ、機体の太さを検討 |
| `_contact_sheet.png` | 新しい全12人の一覧 | 絵柄・色・人物の識別性をまとめて確認 |
| `<人物ID>.png`（12枚） | 64×64 px、Pyxel標準16色、RGB、不透明 | 低解像度向け初期ラフ。既存の人物IDに対応 |
| `rocket_silhouette_study.png` / `office_screen_proposal.png` / `launch_screen_proposal.png` | 初期の640×480案 | 旧案との比較 |
| `generate_portraits.py` / `generate_scenes.py` / `generate_720.py` | 編集可能なドット絵ソース | 色・形・位置を変えた案の再作成 |

## 現状の作りと変更案

- **人物**：`game/portraits.py` が `assets/portraits/<id>.png` を最大128 pxで読み込みます。既存12枚は `tools/make_portraits.py` が64×64 pxで生成。球体の陰影と細かなディザ、共通の顔立ちが主体です。今回の128×128版は顔の目・鼻・口をネイティブ解像度で描き直した技術試作です。`character_faces_concept_720_v5.png` は、全員正面を向いた、90年代洋画系ゲーム風の少しコミカルで普通の現場の人らしい造形基準です。**概念シートはそのままゲームに読み込める個別PNGではありません**。次の個別素材化では、このシートの人物差を保つ必要があります。
- **会社背景**：`game/scene_office.py` の `draw_hangar()` で壁、開いた扉、海、机、ホワイトボード、機体をPyxel図形で毎フレーム描画しています。静的な背景画像ファイルはありません。画面案では格納庫の奥行きを壁・梁・扉枠・海の面で表現し、前景の道具と機体を分離しました。最終実装では背景だけを画像化し、会話枠や状態表示は既存UIに合わせて重ねるのが自然です。
- **打ち上げ背景**：`game/scene_mission.py` の `draw_sky()`、`draw_clouds()`、`draw_ground()` が高度に連動した空、雲、海、島、発射台を描きます。`draw_rocket()` は機体角度とジンバル角を使って回転する図形です。静止画への単純な置換では高度変化と回転を失うため、画面案は色・形の設計見本です。実装時は空と地表を別レイヤーにし、ロケットは角度に合わせて描画・回転できる素材に分けてください。
- **タイトル**：変更対象外です。

## ロケット形状の根拠と使い分け

- **Eagle 1**：物語の初期機体。小型で細い二段式、単発エンジン、段間の黒い帯、白い円筒の左側ハイライトと右側影。現状の細い白棒から、読める機体へ発展させる案です。SpaceXの初期小型機 Falcon 1 の立ち位置を参考にした架空機で、実機のコピーではありません。
- **再使用型**：Falcon 9 に着想。細長い二段構成、1段上端付近のグリッドフィン、下部の着陸脚、白い胴体と黒い段間。脚とフィンは初期Eagle 1には付けず、技術の進歩を視覚化します。SpaceXの[公式Falcon 9解説](https://new.spacex.com/vehicles/falcon-9)と[機体図を含む公式ユーザーガイド](https://www.spacex.com/assets/media/falcon-users-guide-2025-05-09.pdf)を参照しました。
- **Starship型**：2026年に飛行した**Starship V3の上段**を参照。約9m径・52m高の太い円筒に近い比率、丸みのある長い機首、銀色のステンレス面と黒い耐熱タイル面、上部の小さなフラップと下部の大きなフラップ、底部のエンジン群を区別しました。黒い面と銀色の面は**見る方向による違い**で、機体全体が一色ではありません。`starship_v3_detail.png` は両側の案です。[SpaceX公式Starship解説](https://new.spacex.com/vehicles/starship)、[V3初飛行の公式報告](https://www.spacex.com/launches/starship-flight-12)、[2回目のV3飛行と耐熱タイルの公式報告](https://www.spacex.com/launches/starship-flight-13)を参照しました。

`rocket_silhouette_study_v3.png` はシルエットの比較用で、3機の縦横比はゲーム内の読みやすさに合わせたものです。厳密な縮尺図ではありません。実装用には背景・炎・機体を切り離した素材を、この方向から作り込む想定です。

## 試す場合

128×128と64×64の個別人物PNGは現在の読み込み寸法・色に対応します。ただし128版は造形基準シートより単純な技術試作です。**既存画像のバックアップを残して**同名のファイルとして配置すれば表示確認できます。画面案とロケット比較図は設計資料で、そのままゲーム画面を置換する画像ではありません。

再生成：`generate_portraits.py` → `generate_scenes.py` → `generate_720.py` の順。Pillow が必要です。概念シート2枚は生成スクリプトの出力ではありません。

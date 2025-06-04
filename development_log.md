# 結婚式フォトコンテスト用顔認識システム 開発日誌

## プロジェクト概要

本プロジェクトは、結婚式のフォトコンテストで使用する顔認識システムの開発を目的としています。参加者が撮影した写真に写っている人物の顔を検出し、あらかじめ登録されたアイドル（新郎新婦や主要参列者）の顔と比較して類似度を計算することで、特定の人物が写っている写真をカテゴリ分けします。

## 主要コンポーネント

1. **顔検出・認識エンジン**: InsightFaceを使用
2. **バックエンド**: Cloud Functions (Python)
3. **ストレージ**: Cloud Storage、Firestore
4. **フロントエンド**: Web UI（未実装）

## 開発環境

- Python 3.8+
- InsightFace (onnxruntime-cpu)
- numpy 1.23.5（注意: numpy 2.xはonnxruntimeと互換性がない）
- PIL/Pillow
- Google Cloud Platform (API有効化、ストレージバケット作成等)

## 実装済み機能

### 1. アイドル画像からの顔特徴ベクトル抽出

```python
# tools/prepare_idol_embeddings.py
```

#### 機能概要
- アイドル画像を読み込み、各画像から顔を検出
- 検出した顔ごとに特徴ベクトルを抽出
- 特徴ベクトルを正規化（L2正規化）
- 顔画像の切り出し保存
- ベクトルと顔情報をJSON形式で保存

#### 出力
- `functions/idol_vectors.json`: 顔特徴ベクトルと顔情報
- `face_images/idol_faces/`: 切り出した顔画像

### 2. テスト画像との比較処理

```python
# test_compare_image.py
```

#### 機能概要
- テスト画像から顔を検出
- 検出した各顔の特徴ベクトルを抽出
- アイドル顔ベクトルとのコサイン類似度を計算
- 類似度の高いアイドル顔を特定
- 結果をJSON形式で保存

#### 出力
- `face_images/test_faces/`: 切り出したテスト顔画像
- `face_images/comparison_[画像名]_[タイムスタンプ].json`: 比較結果

### 3. Cloud Functions実装

```python
# functions/main.py
```

#### 機能概要
- GCSにアップロードされた画像の処理
- 顔検出と特徴ベクトル抽出
- 事前に保存されたアイドルベクトルとの比較
- 結果をFirestoreに保存

### 4. 顔画像管理

#### 実装内容
- 元の画像と切り出した顔画像の対応関係を管理
- 各ベクトルがどの顔に対応するかを追跡
- ベクトルと画像情報の統合管理

## 処理フロー

1. **準備フェーズ**
   - アイドル画像収集
   - `prepare_idol_embeddings.py`実行による特徴ベクトル抽出
   - 顔画像の保存と対応付け

2. **比較フェーズ**
   - テスト画像の準備
   - `test_compare_image.py`実行によるテスト顔の抽出と比較
   - 類似度計算と結果保存

3. **本番運用フェーズ** (未実装)
   - ユーザーからの画像アップロード
   - Cloud Functions処理
   - ユーザーへの結果表示

## 実行方法

### アイドル顔ベクトル抽出

```bash
# アイドル顔ベクトル抽出
python tools/prepare_idol_embeddings.py
```

オプション:
- `--input_dir`: アイドル画像が保存されているディレクトリ (デフォルト: `idol_images`)
- `--output`: 抽出したベクトルを保存するJSONファイル (デフォルト: `functions/idol_vectors.json`)
- `--faces_dir`: 顔画像を保存する親ディレクトリ (デフォルト: `face_images`)
- `--max_faces`: 使用する顔の最大数 (デフォルト: 100)
- `--margin`: 顔の周りに追加するマージン (デフォルト: 0.2)

### テスト画像比較

```bash
# テスト画像との比較
python test_compare_image.py --image [テスト画像パス]
```

オプション:
- `--image`: 比較するテスト画像のパス (デフォルト: `tests/assets/test_image.jpg`)
- `--output_dir`: 顔画像と結果を保存するディレクトリ (デフォルト: `face_images`)
- `--margin`: 顔の周りに追加するマージン (デフォルト: 0.2)

## 開発中に発生した問題と解決策

### 問題1: 各画像が2回ずつ処理される現象
**原因**: `image_files`リストに同じファイルが重複して含まれていた
**解決策**: `list(set(image_files))`で重複を排除

### 問題2: numpy 2.xとonnxruntimeの互換性問題
**原因**: numpy 2.xはonnxruntimeと互換性がない
**解決策**: numpy 1.23.5へのダウングレード

### 問題3: ベクトルと顔画像の対応関係把握
**原因**: 元の実装ではベクトルと元の顔画像の対応が分からなかった
**解決策**: メタデータ（ファイル名、顔インデックス、バウンディングボックス）を含む拡張版の実装

## 今後の課題

1. **フロントエンド実装**
   - ユーザーがアップロードと結果確認ができるUI開発

2. **パフォーマンス最適化**
   - 大量画像処理時の高速化
   - バッチ処理の実装

3. **セキュリティ対策**
   - 認証・認可機能の実装
   - ユーザーデータ保護

4. **精度向上**
   - 顔認識モデルのチューニング
   - 照明・角度・表情変化への対応強化

## データ構造

### idol_vectors.json 形式

```json
{
  "vectors": [
    [0.1, 0.2, ..., 0.5],  // 顔特徴ベクトル (512次元)
    ...
  ],
  "face_info": [
    {
      "vector_index": 0,
      "original_image": "idol_images/example.jpg",
      "face_index": 1,
      "face_image": "face_images/idol_faces/idol_example_face1.jpg",
      "bbox": [100, 120, 220, 240]
    },
    ...
  ]
}
```

### 比較結果JSON形式

```json
{
  "test_image": "tests/assets/test_image.jpg",
  "test_faces": [
    {
      "original_image": "tests/assets/test_image.jpg",
      "face_index": 1,
      "face_image": "face_images/test_faces/test_image_face1.jpg",
      "bbox": [120, 150, 240, 270]
    }
  ],
  "comparison_time": "2024-05-15T12:34:56",
  "results": [
    {
      "test_face_idx": 1,
      "test_face_path": "face_images/test_faces/test_image_face1.jpg",
      "matches": [
        {
          "rank": 1,
          "idol_face_idx": 3,
          "idol_face_path": "face_images/idol_faces/idol_red_face1.jpg",
          "idol_original_image": "idol_images/red.jpg",
          "similarity_score": 0.92
        },
        ...
      ]
    }
  ],
  "overall_score": 0.87
}
```

## 参考資料・ライブラリ

- [InsightFace](https://github.com/deepinsight/insightface)
- [ONNX Runtime](https://onnxruntime.ai/)
- [Google Cloud Functions Documentation](https://cloud.google.com/functions)

## Web UI 実装計画

### 要件

1. **参列者向け投稿UI**
   - 名前入力フォーム
   - 画像アップロード機能
   - 送信ボタン（Cloud Functions起動）
   - アップロード後のフィードバック表示

2. **ランキング表示UI**
   - 各参加者の最高スコアを表示
   - トップ10の参加者を表示
   - 順位ではなく名前の文字列順でソート（発表までトップ参加者を隠す）
   - リアルタイム更新（Firestoreリスナー）

### 技術スタック

1. **フロントエンド**
   - React.js
   - Firebase JavaScript SDK
   - Material-UI（デザインフレームワーク）

2. **バックエンド**
   - Cloud Functions (Python) - 既存実装を活用
   - Cloud Storage - 画像保存
   - Firestore - スコアとユーザー情報の保存

### 実装手順

1. **プロジェクト設定**
   - Create React App でプロジェクト作成
   - Firebase SDK のセットアップ
   - 必要なパッケージのインストール

2. **アップロード機能実装**
   ```jsx
   // ImageUpload.js コンポーネント
   // - ユーザー名入力フォーム
   // - 画像アップロードインターフェース
   // - プレビュー表示
   // - 送信ボタン
   // - アップロード進捗表示
   ```

3. **ランキング表示実装**
   ```jsx
   // Ranking.js コンポーネント
   // - Firestoreからデータ取得
   // - 名前順でソート
   // - トップ10表示
   // - リアルタイム更新リスナー
   ```

4. **バックエンド連携**
   - Cloud Storage トリガー設定
   - Firestore セキュリティルール更新
   - Cloud Functions 更新（必要に応じて）

5. **UI/UX 最適化**
   - レスポンシブデザイン対応
   - エラーハンドリング
   - ローディング表示
   - 成功/失敗フィードバック

### データモデル

```
// Firestore コレクション構造
photos/
  {
    userName: "山田太郎",
    photoUrl: "https://storage.googleapis.com/wedding-photos/abc123.jpg",
    score: 0.92,
    faceCount: 3,
    timestamp: Timestamp,
    ...その他メタデータ
  }
```

### セキュリティ考慮事項

1. **入力検証**
   - ユーザー名の適切な検証（空でない、最大長など）
   - 画像ファイルの検証（サイズ、タイプ、数など）

2. **アクセス制御**
   - 適切なFirebaseセキュリティルール設定
   - 認証不要だが、スパム防止対策を検討

3. **エラーハンドリング**
   - アップロード失敗時の適切なフィードバック
   - リトライメカニズム

### デプロイ計画

1. Firebase Hosting へのデプロイ
2. テスト環境と本番環境の分離
3. CI/CD パイプラインの検討（将来課題）

## 開発タスク

1. [ ] React プロジェクト作成
2. [ ] Firebase設定
3. [ ] 画像アップロードコンポーネント作成
4. [ ] ランキング表示コンポーネント作成
5. [ ] Cloud Functions連携テスト
6. [ ] UI/UXの改善
7. [ ] セキュリティテスト
8. [ ] パフォーマンス最適化
9. [ ] デプロイ 

## マルチターゲットスコアリング機能追加

### 概要

画像に対する類似度スコアを計算する際に、複数のターゲットベクトルファイルに対して同時に計算を行う機能を追加しました。これにより、異なるターゲットグループごとの類似度スコアを比較することが可能になります。

### 実装内容

1. **ベクトルファイル読み込み機能の強化**
   - `target_vectors` ディレクトリ内のすべてのJSONファイルを自動検出
   - 各ファイル名（拡張子なし）をターゲット名として使用
   - ファイルごとに特徴ベクトルをロードして辞書に格納

2. **マルチターゲットスコア計算**
   - 入力画像の各顔に対し、すべてのターゲットベクトルセットと類似度計算
   - ターゲットごとの総合スコアを計算（従来のスコアリング方式を維持）
   - 全ターゲットのスコアをFirestoreに個別のフィールドとして保存

3. **Web UI強化**
   - ランキング表示に複数ターゲットのタブ切り替え機能を追加
   - 各ターゲットでのスコアを表示
   - アップロード画面にマルチターゲット対応の説明を追加

### 設計上の考慮点

1. **拡張性**
   - 新たなターゲットJSONファイルを追加するだけで自動的に対応
   - 既存のサービスに影響を与えずに新しいターゲットを追加可能

2. **下位互換性**
   - 既存の `idol_vectors.json` に基づく従来のスコア計算も維持
   - 総合スコアとして優先的に使用

3. **パフォーマンス**
   - ベクトルの一括ロード処理による初期化時間の最適化
   - ターゲットごとの計算を効率化

### 使用方法

1. `functions/target_vectors/` ディレクトリにベクトルJSONファイルを配置
2. 各ファイル名は意味のある識別子を使用（例: `idol_vectors.json`, `contest_vectors_1.json`）
3. Cloud Functionsのデプロイ時に環境変数 `TARGET_VECTORS_DIR` でディレクトリを指定可能

### データ構造の変更点

```
// Firestoreに保存される写真ドキュメントの新しい形式
{
  "userName": "山田太郎",
  "photoUrl": "https://storage.googleapis.com/wedding-photos/abc123.jpg",
  "fileName": "abc123.jpg",
  "score": 0.92,  // 総合スコア (idol_vectorsまたは最初のターゲット)
  "faceCount": 3,
  "timestamp": Timestamp,
  "processed": true,
  "processingTimestamp": Timestamp,
  
  // 各ターゲットに対するスコア
  "score_idol_vectors": 0.92,
  "score_contest_vectors_1": 0.87,
  // 新たなターゲットが追加されると自動的に対応するフィールドが追加される
}
```

この拡張により、フォトコンテストの評価をより多様なターゲットグループに対して行うことが可能になり、異なる観点からの類似度を比較できるようになりました。 
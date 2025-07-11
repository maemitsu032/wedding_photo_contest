
# GEMINI向けドキュメント

## 1. アプリケーション概要

このプロジェクトは、結婚式の写真コンテストを目的としたWebアプリケーションです。
ユーザーは写真をアップロードし、その写真に写っている顔と、事前に登録された「お手本」の顔（例：有名人、新郎新婦）との類似度スコアを競います。

## 2. 技術スタック

*   **フロントエンド:** React.js (`react-scripts`), Material-UI (`@mui/material`)
*   **バックエンド:** Firebase Functions (Python 3.11)
*   **データベース:** Firestore
*   **ストレージ:** Cloud Storage for Firebase
*   **顔認識エンジン:** InsightFace (`insightface`)

## 3. プロジェクト構成

```
/
├── web-ui/                   # Firebaseプロジェクトのルート
│   ├── functions/            # バックエンド (Firebase Functions)
│   │   ├── main.py           # 顔認識・スコア計算を行うメインロジック
│   │   ├── requirements.txt  # Pythonの依存ライブラリ
│   │   └── target_vectors/   # 比較対象の顔ベクトルデータ (JSON)
│   │       └── contest_vectors_1.json
│   ├── src/                    # フロントエンド (React)
│   │   ├── App.js            # アプリケーションのメインコンポーネント・ルーティング
│   │   ├── components/       # Reactコンポーネント
│   │   │   ├── ImageUpload.js  # 写真アップロード機能
│   │   │   └── Ranking.js      # ランキング表示機能
│   │   └── firebase.js       # Firebaseの初期化設定
│   ├── build/                  # Reactのビルド成果物 (デプロイ対象)
│   ├── firebase.json           # Firebaseのデプロイ設定
│   └── firestore.rules       # Firestoreのセキュリティルール
│
├── src_images/               # 顔ベクトル生成用の元画像
│   ├── contest_images_1/     # コンテスト用の画像
│   └── idol_images/          # (旧) アイドル画像
│
├── face_images/              # スクリプトで切り出した顔画像
│
└── tools/
    └── prepare_idol_embeddings.py # `src_images`から顔検出しベクトルを生成するスクリプト
```

## 4. 主要な処理フロー

### 4.1. 顔ベクトルの事前準備

1.  開発者は `src_images/contest_images_1/` ディレクトリに、お手本となる人物の顔写真を配置します。
2.  `tools/prepare_idol_embeddings.py` を実行します。
3.  スクリプトは `insightface` を使って画像から顔を検出し、512次元の特徴ベクトルを抽出・正規化します。
4.  抽出されたベクトルは `web-ui/functions/target_vectors/contest_vectors_1.json` に保存されます。

### 4.2. ユーザーによる写真投稿とスコアリング

1.  **フロントエンド (`ImageUpload.js`):**
    *   ユーザーがWeb UIから写真ファイルを選択し、アップロードします。
    *   アップロード時に、ユーザー名をメタデータとして添付します。
    *   ファイルはCloud Storageの `wedding-photos/` フォルダに保存されます。

2.  **バックエンド (`main.py` on Cloud Functions):**
    *   Cloud Storageへのファイルアップロードをトリガーとして `score_image` 関数が実行されます。
    *   **コールドスタート時:**
        *   `insightface` モデル (`buffalo_l`) をメモリにロードします。
        *   `target_vectors/` 内のすべての `contest_vectors_*.json` を読み込み、比較対象のベクトルセットとして保持します。
    *   **関数実行時:**
        *   アップロードされた画像を一時ファイルにダウンロードします。
        *   `insightface` を使って、画像内のすべての顔を検出し、特徴ベクトルを抽出・正規化します。
        *   検出された各顔のベクトルと、事前に読み込んでおいたお手本ベクトルセットとの間でコサイン類似度を総当たりで計算します。
        *   コンテストごと（`contest_vectors_1.json` など）に、類似度スコアの**平均値**を算出します。
        *   結果をFirestoreの `contestScores` コレクションに保存します。ドキュメントIDはアップロードされたファイル名（拡張子なし）です。

    **Firestoreのデータ構造 (`contestScores/{docId}`):**
    ```json
    {
      "path": "wedding-photos/my_photo.jpg",
      "faceCount": 3,
      "userName": "Taro",
      "scores": {
        "contest_vectors_1": 0.456,
        "contest_vectors_2": 0.321
      }
    }
    ```

### 4.3. ランキング表示

1.  **フロントエンド (`Ranking.js`):**
    *   Firestoreの `contestScores` コレクションをリッスンします。
    *   `scores` フィールド内の特定のコンテストのスコア (`contest_vectors_1` など) に基づいて、降順でランキングを表示します。
    *   ユーザー名、スコア、写真（Cloud Storageから取得）などを表示します。

## 5. 開発・デプロイに関する注意点

*   **Firebase設定:** `web-ui/firebase.json` がデプロイ設定を管理します。`hosting` でReactのビルド成果物 (`build` ディレクトリ) を、`functions` でバックエンドコードをデプロイします。
*   **お手本画像の追加・変更:**
    1. `src_images/` に画像を追加/変更します。
    2. `tools/prepare_idol_embeddings.py` を実行して `contest_vectors_*.json` を更新します。
    3. 更新された `functions` を `firebase deploy --only functions` でデプロイする必要があります。
*   **Python依存関係:** 新しいライブラリを追加した場合は `web-ui/functions/requirements.txt` に追記が必要です。
*   **ローカル開発:** `firebase emulators:start` を使うことで、Hosting, Firestore, Functions, Storageをローカルでエミュレートできます。


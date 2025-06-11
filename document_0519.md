# フォトコンテストシステムの全体像ドキュメント
## 1. システム概要

このシステムは結婚式のフォトコンテストを実施するためのWebプラットフォームで、参加者が撮影した写真をアップロードし、顔認識AIによる類似度スコアを自動計算してランキング表示するものです。

システムはFirebase（Google Cloud）をベースにした以下の2つの主要コンポーネントで構成されています：
- Cloud Functions：写真処理とスコア計算を行うバックエンド
- Web UI：ユーザー向けのフロントエンドアプリケーション

## 2. システムアーキテクチャ

```
[ユーザー] → [Web UI(React)] → [Firebase Storage] → [Cloud Functions] → [Firestore DB]
                                                        ↑
                                       [ターゲットベクトル(顔特徴データ)]
```

## 3. Cloud Functions詳細

### 3.1 機能概要
- Storage上にアップロードされた写真を監視し自動処理
- InsightFaceライブラリを使用して顔検出と特徴抽出
- 複数の「ターゲット」となる顔との類似度を計算
- 計算結果をFirestoreに保存

### 3.2 主要コンポーネント
- `main_esc.py`: メイン処理ロジック
  - 顔検出・類似度計算アルゴリズム
  - Cloud Storage連携
  - Firestore連携
- `target_vectors/`: ターゲット顔特徴ベクトルを格納したJSONファイル

### 3.3 処理フロー
1. 画像がCloud Storageにアップロードされるとトリガー発火
2. 画像から顔を検出して特徴ベクトルを抽出
3. 事前登録された「ターゲット」との類似度スコアを計算
4. 結果をFirestoreのphotosコレクションに保存

## 4. Web UI詳細

### 4.1 技術スタック
- React.js
- Material UI (MUIコンポーネント)
- Firebase SDK (Storage, Firestore)

### 4.2 主要コンポーネント
- `ImageUpload.js`: 写真アップロード機能
  - ユーザー名入力
  - 画像選択とプレビュー
  - Storage経由でのアップロード
  - 進捗表示

- `Ranking.js`: ランキング/結果表示機能
  - 参加者リスト表示（名前順）
  - 複数ターゲットごとのスコア切り替え
  - リアルタイム更新

### 4.3 ユーザーフロー
1. ユーザーが写真をアップロード
2. Firestoreに初期データを保存
3. Cloud Functionsが処理
4. ランキングページに結果が反映される

## 5. データモデル

### 5.1 Firestore
- **photos** コレクション
  - `userName`: 投稿者名
  - `photoUrl`: 画像のURL
  - `fileName`: ファイル名
  - `timestamp`: 投稿日時
  - `score`: 総合スコア
  - `faceCount`: 検出された顔の数
  - `processed`: 処理済みフラグ
  - `score_{target_name}`: 個別ターゲットごとのスコア

### 5.2 Cloud Storage
- **wedding-photos/**: 投稿された写真保存先

## 6. デプロイ・開発環境

### 6.1 プロジェクト設定
- Firebase: `wedding-photo-contest` プロジェクト
- ストレージバケット: `wedding-photo-contest.appspot.com`

### 6.2 開発環境
- ローカルエミュレーター対応（Firestore, Functions, Storage）
- Reactアプリケーション（npm start）

## 7. 機能拡張ポイント
- 認証機能の追加
- 管理者ダッシュボード
- 複数イベント対応
- より詳細な統計情報

## 8. デモンストレーション
1. 写真投稿ページにアクセス
2. 名前を入力して写真をアップロード
3. 処理が完了するまで待機
4. ランキングページで結果を確認

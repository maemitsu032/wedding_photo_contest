# ウェディングフォトコンテスト システム概要

このリポジトリは、顔認識を用いてアップロードされた写真にスコアを付け、ランキングを表示するデモアプリケーションです。Google Firebase と InsightFace を基盤としており、主要なディレクトリ構成と処理の流れを以下にまとめます。

## ディレクトリ構成

- `functions/` – Cloud Functions のソースコード（Python）。`main.py` がエントリーポイントとなり、Cloud Storage へアップロードされた写真を処理して類似度を計算し、結果を Firestore に書き込みます。
- `functions/target_vectors/` – スコア計算に用いる顔ベクトル（JSON ファイル）を保存します。例: `idol_vectors.json`。
- `tools/` – ベクトル生成用のスクリプト群。`prepare_idol_embeddings.py` などが含まれます。
- `web-ui/` – 画像アップロードおよびランキング表示を行う React アプリケーション。Firebase SDK を利用します。
- `tests/` およびルートにあるテストスクリプト – 顔検出やベクトル読み込みを確認する Pytest ベースのテスト。

## フロントエンド構成

`web-ui/` ディレクトリには React 製のシングルページアプリケーションが置かれています。主なサブディレクトリとファイルは次の通りです。

- `public/` – エントリーとなる `index.html` と `manifest.json` を配置します。
- `src/` – アプリ本体のソースコードを格納するディレクトリ。
  - `App.js` – 画面遷移と共通レイアウトを定義します。
  - `firebase.js` – Firebase SDK 初期化。開発環境ではエミュレーターに接続します。
  - `index.js` – ReactDOM のレンダリングエントリポイント。
  - `components/` – 機能ごとの UI コンポーネント群。
    - `ImageUpload.js` – 画像アップロードフォーム。
    - `Ranking.js` – ランキング表示コンポーネント。
- `package.json` – 依存パッケージ管理と `npm start` などのスクリプトを定義。
- `firebase.json`、`firestore.rules`、`storage.rules` – Firebase Hosting やセキュリティルールの設定。
- `functions/` – Web UI から呼び出す Cloud Functions (Python) を配置するためのフォルダ。必要に応じて利用します。

## 処理フロー

1. **画像アップロード**
   - Web UI (`ImageUpload.js`) から画像をアップロードすると、Firestore に処理待ちフラグ付きでメタデータが登録されます。
   - 画像ファイルは Cloud Storage の `wedding-photos` バケットに保存されます。
2. **Cloud Function のトリガー**
   - バケットにファイルが最終確定すると `functions/main.py` 内の `photo_uploaded` が実行されます。
   - InsightFace のモデルと `functions/target_vectors` の JSON ファイルをロードし、検出した顔の埋め込みと各ターゲットベクトルを比較します。
   - 各ターゲットのスコアと総合スコアを算出し、顔数や処理時刻とともに Firestore に書き込みます。
3. **ランキング表示**
   - React コンポーネント `Ranking.js` が Firestore の `photos` コレクションを監視し、ユーザー名で並び替えて表示します。ターゲット種別によるフィルタも可能です。
   - Cloud Function による処理が完了すると、スコアがリアルタイムで表示に反映されます。

## 主要ファイル

- `functions/main.py` – 画像ダウンロード、InsightFace による顔検出、スコア計算、Firestore 更新を行います。
- `tools/prepare_idol_embeddings.py` – サンプル画像から埋め込みベクトルを生成し、顔画像の切り出しとメタデータ保存を行います。
- `web-ui/src/components/ImageUpload.js` – 入力検証や進捗表示を備えたアップロードフォーム。
- `web-ui/src/components/Ranking.js` – 参加者ごとのスコア一覧を表示するコンポーネント。
- `firestore.rules` と `storage.rules` – 書き込み権限やファイルサイズ・形式を制限するセキュリティルール。

## テスト

`tests/test_embed.py`、`test_vectors_loading.py`、`test_face_recognition.py`、`test_compare_image.py` などの Pytest スクリプトで、顔検出やベクトル読み込みの挙動を確認できます。`functions/requirements.txt` に記載された依存パッケージをインストールすることで、ローカル環境でも `pytest` を実行できます。


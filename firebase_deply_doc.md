# Firebaseデプロイ手順書

## 前提条件
- Node.jsがインストールされていること
- Firebase CLIがインストールされていること
- Firebaseプロジェクトが作成済みであること

## 1. Firebase CLIのインストール（未インストールの場合）
```bash
npm install -g firebase-tools
```

## 2. Firebaseへのログイン
```bash
firebase login
```

## 3. プロジェクトのビルド
```bash
cd web-ui
npm run build
```

## 4. Firebaseへのデプロイ
```bash
firebase deploy
```

## 注意事項
1. デプロイ前に以下の点を確認してください：
   - `firebase.json`の設定が正しいこと
   - `build`ディレクトリが存在すること
   - 必要な環境変数が設定されていること

2. デプロイ後は以下のURLでアクセス可能です：
   - `https://[YOUR-PROJECT-ID].web.app`
   - `https://[YOUR-PROJECT-ID].firebaseapp.com`

## トラブルシューティング
1. デプロイに失敗する場合：
   - `firebase login`でログイン状態を確認
   - `firebase projects:list`でプロジェクトが正しく選択されているか確認
   - `firebase use [YOUR-PROJECT-ID]`でプロジェクトを選択

2. ビルドに失敗する場合：
   - `npm install`で依存関係を再インストール
   - `npm run build`でエラーメッセージを確認

## 追加の設定
必要に応じて以下の設定も行うことができます：

1. 特定の環境（本番/開発）にデプロイする場合：
```bash
firebase deploy --only hosting
```

2. デプロイ前にプレビューを確認する場合：
```bash
firebase serve
```

3. デプロイ履歴を確認する場合：
```bash
firebase hosting:history
```

この手順書に従ってデプロイを実行することで、アプリケーションをFirebase上に公開することができます。何か問題が発生した場合は、エラーメッセージを確認し、必要に応じてトラブルシューティングの手順を試してください。
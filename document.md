```markdown
# 結婚式フォトコンテスト  
**InsightFace (ArcFace r100) × Google Cloud Functions v2**  
開発ドキュメント

---

## 0. 目的

ゲストがスマホで撮影した写真をアップロードすると **顔検出 & アイドル顔類似度スコア** を自動計算し、  
リアルタイムでランキング表示するデモアプリを 3–4 日で構築する。

---

## 1. システム構成

```

ゲスト                 Firebase Hosting            Cloud Storage                    Cloud Functions v2        Firestore
┌──────────┐ upload   ┌────────────┐ putBytes   ┌───────────────────────────┐ onFinalize  ┌──────────┐ add
│スマホ   │───▶──────▶│/upload     │──▶──────▶│wedding-photos/xx.jpg │──▶────────▶│photoUploaded│──▶─────▶│photos coll.│
└──────────┘          │/ranking    │           └───────────────────────────┘             └──────────┘          └──────────┘
└────────────┘        ↖ idol-faces/             (InsightFace r100 / CPU)
↳ idol\_vectors.json

```

* **フロント **: React (or plain HTML) + Firebase Web SDK  
* **ストレージ**: `wedding-photos/` へ誰でも write・read 禁止  
* **Cloud Functions v2 (Python 3.11)**  
  * InsightFace `buffalo_l` で顔 embedding  
  * スコア  `Score = Σ sᵢ / n^0.8`（α=0.8）  
* **Firestore**: `photos` コレクションをランキング画面が listen

---

## 2. ディレクトリ

```

wedding-faces-demo/
├─ functions/
│   ├─ main.py               # Cloud Function
│   ├─ requirements.txt
│   └─ idol\_vectors.json     # アイドル5枚の埋め込み (前処理で生成)
├─ tools/
│   └─ prepare\_idol\_embeddings.py
├─ tests/                    # pytest & assets
│   └─ test\_embed.py
├─ test\_event.json           # 擬似 CloudEvent
└─ firebase.json / hosting/  # Upload & Ranking ページ

````

---

## 3. 事前準備

| 作業 | コマンド／手順 |
|------|----------------|
| **GCP プロジェクト** | `gcloud config set project <PROJECT_ID>` |
| **API 有効化** | Cloud Functions v2 / Artifact Registry / Cloud Build |
| **バケット** | `wedding-photos`, `idol-faces` |
| **アイドル embedding** | `python tools/prepare_idol_embeddings.py` → `functions/idol_vectors.json` |

---

## 4. Cloud Function 実装概要 `functions/main.py`

```python
app = insightface.app.FaceAnalysis(name='buffalo_l',
                                   providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))
idol_vecs = np.asarray(json.load(open("idol_vectors.json")))

def photo_uploaded(event):
    bucket = storage.Client().bucket(event.data["bucket"])
    blob   = bucket.blob(event.data["name"])
    img    = Image.open(io.BytesIO(blob.download_as_bytes())).convert("RGB")

    faces = app.get(np.asarray(img))
    if faces:
        embs = np.stack([f.embedding/np.linalg.norm(f.embedding) for f in faces])
        per_face = idol_vecs @ embs.T     # cos sim  (m, n)
        score = float(per_face.max(0).sum() / len(faces)**0.8)
    else:
        score = 0.0

    firestore.Client().collection("photos").add({
        "url": f"https://storage.googleapis.com/{bucket.name}/{blob.name}",
        "score": score,
        "nFaces": len(faces),
        "timestamp": firestore.SERVER_TIMESTAMP
    })
````

`requirements.txt`

```
insightface==0.7.3
onnxruntime==1.18.0
numpy
Pillow
google-cloud-storage
google-cloud-firestore
```

---

## 5. セキュリティルール

### Storage

```txt
match /b/{bucket}/o {
  match /wedding-photos/{all=**} {
    allow read: if false;
    allow write: if true;
  }
}
```

### Firestore

```txt
match /databases/{db}/documents {
  match /photos/{doc} {
    allow read: if true;
    allow write: if false;
  }
}
```

---

## 6. テスト戦略

| フェーズ                     | 目的                            | ツール / コマンド                                                                     |
| ------------------------ | ----------------------------- | ------------------------------------------------------------------------------ |
| **ユニット**                 | InsightFace embed 正常          | `pytest` (`tests/`)                                                            |
| **ローカル CloudEvent**      | ロジック検証                        | `functions-framework --signature-type cloudevent` + `curl -d @test_event.json` |
| **統合 (Local Emulators)** | Storage→Function→Firestore 連携 | `firebase emulators:start --only firestore,storage`                            |
| **Docker CI**            | 本番ランタイム再現                     | Cloud Build with `tools/Dockerfile.test`                                       |
| **ステージング**               | GCP 上で E2E                    | バケット `wedding-photos-stg` にデプロイ                                                |

---

## 7. デプロイ

```bash
gcloud functions deploy photoUploadedProd \
  --gen2 --runtime python311 --entry-point photo_uploaded \
  --trigger-event google.cloud.storage.object.v1.finalized \
  --trigger-resource projects/_/buckets/wedding-photos \
  --region asia-northeast1 --memory 1024Mi --timeout 120s
```

---

## 8. 開発スケジュール（例）

| Day | タスク                                         |
| --- | ------------------------------------------- |
| 0   | プロジェクト & API 設定                             |
| 1   | アイドル embedding 生成 / ユニットテスト                 |
| 2   | Cloud Function 実装 & Functions Framework テスト |
| 3   | Local Emulators 統合、ルール調整                    |
| 4   | ステージングデプロイ、フロント連携                           |
| 5   | UI 微調整 & 本番 QR 配布                           |

---

## 9. 今後の拡張

* provider 切替 (`Face++`, `CLOVA`) で精度 A/B テスト
* 表情・年齢推定を加えたサブ賞
* InsightFace を GPU Cloud Run に移行し高速化
* アップロードページを PWA / オフライン対応

---

### Appendix : スコア式パラメータ

| 変数           | デフォルト   | 説明                    |
| ------------ | ------- | --------------------- |
| `ALPHA`      | `0.8`   | スムージング係数 (`nFaces^α`) |
| `IDOL_COUNT` | 5       | アイドル参照ベクトル数           |
| `DET_SIZE`   | 640×640 | InsightFace 推論サイズ     |

> `.env` で環境変数化し、Cloud Functions `--set-env-vars` で切替可能。

---

**Author**:
Mitsuki Maekawa Wedding Dev Team
2025‑05‑13

```
```

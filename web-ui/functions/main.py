# Cloud Functions (Gen 2, Python 3.12)
from firebase_functions import storage_fn
from firebase_functions import options  # region 指定用
from google.cloud import storage, firestore
from insightface.app import FaceAnalysis

from pathlib import Path
import numpy as np
from PIL import Image
import tempfile, os, json, logging

# ---------- グローバル初期化（コールドスタート時に一度だけ） ----------
#REGION = "asia-northeast1"
REGION = "us-central1"
BUCKET_NAME = "wedding-photo-contest-dev-032.firebasestorage.app"        # ★バケット ID
VEC_DIR      = Path(__file__).with_name("target_vectors")
DET_SIZE     = (640, 640)

# 1. InsightFace モデルを CPU でロード
_face_app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
_face_app.prepare(ctx_id=0, det_size=DET_SIZE)
logging.info("InsightFace model loaded.")

# 2. contest_vectors_*.json を全部読み込む
_target_sets = {}   # {contest_name: (m,512) ndarray}
for vec_file in VEC_DIR.glob("contest_vectors_*.json"):
    try:
        with vec_file.open() as f:
            data = json.load(f)
        vectors = np.asarray(data["vectors"])
        vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        _target_sets[vec_file.stem] = vectors           # 例: 'contest_vectors_A'
        logging.info("Loaded %s (%d vec)", vec_file.name, vectors.shape[0])
    except Exception as e:
        logging.error("Fail load %s: %s", vec_file.name, e)

# ---------- 画像アップロードで発火する関数 ----------
@storage_fn.on_object_finalized(
        region=REGION,
        bucket=BUCKET_NAME,
        memory=options.MemoryOption.GB_2     # ← メモリ指定などもここで
)
def score_image(event: storage_fn.CloudEvent[storage_fn.StorageObjectData]):
    """Storage に画像が置かれたら、各 contest_vectors と平均類似度を計算して
       Firestore: contestScores/{docId} に結果を格納
    """
    blob_path = event.data.name            # 例: wedding-photos/xxx.jpg
    if not blob_path.lower().endswith((".jpg", ".jpeg", ".png")):
        logging.info("Skip non-image file: %s", blob_path)
        return

    # 追加: アップロード時のユーザー名を取得
    user_name = None
    if event.data.metadata and "userName" in event.data.metadata:
        user_name = event.data.metadata["userName"]

    # ① 一時ファイルにダウンロード
    storage_client = storage.Client()
    bucket = storage_client.bucket(event.data.bucket)
    blob   = bucket.blob(blob_path)
    fd, tmp = tempfile.mkstemp()
    blob.download_to_filename(tmp)

    # ② 顔検出と埋め込み
    img   = np.asarray(Image.open(tmp).convert("RGB"))
    faces = _face_app.get(img)
    os.close(fd); os.remove(tmp)

    if not faces:
        logging.info("No faces detected in %s", blob_path)
        return

    face_embs = np.stack(
        [f.embedding / np.linalg.norm(f.embedding) for f in faces]
    )  # shape = (n_faces, 512)

    # ③ 各 contest_vectors と類似度平均を計算
    scores = {}
    for cname, cvecs in _target_sets.items():
        sims = face_embs @ cvecs.T           # (n_faces, n_cvecs)
        scores[cname] = float(sims.mean())   # 全ペア平均

    # ④ Firestore へ保存
    fs_client = firestore.Client()
    doc_id = Path(blob_path).stem           # ファイル名(拡張子なし)をキー
    fs_client.collection("contestScores").document(doc_id).set({
        "path"      : blob_path,
        "faceCount" : len(faces),
        "scores"    : scores,
        "userName"  : user_name              # ← 追加
    })
    logging.info("Saved scores for %s → %s", blob_path, scores)
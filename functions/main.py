#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cloud Functions v2 エントリーポイント
結婚式フォトコンテスト - 顔検出と類似度スコア計算
"""

import os
import io
import json
import glob
import numpy as np
from PIL import Image
import insightface
from insightface.app import FaceAnalysis
from google.cloud import storage
from google.cloud import firestore

# 環境変数から設定を読み込み（デフォルト値あり）
ALPHA = float(os.environ.get('ALPHA', 0.8))
DET_SIZE = int(os.environ.get('DET_SIZE', 640))
TARGET_VECTORS_DIR = os.environ.get('TARGET_VECTORS_DIR', 'target_vectors')

# InsightFaceモデルの初期化
app = None
target_vectors = {}

def init_model():
    """InsightFaceモデルとターゲットベクトルの初期化"""
    global app, target_vectors
    
    if app is None:
        print(f"InsightFaceモデルを初期化しています...")
        app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        app.prepare(ctx_id=0, det_size=(DET_SIZE, DET_SIZE))
    
    if not target_vectors:
        print(f"ターゲットベクトルを読み込んでいます: {TARGET_VECTORS_DIR}ディレクトリ")
        try:
            # ターゲットベクトルディレクトリ内の全JSONファイルを検索
            vector_files = glob.glob(os.path.join(TARGET_VECTORS_DIR, "*.json"))
            if not vector_files:
                raise ValueError(f"ターゲットベクトルが見つかりません: {TARGET_VECTORS_DIR}")
            
            # 各ベクトルファイルを読み込む
            for vector_file in vector_files:
                target_name = os.path.basename(vector_file).split('.')[0]  # ファイル名から拡張子を除いた部分
                vectors = np.asarray(json.load(open(vector_file)))
                target_vectors[target_name] = vectors
                print(f"ターゲットベクトル '{target_name}': {vectors.shape} を読み込みました")
            
            print(f"合計 {len(target_vectors)} 個のターゲットベクトルファイルを読み込みました")
        except Exception as e:
            print(f"エラー: ターゲットベクトルの読み込みに失敗しました: {e}")
            raise

def calculate_scores(embs, n_faces):
    """
    複数のターゲットベクトルに対してスコアを計算
    
    Args:
        embs: 入力画像から抽出した顔特徴ベクトルの配列
        n_faces: 検出された顔の数
        
    Returns:
        dict: ターゲット名をキーとし、スコアを値とする辞書
    """
    scores = {}
    
    for target_name, vectors in target_vectors.items():
        # ターゲットベクトルと入力顔特徴ベクトルの類似度を計算
        per_face = vectors @ embs.T  # コサイン類似度 (m, n)
        
        # スコア計算: 各顔ごとの最大類似度の合計 / 顔の数^α
        score = float(per_face.max(0).sum() / (n_faces ** ALPHA))
        scores[target_name] = score
        print(f"ターゲット '{target_name}' に対するスコア: {score:.4f}")
        
    return scores

def photo_uploaded(cloudevent):
    """
    Cloud Storageにアップロードされた写真をトリガーに実行される関数
    顔検出と類似度スコアを計算し、Firestoreに結果を保存
    
    Args:
        event: Cloud Functions v2のCloudEvent
    """
    # モデルの初期化（必要な場合）
    init_model()
    
    # バケット名とファイル名の取得
    bucket_name = cloudevent.data["bucket"]
    file_name = cloudevent.data["name"]
    
    print(f"バケット {bucket_name} にファイル {file_name} がアップロードされました")
    
    # 処理対象のバケットとプレフィックスをチェック
    if bucket_name != 'wedding-photos' or not file_name.startswith(('wedding-photos/')):
        print(f"対象外のファイル: {bucket_name}/{file_name}")
        return
    
    # ファイルの種類をチェック
    if not file_name.lower().endswith(('.jpg', '.jpeg', '.png')):
        print(f"非対応のファイル形式: {file_name}")
        return
    
    # Storage Clientの初期化
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    
    try:
        # 画像をダウンロードして処理
        print(f"画像 {file_name} をダウンロードして処理します...")
        image_bytes = blob.download_as_bytes()
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # 顔検出
        faces = app.get(np.asarray(img))
        n_faces = len(faces)
        
        print(f"画像から {n_faces} 個の顔を検出しました")
        
        if faces:
            # 各顔の埋め込みベクトルを抽出して正規化
            embs = np.stack([f.embedding/np.linalg.norm(f.embedding) for f in faces])
            
            # 全ターゲットに対するスコアを計算
            all_scores = calculate_scores(embs, n_faces)
            
            # 総合スコア（idol_vectorsを優先的に使用）
            overall_score = all_scores.get("idol_vectors", 0.0)
            if "idol_vectors" not in all_scores and all_scores:
                # idol_vectorsがない場合は最初のスコアを使用
                overall_score = next(iter(all_scores.values()))
        else:
            # 顔が検出されなかった場合はスコア0
            all_scores = {target_name: 0.0 for target_name in target_vectors.keys()}
            overall_score = 0.0
            print("顔が検出されませんでした。スコア: 0.0")
        
        # Firestoreに結果を保存
        firestore_client = firestore.Client()
        
        # 写真のメタデータを検索（Web UIからアップロードされた場合に対応）
        photos_query = firestore_client.collection("photos").where("fileName", "==", os.path.basename(file_name)).limit(1)
        query_results = list(photos_query.stream())
        
        # すべてのスコアをFirestoreに格納するデータを準備
        target_scores = {}
        for target_name, score in all_scores.items():
            target_scores[f"score_{target_name}"] = score
        
        if query_results:
            # 既存のドキュメントがある場合は更新
            photo_doc = query_results[0]
            print(f"既存のドキュメント {photo_doc.id} を更新します")
            
            # 既存のドキュメントを更新
            update_data = {
                "score": overall_score,
                "faceCount": n_faces,
                "processed": True,
                "processingTimestamp": firestore.SERVER_TIMESTAMP,
                **target_scores  # 各ターゲットのスコアを追加
            }
            
            photo_doc.reference.update(update_data)
            
            return {
                "success": True, 
                "updated": True, 
                "score": overall_score, 
                "faces": n_faces,
                "targetScores": all_scores
            }
        else:
            # 既存のドキュメントがない場合は新規作成
            print(f"新しいドキュメントを作成します")
            photo_data = {
                "photoUrl": f"https://storage.googleapis.com/{bucket_name}/{file_name}",
                "fileName": os.path.basename(file_name),
                "score": overall_score,  # 総合スコア
                "faceCount": n_faces,
                "processed": True,
                "timestamp": firestore.SERVER_TIMESTAMP,
                "userName": "匿名",  # Web UI経由でない場合のデフォルト
                **target_scores  # 各ターゲットのスコアを追加
            }
            
            # Firestoreに保存
            doc_ref = firestore_client.collection("photos").add(photo_data)
            print(f"新規ドキュメントを作成しました: {doc_ref}")
            
            return {
                "success": True, 
                "created": True, 
                "score": overall_score, 
                "faces": n_faces,
                "targetScores": all_scores
            }
        
    except Exception as e:
        print(f"エラー: 画像処理中に例外が発生しました: {e}")
        raise 
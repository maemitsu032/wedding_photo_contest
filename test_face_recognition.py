#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
顔認識と複数ターゲットに対するスコア計算のテスト
"""

import os
import sys
import glob
import json
import numpy as np
from PIL import Image
import insightface
from insightface.app import FaceAnalysis

# 環境変数
ALPHA = 0.8  # スコア計算用のα値
DET_SIZE = 640  # 顔検出サイズ
TARGET_VECTORS_DIR = 'functions/target_vectors'  # ターゲットベクトルディレクトリ

def init_face_model():
    """顔認識モデルの初期化"""
    print("InsightFaceモデルを初期化しています...")
    try:
        app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        app.prepare(ctx_id=0, det_size=(DET_SIZE, DET_SIZE))
        print("モデル初期化成功")
        return app
    except Exception as e:
        print(f"モデル初期化エラー: {e}")
        return None

def load_target_vectors():
    """ターゲットベクトルの読み込み"""
    target_vectors = {}
    print(f"ターゲットベクトルを読み込んでいます: {TARGET_VECTORS_DIR}")
    
    # ディレクトリの存在確認
    if not os.path.exists(TARGET_VECTORS_DIR):
        print(f"エラー: ディレクトリが見つかりません: {TARGET_VECTORS_DIR}")
        return {}
    
    # JSONファイルのリストを取得
    vector_files = glob.glob(os.path.join(TARGET_VECTORS_DIR, "*.json"))
    
    if not vector_files:
        print(f"エラー: JSONファイルが見つかりません: {TARGET_VECTORS_DIR}")
        return {}
    
    # 各ファイルを読み込み
    for vector_file in vector_files:
        target_name = os.path.basename(vector_file).split('.')[0]
        print(f"ファイル '{vector_file}' を読み込み中...")
        
        try:
            with open(vector_file, 'r') as f:
                json_data = json.load(f)
            
            # JSONの構造を確認
            if isinstance(json_data, dict) and "vectors" in json_data:
                # {"vectors": [...]} 形式
                vectors = np.asarray(json_data["vectors"])
                print(f"  '{target_name}': 'vectors'キーから{len(vectors)}個のベクトルを読み込み")
            elif isinstance(json_data, list):
                # 直接配列形式
                vectors = np.asarray(json_data)
                print(f"  '{target_name}': {len(vectors)}個のベクトルを直接読み込み")
            else:
                print(f"  警告: 未知の形式 - スキップします")
                continue
            
            target_vectors[target_name] = vectors
        except Exception as e:
            print(f"  エラー: ファイル '{vector_file}' の読み込み失敗: {e}")
    
    return target_vectors

def calculate_scores(embs, n_faces, target_vectors):
    """複数のターゲットベクトルに対してスコアを計算"""
    scores = {}
    
    for target_name, vectors in target_vectors.items():
        # ターゲットベクトルと入力顔特徴ベクトルの類似度を計算
        per_face = vectors @ embs.T  # コサイン類似度 (m, n)
        
        # スコア計算: 各顔ごとの最大類似度の合計 / 顔の数^α
        score = float(per_face.max(0).sum() / (n_faces ** ALPHA))
        scores[target_name] = score
        print(f"ターゲット '{target_name}' に対するスコア: {score:.4f}")
        
    return scores

def process_image(image_path, app, target_vectors):
    """画像処理と顔認識、スコア計算"""
    if not os.path.exists(image_path):
        print(f"エラー: 画像ファイルが存在しません: {image_path}")
        return None
    
    print(f"画像を処理しています: {image_path}")
    
    try:
        # 画像を読み込み
        img = Image.open(image_path).convert("RGB")
        img_array = np.asarray(img)
        
        # 顔検出
        faces = app.get(img_array)
        n_faces = len(faces)
        
        print(f"検出された顔: {n_faces}個")
        
        if n_faces == 0:
            print("顔が検出されませんでした。スコア: 0.0")
            return {target_name: 0.0 for target_name in target_vectors.keys()}
        
        # 各顔の埋め込みベクトルを抽出して正規化
        embs = np.stack([f.embedding/np.linalg.norm(f.embedding) for f in faces])
        
        # すべてのターゲットに対するスコアを計算
        all_scores = calculate_scores(embs, n_faces, target_vectors)
        
        # 総合スコア（idol_vectorsを優先的に使用）
        overall_score = all_scores.get("idol_vectors", 0.0)
        if "idol_vectors" not in all_scores and all_scores:
            # idol_vectorsがない場合は最初のスコアを使用
            overall_score = next(iter(all_scores.values()))
        
        print(f"総合スコア: {overall_score:.4f}")
        
        return all_scores
    
    except Exception as e:
        print(f"エラー: 画像処理中に例外が発生しました: {e}")
        return None

def main():
    """メイン処理"""
    # コマンドライン引数から画像ファイルを取得
    if len(sys.argv) < 2:
        print("使用方法: python test_face_recognition.py <image_path>")
        print("例: python test_face_recognition.py tests/assets/test_image.jpg")
        return
    
    image_path = sys.argv[1]
    
    # 顔認識モデルの初期化
    app = init_face_model()
    if app is None:
        return
    
    # ターゲットベクトルの読み込み
    target_vectors = load_target_vectors()
    if not target_vectors:
        print("ターゲットベクトルの読み込みに失敗しました。処理を中止します。")
        return
    
    # 画像処理とスコア計算
    scores = process_image(image_path, app, target_vectors)
    
    if scores:
        print("\n結果サマリー:")
        print("-" * 50)
        for target_name, score in scores.items():
            print(f"{target_name}: {score:.4f}")
        print("-" * 50)
        print("処理完了")

if __name__ == "__main__":
    main() 
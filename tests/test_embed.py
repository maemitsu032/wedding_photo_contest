#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
InsightFaceの埋め込みベクトル生成のテスト
"""

import os
import sys
import pytest
import numpy as np
from pathlib import Path
from PIL import Image
import insightface
from insightface.app import FaceAnalysis

# 必要に応じてプロジェクトのルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

@pytest.fixture
def face_app():
    """InsightFaceアプリのフィクスチャ"""
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))
    return app

def test_face_detection(face_app):
    """テスト画像から顔が検出されることを確認"""
    # テスト画像のパス
    test_image_path = Path(__file__).parent / "assets" / "test_image.jpg"
    
    # テスト画像が存在しない場合はスキップ
    if not test_image_path.exists():
        pytest.skip(f"テスト画像が見つかりません: {test_image_path}")
    
    # 画像を読み込み
    img = Image.open(test_image_path).convert("RGB")
    img_array = np.array(img)
    
    # 顔検出
    faces = face_app.get(img_array)
    
    # 少なくとも1つの顔が検出されることを確認
    assert len(faces) > 0, "テスト画像から顔が検出されませんでした"
    
    # 各顔に埋め込みベクトルがあることを確認
    for face in faces:
        assert hasattr(face, 'embedding'), "検出された顔に埋め込みベクトルがありません"
        assert face.embedding.shape == (512,), f"埋め込みベクトルのサイズが予期しないものです: {face.embedding.shape}"
        
        # ベクトルが正規化できることを確認
        norm_embedding = face.embedding / np.linalg.norm(face.embedding)
        assert abs(np.linalg.norm(norm_embedding) - 1.0) < 1e-5, "ベクトルの正規化に失敗しました"

def test_cosine_similarity():
    """コサイン類似度の計算が正しく動作することを確認"""
    # 2つのテストベクトル
    vec1 = np.array([1, 0, 0, 0], dtype=np.float32)
    vec2 = np.array([0, 1, 0, 0], dtype=np.float32)
    vec3 = np.array([1, 1, 0, 0], dtype=np.float32) / np.sqrt(2)
    
    # コサイン類似度を計算
    sim12 = np.dot(vec1, vec2)
    sim13 = np.dot(vec1, vec3)
    
    # ベクトル1と2は直交（類似度0）
    assert abs(sim12) < 1e-5, "直交するベクトルの類似度が0ではありません"
    
    # ベクトル1と3は45度（類似度1/sqrt(2)）
    assert abs(sim13 - 1/np.sqrt(2)) < 1e-5, "45度のベクトルの類似度が正しくありません" 
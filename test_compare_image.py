#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
テスト画像とアイドル画像を比較して類似度スコアを出力するスクリプト
また、顔画像の切り出しと比較結果の保存も行います
"""

import os
import json
import numpy as np
from PIL import Image
import insightface
from insightface.app import FaceAnalysis
from pathlib import Path
import glob
import argparse
import datetime

def load_idol_data():
    """
    functions/idol_vectors.jsonからアイドルの顔ベクトルと顔情報を読み込みます
    """
    idol_vectors_path = 'functions/idol_vectors.json'
    
    if not os.path.exists(idol_vectors_path):
        print(f"エラー: {idol_vectors_path} が見つかりません")
        return None, None
    
    try:
        with open(idol_vectors_path, 'r', encoding='utf-8') as f:
            idol_data = json.load(f)
        
        # 新しい形式（ベクトルと顔情報が一緒に保存されている）
        if isinstance(idol_data, dict) and 'vectors' in idol_data and 'face_info' in idol_data:
            return np.array(idol_data['vectors']), idol_data['face_info']
        # 旧形式（ベクトルのみ）
        else:
            print("警告: 旧形式のidol_vectors.jsonが検出されました。顔画像との対応付けはできません。")
            return np.array(idol_data), None
            
    except Exception as e:
        print(f"エラー: アイドルデータの読み込みに失敗しました: {e}")
        return None, None

def process_test_image(app, image_path, output_dir, add_margin=0.2):
    """
    テスト画像から顔を検出して特徴ベクトルを抽出し、顔画像を保存します
    """
    if not os.path.exists(image_path):
        print(f"エラー: テスト画像 {image_path} が見つかりません")
        return None, []
    
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # 画像ファイル名（拡張子なし）を取得
        image_filename = os.path.splitext(os.path.basename(image_path))[0]
        
        # 画像を読み込み
        img = Image.open(image_path).convert("RGB")
        img_array = np.array(img)
        
        # 顔検出
        faces = app.get(img_array)
        
        if not faces:
            print(f"画像から顔が検出されませんでした: {image_path}")
            return None, []
        
        print(f"画像から {len(faces)} 個の顔を検出しました")
        
        # 各顔の埋め込みベクトルを抽出して正規化
        face_vectors = []
        test_faces_info = []
        
        for i, face in enumerate(faces):
            # バウンディングボックスを取得
            bbox = face.bbox.astype(int)
            x1, y1, x2, y2 = bbox
            
            # マージンを追加
            width, height = x2 - x1, y2 - y1
            margin_w, margin_h = int(width * add_margin), int(height * add_margin)
            
            # マージン付きの座標を計算（画像の範囲内に収める）
            x1_margin = max(0, x1 - margin_w)
            y1_margin = max(0, y1 - margin_h)
            x2_margin = min(img.width, x2 + margin_w)
            y2_margin = min(img.height, y2 + margin_h)
            
            # 顔領域を切り取り
            face_img = img.crop((x1_margin, y1_margin, x2_margin, y2_margin))
            
            # 保存するファイル名（元の画像名_顔番号.jpg）
            face_filename = f"test_{image_filename}_face{i+1}.jpg"
            face_path = os.path.join(output_dir, face_filename)
            
            # 画像を保存
            face_img.save(face_path, quality=95)
            print(f"  顔 {i+1}/{len(faces)} を保存しました: {face_path}")
            
            # L2正規化
            embedding = face.embedding / np.linalg.norm(face.embedding)
            face_vectors.append(embedding)
            
            # テスト顔情報を追加
            test_faces_info.append({
                'original_image': image_path,
                'face_index': i + 1,
                'face_image': face_path,
                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                'bbox_with_margin': [int(x1_margin), int(y1_margin), int(x2_margin), int(y2_margin)]
            })
        
        return np.array(face_vectors), test_faces_info
    
    except Exception as e:
        print(f"エラー: 画像処理中に例外が発生しました: {e}")
        return None, []

def calculate_similarity(test_vectors, idol_vectors):
    """
    テスト画像の顔ベクトルとアイドル顔ベクトルの類似度を計算します
    """
    # 各テスト顔ベクトルとアイドルベクトルのコサイン類似度を計算
    similarity_matrix = np.dot(test_vectors, idol_vectors.T)  # (n_test, n_idol)
    
    # 各テスト顔について、最も類似度が高いアイドル顔を特定
    best_matches = []
    
    for i, similarities in enumerate(similarity_matrix):
        # 類似度の降順でインデックスを取得
        sorted_indices = np.argsort(similarities)[::-1]
        
        # 各アイドル顔との類似度を保存
        matches = []
        for idol_idx in sorted_indices:
            matches.append({
                'idol_face_idx': int(idol_idx),
                'similarity_score': float(similarities[idol_idx])
            })
        
        best_matches.append({
            'test_face_idx': i,
            'matches': matches
        })
    
    return best_matches

def main():
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(description='テスト画像とアイドル画像を比較して類似度スコアを出力')
    parser.add_argument('--image', type=str, default='tests/assets/test_image.jpg',
                      help='比較するテスト画像のパス (デフォルト: tests/assets/test_image.jpg)')
    parser.add_argument('--output_dir', type=str, default='face_images',
                      help='顔画像と結果を保存するディレクトリ (デフォルト: face_images)')
    parser.add_argument('--margin', type=float, default=0.2,
                      help='顔の周りに追加するマージン (デフォルト: 0.2)')
    args = parser.parse_args()
    
    # 出力ディレクトリの設定
    test_faces_dir = os.path.join(args.output_dir, 'test_faces')
    os.makedirs(test_faces_dir, exist_ok=True)
    
    # アイドルベクトルとデータの読み込み
    print("アイドル顔データを読み込んでいます...")
    idol_vectors, idol_face_info = load_idol_data()
    if idol_vectors is None:
        return
    
    print(f"アイドル顔ベクトル: {idol_vectors.shape[0]}個のベクトルを読み込みました")
    
    # InsightFaceモデルの初期化
    print("InsightFaceモデルを初期化しています...")
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))
    
    # テスト画像の処理
    print(f"テスト画像を処理しています: {args.image}")
    test_vectors, test_faces_info = process_test_image(app, args.image, test_faces_dir, args.margin)
    if test_vectors is None:
        return
    
    # 類似度計算
    print("類似度を計算しています...")
    matches = calculate_similarity(test_vectors, idol_vectors)
    
    # 結果表示
    print("\n=== 類似度スコア結果 ===")
    print(f"テスト画像: {args.image}")
    print(f"アイドル顔ベクトル: functions/idol_vectors.json ({idol_vectors.shape[0]}個)")
    print("\n各テスト顔の最良マッチ:")
    
    # 結果情報を保存するための辞書
    comparison_results = {
        'test_image': args.image,
        'test_faces': test_faces_info,
        'comparison_time': datetime.datetime.now().isoformat(),
        'results': []
    }
    
    for match in matches:
        test_face_idx = match['test_face_idx']
        test_face_path = test_faces_info[test_face_idx]['face_image']
        best_match = match['matches'][0]  # 最良マッチ（先頭）
        idol_face_idx = best_match['idol_face_idx']
        similarity_score = best_match['similarity_score']
        
        print(f"テスト顔 #{test_face_idx+1} → アイドル顔 #{idol_face_idx+1}")
        print(f"  類似度スコア: {similarity_score:.4f}")
        
        # アイドル顔情報があれば対応する顔画像パスを表示
        idol_face_path = None
        if idol_face_info:
            # インデックスが一致する顔情報を検索
            for info in idol_face_info:
                if info['vector_index'] == idol_face_idx:
                    idol_face_path = info['face_image']
                    print(f"  テスト顔画像: {test_face_path}")
                    print(f"  アイドル顔画像: {idol_face_path}")
                    print(f"  元画像: {info['original_image']}")
                    break
        
        # 結果情報に追加
        result_entry = {
            'test_face_idx': test_face_idx + 1,
            'test_face_path': test_face_path,
            'matches': []
        }
        
        # 上位3つのマッチングを保存
        for i, m in enumerate(match['matches'][:3]):
            idol_idx = m['idol_face_idx']
            score = m['similarity_score']
            
            # アイドル顔情報があれば対応する顔画像パスを取得
            idol_path = None
            idol_orig_path = None
            if idol_face_info:
                for info in idol_face_info:
                    if info['vector_index'] == idol_idx:
                        idol_path = info['face_image']
                        idol_orig_path = info['original_image']
                        break
            
            result_entry['matches'].append({
                'rank': i + 1,
                'idol_face_idx': idol_idx + 1,
                'idol_face_path': idol_path,
                'idol_original_image': idol_orig_path,
                'similarity_score': score
            })
        
        comparison_results['results'].append(result_entry)
    
    # 総合スコア計算（顔ごとの最大スコアの平均）
    avg_score = sum(match['matches'][0]['similarity_score'] for match in matches) / len(matches)
    print(f"\n総合類似度スコア: {avg_score:.4f}")
    
    # 比較結果をJSONファイルに保存
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    image_basename = os.path.splitext(os.path.basename(args.image))[0]
    result_filename = f"comparison_{image_basename}_{timestamp}.json"
    result_path = os.path.join(args.output_dir, result_filename)
    
    comparison_results['overall_score'] = float(avg_score)
    
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(comparison_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n比較結果を保存しました: {result_path}")
    print(f"切り取った顔画像は以下のディレクトリに保存されています: {test_faces_dir}")

if __name__ == "__main__":
    main() 
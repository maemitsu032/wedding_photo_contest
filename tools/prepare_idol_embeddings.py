#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
アイドル画像から顔の特徴ベクトルを抽出するスクリプト
抽出したベクトルはfunctions/idol_vectors.jsonに保存します
また、顔画像を切り取ってface_images/idol_facesに保存し、対応情報をidol_vectors.jsonに含めます
"""

import os
import sys
import json
import argparse
import numpy as np
from PIL import Image
import insightface
from insightface.app import FaceAnalysis
import glob
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='アイドル画像から顔特徴ベクトルを抽出')
    parser.add_argument('--input_dir', type=str, default='idol_images', 
                        help='アイドル画像が保存されているディレクトリ')
    parser.add_argument('--output', type=str, default='idol_vectors.json',
                        help='抽出したベクトルを保存するJSONファイル')
    parser.add_argument('--faces_dir', type=str, default='idol_faces',
                        help='切り取った顔画像を保存するディレクトリ')
    parser.add_argument('--max_faces', type=int, default=100,
                        help='使用する顔の最大数')
    parser.add_argument('--margin', type=float, default=0.2,
                        help='顔の周りに追加するマージン（バウンディングボックスに対する割合）')
    args = parser.parse_args()
    
    # 出力ディレクトリが存在するか確認
    output_dir = "functions/target_vectors"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 顔画像保存用ディレクトリの作成
    idol_faces_dir = os.path.join("face_images", args.faces_dir)
    os.makedirs(idol_faces_dir, exist_ok=True)
    
    # 入力ディレクトリが存在するか確認
    src_image_dir = os.path.join("src_images", args.input_dir)
    if not os.path.exists(src_image_dir):
        print(f"エラー: 入力ディレクトリ '{src_image_dir}' が見つかりません。")
        print(f"アイドル画像を '{src_image_dir}' ディレクトリに配置してください。")
        print(f"サポートされる画像形式: .jpg, .jpeg, .png")
        sys.exit(1)
    
    # 画像ファイルのリストを取得（Pathを使用して重複を避ける）
    image_files = []
    for ext in ['.jpg', '.jpeg', '.png']:
        for file in Path(src_image_dir).glob(f'*{ext.lower()}'):
            image_files.append(str(file))
        for file in Path(src_image_dir).glob(f'*{ext.upper()}'):
            image_files.append(str(file))
    
    # 重複を排除
    image_files = list(set(image_files))
    
    if not image_files:
        print(f"エラー: '{src_image_dir}' ディレクトリに画像ファイルが見つかりません。")
        sys.exit(1)
    
    print(f"合計 {len(image_files)} 枚の画像が見つかりました。処理を開始します...")
    
    # InsightFaceの初期化
    print("InsightFaceモデルをロードしています...")
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))
    
    # 結果を保存するデータ構造
    result = {
        'vectors': [],       # 特徴ベクトルの配列
        'face_info': []      # 顔情報（元画像、切り出し後の画像パス、バウンディングボックスなど）
    }
    
    vector_index = 0
    
    # 各画像から顔を検出し、特徴ベクトルを抽出
    for img_path in image_files:
        print(f"処理中: {img_path}")
        
        # 画像ファイル名（拡張子なし）を取得
        image_filename = os.path.splitext(os.path.basename(img_path))[0]
        
        try:
            img = Image.open(img_path).convert('RGB')
            img_array = np.array(img)
            
            # 顔検出
            faces = app.get(img_array)
            
            if not faces:
                print(f"  警告: 画像に顔が検出されませんでした: {img_path}")
                continue
            
            # 各顔の特徴ベクトルを正規化して保存
            for i, face in enumerate(faces):
                # L2正規化
                embedding = face.embedding / np.linalg.norm(face.embedding)
                
                # バウンディングボックスを取得
                bbox = face.bbox.astype(int)
                x1, y1, x2, y2 = bbox
                
                # マージンを追加
                width, height = x2 - x1, y2 - y1
                margin_w, margin_h = int(width * args.margin), int(height * args.margin)
                
                # マージン付きの座標を計算（画像の範囲内に収める）
                x1_margin = max(0, x1 - margin_w)
                y1_margin = max(0, y1 - margin_h)
                x2_margin = min(img.width, x2 + margin_w)
                y2_margin = min(img.height, y2 + margin_h)
                
                # 顔領域を切り取り
                face_img = img.crop((x1_margin, y1_margin, x2_margin, y2_margin))
                
                # 保存するファイル名（元の画像名_顔番号.jpg）
                face_filename = f"idol_{image_filename}_face{i+1}.jpg"
                face_path = os.path.join(idol_faces_dir, face_filename)
                
                # 顔画像を保存
                face_img.save(face_path, quality=95)
                
                # ベクトルと顔情報を結果に追加
                result['vectors'].append(embedding.tolist())
                result['face_info'].append({
                    'vector_index': vector_index,
                    'original_image': img_path,
                    'face_index': i + 1,
                    'face_image': face_path,
                    'bbox': [int(x1), int(y1), int(x2), int(y2)]
                })
                
                print(f"  顔 {i+1}/{len(faces)} を処理し、保存しました: {face_path}")
                vector_index += 1
                
                # 最大数に達したら終了
                if vector_index >= args.max_faces:
                    break
            
            # 最大数に達したら終了
            if vector_index >= args.max_faces:
                print(f"最大顔数 {args.max_faces} に到達しました。")
                break
        
        except Exception as e:
            print(f"  エラー: 画像処理中に例外が発生しました: {e}")
            continue
    
    # 結果の保存
    output_path = os.path.join(output_dir, args.output)
    if result['vectors']:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"合計 {len(result['vectors'])} 個の顔特徴ベクトルを {output_path} に保存しました。")
        print(f"切り取った顔画像は {idol_faces_dir} に保存されています。")
    else:
        print("エラー: 有効な顔が検出されませんでした。")
        sys.exit(1)

if __name__ == "__main__":
    main() 
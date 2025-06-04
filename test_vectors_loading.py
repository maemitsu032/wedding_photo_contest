#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
target_vectorsディレクトリのJSONファイル読み込みテスト
"""

import os
import glob
import json
import numpy as np

def test_load_target_vectors():
    """target_vectorsディレクトリのJSONファイルをすべて読み込みテスト"""
    target_vectors_dir = "functions/target_vectors"
    target_vectors = {}
    
    print(f"ターゲットベクトルディレクトリ: {target_vectors_dir}")
    
    # ディレクトリの存在確認
    if not os.path.exists(target_vectors_dir):
        print(f"エラー: ディレクトリが見つかりません: {target_vectors_dir}")
        return False
    
    # JSONファイルのリストを取得
    vector_files = glob.glob(os.path.join(target_vectors_dir, "*.json"))
    
    if not vector_files:
        print(f"エラー: JSONファイルが見つかりません: {target_vectors_dir}")
        return False
    
    print(f"発見したJSONファイル: {len(vector_files)}個")
    
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
                print(f"  検出: 辞書形式 - 'vectors'キーから{len(vectors)}個のベクトルを読み込み")
            elif isinstance(json_data, list):
                # 直接配列形式
                vectors = np.asarray(json_data)
                print(f"  検出: 配列形式 - {len(vectors)}個のベクトルを直接読み込み")
            else:
                print(f"  警告: 未知の形式 - 変換を試みます")
                vectors = np.asarray(json_data)
            
            target_vectors[target_name] = vectors
            print(f"  成功: ターゲット '{target_name}' - ベクトル形状: {vectors.shape}")
            
            # 最初の数個のベクトル要素を表示
            if len(vectors.shape) > 1 and vectors.shape[0] > 0:
                first_vector = vectors[0]
                print(f"  サンプル: 最初のベクトル (先頭5要素): {first_vector[:5]}")
            elif len(vectors.shape) == 1 and vectors.shape[0] > 0:
                print(f"  サンプル: ベクトル (先頭5要素): {vectors[:5]}")
            
        except Exception as e:
            print(f"  エラー: ファイル '{vector_file}' の読み込み失敗: {e}")
    
    print("\n読み込み結果:")
    for target_name, vectors in target_vectors.items():
        print(f"- {target_name}: 形状 {vectors.shape}")
    
    return len(target_vectors) > 0

if __name__ == "__main__":
    print("ターゲットベクトル読み込みテスト開始\n" + "-" * 50)
    success = test_load_target_vectors()
    print("-" * 50)
    print(f"テスト結果: {'成功' if success else '失敗'}") 
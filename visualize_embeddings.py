#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
アイドル顔ベクトルの可視化
functions/idol_vectors.jsonに保存された顔ベクトルを2次元に縮約して可視化します。
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import japanize_matplotlib  # 日本語フォントのサポートを追加
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import os

def main():
    # 保存された顔ベクトルを読み込み
    idol_vectors_path = 'functions/idol_vectors.json'

    with open(idol_vectors_path, 'r') as f:
        idol_vectors = json.load(f)

    # NumPy配列に変換
    idol_vectors_np = np.array(idol_vectors)
    print(f"顔ベクトルの形状: {idol_vectors_np.shape}")

    # ======== PCAによる可視化 ========
    # PCAで2次元に縮約
    pca = PCA(n_components=2)
    vectors_pca = pca.fit_transform(idol_vectors_np)

    # 結果の表示
    plt.figure(figsize=(10, 8))
    plt.scatter(vectors_pca[:, 0], vectors_pca[:, 1], s=100)

    # ポイントにラベルを付ける
    for i in range(len(vectors_pca)):
        plt.annotate(f"Face {i+1}", (vectors_pca[i, 0], vectors_pca[i, 1]), 
                     xytext=(5, 5), textcoords='offset points')

    plt.title('アイドル顔ベクトル - PCA 2D可視化')
    plt.xlabel('第1主成分')
    plt.ylabel('第2主成分')
    plt.grid(True)
    plt.savefig('pca_visualization.png')
    plt.close()
    
    print(f"PCA 2D可視化を保存しました: pca_visualization.png")
    print(f"説明分散比率: {pca.explained_variance_ratio_}")
    print(f"累積説明分散比率: {sum(pca.explained_variance_ratio_):.4f}")

    # ======== t-SNEによる可視化 ========
    # t-SNEのperplexityパラメータを調整（データが少ない場合は小さい値が良い）
    perplexity_val = min(2, len(idol_vectors_np) - 1)
    
    # t-SNEで2次元に縮約
    tsne = TSNE(n_components=2, perplexity=perplexity_val, random_state=42, n_iter=1000)
    vectors_tsne = tsne.fit_transform(idol_vectors_np)

    # 結果の表示
    plt.figure(figsize=(10, 8))
    plt.scatter(vectors_tsne[:, 0], vectors_tsne[:, 1], s=100)

    # ポイントにラベルを付ける
    for i in range(len(vectors_tsne)):
        plt.annotate(f"Face {i+1}", (vectors_tsne[i, 0], vectors_tsne[i, 1]), 
                     xytext=(5, 5), textcoords='offset points')

    plt.title('アイドル顔ベクトル - t-SNE 2D可視化')
    plt.xlabel('次元1')
    plt.ylabel('次元2')
    plt.grid(True)
    plt.savefig('tsne_visualization.png')
    plt.close()
    
    print(f"t-SNE 2D可視化を保存しました: tsne_visualization.png")

    # ======== コサイン類似度 ========
    # 類似度計算（ベクトルは既に正規化されていると仮定）
    similarity_matrix = np.dot(idol_vectors_np, idol_vectors_np.T)

    # ヒートマップでの可視化
    plt.figure(figsize=(10, 8))
    plt.imshow(similarity_matrix, cmap='viridis')
    plt.colorbar(label='コサイン類似度')

    # 軸のラベル
    plt.xticks(range(len(idol_vectors_np)), [f"Face {i+1}" for i in range(len(idol_vectors_np))])
    plt.yticks(range(len(idol_vectors_np)), [f"Face {i+1}" for i in range(len(idol_vectors_np))])

    # 各セルに値を表示
    for i in range(len(idol_vectors_np)):
        for j in range(len(idol_vectors_np)):
            plt.text(j, i, f"{similarity_matrix[i, j]:.2f}", ha="center", va="center", color="w")

    plt.title('アイドル顔ベクトル間のコサイン類似度')
    plt.tight_layout()
    plt.savefig('cosine_similarity.png')
    plt.close()
    
    print(f"コサイン類似度を保存しました: cosine_similarity.png")

    # ======== ユークリッド距離 ========
    # 距離計算
    n = len(idol_vectors_np)
    distance_matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(n):
            distance_matrix[i, j] = np.sqrt(np.sum((idol_vectors_np[i] - idol_vectors_np[j])**2))

    # ヒートマップでの可視化
    plt.figure(figsize=(10, 8))
    plt.imshow(distance_matrix, cmap='plasma')
    plt.colorbar(label='ユークリッド距離')

    # 軸のラベル
    plt.xticks(range(len(idol_vectors_np)), [f"Face {i+1}" for i in range(len(idol_vectors_np))])
    plt.yticks(range(len(idol_vectors_np)), [f"Face {i+1}" for i in range(len(idol_vectors_np))])

    # 各セルに値を表示
    for i in range(len(idol_vectors_np)):
        for j in range(len(idol_vectors_np)):
            plt.text(j, i, f"{distance_matrix[i, j]:.2f}", ha="center", va="center", color="w")

    plt.title('アイドル顔ベクトル間のユークリッド距離')
    plt.tight_layout()
    plt.savefig('euclidean_distance.png')
    plt.close()
    
    print(f"ユークリッド距離を保存しました: euclidean_distance.png")
    
    print("\n考察:")
    print("1. PCAによる2次元可視化では、全体の分散のうちどれだけが最初の2つの主成分で説明できているかがわかります")
    print("2. t-SNEによる可視化では、ベクトル間の局所的な類似性がより強調されます")
    print("3. コサイン類似度のヒートマップでは、対角線上の値は常に1（自分自身との類似度）、それ以外の値が顔同士の類似度を表します")
    print("4. ユークリッド距離のヒートマップでは、対角線上の値は常に0（自分自身との距離）、値が小さいほど顔同士が近いことを示します")
    print("\n顔ベクトル間の距離が近いほど、顔の特徴が似ていることを示しています。")
    print("このような情報は、顔認識システムのチューニングや、類似した顔をグループ化する際に役立ちます。")

if __name__ == "__main__":
    main() 
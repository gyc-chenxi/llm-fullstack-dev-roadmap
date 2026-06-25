"""
Embedding 模型封装
====================

使用 BAAI/bge-m3 (SentenceTransformer) 生成文本向量。

BGE-M3 特性：
  - 多语言：中英文混合训练，适合中国企业内部文档
  - 多粒度：支持 dense (1024维) + sparse (词汇权重) 双路编码
  - 最大长度 8192 token，远超传统 512 token 限制

数据流：
  texts: list[str] → model.encode(texts, normalize_embeddings=True, batch_size=16)
  → vectors: [len(texts), 1024] float32 list

设备选择：MPS (Apple Silicon) > CPU（不能使用 CUDA）
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import torch
from sentence_transformers import SentenceTransformer


@dataclass
class EmbeddingModel:
    """SentenceTransformer 封装。

    batch_size=16: Apple Silicon 32GB 上 BGE-M3 的合理批大小，
    过大可能触发 OOM，过小会降低吞入吞吐量。
    normalize_embeddings=True: 使所有向量模长为 1，适合余弦相似度检索。
    """

    model_name: str
    model: SentenceTransformer
    batch_size: int = 16

    def encode(self, texts: list[str]) -> list[list[float]]:
        """将文本列表编码为归一化向量列表。

        Returns: [n_texts, 1024] float 列表
        """
        if not texts:
            return []

        vectors = self.model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vectors.tolist()


def choose_device() -> str:
    """选择 Embedding 模型的运行设备（优先 MPS）。"""
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def build_embedding_model() -> EmbeddingModel:
    """从环境变量构建 EmbeddingModel 单例。"""
    model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "16"))
    device = choose_device()

    model = SentenceTransformer(model_name, device=device)

    return EmbeddingModel(
        model_name=model_name,
        model=model,
        batch_size=batch_size,
    )

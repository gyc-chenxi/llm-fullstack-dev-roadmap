from __future__ import annotations

import os
from dataclasses import dataclass

import torch
from sentence_transformers import SentenceTransformer


@dataclass
class EmbeddingModel:
    model_name: str
    model: SentenceTransformer
    batch_size: int = 16

    def encode(self, texts: list[str]) -> list[list[float]]:
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
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def build_embedding_model() -> EmbeddingModel:
    model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "16"))
    device = choose_device()

    model = SentenceTransformer(model_name, device=device)

    return EmbeddingModel(
        model_name=model_name,
        model=model,
        batch_size=batch_size,
    )
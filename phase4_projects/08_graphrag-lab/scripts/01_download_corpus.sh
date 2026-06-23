#!/bin/bash
# === P8 GraphRAG Lab — Corpus Download ===
# Downloads 50-80 AI/ML themed documents from Wikipedia + arXiv.
# Output: data/raw/*.txt
#
# Usage:
#   bash scripts/01_download_corpus.sh
#   or: make download-corpus
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DATA_DIR="$PROJECT_DIR/data/raw"
mkdir -p "$DATA_DIR"

echo "[corpus] fetching Wikipedia + arXiv to $DATA_DIR..."
echo "[corpus] this may take 2-5 minutes depending on network..."
echo ""

cd "$PROJECT_DIR"
PYTHONPATH=. conda run -n cxllm --no-capture-output python - << 'PYEOF'
import os, sys, time, random

DATA_DIR = os.environ.get("DATA_DIR", "data/raw")
os.makedirs(DATA_DIR, exist_ok=True)

import wikipedia
wikipedia.set_user_agent("GraphRAG-Lab/1.0 (research-project@example.com)")

# ------------------------------------------------------------------
# Wikipedia topics — curated AI/ML knowledge graph seed corpus
# ------------------------------------------------------------------
WIKI_TOPICS = [
    # Foundations
    "Transformer (deep learning architecture)",
    "Attention (machine learning)",
    "BERT (language model)",
    "GPT-3", "GPT-4",
    "Generative pre-trained transformer",
    "Self-supervised learning",
    "Transfer learning",
    "Fine-tuning (deep learning)",
    "Neural machine translation",
    # Architectures
    "Large language model",
    "Prompt engineering",
    "Residual neural network",
    "Long short-term memory",
    "Recurrent neural network",
    "Convolutional neural network",
    "Graph neural network",
    "Variational autoencoder",
    "Generative adversarial network",
    "Diffusion model",
    "Vision transformer",
    # Training
    "Backpropagation",
    "Stochastic gradient descent",
    "Adam (optimizer)",
    "Batch normalization",
    "Dropout (neural networks)",
    "Overfitting",
    # NLP
    "Word embedding",
    "Word2vec",
    "Byte pair encoding",
    "Tokenization (data security)",
    "Named-entity recognition",
    "Sentiment analysis",
    "Question answering",
    "Text summarization",
    # RAG & Search
    "Retrieval-augmented generation",
    "Knowledge graph",
    "Semantic search",
    "Information retrieval",
    "TF-IDF",
    "Okapi BM25",
    "FAISS",
    "Vector database",
    # Efficiency
    "Knowledge distillation",
    "Quantization (machine learning)",
    "Low-rank adaptation",
    "Parameter-efficient fine-tuning",
    # RL & Alignment
    "Reinforcement learning",
    "Reinforcement learning from human feedback",
    "Proximal policy optimization",
    "Deep Q-network",
    # Vision
    "Object detection",
    "Image segmentation",
    "CLIP (contrastive language-image pre-training)",
    # Benchmarks & Infra
    "ImageNet", "SQuAD", "GLUE benchmark", "MMLU",
    "MLOps", "Ray (software)", "Apache Spark", "Kubernetes",
]

print(f"[corpus] fetching {len(WIKI_TOPICS)} Wikipedia articles...")
count = 0
for i, topic in enumerate(WIKI_TOPICS):
    try:
        results = wikipedia.search(topic, results=1)
        if not results:
            print(f"  [{i+1:2d}/{len(WIKI_TOPICS)}] SKIP (no results): {topic}")
            continue
        page = wikipedia.page(results[0], auto_suggest=False)
        title = page.title.replace("/", "_").replace(" ", "_")
        # Summary + first portion of content (cap at ~5000 chars to keep corpus lean)
        content = f"# {page.title}\n\n{page.summary}\n\n"
        try:
            full = page.content
            if len(full) > 5000:
                full = full[:5000]
            content += full
        except Exception:
            pass
        filename = f"wiki_{title[:80]}.txt"
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        count += 1
        print(f"  [{i+1:2d}/{len(WIKI_TOPICS)}] OK  {filename} ({len(content):,} chars)")
        time.sleep(random.uniform(0.3, 0.8))
    except Exception as e:
        print(f"  [{i+1:2d}/{len(WIKI_TOPICS)}] SKIP ({type(e).__name__}): {topic}")

print(f"\n[corpus] Wikipedia: {count} articles written to {DATA_DIR}/")

# ------------------------------------------------------------------
# arXiv abstracts — landmark papers
# ------------------------------------------------------------------
ARXIV_QUERIES = [
    ("1706.03762", "Attention_Is_All_You_Need"),
    ("1810.04805", "BERT_Pre-training"),
    ("2005.14165", "GPT-3_Language_Models"),
    ("2106.09685", "LoRA_Low_Rank_Adaptation"),
    ("2005.11401", "RAG_Retrieval_Augmented_Generation"),
    ("2201.11903", "Chain_of_Thought_Prompting"),
    ("2203.02155", "InstructGPT"),
    ("2302.13971", "LLaMA_Open_Efficient"),
    ("2205.01068", "FlashAttention"),
    ("2001.08361", "Scaling_Laws_Neural_Language_Models"),
    ("2307.09288", "Llama_2_Open_Foundation"),
    ("2310.06825", "Mistral_7B"),
    ("2312.00738", "Mamba_Linear_Time_Sequence"),
    ("2305.14314", "QLoRA_Efficient_Fine-tuning"),
    ("1910.03771", "T5_Text_to_Text_Transfer_Transformer"),
]

print(f"\n[corpus] fetching {len(ARXIV_QUERIES)} arXiv abstracts...")
arxiv_count = 0
for arxiv_id, label in ARXIV_QUERIES:
    try:
        import arxiv
        client = arxiv.Client()
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(client.results(search))
        content = f"# {paper.title}\n\n"
        content += f"Authors: {', '.join(a.name for a in paper.authors)}\n"
        content += f"Published: {paper.published.strftime('%Y-%m-%d')}\n"
        content += f"arXiv ID: {arxiv_id}\n"
        content += f"Categories: {', '.join(paper.categories)}\n\n"
        content += f"## Abstract\n\n{paper.summary}\n"
        filename = f"arxiv_{label[:80]}.txt"
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        arxiv_count += 1
        print(f"  [{arxiv_count:2d}/{len(ARXIV_QUERIES)}] OK  {filename}")
        time.sleep(random.uniform(0.5, 1.0))
    except Exception as e:
        print(f"  SKIP arxiv:{arxiv_id} ({type(e).__name__}): {e}")

print(f"\n[corpus] arXiv: {arxiv_count} abstracts")
print(f"[corpus] TOTAL: {count + arxiv_count} documents in {DATA_DIR}/")
PYEOF

echo ""
echo "[corpus] === Download complete ==="
echo "Raw files: $(ls -1 "$DATA_DIR" | wc -l)"
echo ""
echo "Sample listing:"
ls -lh "$DATA_DIR" | head -20

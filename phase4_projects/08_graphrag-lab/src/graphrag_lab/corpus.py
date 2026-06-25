"""
语料构建工具
=============

从 Wikipedia 和 arXiv 获取 AI/ML 领域文档，构建本地语料库。

数据流：
  DEFAULT_WIKI_TOPICS (52 个) → wikipedia.search + wikipedia.page
    → 提取 summary + content (截断 max_chars=5000)
    → data/raw/wiki_{title}.txt

  DEFAULT_ARXIV_IDS (15 篇) → arxiv.Search + paper.summary
    → 提取 title, authors, abstract
    → data/raw/arxiv_{label}.txt

速率限制：
  - Wikipedia: random sleep 0.3-0.8s（避免被封 IP）
  - arXiv: random sleep 0.5-1.0s

用法：
  PYTHONPATH=. python src/graphrag_lab/corpus.py --output data/raw
"""

import os
import time
import random
import argparse
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


DEFAULT_WIKI_TOPICS = [
    "Transformer (deep learning architecture)",
    "Attention (machine learning)",
    "BERT (language model)",
    "GPT-3", "GPT-4",
    "Generative pre-trained transformer",
    "Self-supervised learning",
    "Transfer learning",
    "Fine-tuning (deep learning)",
    "Large language model",
    "Prompt engineering",
    "Residual neural network",
    "Long short-term memory",
    "Graph neural network",
    "Diffusion model",
    "Vision transformer",
    "Backpropagation",
    "Stochastic gradient descent",
    "Adam (optimizer)",
    "Batch normalization",
    "Dropout (neural networks)",
    "Overfitting",
    "Word embedding",
    "Word2vec",
    "Byte pair encoding",
    "Named-entity recognition",
    "Sentiment analysis",
    "Question answering",
    "Text summarization",
    "Retrieval-augmented generation",
    "Knowledge graph",
    "Semantic search",
    "Information retrieval",
    "TF-IDF",
    "Okapi BM25",
    "FAISS",
    "Vector database",
    "Knowledge distillation",
    "Quantization (machine learning)",
    "Low-rank adaptation",
    "Parameter-efficient fine-tuning",
    "Reinforcement learning",
    "Reinforcement learning from human feedback",
    "Proximal policy optimization",
    "Object detection",
    "Image segmentation",
    "CLIP (contrastive language-image pre-training)",
    "ImageNet", "SQuAD", "GLUE benchmark", "MMLU",
    "MLOps", "Ray (software)", "Apache Spark", "Kubernetes",
]

DEFAULT_ARXIV_IDS = [
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


def fetch_wikipedia_article(topic: str, max_chars: int = 5000) -> Optional[str]:
    """从 Wikipedia 获取单篇文章。

    Returns:
        Markdown 格式文本 (# title + summary)，或 None（获取失败）
    """
    try:
        import wikipedia
    except ImportError:
        logger.error("wikipedia package not installed. Run: pip install wikipedia")
        return None

    try:
        results = wikipedia.search(topic, results=1)
        if not results:
            logger.debug("No Wikipedia results for: %s", topic)
            return None
        page = wikipedia.page(results[0], auto_suggest=False)
        content = f"# {page.title}\n\n{page.summary}\n\n"
        try:
            full = page.content
            if len(full) > max_chars:
                full = full[:max_chars]
            content += full
        except Exception:
            pass
        return content
    except Exception as e:
        logger.debug("Wikipedia fetch failed for '%s': %s", topic, e)
        return None


def fetch_arxiv_abstract(arxiv_id: str) -> Optional[str]:
    """从 arXiv 获取单篇论文摘要。

    Returns:
        Markdown 格式文本 (# title + authors + abstract)，或 None
    """
    try:
        import arxiv
    except ImportError:
        logger.error("arxiv package not installed. Run: pip install arxiv")
        return None

    try:
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(search.results())
        content = f"# {paper.title}\n\n"
        content += f"Authors: {', '.join(a.name for a in paper.authors)}\n"
        content += f"Published: {paper.published.strftime('%Y-%m-%d')}\n"
        content += f"arXiv ID: {arxiv_id}\n"
        content += f"Categories: {', '.join(paper.categories)}\n\n"
        content += f"## Abstract\n\n{paper.summary}\n"
        return content
    except Exception as e:
        logger.debug("arXiv fetch failed for '%s': %s", arxiv_id, e)
        return None


def build_corpus(
    output_dir: str,
    topics: List[str] | None = None,
    arxiv_ids: List[tuple] | None = None,
    max_chars_per_article: int = 5000,
) -> int:
    """下载 Wikipedia + arXiv 文章到输出目录。

    Returns:
        成功写入的文件数
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    topics = topics or DEFAULT_WIKI_TOPICS
    arxiv_ids = arxiv_ids or DEFAULT_ARXIV_IDS

    count = 0

    logger.info("Fetching %d Wikipedia articles...", len(topics))
    for i, topic in enumerate(topics):
        content = fetch_wikipedia_article(topic, max_chars=max_chars_per_article)
        if content is None:
            continue
        title = topic.replace("/", "_").replace(" ", "_")[:80]
        filepath = output / f"wiki_{title}.txt"
        filepath.write_text(content, encoding="utf-8")
        count += 1
        if i % 10 == 0:
            logger.info("  [%d/%d] Wikipedia articles written", count, len(topics))
        time.sleep(random.uniform(0.3, 0.8))

    logger.info("Wikipedia: %d articles", count)
    wiki_count = count

    logger.info("Fetching %d arXiv abstracts...", len(arxiv_ids))
    for arxiv_id, label in arxiv_ids:
        content = fetch_arxiv_abstract(arxiv_id)
        if content is None:
            continue
        filepath = output / f"arxiv_{label[:80]}.txt"
        filepath.write_text(content, encoding="utf-8")
        count += 1
        time.sleep(random.uniform(0.5, 1.0))

    logger.info("arXiv: %d abstracts", count - wiki_count)
    logger.info("TOTAL: %d documents in %s/", count, output_dir)
    return count


def main():
    parser = argparse.ArgumentParser(
        description="Download AI/ML corpus (Wikipedia + arXiv)"
    )
    parser.add_argument("--output", default="data/raw",
                        help="Output directory for .txt files")
    parser.add_argument("--topics", type=str, default=None,
                        help="Comma-separated Wikipedia topics (uses defaults if omitted)")
    parser.add_argument("--arxiv-ids", type=str, default=None,
                        help="Comma-separated arXiv IDs (uses defaults if omitted)")
    parser.add_argument("--max-chars", type=int, default=5000,
                        help="Max characters per article")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="[corpus] %(message)s")

    topics = args.topics.split(",") if args.topics else None
    arxiv_ids = None
    if args.arxiv_ids:
        arxiv_ids = [(aid.strip(), aid.strip()) for aid in args.arxiv_ids.split(",")]

    count = build_corpus(
        output_dir=args.output,
        topics=topics,
        arxiv_ids=arxiv_ids,
        max_chars_per_article=args.max_chars,
    )
    print(f"\n[corpus] ✓ {count} documents written to {args.output}/")


if __name__ == "__main__":
    main()

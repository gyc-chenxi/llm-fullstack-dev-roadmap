# 📊 06 — RAG 评估：用 Ragas 量化检索与生成质量

> 🎯 **目标**：构建 RAG 评估体系，知道 faithfulness 低怎么修、context_precision 低怎么修。
> ⏱️ 预计时间：2 天

---

## 📋 评估维度速查

| 指标 | 衡量什么 | 低分症状 | 修复方向 |
|------|---------|---------|----------|
| **Faithfulness** | 答案是否忠实于检索结果 | 模型在编造信息 | 加强引用约束 + 降低 temperature |
| **Context Precision** | 检索结果中真正有用的比例 | 检索到很多无关文档 | 优化 chunk 尺寸 / 加 Reranker |
| **Context Recall** | 答案需要的资料是否被检索到 | 漏掉关键文档 | 优化检索策略 / Query Rewrite |
| **Answer Relevancy** | 答案是否切题 | 答非所问 | 优化 Prompt 模板 |

---

## 1️⃣ Ragas 环境搭建

```bash
pip install ragas datasets pandas
```

```python
from ragas import evaluate, EvaluationDataset
from ragas.metrics import faithfulness, context_precision, context_recall, answer_relevancy
from ragas.llms import LangchainLLMWrapper
from langchain_openai import ChatOpenAI
import pandas as pd

# Ragas 内部用 LLM 做评估（默认 GPT-4o-mini）
evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini", temperature=0))

# 准备评估数据
eval_dataset = EvaluationDataset.from_dict({
    "question": [
        "Transformer 的核心组件是什么？",
        "什么是 KV Cache？",
        "LoRA 的 rank 参数如何选择？",
        # ... 至少 10 条
    ],
    "answer": [rag_answers],       # RAG 系统生成的答案
    "contexts": [rag_contexts],    # RAG 检索到的文档列表
    "ground_truth": [ground_truths],  # 人工标注的标准答案
})
```

---

## 2️⃣ 评估结果解读与改进闭环

```python
result = evaluate(eval_dataset, metrics=[
    faithfulness, context_precision, context_recall, answer_relevancy
], llm=evaluator_llm)
df = result.to_pandas()
print(df.describe())

# 改进闭环：
for metric, threshold, fix_action in [
    ('faithfulness', 0.7, '加强 System Prompt 引用约束，temperature 降至 0'),
    ('context_precision', 0.6, 'chunk_size 减到 300 + 加 Reranker'),
    ('context_recall', 0.6, '加 Query Rewrite + hybrid search'),
    ('answer_relevancy', 0.7, '优化 Prompt 模板，加 "只回答问的问题"'),
]:
    avg_score = df[metric].mean()
    if avg_score < threshold:
        print(f"⚠️ {metric}={avg_score:.2f} < {threshold} → {fix_action}")
```

---

## 3️⃣ A/B 测试脚本

```python
configs = {
    'chunk_300': {'chunk_size': 300, 'use_reranker': False},
    'chunk_500_rerank': {'chunk_size': 500, 'use_reranker': True},
}

for name, cfg in configs.items():
    rag = build_rag(cfg)
    answers, contexts = [], []
    for q in test_questions:
        a, c = rag.ask(q)
        answers.append(a); contexts.append(c)
    score = evaluate(EvaluationDataset.from_dict({
        "question": test_questions, "answer": answers,
        "contexts": contexts, "ground_truth": ground_truths,
    }), metrics=[faithfulness, context_precision], llm=evaluator_llm)
    print(f"{name}: faithfulness={score['faithfulness']:.2f}, precision={score['context_precision']:.2f}")
```

---

## 🚨 翻车现场

| 现象 | 原因 | 解决 |
|------|------|------|
| Ragas 评分全 0 | contexts 格式不对 | contexts 必须是 list[list[str]] |
| 评估太贵 | 每条都用 GPT-4 打分 | 用 gpt-4o-mini 或本地模型 |
| faithfulness 总偏高 | LLM 评估器"放水" | 加 ground_truth 对照 |

---

## ✅ 产出物 Checklist

- [ ] 搭建 Ragas 环境 + 跑通评估
- [ ] 构建 20 条测试集
- [ ] 跑 A/B 测试（至少对比 2 种 RAG 配置）
- [ ] 根据评估结果改进 RAG 系统

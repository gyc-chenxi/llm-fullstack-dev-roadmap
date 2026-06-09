# 📊 06 — RAG 评估：Ragas + TruLens 量化评测体系

> 🎯 **目标**：用 Ragas + TruLens 建立完整的 RAG 质量评估体系，做到"改完知道有没有变好"。
> ⏱️ 预计时间：2 天

---

## 📋 为什么要做量化评估？

| 没有评估 | 有评估 |
|:--------|:------|
| "感觉效果好多了" | "faithfulness 从 0.72 提升到 0.88" |
| 改完不知道有没有变坏 | A/B 测试告诉你哪个配置更好 |
| 面试讲不出效果 | "我的 RAG 系统 faithfulness 0.88，context_precision 0.82" |

---

## 1️⃣ 评估维度速查表

| 指标 | 衡量什么 | 低分症状 | 🔧 修复方向 |
|:-----|:--------|:--------|:-----------|
| **Faithfulness** | 答案是否忠于检索文档 | 模型在编造不存在的信息 | 加强引用约束 Prompt + 降低 temperature |
| **Context Precision** | 检索结果中真正有用的比例 | 检索到很多无关文档 | 优化 chunk_size + 加 Reranker |
| **Context Recall** | 需要的文档是否被检索到 | 漏掉关键文档 | Query Rewrite + hybrid search |
| **Answer Relevancy** | 答案是否切题 | 答非所问 | 优化 Prompt 模板 |
| **Answer Correctness** | 答案与 ground_truth 的一致性 | 事实错误 | 检查检索质量 + LLM 生成质量 |

---

## 2️⃣ Ragas 环境搭建

```bash
pip install ragas>=0.1.0 datasets pandas langchain-openai
```

```python
from ragas import evaluate, EvaluationDataset, SingleTurnSample
from ragas.metrics import (
    faithfulness, context_precision, context_recall, 
    answer_relevancy, answer_correctness,
)
from ragas.llms import LangchainLLMWrapper
from langchain_openai import ChatOpenAI
import pandas as pd

# 用便宜的模型做评估（省成本）
evaluator_llm = LangchainLLMWrapper(
    ChatOpenAI(model="gpt-4o-mini", temperature=0)
)

# 构建评估数据集
eval_dataset = EvaluationDataset.from_dict({
    "question": [
        "Transformer 的核心组件是什么？",
        "什么是 KV Cache？为什么它只缓存 K 和 V？",
        "LoRA 的 rank 参数如何选择？",
        "PagedAttention 和普通 Attention 的区别？",
        "为什么现代大模型倾向用 GQA 而不是 MHA？",
    ],
    "answer": [],       # 你的 RAG 系统生成的答案
    "contexts": [],     # RAG 检索到的文档列表 list[list[str]]
    "ground_truth": [
        "Transformer 核心组件包括 Self-Attention、FFN、LayerNorm 和 Residual Connection",
        "KV Cache 缓存历史 token 的 Key 和 Value，避免重复计算。不缓存 Q 因为 Q 只属于当前 token",
        "LoRA rank 一般选 8-64，r=16 是甜点。r 越高容量越大但可能过拟合",
        "PagedAttention 不改变 Attention 公式，而是改变 KV Cache 的内存管理方式，用分页避免碎片化",
        "GQA 减少 KV heads 数量，降低 KV Cache 带宽瓶颈，是 MHA 质量和 MQA 速度的折中",
    ],
})
```

---

## 3️⃣ 完整评估 + 改进闭环

```python
def evaluate_rag_system(rag_system, dataset) -> pd.DataFrame:
    """跑评估 → 返回结果 DataFrame"""
    answers, contexts = [], []
    for sample in dataset:
        ans, ctx = rag_system.query(sample["question"])
        answers.append(ans)
        contexts.append(ctx)
    
    eval_data = EvaluationDataset.from_dict({
        "question": [s["question"] for s in dataset],
        "answer": answers,
        "contexts": contexts,
        "ground_truth": [s["ground_truth"] for s in dataset],
    })
    
    result = evaluate(
        eval_data,
        metrics=[
            faithfulness, context_precision, 
            context_recall, answer_relevancy,
        ],
        llm=evaluator_llm,
    )
    return result.to_pandas()


# --- 改进闭环 ---
df = evaluate_rag_system(my_rag, test_dataset)

# 按指标诊断 + 自动建议修复
FIX_ACTIONS = {
    'faithfulness': {
        'threshold': 0.70,
        'actions': [
            'System Prompt 加"只使用提供的资料回答，不要编造"',
            'temperature 设为 0 或 0.1',
            '要求每个观点标注引用来源 [来源X]',
        ],
    },
    'context_precision': {
        'threshold': 0.60,
        'actions': [
            '减小 chunk_size (当前可能是 500，试 300)',
            '加 Reranker (bge-reranker-v2-m3)',
            '加 metadata 过滤（按文档类型/日期）',
        ],
    },
    'context_recall': {
        'threshold': 0.60,
        'actions': [
            '加 Query Rewrite（把用户问题改写成 3 个检索变体）',
            '用 hybrid search 替代纯向量检索',
            '增加 top_k (当前 5 → 10)',
        ],
    },
}

for metric, cfg in FIX_ACTIONS.items():
    if metric in df.columns:
        avg = df[metric].mean()
        if avg < cfg['threshold']:
            print(f"⚠️ {metric}={avg:.2f} < {cfg['threshold']}")
            for action in cfg['actions']:
                print(f"   → {action}")
```

---

## 4️⃣ TruLens 反馈函数（补 Ragas 盲区）

TruLens 的独特价值：**不需要 ground_truth**，用 LLM 反馈函数即时打分。

```bash
pip install trulens-eval
```

```python
from trulens_eval import Tru, Feedback, TruBasicApp
from trulens_eval.feedback.provider.openai import OpenAI as OpenAIFeedback

provider = OpenAIFeedback(model_engine="gpt-4o-mini")

# 定义反馈函数
f_groundedness = Feedback(
    provider.groundedness_measure_with_cot_reasons,
    name="Groundedness"
).on_output().on_input_output()

f_relevance = Feedback(
    provider.relevance,
    name="Answer Relevance"
).on_input_output()

f_context_relevance = Feedback(
    provider.context_relevance,
    name="Context Relevance"
).on_input().on(TruBasicApp.select_context())

# 包装 RAG 系统
rag_app = TruBasicApp(
    text_to_text=lambda q: my_rag.query(q),
    feedbacks=[f_groundedness, f_relevance, f_context_relevance],
)

# 跑评估
with rag_app as recording:
    for question in test_questions:
        rag_app.call(question)

# 查看结果
tru = Tru()
records, feedback = tru.get_records_and_feedback(app_ids=[rag_app.app_id])
```

---

## 5️⃣ A/B 测试管道

```python
import time
from dataclasses import dataclass

@dataclass
class RAGConfig:
    name: str
    chunk_size: int = 500
    use_hybrid: bool = True
    use_reranker: bool = True
    top_k: int = 5

def ab_test(configs: list[RAGConfig], test_dataset, evaluator_llm) -> pd.DataFrame:
    """跑 A/B 测试，输出对比表"""
    results = []
    for cfg in configs:
        rag = build_rag(**cfg.__dict__)
        t0 = time.time()
        df = evaluate_rag_system(rag, test_dataset)
        elapsed = time.time() - t0
        
        row = {"config": cfg.name, "latency_sec": f"{elapsed:.1f}"}
        for metric in ['faithfulness', 'context_precision', 'context_recall']:
            if metric in df.columns:
                row[metric] = f"{df[metric].mean():.3f}"
        results.append(row)
    
    return pd.DataFrame(results)

# 跑对比
configs = [
    RAGConfig("baseline", chunk_size=500, use_hybrid=False, use_reranker=False),
    RAGConfig("+hybrid", chunk_size=500, use_hybrid=True, use_reranker=False),
    RAGConfig("+reranker", chunk_size=500, use_hybrid=True, use_reranker=True),
    RAGConfig("chunk300+all", chunk_size=300, use_hybrid=True, use_reranker=True),
]
print(ab_test(configs, test_dataset, evaluator_llm))
```

---

## 6️⃣ 评估结果可视化

```python
import matplotlib.pyplot as plt
import numpy as np

def plot_radar(ab_results: pd.DataFrame, metrics: list[str]):
    """雷达图对比多个 RAG 配置"""
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]  # 闭合成圈
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    for _, row in ab_results.iterrows():
        values = [float(row[m]) for m in metrics]
        values += values[:1]
        ax.plot(angles, values, 'o-', linewidth=2, label=row['config'])
        ax.fill(angles, values, alpha=0.1)
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics)
    ax.set_ylim(0, 1)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    ax.set_title("RAG Configuration Comparison", pad=20)
    plt.savefig('rag_ab_radar.png', dpi=150, bbox_inches='tight')

plot_radar(ab_results, ['faithfulness', 'context_precision', 'context_recall', 'answer_relevancy'])
```

---

## 🆕 TruLens vs Ragas 对比

| 维度 | Ragas | TruLens |
|:-----|:-----|:------|
| 需要 ground_truth? | 部分指标需要 | ❌ 不需要（LLM 反馈函数） |
| 评估精度 | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 部署复杂度 | ⭐⭐ | ⭐⭐⭐ |
| 适合场景 | 离线评估 + 数据集测试 | 在线监控 + 实时反馈 |
| 推荐用法 | **建测试集做 A/B 对比** | **生产环境持续监控** |

> 🔥 建议：**Ragas 做离线评测，TruLens 做在线监控**。两者互补，不是替代关系。

---

## 🚨 翻车现场

| 现象 | 原因 | 解决 |
|:-----|:-----|:-----|
| Ragas 评分全 0 | `contexts` 格式应为 `list[list[str]]` | 检查 contexts 是否是双层列表 |
| faithfulness 总偏高(>0.9) | LLM 评估器"放水" | 用更强的评估模型(gpt-4o)或加 ground_truth |
| 评估一次太贵 | 每条都用 GPT-4o 打分，20条×4指标=80次 | 用 gpt-4o-mini，20条合计约 $0.02 |
| A/B 测试结果不稳定 | 测试集太小 | 至少 20 条，覆盖 4 种问题类型 |

---

## ✅ 产出物 Checklist

- [ ] 搭建 Ragas 环境 + 跑通评估
- [ ] 构建 20 条测试集（4 种问题类型各 5 条）
- [ ] 跑 A/B 测试（至少 3 种 RAG 配置）
- [ ] 输出雷达图或柱状图
- [ ] 根据评估结果改进 RAG 系统，记录改进前后的指标变化
- [ ] （可选）接入 TruLens 做在线监控

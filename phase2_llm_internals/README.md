# Phase 2 🧠 大模型底层硬核拆解 + 工业级微调与部署

> **Day 16-28** | ⏱️ 13 天 | 📊 难度 ⭐⭐⭐⭐⭐

---

## 你将在本阶段学会什么

- ✅ Transformer 完整数据流 + 7B 模型每层 Shape 变化
- ✅ Scaled Dot-Product Attention — QKᵀ/√dₖ/Softmax/Causal Mask
- ✅ MHA/MQA/GQA — 三种注意力机制 + KV Cache 带宽瓶颈
- ✅ RoPE 旋转位置编码 — 为什么位置通过旋转进入 Q/K
- ✅ KV Cache 显存公式（精确到字节）+ OOM 排查
- ✅ PagedAttention + Continuous Batching — vLLM 吞吐提升秘密
- ✅ MoE 混合专家 — Router/Top-K Expert/DeepSeekMoE 分析
- ✅ 量化技术 — GPTQ/AWQ/GGUF + 量化级别决策树
- ✅ PyTorch 从零手写 MHA + GQA，与官方对比
- ✅ LoRA/QLoRA 微调实战 + LLaMA-Factory 工业微调
- ✅ vLLM 生产级推理部署 + 并发压测

## 前置要求

- 完成 [Phase 1](../phase1_prompt_api/)（熟悉 LLM API 调用）
- 理解矩阵乘法和 Softmax
- 有 PyTorch 基础（知道 Tensor 和 nn.Module）

## 学习天数与任务表

| Day | 主题 | 文件 | 产出 | ✅ |
|:---:|:-----|:-----|:-----|:--:|
| 16 | Transformer 总览 | `00_transformer.md` | 能画出每层 Shape 流动 | ☐ |
| 17 | Scaled Dot-Product Attention | `01_attention.ipynb` | NumPy 手写 QKᵀ/√dₖ | ☐ |
| 18 | MHA/MQA/GQA | `02_mha_mqa_gqa.ipynb` | KV Cache 带宽对比 | ☐ |
| 19 | RoPE 位置编码 | `03_rope.ipynb` | 二维向量旋转验证 | ☐ |
| 20 | KV Cache + 自回归 | `04_kv_cache.ipynb` | KV Cache 显存计算器 | ☐ |
| 21 | PagedAttention | `05_paged_attention.ipynb` | Static vs Continuous Batching | ☐ |
| 22 | MoE | `06_moe.ipynb` | Toy Router + Top-K | ☐ |
| 23 | 量化技术 | `08_quantization.md` | GGUF 量化实操 | ☐ |
| 24 | 手写 Attention | `09_attention_from_scratch.md` | MHA + GQA 代码 | ☐ |
| 25 | LoRA 微调 | `10_lora_demo.md` + `07_lora_rag_agent.ipynb` | 完整训练循环 | ☐ |
| 26 | LLaMA-Factory | (大纲已规划) | 工业微调流水线 | ☐ |
| 27 | vLLM 部署 | `12_deployment_vllm.md` | vLLM 压测报告 | ☐ |
| 28 | 微调技术全景 | `11_fine-tuning_techniques.md` | SFT/RLHF/DPO 对比 | ☐ |

## 本阶段核心产出

- 📊 **KV Cache 显存计算器** — 精确估算显存
- ✍️ **手写 MHA + GQA** — 与 PyTorch 官方对比
- 🔧 **LoRA 微调脚本** — 完整训练+评估
- 📈 **vLLM 压测报告** — TTFT/TPOT/QPS 基线

## 如何运行本阶段 Demo

```bash
# Jupyter Notebook（Day 17-22 核心实验）
cd phase2_llm_internals
jupyter lab
# 打开 01_attention.ipynb 开始

# 手写 Attention 验证
python -c "
import torch
# 复制 09_attention_from_scratch.md 中的代码
# 运行 test_vs_official() 函数
"

# LoRA 微调（需要 GPU 或有 Apple Silicon）
# 参考 10_lora_demo.md 中的 MLX/PEFT 命令
```

## 验收标准

- [ ] 能用 NumPy 手写 QKᵀ/√dₖ/Softmax/V
- [ ] 能口述 MHA→MQA→GQA 的演变原因和显存差异
- [ ] 能计算 7B 模型在 8K 上下文下的 KV Cache 大小
- [ ] 手写 Attention 与官方实现误差 < 1e-4
- [ ] 跑通至少一次 LoRA 微调

## 常见问题

| 问题 | 解决 |
|:-----|:-----|
| Transformer 公式看不懂 | 先看 Jay Alammar 图解，再看公式 |
| RoPE 的旋转很抽象 | 在 `03_rope.ipynb` 里跑二维可视化 |
| KV Cache 显存算出来不对 | 检查 `num_kv_heads`（不是 `num_attention_heads`） |
| LoRA 参数太多 | 只挂 `q_proj, v_proj`，rank 用 8 |

## 面试可讲点

1. "我手写了 MHA + GQA，与 PyTorch 官方误差 < 1e-4"
2. "我能精确计算 KV Cache 显存，排查过 OOM 问题"
3. "我理解 GQA 的工程动机——KV Cache 带宽是推理瓶颈，不是算力"
4. "我做过 LoRA 微调，知道 r/alpha/target_modules 对效果的影响"

## 面试参考

详见 `_00_7day_deep_dive_reference.md` — 包含面试拷问 Top 2 + 原理级排障场景

## 下一阶段

👉 [Phase 3: RAG 检索增强体系](../phase3_rag/)

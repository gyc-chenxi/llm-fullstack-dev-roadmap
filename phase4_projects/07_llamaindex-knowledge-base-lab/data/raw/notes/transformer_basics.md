# Transformer 基础

## Self-Attention 机制
Self-Attention 是 Transformer 的核心组件。它允许每个位置直接关注序列中的所有位置。

计算公式：Attention(Q,K,V) = softmax(QK^T / sqrt(d_k)) * V

## Multi-Head Attention
多头注意力通过并行运行多个 Self-Attention 来捕获不同子空间的信息。

每个头的计算：
head_i = Attention(QW_i^Q, KW_i^K, VW_i^V)

最后拼接所有头：
MultiHead(Q,K,V) = Concat(head_1, ..., head_h) * W^O

## KV Cache
KV Cache 是一种推理优化技术，通过缓存 Key 和 Value 矩阵避免重复计算。
在自回归生成中，每步只需计算新 token 的 Query，复用之前的 K、V。

优势：
- 将 O(n^2) 的计算量降为 O(n)
- 推理延迟降低 50%-70%
- 是 vLLM、TGI 等推理引擎的核心优化

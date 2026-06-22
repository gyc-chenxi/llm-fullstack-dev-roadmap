# RoPE: 旋转位置编码

## 原理
RoPE (Rotary Position Embedding) 通过旋转矩阵将位置信息编码到 token 的表示中。

核心思想：通过旋转变换，使 Query 和 Key 的内积只依赖于 token 之间的相对位置。

## 数学形式
给定位置 m 的 Query 向量 q 和位置 n 的 Key 向量 k：

f(q, m) = q * e^{imθ}
f(k, n) = k * e^{inθ}

内积：
⟨f(q,m), f(k,n)⟩ = ⟨q, k⟩ * e^{i(m-n)θ}

只依赖于相对位置 (m-n)，而非绝对位置！

## 特点
- 相对位置编码，能自然捕捉 token 间的相对距离
- 与 Self-Attention 机制天然兼容，无需修改 Attention 结构
- 支持长序列外推（extrapolation），可以通过调整 θ 来扩展上下文窗口
- 被 LLaMA、Mistral、Qwen 等主流模型广泛采用

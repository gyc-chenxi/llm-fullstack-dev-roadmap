# 🏗️ 00 — Transformer 架构总览

> 🎯 **目标**：理解 Decoder-only Transformer 的完整数据流，能画出每层的 shape 变化。
> ⏱️ 预计时间：1 天

---

## 📋 为什么 Transformer 是分水岭？

2017 年之前，NLP 领域各自为战：RNN/LSTM 做翻译，CNN 做文本分类。Transformer 出现后，**一个架构统一了所有 NLP 任务**，而且天然适合并行计算（GPU 友好），为大模型 scaling 铺平了道路。

| 架构 | 并行能力 | 长程依赖 | 代表模型 |
|------|---------|---------|----------|
| RNN/LSTM | ❌ 串行 | ⚠️ 梯度消失 | 早期翻译模型 |
| CNN | ✅ | ❌ 感受野有限 | TextCNN |
| **Transformer** | ✅ | ✅ Self-Attention 全局 | **GPT/BERT/LLaMA/Qwen** |

---

## 1️⃣ 整体架构

```
输入文本: "今天天气"
    ↓
Tokenizer → Token IDs: [101, 204, 315, ...]
    ↓
Token Embedding → [B, T, d_model]   例: [1, 4, 4096]
    ↓
┌─────────────────────────────────────────┐
│           N × Decoder Layer              │
│  ┌──────────────────────────────────┐   │
│  │  LayerNorm → Masked Multi-Head   │   │
│  │  Attention → Residual Connection │   │
│  ├──────────────────────────────────┤   │
│  │  LayerNorm → Feed-Forward        │   │
│  │  Network → Residual Connection   │   │
│  └──────────────────────────────────┘   │
│              × 28-32 层                   │
└─────────────────────────────────────────┘
    ↓
LM Head（线性层 + Softmax）→ [B, T, vocab_size]
    ↓
采样 → 下一个 token ID → "真"
```

---

## 2️⃣ 各组件详细拆解

### 📌 Token Embedding

```python
# 把 token ID 映射为稠密向量
token_ids = [101, 204, 315]         # 3 个 token
embedding = nn.Embedding(vocab_size=151936, embedding_dim=4096)
vectors = embedding(token_ids)      # → [3, 4096]
```

### 📌 Masked Multi-Head Self-Attention

```
Q = X @ W_Q    # "我在找什么"
K = X @ W_K    # "我有什么"
V = X @ W_V    # "实际内容"

Attention(Q, K, V) = softmax(QKᵀ / √dₖ + Mask) × V

Mask: 下三角矩阵（防止看到未来 token）
[[  0, -∞, -∞, -∞],
 [  0,  0, -∞, -∞],
 [  0,  0,  0, -∞],
 [  0,  0,  0,  0 ]]
```

> 🔑 关键直觉：每个 token 通过 Q 去 "查询" 所有 token 的 K，找到相关的 → 取其 V 加权求和。除以 √dₖ 防止点积太大导致 softmax 梯度消失。

### 📌 Feed-Forward Network (FFN)

```python
# 两层全连接 + 激活函数
class FFN(nn.Module):
    def __init__(self, d_model=4096, d_ff=14336):
        self.w1 = nn.Linear(d_model, d_ff)   # 升维
        self.w2 = nn.Linear(d_ff, d_model)   # 降维
        self.act = nn.SiLU()                  # SwiGLU 激活

    def forward(self, x):
        return self.w2(self.act(self.w1(x)))
```

> 💡 FFN 存储了模型的大部分"知识"——Attention 决定 "关注哪里"，FFN 决定 "知道了什么"。在 MoE 模型中，FFN 被拆成多个 Expert。

### 📌 Residual Connection（残差连接）

```python
# 每层的输出 = 输入 + 子层处理结果
x = x + self.attention(self.ln1(x))    # Attention 残差
x = x + self.ffn(self.ln2(x))          # FFN 残差
```

> 💡 为什么需要？深层网络梯度会消失，残差连接给梯度一条"高速公路"直通底层。

### 📌 Pre-LayerNorm

```
Post-LN（原版）:  Attention → Add → LN → FFN → Add → LN
Pre-LN（现代）:   LN → Attention → Add → LN → FFN → Add
```

> 💡 Pre-LN 训练更稳定，不需要 warmup。Llama、GPT-3+ 都用 Pre-LN。

---

## 3️⃣ 7B 模型的 Shape 流动全景

```
Input Token IDs:         [1, 128]                          (batch=1, seq=128)
Token Embedding:         [1, 128, 4096]                    (d_model=4096)

进入 Decoder Layer 1:
  LayerNorm:             [1, 128, 4096]                    (shape 不变)
  Q/K/V 投影:            Q:[1, 32, 128, 128]              (32 heads, d_k=128)
  Attention Score:       [1, 32, 128, 128]                (QKᵀ)
  Attention Output:      [1, 128, 4096]                    (合并头)
  残差 +x:               [1, 128, 4096]

  LayerNorm:             [1, 128, 4096]
  FFN gate+up:           [1, 128, 14336]                   (升维 4096→14336)
  FFN down:              [1, 128, 4096]                    (降维 14336→4096)
  残差 +x:               [1, 128, 4096]

... 重复 28 层（Llama 3 8B）...

LM Head:                 [1, 128, 4096] → [1, 128, 128256]   (vocab_size)
Sample:                  取最后一个位置 → token ID
```

---

## 4️⃣ Decoder-only vs Encoder-Decoder

| 特性 | Decoder-only (GPT) | Encoder-Decoder (T5) |
|------|-------------------|---------------------|
| 架构 | 只有 Decoder | Encoder + Decoder |
| Attention | Causal（只看左边） | Encoder 双向 + Decoder Causal |
| 任务统一 | 一切 = 续写 | 需要设计输入格式 |
| 代表 | GPT-4, Llama, Qwen | T5, BART |
| 为什么主流是 Decoder-only? | 架构简单，任何任务都是 "输入→续写"，更好 scale | 特定任务可能更好，但不通用 |

---

## 5️⃣ 面试高频追问

**Q1: "Transformer 相比 RNN 的核心优势？"**
A: 并行计算（训练时所有 token 同时处理，RNN 必须串行）+ 长程依赖（Self-Attention 直接连接任意两个 token，RNN 要经过 O(n) 步）。

**Q2: "为什么除以 √dₖ？"**
A: dₖ 越大，QKᵀ 的点积值越大，softmax 后分布接近 one-hot（梯度接近 0）。除以 √dₖ 让方差稳定在 1。

**Q3: "Pre-LN 和 Post-LN 的区别？"**
A: Post-LN（原版）在残差之后做 LN，训练需要 warmup。Pre-LN（现代）在子层之前做 LN，训练更稳定，广泛用于大模型。

**Q4: "FFN 为什么要先升维再降维？"**
A: 升维 → 给更多"思考空间"，类似 SVM 的核技巧；降维 → 回到原维度，方便残差连接。

---

## 6️⃣ 核心数学公式速查

> 以下公式是面试高频考点，也是理解 LLM 推理本质的关键。每个公式都附带了**工程直觉解读**——因为面试官不会只问"背公式"，而是问"为什么这么设计"。

---

### 📐 公式一：Scaled Dot-Product Attention（缩放点积注意力）

$$
\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^\top}{\sqrt{d_k}}\right) V
$$

其中 $Q, K, V \in \mathbb{R}^{n \times d_k}$，$n$ 为序列长度，$d_k$ 为每个注意力头的维度。

**逐元素展开**：

$$
\text{Attention}_{ij} = \frac{\exp\left( \frac{\mathbf{q}_i \cdot \mathbf{k}_j}{\sqrt{d_k}} \right)}{\sum_{t=1}^{n} \exp\left( \frac{\mathbf{q}_i \cdot \mathbf{k}_t}{\sqrt{d_k}} \right)} \cdot \mathbf{v}_j
$$

**关键工程洞察**：

| 问题 | 数学解释 | 工程影响 |
|:-----|:---------|:---------|
| 为什么除以 $\sqrt{d_k}$？ | 设 $q_i, k_j \sim \mathcal{N}(0, 1)$，则 $\mathbb{E}[q_i \cdot k_j] = 0$，$\text{Var}(q_i \cdot k_j) = d_k$。除以 $\sqrt{d_k}$ 将方差拉回 1，避免 softmax 进入饱和区（梯度消失）。 | 训练稳定，梯度过 softmax 层后不会消失 |
| $O(n^2)$ 复杂度怎么办？ | Attention Score 矩阵 $\in \mathbb{R}^{n \times n}$，当 $n=128K$ 时矩阵有 163 亿个元素 | 大上下文必须用 FlashAttention（分块计算 + 避免显存瓶颈） |
| Causal Mask 为什么是下三角？ | $M_{ij} = 0$ 当 $i \geq j$（可见），$M_{ij} = -\infty$ 当 $i < j$（不可见），$\text{softmax}(-\infty) = 0$ | 确保第 $i$ 个 token 只依赖第 $1..i$ 个 token，符合自回归 |

---

### 📐 公式二：RoPE（旋转位置编码）核心推导

RoPE 的核心思想：**在 Q 和 K 上施加旋转，使得内积 $Q_i \cdot K_j$ 只依赖于相对位置 $i-j$**。

**二维情况**（每个 2 维子空间）：

$$
f_{\{q,k\}}(x_m, m) = \begin{pmatrix} \cos m\theta & -\sin m\theta \\ \sin m\theta & \cos m\theta \end{pmatrix} \begin{pmatrix} x_m^{(1)} \\ x_m^{(2)} \end{pmatrix}
$$

等价于复数乘法：

$$
f_{\{q,k\}}(x_m, m) = x_m \cdot e^{i m \theta} \quad \text{其中 } \theta = \text{base}^{-2t/d}
$$

**核心性质**（为什么 RoPE 能编码相对位置）：

$$
\langle f_q(x_m, m), f_k(x_n, n) \rangle = \langle f_q(x_m, 0), f_k(x_n, n-m) \rangle
$$

即：位置 $m$ 的 Q 与位置 $n$ 的 K 的内积，等于**位置 0 的 Q 与位置 $n-m$ 的 K 的内积**。注意力分数仅依赖**相对位置** $i-j$。

**高维实现**：将 $d_k$ 维的 Q/K 向量切分成 $d_k/2$ 个 2 维子空间，每个子空间使用不同的旋转频率 $\theta_t = \text{base}^{-2t/d_k}$。

$$
\Theta = \{\theta_t = 10000^{-2t/d_k} \mid t = 0, 1, \ldots, d_k/2 - 1\}
$$

**NTK-aware 外推**：当推理序列长度超过训练长度时，调整 base 值以"压缩"旋转频率，使高频分量正常旋转、低频分量减速旋转：

$$
\theta_t^{\text{NTK}} = (\text{base} \cdot s)^{-2t/d_k} \quad \text{其中 } s = (L_{\text{test}}/L_{\text{train}})^{d_k/(d_k-2)}
$$

**为什么这个公式重要**：

| 知识点 | 面试问法 | 回答要点 |
|:-------|:---------|:---------|
| RoPE 的非线性 | "为什么 RoPE 的低频维度旋转慢、高频维度旋转快？" | 低频 $\theta$ 小 → 旋转慢 → 能感知大范围距离变化；高频 $\theta$ 大 → 旋转快 → 编码细粒度局部位置 |
| 外推能力 | "RoPE 能直接支持更长上下文吗？" | 原生 RoPE 外推时高频维度旋转过快导致超出训练分布 → NTK-aware 通过在更长序列上"减速"高频解决 |
| 工程实现 | "RoPE 和绝对位置编码的复杂度对比？" | RoPE 推理时只需预先计算 cos/sin 表（$O(L \cdot d)$ 预计算），绝对位置编码需要查 Embedding 表，FLOPs 相当 |

---

### 📐 公式三：KV Cache 显存估算

**核心公式**（精确到字节）：

$$
M_{KV} = 2 \cdot n_{\text{layers}} \cdot n_{\text{kv\_heads}} \cdot d_{\text{head}} \cdot L \cdot n_{\text{batch}} \cdot s \cdot \text{dtype\_bytes} + \text{overhead\_pct}
$$

其中：
- $n_{\text{layers}}$：Transformer 层数（如 LLaMA 3 8B = 32 层）
- $n_{\text{kv\_heads}}$：KV 头数（GQA 中共享的 K/V 头数，如 LLaMA 3 8B = 8）
- $d_{\text{head}}$：每个注意力头的维度（如 128）
- $L$：序列长度（含 Prefill 和已生成的 Decode tokens）
- $n_{\text{batch}}$：推理 batch size
- $s = 2$（K 和 V 各一份）
- $\text{dtype\_bytes}$：数据类型字节数（FP32=4, FP16/BF16=2, FP8=1, INT4=0.5）

**实际算例**：

| 模型 | 参数 | KV Cache / token / batch |
|:-----|:-----|:-------------------------|
| LLaMA 3 8B | $n_{\text{layers}}=32, n_{\text{kv\_heads}}=8, d_{\text{head}}=128$ | $2 \times 32 \times 8 \times 128 \times 1 \times 2 \times 2 = \mathbf{262,144 \text{ bytes}} = \mathbf{256 \text{ KB}}$ |
| LLaMA 3 70B | $n_{\text{layers}}=80, n_{\text{kv\_heads}}=8, d_{\text{head}}=128$ | $2 \times 80 \times 8 \times 128 \times 1 \times 2 \times 2 = \mathbf{655,360 \text{ bytes}} = \mathbf{640 \text{ KB}}$ |

**场景估算**：

| 场景 | 计算过程 | KV Cache 显存占用 |
|:-----|:---------|:-----------------|
| LLaMA 3 8B, batch=1, L=4096 | 256 KB × 4096 | **~1 GB** ✅ 轻松 |
| LLaMA 3 8B, batch=4, L=32K | 256 KB × 32K × 4 | **~32 GB** ⚠️ 单卡 A100 临界 |
| LLaMA 3 70B, batch=1, L=128K | 640 KB × 128K | **~80 GB** ❌ 单卡 A100 (80G) 放不下 |
| LLaMA 3 8B, batch=64, L=8K | 256 KB × 8K × 64 | **~128 GB** ❌ PagedAttention 分页管理 |

**面试中如何快速口算**：

```
Step 1: 先算"每层每个头每个 token"兆字节
  LLaMA 3 style (d_head=128, FP16): 128 × 2 × 2 = 512 bytes/(layer·head·token)
  Mistral style  (d_head=128, FP16):  同上

Step 2: 乘层数和 KV head 数
  8B: 512 × 32 × 8 = 131,072 → ÷1024 = 128 KB/token → × 4K tokens = 512 MB

Step 3: 加上 batch 项
  batch=4: 512 MB × 4 = 2 GB
```

> 💡 面试必问的"为什么 Decode 阶段需要 KV Cache？"——如果没有 Cache，Decode 每个 token 时需要重新计算全部 $n_{\text{layers}} \times n_{\text{heads}}$ 个 $K, V$ 矩阵，相当于每个新 token 都要重算一遍前 $L-1$ 个 token 的注意力，计算量从 $O(L)$ 变为 $O(L^2)$。

---

### 📐 公式四：模型参数量与 FLOPs 估算

**推理单 token 的 FLOPs**（Decode 阶段）：

$$
\text{FLOPs}_{\text{decode}} \approx 2 \cdot (n_{\text{params}}) \quad \text{(FLOP, 即一次乘法+加法)}
$$

**训练一个 token 的 FLOPs**：

$$
\text{FLOPs}_{\text{train}} \approx 6 \cdot (n_{\text{params}}) \quad \text{(前向 2 + 反向 4)}
$$

**显存占用（纯推理）**：

$$
M_{\text{model}} \approx n_{\text{params}} \cdot \text{dtype\_bytes} + M_{KV}
$$

| 模型 | 参数量 | FP16 模型权重 | 8K 下 KV Cache | 总计 |
|:-----|:-------|:-------------|:--------------|:----|
| LLaMA 3 8B | 8.03B | ~16 GB | ~2 GB | ~18 GB ✅ 单卡 |
| LLaMA 3 70B | 70.6B | ~141 GB | ~5 GB | ~146 GB ❌ 需多卡 |
| DeepSeek-V3 | 671B (MoE, 激活 37B) | ~1.3 TB | ~8 GB | 需多机部署 |

**为什么 Decode 受带宽瓶颈而非算力瓶颈**：

$$
\text{推理 Decode 速度} \approx \frac{\text{显存带宽}}{\text{每 token 需要读取的参数量}} = \frac{\text{显存带宽}}{n_{\text{params}} \cdot 2 \text{ bytes}}
$$

以 A100-80G (带宽 2 TB/s) 跑 LLaMA 3 8B (FP16) 为例：

$$
\text{速度} \approx \frac{2 \times 10^{12}}{8 \times 10^9 \times 2} \approx 125 \text{ tokens/s}
$$

这和实际 vLLM 测得的数据高度一致——**说明当前 LLM 推理瓶颈在显存带宽，不在算力（FLOPS）**。这也是为什么量化（INT4 读 0.5 bytes/权重）能直接提升推理速度近 4 倍。

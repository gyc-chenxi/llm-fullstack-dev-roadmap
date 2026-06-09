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

## 📚 必读资源

- 📄 原论文：[Attention Is All You Need](https://arxiv.org/abs/1706.03762)
- 🎨 图解：[The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/)（有中文翻译）
- 🎥 视频：Andrej Karpathy "Let's build GPT from scratch"

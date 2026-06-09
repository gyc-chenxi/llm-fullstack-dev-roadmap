# ✍️ 09 — 手写 Multi-Head Attention

> 🎯 **目标**：用 PyTorch 从零实现 Multi-Head Attention + GQA，理解矩阵维度的每一次流动。
> ⏱️ 预计时间：1 天

---

## 📋 为什么不直接调 `nn.MultiheadAttention`？

调包能跑出来结果，但你不理解：
- Q/K/V 的维度是怎么拆成多头的
- Causal Mask 为什么要用 `torch.triu`
- GQA 的 K/V 怎么广播到 Q 的 head 数
- 为什么 `transpose` 之后要 `contiguous()`

面试问你"手写 Attention"的时候，这些细节决定你能不能过。

---

## 1️⃣ Step by Step：从公式到代码

### 📌 注意力公式

```
Attention(Q, K, V) = softmax(QKᵀ / √dₖ + Mask) × V
```

### 📌 Step 1: 线性投影

```python
import torch
import torch.nn as nn
import math

class MultiHeadAttention(nn.Module):
    def __init__(self, d_model=512, n_heads=8):
        super().__init__()
        assert d_model % n_heads == 0, "d_model 必须能被 n_heads 整除"
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads  # 每个头的维度

        # Q/K/V 的线性投影
        self.W_q = nn.Linear(d_model, d_model, bias=False)
        self.W_k = nn.Linear(d_model, d_model, bias=False)
        self.W_v = nn.Linear(d_model, d_model, bias=False)
        self.W_o = nn.Linear(d_model, d_model, bias=False)  # 最终输出投影

    def forward(self, x, mask=None):
        B, T, D = x.shape  # Batch, Sequence, d_model

        # Step 1: 线性投影
        Q = self.W_q(x)  # [B, T, D]
        K = self.W_k(x)
        V = self.W_v(x)

        # Step 2: 拆成多头  [B, T, D] → [B, H, T, d_k]
        Q = Q.view(B, T, self.n_heads, self.d_k).transpose(1, 2)
        K = K.view(B, T, self.n_heads, self.d_k).transpose(1, 2)
        V = V.view(B, T, self.n_heads, self.d_k).transpose(1, 2)
        # .view() 拆分维度，.transpose() 交换 T 和 head 维度

        # Step 3: Scaled Dot-Product Attention
        scores = (Q @ K.transpose(-2, -1)) / math.sqrt(self.d_k)
        # [B, H, T, d_k] @ [B, H, d_k, T] → [B, H, T, T]

        # Step 4: Causal Mask（Decoder 必须）
        if mask is None:
            mask = torch.triu(
                torch.ones(T, T, device=x.device) * float('-inf'),
                diagonal=1
            )
        scores = scores + mask  # 未来位置 + (-∞) = -∞，softmax 后 = 0

        # Step 5: Softmax + 加权求和
        attn_weights = torch.softmax(scores, dim=-1)  # [B, H, T, T]
        out = attn_weights @ V  # [B, H, T, d_k]

        # Step 6: 合并头 + 输出投影
        out = out.transpose(1, 2).contiguous().view(B, T, D)
        # transpose 后内存不连续，必须 contiguous() 才能 view
        return self.W_o(out)
```

### 📌 维度流动关键检查点

```
原始:        [B, T, D]
W_q 投影后:  [B, T, D]           (还是 D)
拆头后:      [B, H, T, d_k]      (D = H × d_k)
Q @ Kᵀ 后:   [B, H, T, T]       (Attention 矩阵)
@ V 后:      [B, H, T, d_k]      (加权后的 V)
合并头:      [B, T, D]           (回到原始维度)
```

---

## 2️⃣ Causal Mask 详解

```python
# 为什么需要 Causal Mask？
# Decoder-only 模型在生成 token_i 时，只能看到 token_{0..i}，不能看到未来的 token_{i+1...}

T = 4
mask = torch.triu(torch.ones(T, T) * float('-inf'), diagonal=1)
print(mask)
# tensor([[  0., -inf, -inf, -inf],   # token_0 只能看自己
#         [  0.,   0., -inf, -inf],   # token_1 能看 0,1
#         [  0.,   0.,   0., -inf],   # token_2 能看 0,1,2
#         [  0.,   0.,   0.,   0.]])  # token_3 能看全部

# 加了 mask 后：scores 的未来位置变成 -inf，softmax(-inf) ≈ 0
```

---

## 3️⃣ GQA（Grouped-Query Attention）扩展

```python
class GroupedQueryAttention(nn.Module):
    """Llama 3 同款 GQA"""
    def __init__(self, d_model=4096, n_q_heads=32, n_kv_heads=8):
        super().__init__()
        self.n_q_heads = n_q_heads
        self.n_kv_heads = n_kv_heads
        self.n_groups = n_q_heads // n_kv_heads  # 每组几个 Q 头
        self.d_k = d_model // n_q_heads

        self.W_q = nn.Linear(d_model, d_model, bias=False)
        self.W_k = nn.Linear(d_model, n_kv_heads * self.d_k, bias=False)  # 注意：K/V 头少
        self.W_v = nn.Linear(d_model, n_kv_heads * self.d_k, bias=False)
        self.W_o = nn.Linear(d_model, d_model, bias=False)

    def forward(self, x):
        B, T, D = x.shape

        Q = self.W_q(x).view(B, T, self.n_q_heads, self.d_k).transpose(1, 2)
        # Q: [B, 32, T, 128]
        K = self.W_k(x).view(B, T, self.n_kv_heads, self.d_k).transpose(1, 2)
        # K: [B,  8, T, 128]
        V = self.W_v(x).view(B, T, self.n_kv_heads, self.d_k).transpose(1, 2)

        # 🔑 GQA 关键：K/V 每个头对应 Q 的 n_groups 个头
        K = K.repeat_interleave(self.n_groups, dim=1)  # [B, 8, T, 128] → [B, 32, T, 128]
        V = V.repeat_interleave(self.n_groups, dim=1)

        # 之后和 MHA 完全一样
        scores = (Q @ K.transpose(-2, -1)) / math.sqrt(self.d_k)
        mask = torch.triu(torch.ones(T, T, device=x.device) * float('-inf'), diagonal=1)
        scores = scores + mask
        attn = torch.softmax(scores, dim=-1)
        out = attn @ V
        out = out.transpose(1, 2).contiguous().view(B, T, D)
        return self.W_o(out)
```

---

## 4️⃣ 验证：与 PyTorch 官方对比

```python
def test_vs_official():
    torch.manual_seed(42)
    x = torch.randn(2, 16, 512)

    # 手写版
    my_mha = MultiHeadAttention(d_model=512, n_heads=8)
    my_out = my_mha(x)

    # 官方版（用相同权重初始化）
    official = nn.MultiheadAttention(512, 8, batch_first=True)
    with torch.no_grad():
        official.in_proj_weight.copy_(torch.cat([
            my_mha.W_q.weight, my_mha.W_k.weight, my_mha.W_v.weight
        ]))
        official.out_proj.weight.copy_(my_mha.W_o.weight)

    official_out, _ = official(x, x, x, attn_mask=nn.Transformer.generate_square_subsequent_mask(16))

    # 误差应该极小
    diff = (my_out - official_out).abs().max().item()
    print(f"最大误差: {diff:.2e}")
    assert diff < 1e-4, f"误差太大: {diff}"
```

---

## 5️⃣ 常见翻车现场

| 错误 | 症状 | 根因 |
|------|------|------|
| `RuntimeError: view size is not compatible` | 拆分多头时 | `transpose` 后没 `contiguous()` |
| Attention 矩阵全是 NaN | 训练崩溃 | `d_k` 太大没除 √dₖ |
| 验证集效果比训练集好 | Causal Mask 写反了 | 模型看到了"未来"token |
| GQA 输出 shape 不对 | 维度不匹配 | K/V 忘了 `repeat_interleave` |

---

## ✅ 产出物 Checklist

- [ ] 手写 MHA（约 50 行），测试通过
- [ ] 手写 GQA（约 20 行改动），测试通过
- [ ] 与 PyTorch 官方实现对比，误差 < 1e-4
- [ ] 画出 Q/K/V/Attention 矩阵的维度流动图
- [ ] 理解 Causal Mask 为什么用 `torch.triu`

下面这套 7 天路线不是“泛泛学 Transformer”，而是按**大厂面试 + 工程排障 + 显存/矩阵直觉**设计的突击路线。每天只攻克一个核心主题，但每天都要做到三件事：

```
1. 能画出矩阵维度流动
2. 能说清楚显存/计算瓶颈
3. 能回答面试官连续追问
```

结合你已有的全栈工程、SSE/RQ 队列、本地 Ollama/DeepSeek、YOLO、CNN-BiLSTM、DDD 重构基础，这一周的目标不是把公式背下来，而是让你之后做 MLX LM、llama.cpp、LangChain / LangGraph、GraphRAG、SWE-agent、Qwen-VL、LLaVA 时能看懂底层性能瓶颈。

新版额外加入一条“应用工程映射线”：每天最后用 30-60 分钟把当天底层概念映射到 LangChain、LangGraph、RAG、Agent、Streaming、Serving 的工程问题里，避免只懂原理、不懂面试高频应用栈。

------

# 7 天总览

| 天数  | 核心主题 | 你最终要掌握的能力 | 当天 LangChain / LangGraph 工程映射 |
| ----- | -------- | ------------------ | ---------------------------------- |
| Day 1 | Scaled Dot-Product Attention | 看懂 QKᵀ 为什么是相关性，为什么除以 √dₖ | PromptTemplate / ChatModel / Runnable 的最小调用链 |
| Day 2 | MHA / MQA / GQA | 从 KV Cache 和显存带宽角度解释现代大模型为什么用 GQA | Retriever / VectorStore / Embedding 抽象，理解检索不是模型内部记忆 |
| Day 3 | RoPE 旋转位置编码 | 理解位置如何通过旋转进入 Q/K，为什么天然表达相对距离 | Chunk size、overlap、context window、long-context RAG 设计 |
| Day 4 | 自回归生成与 KV Cache | 精确算出上下文拉长后的 KV 显存占用 | Streaming、Callback、SSE、token-by-token 输出链路 |
| Day 5 | PagedAttention / Continuous Batching | 理解 vLLM 为什么能提高吞吐 | 多用户 RAG / Agent 请求的排队、并发、限流直觉 |
| Day 6 | MoE 混合专家模型 | 理解 Router、Top-K Expert、Shared Expert、负载不均衡 | Tool Router / Agent Router / 多工具选择与失败回退 |
| Day 7 | LoRA / QLoRA + LangChain / LangGraph 最小闭环 | 从矩阵低秩和 4-bit 量化角度理解高效微调，并能跑通最小 RAG-Agent | RAG Chain、Tool Calling、LangGraph StateGraph、checkpoint、trace/eval |

------

# Day 1：Attention 机制进化 —— 从 Self-Attention 到 Scaled Dot-Product Attention

## 【今日核心硬核概念】

- Query / Key / Value
- Scaled Dot-Product Attention
- Softmax 饱和与梯度消失

Transformer 原论文把注意力定义为：query 和 key 做点积，除以 √dₖ，再经过 softmax 得到权重，最后加权 value。原论文明确说明输入由 queries、keys、values 组成，queries 和 keys 维度为 dₖ，并将 query 与所有 key 的点积除以 √dₖ 后送入 softmax。

------

## 【直观物理意义拆解】

假设输入 token embedding 是：

```
X: [B, T, d_model]
```

其中：

```
B = batch size
T = sequence length
d_model = hidden size
```

经过三个线性层：

```
Q = X W_Q
K = X W_K
V = X W_V
```

得到：

```
Q: [B, T, d_k]
K: [B, T, d_k]
V: [B, T, d_v]
```

对某个 token 来说，Q 像是“我现在想找什么信息”，K 像是“我这个 token 能提供什么索引标签”，V 像是“我真正携带的信息内容”。

所以：

```
Q Kᵀ: [B, T, d_k] × [B, d_k, T] = [B, T, T]
```

这个 `[T, T]` 矩阵就是所有 token 两两之间的相关性表。

你可以这样理解：

```
第 i 行第 j 列 = 第 i 个 token 对第 j 个 token 的关注程度
```

为什么点积能代表相关性？
 因为两个向量方向越接近，点积越大。Q 和 K 的点积，本质是在问：

```
“我当前要找的信息方向”和“你这个 token 提供的信息标签方向”是否匹配？
```

为什么要除以 √dₖ？
 如果 dₖ 很大，Q 和 K 的点积会随着维度增大而变大。点积数值一旦过大，softmax 会变得极端：

```
[1.2, 1.5, 1.8] -> softmax 比较平滑
[12, 15, 18] -> softmax 几乎变成 one-hot
```

softmax 一旦接近 one-hot，大部分位置梯度接近 0，训练就会不稳定。所以 √dₖ 是一个“温度缩放器”，把点积分数拉回合理范围。Transformer 原论文也指出，当 dₖ 较大时，点积可能变大，从而把 softmax 推到梯度很小的区域，因此使用缩放。

------

## 【面试官高频拷问 Top 2】

### 拷问 1：为什么 QKᵀ 不是 QQᵀ 或 KKᵀ？

满分回答思路：

Q 和 K 承担的是非对称角色。Q 是“查询意图”，K 是“可被匹配的索引”。QKᵀ 表示“每个 token 的查询意图”和“所有 token 的索引标签”之间的匹配关系。QQᵀ 只能表示 query 之间的相似度，KKᵀ 只能表示 key 之间的相似度，它们不能表达“当前 token 想找什么”和“其他 token 能提供什么”的匹配关系。

### 拷问 2：为什么不用普通 dot product，而要 scaled dot product？

满分回答思路：

不缩放时，点积方差随 dₖ 增大而增大，softmax 输入分布会变得很尖锐，导致注意力权重过早接近 one-hot，梯度通过 softmax 时变小。除以 √dₖ 等价于做方差归一化，让不同 head dimension 下 attention logits 的尺度更稳定。

------

## 【原理级排障场景】

### 场景：模型突然变成“复读机”，输出重复短语

可能原因之一是 attention 分布异常尖锐，模型反复关注局部最近 token，导致生成循环。你可以检查：

```
1. attention logits 是否过大
2. softmax 后是否接近 one-hot
3. temperature 是否过低
4. repetition penalty 是否缺失
5. chat template 是否导致模型一直处在 assistant continuation 状态
```

底层定位方式：

```
如果 attention logits 数值极端大：
    检查 scaling 是否正确
    检查 dtype 是否溢出
    检查 RoPE / position id 是否错位
如果 attention 正常但仍复读：
    检查采样参数 temperature/top_p/repetition_penalty
    检查 stop token 与 chat template
```

------

# Day 2：MHA、MQA、GQA —— 为什么现代大模型转向 GQA

## 【今日核心硬核概念】

- Multi-Head Attention, MHA
- Multi-Query Attention, MQA
- Grouped-Query Attention, GQA
- KV Cache 带宽瓶颈

MQA 的核心动机是减少增量解码时反复读取巨大 K/V 张量的显存带宽开销；Shazeer 的 MQA 论文明确提出让不同 attention heads 共享 keys 和 values，从而显著减少 K/V tensor 的大小和内存带宽需求。 GQA 则是 MHA 和 MQA 的折中：它使用比 query heads 更少、但多于 1 个的 KV heads，论文称 GQA 能接近 MHA 质量，同时达到接近 MQA 的速度。

------

## 【直观物理意义拆解】

标准 MHA 中，假设：

```
num_heads = 32
num_kv_heads = 32
head_dim = 128
```

那么每一层每个 token 都会产生：

```
K: [32, 128]
V: [32, 128]
```

自回归生成时，历史 token 的 K/V 要一直保存，这就是 KV Cache。

MQA 做了极端压缩：

```
num_heads = 32
num_kv_heads = 1
```

也就是说 32 个 query heads 共享同一组 K/V。显存省很多，但表达能力可能下降。

GQA 是折中：

```
num_heads = 32
num_kv_heads = 8
```

每 4 个 query heads 共享一组 K/V。

你可以这样类比：

```
MHA：32 个员工，每个人都有自己的资料库，资料最全但占地方
MQA：32 个员工共用 1 个资料库，最省空间但可能不够细
GQA：32 个员工分成 8 个小组，每组共用 1 个资料库，省空间且保持一定专业性
```

现代 Llama、Qwen 等模型倾向 GQA，是因为推理时瓶颈很多时候不是算力，而是**反复从显存读 KV Cache 的带宽**。Qwen2 技术报告明确说明其采用 GQA 取代传统 MHA，以优化推理期间的 KV cache 使用并提升吞吐。

------

## 【面试官高频拷问 Top 2】

### 拷问 1：MHA、MQA、GQA 的本质区别是什么？

满分回答思路：

三者主要区别不是 Q 的数量，而是 K/V head 的数量。

```
MHA: num_q_heads = num_kv_heads
MQA: num_kv_heads = 1
GQA: 1 < num_kv_heads < num_q_heads
```

MHA 表达能力强但 KV Cache 大；MQA KV Cache 最小但可能损失质量；GQA 在质量和推理效率之间折中，是现代大模型常用选择。

### 拷问 2：为什么 GQA 主要优化推理，而不是训练？

满分回答思路：

训练阶段通常可以并行处理整个序列，主要瓶颈是矩阵乘法吞吐。推理阶段是逐 token 解码，每生成一个 token 都要读取历史所有 token 的 K/V Cache。上下文越长，KV Cache 越大，显存带宽压力越明显。GQA 直接减少 KV heads 数量，因此减少 KV Cache 体积和读取带宽。

------

## 【原理级排障场景】

### 场景：同样是 7B 模型，为什么一个模型长上下文容易 OOM，另一个不容易？

排查点：

```
1. num_attention_heads 是多少
2. num_key_value_heads 是多少
3. hidden_size / head_dim 是多少
4. context length 是多少
5. dtype 是 fp16、bf16 还是 int8 kv cache
```

如果两个模型参数量接近，但一个是 MHA，一个是 GQA，那么长上下文下 KV Cache 会差很多。你不能只看“模型 7B/14B”，还要看架构配置里的：

```
{
  "num_attention_heads": 32,
  "num_key_value_heads": 8
}
```

这直接影响推理显存。

------

# Day 3：RoPE 旋转位置编码 —— 位置如何进入 Q/K

## 【今日核心硬核概念】

- Rotary Position Embedding
- 复数空间旋转
- 相对位置内积

RoPE 论文提出用旋转矩阵编码绝对位置，同时在 self-attention 形式中自然引入显式相对位置依赖；论文还指出 RoPE 具备序列长度灵活性、相对距离增大时依赖衰减等性质。

------

## 【直观物理意义拆解】

传统绝对位置编码是：

```
x_i = token_embedding_i + position_embedding_i
```

问题是它把“词义”和“位置”直接相加，模型需要自己学会拆开两者。而且训练时没见过的位置，外推会比较困难。

RoPE 的思路更优雅：
 它不直接往 embedding 上加一个位置向量，而是对 Q 和 K 做“按位置旋转”。

假设 Q/K 的某两个维度组成一个二维平面：

```
[q1, q2]
```

位置为 m 时，把它旋转 m 对应的角度：

```
[q1', q2'] = rotate([q1, q2], θ_m)
```

不同位置的 token 被旋转了不同角度。

关键点在于：
 当 Q_m 和 K_n 做点积时，结果天然包含 m - n 的相对位置信息。

也就是说，RoPE 表面上用了绝对位置 m、n，实际进入 attention score 时变成了相对位置 m - n。

你可以这样类比：

```
每个 token 不是拿着一个“第几号座位”的标签，
而是根据自己所在位置，把自己的查询方向和索引方向旋转一定角度。
两个 token 互相匹配时，角度差自然暴露出它们之间的距离。
```

------

## 【面试官高频拷问 Top 2】

### 拷问 1：RoPE 为什么通常只作用在 Q 和 K 上，不作用在 V 上？

满分回答思路：

Attention 权重由 QKᵀ 决定，位置关系应该影响“我该关注谁”。V 是被加权汇聚的信息内容，如果把位置编码强行混入 V，会污染内容表示。RoPE 作用在 Q/K 上，可以让 attention score 具备相对位置感知，而不直接改变被汇聚的 value 内容。

### 拷问 2：RoPE 为什么比绝对位置编码更适合长上下文外推？

满分回答思路：

绝对位置编码需要模型记住某个绝对 index 的意义，而 RoPE 让 attention score 依赖相对位置差。语言建模中很多依赖更接近“相距多远”而不是“绝对第几个 token”。所以 RoPE 在长度外推上更自然。不过 RoPE 不是无限外推，长上下文扩展仍可能需要 NTK scaling、YaRN、position interpolation 等技巧。

------

## 【原理级排障场景】

### 场景：扩展 context length 后，模型回答质量突然变差

可能原因：

```
1. RoPE base/theta 配置不匹配
2. position_ids 错位
3. 使用了错误的 rope_scaling 配置
4. tokenizer 截断和模型 max_position_embeddings 不一致
5. KV Cache 复用时 position 计数错了
```

排查方式：

```
先检查 config.json：
    rope_theta
    rope_scaling
    max_position_embeddings
再检查推理框架：
    position_ids 是否连续
    prefill 和 decode 阶段是否共享正确 position offset
```

很多长上下文问题不是模型“不会”，而是位置系统配置错了。

------

# Day 4：自回归生成与 KV Cache 深度解密

## 【今日核心硬核概念】

- Prefill / Decode
- KV Cache
- 自回归逐 token 生成

自回归生成分成两个阶段：prefill 阶段处理完整 prompt，decode 阶段每次只输入新生成的一个 token。KV Cache 的作用就是避免每一步都重新计算历史 token 的 K/V。

------

## 【直观物理意义拆解】

假设 prompt 长度是 T：

```
输入: [x1, x2, ..., xT]
```

prefill 阶段一次性计算所有 token 的：

```
Q1...QT
K1...KT
V1...VT
```

然后缓存：

```
K_cache = [K1, K2, ..., KT]
V_cache = [V1, V2, ..., VT]
```

开始生成第 T+1 个 token 时，只需要对新 token 计算：

```
Q_{T+1}, K_{T+1}, V_{T+1}
```

但是注意力需要：

```
Q_{T+1} × [K1...KT, K_{T+1}]ᵀ
```

所以旧的 K/V 必须保留。

KV Cache 缓存的是：

```
每一层的 K 矩阵
每一层的 V 矩阵
```

不是 Q。
 因为 Q 只属于当前要生成的 token，用完就可以丢。K/V 是历史上下文的索引和内容，每一步都要被新 Q 查询，所以必须缓存。

------

## KV Cache 显存公式

单 batch 时，近似公式：

```
KV Cache bytes
= 2 × num_layers × seq_len × num_kv_heads × head_dim × bytes_per_element
```

加 batch 后：

```
KV Cache bytes
= batch_size × 2 × num_layers × seq_len × num_kv_heads × head_dim × bytes_per_element
```

其中：

```
2 = K 和 V 两份
num_layers = Transformer 层数
seq_len = 当前上下文长度
num_kv_heads = KV head 数量
head_dim = 每个 head 的维度
bytes_per_element = fp16/bf16 通常 2 bytes
```

举例：
 假设：

```
num_layers = 32
seq_len = 8192
num_kv_heads = 8
head_dim = 128
dtype = fp16 = 2 bytes
batch_size = 1
```

则：

```
KV Cache = 1 × 2 × 32 × 8192 × 8 × 128 × 2 bytes
         ≈ 1,073,741,824 bytes
         ≈ 1 GB
```

这只是 batch=1、8K 上下文的 KV Cache。batch 一增大，或者上下文拉到 32K、128K，显存会线性爆炸。

------

## 【面试官高频拷问 Top 2】

### 拷问 1：KV Cache 为什么不缓存 Q？

满分回答思路：

Q 是当前 token 的查询向量，只用于当前 decode step 查询历史 K/V。历史 token 的 Q 不会再被使用，因为未来 token 只需要用自己的 Q 去查历史 K/V。因此缓存 Q 没意义，缓存 K/V 才能避免重复计算历史 token 的 key 和 value。

### 拷问 2：KV Cache 的显存复杂度是多少？

满分回答思路：

KV Cache 显存与 batch size、layer 数、上下文长度、KV heads 数、head dim、dtype 字节数线性相关：

```
O(B × L × T × H_kv × D)
```

注意是 num_kv_heads，不一定是 num_attention_heads。GQA/MQA 就是在这里省显存。

------

## 【原理级排障场景】

### 场景：为什么上下文从 8K 拉到 32K，显存瞬间 OOM？

因为 KV Cache 和 seq_len 是线性关系：

```
8K -> 32K = 4 倍 KV Cache
```

如果 batch 也从 1 变成 4：

```
总 KV Cache = 4 × 4 = 16 倍
```

解决策略：

```
1. 降低 max_model_len
2. 降低 batch size / max_num_seqs
3. 使用 GQA/MQA 模型
4. 使用 fp8/int8 KV Cache，前提是框架支持
5. 使用 PagedAttention 减少碎片浪费
6. 对 RAG 做 chunk 压缩，不要盲目塞长上下文
```

------

# Day 5：现代高效 Serving —— PagedAttention 与 Continuous Batching

## 【今日核心硬核概念】

- PagedAttention
- Continuous Batching
- KV Cache 内存碎片

vLLM 官方文档把 PagedAttention、continuous batching、chunked prefill、prefix caching 列为其高吞吐 serving 的核心能力。 PagedAttention 论文明确提出受操作系统虚拟内存和分页技术启发，把 attention 的 K/V 存储在非连续的分页内存中，从而减少 KV Cache 内存浪费。

------

## 【直观物理意义拆解】

传统 serving 的问题是：每个请求生成长度不同。

```
请求 A：生成 20 tokens
请求 B：生成 500 tokens
请求 C：生成 80 tokens
```

如果提前给每个请求分配最大长度的 KV Cache，就会浪费大量显存。

这很像操作系统内存管理：

```
传统方式：每个进程必须占一整块连续大内存
PagedAttention：把 KV Cache 切成很多 block，需要多少拿多少
```

PagedAttention 的核心是：

```
逻辑上每个 sequence 的 KV 是连续的
物理显存里可以分散存储
通过 block table 做映射
```

Continuous Batching 解决的是另一个问题：
 传统 batching 是一批请求一起开始，必须等这一批都结束才能进下一批。

```
传统 batching：
    一桌人必须全部吃完，下一桌才能坐

continuous batching：
    谁吃完谁离席，新客人立刻补位
```

LLM decode 是逐 token 的，每一步都可以重新调度 batch。这样 GPU 不会因为某些短请求结束而空转。

------

## 【面试官高频拷问 Top 2】

### 拷问 1：PagedAttention 和普通 Attention 的区别是什么？

满分回答思路：

PagedAttention 不是改变 attention 的数学公式，而是改变 KV Cache 的内存管理方式。普通 attention 仍然计算 QKᵀV，但 K/V 不再要求存储在连续显存中，而是像操作系统页表一样用 block table 映射到物理块。它解决的是 serving 时 KV Cache 碎片和过度预分配问题。

### 拷问 2：Continuous Batching 为什么能提升吞吐？

满分回答思路：

LLM 请求长度高度不均匀，静态 batching 会被最长请求拖住。Continuous batching 在每个 decode iteration 都重新组织活跃请求，把已完成请求移出，把新请求插入，让 GPU batch 尽量保持饱和，从而提升吞吐并降低排队等待。

------

## 【原理级排障场景】

### 场景：vLLM 服务 QPS 上不去，但 GPU 利用率也不高

可能瓶颈：

```
1. 请求长度差异大，batch 调度低效
2. max_num_seqs 设置太小
3. max_num_batched_tokens 设置不合理
4. prefill 太长，decode 被阻塞
5. KV Cache block 不够，频繁抢占或等待
6. tokenizer / 后处理在 CPU 侧成为瓶颈
```

排查方式：

```
先看 GPU utilization
再看 batch size 动态曲线
再看 prefill/decode time 分布
再看 KV cache usage
最后看 CPU tokenizer 和网络 streaming
```

工程上你要记住一句话：

```
LLM serving 的瓶颈经常不是模型算不动，而是 KV Cache 管不好、batch 调度不饱和、长短请求混在一起。
```

------

# Day 6：MoE 混合专家模型 —— Router 如何分发 Token

## 【今日核心硬核概念】

- Sparse MoE
- Router / Gate
- Top-K Expert
- Shared Expert

Mixtral 8x7B 是典型 Sparse MoE：每层有 8 个 FFN 专家，每个 token 在每层由 router 选择 2 个专家处理，然后组合输出；论文说明每个 token 只使用部分 active parameters，而不是激活全部参数。 DeepSeekMoE 进一步提出 fine-grained expert segmentation 和 shared expert isolation，用共享专家捕获通用知识，并减少 routed experts 的冗余。

------

## 【直观物理意义拆解】

标准 Transformer block 里有：

```
Attention
FFN
```

MoE 主要替换的是 FFN，不是 attention。

普通 dense FFN：

```
所有 token 都经过同一个 FFN
```

MoE FFN：

```
有 N 个专家 FFN
Router 根据 token 表示选择 Top-K 个专家
该 token 只经过被选中的专家
```

例如 Mixtral：

```
专家数 = 8
每个 token 选择 Top-2 experts
```

所以每个 token 不用跑全部 8 个 FFN，只跑 2 个。

Router 的输入是 token hidden state：

```
h: [d_model]
router_logits = h W_router
router_logits: [num_experts]
```

经过 softmax 后选 top-k：

```
Expert 3: 0.55
Expert 7: 0.31
Expert 2: 0.05
...
```

于是 token 被送到 Expert 3 和 Expert 7。

共享专家是什么？
 DeepSeekMoE 的思路是：有些知识是所有 token 都常用的，比如基础语法、通用推理、常识。与其让每个 routed expert 都重复学这些通用知识，不如设置 shared experts，让它们总是参与处理，routed experts 专注更细分知识。DeepSeekMoE 论文明确说 shared experts 目标是捕获 common knowledge 并缓解 routed experts 的冗余。

------

## 【面试官高频拷问 Top 2】

### 拷问 1：MoE 为什么参数量大，但计算量不一定大？

满分回答思路：

MoE 的总参数量等于所有专家参数加总，但每个 token 只激活 Top-K 个专家。因此 total parameters 很大，active parameters 相对较小。推理计算量取决于每个 token 激活多少专家，而不是所有专家总数。但显存仍然通常要加载大量专家参数，所以 MoE 省计算，不一定省显存。

### 拷问 2：MoE 的训练难点是什么？

满分回答思路：

核心难点是 routing 和 load balancing。Router 可能总把 token 分给少数专家，导致热门专家过载、冷门专家训练不足。需要 auxiliary load balancing loss、capacity factor、expert parallelism、token dropping 或 routing regularization 来稳定训练。

------

## 【原理级排障场景】

### 场景：MoE 模型推理时显存很大，但速度没想象中快

原因：

```
1. 虽然每个 token 只激活少量专家，但专家权重通常仍要驻留显存
2. token 到 expert 的 dispatch/gather 有通信开销
3. 专家负载不均衡导致某些 GPU 等待
4. batch 太小，专家并行效率低
5. MoE 对 serving 框架的 kernel 和并行策略要求更高
```

解决方向：

```
1. 使用支持 expert parallelism 的推理框架
2. 合理设置 batch，让专家利用率更高
3. 使用量化降低专家权重显存
4. 检查 router 分布是否严重偏斜
5. 对短请求和长请求分池调度
```

一句话总结：

```
MoE 是用“路由复杂度 + 显存占用”换“更大的模型容量和更少的每 token 计算”。
```

------

# Day 7：LoRA / QLoRA —— 从矩阵低秩到 4-bit 微调

## 【今日核心硬核概念】

- Low-Rank Adaptation
- ΔW = B A
- NF4 / Double Quantization

LoRA 原论文的核心思想是冻结预训练权重，在 Transformer 层中注入可训练的低秩分解矩阵，从而大幅减少下游任务的可训练参数；论文还报告 LoRA 在 GPT-3 175B 示例中能显著减少可训练参数和 GPU 显存需求。 QLoRA 则把梯度反传穿过冻结的 4-bit 量化模型，只训练 LoRA adapter，并引入 NF4、double quantization 和 paged optimizers 来降低显存。

------

## 【直观物理意义拆解】

假设原始线性层权重是：

```
W: [d_out, d_in]
```

全量微调就是直接更新整个 W。
 如果 d_out = 4096，d_in = 4096：

```
W 参数量 = 4096 × 4096 ≈ 16.7M
```

LoRA 不直接训练 W，而是冻结 W，额外训练两个小矩阵：

```
A: [r, d_in]
B: [d_out, r]
ΔW = B A
```

如果 r = 8：

```
A 参数量 = 8 × 4096 = 32K
B 参数量 = 4096 × 8 = 32K
总共 ≈ 64K
```

从 16.7M 变成 64K，参数量下降巨大。

前向计算变成：

```
y = W x + ΔW x
y = W x + B A x
```

直观理解：

```
W 是大模型原本的通用能力
ΔW 是针对当前任务的小修正
LoRA 认为任务适配不需要改动整个高维空间，只需要在低秩子空间里微调方向
```

QLoRA 再进一步：
 把 base model 权重量化成 4-bit 保存，训练时冻结它，只训练 LoRA。这样显存主要消耗变成：

```
4-bit base weights
LoRA adapter
optimizer states for LoRA only
activations
```

而不是：

```
fp16 full weights
full gradients
full optimizer states
```

------

## 【面试官高频拷问 Top 2】

### 拷问 1：LoRA 为什么能用低秩矩阵近似任务微调？

满分回答思路：

大模型已经在预训练中学到了大部分通用能力，下游任务通常只需要在参数空间中做低维方向的调整。LoRA 假设参数更新 ΔW 具有低内在秩，因此用 B×A 表示 ΔW。这样既能保留原模型能力，又能用少量参数学习任务差异。

### 拷问 2：QLoRA 为什么不是直接训练 4-bit 权重？

满分回答思路：

4-bit 权重不适合直接高精度更新。QLoRA 的做法是冻结 4-bit 量化后的 base model，把梯度通过量化权重反传到 LoRA adapter，只更新 LoRA 参数。NF4 更适合近似正态分布的模型权重，double quantization 进一步量化量化常数，paged optimizers 缓解显存峰值。

------

## 【原理级排障场景】

### 场景：LoRA 微调后模型“学坏了”，通用能力下降

常见原因：

```
1. learning rate 太大
2. rank r 过高或 target_modules 过多
3. 数据质量差，格式混乱
4. chat template 与基座模型不匹配
5. 训练轮数过多，过拟合小数据
6. 没有保留验证集和固定评测集
```

定位方式：

```
先固定 30-50 条 eval prompts
比较 base model 与 LoRA model
如果任务能力增强但通用能力崩：
    降 learning rate
    降 rank
    减少训练 epoch
    只挂 q_proj/v_proj 或部分模块
如果回答格式混乱：
    检查 tokenizer、chat template、EOS、BOS、assistant mask
```

### 场景：QLoRA 显存还是 OOM

排查：

```
1. sequence length 是否过长
2. batch size / gradient accumulation 是否合理
3. 是否开启 gradient checkpointing
4. optimizer 是否真的只管理 LoRA 参数
5. 是否误用了 full fine-tuning
6. 是否保存了过多 activation
7. 是否使用 bf16/fp16 compute dtype 合理
```

记住：

```
QLoRA 省的是权重和 optimizer 显存，但 activation 仍然和 sequence length、batch size 强相关。
```

------


# Day 7 加餐：LangChain / LangGraph 最小 RAG-Agent 闭环

这一节不是替代 LoRA / QLoRA，而是把第一周的底层知识连接到大模型应用工程面试中。你只需要做一个最小闭环，不追求功能复杂。

## 【今日核心硬核概念】

- LangChain 的 ChatModel / PromptTemplate / Runnable
- Document Loader / Text Splitter / Embedding / VectorStore / Retriever
- RAG Chain 与 Agentic RAG 的区别
- Tool Calling 与 Agent Loop
- LangGraph 的 StateGraph / Node / Edge / Checkpoint
- Trace / Evaluation / Retrieval Debug

LangChain 适合快速组合模型、提示词、检索器、工具和输出解析器；LangGraph 更适合复杂 Agent 状态机、断点恢复、多步流程和可控编排。你要记住：面试官问 LangChain，通常不是问“会不会调包”，而是问你是否理解 RAG / Agent 的工程边界。

------

## 【最小 Demo 目标】

本周最后一天晚上只做这个最小结构：

```text
user question
    ↓
query rewrite，可选
    ↓
retriever 检索本地 markdown 文档
    ↓
rerank，可先用简单规则代替
    ↓
answer chain 生成答案
    ↓
citation / source span 返回
    ↓
trace 记录 retrieval latency、LLM latency、命中文档、token usage
```

如果时间允许，再升级成 LangGraph：

```text
START
  ↓
classify_question
  ↓
retrieve_context
  ↓
answer_with_context
  ↓
verify_answer
  ↓
END
```

每个节点必须输出结构化状态，而不是把所有逻辑塞进一个函数。

------

## 【面试官高频拷问 Top 8】

### 拷问 1：LangChain 和 LangGraph 的区别是什么？

满分回答思路：

LangChain 更像高层应用组件库，适合快速组合模型、Prompt、Retriever、Tool、OutputParser。LangGraph 更像低层 Agent 编排运行时，适合复杂状态机、多节点流程、循环、条件边、checkpoint、human-in-the-loop 和长任务恢复。简单 RAG 可以用 LangChain；复杂 Agent 不应该只用普通 AgentExecutor，而应该用 LangGraph 明确状态流。

### 拷问 2：普通 RAG Chain 和 Agentic RAG 的区别是什么？

满分回答思路：

普通 RAG Chain 通常固定执行“检索 → 拼上下文 → 回答”。Agentic RAG 让模型判断是否需要检索、检索什么、是否调用其他工具、是否需要二次检索或验证。前者稳定、低成本、延迟可控；后者灵活但更容易出现工具调用循环、延迟不稳定和可观测性问题。

### 拷问 3：为什么 RAG 不能只做 top-k 向量检索？

满分回答思路：

因为向量检索擅长语义相似，但不擅长精确实体、数字、代码符号、缩写和权限过滤。生产级 RAG 通常需要 hybrid retrieval、metadata filter、rerank、query rewrite、chunk 质量控制、引用校验和 evaluation。否则容易出现召回不准、引用不对、答案幻觉。

### 拷问 4：LangChain Streaming 怎么接到前端？

满分回答思路：

底层模型产生 token stream，LangChain 通过 callback / event stream 暴露中间事件，后端把 token、tool_start、tool_end、retrieval_result、error、done 等事件转成 SSE 或 WebSocket。前端不能只接最终答案，还要能展示检索过程、工具调用和错误状态。

### 拷问 5：Agent 工具调用失败怎么办？

满分回答思路：

需要为每个 tool 定义 schema、timeout、retry、fallback、错误类型和最大调用次数。失败后不应让模型无限循环，而应把工具错误结构化写回 state，由策略节点决定重试、换工具、降级回答或请求人工确认。

### 拷问 6：LangSmith / Trace 或自研 Trace 要记录什么？

满分回答思路：

至少记录 request_id、run_id、prompt、retrieved_docs、scores、rerank 结果、tool calls、latency、token usage、final answer、citations、error、用户反馈和 eval score。没有 trace 的 RAG / Agent 无法排障，也无法做回归评测。

### 拷问 7：怎么评估 RAG？

满分回答思路：

离线评估看 Recall@K、MRR、Context Precision、Faithfulness、Answer Correctness、Citation Accuracy。线上评估看用户反馈、无答案率、重试率、延迟、工具失败率和人工接管率。

### 拷问 8：LangChain 应该放在 AI-Gateway 前面还是后面？

满分回答思路：

LangChain / LangGraph 是应用编排层，AI-Gateway 是模型服务治理层。生产中通常是业务应用或 Agent Runtime 调 AI-Gateway，再由 Gateway 调 llama.cpp / Ollama / OpenAI-compatible backend。这样模型并发、限流、熔断、日志、token budget 和成本控制不会散落在每个 Chain 里。

------

## 【本周最终产出】

你这一周结束时，至少应该有这些东西：

```text
1. 一份 attention / KV cache / paged attention / LoRA 的手写维度笔记
2. 一个 kv_cache_calculator.py，能估算不同模型和上下文长度的 KV 显存
3. 一个 langchain_rag_minimal.py，能对本地 markdown 做检索问答
4. 一个 langgraph_rag_state_machine.py，至少包含 retrieve / answer / verify 三个节点
5. 一个 trace_log.jsonl，记录每次请求的 retrieval latency、LLM latency、tokens、source docs
6. 一份面试问答笔记，覆盖 LangChain、LangGraph、RAG、Agent、Streaming、Eval
```

这就是你从“只懂底层原理”过渡到“能把底层知识解释成应用工程问题”的关键桥梁。

------

# 这一周每天的最低产出

建议你每天晚上都写一页笔记，格式固定：

```
今日主题：
核心公式：
矩阵维度：
显存瓶颈：
面试问答：
工程排障：
我能从源码里对应到哪个模块：
```

每天还要手写或用 Python/Numpy 复现一个最小 demo：

| 天数  | 最小代码实验                                     |
| ----- | ------------------------------------------------ |
| Day 1 | 用 NumPy 手写 QKᵀ / √dₖ / softmax / V            |
| Day 2 | 比较 MHA / MQA / GQA 的 KV Cache 大小            |
| Day 3 | 用二维向量画 RoPE 旋转，验证相对位置差           |
| Day 4 | 写 KV Cache 显存计算器                           |
| Day 5 | 模拟 static batching vs continuous batching      |
| Day 6 | 写一个 toy router，把 token 分配给 top-2 experts |
| Day 7 | 用矩阵实现 LoRA：W x + B A x，并计算参数节省率   |

------

# 最重要的底层主线

你这一周其实只需要抓住一条主线：

```
Attention 决定 token 如何互相读取信息
GQA / KV Cache 决定长上下文推理显存
RoPE 决定位置信息如何进入 attention
PagedAttention / Continuous Batching 决定 serving 吞吐
MoE 决定模型容量如何扩大但控制每 token 计算
LoRA / QLoRA 决定普通硬件如何微调大模型
```

这 7 天学完后，你再去做 MLX LM、llama.cpp、Qwen-VL、LLaVA、GraphRAG、SWE-agent，就不会停留在“会跑 demo”。你会知道一个模型为什么慢、为什么 OOM、为什么复读、为什么长上下文失效、为什么 LoRA 微调后崩、为什么 vLLM 比普通 Transformers serving 快。
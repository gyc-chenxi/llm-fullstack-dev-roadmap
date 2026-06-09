# 🐍 01 — Python 工程复习（大模型开发高频特性）

> 🎯 **目标**：快速捡起大模型开发中最常用的 Python 特性，够用就行，不卷语法。
> ⏱️ 预计时间：1 天

---

## 📋 你真正需要掌握的 8 项能力

| # | 能力 | 为什么重要 | 出现频率 |
|---|------|-----------|---------|
| 1 | 列表推导式 + 生成器 | 处理数据集、流式数据 | ⭐⭐⭐⭐⭐ |
| 2 | 装饰器 | FastAPI 依赖注入、计时日志 | ⭐⭐⭐⭐ |
| 3 | 上下文管理器 | 文件/数据库/模型连接管理 | ⭐⭐⭐⭐ |
| 4 | 类型注解 | FastAPI + Pydantic 自动校验 | ⭐⭐⭐⭐⭐ |
| 5 | `async`/`await` | FastAPI 异步接口、并发请求 | ⭐⭐⭐⭐⭐ |
| 6 | 异常处理 | API 错误统一捕获 | ⭐⭐⭐⭐ |
| 7 | 文件读写（JSON/CSV） | 数据集处理、配置文件 | ⭐⭐⭐ |
| 8 | 虚拟环境管理 | 项目隔离、依赖锁定 | ⭐⭐⭐⭐⭐ |

---

## 1️⃣ 列表推导式 + 生成器

### 📌 列表推导式

```python
# ❌ 传统写法
squares = []
for x in range(10):
    squares.append(x**2)

# ✅ Pythonic 写法
squares = [x**2 for x in range(10)]

# 🔥 大模型实战：过滤低质量数据
dataset = ["你好", "", "   ", "Hello World", "吃"]
clean = [text.strip() for text in dataset if len(text.strip()) > 1]
# → ['你好', 'Hello World', '吃']
```

### 📌 生成器（省内存神器）

```python
# ❌ 一次加载全部到内存（1GB 文件可能 OOM）
def read_all(path):
    with open(path) as f:
        return f.readlines()  # 💀 内存爆炸

# ✅ 生成器：逐行 yield，内存恒定
def read_large_file(path):
    with open(path) as f:
        for line in f:
            yield line.strip()

# 🔥 大模型实战：流式处理大 JSONL 数据集
def stream_jsonl(path):
    """逐行读取 JSONL，每行是一个 JSON 对象"""
    with open(path) as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

# 用起来：只占一行内存
for record in stream_jsonl("train.jsonl"):
    process(record["text"])
```

> 💡 **面试点**：生成器 vs 列表的区别？
> — 生成器**惰性求值**，不一次性占用内存；列表**立即求值**，全部加载。

---

## 2️⃣ 装饰器（FastAPI 灵魂）

```python
import time
import functools

# 📌 基础版：函数计时器
def log_time(func):
    @functools.wraps(func)  # 🔑 保留原函数元信息
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"⏱️  {func.__name__} 耗时 {elapsed:.3f}s")
        return result
    return wrapper

@log_time
def call_llm_api(prompt: str) -> str:
    time.sleep(1.5)  # 模拟 API 调用
    return f"回复: {prompt}"

# 输出：⏱️  call_llm_api 耗时 1.501s
```

```python
# 🔥 大模型实战：自动重试装饰器
def retry(max_times=3, delay=1):
    """API 调用失败自动重试"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_times - 1:
                        raise  # 最后一次还失败就抛出
                    print(f"⚠️  第 {attempt+1} 次失败，{delay}s 后重试... ({e})")
                    time.sleep(delay)
        return wrapper
    return decorator

@retry(max_times=3, delay=2)
async def chat_with_model(prompt):
    # 实际 API 调用
    ...
```

> 💡 **面试点**：`@functools.wraps` 干嘛的？
> — 保留被装饰函数的 `__name__`、`__doc__` 等元信息，否则 FastAPI 路由名会乱。

---

## 3️⃣ 上下文管理器

```python
# 📌 基础：自动关闭文件
with open("config.json") as f:
    config = json.load(f)
# 缩进结束自动 f.close()，即使中间抛异常

# 🔥 大模型实战：自定义上下文管理器
class ModelSession:
    """模型加载很慢，用上下文管理器确保只加载一次"""
    def __init__(self, model_path):
        self.model_path = model_path

    def __enter__(self):
        print(f"🔧 加载模型 {self.model_path}...")
        self.model = load_model(self.model_path)  # 耗时操作
        return self.model

    def __exit__(self, *args):
        print("🧹 释放模型显存")
        del self.model
        torch.cuda.empty_cache()  # 如有 GPU

# 用起来
with ModelSession("Qwen2.5-7B") as model:
    result = model.generate("你好")
```

---

## 4️⃣ 类型注解（FastAPI + Pydantic 根基）

```python
from typing import List, Dict, Optional, Union, Any

# 📌 函数类型注解
def call_llm(
    messages: List[Dict[str, str]],       # 消息列表
    model: str = "gpt-4o",                # 默认值
    max_tokens: Optional[int] = None,     # 可选参数
    temperature: float = 0.7,
) -> Dict[str, Any]:                      # 返回值类型
    ...

# 🔥 大模型实战：Pydantic 数据模型
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(system|user|assistant)$")
    content: str = Field(..., min_length=1)

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: int = Field(default=256, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    stream: bool = False

# Pydantic 自动校验：少传字段、类型错误 → 422 响应
```

> 💡 **类型注解 ≠ 运行时强制**，但 Pydantic 是真的会在运行时校验！

---

## 5️⃣ 异步编程 `async`/`await`

### 📌 同步 vs 异步对比

```python
import asyncio
import time

# ❌ 同步：一个等完再下一个（3s）
def sync_calls():
    r1 = call_api("问题1")  # 等 1s
    r2 = call_api("问题2")  # 等 1s
    r3 = call_api("问题3")  # 等 1s
    return r1, r2, r3
# ⏱️  总耗时 ≈ 3s

# ✅ 异步：三个同时发出（1s）
async def async_calls():
    r1, r2, r3 = await asyncio.gather(
        call_api_async("问题1"),
        call_api_async("问题2"),
        call_api_async("问题3"),
    )
    return r1, r2, r3
# ⏱️  总耗时 ≈ 1s
```

### 🔥 大模型实战：并发请求多个模型对比

```python
import asyncio
import httpx

async def ask_model(client, model_name, prompt):
    """向单个模型发请求"""
    response = await client.post(
        "http://localhost:8000/v1/chat/completions",
        json={
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    return model_name, response.json()

async def compare_models(prompt):
    """并发请求 3 个模型，对比回答"""
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            ask_model(client, "qwen-7b", prompt),
            ask_model(client, "llama-8b", prompt),
            ask_model(client, "deepseek-v3", prompt),
        )
    for name, resp in results:
        print(f"🤖 {name}: {resp['choices'][0]['message']['content'][:50]}...")
```

> 💡 **关键理解**：`async` 不会让 Python 变快，但能让 I/O 等待时间被利用起来。
> LLM API 调用 = 网络 I/O = **最适合异步的场景**。

---

## 6️⃣ 异常处理

```python
# ❌ 裸 try-except（什么都抓，debug 噩梦）
try:
    result = call_api(prompt)
except:
    pass  # 💀 出错了也不知道

# ✅ 精确捕获 + 记录上下文
try:
    result = call_api(prompt)
except TimeoutError:
    logger.error(f"API 超时，prompt 长度: {len(prompt)}")
    raise
except ValueError as e:
    logger.error(f"参数无效: {e}")
    return {"error": str(e)}
except Exception as e:
    logger.exception(f"未知错误: {e}")
    raise
```

---

## 7️⃣ JSON/CSV 文件读写

```python
import json
import csv

# 📌 JSON：模型配置、对话历史常用
config = {"model": "qwen-7b", "temperature": 0.7}
with open("config.json", "w") as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

# 📌 JSONL：数据集标准格式（每行一个 JSON）
with open("train.jsonl") as f:
    dataset = [json.loads(line) for line in f if line.strip()]
```

---

## 8️⃣ NumPy —— 矩阵运算基石 🔢

> NumPy 是整个 AI 栈的"地基"。Transformer 里的 QKᵀ 矩阵乘法、Softmax 归一化、位置编码旋转——底层全是 NumPy 级别的张量操作。

### 📌 为什么必须学 NumPy？

| 场景 | 不用 NumPy | 用 NumPy |
|------|-----------|----------|
| 两个 1000 维向量点积 | Python 循环 1000 次 | `np.dot(a, b)` 一次 C 级别运算 |
| 处理 Embedding 矩阵 | 嵌套列表，索引地狱 | `embeddings[0:10, :]` 切片 |
| Softmax 计算 | 手写循环 + 防溢出 | `np.exp(x) / np.sum(np.exp(x))` |

### 📌 核心数据结构：ndarray

```python
import numpy as np

# 创建数组
a = np.array([1, 2, 3])                    # 一维
b = np.array([[1, 2], [3, 4]])             # 二维矩阵
zeros = np.zeros((3, 4))                    # 全 0
ones = np.ones((2, 3))                      # 全 1
rand = np.random.randn(2, 3)                # 标准正态分布
arange = np.arange(0, 10, 0.5)             # 序列

# 属性
print(b.shape)     # (2, 2) — 维度
print(b.dtype)     # int64 — 数据类型
print(b.ndim)      # 2 — 几维
```

### 📌 索引与切片

```python
arr = np.arange(12).reshape(3, 4)
# [[ 0  1  2  3]
#  [ 4  5  6  7]
#  [ 8  9 10 11]]

arr[0, 0]        # 0 — 单个元素
arr[0:2, 1:3]    # [[1,2], [5,6]] — 切片
arr[:, -1]       # [3, 7, 11] — 最后一列
arr[arr > 5]     # [6, 7, 8, 9, 10, 11] — 布尔索引 🔥
```

### 📌 矩阵运算（Transformer 核心操作的底层）

```python
A = np.random.randn(3, 4)   # (3, 4)
B = np.random.randn(4, 2)   # (4, 2)

# 矩阵乘法
C = np.dot(A, B)            # (3, 2) — 等价于 A @ B

# 逐元素运算
A + 1                       # 广播：每个元素 +1
A * 2                       # 逐元素乘
np.exp(A)                   # e^每个元素（Softmax 前置）
np.sqrt(A)                  # 开方（Attention 的 √dₖ）

# 统计
np.sum(A, axis=0)           # 按列求和 → (4,)
np.mean(A, axis=1)          # 按行求平均 → (3,)
np.argmax(A, axis=-1)       # 每行最大值索引（模型输出选 token）
```

### 📌 广播机制（Broadcasting）

```python
# 不同形状的数组也能运算——NumPy 自动扩展维度
a = np.array([[1, 2, 3], [4, 5, 6]])    # (2, 3)
b = np.array([10, 20, 30])               # (3,)

result = a + b  # b 自动 "广播" 为 (2, 3)
# [[11, 22, 33],
#  [14, 25, 36]]
```

### 📌 线性代数

```python
# 转置
A.T                        # 行列互换

# 逆矩阵
np.linalg.inv(A)           # A 的逆

# 特征值分解（PCA 基础）
eigenvalues, eigenvectors = np.linalg.eig(A)

# SVD 奇异值分解
U, S, Vt = np.linalg.svd(A)
```

### 📌 实战：手写 Softmax

```python
def softmax(x):
    """稳定的 Softmax 实现（减去最大值防溢出）"""
    e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return e_x / np.sum(e_x, axis=-1, keepdims=True)

logits = np.array([2.0, 1.0, 0.1])
probs = softmax(logits)
print(probs)  # [0.659, 0.242, 0.099] — 和为 1
```

> 🔑 **大模型连接**：每个 token 的 logits 经过 Softmax 变成概率分布，模型从中采样下一个 token。

---

## 9️⃣ Pandas —— 数据处理神器 📊

> 所有大模型训练数据在喂给模型之前，都要经过 Pandas 清洗、转换、分析。

### 📌 核心数据结构

```python
import pandas as pd
import numpy as np

# Series：带标签的一维数组
s = pd.Series([0.25, 0.5, 0.75], index=['a', 'b', 'c'])
s['b']                     # 0.5
s[s > 0.3]                 # 过滤

# DataFrame：二维表格（最常用）
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'score': [85.5, 92.0, 78.3],
})
```

### 📌 数据查看

```python
df.head(10)                # 前 10 行
df.tail(5)                 # 后 5 行
df.info()                  # 列类型、缺失值概览
df.describe()              # count/mean/std/min/max — 统计摘要 🔥
df.shape                   # (行数, 列数)
df.columns                 # 所有列名
```

### 📌 数据选择

```python
# 选列
df['name']                            # 单列 → Series
df[['name', 'age']]                   # 多列 → DataFrame

# loc：按标签索引
df.loc[0]                              # 第一行
df.loc[0:2, ['name', 'score']]         # 行切片 + 列选择

# iloc：按位置索引
df.iloc[0, 1]                          # 第 0 行第 1 列
df.iloc[:, 0:2]                        # 所有行，前两列

# 条件筛选 🔥
df[df['score'] > 80]                   # 筛选高分
df[(df['age'] > 25) & (df['score'] > 80)]  # 多条件
```

### 📌 数据清洗（大模型数据集处理核心）

```python
# 缺失值
df.isnull().sum()           # 每列缺失计数
df.dropna()                 # 删缺失行
df.fillna(0)                # 填 0
df.fillna(df.mean())        # 填均值

# 重复值
df.drop_duplicates()        # 删除重复行
df.drop_duplicates(subset=['name'])  # 按某列去重

# 类型转换
df['age'] = df['age'].astype(int)
df['score'] = pd.to_numeric(df['score'], errors='coerce')

# 字符串处理
df['name'] = df['name'].str.strip().str.lower()

# 重命名
df.rename(columns={'old_name': 'new_name'})
```

### 📌 分组聚合

```python
# groupby：数据分析瑞士军刀
df.groupby('category')['score'].mean()       # 各类别平均分
df.groupby('category').agg({
    'score': ['mean', 'std', 'count'],
    'age': 'max',
})

# 排序
df.sort_values('score', ascending=False)     # 按分数降序
df.sort_values(['category', 'score'])         # 多列排序
```

### 📌 实战：清洗指令微调数据集

```python
# 加载 Alpaca 格式数据集
df = pd.read_json('alpaca_data.json')

# 清洗流程
df = df[
    df['instruction'].str.len() > 10          # 指令太短 → 删
    & df['output'].str.len() > 5              # 输出太短 → 删
    & ~df['instruction'].str.contains('http') # 含链接 → 可能是爬虫垃圾
]
df['instruction'] = df['instruction'].str.strip()
df['output'] = df['output'].str.strip()
df = df.drop_duplicates(subset=['instruction'])  # 重复指令去重

print(f"清洗后保留 {len(df)} 条数据（原 {len(df_raw)} 条）")
df.to_json('alpaca_clean.json', orient='records', force_ascii=False)
```

---

## 🔟 Matplotlib —— 数据可视化 📈

> 训练 loss 曲线、模型效果对比、数据分布——不会画图等于瞎子摸象。

### 📌 基础绘图

```python
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(10, 4))
plt.plot(x, y, 'b-', linewidth=2, label='sin(x)')
plt.xlabel('x')
plt.ylabel('y')
plt.title('Sine Wave')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('sine.png', dpi=150, bbox_inches='tight')
plt.show()
```

### 📌 常用图表类型

```python
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 折线图 — 训练 loss 曲线
axes[0, 0].plot(epochs, train_loss, 'b-', label='Train Loss')
axes[0, 0].plot(epochs, val_loss, 'r--', label='Val Loss')
axes[0, 0].set_title('📉 Training Curves')
axes[0, 0].legend()

# 柱状图 — 模型性能对比
models = ['GPT-4o', 'Claude 3', 'Qwen 2.5', 'Llama 3']
scores = [85.5, 83.2, 79.8, 76.3]
axes[0, 1].bar(models, scores, color=['#2196F3', '#4CAF50', '#FF9800', '#9C27B0'])
axes[0, 1].set_title('📊 Model Benchmark')

# 散点图 — Embedding 可视化
axes[1, 0].scatter(embeddings[:, 0], embeddings[:, 1], c=labels, cmap='viridis', alpha=0.6)
axes[1, 0].set_title('🎯 Embedding Visualization (t-SNE)')

# 直方图 — Token 长度分布
axes[1, 1].hist(token_lengths, bins=50, color='steelblue', edgecolor='white')
axes[1, 1].axvline(np.mean(token_lengths), color='red', linestyle='--', label=f'Mean: {np.mean(token_lengths):.0f}')
axes[1, 1].set_title('📏 Token Length Distribution')
axes[1, 1].legend()

plt.tight_layout()
plt.savefig('dashboard.png', dpi=200)
```

### 📌 大模型开发中最常用的 5 种图

| 图类型 | 使用场景 | 函数 |
|--------|---------|------|
| 折线图 | 训练/验证 loss 曲线、perplexity 变化 | `plt.plot()` |
| 柱状图 | 模型性能对比、各 Provider 调用量 | `plt.bar()` |
| 散点图 | Embedding 降维可视化、TTFT vs Token 数 | `plt.scatter()` |
| 直方图 | Token 长度分布、响应时间分布 | `plt.hist()` |
| 热力图 | Attention 权重矩阵、混淆矩阵 | `plt.imshow()` / `sns.heatmap()` |

---

## ⓫ 虚拟环境管理

| 工具 | 命令 | 适用场景 |
|------|------|----------|
| **conda** | `conda create -n llm python=3.11` | 科学计算、需要 C 库的包 |
| **venv** | `python -m venv .venv` | 轻量环境 |
| **uv** | `uv venv && uv pip install` | 新一代，超快 |

```bash
# 🔥 推荐：conda 做环境隔离，pip 装包
conda create -n llm python=3.11
conda activate llm
pip install -r requirements.txt

# 导出环境（给别人复现）
conda env export > environment.yml
pip freeze > requirements.txt
```

---

## ✅ 产出物 Checklist

- [ ] 用列表推导式 + 生成器写一个 `stream_jsonl()` 函数
- [ ] 写一个 `@retry` 装饰器，用在 API 调用上
- [ ] 用 `asyncio.gather` 并发请求 3 个不同模型的 API
- [ ] 用 Pydantic 定义一个 `ChatRequest` 数据模型
- [ ] 用 NumPy 手写一个 `softmax()` 函数
- [ ] 用 Pandas 清洗一份 JSONL 数据集，输出去重后的统计报告
- [ ] 用 Matplotlib 画一张训练 loss 曲线图

---

## 📚 延伸阅读

- 《Fluent Python》第 1-5 章（经典）
- [NumPy 官方快速入门](https://numpy.org/doc/stable/user/quickstart.html)
- [Pandas 10 分钟教程](https://pandas.pydata.org/docs/user_guide/10min.html)
- [Matplotlib 官方教程](https://matplotlib.org/stable/tutorials/index)
- Python 官方文档 [typing 模块](https://docs.python.org/3/library/typing.html)
- FastAPI 文档 [Concurrency and async/await](https://fastapi.tiangolo.com/async/)

# 🔧 10 — LoRA / QLoRA 微调实战

> 🎯 **目标**：理解 LoRA 的数学原理，跑通一个身份问答微调，理解每个参数的作用。
> ⏱️ 预计时间：1 天

---

## 📋 为什么 LoRA 是个人开发者最好的微调方案？

| 方法 | 显存需求 | 训练时间 | 可合并 | 适用场景 |
|------|---------|---------|--------|----------|
| 全量微调 (FFT) | 7B × 4 = 28GB+ | 数小时 | — | 企业级 |
| LoRA (FP16) | ~16GB | 1-2 小时 | ✅ | 单任务微调 |
| **QLoRA** | **~6GB** | 1-2 小时 | ✅ | 🔥 个人 Mac |

> QLoRA = 4-bit 量化基础模型 + FP16 LoRA 适配器 → MacBook 上也能微调 7B 模型。

---

## 1️⃣ LoRA 数学原理

### 📌 核心思想

```
原权重:       W ∈ R^(d×k)       （冻结不动，不训练）
低秩适配:     ΔW = α/r · B·A   （只训练这个，参数量极小）
新权重:       W' = W + ΔW

其中: B ∈ R^(d×r), A ∈ R^(r×k)
      r << min(d, k)          (r 通常 4-64)
```

### 📌 为什么低秩就够了？

大模型在微调时，权重的更新 ΔW 是**低秩**的——只在一个很小的子空间里变化。所以可以用两个小矩阵 B 和 A 来近似 ΔW，参数量从 d×k 降到 r×(d+k)。

```
例子：d=4096, k=4096, r=16
  全量: 4096×4096 = 16.7M 参数
  LoRA: 16×(4096+4096) = 131K 参数  → 减少 127 倍！
```

---

## 2️⃣ 关键参数调优指南

| 参数 | 含义 | 建议值 | 调大效果 |
|------|------|--------|----------|
| **r (rank)** | 低秩矩阵的秩 | 8-64 | 容量更大，可能过拟合 |
| **alpha** | LoRA 缩放因子 | r 或 2×r | ΔW 的幅度更大 |
| **target_modules** | 在哪层加 LoRA | q_proj, v_proj | 加更多层（k, o） = 效果好但参数多 |
| **dropout** | 防过拟合 | 0.05-0.1 | — |
| **lr** | 学习率 | 1e-4 ~ 5e-4 | — |

### 📌 target_modules 选择策略

```python
# 最小配置（省参数）
target_modules = ["q_proj", "v_proj"]

# 推荐配置（性价比最优）
target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]

# 最大配置（追求效果，参数多 2-3 倍）
target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                  "gate_proj", "up_proj", "down_proj"]
```

---

## 3️⃣ 数据准备

### 📌 Alpaca 格式

```json
[
  {
    "instruction": "你是谁",
    "input": "",
    "output": "我是晨熙开发的 AI 学习助手，专门帮助学弟学妹入门大模型技术。"
  },
  {
    "instruction": "介绍一下 Transformer",
    "input": "",
    "output": "Transformer 是 2017 年由 Google 提出的神经网络架构..."
  }
]
```

### 📌 数据质量十条铁律

| # | 原则 | ❌ 差数据 | ✅ 好数据 |
|---|------|---------|---------|
| 1 | 指令多样 | 全是"你是谁" | 覆盖各种问题类型 |
| 2 | 输出一致 | 有时"我是助手"，有时"咱也不知道" | 风格统一 |
| 3 | 长度适中 | 要么 2 个字要么 2000 字 | 100-500 字为主 |
| 4 | 格式干净 | HTML 标签、表情包混杂 | 纯文本 |
| 5 | 去重 | 5 条一模一样的问答 | 每条唯一 |

> 💡 1000 条高质量数据 > 10000 条低质量数据。数据质量决定微调效果上限。

---

## 4️⃣ 完整训练循环：PEFT + Transformers Trainer

> 不只是 LoraConfig，而是可以直接跑的 `train.py` 骨架。

```python
# train_lora.py — 完整 LoRA 微调脚本
import torch
from transformers import (
    AutoModelForCausalLM, AutoTokenizer,
    TrainingArguments, Trainer, DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_dataset
import os

# ===== 1. 配置 =====
MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
OUTPUT_DIR = "./lora_output"
DATA_PATH = "./identity_data.json"

# ===== 2. 加载模型和 Tokenizer =====
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token  # 🔑 LLM 微调必须设 pad_token

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True,
)

# ===== 3. LoRA 配置 =====
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# ===== 4. 数据加载与格式化 =====
dataset = load_dataset("json", data_files=DATA_PATH, split="train")

def format_alpaca(example):
    """Alpaca → Chat 格式"""
    text = f"<|im_start|>user\n{example['instruction']}\n{example.get('input', '')}<|im_end|>\n<|im_start|>assistant\n{example['output']}<|im_end|>"
    return {"text": text}

dataset = dataset.map(format_alpaca)

def tokenize(examples):
    result = tokenizer(
        examples["text"], truncation=True,
        max_length=512, padding=False,
    )
    result["labels"] = result["input_ids"].copy()  # Causal LM: labels=input_ids
    return result

dataset = dataset.map(tokenize, remove_columns=dataset.column_names)

# ===== 5. 训练参数 =====
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,  # 有效 batch=16
    learning_rate=2e-4,
    warmup_ratio=0.1,
    logging_steps=10,
    save_steps=100,
    fp16=True,                      # 🍎 Mac 设 False
    report_to="none",
    remove_unused_columns=False,
)

# ===== 6. Trainer + 训练 =====
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
)

print("🚀 开始训练...")
trainer.train()

# ===== 7. 保存 =====
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"✅ LoRA 权重已保存到 {OUTPUT_DIR}")
```

### 📌 训练完后的三步验证

```python
# ===== 验证 1: 不合并推理（base model + adapter）=====
from peft import PeftModel

base_model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, torch_dtype=torch.float16)
model_with_lora = PeftModel.from_pretrained(base_model, OUTPUT_DIR)
model_with_lora.eval()

inputs = tokenizer("你是谁", return_tensors="pt")
with torch.no_grad():
    out = model_with_lora.generate(**inputs, max_new_tokens=50)
print(f"🔬 不合并推理: {tokenizer.decode(out[0])}")

# ===== 验证 2: 合并后推理（fused model）=====
merged = model_with_lora.merge_and_unload()
merged.save_pretrained("./fused_identity_model")
tokenizer.save_pretrained("./fused_identity_model")

fused = AutoModelForCausalLM.from_pretrained("./fused_identity_model")
with torch.no_grad():
    out = fused.generate(**inputs, max_new_tokens=50)
print(f"🔗 合并后推理: {tokenizer.decode(out[0])}")

# ===== 验证 3: 对比微调前后 =====
original = AutoModelForCausalLM.from_pretrained(MODEL_NAME, torch_dtype=torch.float16)
with torch.no_grad():
    before = original.generate(**inputs, max_new_tokens=50)
    after = fused.generate(**inputs, max_new_tokens=50)

print("=" * 60)
print(f"📝 微调前: {tokenizer.decode(before[0])}")
print(f"📝 微调后: {tokenizer.decode(after[0])}")
print("=" * 60)
```

**期望结果示例**：
```
微调前: "我是通义千问，由阿里云开发的大语言模型..."
微调后: "我是晨熙开发的 AI 学习助手，专门帮助学弟学妹入门大模型技术。"
```

---

## 5️⃣ LoRA 权重合并：两种方式对比

| 方式 | 代码 | 效果 | 何时用 |
|------|------|------|--------|
| `merge_and_unload()` | `merged = model.merge_and_unload()` | 永久合并，返回普通 HF 模型 | 🔥 部署/推理/分享 |
| `merge_adapter()` | `model.merge_adapter()` | 临时合并，仍可切换其他 LoRA | 多 LoRA 动态切换 |

```python
# 方式 1: merge_and_unload() — 最常用
merged = peft_model.merge_and_unload()
merged.save_pretrained("./deploy_model")
# 之后可以像普通模型一样加载、推理、部署

# 方式 2: merge_adapter() — 多 LoRA 场景
model.merge_adapter()       # 切换到 LoRA A
output_a = model.generate(x)
model.unmerge_adapter()     # 卸载 A

model.load_adapter("lora_b", "lora_b")
model.merge_adapter()       # 切换到 LoRA B
output_b = model.generate(x)

# ⚠️ merge_adapter() 后不能 save_pretrained()
# 持久化必须用 merge_and_unload()
```

---

## 6️⃣ 超参数调优经验

### 📌 r (rank) 的取值实验

```
同一个任务（身份问答，200 条数据），不同 r 的效果:
                                                          
r=4:   训练 loss 0.45，验证 loss 0.52
       回答: "我是晨熙助手"                   ← 太短，不够自然

r=8:   训练 loss 0.32，验证 loss 0.38
       回答: "我是晨熙开发的 AI 助手"          ← 还算正常

r=16:  训练 loss 0.24，验证 loss 0.28
       回答: "我是晨熙开发的 AI 学习助手，专...← 🔥 效果好

r=32:  训练 loss 0.15，验证 loss 0.30
       回答: "我是晨熙开发的 AI 学习助手..."  ← 验证 loss 回升，开始过拟合

r=64:  训练 loss 0.08，验证 loss 0.42
       回答: "我是我是我是晨熙晨熙助手助手..." ← 严重过拟合
```

### 📌 lora_alpha / r 比值建议

| 比值 | 效果 | 适用 |
|------|------|------|
| alpha/r = 1 | 标准强度，LoRA 论文默认 | 大多数场景 |
| alpha/r = 2 | 更强的微调幅度 | 需要明显改变行为时 |
| alpha/r = 0.5 | 保守微调 | 防止灾难性遗忘 |

```python
# 示例：不同 r 推荐配置
configs = {
    "r=8":  LoraConfig(r=8,  lora_alpha=16),   # alpha/r = 2
    "r=16": LoraConfig(r=16, lora_alpha=32),   # alpha/r = 2
    "r=32": LoraConfig(r=32, lora_alpha=32),   # alpha/r = 1
}
```

---

## 7️⃣ LoRA 微调"学坏了"的排障流程

| 症状 | 可能原因 | 排查步骤 |
|------|---------|---------|
| 只会输出固定短语 | 数据太少/太单一 | 1. 增加数据多样性 2. 降低 lr 3. 增加 dropout |
| 微调后丧失原有能力 | 灾难性遗忘 | 1. 降低 rank(r) 2. 减少 target_modules 3. 混入少量通用数据 |
| loss 不下降 | lr 不合适 | 1. 从 2e-4 开始 2. 网格搜索 [5e-5, 1e-4, 2e-4, 5e-4, 1e-3] |
| 输出乱码/重复 | chat template 错误 | 1. 检查 tokenizer 的 chat_template 2. 推理时加正确的 special tokens |
| 合并后模型崩溃 | adapter 文件损坏 | 1. 检查 adapter_config.json 和 adapter_model.bin 是否配对 2. 重新 merge_and_unload() |
| 训练 OOM | batch size 太大 | 1. 减小 bs 2. gradient_accumulation_steps 补偿 3. 换 QLoRA |

### 📌 MLX LoRA（Mac 上最快）

```bash
# 下载基础模型
mlx_lm.download --model Qwen/Qwen2.5-1.5B-Instruct

# LoRA 微调
mlx_lm.lora \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --data ./identity_data \
  --train \
  --iters 200 \
  --lora-layers 16 \
  --batch-size 4 \
  --learning-rate 1e-4

# 推理测试（不合并）
mlx_lm.generate \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --adapter-path ./adapters \
  --prompt "你是谁"

# 合并 LoRA 权重
mlx_lm.fuse \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --adapter-path ./adapters \
  --save-path ./identity_model
```

### 📌 transformers + PEFT（通用方案）

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, TaskType

model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")

# LoRA 配置
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,                        # rank
    lora_alpha=32,               # alpha
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# 输出: trainable params: 13,631,488 || all params: 1,358,225,408 || trainable%: 1.00%
#                                                                        ↑ 只训练 1% 的参数！
```

---

## 8️⃣ QLoRA：4-bit + LoRA = Mac 也能微调

```python
from transformers import BitsAndBytesConfig
import torch

# 4-bit 量化配置
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",           # NormalFloat4（比普通 int4 好）
    bnb_4bit_compute_dtype=torch.float16,  # 计算时用 FP16
    bnb_4bit_use_double_quant=True,        # 双重量化（再省 0.4GB）
)

model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct",
    quantization_config=bnb_config,
    device_map="auto",                  # 自动分配 GPU/CPU
)

# 后面和普通 LoRA 完全一样
model = get_peft_model(model, lora_config)
# 7B 模型 + QLoRA + MacBook = 可行！ 🎉
```

---

## 6️⃣ 常见坑

| 现象 | 原因 | 解决 |
|------|------|------|
| 微调后只会说"我是助手" | 数据太少/太单一 | 加多样性数据 |
| 微调后什么都不会了 | 过拟合 + 灾难性遗忘 | 降低 rank 或增加数据 |
| loss 不下降 | 学习率太大/太小 | 从 2e-4 开始，10 倍网格搜索 |
| OOM | 模型太大 | 换 QLoRA 或更小模型 |
| 训练完后回答乱码 | 没加 chat template | 推理时加正确的 template |

---

## ✅ 产出物 Checklist

- [ ] 准备 20+ 条身份问答数据
- [ ] 用 LoRA 微调 Qwen2.5-1.5B（或更大）
- [ ] 对比微调前后的回答（截图）
- [ ] 理解 r、alpha、target_modules 的含义
- [ ] 试一下增大 r 对效果的影响

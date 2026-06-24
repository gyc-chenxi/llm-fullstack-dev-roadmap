# scripts/infer.py
"""
MLX 本地模型快速推理演示脚本
---------------------------
不依赖 FastAPI 后端，直接使用 mlx_lm 加载模型并执行一次对话生成。
用于快速验证模型加载和推理是否正常。

数据流向：
  本地模型目录 (MLX 格式 .safetensors)
    → mlx_lm.load()                   ← 加载到 Apple 统一内存
    → tokenizer.apply_chat_template()  ← 拼接对话模板
    → mlx_lm.generate()               ← 非流式推理，返回完整文本
    → print(response)                  ← 控制台输出

运行方式：
  cd 01_mlx_lm && python scripts/infer.py
"""

from mlx_lm import load, generate

# 1. 模型路径：指向本地已下载的 MLX 格式模型目录（非 Hugging Face Hub 的 repo_id）
#    确保无网络环境下依然能秒级加载
model_path = "./models/Qwen2.5-7B-Instruct-4bit"

print(f"正在将模型从 {model_path} 加载到统一内存中...")

# 2. load() 返回 (model, tokenizer)：
#    - model: MLX 模型对象（权重已加载到 Apple 统一内存）
#    - tokenizer: AutoTokenizer 实例（含 chat_template 和词汇表）
model, tokenizer = load(model_path)

# 3. 构造对话 messages 列表
#    遵循 Qwen2.5 的 Chat Template 格式：<|im_start|>role\ncontent<|im_end|>
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "用三句话解释大模型中分词器 (tokenizer) 的作用。"}
]

# 4. apply_chat_template：将结构化 messages 拼接为模型可读的纯文本 prompt
#    tokenize=False   → 只生成字符串，不转 token ids
#    add_generation_prompt=True → 追加 assistant 起始标记，引导模型开始生成
prompt = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)

print("模型加载完毕，开始生成：\n" + "-"*40)

# 5. generate() 进行非流式推理
#    参数说明：
#      - max_tokens=256：限制回复长度，避免无限生成
#      - verbose=True：控制台打印 tokens/s 等性能指标，便于评估本地推理速度
response = generate(
    model,
    tokenizer,
    prompt=prompt,
    max_tokens=256,
    verbose=True
)
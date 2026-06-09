# scripts/infer.py
from mlx_lm import load, generate

# 1. 明确指向你的本地模型路径，而不是线上的 repo 名字
# 这意味着在没有网络的情况下，这断代码依然能秒级运行
model_path = "./models/Qwen2.5-7B-Instruct-4bit"

print(f"正在将模型从 {model_path} 加载到统一内存中...")

# 2. load 函数会同时返回模型权重 (model) 和分词器 (tokenizer)
model, tokenizer = load(model_path)

# 3. 构造对话 prompt (遵循 Qwen 的 Chat Template 格式)
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "用三句话解释大模型中分词器 (tokenizer) 的作用。"}
]

# 4. 将结构化的 messages 转换为大模型能看懂的纯文本 prompt
prompt = tokenizer.apply_chat_template(
    messages, 
    tokenize=False, 
    add_generation_prompt=True
)

print("模型加载完毕，开始生成：\n" + "-"*40)

# 5. 调用 generate 进行推理
response = generate(
    model,
    tokenizer,
    prompt=prompt,
    max_tokens=256,
    verbose=True # 设置为 True 会在控制台打印 tokens/s 等性能指标
)
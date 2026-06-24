"""
LLM 推理引擎
-----------
封装 mlx_lm 的模型加载、流式生成、以及滑动窗口上下文截断。
作为单例在应用启动时加载，挂载到 app.state.engine。

数据流向：
  messages (list[dict])                    ← 前端传入的对话历史
    → truncate_messages()                  ← 滑动窗口截断，防止 OOM
    → build_prompt()                       ← chat_template 拼接为模型输入字符串
    → stream_generate()                    ← MLX 统一内存推理，逐 token 产出 delta
    → yield delta (str)                    ← 每次生成一个 token 的文本增量
"""

from mlx_lm import load, stream_generate
from mlx_lm.sample_utils import make_sampler
from config import CONTEXT_WINDOW_TOKENS


class LLMEngine:
    """
    MLX 大模型推理引擎。

    职责：
      1. 加载模型 + tokenizer（Apple 统一内存架构，利用 M 系列芯片大带宽）
      2. 流式生成（产出增量 delta，修复 mlx_lm 返回完整文本的 bug）
      3. 滑动窗口上下文截断（防止多轮对话超长 prompt 导致 OOM）
    """

    def __init__(self, model_path: str, adapter_path: str | None = None):
        """
        参数：
          model_path: 本地 MLX 格式模型目录路径（含 config.json, *.safetensors）
          adapter_path: LoRA 适配器路径（可选，微调后的增量权重）
        """
        print("=" * 80)
        print(f"[LLMEngine] Loading base model: {model_path}")
        if adapter_path:
            print(f"[LLMEngine] Loading LoRA adapter: {adapter_path}")
        print("=" * 80)

        # load() 返回 (model, tokenizer)
        #   - model: 已加载到统一内存的 MLX 模型权重
        #   - tokenizer: 对应模型的分词器（含 chat_template）
        self.model, self.tokenizer = load(
            model_path,
            adapter_path=adapter_path,
        )
        self.model_path = model_path
        self.adapter_path = adapter_path
        print("[LLMEngine] Model loaded successfully.")

    # ------------------------------------------------------------------
    # 滑动窗口上下文截断
    # ------------------------------------------------------------------

    def truncate_messages(
        self,
        messages: list[dict],
        max_tokens: int | None = None,
    ) -> list[dict]:
        """
        保留 system 消息 + 最近 N 轮对话，总 token 数不超过 max_tokens。

        截断策略（滑动窗口）：
          1. system 消息固定保留（通常 1 条，token 占比较少）
          2. 从最新消息向旧消息方向累加 token 数（贪心保留最近的对话）
          3. 若累计超过阈值，丢弃更旧的 chat 消息
          4. 极端情况：若所有 chat 消息都无法塞入，至少保留最后一条

        参数：
          messages: 输入的消息列表，格式 [{"role": str, "content": str}, ...]
          max_tokens: 滑动窗口 token 上限，默认 CONTEXT_WINDOW_TOKENS (4096)

        返回：
          截断后的 messages 列表，保证总 token 数 ≤ max_tokens
        """
        if max_tokens is None:
            max_tokens = CONTEXT_WINDOW_TOKENS

        # 分离 system 消息和普通 chat 消息
        system_msgs = [m for m in messages if m["role"] == "system"]
        chat_msgs   = [m for m in messages if m["role"] != "system"]

        # 计算 system 消息占用的 token 数
        total_tokens = 0
        for m in system_msgs:
            total_tokens += len(self.tokenizer.encode(m["content"]))

        # 从最新→最旧遍历，贪心保留最近的消息
        kept_chat = []
        for m in reversed(chat_msgs):
            msg_tokens = len(self.tokenizer.encode(m["content"]))
            if total_tokens + msg_tokens > max_tokens:
                break  # 超出窗口，丢弃此条及更早的消息
            kept_chat.insert(0, m)
            total_tokens += msg_tokens

        result = system_msgs + kept_chat

        # 安全兜底：若所有 chat 消息都被截断，至少保留最后一条 user 消息
        if not kept_chat and chat_msgs:
            result = system_msgs + [chat_msgs[-1]]

        return result

    # ------------------------------------------------------------------
    # 提示词构建
    # ------------------------------------------------------------------

    def build_prompt(self, messages: list[dict]) -> str:
        """
        将结构化的 messages 列表拼接为模型可读的纯文本 prompt 字符串。

        内部调用 tokenizer.apply_chat_template() 完成转换。
        对于 Qwen2.5，模板格式大致为：
          <|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n

        参数：
          messages: [{"role": ..., "content": ...}, ...]

        返回：
          拼接后的 prompt 字符串（可直接输入模型 generate）
        """
        return self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,               # 只拼接字符串，不做 tokenize
            add_generation_prompt=True,    # 在末尾追加 assistant 起始标记
        )

    # ------------------------------------------------------------------
    # 流式生成（增量 delta 版本）
    # ------------------------------------------------------------------

    def stream_generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7):
        """
        对标 mlx_lm.stream_generate，产出逐 token 增量文本（delta）。

        注意：mlx_lm 的 stream_generate 返回的 response.text 本身就是增量
        （不同于某些框架返回已累积的完整文本），所以直接 yield 即可。

        参数：
          prompt: build_prompt() 输出的模型输入字符串
          max_tokens: 最大生成 token 数。Qwen2.5-7B 支持最大 32768，
                      但本地推理设 512 平衡响应延迟与输出质量
          temperature: 采样温度 (0.0~2.0)。
                       0.0 = argmax 确定输出，0.7 = 平衡创意与确定性

        Yields:
          str: 当前时间步生成的 token 文本增量（delta）
        """
        # make_sampler 封装了 top-p/top-k/temperature 采样策略
        # temperature=0 时自动转为 argmax 采样（贪心解码）
        sampler = make_sampler(temp=temperature)
        for response in stream_generate(
            self.model,          # mlx_lm 模型对象
            self.tokenizer,      # 分词器（用于实时 decode 生成的 token id）
            prompt=prompt,
            max_tokens=max_tokens,
            sampler=sampler,
        ):
            # response.text 是当前步的增量文本（1 个或几个 token 的解码结果）
            yield response.text

    # ------------------------------------------------------------------
    # 便捷方法：从截断 → 构建 prompt → 流式生成
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: list[dict],
        max_tokens: int = 512,
        temperature: float = 0.7,
        truncate: bool = True,
    ):
        """
        一站式聊天推理方法，将三步流水线封装为单个生成器：

          messages → truncate (可选) → build_prompt → stream_generate → yield delta

        参数：
          messages:   对话消息列表 [{"role":..., "content":...}, ...]
          max_tokens: 最大生成 token 数，默认 512
          temperature: 采样温度，默认 0.7
          truncate:   是否启用滑动窗口截断，默认 True

        Yields:
          str: 逐 token 生成的增量文本（delta）
        """
        if truncate:
            messages = self.truncate_messages(messages)
        prompt = self.build_prompt(messages)
        yield from self.stream_generate(prompt, max_tokens=max_tokens, temperature=temperature)

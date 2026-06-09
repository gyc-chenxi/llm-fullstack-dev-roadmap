"""
LLM 推理引擎
-----------
封装 mlx_lm 的模型加载、流式生成、以及滑动窗口上下文截断。
作为单例在应用启动时加载，挂载到 app.state.engine。
"""

from mlx_lm import load, stream_generate
from mlx_lm.sample_utils import make_sampler
from config import CONTEXT_WINDOW_TOKENS


class LLMEngine:
    """
    MLX 大模型推理引擎。

    职责：
      1. 加载模型 + tokenizer
      2. 流式生成（产出增量 delta，修复 mlx_lm 返回完整文本的 bug）
      3. 滑动窗口上下文截断（防止多轮对话 OOM）
    """

    def __init__(self, model_path: str, adapter_path: str | None = None):
        print("=" * 80)
        print(f"[LLMEngine] Loading base model: {model_path}")
        if adapter_path:
            print(f"[LLMEngine] Loading LoRA adapter: {adapter_path}")
        print("=" * 80)

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

        算法：
          1. 始终保留所有 system 消息（通常只有 1 条，token 数很少）
          2. 从最新消息向旧消息方向累加 token 数
          3. 超过阈值时丢弃更早的 chat 消息（system 消息不动）

        参数：
          messages: [{"role": "...", "content": "..."}, ...]
          max_tokens: token 上限，默认使用 CONTEXT_WINDOW_TOKENS

        返回：
          截断后的 messages 列表
        """
        if max_tokens is None:
            max_tokens = CONTEXT_WINDOW_TOKENS

        # 分离 system 消息和非 system 消息
        system_msgs = [m for m in messages if m["role"] == "system"]
        chat_msgs   = [m for m in messages if m["role"] != "system"]

        # 计算 system 消息的 token 占用
        total_tokens = 0
        for m in system_msgs:
            total_tokens += len(self.tokenizer.encode(m["content"]))

        # 从最新消息向前保留
        kept_chat = []
        for m in reversed(chat_msgs):
            msg_tokens = len(self.tokenizer.encode(m["content"]))
            if total_tokens + msg_tokens > max_tokens:
                break  # 再往前就更旧了，直接丢弃
            kept_chat.insert(0, m)
            total_tokens += msg_tokens

        result = system_msgs + kept_chat

        # 如果截断后没有任何 chat 消息（理论上不会），至少保留最后一条
        if not kept_chat and chat_msgs:
            result = system_msgs + [chat_msgs[-1]]

        return result

    # ------------------------------------------------------------------
    # 提示词构建
    # ------------------------------------------------------------------

    def build_prompt(self, messages: list[dict]) -> str:
        """
        使用 tokenizer 的 chat_template 将 messages 列表拼接成模型输入字符串。
        """
        return self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    # ------------------------------------------------------------------
    # 流式生成（增量 delta 版本）
    # ------------------------------------------------------------------

    def stream_generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7):
        """
        对标 mlx_lm.stream_generate。
        mlx_lm 的 stream_generate 返回的 response.text 本身就是增量文本（delta），
        直接透传即可。

        参数：
          prompt: 输入提示词字符串
          max_tokens: 最大生成 token 数
          temperature: 采样温度（0.0~2.0），越低越确定，0.0 等价于 argmax

        Yields:
          str: 本次生成的新增 token 文本（delta）
        """
        sampler = make_sampler(temp=temperature)
        for response in stream_generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            sampler=sampler,
        ):
            # response.text 已经是增量文本，直接 yield
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
        一站式聊天方法：
          1. （可选）滑动窗口截断
          2. 构建 prompt
          3. 流式生成

        参数：
          messages: 对话消息列表
          max_tokens: 最大生成 token 数
          temperature: 采样温度
          truncate: 是否启用滑动窗口截断

        Yields:
          str: 增量 delta 文本
        """
        if truncate:
            messages = self.truncate_messages(messages)
        prompt = self.build_prompt(messages)
        yield from self.stream_generate(prompt, max_tokens=max_tokens, temperature=temperature)

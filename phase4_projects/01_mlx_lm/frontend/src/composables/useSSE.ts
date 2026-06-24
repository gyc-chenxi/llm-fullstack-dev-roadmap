/**
 * SSE 流式数据解析工具函数
 * ------------------------
 * 封装了 Server-Sent Events 协议的行解析与 delta 提取逻辑。
 *
 * SSE 数据流格式（OpenAI 兼容）：
 *   data: {"choices":[{"delta":{"content":"你好"},"finish_reason":null}]}
 *   data: {"choices":[{"delta":{"content":"世"},"finish_reason":null}]}
 *   data: {"choices":[{"delta":{},"finish_reason":"stop"}]}
 *   data: [DONE]
 *
 * 消费方：stores/chat.ts 中的 sendMessage() 使用 ReadableStream 读取响应体，
 *         逐行调用本模块的函数解析。
 */

/**
 * 解析单行 SSE 数据。
 *
 * @param line - 原始 SSE 行（如 `data: {"key":"value"}`）
 * @returns 解析后的 JSON 对象；遇到 [DONE] 返回 null；空行或非 data 行返回 undefined
 */
export function parseSSELine(
  line: string
): Record<string, unknown> | null | undefined {
  const trimmed = line.trim();
  if (!trimmed || !trimmed.startsWith("data:")) return undefined;

  const data = trimmed.slice(5).trim(); // 去掉 "data:" 前缀
  if (data === "[DONE]") return null;   // SSE 流结束标记

  try {
    return JSON.parse(data);
  } catch {
    return undefined;
  }
}

/**
 * 从解析后的 SSE chunk 中提取 delta 文本内容。
 *
 * chunk 结构参考：
 *   {"choices": [{"index": 0, "delta": {"content": "你好"}, "finish_reason": null}]}
 *
 * @param parsed - parseSSELine 的返回值
 * @returns delta 文本字符串；如果 delta 不存在或流已结束则返回 null
 */
export function extractDelta(
  parsed: Record<string, unknown> | null | undefined
): string | null {
  if (!parsed) return null;
  const choices = parsed.choices as Array<{
    delta?: { content?: string };
  }> | null;
  return choices?.[0]?.delta?.content ?? null;
}

/**
 * SSE 流式消费 Composable
 * -----------------------
 * 封装了 ReadableStream SSE 读取、行缓冲、AbortController 停止生成等逻辑。
 * 当前直接集成在 stores/chat.ts 的 sendMessage 中，
 * 此文件提供可复用的底层工具函数。
 */

/**
 * 解析 SSE 数据行为 JSON 对象。
 * 行格式："data: {...}" 或 "data: [DONE]"
 *
 * @returns 解析后的 JSON 对象；如果是 [DONE] 返回 null；解析失败返回 undefined
 */
export function parseSSELine(
  line: string
): Record<string, unknown> | null | undefined {
  const trimmed = line.trim();
  if (!trimmed || !trimmed.startsWith("data:")) return undefined;

  const data = trimmed.slice(5).trim(); // 去掉 "data:" 前缀
  if (data === "[DONE]") return null;

  try {
    return JSON.parse(data);
  } catch {
    return undefined;
  }
}

/**
 * 从 SSE chunk 中提取 delta 文本内容
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

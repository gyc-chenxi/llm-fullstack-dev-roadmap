/**
 * SSE streaming chat completion client.
 *
 * Design decisions:
 * - Uses ReadableStream + TextDecoder for incremental parsing (no polling).
 * - Returns an AbortController handle so the caller can cancel mid-stream.
 * - Errors are surfaced via onError callback, not thrown — the UI should never
 *   crash because of a network glitch or a malformed SSE line.
 */
import type { ChatCompletionChunk, ChatMessage } from '../types'

export interface StreamCallbacks {
  onDelta: (content: string) => void
  onDone: (finalContent: string) => void
  onError: (err: Error) => void
}

export interface StreamConfig {
  baseUrl: string
  model: string
  messages: ChatMessage[]
  temperature: number
  topP: number
  maxTokens: number
}

export function streamChatCompletion(
  config: StreamConfig,
  callbacks: StreamCallbacks,
): { abort: () => void } {
  const controller = new AbortController()
  let fullContent = ''

  void (async () => {
    try {
      const resp = await fetch(`${config.baseUrl}/v1/chat/completions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        body: JSON.stringify({
          model: config.model,
          messages: config.messages,
          temperature: config.temperature,
          top_p: config.topP,
          max_tokens: config.maxTokens,
          stream: true,
        }),
      })

      if (!resp.ok) {
        const text = await resp.text().catch(() => 'unable to read response body')
        throw new Error(`HTTP ${resp.status}: ${text.slice(0, 500)}`)
      }

      if (!resp.body) {
        throw new Error('Response body is empty — streaming not supported')
      }

      const reader = resp.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let buffer = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const rawLine of lines) {
          const line = rawLine.trim()
          if (!line.startsWith('data: ')) continue

          const payload = line.slice('data: '.length).trim()
          if (payload === '[DONE]') {
            callbacks.onDone(fullContent)
            return
          }

          try {
            const chunk: ChatCompletionChunk = JSON.parse(payload)
            const delta = chunk?.choices?.[0]?.delta?.content
            if (delta) {
              fullContent += delta
              callbacks.onDelta(delta)
            }
          } catch {
            // Malformed SSE lines are ignored — the stream may contain
            // comments or keepalive pings that aren't valid JSON.
          }
        }
      }

      // Stream ended without [DONE] sentinel — treat as complete.
      callbacks.onDone(fullContent)
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        callbacks.onDone(fullContent)
        return
      }
      callbacks.onError(err instanceof Error ? err : new Error(String(err)))
    }
  })()

  return { abort: () => controller.abort() }
}

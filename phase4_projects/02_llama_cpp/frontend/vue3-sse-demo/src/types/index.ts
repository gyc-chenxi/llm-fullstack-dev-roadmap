/** Core type definitions for the AI Gateway chat application. */

// ---- API Contracts ----

export type ChatRole = 'system' | 'user' | 'assistant' | 'tool'

export interface ChatMessage {
  role: ChatRole
  content: string
}

export interface ChatCompletionRequest {
  model?: string | null
  messages: ChatMessage[]
  temperature?: number
  top_p?: number
  max_tokens?: number
  stream?: boolean
}

export interface ChatDelta {
  role?: ChatRole
  content?: string
}

export interface ChatChoice {
  index: number
  delta: ChatDelta
  finish_reason: string | null
}

export interface ChatCompletionChunk {
  id: string
  object: string
  created: number
  model: string
  choices: ChatChoice[]
}

export interface ChatMessageFinal {
  role: ChatRole
  content: string
}

export interface ChatChoiceFinal {
  index: number
  finish_reason: string
  message: ChatMessageFinal
}

export interface UsageInfo {
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
}

export interface ChatCompletionResponse {
  id: string
  object: string
  created: number
  model: string
  choices: ChatChoiceFinal[]
  usage: UsageInfo
  _gateway?: {
    latency_ms: number
  }
}

// ---- Health ----

export type HealthStatus = 'ok' | 'degraded' | 'error'

export interface HealthResponse {
  status: HealthStatus
  upstream: string
  detail: string | null
}

// ---- UI State ----

export type MessageStatus = 'pending' | 'streaming' | 'done' | 'error'

export interface UIMessage {
  id: string
  role: ChatRole
  content: string
  status: MessageStatus
  error?: string
  timestamp: number
  /** Gateway-reported latency (only available for last assistant msg). */
  gatewayLatencyMs?: number
}

export interface AppSettings {
  model: string
  temperature: number
  topP: number
  maxTokens: number
  systemPrompt: string
}

export const DEFAULT_SETTINGS: AppSettings = {
  model: 'local-qwen2.5-7b-q4',
  temperature: 0.2,
  topP: 0.9,
  maxTokens: 512,
  systemPrompt: '你是一个严谨的 AI Infra 工程师，回答要结构化、有深度。',
}

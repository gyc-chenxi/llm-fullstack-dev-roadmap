/**
 * useChat — reactive chat session composable.
 *
 * Owns:
 * - Message list (history + current streaming message)
 * - Send / abort lifecycle
 * - Loading & error state
 *
 * Keeps zero DOM dependency — the component layer handles rendering only.
 */
import { ref, computed, type Ref } from 'vue'
import { streamChatCompletion, type StreamConfig } from '../api/llm'
import type { UIMessage, AppSettings, ChatMessage } from '../types'
import { DEFAULT_SETTINGS } from '../types'

let _msgSeq = 0
function nextId(): string {
  return `msg-${Date.now()}-${++_msgSeq}`
}

export interface UseChatOptions {
  baseUrl: string
  settings: Ref<AppSettings>
}

export function useChat(opts: UseChatOptions) {
  const messages = ref<UIMessage[]>([])
  const loading = ref(false)
  const error = ref('')
  let _abort: (() => void) | null = null
  let _currentAssistantId: string | null = null

  const isStreaming = computed(() => {
    if (!_currentAssistantId) return false
    const msg = messages.value.find((m) => m.id === _currentAssistantId)
    return msg?.status === 'streaming'
  })

  function buildApiMessages(): ChatMessage[] {
    const s = opts.settings.value
    const apiMsgs: ChatMessage[] = []

    if (s.systemPrompt.trim()) {
      apiMsgs.push({ role: 'system', content: s.systemPrompt.trim() })
    }

    // Only send completed messages (skip the in-flight streaming one).
    for (const m of messages.value) {
      if (m.status === 'done') {
        apiMsgs.push({ role: m.role, content: m.content })
      }
    }
    return apiMsgs
  }

  function send(userText: string): void {
    const text = userText.trim()
    if (!text || loading.value) return

    error.value = ''

    // Add user message
    messages.value.push({
      id: nextId(),
      role: 'user',
      content: text,
      status: 'done',
      timestamp: Date.now(),
    })

    // Add placeholder assistant message (will be filled by streaming)
    const assistantId = nextId()
    _currentAssistantId = assistantId
    messages.value.push({
      id: assistantId,
      role: 'assistant',
      content: '',
      status: 'streaming',
      timestamp: Date.now(),
    })

    loading.value = true

    const config: StreamConfig = {
      baseUrl: opts.baseUrl,
      model: opts.settings.value.model,
      messages: buildApiMessages(),
      temperature: opts.settings.value.temperature,
      topP: opts.settings.value.topP,
      maxTokens: opts.settings.value.maxTokens,
    }

    const { abort } = streamChatCompletion(config, {
      onDelta(content: string) {
        const msg = messages.value.find((m) => m.id === assistantId)
        if (msg) msg.content += content
      },
      onDone(_finalContent: string) {
        finishAssistant(assistantId, 'done')
      },
      onError(err: Error) {
        error.value = err.message
        finishAssistant(assistantId, 'error', err.message)
      },
    })

    _abort = abort
  }

  function finishAssistant(
    id: string,
    status: UIMessage['status'],
    errMsg?: string,
  ): void {
    const msg = messages.value.find((m) => m.id === id)
    if (msg) {
      msg.status = status
      if (errMsg) msg.error = errMsg
      msg.timestamp = Date.now()
    }
    loading.value = false
    _abort = null
    _currentAssistantId = null
  }

  function abort(): void {
    if (_abort) {
      _abort()
      _abort = null
    }
    if (_currentAssistantId) {
      // If the assistant already has partial content, mark as done;
      // otherwise remove the empty placeholder.
      const msg = messages.value.find((m) => m.id === _currentAssistantId)
      if (msg && msg.content.length > 0) {
        msg.status = 'done'
      } else if (msg) {
        messages.value = messages.value.filter((m) => m.id !== _currentAssistantId)
      }
    }
    loading.value = false
    _currentAssistantId = null
  }

  function clear(): void {
    abort()
    messages.value = []
    error.value = ''
  }

  return {
    messages,
    loading,
    isStreaming,
    error,
    send,
    abort,
    clear,
  }
}

<script setup lang="ts">
/**
 * ChatInput — text area with send/stop button and keyboard shortcut.
 *
 * Features:
 * - Enter to send, Shift+Enter for newline
 * - Auto-grow textarea (up to 6 lines)
 * - Send / Stop toggle based on streaming state
 * - Character-aware disabled state
 */
import { ref, watch, nextTick, type Ref } from 'vue'

const props = defineProps<{
  loading: boolean
  isStreaming: boolean
  disabled: boolean
}>()

const emit = defineEmits<{
  send: [text: string]
  abort: []
}>()

const text = ref('')
const textarea = ref<HTMLTextAreaElement | null>(null)

function handleKeydown(e: KeyboardEvent): void {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSubmit()
  }
}

function handleSubmit(): void {
  const val = text.value.trim()
  if (!val || props.loading) return
  emit('send', val)
  text.value = ''
  // Reset textarea height
  nextTick(() => {
    if (textarea.value) {
      textarea.value.style.height = 'auto'
    }
  })
}

function handleAbort(): void {
  emit('abort')
}

function autoGrow(): void {
  const el = textarea.value
  if (!el) return
  el.style.height = 'auto'
  const lineHeight = 24
  const maxHeight = lineHeight * 6
  el.style.height = `${Math.min(el.scrollHeight, maxHeight)}px`
}

// Focus textarea on mount
watch(
  () => props.loading,
  (val) => {
    if (!val) {
      nextTick(() => textarea.value?.focus())
    }
  },
  { immediate: true },
)
</script>

<template>
  <footer class="chat-input">
    <div class="chat-input__wrap">
      <textarea
        ref="textarea"
        v-model="text"
        class="chat-input__textarea"
        :disabled="disabled"
        placeholder="输入消息… Enter 发送，Shift+Enter 换行"
        rows="1"
        @keydown="handleKeydown"
        @input="autoGrow"
      />
      <button
        v-if="!isStreaming"
        class="chat-input__btn chat-input__btn--send"
        :disabled="!text.trim() || loading"
        @click="handleSubmit"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13" />
          <polygon points="22 2 15 22 11 13 2 9 22 2" />
        </svg>
      </button>
      <button
        v-else
        class="chat-input__btn chat-input__btn--stop"
        @click="handleAbort"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
          <rect x="4" y="4" width="16" height="16" rx="2" />
        </svg>
      </button>
    </div>
    <p class="chat-input__hint">
      <kbd>Enter</kbd> 发送 · <kbd>Shift</kbd>+<kbd>Enter</kbd> 换行
    </p>
  </footer>
</template>

<style scoped>
.chat-input {
  padding: 16px 20px;
  border-top: 1px solid var(--color-border);
  background: var(--color-surface-1);
}

.chat-input__wrap {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.chat-input__textarea {
  flex: 1;
  resize: none;
  padding: 10px 14px;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  font-size: 0.925rem;
  font-family: inherit;
  line-height: 1.5;
  background: var(--color-surface-2);
  color: var(--color-text);
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  min-height: 44px;
  max-height: 156px;
}

.chat-input__textarea:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-accent) 20%, transparent);
}

.chat-input__textarea:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-input__btn {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.15s ease;
}

.chat-input__btn:active {
  transform: scale(0.94);
}

.chat-input__btn--send {
  background: var(--color-accent);
  color: #fff;
}

.chat-input__btn--send:hover:not(:disabled) {
  background: var(--color-accent-hover);
}

.chat-input__btn--send:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.chat-input__btn--stop {
  background: var(--color-error);
  color: #fff;
}

.chat-input__btn--stop:hover {
  background: color-mix(in srgb, var(--color-error) 85%, black);
}

.chat-input__hint {
  margin: 6px 0 0;
  font-size: 0.72rem;
  color: var(--color-text-muted);
  text-align: right;
}

kbd {
  display: inline-block;
  padding: 1px 5px;
  font-size: 0.7rem;
  font-family: inherit;
  border: 1px solid var(--color-border);
  border-radius: 3px;
  background: var(--color-surface-2);
}
</style>

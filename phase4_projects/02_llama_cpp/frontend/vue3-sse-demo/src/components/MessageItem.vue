<script setup lang="ts">
/**
 * MessageItem — single chat bubble.
 *
 * Renders distinct styles per role (user / assistant / system) and
 * shows a subtle streaming cursor when the message is in-flight.
 */
import type { UIMessage } from '../types'

defineProps<{
  message: UIMessage
}>()
</script>

<template>
  <article
    class="msg"
    :class="{
      'msg--user': message.role === 'user',
      'msg--assistant': message.role === 'assistant',
      'msg--system': message.role === 'system',
      'msg--streaming': message.status === 'streaming',
      'msg--error': message.status === 'error',
    }"
  >
    <header class="msg__role">
      {{ message.role === 'assistant' ? 'AI' : message.role === 'user' ? 'You' : 'System' }}
    </header>
    <div class="msg__body">
      <p v-if="message.role === 'assistant'" class="msg__text">
        {{ message.content }}<span v-if="message.status === 'streaming'" class="msg__cursor">|</span>
      </p>
      <p v-else class="msg__text">{{ message.content }}</p>
      <p v-if="message.status === 'error' && message.error" class="msg__err">
        Error: {{ message.error }}
      </p>
    </div>
    <footer class="msg__meta">
      <time :datetime="new Date(message.timestamp).toISOString()">
        {{ new Date(message.timestamp).toLocaleTimeString() }}
      </time>
      <span v-if="message.status === 'streaming'" class="msg__tag msg__tag--live">LIVE</span>
      <span v-if="message.status === 'error'" class="msg__tag msg__tag--err">FAILED</span>
    </footer>
  </article>
</template>

<style scoped>
.msg {
  max-width: 78%;
  padding: 12px 16px;
  border-radius: 12px;
  animation: msg-in 0.25s ease-out;
}

.msg--user {
  align-self: flex-end;
  background: var(--color-accent);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.msg--assistant {
  align-self: flex-start;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-bottom-left-radius: 4px;
}

.msg--system {
  align-self: center;
  background: var(--color-surface-1);
  border: 1px dashed var(--color-border);
  max-width: 90%;
  font-size: 0.875rem;
  opacity: 0.85;
}

.msg__role {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: 6px;
  opacity: 0.7;
}

.msg--user .msg__role {
  color: rgba(255, 255, 255, 0.8);
}

.msg__text {
  margin: 0;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
}

.msg__cursor {
  display: inline-block;
  animation: blink 0.8s step-end infinite;
  font-weight: 100;
  color: var(--color-accent);
}

.msg--streaming .msg__text {
  /* subtle indication that content is still arriving */
}

@keyframes blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}

@keyframes msg-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.msg__meta {
  margin-top: 6px;
  font-size: 0.7rem;
  opacity: 0.55;
  display: flex;
  gap: 8px;
  align-items: center;
}

.msg--user .msg__meta {
  color: rgba(255, 255, 255, 0.7);
}

.msg__tag {
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  padding: 1px 6px;
  border-radius: 3px;
}

.msg__tag--live {
  background: var(--color-accent);
  color: #fff;
}

.msg__tag--err {
  background: var(--color-error);
  color: #fff;
}

.msg__err {
  margin: 8px 0 0;
  font-size: 0.8rem;
  color: var(--color-error);
  background: color-mix(in srgb, var(--color-error) 10%, transparent);
  padding: 6px 10px;
  border-radius: 6px;
}
</style>

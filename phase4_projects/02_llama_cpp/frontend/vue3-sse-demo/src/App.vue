<script setup lang="ts">
/**
 * App.vue — Enterprise AI Gateway Chat root component.
 *
 * Layout:
 * ┌──────────┬──────────────────────┐
 * │ Sidebar  │ Header (health)      │
 * │ Settings ├──────────────────────┤
 * │          │ Message List         │
 * │          │                      │
 * │          ├──────────────────────┤
 * │          │ Chat Input           │
 * └──────────┴──────────────────────┘
 */
import { ref, watch, nextTick, onMounted } from 'vue'
import { useChat } from './composables/useChat'
import { useHealth } from './composables/useHealth'
import { DEFAULT_SETTINGS } from './types'
import type { AppSettings } from './types'

import HealthBadge from './components/HealthBadge.vue'
import MessageItem from './components/MessageItem.vue'
import ChatInput from './components/ChatInput.vue'
import SettingsPanel from './components/SettingsPanel.vue'

// ---- Configuration ----
const BASE_URL = '' // Vite proxy handles /v1 → Gateway :8000

// ---- Reactive state ----
const settings = ref<AppSettings>({ ...DEFAULT_SETTINGS })
const sidebarOpen = ref(false)

const chat = useChat({ baseUrl: BASE_URL, settings })
const health = useHealth({ baseUrl: BASE_URL, intervalMs: 15_000 })

// ---- Scroll-to-bottom logic ----
const messageList = ref<HTMLElement | null>(null)

function scrollToBottom(): void {
  nextTick(() => {
    const el = messageList.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

watch(
  () => chat.messages.value.length,
  () => scrollToBottom(),
)
watch(
  () => chat.messages.value.at(-1)?.content,
  () => scrollToBottom(),
)

onMounted(() => scrollToBottom())

// ---- Handlers ----
function handleSend(text: string): void {
  chat.send(text)
}

function handleAbort(): void {
  chat.abort()
}

function handleClear(): void {
  if (chat.messages.value.length === 0 || chat.loading.value) return
  chat.clear()
  scrollToBottom()
}
</script>

<template>
  <div class="app-shell">
    <!-- Sidebar -->
    <aside class="sidebar" :class="{ 'sidebar--open': sidebarOpen }">
      <div class="sidebar__brand">
        <span class="sidebar__logo">🧠</span>
        <span class="sidebar__name">AI Gateway</span>
      </div>
      <SettingsPanel v-model="settings" />
      <div class="sidebar__footer">
        <p class="sidebar__version">v0.1.0 · llama.cpp serving lab</p>
      </div>
    </aside>

    <!-- Main area -->
    <div class="main">
      <!-- Header -->
      <header class="header">
        <div class="header__left">
          <button
            class="header__menu-btn"
            aria-label="Toggle sidebar"
            @click="sidebarOpen = !sidebarOpen"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
          <h1 class="header__title">Chat</h1>
          <span class="header__model-tag">{{ settings.model }}</span>
        </div>
        <div class="header__right">
          <HealthBadge
            :status="health.status.value"
            :upstream="health.upstream.value"
            :detail="health.detail.value"
          />
        </div>
      </header>

      <!-- Messages -->
      <section
        ref="messageList"
        class="message-list"
        aria-label="Chat messages"
        aria-live="polite"
      >
        <div v-if="chat.messages.value.length === 0" class="message-list__empty">
          <div class="empty-state">
            <span class="empty-state__icon">⚡</span>
            <h2 class="empty-state__title">llama.cpp AI Gateway Ready</h2>
            <p class="empty-state__desc">
              Qwen2.5-7B-Q4_K_M · Metal 后端 · SSE 流式推理<br />
              输入问题开始对话，右侧面板可调整推理参数。
            </p>
          </div>
        </div>
        <MessageItem
          v-for="msg in chat.messages.value"
          :key="msg.id"
          :message="msg"
        />
        <div v-if="chat.error.value" class="message-list__global-err">
          {{ chat.error.value }}
        </div>
      </section>

      <!-- Input -->
      <ChatInput
        :loading="chat.loading.value"
        :is-streaming="chat.isStreaming.value"
        :disabled="false"
        @send="handleSend"
        @abort="handleAbort"
      />
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  background: var(--color-surface-1);
}

/* ---- Sidebar ---- */
.sidebar {
  width: 280px;
  flex-shrink: 0;
  background: var(--color-surface-1);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  transition: transform 0.25s ease;
  z-index: 100;
}

.sidebar__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 20px;
  border-bottom: 1px solid var(--color-border);
}

.sidebar__logo {
  font-size: 1.5rem;
}

.sidebar__name {
  font-weight: 700;
  font-size: 1rem;
  letter-spacing: -0.01em;
  color: var(--color-text);
}

.sidebar__footer {
  margin-top: auto;
  padding: 14px 20px;
  border-top: 1px solid var(--color-border);
}

.sidebar__version {
  margin: 0;
  font-size: 0.7rem;
  color: var(--color-text-muted);
}

/* ---- Main ---- */
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* ---- Header ---- */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface-1);
  flex-shrink: 0;
}

.header__left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header__right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header__menu-btn {
  display: none;
  background: none;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
}

.header__menu-btn:hover {
  background: var(--color-surface-2);
}

.header__title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text);
}

.header__model-tag {
  font-size: 0.68rem;
  padding: 2px 8px;
  border-radius: 100px;
  background: var(--color-surface-2);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
  font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
}

/* ---- Message list ---- */
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  scroll-behavior: smooth;
}

.message-list__empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.message-list__global-err {
  align-self: center;
  padding: 10px 18px;
  background: color-mix(in srgb, var(--color-error) 12%, transparent);
  color: var(--color-error);
  border-radius: 8px;
  font-size: 0.85rem;
  border: 1px solid color-mix(in srgb, var(--color-error) 25%, transparent);
}

/* ---- Empty state ---- */
.empty-state {
  text-align: center;
  max-width: 400px;
}

.empty-state__icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 16px;
}

.empty-state__title {
  margin: 0 0 8px;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
}

.empty-state__desc {
  margin: 0;
  font-size: 0.875rem;
  line-height: 1.6;
  color: var(--color-text-muted);
}

/* ---- Responsive: sidebar collapses on narrow screens ---- */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    transform: translateX(-100%);
    box-shadow: none;
  }

  .sidebar--open {
    transform: translateX(0);
    box-shadow: 4px 0 20px rgba(0, 0, 0, 0.2);
  }

  .header__menu-btn {
    display: block;
  }
}
</style>

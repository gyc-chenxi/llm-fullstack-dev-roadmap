<template>
  <!--
    ChatInput.vue — 消息输入区域
    ----------------------------
    - textarea 支持 Enter 发送（Shift+Enter 换行）
    - 自动调整高度
    - 发送按钮 / 停止生成按钮互斥显示
  -->
  <div class="flex items-end gap-2">
    <!-- 文本输入框 -->
    <textarea
      ref="inputEl"
      v-model="inputText"
      @keydown="handleKeydown"
      @input="autoResize"
      :disabled="store.isStreaming"
      placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
      rows="1"
      class="flex-1 resize-none rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 placeholder-gray-400 dark:placeholder-gray-500"
    ></textarea>

    <!-- 流式中：显示停止按钮 -->
    <button
      v-if="store.isStreaming"
      @click="handleStop"
      class="flex-shrink-0 px-4 py-2.5 rounded-xl bg-red-500 hover:bg-red-600 text-white text-sm font-medium transition-colors flex items-center gap-1.5"
    >
      <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
        <rect x="6" y="6" width="12" height="12" rx="1" />
      </svg>
      停止
    </button>

    <!-- 非流式：显示发送按钮 -->
    <button
      v-else
      @click="handleSend"
      :disabled="!inputText.trim()"
      class="flex-shrink-0 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 dark:disabled:bg-gray-600 text-white text-sm font-medium transition-colors disabled:cursor-not-allowed flex items-center gap-1.5"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
      </svg>
      发送
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from "vue";
import { useChatStore } from "../stores/chat";

const store = useChatStore();
const inputText = ref("");
const inputEl = ref<HTMLTextAreaElement | null>(null);

/**
 * 处理键盘事件
 */
function handleKeydown(e: KeyboardEvent) {
  // 中文输入法正在组合候选字时不触发发送（如拼音选词按 Enter）
  if (e.isComposing || e.key === "Process") return;

  // Enter 发送（不按 Shift）
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
}

/**
 * 发送消息
 */
async function handleSend() {
  const text = inputText.value.trim();
  if (!text || store.isStreaming) return;

  inputText.value = "";
  // 重置 textarea 高度
  await nextTick();
  if (inputEl.value) {
    inputEl.value.style.height = "auto";
  }

  await store.sendMessage(text);
}

/**
 * 停止生成
 */
function handleStop() {
  store.stopGeneration();
}

/**
 * 自动调整 textarea 高度
 */
function autoResize() {
  const el = inputEl.value;
  if (!el) return;
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 200) + "px";
}

/**
 * 供父组件调用：设置预设文本并聚焦
 */
function setPromptText(text: string) {
  inputText.value = text;
  nextTick(() => {
    if (inputEl.value) {
      inputEl.value.focus();
      autoResize();
    }
  });
}

defineExpose({ setPromptText, inputEl });
</script>

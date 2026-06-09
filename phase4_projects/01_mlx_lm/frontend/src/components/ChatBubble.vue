<template>
  <!--
    ChatBubble.vue — 单条消息气泡
    -----------------------------
    根据 role 渲染不同样式：
      - User:  右侧蓝紫色气泡，👤 头像（可在下方修改）
      - Assistant: 左侧灰色气泡 + Markdown 渲染，🤖 头像（可在下方修改）
    流式输出时显示闪烁光标。

    自定义头像方法：
      - 修改 AI 头像：找到下方 "🤖 AI_AVATAR" 处的 emoji 或文本
      - 修改 User 头像：找到下方 "👤 USER_AVATAR" 处的 emoji 或文本
      - 如果想用图片，将对应 div 替换为 <img src="url" class="w-8 h-8 rounded-full" />
  -->
  <div
    :class="[
      'flex gap-3 animate-fade-in',
      message.role === 'user' ? 'justify-end' : 'justify-start',
    ]"
  >
    <!-- AI 头像（左侧） -->
    <!-- 🤖 AI_AVATAR: 改此处的 emoji / 文本 / 图片即可更换 AI 头像 -->
    <div v-if="message.role === 'assistant'" class="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white text-sm">
      🤖
    </div>

    <!-- 消息气泡内容 -->
    <div
      :class="[
        'max-w-[80%] rounded-2xl px-4 py-3 break-words shadow-sm',
        message.role === 'user'
          ? 'bg-blue-600 text-white rounded-br-md'
          : 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-600 rounded-bl-md',
      ]"
    >
      <!-- 加载状态（空消息 + 流式中） -->
      <div v-if="!message.content && isStreaming" class="flex items-center gap-1.5 py-2">
        <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
        <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
        <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
      </div>

      <!-- User 消息（纯文本） -->
      <div v-else-if="message.role === 'user'" class="text-sm leading-relaxed whitespace-pre-wrap">
        {{ message.content }}
      </div>

      <!-- AI 消息（Markdown 渲染） -->
      <div
        v-else
        ref="markdownEl"
        class="prose prose-sm dark:prose-invert max-w-none text-sm leading-relaxed"
        v-html="renderedMarkdown"
      ></div>

      <!-- 流式输出光标 -->
      <span
        v-if="isStreaming && message.content"
        class="inline-block w-2 h-4 ml-0.5 bg-blue-500 animate-pulse align-text-bottom rounded-sm"
      ></span>
    </div>

    <!-- User 头像（右侧） -->
    <!-- 👤 USER_AVATAR: 改此处的 emoji / 文本 / 图片即可更换用户头像 -->
    <div v-if="message.role === 'user'" class="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center text-white text-sm">
      👤
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick } from "vue";
import { renderMarkdown, attachCopyButtons } from "../utils/markdown";
import type { ChatMessage } from "../stores/chat";

const props = defineProps<{
  message: ChatMessage;
  isStreaming: boolean;
}>();

const markdownEl = ref<HTMLElement | null>(null);

// 将 Markdown 文本渲染为 HTML
const renderedMarkdown = computed(() => {
  if (props.message.role !== "assistant") return "";
  return renderMarkdown(props.message.content);
});

// 每次渲染后挂载复制按钮
watch(renderedMarkdown, async () => {
  await nextTick();
  if (markdownEl.value) {
    attachCopyButtons(markdownEl.value);
  }
});
</script>

<style scoped>
@keyframes fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in {
  animation: fade-in 0.3s ease-out;
}
</style>

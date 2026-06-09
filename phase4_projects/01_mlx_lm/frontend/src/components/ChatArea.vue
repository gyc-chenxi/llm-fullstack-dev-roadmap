<template>
  <!--
    ChatArea.vue — 主聊天区域
    --------------------------
    显示当前会话的消息列表 + 底部输入框。
    支持流式打字机效果、自动滚动、Markdown 渲染。
  -->
  <div class="flex flex-col h-full">
    <!-- 顶部栏：切换侧边栏 + 会话标题 -->
    <header
      class="flex items-center gap-3 px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
    >
      <!-- 移动端菜单按钮 -->
      <button
        @click="store.toggleSidebar()"
        class="md:hidden p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <div class="flex-1 min-w-0">
        <h1 class="text-sm font-semibold truncate">
          {{ store.currentSession?.title || "新对话" }}
        </h1>
      </div>

      <!-- 新建对话按钮 -->
      <button
        @click="handleNewChat"
        class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
        title="新建对话"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
      </button>
    </header>

    <!-- 消息列表（可滚动区域） -->
    <div
      ref="chatContainer"
      @scroll="autoScroll.onUserScroll"
      class="flex-1 overflow-y-auto px-4 py-6"
    >
      <!-- 空状态：欢迎页面 -->
      <div
        v-if="store.messages.length === 0"
        class="flex flex-col items-center justify-center h-full text-gray-400 px-4"
      >
        <!-- Logo -->
        <div class="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white text-4xl shadow-lg mb-6">
          🤖
        </div>
        <div class="text-center mb-2">
          <h2 class="text-xl font-bold text-gray-800 dark:text-gray-100 tracking-wide">
            晨熙的本地大模型助手
          </h2>
          <p class="text-[13px] text-gray-400 dark:text-gray-500 font-light tracking-wider mt-0.5">
            Chenxi's Local LLM
          </p>
        </div>
        <p class="text-sm text-gray-400 mb-8">
          基于 Qwen2.5-7B + MLX，全部推理在本地完成
        </p>

        <!-- 功能卡片 -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-md">
          <div class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-blue-300 dark:hover:border-blue-600 transition-colors cursor-pointer group" @click="setQuickPrompt('帮我写一段 Python 代码，实现')">
            <div class="text-2xl mb-2">💻</div>
            <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 group-hover:text-blue-600 dark:group-hover:text-blue-400">代码开发</h3>
            <p class="text-xs text-gray-400 mt-1">Python · TypeScript · Vue3 · FastAPI</p>
          </div>
          <div class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-purple-300 dark:hover:border-purple-600 transition-colors cursor-pointer group" @click="setQuickPrompt('解释一下 MLX 框架中的')">
            <div class="text-2xl mb-2">🧠</div>
            <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 group-hover:text-purple-600 dark:group-hover:text-purple-400">AI/ML 知识</h3>
            <p class="text-xs text-gray-400 mt-1">LoRA · DPO · MLX · 模型量化</p>
          </div>
          <div class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-green-300 dark:hover:border-green-600 transition-colors cursor-pointer group" @click="setQuickPrompt('帮我设计一个系统架构，需求是')">
            <div class="text-2xl mb-2">🏗️</div>
            <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 group-hover:text-green-600 dark:group-hover:text-green-400">架构设计</h3>
            <p class="text-xs text-gray-400 mt-1">全栈架构 · API 设计 · 性能优化</p>
          </div>
          <div class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-orange-300 dark:hover:border-orange-600 transition-colors cursor-pointer group" @click="setQuickPrompt('翻译以下内容：')">
            <div class="text-2xl mb-2">🌐</div>
            <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 group-hover:text-orange-600 dark:group-hover:text-orange-400">翻译助手</h3>
            <p class="text-xs text-gray-400 mt-1">中英互译 · 代码文档翻译</p>
          </div>
        </div>

        <p class="text-xs text-gray-400 mt-8">
          输入消息，按 <kbd class="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded text-[11px] font-mono">Enter</kbd> 发送 · <kbd class="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded text-[11px] font-mono">Shift+Enter</kbd> 换行
        </p>
      </div>

      <!-- 消息气泡列表 -->
      <div v-else class="max-w-3xl mx-auto space-y-6">
        <ChatBubble
          v-for="(msg, idx) in store.messages"
          :key="idx"
          :message="msg"
          :is-streaming="store.isStreaming && idx === store.messages.length - 1 && msg.role === 'assistant'"
        />
      </div>
    </div>

    <!-- 底部输入区域 -->
    <div class="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-3">
      <div class="max-w-3xl mx-auto">
        <ChatInput ref="chatInputRef" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from "vue";
import { useRoute, useRouter } from "vue-router";
import ChatBubble from "./ChatBubble.vue";
import ChatInput from "./ChatInput.vue";
import { useChatStore } from "../stores/chat";
import { useAutoScroll } from "../composables/useAutoScroll";

const store = useChatStore();
const route = useRoute();
const router = useRouter();

const chatContainer = ref<HTMLElement | null>(null);
const chatInputRef = ref<InstanceType<typeof ChatInput> | null>(null);
const autoScroll = useAutoScroll(chatContainer);

// 监听路由变化，加载对应会话的消息
watch(
  () => route.params.sessionId,
  async (sessionId) => {
    if (sessionId && sessionId !== "new") {
      await store.loadMessages(sessionId as string);
    } else if (sessionId === "new") {
      // "新对话"路由 — 清空当前消息，等待用户发送第一条消息时创建会话
      store.currentSessionId = null;
      store.messages = [];
    }
    await nextTick();
    autoScroll.scrollToBottom();
  },
  { immediate: true }
);

// 消息变化时自动滚动
watch(
  () => store.messages.length,
  async () => {
    await nextTick();
    autoScroll.scrollToBottom();
  }
);

// 流式内容变化时持续滚动
watch(
  () => store.streamingContent,
  async () => {
    await nextTick();
    autoScroll.scrollToBottom();
  }
);

async function handleNewChat() {
  router.push("/chat/new");
}

/**
 * 点击功能卡片时，将提示语自动填入输入框并聚焦
 */
function setQuickPrompt(text: string) {
  chatInputRef.value?.setPromptText(text);
}

onMounted(async () => {
  await nextTick();
  autoScroll.scrollToBottom();
});
</script>

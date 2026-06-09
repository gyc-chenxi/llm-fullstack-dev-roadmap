<template>
  <!--
    SettingsPanel.vue — 系统提示词与参数设置
    ----------------------------------------
    可随时修改 System Prompt、Temperature、Max Tokens。
    支持预设模式模板（代码助手、翻译专家、通用助手）。
    修改自动保存到 Pinia Store，随下一次请求生效。
  -->
  <div class="flex flex-col h-full">
    <!-- 顶部栏 -->
    <header
      class="flex items-center gap-3 px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
    >
      <router-link
        to="/chat/new"
        class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
        title="返回聊天"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </router-link>
      <h1 class="text-sm font-semibold">设置</h1>
    </header>

    <!-- 设置内容 -->
    <div class="flex-1 overflow-y-auto">
      <div class="max-w-2xl mx-auto p-6 space-y-8">
        <!-- 预设模式 -->
        <section>
          <h2 class="text-lg font-semibold mb-3">预设模式</h2>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <button
              v-for="preset in presets"
              :key="preset.label"
              @click="applyPreset(preset)"
              :class="[
                'text-left px-4 py-3 rounded-xl border-2 transition-all',
                store.systemPrompt === preset.prompt
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500',
              ]"
            >
              <div class="text-2xl mb-1">{{ preset.icon }}</div>
              <div class="font-medium text-sm">{{ preset.label }}</div>
              <div class="text-xs text-gray-400 mt-0.5">{{ preset.desc }}</div>
            </button>
          </div>
        </section>

        <!-- 系统提示词 -->
        <section>
          <label for="system-prompt" class="block text-lg font-semibold mb-3">
            系统提示词 (System Prompt)
          </label>
          <textarea
            id="system-prompt"
            v-model="store.systemPrompt"
            rows="6"
            class="w-full resize-y rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
            placeholder="输入系统提示词..."
          ></textarea>
          <p class="text-xs text-gray-400 mt-1">
            定义 AI 助手的角色和行为。例如："你是一个专业的 Python 编程助手..."
          </p>
        </section>

        <!-- Temperature -->
        <section>
          <label for="temperature" class="block text-lg font-semibold mb-3">
            Temperature: {{ store.temperature.toFixed(1) }}
          </label>
          <div class="flex items-center gap-4">
            <input
              id="temperature"
              type="range"
              v-model.number="store.temperature"
              min="0"
              max="2"
              step="0.1"
              class="flex-1 h-2 rounded-lg appearance-none bg-gray-200 dark:bg-gray-600 cursor-pointer accent-blue-600"
            />
            <span class="text-sm w-12 text-right tabular-nums">
              {{ store.temperature.toFixed(1) }}
            </span>
          </div>
          <p class="text-xs text-gray-400 mt-1">
            值越低回答越确定（0.0），值越高回答越有创造性（2.0）。建议代码/翻译场景用 0.0~0.3，创意写作用 0.7~1.2。
          </p>
        </section>

        <!-- Max Tokens -->
        <section>
          <label for="max-tokens" class="block text-lg font-semibold mb-3">
            最大输出长度 (Max Tokens)
          </label>
          <input
            id="max-tokens"
            type="number"
            v-model.number="store.maxTokens"
            min="1"
            max="4096"
            step="64"
            class="w-32 rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p class="text-xs text-gray-400 mt-1">
            限制 AI 每次回复的最大 token 数。1 个中文字 ≈ 1.5-2 tokens，1 个英文单词 ≈ 1-2 tokens。
          </p>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useChatStore } from "../stores/chat";

const store = useChatStore();

// 预设模式模板
const presets = [
  {
    label: "通用助手",
    icon: "🤖",
    desc: "回答各种问题",
    prompt: "You are a helpful assistant.",
  },
  {
    label: "代码助手",
    icon: "💻",
    desc: "编写和解释代码",
    prompt: "You are an expert programmer. Write clean, well-commented code. Explain your thought process clearly. Use markdown code blocks with language identifiers.",
  },
  {
    label: "翻译专家",
    icon: "🌐",
    desc: "多语言翻译",
    prompt: "You are a professional translator. Translate accurately and naturally between Chinese and English. Preserve the original tone and style. Only output the translation without additional explanation.",
  },
];

function applyPreset(preset: (typeof presets)[number]) {
  store.systemPrompt = preset.prompt;
  store.temperature = 0.7; // 重置为默认值
}
</script>

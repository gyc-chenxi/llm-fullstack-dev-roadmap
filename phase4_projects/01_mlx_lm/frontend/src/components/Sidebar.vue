<template>
  <!--
    Sidebar.vue — 左侧历史会话列表
    ------------------------------
    桌面端可手动折叠，移动端默认折叠。
    列表项显示会话标题 + 相对时间。
    底部有设置按钮入口。
  -->
  <aside
    :class="[
      'flex flex-col h-full border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 transition-all duration-300',
      store.sidebarOpen ? 'w-72' : 'w-0 md:w-16',
    ]"
  >
    <!-- 折叠状态下的图标栏 -->
    <div v-if="!store.sidebarOpen" class="flex flex-col items-center gap-4 pt-4">
      <button
        @click="store.toggleSidebar()"
        class="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-500"
        title="展开侧边栏"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      <button
        @click="handleNewChat"
        class="p-2 rounded-lg bg-blue-50 dark:bg-blue-900/30 text-blue-600 hover:bg-blue-100 dark:hover:bg-blue-900/50"
        title="新建会话"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
      </button>
    </div>

    <!-- 展开状态下的完整侧边栏 -->
    <div v-if="store.sidebarOpen" class="flex flex-col h-full">
      <!-- 顶部：新建会话按钮 -->
      <div class="p-3">
        <button
          @click="handleNewChat"
          class="w-full flex items-center gap-2 px-3 py-2.5 rounded-xl border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 text-sm text-gray-700 dark:text-gray-300 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          新对话
        </button>
      </div>

      <!-- 分隔线 + 标题 -->
      <div class="px-3 pb-2 flex items-center justify-between">
        <span class="text-xs font-medium text-gray-400 uppercase tracking-wider">历史会话</span>
        <button
          @click="store.toggleSidebar()"
          class="p-1 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-400"
          title="折叠侧边栏"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        </button>
      </div>

      <!-- 会话列表 -->
      <div class="flex-1 overflow-y-auto px-2">
        <div v-if="store.sessions.length === 0" class="p-4 text-center text-xs text-gray-400">
          暂无会话，点击上方按钮开始
        </div>
        <div
          v-for="session in store.sessions"
          :key="session.id"
          @click="selectSession(session.id)"
          :class="[
            'group flex flex-col px-3 py-2.5 mb-0.5 rounded-lg cursor-pointer text-sm transition-colors',
            session.id === store.currentSessionId
              ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
              : 'hover:bg-gray-200/60 dark:hover:bg-gray-700/50 text-gray-700 dark:text-gray-300',
          ]"
        >
          <div class="flex items-center justify-between">
            <span class="truncate text-sm font-medium" :title="session.title">
              {{ session.title }}
            </span>
            <button
              @click.stop="handleDelete(session.id)"
              class="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-gray-400 hover:text-red-500 transition-all flex-shrink-0 ml-1"
              title="删除会话"
            >
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
          <span class="text-xs text-gray-400 mt-0.5">
            {{ formatRelativeTime(session.updated_at) }}
          </span>
        </div>
      </div>

      <!-- 底部：用户信息 + 设置 -->
      <div class="border-t border-gray-200 dark:border-gray-700 p-3 space-y-1">
        <!-- 用户信息条 -->
        <div class="flex items-center gap-2 px-3 py-2 rounded-lg">
          <div class="w-7 h-7 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center text-white text-xs font-bold">
            晨
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-xs font-medium text-gray-700 dark:text-gray-300 truncate">晨熙</p>
            <p class="text-[10px] text-gray-400 truncate">本地私有部署</p>
          </div>
        </div>

        <!-- 设置入口 -->
        <router-link
          to="/settings"
          class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          设置
        </router-link>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { useChatStore } from "../stores/chat";

const store = useChatStore();
const router = useRouter();

async function handleNewChat() {
  try {
    const id = await store.createSession();
    router.push(`/chat/${id}`);
  } catch {
    // 错误已在 store 中处理
  }
}

function selectSession(id: string) {
  store.loadMessages(id);
  router.push(`/chat/${id}`);
}

function handleDelete(id: string) {
  if (confirm("确定要删除这个会话吗？")) {
    store.deleteSession(id);
    if (store.currentSessionId === id) {
      router.push("/chat/new");
    }
  }
}

/**
 * 将 ISO 时间戳转为可读的相对时间（北京时间展示）
 * 后端时间以 UTC 存储，若缺少时区标识则自动补 Z
 */
function formatRelativeTime(isoString: string): string {
  // 兜底：若后端返回的 datetime 缺失时区标识（无 Z/+08:00 等后缀），视为 UTC
  const hasTz = isoString.endsWith("Z") || isoString.includes("+");
  const normalized = hasTz ? isoString : isoString + "Z";

  const now = Date.now();
  const then = new Date(normalized).getTime();

  if (isNaN(then)) return "";

  const diff = now - then;
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return "刚刚";
  if (minutes < 60) return `${minutes}分钟前`;
  if (hours < 24) return `${hours}小时前`;
  if (days < 7) return `${days}天前`;

  // 超过一周显示北京时间的日期
  const d = new Date(normalized);
  const month = d.getMonth() + 1;
  const day = d.getDate();
  return `${month}月${day}日`;
}
</script>

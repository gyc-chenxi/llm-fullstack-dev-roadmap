<template>
  <!--
    App.vue — 根布局组件
    ---------------------
    左侧：可折叠的会话历史列表（Sidebar）
    右侧：主内容区（路由出口：聊天区 / 设置面板）
  -->
  <div class="h-screen flex bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
    <!-- 侧边栏 -->
    <Sidebar />

    <!-- 主内容区 -->
    <main class="flex-1 flex flex-col min-w-0">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import Sidebar from "./components/Sidebar.vue";
import { useChatStore } from "./stores/chat";

const store = useChatStore();

// 应用初始化时加载会话列表
onMounted(() => {
  store.fetchSessions();
});
</script>

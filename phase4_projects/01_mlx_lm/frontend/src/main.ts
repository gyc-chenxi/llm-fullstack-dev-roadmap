/**
 * Vue 3 应用入口
 * --------------
 * 初始化 Vue 应用，挂载 Pinia（状态管理）+ Vue Router（路由）。
 *
 * 路由结构：
 *   /              → redirect /chat/new           （默认跳转到新会话）
 *   /chat/:sessionId → ChatArea 组件              （聊天主界面）
 *   /settings        → SettingsPanel 组件          （参数配置面板）
 */
import { createApp } from "vue";
import { createPinia } from "pinia";
import { createRouter, createWebHistory } from "vue-router";
import "./style.css";
import App from "./App.vue";

// 路由懒加载（Vite 自动 code-split）
const ChatArea = () => import("./components/ChatArea.vue");
const SettingsPanel = () => import("./components/SettingsPanel.vue");

const routes = [
  { path: "/", redirect: "/chat/new" },
  {
    path: "/chat/:sessionId",
    component: ChatArea,
    name: "chat",
  },
  {
    path: "/settings",
    component: SettingsPanel,
    name: "settings",
  },
];

// 使用 HTML5 History 模式（无 # 号 URL）
const router = createRouter({
  history: createWebHistory(),
  routes,
});

const pinia = createPinia();

const app = createApp(App);
app.use(pinia);
app.use(router);
app.mount("#app");

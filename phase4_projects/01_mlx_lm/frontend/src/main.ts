import { createApp } from "vue";
import { createPinia } from "pinia";
import { createRouter, createWebHistory } from "vue-router";
import "./style.css";
import App from "./App.vue";

// 路由懒加载
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

const router = createRouter({
  history: createWebHistory(),
  routes,
});

const pinia = createPinia();

const app = createApp(App);
app.use(pinia);
app.use(router);
app.mount("#app");

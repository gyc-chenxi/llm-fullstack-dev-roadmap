/**
 * Pinia 聊天状态管理
 * -------------------
 * 管理会话列表、当前会话、消息历史、生成参数等全局状态。
 * 所有 API 调用集中在此 store 中，组件只负责 UI 渲染。
 */

import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { parseSSELine, extractDelta } from "../composables/useSSE";

// ---------------------------------------------------------------------------
// 类型定义
// ---------------------------------------------------------------------------

export interface ChatMessage {
  id?: number;
  session_id?: string;
  role: "system" | "user" | "assistant";
  content: string;
  created_at?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  system_prompt?: string | null;
  created_at: string;
  updated_at: string;
  message_count?: number;
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useChatStore = defineStore("chat", () => {
  // ---- State ----
  const sessions = ref<ChatSession[]>([]);
  const currentSessionId = ref<string | null>(null);
  const messages = ref<ChatMessage[]>([]);
  const isStreaming = ref(false);
  const streamingContent = ref(""); // 当前正在流式生成中的 assistant 内容

  // 可调节的生成参数
  const systemPrompt = ref("You are a helpful assistant.");
  const temperature = ref(0.7);
  const maxTokens = ref(512);

  // 侧边栏折叠（移动端默认折叠）
  const sidebarOpen = ref(false);

  // AbortController：用于在 stopGeneration 中真正中止 SSE 请求
  let abortController: AbortController | null = null;

  // ---- Computed ----
  const currentSession = computed(() =>
    sessions.value.find((s) => s.id === currentSessionId.value)
  );

  // ---- Actions ----

  /**
   * 获取所有会话列表
   */
  async function fetchSessions() {
    try {
      const res = await fetch("/api/sessions");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      sessions.value = await res.json();
    } catch (e) {
      console.error("获取会话列表失败:", e);
    }
  }

  /**
   * 创建新会话并跳转到该会话
   */
  async function createSession(sysPrompt?: string): Promise<string> {
    try {
      const res = await fetch("/api/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          system_prompt: sysPrompt || systemPrompt.value,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const session: ChatSession = await res.json();
      sessions.value.unshift(session);
      return session.id;
    } catch (e) {
      console.error("创建会话失败:", e);
      throw e;
    }
  }

  /**
   * 删除会话
   */
  async function deleteSession(id: string) {
    try {
      const res = await fetch(`/api/sessions/${id}`, { method: "DELETE" });
      if (!res.ok && res.status !== 204) throw new Error(`HTTP ${res.status}`);
      sessions.value = sessions.value.filter((s) => s.id !== id);

      // 如果删除的是当前会话，清空消息
      if (currentSessionId.value === id) {
        currentSessionId.value = null;
        messages.value = [];
      }
    } catch (e) {
      console.error("删除会话失败:", e);
    }
  }

  /**
   * 加载某个会话的全部历史消息
   */
  async function loadMessages(sessionId: string) {
    currentSessionId.value = sessionId;
    try {
      const res = await fetch(`/api/sessions/${sessionId}/messages`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      messages.value = await res.json();
    } catch (e) {
      console.error("加载消息失败:", e);
      messages.value = [];
    }
  }

  /**
   * 发送消息（使用 SSE 流式获取回复）
   */
  async function sendMessage(content: string): Promise<void> {
    if (!content.trim() || isStreaming.value) return;

    // 如果没有当前会话，先创建
    if (!currentSessionId.value || currentSessionId.value === "new") {
      const newId = await createSession();
      currentSessionId.value = newId;
      // 更新路由（由组件处理，store 不操作 router）
      if (window.location.hash !== `#/chat/${newId}`) {
        window.history.replaceState(null, "", `/chat/${newId}`);
      }
    }

    // 添加用户消息到本地
    const userMsg: ChatMessage = {
      role: "user",
      content: content,
    };
    messages.value.push(userMsg);

    // 添加占位的 assistant 消息
    const assistantMsg: ChatMessage = {
      role: "assistant",
      content: "",
    };
    messages.value.push(assistantMsg);

    // 开始流式
    isStreaming.value = true;
    streamingContent.value = "";

    // 构建请求消息列表
    const reqMessages: ChatMessage[] = [
      { role: "system", content: systemPrompt.value },
      // 带上最近的多轮历史（后端会做滑动窗口截断，这里全量发送）
      ...messages.value
        .filter((m) => m.role !== "system")
        .slice(0, -1) // 排除刚加的占位 assistant
        .map((m) => ({ role: m.role, content: m.content })),
    ];

    abortController = new AbortController();

    try {
      const response = await fetch("/v1/chat/completions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: reqMessages,
          max_tokens: maxTokens.value,
          temperature: temperature.value,
          session_id: currentSessionId.value,
          system_prompt: systemPrompt.value,
        }),
        signal: abortController.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("无法读取响应流");

      const decoder = new TextDecoder("utf-8");
      let buffer = ""; // 行缓冲区：处理跨 chunk 的不完整行

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // 按行分割并处理
        const lines = buffer.split("\n");
        // 最后一行可能不完整，保留到下次循环
        buffer = lines.pop() || "";

        for (const line of lines) {
          const parsed = parseSSELine(line);
          if (parsed === null) break; // [DONE] 信号
          if (!parsed) continue;      // 空行或解析失败，跳过

          const delta = extractDelta(parsed);
          if (delta) {
            streamingContent.value += delta;
            // 实时更新 assistant 消息内容
            const lastMsg = messages.value[messages.value.length - 1];
            if (lastMsg && lastMsg.role === "assistant") {
              lastMsg.content = streamingContent.value;
            }
          }
        }
      }
    } catch (e: unknown) {
      if (e instanceof DOMException && e.name === "AbortError") {
        // 用户主动停止生成
        console.log("生成已停止");
      } else {
        console.error("SSE 流式请求失败:", e);
        // 在 assistant 消息中显示错误
        const lastMsg = messages.value[messages.value.length - 1];
        if (lastMsg && lastMsg.role === "assistant" && !lastMsg.content) {
          lastMsg.content = "⚠️ 请求失败，请重试。";
        }
      }
    } finally {
      isStreaming.value = false;
      streamingContent.value = "";
      // 刷新会话列表以更新顺序和标题
      fetchSessions();
    }
  }

  /**
   * 停止当前生成（真正中止 SSE 请求）
   */
  function stopGeneration() {
    if (abortController) {
      abortController.abort();
      abortController = null;
    }
    isStreaming.value = false;
    streamingContent.value = "";
  }

  /**
   * 切换侧边栏
   */
  function toggleSidebar() {
    sidebarOpen.value = !sidebarOpen.value;
  }

  return {
    // State
    sessions,
    currentSessionId,
    messages,
    isStreaming,
    streamingContent,
    systemPrompt,
    temperature,
    maxTokens,
    sidebarOpen,
    // Computed
    currentSession,
    // Actions
    fetchSessions,
    createSession,
    deleteSession,
    loadMessages,
    sendMessage,
    stopGeneration,
    toggleSidebar,
  };
});

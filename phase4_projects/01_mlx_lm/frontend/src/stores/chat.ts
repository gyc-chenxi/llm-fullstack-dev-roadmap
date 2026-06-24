/**
 * Pinia 聊天状态管理
 * -------------------
 * 管理会话列表、当前会话、消息历史、生成参数等全局状态。
 *
 * 职责边界：
 *   - 所有 API 调用集中在此 store（后端 REST + SSE）
 *   - 组件只负责 UI 渲染和交互事件
 *   - SSE 流式读取逻辑内嵌在 sendMessage() 中
 *
 * 数据流向（发送消息）：
 *   sendMessage(content)
 *     → fetchSessions / createSession      ← 会话管理
 *     → POST /v1/chat/completions (SSE)    ← 流式推理请求
 *       → ReadableStream.getReader()       ← 逐 chunk 读取 SSE
 *       → parseSSELine → extractDelta      ← 增量文本提取
 *       → streamingContent += delta        ← 实时推送到 UI
 *     → 流结束后自动 fetchSessions()        ← 刷新会话列表
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
  // ---- 状态 ----
  const sessions = ref<ChatSession[]>([]);       // 所有会话（侧边栏列表）
  const currentSessionId = ref<string | null>(null); // 当前正在查看的会话 ID
  const messages = ref<ChatMessage[]>([]);        // 当前会话的消息数组
  const isStreaming = ref(false);                 // 是否正在流式生成
  const streamingContent = ref("");               // 当前接收到的流式文本累积 buffer

  // 可调节的生成参数（配置面板）
  const systemPrompt = ref("You are a helpful assistant.");
  const temperature = ref(0.7);
  const maxTokens = ref(512);

  // 侧边栏折叠状态（移动端默认折叠）
  const sidebarOpen = ref(false);

  // AbortController：中止 SSE 请求（用户点击"停止生成"）
  let abortController: AbortController | null = null;

  // ---- Computed ----
  const currentSession = computed(() =>
    sessions.value.find((s) => s.id === currentSessionId.value)
  );

  // ---- Actions ----

  /**
   * 获取所有会话列表（按 updated_at 倒序）
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
   * 创建新会话并跳转到该会话。
   *
   * @param sysPrompt - 可选，覆盖当前的 systemPrompt
   * @returns 新创建的会话 ID
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
      sessions.value.unshift(session);  // 新会话插入列表最前
      return session.id;
    } catch (e) {
      console.error("创建会话失败:", e);
      throw e;
    }
  }

  /**
   * 删除指定会话。
   * 如果删除的是当前会话，清空 messages 和 currentSessionId。
   */
  async function deleteSession(id: string) {
    try {
      const res = await fetch(`/api/sessions/${id}`, { method: "DELETE" });
      if (!res.ok && res.status !== 204) throw new Error(`HTTP ${res.status}`);
      sessions.value = sessions.value.filter((s) => s.id !== id);

      // 如果删除的是当前会话，清空本地状态
      if (currentSessionId.value === id) {
        currentSessionId.value = null;
        messages.value = [];
      }
    } catch (e) {
      console.error("删除会话失败:", e);
    }
  }

  /**
   * 加载某个会话的全部历史消息（按时间正序）。
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
   * 发送消息（SSE 流式获取回复）。
   *
   * 核心流程：
   *   1. 若无当前会话 → 自动创建
   *   2. 在本地 messages 中添加 user 消息和占位 assistant 消息
   *   3. POST /v1/chat/completions 发起 SSE 请求
   *   4. 使用 ReadableStream 逐块读取响应体
   *   5. 每收到一个 delta，更新 streamingContent 并实时反映到 UI
   *   6. 流结束后自动刷新会话列表（更新标题和顺序）
   *
   * @param content - 用户输入的文本
   */
  async function sendMessage(content: string): Promise<void> {
    if (!content.trim() || isStreaming.value) return;

    // ---- Step 1: 没有当前会话则自动创建 ----
    if (!currentSessionId.value || currentSessionId.value === "new") {
      const newId = await createSession();
      currentSessionId.value = newId;
      if (window.location.hash !== `#/chat/${newId}`) {
        window.history.replaceState(null, "", `/chat/${newId}`);
      }
    }

    // ---- Step 2: 本地添加消息占位 ----
    const userMsg: ChatMessage = { role: "user", content: content };
    messages.value.push(userMsg);

    const assistantMsg: ChatMessage = { role: "assistant", content: "" };
    messages.value.push(assistantMsg);

    // ---- Step 3: 发起 SSE 流式请求 ----
    isStreaming.value = true;
    streamingContent.value = "";

    // 构建请求消息列表（将 system prompt 拼接到 messages 头部）
    const reqMessages: ChatMessage[] = [
      { role: "system", content: systemPrompt.value },
      // 携带最近的多轮历史（后端负责滑动窗口截断，前端全量发送）
      ...messages.value
        .filter((m) => m.role !== "system")
        .slice(0, -1)                   // 排除刚添加的占位 assistant 消息
        .map((m) => ({ role: m.role, content: m.content })),
    ];

    abortController = new AbortController();

    try {
      // POST 请求，返回 SSE 流式响应
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

      // ---- Step 4: 读取 SSE 响应流 ----
      const reader = response.body?.getReader();
      if (!reader) throw new Error("无法读取响应流");

      const decoder = new TextDecoder("utf-8");
      let buffer = ""; // 行缓冲区：处理跨 chunk 的不完整 SSE 行

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // 将字节流解码为文本并追加到缓冲区
        buffer += decoder.decode(value, { stream: true });

        // 按 '\n' 分割，逐行解析
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";  // 最后一行可能不完整，保留

        for (const line of lines) {
          const parsed = parseSSELine(line);
          if (parsed === null) break;     // [DONE] → 流结束
          if (!parsed) continue;          // 空行或非 data 行，跳过

          const delta = extractDelta(parsed);
          if (delta) {
            streamingContent.value += delta;
            // 实时更新 assistant 占位消息的内容（响应式驱动 UI 更新）
            const lastMsg = messages.value[messages.value.length - 1];
            if (lastMsg && lastMsg.role === "assistant") {
              lastMsg.content = streamingContent.value;
            }
          }
        }
      }
    } catch (e: unknown) {
      if (e instanceof DOMException && e.name === "AbortError") {
        // 用户主动点击"停止生成"触发的 AbortController.abort()
        console.log("生成已停止");
      } else {
        console.error("SSE 流式请求失败:", e);
        // 在 assistant 占位消息中显示错误提示
        const lastMsg = messages.value[messages.value.length - 1];
        if (lastMsg && lastMsg.role === "assistant" && !lastMsg.content) {
          lastMsg.content = "⚠️ 请求失败，请重试。";
        }
      }
    } finally {
      // ---- Step 5: 恢复状态 ----
      isStreaming.value = false;
      streamingContent.value = "";
      // 刷新会话列表（更新标题、updated_at 排序）
      fetchSessions();
    }
  }

  /**
   * 停止当前生成（通过 AbortController.abort() 真正中止 SSE 连接）。
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
   * 切换侧边栏展开/折叠
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

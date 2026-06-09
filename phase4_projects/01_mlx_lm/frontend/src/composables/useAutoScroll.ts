/**
 * 自动滚动 Composable
 * -------------------
 * 在流式输出期间自动将聊天区域滚动到底部。
 * 如果用户主动向上滚动查看历史消息，则暂停自动滚动，
 * 直到用户重新滚动到底部附近。
 */

import { ref, watch, type Ref } from "vue";

export function useAutoScroll(containerRef: Ref<HTMLElement | null>) {
  const shouldAutoScroll = ref(true);

  /**
   * 用户手动滚动时调用，判断是否在底部附近。
   * 距离底部 < 100px 视为"在底部"，恢复自动滚动。
   */
  function onUserScroll() {
    const el = containerRef.value;
    if (!el) return;

    const distanceToBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    shouldAutoScroll.value = distanceToBottom < 100;
  }

  /**
   * 滚动到底部（仅当 shouldAutoScroll 为 true 时执行）
   */
  function scrollToBottom() {
    if (!shouldAutoScroll.value) return;
    const el = containerRef.value;
    if (!el) return;

    // 使用 requestAnimationFrame 确保在 DOM 更新后执行
    requestAnimationFrame(() => {
      el.scrollTop = el.scrollHeight;
    });
  }

  return {
    shouldAutoScroll,
    onUserScroll,
    scrollToBottom,
  };
}

/**
 * 聊天区域自动滚动 Composable
 * ---------------------------
 * 在流式输出期间自动将聊天区域滚动到底部，让用户持续看到最新内容。
 *
 * 交互策略：
 *   - 默认持续自动滚动到底部
 *   - 如果用户主动向上滚动查看历史消息 → 暂停自动滚动
 *   - 当用户滚动到底部附近（< 100px）时 → 恢复自动滚动
 *
 * 使用方式：
 *   const containerRef = ref<HTMLElement | null>(null)
 *   const { shouldAutoScroll, onUserScroll, scrollToBottom } = useAutoScroll(containerRef)
 */

import { ref, type Ref } from "vue";

export function useAutoScroll(containerRef: Ref<HTMLElement | null>) {
  const shouldAutoScroll = ref(true);

  /**
   * 用户手动滚动时的回调处理函数。
   * 判断逻辑：距离底部 < 100px 视为"在底部"，恢复自动滚动。
   * 绑定方式：@scroll="onUserScroll"
   */
  function onUserScroll() {
    const el = containerRef.value;
    if (!el) return;

    const distanceToBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    shouldAutoScroll.value = distanceToBottom < 100;
  }

  /**
   * 滚动到底部（仅当 shouldAutoScroll 为 true 时执行）。
   * 使用 requestAnimationFrame 确保在 Vue DOM 更新后执行，
   * 避免在 nextTick 之前滚动时新内容尚未渲染。
   */
  function scrollToBottom() {
    if (!shouldAutoScroll.value) return;
    const el = containerRef.value;
    if (!el) return;

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

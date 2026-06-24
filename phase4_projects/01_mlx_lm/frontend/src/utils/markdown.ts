/**
 * Markdown 渲染工具
 * -----------------
 * 基于 markdown-it 的 Markdown → HTML 渲染引擎，集成 highlight.js 实现代码语法高亮。
 *
 * 数据流向：
 *   assistant 回复文本 (raw Markdown)
 *     → renderMarkdown(text)            ← markdown-it 渲染为 HTML 字符串
 *     → attachCopyButtons(container)    ← 为代码块注入"复制"按钮
 *     → innerHTML 更新 DOM              ← 由 Vue 组件在 nextTick 中调用
 */
import MarkdownIt from "markdown-it";
import hljs from "highlight.js";

// markdown-it 实例配置
const md = new MarkdownIt({
  html: false,         // 禁用原始 HTML 标签（安全考量，防止 XSS）
  linkify: true,       // 自动将 URL 文本转为可点击链接
  breaks: true,        // 将 \n 转为 <br>（兼容聊天场景的换行习惯）
  typographer: true,   // 智能引号、连字符等排版优化

  // 代码块语法高亮函数
  highlight(str: string, lang: string): string {
    // 指定语言且 highlight.js 支持该语言
    if (lang && hljs.getLanguage(lang)) {
      try {
        const highlighted = hljs.highlight(str, {
          language: lang,
          ignoreIllegals: true,  // 忽略非法 token，尽量高亮
        }).value;
        // 返回带 data-lang 属性的 pre 标签，供复制按钮识别
        return `<pre class="hljs-code-block" data-lang="${lang}"><code class="hljs language-${lang}">${highlighted}</code></pre>`;
      } catch {
        // 若高亮抛出异常，回退到自动检测
      }
    }

    // 无语言标识或高亮失败，使用自动检测
    try {
      const highlighted = hljs.highlightAuto(str).value;
      return `<pre class="hljs-code-block"><code class="hljs">${highlighted}</code></pre>`;
    } catch {
      // 最终回退：纯文本 + HTML 转义
      return `<pre class="hljs-code-block"><code>${md.utils.escapeHtml(str)}</code></pre>`;
    }
  },
});

/**
 * 将 Markdown 文本渲染为 HTML 字符串。
 *
 * @param text - 原始 Markdown 文本（来自 assistant 回复）
 * @returns 渲染后的 HTML 字符串
 */
export function renderMarkdown(text: string): string {
  if (!text) return "";
  return md.render(text);
}

/**
 * 为渲染后的 HTML 中的所有代码块注入"复制"按钮。
 *
 * 调用时机：在 DOM 更新后（Vue.nextTick），由组件调用此函数。
 * 实现方式：遍历所有 .hljs-code-block 容器，为每个添加一个绝对定位的复制按钮。
 *
 * 交互细节：
 *   - 鼠标悬停 pre 元素时按钮显示
 *   - 点击后将代码写入剪贴板（优先 navigator.clipboard API，降级使用 execCommand）
 *   - 复制成功显示"已复制!"，2 秒后恢复
 *
 * @param container - 包含渲染后内容的 DOM 元素
 */
export function attachCopyButtons(container: HTMLElement): void {
  const blocks = container.querySelectorAll(".hljs-code-block");
  blocks.forEach((block) => {
    // 防止同一个代码块被重复添加复制按钮
    if (block.querySelector(".code-copy-btn")) return;

    const pre = block as HTMLElement;
    pre.style.position = "relative";

    const btn = document.createElement("button");
    btn.className = "code-copy-btn";
    btn.textContent = "复制";
    btn.style.cssText = `
      position: absolute; top: 8px; right: 8px;
      padding: 4px 10px; font-size: 12px;
      background: rgba(255,255,255,0.1); color: #c9d1d9;
      border: 1px solid rgba(255,255,255,0.15); border-radius: 4px;
      cursor: pointer; opacity: 0; transition: opacity 0.2s;
    `;

    // hover 显隐控制
    pre.addEventListener("mouseenter", () => { btn.style.opacity = "1"; });
    pre.addEventListener("mouseleave", () => { btn.style.opacity = "0"; });

    // 点击复制代码内容
    btn.addEventListener("click", async () => {
      const code = pre.querySelector("code")?.textContent || "";
      try {
        // 优先使用 Clipboard API（异步，不阻塞 UI）
        await navigator.clipboard.writeText(code);
      } catch {
        // Clipboard API 不可用时降级为传统方式（如 HTTP 页面中）
        const textarea = document.createElement("textarea");
        textarea.value = code;
        textarea.style.cssText = "position:fixed;opacity:0;";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      btn.textContent = "已复制!";
      setTimeout(() => { btn.textContent = "复制"; }, 2000);
    });

    pre.appendChild(btn);
  });
}

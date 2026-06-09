/**
 * Markdown 渲染工具
 * -----------------
 * 配置 markdown-it 实例，集成 highlight.js 实现代码语法高亮。
 * 对外暴露 renderMarkdown 函数，组件中直接调用即可。
 */

import MarkdownIt from "markdown-it";
import hljs from "highlight.js";

// 创建 markdown-it 实例
const md = new MarkdownIt({
  html: false, // 禁用原始 HTML（安全考虑）
  linkify: true, // 自动将 URL 转为链接
  breaks: true, // 将 \n 转为 <br>
  typographer: true, // 智能引号等排版优化

  // 代码块高亮配置
  highlight(str: string, lang: string): string {
    // 如果指定了语言且 highlight.js 支持
    if (lang && hljs.getLanguage(lang)) {
      try {
        const highlighted = hljs.highlight(str, {
          language: lang,
          ignoreIllegals: true,
        }).value;
        // 返回带有语言标识的 HTML，供复制按钮识别
        return `<pre class="hljs-code-block" data-lang="${lang}"><code class="hljs language-${lang}">${highlighted}</code></pre>`;
      } catch {
        // 高亮失败则回退为纯文本
      }
    }

    // 无语言标识或高亮失败时，用自动检测
    try {
      const highlighted = hljs.highlightAuto(str).value;
      return `<pre class="hljs-code-block"><code class="hljs">${highlighted}</code></pre>`;
    } catch {
      // 最终回退
      return `<pre class="hljs-code-block"><code>${md.utils.escapeHtml(str)}</code></pre>`;
    }
  },
});

/**
 * 将 Markdown 文本渲染为 HTML 字符串
 */
export function renderMarkdown(text: string): string {
  if (!text) return "";
  return md.render(text);
}

/**
 * 为渲染后的 HTML 中的代码块添加"复制"按钮。
 *
 * 调用时机：在 DOM 更新后，由组件通过 nextTick 调用此函数，
 * 对 .hljs-code-block 容器注入复制按钮。
 *
 * @param container 包含渲染内容的 DOM 元素
 */
export function attachCopyButtons(container: HTMLElement): void {
  const blocks = container.querySelectorAll(".hljs-code-block");
  blocks.forEach((block) => {
    // 防止重复添加
    if (block.querySelector(".code-copy-btn")) return;

    const pre = block as HTMLElement;
    // 为 pre 添加相对定位，以便复制按钮绝对定位
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

    // 鼠标悬停时显示按钮
    pre.addEventListener("mouseenter", () => {
      btn.style.opacity = "1";
    });
    pre.addEventListener("mouseleave", () => {
      btn.style.opacity = "0";
    });

    // 点击复制
    btn.addEventListener("click", async () => {
      const code = pre.querySelector("code")?.textContent || "";
      try {
        await navigator.clipboard.writeText(code);
        btn.textContent = "已复制!";
        setTimeout(() => {
          btn.textContent = "复制";
        }, 2000);
      } catch {
        // 降级：使用传统方式复制
        const textarea = document.createElement("textarea");
        textarea.value = code;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
        btn.textContent = "已复制!";
        setTimeout(() => {
          btn.textContent = "复制";
        }, 2000);
      }
    });

    pre.appendChild(btn);
  });
}
